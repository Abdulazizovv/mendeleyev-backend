# Xodimlar Maosh API

## Umumiy Ma'lumot

Xodimlar maosh API xodimlarning maoshini hisoblash, to'lash va balansini boshqarish uchun ishlatiladi.

**Base URL:** `/api/v1/branches/staff/`  
**Authentication:** Bearer Token required

---

## Endpoints

### 1. Balansni O'zgartirish (Change Balance) 🆕

Admin tomonidan xodim balansini qo'lda o'zgartirish. Kassa bilan integratsiya qilingan - to'lov amalga oshirilganda avtomatik kassadan pul chiqimi qayd qilinadi.

**POST** `/api/v1/branches/staff/{id}/change-balance/`

**Parameters:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| id | UUID | Path | Xodim ID (BranchMembership) |

**Request Body:**

```json
{
  "transaction_type": "deduction",
  "amount": 3000000,
  "description": "Dekabr oyi maoshi",
  "create_cash_transaction": true,
  "cash_register_id": "uuid",
  "payment_method": "cash",
  "reference": "SAL-2024-12"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| transaction_type | string | Yes | Tranzaksiya turi |
| amount | integer | Yes | Miqdor (so'm, musbat) |
| description | string | Yes | Tavsif |
| create_cash_transaction | boolean | No | Kassa tranzaksiyasi yaratish (default: false) |
| cash_register_id | UUID | No* | Kassa ID (*create_cash_transaction=true bo'lsa majburiy) |
| payment_method | string | No | To'lov usuli (default: cash) |
| reference | string | No | Referens raqami |

**Transaction Types (Balans tranzaksiya turlari):**

| Type | Uzbek | Balans Ta'siri | Kassa Ta'siri |
|------|-------|----------------|---------------|
| `salary_accrual` | Oylik hisoblash | ➕ Qo'shiladi | ➖ Kassadan chiqmaydi |
| `bonus` | Bonus | ➕ Qo'shiladi | ➖ Kassadan chiqmaydi |
| `other` | Boshqa | ➕ Qo'shiladi | ➖ Kassadan chiqmaydi |
| `deduction` | Balansdan chiqarish | ➖ Ayiriladi | ✅ Kassa chiqimi (agar create_cash_transaction=true) |
| `advance` | Avans berish | ➖ Ayiriladi | ✅ Kassa chiqimi (agar create_cash_transaction=true) |
| `fine` | Jarima | ➖ Ayiriladi | ✅ Kassa chiqimi (agar create_cash_transaction=true) |
| `adjustment` | To'g'rilash | ➖ Ayiriladi | ✅ Kassa chiqimi (agar create_cash_transaction=true) |

**Payment Methods:**

- `cash` - Naqd pul
- `bank_transfer` - Bank o'tkazmasi
- `card` - Karta
- `mobile_payment` - Mobil to'lov
- `other` - Boshqa

**Response:** `200 OK`

```json
{
  "staff": {
    "id": "uuid",
    "full_name": "Ali Valiyev",
    "phone_number": "+998901234567",
    "role": "teacher",
    "monthly_salary": 3000000,
    "balance": 0,
    "hire_date": "2024-01-15"
  },
  "balance_transaction_id": "uuid",
  "cash_transaction_id": "uuid",
  "previous_balance": 3000000,
  "new_balance": 0
}
```

**Error Responses:**

```json
// 400 - Validation error
{
  "cash_register_id": ["Cash register ID is required when create_cash_transaction is True"]
}

// 400 - Invalid cash transaction for accrual types
{
  "create_cash_transaction": ["Cannot create cash transaction for salary_accrual. Cash transactions are only for payments (deduction, advance, fine, adjustment)."]
}

// 400 - Service error
{
  "error": "Cash register not found or doesn't belong to staff's branch"
}

