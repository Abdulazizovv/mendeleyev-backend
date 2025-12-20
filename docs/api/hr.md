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

**Base URL:** `/api/v1/branches/staff/`

**Authentication:** Bearer token kerak (Authorization: Bearer YOUR_TOKEN)

**Permissions:** `IsAuthenticated` + `HasBranchRole` kerak barcha endpoint'larda

**Important Field Names:**
- `role_ref` - Role ForeignKey (UUID)
- `role` - Legacy CharField (for backward compatibility)
- `monthly_salary` - Oylik maosh (integer)
- `salary` - Computed field from `get_salary()` method

### 1. List Staff

**Endpoint**: `GET /api/v1/branches/staff/`

**Description**: Barcha xodimlar ro'yxatini olish. Ixcham ma'lumotlar bilan. Pagination, filtering, search, ordering qo'llab-quvvatlanadi.

**⚡ Performance:** Ixcham response - faqat zarur maydonlar qaytariladi.

**Query Parameters**:
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `branch` | UUID | Filial ID bo'yicha filter | `?branch=uuid-here` |
| `role_ref` | UUID | Lavozim ID bo'yicha filter (Role model) | `?role_ref=uuid-here` |
| `employment_type` | string | Ish turi: full_time, part_time, contract, intern | `?employment_type=full_time` |
| `status` | string | active yoki terminated | `?status=active` |
| `search` | string | Ism, telefon, pasport bo'yicha qidirish | `?search=Ali` |
| `ordering` | string | Tartiblash: hire_date, monthly_salary, balance, created_at | `?ordering=-hire_date` |
| `page` | number | Sahifa raqami | `?page=2` |
| `page_size` | number | Har sahifada nechta | `?page_size=20` |

**Response**: 200 OK (Compact - only essential fields)
```json
{
  "count": 25,
  "next": "http://api.example.com/api/v1/branches/staff/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "full_name": "Ali Valiyev",
      "phone_number": "+998901234567",
      "role": "teacher",
      "role_display": "O'qituvchi",
      "role_ref_name": "Matematika o'qituvchisi",
      "title": "Katta o'qituvchi",
      "employment_type": "full_time",
      "employment_type_display": "To'liq ish kuni",
      "hire_date": "2024-01-15",
      "balance": 1500000,
      "monthly_salary": 4000000,
      "is_active": true
    }
  ]
}
```

**Note:** List API faqat asosiy ma'lumotlarni qaytaradi. To'liq ma'lumot uchun detail endpoint'dan foydalaning.

**Examples**:
```bash
# All active staff
GET /api/v1/branches/staff/?status=active

# Teachers only
GET /api/v1/branches/staff/?role=uuid&status=active

# Search by name
GET /api/v1/branches/staff/?search=Ali

# Sort by hire date (newest first)
GET /api/v1/branches/staff/?ordering=-hire_date
```

---

### 2. Create Staff Member

**Endpoint**: `POST /api/v1/branches/staff/`

**Request Body**:
```json
{
  "user": "uuid",
  "branch": "uuid",
  "role_ref": "uuid",
  "hire_date": "2024-01-15",
  "employment_type": "full_time",
  "monthly_salary": 4000000,
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor tumani",
  "emergency_contact": "+998901111111",
  "notes": "Matematika fanidan mutaxassis"
}
```

**Required Fields**:
- `user` (UUID) - User ID
- `branch` (UUID) - Branch ID  
- `role_ref` (UUID) - Role ID
- `hire_date` (date) - YYYY-MM-DD
- `employment_type` (string) - full_time, part_time, contract, intern
- `monthly_salary` (integer) - Oylik maosh (so'm)

**Response**: 201 Created
```json
{
  "id": "uuid",
  "user": "uuid",
  "branch": "uuid",
  "role_ref": "uuid",
  "role_ref_name": "O'qituvchi",
  "hire_date": "2024-01-15",
  "employment_type": "full_time",
  "monthly_salary": 4000000,
  "salary": 4000000,
  "balance": 0,
  "is_active_employment": true
}
```

---

### 3. Get Staff Details

**Endpoint**: `GET /api/v1/branches/staff/{id}/`

**Description**: Xodimning to'liq ma'lumotlari, tranzaksiyalari va to'lovlari bilan.

**📊 Includes:**
- Complete user and branch information
- Role details with permissions
- Financial summaries
- Last 10 transactions
- Last 10 salary payments
- Employment statistics

**Response**: 200 OK (Complete with all related data)
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "email": "ali@example.com",
  "full_name": "Ali Valiyev",
  
  "branch": "uuid",
  "branch_name": "Toshkent filiali",
  "branch_type": "main",
  
  "role": "teacher",
  "role_display": "O'qituvchi",
  "role_ref": "uuid",
  "role_ref_id": "uuid",
  "role_ref_name": "Matematika o'qituvchisi",
  "role_ref_permissions": {
    "can_view_students": true,
    "can_edit_grades": true
  },
  "title": "Katta o'qituvchi",
  
  "balance": 1500000,
  "balance_status": "positive",
  "salary": 4000000,
  "salary_type": "monthly",
  "monthly_salary": 4000000,
  "hourly_rate": null,
  "per_lesson_rate": null,
  
  "hire_date": "2024-01-15",
  "termination_date": null,
  "employment_type": "full_time",
  "employment_type_display": "To'liq ish kuni",
  "days_employed": 120,
  "years_employed": 0.33,
  "is_active_employment": true,
  
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor tumani",
  "emergency_contact": "+998901111111",
  "notes": "Matematika fanidan mutaxassis",
  
  "recent_transactions": [
    {
      "id": "uuid",
      "transaction_type": "salary",
      "transaction_type_display": "Oylik",
      "amount": 4000000,
      "previous_balance": 1000000,
      "new_balance": 5000000,
      "description": "Yanvar oyi ish haqi",
      "processed_by_name": "Admin User",
      "created_at": "2024-01-31T10:00:00Z"
    }
  ],
  
  "recent_payments": [
    {
      "id": "uuid",
      "month": "2024-01",
      "amount": 4000000,
      "payment_date": "2024-01-31",
      "payment_method": "bank_transfer",
      "payment_method_display": "Bank o'tkazmasi",
      "status": "completed",
      "status_display": "To'landi",
      "processed_by_name": "Admin User"
    }
  ],
  
  "transaction_summary": {
    "total_transactions": 25,
    "total_received": 15000000,
    "total_deducted": 2000000
  },
  
  "payment_summary": {
    "total_payments": 10,
    "total_amount_paid": 40000000,
    "pending_payments": 2
  },
  
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-12-16T08:30:00Z"
}
```

---

### 4. Update Staff

**Endpoint**: `PATCH /api/v1/branches/staff/{id}/`

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

**Endpoint**: `DELETE /api/v1/branches/staff/{id}/`

**Response**: 204 No Content

**Note**: Soft delete - `deleted_at` timestamp is set, data is preserved.

---

### 6. Staff Statistics

**Endpoint**: `GET /api/v1/branches/staff/stats/`

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

**Endpoint**: `POST /api/v1/branches/staff/{id}/add_balance/`

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

**Endpoint**: `POST /api/v1/branches/staff/{id}/pay_salary/`

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
curl -X POST http://localhost:8000/api/v1/branches/staff/ \
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
curl -X POST http://localhost:8000/api/v1/branches/staff/{id}/pay_salary/ \
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
curl -X GET "http://localhost:8000/api/v1/branches/staff/?role=teacher-role-uuid&status=active" \
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
