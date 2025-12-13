# Staff Management API

Complete API documentation for staff (employee) management via `BranchMembership` model.

## Overview

The staff management system is built on the unified `BranchMembership` model, eliminating duplication by using `Role` as the single source of truth for staff positions. This architecture follows Django best practices and provides:

- Complete employment tracking (hire date, termination, employment type)
- Passport and address information
- Emergency contact details
- Balance management (salary, bonuses, deductions)
- Salary payment tracking
- Employment history and statistics

## Architecture

### Key Models

**BranchMembership** (Single Source of Truth for Staff):
- User, Branch, Role relationships
- Employment details: hire_date, termination_date, employment_type
- Personal info: passport_serial, passport_number, address, emergency_contact
- Financial: salary, balance
- Soft delete support

**Role** (Position/Job Title):
- name, code, description
- salary_range_min, salary_range_max
- Permissions via RolePermission

**BalanceTransaction** (Financial Operations):
- Transaction types: salary, bonus, deduction, advance, fine
- Tracks amount, balance changes, and transaction history

**SalaryPayment** (Payment Records):
- Payment methods: cash, bank_transfer, card
- Payment status: pending, completed, failed
- Links to specific staff member

### Services

**BalanceService** (apps/branch/services.py):
- Atomic transaction handling with `select_for_update()`
- Methods: `apply_transaction()`, `add_salary()`, `add_bonus()`, `apply_deduction()`, `give_advance()`, `apply_fine()`

## API Endpoints

Base URL: `/api/branch/staff/`

### 1. List Staff

**Endpoint**: `GET /api/branch/staff/`

**Query Parameters**:
- `branch` (UUID): Filter by branch
- `role` (UUID): Filter by role/position
- `employment_type` (string): full_time, part_time, contract, intern
- `status` (string): active, terminated
- `search` (string): Search by name, phone, passport
- `ordering` (string): Sort by hire_date, salary, balance, created_at

**Response**: 200 OK
```json
{
  "count": 25,
  "next": "http://api.example.com/api/branch/staff/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "first_name": "Ali",
        "last_name": "Valiyev",
        "phone": "+998901234567",
        "email": "ali@example.com"
      },
      "branch": {
        "id": "uuid",
        "name": "Toshkent filiali"
      },
      "role": {
        "id": "uuid",
        "name": "O'qituvchi",
        "code": "teacher",
        "salary_range_min": "3000000.00",
        "salary_range_max": "5000000.00"
      },
      "hire_date": "2024-01-15",
      "termination_date": null,
      "employment_type": "full_time",
      "salary": "4000000.00",
      "balance": "1500000.00",
      "passport_serial": "AB",
      "passport_number": "1234567",
      "address": "Toshkent sh., Chilonzor tumani",
      "emergency_contact": "+998901111111",
      "notes": "Matematika fanidan mutaxassis",
      "is_active_employment": true,
      "days_employed": 120,
      "years_employed": 0.33,
      "balance_status": "positive",
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

**Examples**:
```bash
# All active staff
GET /api/branch/staff/?status=active

# Teachers only
GET /api/branch/staff/?role=uuid&status=active

# Search by name
GET /api/branch/staff/?search=Ali

# Sort by hire date (newest first)
GET /api/branch/staff/?ordering=-hire_date
```

---

### 2. Create Staff Member

**Endpoint**: `POST /api/branch/staff/`

**Request Body**:
```json
{
  "user": "uuid",
  "branch": "uuid",
  "role": "uuid",
  "hire_date": "2024-01-15",
  "employment_type": "full_time",
  "salary": "4000000.00",
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor tumani",
  "emergency_contact": "+998901111111",
  "notes": "Matematika fanidan mutaxassis"
}
```

**Required Fields**:
- user, branch, role, hire_date, employment_type, salary

**Response**: 201 Created
```json
{
  "id": "uuid",
  "user": {...},
  "branch": {...},
  "role": {...},
  "hire_date": "2024-01-15",
  "employment_type": "full_time",
  "salary": "4000000.00",
  "balance": "0.00",
  ...
}
```

---

### 3. Get Staff Details

**Endpoint**: `GET /api/branch/staff/{id}/`

**Response**: 200 OK
```json
{
  "id": "uuid",
  "user": {
    "id": "uuid",
    "first_name": "Ali",
    "last_name": "Valiyev",
    "phone": "+998901234567",
    "email": "ali@example.com"
  },
  "branch": {
    "id": "uuid",
    "name": "Toshkent filiali"
  },
  "role": {
    "id": "uuid",
    "name": "O'qituvchi",
    "code": "teacher",
    "salary_range_min": "3000000.00",
    "salary_range_max": "5000000.00"
  },
  "hire_date": "2024-01-15",
  "termination_date": null,
  "employment_type": "full_time",
  "salary": "4000000.00",
  "balance": "1500000.00",
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor tumani",
  "emergency_contact": "+998901111111",
  "notes": "Matematika fanidan mutaxassis",
  "is_active_employment": true,
  "days_employed": 120,
  "years_employed": 0.33,
  "balance_status": "positive"
}
```

---

### 4. Update Staff

**Endpoint**: `PATCH /api/branch/staff/{id}/`

**Request Body** (partial update):
```json
{
  "salary": "4500000.00",
  "address": "Yangi manzil",
  "notes": "Ish ko'rsatkichi yaxshi"
}
```

**Terminate Employment**:
```json
{
  "termination_date": "2024-12-31"
}
```

**Response**: 200 OK (full object)

---

### 5. Delete Staff (Soft Delete)

**Endpoint**: `DELETE /api/branch/staff/{id}/`

**Response**: 204 No Content

**Note**: Soft delete - `deleted_at` timestamp is set, data is preserved.

---

### 6. Staff Statistics

**Endpoint**: `GET /api/branch/staff/stats/`

**Query Parameters**:
- `branch` (UUID): Filter statistics by branch

**Response**: 200 OK
```json
{
  "total_staff": 25,
  "active_staff": 22,
  "terminated_staff": 3,
  "by_employment_type": [
    {"employment_type": "full_time", "count": 18},
    {"employment_type": "part_time", "count": 4}
  ],
  "by_role": [
    {"role__name": "O'qituvchi", "count": 15},
    {"role__name": "Admin", "count": 5},
    {"role__name": "Manager", "count": 2}
  ],
  "average_salary": 3850000.00
}
```

---

### 7. Add Balance Transaction

**Endpoint**: `POST /api/branch/staff/{id}/add_balance/`

**Request Body**:
```json
{
  "amount": "500000.00",
  "transaction_type": "bonus",
  "description": "Yangi yil bonusi"
}
```

**Transaction Types**:
- `salary`: Monthly salary
- `bonus`: Performance bonus
- `deduction`: Deduction from balance
- `advance`: Salary advance
- `fine`: Penalty/fine

**Response**: 200 OK (updated staff object with new balance)

**Examples**:
```json
// Salary payment
{
  "amount": "4000000.00",
  "transaction_type": "salary",
  "description": "Yanvar oyi ish haqi"
}