// 400 - Amount validation
{
  "error": "Amount must be positive"
}
```

**Use Cases:**

1. **Maosh hisoblash (balansga qo'shish, kassa EMAS):**
```json
{
  "transaction_type": "salary_accrual",
  "amount": 100000,
  "description": "Kunlik maosh - 2024-12-20",
  "create_cash_transaction": false
}
```

2. **Maosh to'lash (kassadan chiqim):**
```json
{
  "transaction_type": "deduction",
  "amount": 3000000,
  "description": "Dekabr oyi maoshi",
  "create_cash_transaction": true,
  "cash_register_id": "uuid",
  "payment_method": "cash"
}
```

3. **Bonus qo'shish (balansga faqat):**
```json
{
  "transaction_type": "bonus",
  "amount": 500000,
  "description": "Yangi yil bonusi",
  "create_cash_transaction": false
}
```

4. **Avans berish (kassadan chiqim):**
```json
{
  "transaction_type": "advance",
  "amount": 1000000,
  "description": "Avans - Dekabr",
  "create_cash_transaction": true,
  "cash_register_id": "uuid",
  "payment_method": "cash"
}
```

5. **Jarima (balansdan ayirish + kassa chiqimi):**
```json
{
  "transaction_type": "fine",
  "amount": 100000,
  "description": "Kechikish uchun jarima",
  "create_cash_transaction": true,
  "cash_register_id": "uuid"
}
```

---

### 2. Balans Qo'shish (Add Balance) ⚠️ DEPRECATED

⚠️ **DEPRECATED:** Ushbu endpoint change-balance bilan almashtirildi.

Xodimning balansiga tranzaksiya qo'shish (bonus, jarima va boshqalar).

**POST** `/api/v1/branches/staff/{id}/add_balance/`

**Request Body:**

```json
{
  "transaction_type": "bonus",
  "amount": 500000,
  "description": "Yangi yil bonusi",
  "reference": "BONUS-2024"
}
```

---

### 3. Maosh To'lash (Pay Salary)

Xodimga maosh to'lovi amalga oshirish.

**POST** `/api/v1/branches/staff/{id}/pay_salary/`

**Request Body:**

```json
{
  "amount": 3000000,
  "payment_date": "2024-12-05",
  "payment_method": "bank_transfer",
  "payment_type": "salary",
  "month": "2024-12-01",
  "notes": "Dekabr oyi to'lovi",
  "reference_number": "PAY-2024-12-001"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | integer | Yes | To'lov miqdori (so'm, musbat) |
| payment_date | date | Yes | To'lov sanasi (YYYY-MM-DD, kelajakda bo'lmasligi kerak) |
| payment_method | string | Yes | To'lov usuli |
| payment_type | string | No | To'lov turi (default: `salary`) |
| month | date | Yes | Qaysi oy uchun to'lov (YYYY-MM-01 formatida) |
| notes | string | No | Qo'shimcha izohlar |
| reference_number | string | No | To'lov referens raqami |

**Payment Methods:**

- `cash` - Naqd
- `bank_transfer` - Bank o'tkazmasi
- `card` - Karta
- `other` - Boshqa

**Payment Types (To'lov turlari):**

- `advance` - **Avans to'lovi** (oy o'rtasida beriladi, balansdan ayiriladi)
- `salary` - **Oylik to'lovi** (oy oxirida to'liq to'lov, balansdan ayiriladi)
- `bonus_payment` - **Bonus to'lovi** (qo'shimcha to'lov, balansdan ayiriladi)
- `other` - **Boshqa to'lov**

**Muhim farq:**
- `salary_accrual` (transaction_type) = Balansga **QO'SHISH** (hisoblash)
- `salary` (payment_type) = Balansdan **AYIRISH** (to'lov)

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "full_name": "Ali Valiyev",
  "balance": 0,
  "payment_info": {
    "payment_id": "payment-uuid",
    "previous_balance": 3000000,
    "new_balance": 0,
    "amount_paid": 3000000
  },
  "recent_payments": [
    {
      "id": "payment-uuid",
      "month": "2024-12-01",
      "month_display": "December 2024",
      "amount": 3000000,
      "payment_date": "2024-12-05",
      "payment_method": "bank_transfer",
      "payment_method_display": "Bank o'tkazmasi",
      "status": "paid",
      "status_display": "To'langan",
      "notes": "Dekabr oyi to'lovi",
      "reference_number": "PAY-2024-12-001",
      "processed_by_name": "Admin User",
      "created_at": "2024-12-18T10:00:00Z"
    }
  ]
}
```

**Error Responses:**

```json
// 400 - Month validation
{
  "month": ["Month must be the first day (YYYY-MM-01)"]
}

// 400 - Payment date validation
{
  "payment_date": ["Payment date cannot be in the future"]
}

// 400 - Month validation
{
  "month": ["Cannot pay salary for future months"]
}

// 400 - Duplicate payment
{
  "error": "Payment already exists for 2024-12"
}
```

---

### 4. Maosh Hisoblash (Calculate Salary)

Oylik maoshni hisoblash (qancha to'lash kerak).

**GET** `/api/v1/branches/staff/{id}/calculate-salary/`

**Parameters:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| id | UUID | Path | Xodim ID |
| year | integer | Query | Yil (optional, default: joriy yil) |
| month | integer | Query | Oy 1-12 (optional, default: joriy oy) |

**Response:** `200 OK`

```json
{
  "success": true,
  "monthly_salary": 3000000,
  "days_in_month": 31,
  "daily_salary": 96774,
  "total_amount": 3000000,
  "year": 2024,
  "month": 12
}
```

**Failed Response:**

```json
{
  "success": false,
  "reason": "Not monthly salary or zero amount"
}
```

**Examples:**

```bash
# Joriy oy uchun hisoblash
GET /api/v1/branches/staff/{id}/calculate-salary/

