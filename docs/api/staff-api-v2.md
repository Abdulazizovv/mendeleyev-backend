# Staff Management API v2

**Base URL:** `/api/v1/branches/staff/`  
**Authentication:** Bearer Token required  
**Updated:** 2024-12-16

---

## 📋 Overview

Staff management API built on `BranchMembership` model with clear role hierarchy:

### Role System

**BranchRole** (CharField choices) - Basic role types:
- `super_admin` - Super Admin
- `branch_admin` - Filial admini  
- `teacher` - O'qituvchi
- `student` - O'quvchi (excluded from staff API)
- `parent` - Ota-ona (excluded from staff API)
- `other` - Boshqa xodim (requires role_ref)

**Role** (ForeignKey model) - Detailed custom roles:
- Flexible permissions (JSON)
- Branch-specific or global
- Salary guidance (optional)
- Examples: "Matematika o'qituvchisi", "Qorovul", "Oshpaz", etc.

### Key Changes in v2

✅ **Soft Delete Fixed** - `unique_together` removed, no more unique constraint errors  
✅ **Role Clarity** - Clear distinction between BranchRole and Role model  
✅ **Enhanced Stats** - Comprehensive statistics with financial data  
✅ **Validation** - Prevents duplicate active memberships  
✅ **Complete Data** - Detail API includes everything

---

## 🔍 API Endpoints

### 1. List Staff

**GET** `/api/v1/branches/staff/`

Returns compact list of staff members (excludes students and parents).

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branch` | UUID | Filter by branch |
| `role` | string | Filter by BranchRole (teacher, branch_admin, etc) |
| `role_ref` | UUID | Filter by custom Role model |
| `employment_type` | string | Filter: full_time, part_time, contract |
| `status` | string | Filter: active, terminated |
| `search` | string | Search by name, phone, passport |
| `ordering` | string | Sort: hire_date, monthly_salary, balance |
| `page` | number | Page number |
| `page_size` | number | Items per page |

**Response:** `200 OK`

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

**Examples:**

```bash
# Active staff only
GET /api/v1/branches/staff/?status=active

# Teachers with custom role
GET /api/v1/branches/staff/?role=teacher&role_ref=uuid

# Search by name
GET /api/v1/branches/staff/?search=Ali

# Sort by salary
GET /api/v1/branches/staff/?ordering=-monthly_salary
```

---

### 2. Create Staff

**POST** `/api/v1/branches/staff/`

Creates new user (if doesn't exist) and staff membership.

**Request Body:**

```json
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "email": "ali@example.com",
  "password": "securepass123",
  
  "branch_id": "uuid",
  "role": "teacher",
  "role_ref_id": "uuid",
  "title": "Katta o'qituvchi",
  
  "monthly_salary": 4000000,
  "salary_type": "monthly",
  "hire_date": "2024-01-15",
  "employment_type": "full_time",
  
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor",
  "emergency_contact": "+998901111111",
  "notes": {}
}
```

**Required Fields:**
- `phone_number` - User phone (unique)
- `first_name` - First name
- `last_name` - Last name
- `branch_id` - Branch UUID
- `role` - BranchRole choice

**Optional Fields:**
- `email` - Email address
- `password` - If omitted, auto-generated
- `role_ref_id` - Custom Role UUID (required if role="other")
- `title` - Job title
- `monthly_salary` - Default: 0
- `salary_type` - Default: "monthly"
- `hire_date` - Hire date
- `employment_type` - Default: "full_time"
- Personal info fields

**Validation:**
- Phone number must be unique for new users
- Cannot create duplicate active membership (user + branch)
- If `role="other"`, `role_ref_id` is required

**Response:** `201 Created`

Returns `StaffDetailSerializer` with all created data.

**Errors:**

```json
// Duplicate membership
{
  "phone_number": ["Bu foydalanuvchi allaqachon uuid filialida mavjud."]
}