// Bonus
{
  "amount": "1000000.00",
  "transaction_type": "bonus",
  "description": "Yillik bonus"
}

// Deduction
{
  "amount": "200000.00",
  "transaction_type": "deduction",
  "description": "Telefon to'lovi"
}
```

---

### 8. Record Salary Payment

**Endpoint**: `POST /api/branch/staff/{id}/pay_salary/`

**Request Body**:
```json
{
  "amount": "4000000.00",
  "payment_method": "bank_transfer",
  "payment_status": "completed",
  "notes": "Yanvar oyi ish haqi"
}
```

**Payment Methods**:
- `cash`: Cash payment
- `bank_transfer`: Bank transfer
- `card`: Card payment

**Payment Status**:
- `pending`: Payment scheduled
- `completed`: Payment completed
- `failed`: Payment failed

**Response**: 200 OK (updated staff object)

---

## Business Logic

### Employment Status

**Active Employment**:
- `termination_date` is null
- `deleted_at` is null

**Terminated Employment**:
- `termination_date` is set

**Soft Deleted**:
- `deleted_at` is set
- Data preserved for audit trail

### Balance Management

**Transactions are atomic** using `select_for_update()`:
1. Lock membership row
2. Create BalanceTransaction record
3. Update membership.balance
4. Commit transaction

**Balance Types**:
- **Positive**: balance > 0 (credit to employee)
- **Zero**: balance == 0
- **Negative**: balance < 0 (debt from employee)

### Salary Validation

When creating/updating staff:
- Salary must be within role's `salary_range_min` and `salary_range_max` (if defined)
- Validation performed in serializer

---

## Permissions

All endpoints require:
- `IsAuthenticated`: User must be logged in
- `HasBranchRole`: User must have role in relevant branch

**Branch Access**:
- SuperAdmin: Access to all branches
- BranchAdmin: Access to managed branches only
- Staff: Read-only access to own data

---

## Employment Types

```python
class EmploymentType(models.TextChoices):
    FULL_TIME = 'full_time', 'To\'liq stavka'
    PART_TIME = 'part_time', 'Yarim stavka'
    CONTRACT = 'contract', 'Shartnoma asosida'
    INTERN = 'intern', 'Amaliyotchi'
```

---

## Examples

### Creating Staff with Full Details

```bash
curl -X POST http://localhost:8000/api/branch/staff/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user": "user-uuid",
    "branch": "branch-uuid",
    "role": "role-uuid",
    "hire_date": "2024-01-15",
    "employment_type": "full_time",
    "salary": "4000000.00",
    "passport_serial": "AB",
    "passport_number": "1234567",
    "address": "Toshkent sh., Chilonzor tumani",
    "emergency_contact": "+998901111111",
    "notes": "Matematika fanidan mutaxassis"
  }'
```

### Paying Salary

```bash
curl -X POST http://localhost:8000/api/branch/staff/{id}/pay_salary/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "4000000.00",
    "payment_method": "bank_transfer",
    "payment_status": "completed",
    "notes": "Yanvar oyi ish haqi"
  }'
```

### Filtering Active Teachers

```bash
curl -X GET "http://localhost:8000/api/branch/staff/?role=teacher-role-uuid&status=active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Related Documentation

- [Models Architecture](../models-architecture.md)
- [Permissions & RBAC](../permissions-rbac.md)
- [Branch Management](./branch.md)
- [Role Management](./role.md)

---

## Migration History

- `0011_add_complete_staff_fields`: Added all employment fields to BranchMembership
- `0012_add_balance_salary_models`: Added BalanceTransaction and SalaryPayment models

---

## Changelog

**2024-12-13**:
- Initial staff management API implementation
- Unified BranchMembership as single staff model
- HR app deprecated and removed
- Complete employment tracking added
- Balance management system implemented