# Ma'lum oy uchun hisoblash
GET /api/v1/branches/staff/{id}/calculate-salary/?year=2024&month=11
```

---

### 5. Oylik Xulosa (Monthly Summary)

Oylik maosh xulosasi (qancha hisoblangan, qancha to'langan).

**GET** `/api/v1/branches/staff/{id}/monthly-summary/`

**Parameters:**

| Parameter | Type | Location | Description |
|-----------|------|----------|-------------|
| id | UUID | Path | Xodim ID |
| year | integer | Query | Yil (optional, default: joriy yil) |
| month | integer | Query | Oy 1-12 (optional, default: joriy oy) |

**Response:** `200 OK`

```json
{
  "year": 2024,
  "month": 12,
  "total_accrued": 3000000,
  "total_paid": 3000000,
  "balance_change": 0,
  "payments_count": 1,
  "transactions_count": 31
}
```

**Fields:**

- `total_accrued` - Jami hisoblangan summa (balance ga qo'shilgan)
- `total_paid` - Jami to'langan summa (balance dan ayirilgan)
- `balance_change` - Balans o'zgarishi (accrued - paid)
- `payments_count` - To'lovlar soni
- `transactions_count` - Tranzaksiyalar soni

**Examples:**

```bash
# Joriy oy
GET /api/v1/branches/staff/{id}/monthly-summary/

# Noyabr 2024
GET /api/v1/branches/staff/{id}/monthly-summary/?year=2024&month=11
```

---

## 6. Tranzaksiyalar Ro'yxati (Balance Transactions List)

Barcha balans tranzaksiyalarini ko'rish - filter, qidiruv va tartiblash bilan.

**GET** `/api/v1/branches/transactions/`

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| transaction_type | string | Tranzaksiya turi | `salary_accrual`, `bonus`, `deduction`, `advance`, `fine`, `adjustment`, `other` |
| date_from | date | Boshlanish sanasi | `2024-12-01` |
| date_to | date | Tugash sanasi | `2024-12-31` |
| amount_min | integer | Minimal summa | `1000000` |
| amount_max | integer | Maksimal summa | `5000000` |
| reference | string | Referens raqami (qisman) | `PAY-2024` |
| membership | UUID | Xodim ID | `uuid` |
| processed_by | UUID | Kim qayd qilgan | `uuid` |
| search | string | Qidiruv (description, reference, phone, name) | `bonus` |
| ordering | string | Tartiblash | `-created_at`, `amount`, `transaction_type` |
| page | integer | Sahifa raqami | `1` |
| page_size | integer | Sahifadagi elementlar soni | `20` |

**Response:** `200 OK`

```json
{
  "count": 150,
  "next": "http://api/v1/branches/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "staff_id": "membership-uuid",
      "staff_name": "Ali Valiyev",
      "staff_phone": "+998901234567",
      "staff_role": "O'qituvchi",
      "transaction_type": "salary",
      "transaction_type_display": "Maosh",
      "amount": 96774,
      "previous_balance": 0,
      "new_balance": 96774,
      "balance_change": 96774,
      "reference": "DAILY-2024-12-18",
      "description": "Kunlik maosh hisoblash",
      "salary_payment_id": null,
      "salary_payment_month": null,
      "processed_by_name": "System",
      "processed_by_phone": null,
      "created_at": "2024-12-18T00:00:00Z",
      "updated_at": "2024-12-18T00:00:00Z"
    },
    {
      "id": "uuid",
      "staff_id": "membership-uuid",
      "staff_name": "Ali Valiyev",
      "staff_phone": "+998901234567",
      "staff_role": "O'qituvchi",
      "transaction_type": "bonus",
      "transaction_type_display": "Bonus",
      "amount": 500000,
      "previous_balance": 3000000,
      "new_balance": 3500000,
      "balance_change": 500000,
      "reference": "BONUS-2024",
      "description": "Yillik bonus",
      "salary_payment_id": null,
      "salary_payment_month": null,
      "processed_by_name": "Admin User",
      "processed_by_phone": "+998901111111",
      "created_at": "2024-12-15T10:00:00Z",
      "updated_at": "2024-12-15T10:00:00Z"
    }
  ]
}
```

**Filter Examples:**

```bash
# Faqat oylik hisoblash tranzaksiyalari
GET /api/v1/branches/transactions/?transaction_type=salary_accrual