// Missing role_ref
{
  "role_ref_id": ["role=\"other\" bo'lganda role_ref_id majburiy."]
}
```

---

### 3. Get Staff Details

**GET** `/api/v1/branches/staff/{id}/`

Returns complete staff profile with all related data.

**Response:** `200 OK`

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
  "branch_type": "school",
  
  "role": "teacher",
  "role_display": "O'qituvchi",
  "role_ref": "uuid",
  "role_ref_id": "uuid",
  "role_ref_name": "Matematika o'qituvchisi",
  "role_ref_permissions": {
    "academic": ["view_grades", "edit_attendance"],
    "finance": ["view_salary"]
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
  "days_employed": 335,
  "years_employed": 0.92,
  "is_active_employment": true,
  
  "passport_serial": "AB",
  "passport_number": "1234567",
  "address": "Toshkent sh., Chilonzor tumani",
  "emergency_contact": "+998901111111",
  "notes": {},
  
  "recent_transactions": [
    {
      "id": "uuid",
      "transaction_type": "salary",
      "transaction_type_display": "Oylik",
      "amount": 4000000,
      "previous_balance": 1000000,
      "new_balance": 5000000,
      "description": "Dekabr oyi ish haqi",
      "processed_by_name": "Admin User",
      "created_at": "2024-12-01T10:00:00Z"
    }
  ],
  
  "recent_payments": [
    {
      "id": "uuid",
      "month": "2024-12",
      "amount": 4000000,
      "payment_date": "2024-12-01",
      "payment_method": "bank_transfer",
      "payment_method_display": "Bank o'tkazmasi",
      "status": "completed",
      "status_display": "To'landi",
      "processed_by_name": "Admin User",
      "created_at": "2024-12-01T10:00:00Z"
    }
  ],
  
  "transaction_summary": {
    "total_transactions": 25,
    "total_received": 100000000,
    "total_deducted": 5000000
  },
  
  "payment_summary": {
    "total_payments": 12,
    "total_amount_paid": 48000000,
    "pending_payments": 1
  },
  
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Includes:**
- Complete user information
- Branch details
- Role and permissions
- Financial data
- Employment history
- Last 10 transactions
- Last 10 payments
- Summary statistics

---

### 4. Update Staff

**PATCH** `/api/v1/branches/staff/{id}/`

Partial update of staff member.

**Request Body:**

```json
{
  "monthly_salary": 4500000,
  "title": "Bosh o'qituvchi",
  "address": "Yangi manzil",
  "notes": {"performance": "excellent"}
}
```

**Updatable Fields:**
- Role and title
- Salary information
- Employment details
- Personal information
- Notes

**Response:** `200 OK`

Returns updated `StaffDetailSerializer`.

**Terminate Employment:**

```json
{
  "termination_date": "2024-12-31"
}
```

---

### 5. Delete Staff (Soft Delete)

**DELETE** `/api/v1/branches/staff/{id}/`

Soft deletes staff membership (sets `deleted_at` timestamp).

**Response:** `204 No Content`

**Note:** Data is preserved. User can be re-added to branch later.

---

### 6. Staff Statistics

**GET** `/api/v1/branches/staff/stats/`

Xodimlar haqida to'liq statistik ma'lumotlar.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `branch` | UUID | Filial ID (ko'rsatilmasa barcha filiallar) |

**Response:** `200 OK`

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
    {"role": "teacher", "count": 15},
    {"role": "branch_admin", "count": 3},
    {"role": "other", "count": 4}
  ],
  
  "by_custom_role": [
    {
      "role_ref__id": "uuid",
      "role_ref__name": "Matematika o'qituvchisi",
      "count": 5
    }
  ],
  
  "average_salary": 3850000.00,
  "total_salary_budget": 88000000,
  "max_salary": 6000000,
  "min_salary": 2000000,
  
  "total_paid": 156000000,
  "total_pending": 12500000,
  "paid_payments_count": 45,
  "pending_payments_count": 8,
  
  "total_balance": -2500000
}
```