# Faqat bonus tranzaksiyalari
GET /api/v1/branches/transactions/?transaction_type=bonus

# Faqat to'lov (deduction) tranzaksiyalari
GET /api/v1/branches/transactions/?transaction_type=deduction

# Faqat jarimalar
GET /api/v1/branches/transactions/?transaction_type=fine

# Dekabr oyidagi barcha tranzaksiyalar
GET /api/v1/branches/transactions/?date_from=2024-12-01&date_to=2024-12-31

# 1 milliondan katta tranzaksiyalar
GET /api/v1/branches/transactions/?amount_min=1000000

# Ma'lum xodimning tranzaksiyalari
GET /api/v1/branches/transactions/?membership=uuid

# Qidiruv
GET /api/v1/branches/transactions/?search=bonus

# Summa bo'yicha tartiblash
GET /api/v1/branches/transactions/?ordering=-amount

# Kompleks filter
GET /api/v1/branches/transactions/?transaction_type=salary&date_from=2024-12-01&ordering=-created_at&page_size=50
```

---

## 7. Tranzaksiya Tafsilotlari (Transaction Detail)

Bitta tranzaksiyaning to'liq ma'lumotlari.

**GET** `/api/v1/branches/transactions/{id}/`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "staff_id": "membership-uuid",
  "staff_name": "Ali Valiyev",
  "staff_phone": "+998901234567",
  "staff_role": "O'qituvchi",
  "transaction_type": "deduction",
  "transaction_type_display": "Ushlab qolish",
  "amount": 3000000,
  "previous_balance": 3000000,
  "new_balance": 0,
  "balance_change": -3000000,
  "reference": "PAY-2024-12-001",
  "description": "Dekabr oyi maosh to'lovi",
  "salary_payment_id": "payment-uuid",
  "salary_payment_month": "2024-12-01",
  "processed_by_name": "Admin User",
  "processed_by_phone": "+998901111111",
  "created_at": "2024-12-05T10:00:00Z",
  "updated_at": "2024-12-05T10:00:00Z"
}
```

---

## 8. Maosh To'lovlari Ro'yxati (Salary Payments List)

Barcha maosh to'lovlarini ko'rish - filter, qidiruv va tartiblash bilan.

**GET** `/api/v1/branches/payments/`

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| status | string | To'lov holati | `pending`, `paid`, `cancelled` |
| payment_method | string | To'lov usuli | `cash`, `bank_transfer`, `card`, `other` |
| payment_type | string | To'lov turi | `advance`, `salary`, `bonus_payment`, `other` |
| month | date | Aniq oy | `2024-12-01` |
| month_from | date | Oydan | `2024-01-01` |
| month_to | date | Oygacha | `2024-12-01` |
| payment_date_from | date | To'lov sanasidan | `2024-12-01` |
| payment_date_to | date | To'lov sanasigacha | `2024-12-31` |
| amount_min | integer | Minimal summa | `1000000` |
| amount_max | integer | Maksimal summa | `5000000` |
| reference_number | string | To'lov raqami (qisman) | `PAY-2024` |
| membership | UUID | Xodim ID | `uuid` |
| processed_by | UUID | Kim tomonidan | `uuid` |
| search | string | Qidiruv (notes, reference, phone, name) | `dekabr` |
| ordering | string | Tartiblash | `-payment_date`, `-created_at`, `amount`, `month` |
| page | integer | Sahifa raqami | `1` |
| page_size | integer | Sahifadagi elementlar soni | `20` |

**Response:** `200 OK`

```json
{
  "count": 45,
  "next": "http://api/v1/branches/payments/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "staff_id": "membership-uuid",
      "staff_name": "Ali Valiyev",
      "staff_phone": "+998901234567",
      "staff_role": "O'qituvchi",
      "staff_monthly_salary": 3000000,
      "month": "2024-12-01",
      "month_display": "December 2024",
      "amount": 3000000,
      "payment_date": "2024-12-05",
      "payment_method": "bank_transfer",
      "payment_method_display": "Bank o'tkazmasi",
      "status": "paid",
      "status_display": "To'langan",
      "notes": "Dekabr oyi to'lovi",
      "reference_number": "PAY-2024-12-001",
      "transactions_count": 1,
      "processed_by_name": "Admin User",
      "processed_by_phone": "+998901111111",
      "created_at": "2024-12-05T10:00:00Z",
      "updated_at": "2024-12-05T10:00:00Z"
    },
    {
      "id": "uuid",
      "staff_id": "membership-uuid",
      "staff_name": "Vali Toshmatov",
      "staff_phone": "+998902345678",
      "staff_role": "O'qituvchi",
      "staff_monthly_salary": 2500000,
      "month": "2024-12-01",
      "month_display": "December 2024",
      "amount": 2500000,
      "payment_date": "2024-12-06",
      "payment_method": "cash",
      "payment_method_display": "Naqd",
      "status": "paid",
      "status_display": "To'langan",
      "notes": "",
      "reference_number": "",
      "transactions_count": 1,
      "processed_by_name": "Admin User",
      "processed_by_phone": "+998901111111",
      "created_at": "2024-12-06T11:00:00Z",
      "updated_at": "2024-12-06T11:00:00Z"
    }
  ]
}
```

**Filter Examples:**

```bash
# Faqat to'langan to'lovlar
GET /api/v1/branches/payments/?status=paid

# Bank o'tkazmalari
GET /api/v1/branches/payments/?payment_method=bank_transfer

# Faqat avanslar
GET /api/v1/branches/payments/?payment_type=advance

# Faqat oyliklar
GET /api/v1/branches/payments/?payment_type=salary

# Dekabr oyi to'lovlari
GET /api/v1/branches/payments/?month=2024-12-01

# 2024-yil barcha to'lovlari
GET /api/v1/branches/payments/?month_from=2024-01-01&month_to=2024-12-01

# 5-10 dekabr oralig'ida to'langan
GET /api/v1/branches/payments/?payment_date_from=2024-12-05&payment_date_to=2024-12-10

# 2 milliondan katta to'lovlar
GET /api/v1/branches/payments/?amount_min=2000000

# Ma'lum xodimning to'lovlari
GET /api/v1/branches/payments/?membership=uuid

# Qidiruv
GET /api/v1/branches/payments/?search=dekabr

# Summa bo'yicha tartiblash
GET /api/v1/branches/payments/?ordering=-amount

# Kompleks filter
GET /api/v1/branches/payments/?status=paid&payment_method=bank_transfer&month_from=2024-10-01&ordering=-payment_date&page_size=50
```

---

## 9. To'lov Tafsilotlari (Payment Detail)

Bitta to'lovning to'liq ma'lumotlari.

**GET** `/api/v1/branches/payments/{id}/`

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "staff_id": "membership-uuid",
  "staff_name": "Ali Valiyev",
  "staff_phone": "+998901234567",
  "staff_role": "O'qituvchi",
  "staff_monthly_salary": 3000000,
  "month": "2024-12-01",
  "month_display": "December 2024",
  "amount": 3000000,
  "payment_date": "2024-12-05",
  "payment_method": "bank_transfer",
  "payment_method_display": "Bank o'tkazmasi",
  "status": "paid",
  "status_display": "To'langan",
  "notes": "Dekabr oyi to'lovi",
  "reference_number": "PAY-2024-12-001",
  "transactions_count": 1,
  "processed_by_name": "Admin User",
  "processed_by_phone": "+998901111111",
  "created_at": "2024-12-05T10:00:00Z",
  "updated_at": "2024-12-05T10:00:00Z"
}
```

---

## Permissions va Access Control

**Required Permissions:**
- Authentication: Bearer token (required)
- Role: `branch_admin`, `super_admin` (other roles: 403)

**Data Access:**
- **SuperAdmin:** Barcha filiallarning ma'lumotlarini ko'radi
- **BranchAdmin:** Faqat o'z filiallari ma'lumotlarini ko'radi

---

## Pagination

Barcha list endpointlari pagination qo'llab-quvvatlaydi:

```json
{
  "count": 150,
  "next": "http://api/v1/branches/transactions/?page=2",
  "previous": null,
  "results": [...]
}
```

**Default:** `page_size=20`

**Custom page size:**
```bash
GET /api/v1/branches/transactions/?page_size=50
GET /api/v1/branches/payments/?page_size=100
```

---

## Qidiruv (Search)

### Tranzaksiyalar qidiruvi:

Quyidagi fieldlar bo'yicha qidiruv:
- `description` - Tranzaksiya tavsifi
- `reference` - Referens raqami
- `membership__user__phone_number` - Xodim telefoni
- `membership__user__first_name` - Xodim ismi
- `membership__user__last_name` - Xodim familiyasi

**Example:**
```bash
GET /api/v1/branches/transactions/?search=bonus
GET /api/v1/branches/transactions/?search=+998901234567
GET /api/v1/branches/transactions/?search=Ali
```

### To'lovlar qidiruvi:

Quyidagi fieldlar bo'yicha qidiruv:
- `notes` - To'lov izohlari
- `reference_number` - To'lov raqami
- `membership__user__phone_number` - Xodim telefoni
- `membership__user__first_name` - Xodim ismi
- `membership__user__last_name` - Xodim familiyasi

**Example:**
```bash
GET /api/v1/branches/payments/?search=dekabr
GET /api/v1/branches/payments/?search=PAY-2024
GET /api/v1/branches/payments/?search=Vali
```

---

## Tartiblash (Ordering)

### Tranzaksiyalar tartiblashi:

Ordering fields:
- `created_at` - Yaratilgan sana (default: `-created_at`)
- `amount` - Summa
- `transaction_type` - Tranzaksiya turi

**Examples:**
```bash
# Yangilardan eskiga
GET /api/v1/branches/transactions/?ordering=-created_at