**Ma'lumotlar:**
- **total_staff**: Jami xodimlar (faol + ishdan bo'shatilgan)
- **active_staff**: Hozir ishlab turgan xodimlar
- **terminated_staff**: Ishdan bo'shatilgan xodimlar
- **by_employment_type**: Ish turi bo'yicha (to'liq/yarim vaqt)
- **by_role**: Asosiy lavozim bo'yicha
- **by_custom_role**: Maxsus lavozimlar bo'yicha
- **average_salary**: O'rtacha oylik maosh
- **total_salary_budget**: Oylik umumiy maosh byudjeti
- **max_salary**: Eng yuqori maosh
- **min_salary**: Eng past maosh
- **total_paid**: Jami to'langan summa
- **total_pending**: Kutilayotgan to'lovlar
- **paid_payments_count**: To'langan to'lovlar soni
- **pending_payments_count**: Kutilayotgan to'lovlar soni
- **total_balance**: Umumiy balans (manfiy = kompaniya qarzdor)

---

### 7. Add Balance Transaction

**POST** `/api/v1/branches/staff/{id}/add_balance/`

Adds financial transaction to staff balance.

**Request Body:**

```json
{
  "amount": 500000,
  "transaction_type": "bonus",
  "description": "Yangi yil bonusi"
}
```

**Transaction Types:**
- `salary` - Monthly salary
- `bonus` - Performance bonus
- `deduction` - Deduction from balance
- `advance` - Salary advance
- `fine` - Penalty/fine
- `refund` - Refund

**Response:** `200 OK`

Returns updated `StaffDetailSerializer` with new balance.

**Examples:**

```json
// Monthly salary
{
  "amount": 4000000,
  "transaction_type": "salary",
  "description": "Dekabr oyi ish haqi"
}

// Bonus
{
  "amount": 1000000,
  "transaction_type": "bonus",
  "description": "Yillik bonus"
}

// Deduction
{
  "amount": 200000,
  "transaction_type": "deduction",
  "description": "Telefon to'lovi"
}
```

---

### 8. Record Salary Payment

**POST** `/api/v1/branches/staff/{id}/pay_salary/`

Records salary payment for staff member.

**Request Body:**

```json
{
  "amount": 4000000,
  "payment_method": "bank_transfer",
  "payment_status": "completed",
  "notes": "Dekabr oyi ish haqi"
}
```

**Payment Methods:**
- `cash` - Naqd
- `bank_transfer` - Bank o'tkazmasi
- `card` - Karta

**Payment Status:**
- `pending` - Kutilmoqda
- `completed` - To'landi
- `failed` - Xato

**Response:** `200 OK`

Returns updated `StaffDetailSerializer`.

---

## 🔧 Role System Explained

### BranchRole vs Role Model

**When to use BranchRole (CharField):**
- Basic categorization
- System-level permissions
- Quick filtering
- Legacy compatibility

**When to use Role Model (ForeignKey):**
- Detailed job titles
- Custom permissions
- Salary guidance
- Branch-specific roles

**Best Practice:**

```json
{
  "role": "teacher",              // BranchRole - basic type
  "role_ref_id": "uuid",          // Role - detailed "Matematika o'qituvchisi"
  "title": "Katta o'qituvchi"     // Local title
}
```

**Example Roles:**

```json
// Teacher with custom role
{
  "role": "teacher",
  "role_ref_id": "math-teacher-uuid",
  "role_ref_name": "Matematika o'qituvchisi",
  "role_ref_permissions": {
    "academic": ["view_grades", "edit_grades", "manage_homework"],
    "attendance": ["view", "edit"]
  }
}

// Other staff (guard, cook, etc)
{
  "role": "other",
  "role_ref_id": "guard-uuid",
  "role_ref_name": "Qorovul",
  "role_ref_permissions": {
    "security": ["access_gates", "view_cameras"],
    "schedule": ["view_own_schedule"]
  }
}

// Branch admin
{
  "role": "branch_admin",
  "role_ref_id": null,
  "title": "Filial direktori"
}
```