# Kattadan kichikka (summa)
GET /api/v1/branches/transactions/?ordering=-amount

# Kichikdan kattaga (summa)
GET /api/v1/branches/transactions/?ordering=amount

# Tranzaksiya turi bo'yicha
GET /api/v1/branches/transactions/?ordering=transaction_type
```

### To'lovlar tartiblashi:

Ordering fields:
- `payment_date` - To'lov sanasi (default: `-payment_date`)
- `created_at` - Yaratilgan sana
- `amount` - Summa
- `month` - Oy

**Examples:**
```bash
# Yangi to'lovlar birinchi
GET /api/v1/branches/payments/?ordering=-payment_date

# Kattadan kichikka (summa)
GET /api/v1/branches/payments/?ordering=-amount

# Oy bo'yicha
GET /api/v1/branches/payments/?ordering=month

# Yaratilgan vaqt bo'yicha
GET /api/v1/branches/payments/?ordering=-created_at
```

---

## Kompleks Filter Misollari

### Use Case 1: Dekabr oyidagi barcha bonus tranzaksiyalar

```bash
GET /api/v1/branches/transactions/?transaction_type=bonus&date_from=2024-12-01&date_to=2024-12-31&ordering=-amount
```

### Use Case 2: Kunlik maosh hisoblashlari (avtomatik)

```bash
GET /api/v1/branches/transactions/?transaction_type=salary_accrual&date_from=2024-12-01&date_to=2024-12-31&ordering=-created_at
```

### Use Case 3: 2024-yil 4-chorakdagi bank to'lovlari

```bash
GET /api/v1/branches/payments/?payment_method=bank_transfer&month_from=2024-10-01&month_to=2024-12-01&status=paid&ordering=-payment_date
```

### Use Case 4: Ma'lum xodimning barcha jarimalar

```bash
GET /api/v1/branches/transactions/?membership=uuid&transaction_type=fine&ordering=-created_at
```

### Use Case 5: 3 milliondan katta avans to'lovlar

```bash
GET /api/v1/branches/payments/?amount_min=3000000&payment_type=advance&status=paid&ordering=-amount
```

### Use Case 6: Ali ismli xodimning barcha maosh to'lovlari

```bash
GET /api/v1/branches/payments/?search=Ali&payment_type=salary&status=paid&ordering=-payment_date
```

---

## Ishlash Prinsipi

### Maosh Hisoblash va To'lash Jarayoni

```
1. Kunlik Avtomatik Hisoblash (Celery Beat)
   └─> Har kuni soat 00:00 da
   └─> Monthly salary / days_in_month = daily salary
   └─> Balance += daily salary
   └─> BalanceTransaction yaratiladi (type=SALARY_ACCRUAL)

2. Oylik Balans
   └─> 31 kunlik oyda: 3,000,000 / 31 = 96,774 * 31 = 3,000,000
   └─> Staff balance: 96,774 + 96,774 + ... = 3,000,000

3. Maosh To'lash
   └─> POST /pay_salary/
   └─> SalaryPayment yaratiladi (type=SALARY yoki ADVANCE)
   └─> Balance -= payment amount
   └─> BalanceTransaction yaratiladi (type=DEDUCTION)
```

### Tranzaksiya Turlari va Maqsadlari

**BALANSGA QO'SHISH (+):**
- `salary_accrual` - **Oylik hisoblash** (kunlik avtomatik, Celery task)
- `bonus` - **Bonus berish** (qo'lda)
- `advance` - **Avans berish** (balansga qo'shish, noyob holatda)

**BALANSDAN AYIRISH (-):**
- `deduction` - **Balansdan chiqarish** (to'lov amalga oshirilganda avtomatik)
- `fine` - **Jarima** (qo'lda)

**IKKI TOMONLAMA:**
- `adjustment` - **To'g'rilash** (+ yoki -, qo'lda)
- `other` - **Boshqa** (+ yoki -, qo'lda)

### To'lov Turlari (Payment Types)

- `advance` - Avans to'lovi (15-kun: balansdan 1M ayiriladi)
- `salary` - Oylik to'lovi (30-kun: balansdan 2M ayiriladi)
- `bonus_payment` - Bonus to'lovi (bonusdan keyin to'lov)
- `other` - Boshqa to'lov

### Balance Mantiq

**Positive Balance = Kompaniya qarzdor**
- Xodimga to'lash kerak
- Balance: +3,000,000 = 3 million to'lash kerak

**Negative Balance = Xodim qarzdor**
- Xodim avans olgan
- Balance: -500,000 = 500k qaytarish kerak

**Zero Balance = Balansda**
- Hammasi to'langan
- Balance: 0

---

## API Workflow Misollari

### Scenario 1: Oddiy Oylik To'lov

**1. Maoshni hisoblash:**
```bash
GET /api/v1/branches/staff/{id}/calculate-salary/?year=2024&month=12
```

**Response:**
```json
{
  "success": true,
  "monthly_salary": 3000000,
  "total_amount": 3000000,
  "days_in_month": 31
}
```

**2. Oylik xulosani ko'rish:**
```bash
GET /api/v1/branches/staff/{id}/monthly-summary/?year=2024&month=12
```

**Response:**
```json
{
  "total_accrued": 3000000,
  "total_paid": 0,
  "balance_change": 3000000
}
```

**3. To'lov amalga oshirish:**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 3000000,
  "payment_date": "2024-12-05",
  "payment_method": "bank_transfer",
  "month": "2024-12-01"
}
```

---

### Scenario 2: Avans va Oylik (Bir oyda ikki marta to'lov)

**1. 15-kun: Balance ~1,500,000**

**2. Avans berish (1 million):**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 1000000,
  "payment_type": "advance",
  "month": "2024-12-01",
  "payment_date": "2024-12-15",
  "payment_method": "cash",
  "notes": "Avans - 15 dekabr"
}
```

**3. Balance: ~500,000** (avtomatik hisoblash davom etadi)

**4. Oy oxiri: Balance ~1,500,000** (31 kunlik hisob - avans)

**5. Qolgan qismni to'lash:**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 1500000,
  "payment_type": "salary",
  "month": "2024-12-01",
  "payment_date": "2024-12-30",
  "payment_method": "bank_transfer",
  "notes": "Oylik - qolgan qism"
}
```

**6. Natija: Bir oy uchun 2 ta to'lov:**
- Avans: 1,000,000 so'm (15-dekabr)
- Oylik: 1,500,000 so'm (30-dekabr)
- Jami: 2,500,000 so'm

---

### Scenario 3: Qisman To'lov

**1. Balance: 3,000,000**

**2. Qisman to'lov (2 million):**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 2000000,
  "month": "2024-12-01",
  "payment_date": "2024-12-05",
  "payment_method": "cash"
}
```

**3. Yangi balance: 1,000,000** (hali to'lanmagan)

**4. Qolgan qismni to'lash kerak:**
```bash
# Balansni ko'rish
GET /api/v1/branches/staff/{id}/

# Balance: 1,000,000 ko'rsatadi
```

---

### Scenario 3: Bonus Qo'shish

**1. Maosh hisoblangan: 3,000,000**

**2. Bonus qo'shish:**
```bash
POST /api/v1/branches/staff/{id}/add_balance/
{
  "transaction_type": "bonus",
  "amount": 500000,
  "description": "Yillik bonus"
}
```

**3. Balance: 3,500,000**

**4. Umumiy to'lash:**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 3500000,
  "month": "2024-12-01",
  "payment_date": "2024-12-10",
  "payment_method": "bank_transfer"
}
```

---

### Scenario 4: Avans Berish

**1. 15-kun, balance: ~1,500,000**

**2. Avans berish (1 million):**
```bash
POST /api/v1/branches/staff/{id}/pay_salary/
{
  "amount": 1000000,
  "month": "2024-12-01",
  "payment_date": "2024-12-15",
  "payment_method": "cash",
  "notes": "Avans"
}
```

**3. Balance: ~500,000** (avtomatik hisoblash davom etadi)

**4. Oy oxirida balansni to'lash**

---

## Validatsiya Qoidalari

### Amount Validation

```
amount > 0
```

**Error:**
```json
{
  "amount": ["Amount must be greater than 0"]
}
```

### Payment Date Validation

```
payment_date <= today()
```

**Error:**
```json
{
  "payment_date": ["Payment date cannot be in the future"]
}
```