---

## 🔒 Permissions

All endpoints require:
- `IsAuthenticated` - Valid bearer token
- `HasBranchRole` - User must have role in relevant branch

**Access Levels:**
- **SuperAdmin**: Full access to all branches
- **BranchAdmin**: Full access to managed branches
- **Staff**: Read-only access to own data

---

## ✅ Validation Rules

### Creating Staff

1. **Phone uniqueness**: New user requires unique phone
2. **No duplicate active membership**: Same user + branch combination
3. **Role consistency**: If `role="other"`, `role_ref_id` required
4. **Salary validation**: Optional min/max from Role model

### Updating Staff

1. **Cannot change**: `user`, `branch`
2. **Termination**: Set `termination_date` to terminate
3. **Balance**: Use `/add_balance/` endpoint, not direct update

### Soft Delete

1. **Preserves data**: All information kept
2. **No unique constraint**: Can re-create after delete
3. **Filters**: Automatically excluded from queries (`deleted_at__isnull=True`)

---

## 🐛 Common Issues & Solutions

### Issue 1: Unique Constraint Error

**Problem:** Getting unique constraint error when creating staff

**Solution:** 
- Check for existing active membership: `GET /api/v1/branches/staff/?branch=uuid&search=phone`
- Delete old membership if exists: `DELETE /api/v1/branches/staff/{id}/`
- Then create new one

### Issue 2: role="other" without role_ref_id

**Problem:** Validation error when creating "other" staff

**Solution:**
- Create Role first: `POST /api/v1/branches/roles/`
- Use returned UUID in `role_ref_id`

### Issue 3: Students/Parents in Staff API

**Problem:** Students or parents appearing in staff list

**Solution:**
- API automatically filters them out
- Uses: `.exclude(role__in=[BranchRole.STUDENT, BranchRole.PARENT])`
- If still appearing, check `role` field value

---

## 📊 Response Size Comparison

### List Endpoint

- **Fields**: 13 essential fields
- **Size**: ~60-70% smaller than full data
- **Use for**: Tables, cards, quick overview

### Detail Endpoint

- **Fields**: 35+ fields + nested data
- **Size**: Complete profile
- **Use for**: Profile pages, detailed view

---

## 🔄 Migration Notes

### From v1 to v2

1. **unique_together removed** - No more conflicts
2. **Stats enhanced** - More financial data
3. **Validation added** - Prevents duplicates
4. **Role clarity** - Better documentation

### Database Changes

```bash
# Applied migration
docker compose exec django python manage.py migrate

# Migration: 0013_remove_membership_unique_constraint
```

---

## 📚 Related Documentation

- Role Management API: `/docs/api/roles.md`
- Branch Management: `/docs/api/branches.md`
- Permissions: `/docs/permissions-rbac.md`

---

## 🚀 Quick Examples

### Create Teacher

```bash
curl -X POST http://localhost:8000/api/v1/branches/staff/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+998901234567",
    "first_name": "Ali",
    "last_name": "Valiyev",
    "branch_id": "branch-uuid",
    "role": "teacher",
    "role_ref_id": "math-teacher-role-uuid",
    "title": "Katta o'\''qituvchi",
    "monthly_salary": 4000000,
    "hire_date": "2024-01-15",
    "employment_type": "full_time"
  }'
```

### Get Staff Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/branches/staff/stats/?branch=uuid" \
  -H "Authorization: Bearer TOKEN"
```

### Add Bonus

```bash
curl -X POST http://localhost:8000/api/v1/branches/staff/{id}/add_balance/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000000,
    "transaction_type": "bonus",
    "description": "Yillik bonus"
  }'
```

---

**Version:** 2.0  
**Last Updated:** 2024-12-16  
**Status:** Production Ready