### Month Format Validation

```
month.day == 1  // Must be first day
month <= today()  // Cannot be future
```

**Error:**
```json
{
  "month": ["Month must be the first day (YYYY-MM-01)"]
}
```

### Duplicate Payment Check

```
Check: SalaryPayment exists for same month with status=PAID
```

**Error:**
```json
{
  "error": "Payment already exists for 2024-12"
}
```

---

## Frontend Integratsiya

### React Example - Maosh To'lash

```javascript
const paySalary = async (staffId, paymentData) => {
  try {
    const response = await fetch(
      `/api/v1/branches/staff/${staffId}/pay_salary/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: paymentData.amount,
          payment_date: paymentData.date,
          payment_method: paymentData.method,
          month: `${paymentData.year}-${paymentData.month}-01`,
          notes: paymentData.notes,
        }),
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      console.log('Payment successful:', data.payment_info);
      return data;
    } else {
      console.error('Payment failed:', data.error);
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// Foydalanish
await paySalary('staff-uuid', {
  amount: 3000000,
  date: '2024-12-05',
  method: 'bank_transfer',
  year: 2024,
  month: 12,
  notes: 'Dekabr oyi'
});
```

### Vue Example - Oylik Xulosa

```javascript
const fetchMonthlySummary = async (staffId, year, month) => {
  const response = await fetch(
    `/api/v1/branches/staff/${staffId}/monthly-summary/?year=${year}&month=${month}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
  
  return response.json();
};

// Foydalanish
const summary = await fetchMonthlySummary('staff-uuid', 2024, 12);

console.log(`Hisoblangan: ${summary.total_accrued:,} so'm`);
console.log(`To'langan: ${summary.total_paid:,} so'm`);
console.log(`Qoldiq: ${summary.balance_change:,} so'm`);
```

---

## Muhim Eslatmalar

1. **Atomic Transactions:**
   - Barcha balance o'zgarishlari atomic
   - select_for_update() ishlatiladi
   - Race condition yo'q

2. **Audit Trail:**
   - Har bir tranzaksiya saqlanadi
   - previous_balance va new_balance
   - processed_by ma'lumoti

3. **Kassa Integratsiyasi:** 🆕
   - change-balance API orqali kassadan pul chiqimi avtomatik qayd qilinadi
   - create_cash_transaction=true bo'lganda:
     - apps.school.finance.Transaction yaratiladi
     - Kassa balansi avtomatik yangilanadi
     - expense_category=SALARY bo'ladi
   - deduction, advance, fine, adjustment turlari uchun kassa tranzaksiyasi yaratiladi (haqiqiy to'lovlar)

4. **Multiple Payments per Month:**
   - Bir oyda bir necha marta to'lov qilish mumkin
   - Masalan: avans (15-kun) + oylik (30-kun)
   - payment_type orqali farqlanadi: `advance`, `salary`, `bonus_payment`
   - Unique constraint olib tashlangan (migration 0015)

5. **Balance Calculation:**
   - Kunlik avtomatik hisoblash (Celery)
   - Oylik total = daily * days_in_month
   - Prorated calculation qo'llab-quvvatlanadi

6. **Permissions:**
   - Faqat admin va branch admin
   - HasBranchRole permission kerak

7. **Best Practices:**
   - Maosh to'lashda har doim create_cash_transaction=true qiling
   - cash_register_id ni to'g'ri tanlang (xodimning branchiga tegishli bo'lishi kerak)
   - description ni aniq va tushunarli yozing
   - reference ni unique qiling (masalan: SAL-2024-12-001)

---

## API Summary

| Endpoint | Method | Maqsad | Kassa Integratsiya |
|----------|--------|--------|-------------------|
| `/change-balance/` | POST | Balansni o'zgartirish (universal) | ✅ Mavjud |
| `/pay_salary/` | POST | Maosh to'lash (SalaryPayment yaratish) | ❌ Yo'q |
| `/add_balance/` | POST | ⚠️ DEPRECATED | ❌ Yo'q |
| `/calculate-salary/` | GET | Maosh hisoblash (faqat ko'rish) | ❌ Yo'q |
| `/monthly-summary/` | GET | Oylik xulosa | ❌ Yo'q |
| `/transactions/` | GET | Tranzaksiyalar ro'yxati | ❌ Yo'q |
| `/payments/` | GET | To'lovlar ro'yxati | ❌ Yo'q |

---

**Versiya:** 3.0  
**Sana:** 2024-12-20  
**Holat:** Production Ready  
**O'zgarishlar:** Kassa integratsiyasi, change-balance API, add-salary olib tashlandi
