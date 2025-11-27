# Moliya Tizimi API

Moliya tizimi o'quvchilar va xodimlar uchun balans, tranzaksiyalar, to'lovlar, abonement tariflari va chegirmalarni boshqarish uchun API'lar.

## Umumiy Ma'lumotlar

- **Base URL**: `/api/v1/school/finance/`
- **Authentication**: JWT Token talab qilinadi
- **Permissions**: `CanManageFinance` (Super Admin, Branch Admin)
- **Valyuta**: So'm (butun sonlar, `BigIntegerField`)

## Modellar

### 1. CashRegister (Kassa)
Har bir filial o'ziga bir nechta kassa yaratishi mumkin.

### 2. Transaction (Tranzaksiya)
Barcha moliyaviy operatsiyalar uchun asosiy model.

### 3. StudentBalance (O'quvchi Balansi)
Har bir o'quvchi uchun alohida balans.

### 4. SubscriptionPlan (Abonement Tarifi)
Sinf darajasi bo'yicha abonement tariflari. Agar `branch` bo'sh bo'lsa, umumiy tarif (barcha filiallar uchun).

### 5. Discount (Chegirma)
Foiz yoki aniq summa. Agar `branch` bo'sh bo'lsa, umumiy chegirma (barcha filiallar uchun).

### 6. Payment (To'lov)
O'quvchilarning to'lovlari.

## API Endpoints

### Kassalar (Cash Registers)

#### Kassalar ro'yxati
```
GET /api/v1/school/finance/cash-registers/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `search` (string, optional): Qidirish (nomi, tavsif, manzil)
- `ordering` (string, optional): Tartiblash (`name`, `balance`, `created_at`, `-name`, `-balance`, `-created_at`)

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial nomi",
      "name": "Asosiy kassa",
      "description": "Tavsif",
      "balance": 5000000,
      "is_active": true,
      "location": "Manzil",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Kassa yaratish
```
POST /api/v1/school/finance/cash-registers/
```

**Request Body:**
```json
{
  "branch": "uuid",
  "name": "Asosiy kassa",
  "description": "Tavsif",
  "location": "Manzil",
  "is_active": true
}
```

#### Kassa ma'lumotlari
```
GET /api/v1/school/finance/cash-registers/{id}/
```

#### Kassa yangilash
```
PUT /api/v1/school/finance/cash-registers/{id}/
PATCH /api/v1/school/finance/cash-registers/{id}/
```

#### Kassa o'chirish
```
DELETE /api/v1/school/finance/cash-registers/{id}/
```

---

### Tranzaksiyalar (Transactions)

#### Tranzaksiyalar ro'yxati
```
GET /api/v1/school/finance/transactions/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `transaction_type` (string, optional): Tranzaksiya turi (`income`, `expense`, `transfer`, `payment`, `salary`, `refund`)
- `status` (string, optional): Holat (`pending`, `completed`, `cancelled`, `failed`)
- `cash_register` (UUID, optional): Kassa ID
- `search` (string, optional): Qidirish (tavsif, referens raqami)
- `ordering` (string, optional): Tartiblash (`amount`, `transaction_date`, `created_at`, `-amount`, `-transaction_date`, `-created_at`)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial nomi",
      "cash_register": "uuid",
      "cash_register_name": "Kassa nomi",
      "transaction_type": "payment",
      "transaction_type_display": "To'lov",
      "status": "completed",
      "status_display": "Bajarilgan",
      "amount": 1400000,
      "payment_method": "cash",
      "payment_method_display": "Naqd pul",
      "description": "Tavsif",
      "reference_number": "REF-123",
      "student_profile": "uuid",
      "student_name": "O'quvchi nomi",
      "employee_membership": null,
      "employee_name": null,
      "transaction_date": "2024-01-01T00:00:00Z",
      "metadata": {},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Tranzaksiya yaratish
```
POST /api/v1/school/finance/transactions/
```

**Request Body:**
```json
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "income",
  "amount": 1000000,
  "payment_method": "cash",
  "description": "Tavsif",
  "reference_number": "REF-123",
  "student_profile": "uuid",
  "employee_membership": "uuid",
  "transaction_date": "2024-01-01T00:00:00Z",
  "metadata": {}
}
```

**Transaction Types:**
- `income` - Kirim
- `expense` - Chiqim
- `transfer` - O'tkazma
- `payment` - To'lov
- `salary` - Maosh
- `refund` - Qaytarish

**Status Values:**
- `pending` - Kutilmoqda
- `completed` - Bajarilgan
- `cancelled` - Bekor qilingan
- `failed` - Muvaffaqiyatsiz

**Payment Methods:**
- `cash` - Naqd pul
- `card` - Karta
- `bank_transfer` - Bank o'tkazmasi
- `mobile_payment` - Mobil to'lov
- `other` - Boshqa

---

### O'quvchi Balanslari (Student Balances)

#### O'quvchi balanslari ro'yxati
```
GET /api/v1/school/finance/student-balances/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `search` (string, optional): Qidirish (shaxsiy raqam, ism)
- `ordering` (string, optional): Tartiblash (`balance`, `created_at`, `-balance`, `-created_at`)

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "student_profile": "uuid",
      "student_name": "O'quvchi nomi",
      "student_personal_number": "ST-2024-0001",
      "balance": 500000,
      "notes": "Eslatmalar",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### O'quvchi balansi ma'lumotlari
```
GET /api/v1/school/finance/student-balances/{id}/
```

---

### Abonement Tariflari (Subscription Plans)

#### Abonement tariflari ro'yxati
```
GET /api/v1/school/finance/subscription-plans/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `is_active` (boolean, optional): Faol tariflar
- `search` (string, optional): Qidirish (nomi, tavsif)
- `ordering` (string, optional): Tartiblash (`price`, `grade_level_min`, `grade_level_max`, `created_at`)

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial nomi",
      "name": "1-4 sinflar oylik tarifi",
      "description": "Tavsif",
      "grade_level_min": 1,
      "grade_level_max": 4,
      "grade_level_range": "1-4",
      "period": "monthly",
      "period_display": "Oylik",
      "price": 1400000,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Note:** Agar `branch` `null` bo'lsa, bu umumiy tarif (barcha filiallar uchun).

#### Abonement tarifi yaratish
```
POST /api/v1/school/finance/subscription-plans/
```

**Request Body:**
```json
{
  "branch": "uuid",  // null bo'lsa, umumiy tarif
  "name": "1-4 sinflar oylik tarifi",
  "description": "Tavsif",
  "grade_level_min": 1,
  "grade_level_max": 4,
  "period": "monthly",
  "price": 1400000,
  "is_active": true
}
```

**Period Values:**
- `monthly` - Oylik
- `yearly` - Yillik
- `quarterly` - Choraklik
- `semester` - Semestr

#### Abonement tarifi ma'lumotlari
```
GET /api/v1/school/finance/subscription-plans/{id}/
```

#### Abonement tarifi yangilash
```
PUT /api/v1/school/finance/subscription-plans/{id}/
PATCH /api/v1/school/finance/subscription-plans/{id}/
```

#### Abonement tarifi o'chirish
```
DELETE /api/v1/school/finance/subscription-plans/{id}/
```

---

### Chegirmalar (Discounts)

#### Chegirmalar ro'yxati
```
GET /api/v1/school/finance/discounts/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `is_active` (boolean, optional): Faol chegirmalar
- `search` (string, optional): Qidirish (nomi, tavsif)
- `ordering` (string, optional): Tartiblash (`amount`, `created_at`)

**Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial nomi",
      "name": "Yangi o'quvchilar uchun chegirma",
      "discount_type": "percentage",
      "discount_type_display": "Foiz",
      "amount": 10,
      "discount_display": "10%",
      "is_active": true,
      "valid_from": "2024-01-01T00:00:00Z",
      "valid_until": "2024-12-31T23:59:59Z",
      "description": "Tavsif",
      "conditions": {},
      "is_valid": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Note:** Agar `branch` `null` bo'lsa, bu umumiy chegirma (barcha filiallar uchun).

#### Chegirma yaratish
```
POST /api/v1/school/finance/discounts/
```

**Request Body:**
```json
{
  "branch": "uuid",  // null bo'lsa, umumiy chegirma
  "name": "Yangi o'quvchilar uchun chegirma",
  "discount_type": "percentage",
  "amount": 10,  // Foiz bo'lsa 0-100, summa bo'lsa aniq summa
  "is_active": true,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": "2024-12-31T23:59:59Z",
  "description": "Tavsif",
  "conditions": {}
}
```

**Discount Types:**
- `percentage` - Foiz (0-100)
- `fixed` - Aniq summa

#### Chegirma ma'lumotlari
```
GET /api/v1/school/finance/discounts/{id}/
```

#### Chegirma yangilash
```
PUT /api/v1/school/finance/discounts/{id}/
PATCH /api/v1/school/finance/discounts/{id}/
```

#### Chegirma o'chirish
```
DELETE /api/v1/school/finance/discounts/{id}/
```

---

### To'lovlar (Payments)

#### To'lovlar ro'yxati
```
GET /api/v1/school/finance/payments/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `student_profile` (UUID, optional): O'quvchi ID
- `period_start` (date, optional): Davr boshlanishi
- `period_end` (date, optional): Davr tugashi
- `search` (string, optional): Qidirish (shaxsiy raqam, eslatmalar)
- `ordering` (string, optional): Tartiblash (`final_amount`, `payment_date`, `created_at`)

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "student_profile": "uuid",
      "student_name": "O'quvchi nomi",
      "student_personal_number": "ST-2024-0001",
      "branch": "uuid",
      "branch_name": "Filial nomi",
      "subscription_plan": "uuid",
      "subscription_plan_name": "1-4 sinflar (Oylik) - 1400000 so'm",
      "base_amount": 1400000,
      "discount_amount": 140000,
      "final_amount": 1260000,
      "discount": "uuid",
      "discount_name": "Yangi o'quvchilar uchun chegirma - 10%",
      "payment_method": "cash",
      "payment_method_display": "Naqd pul",
      "period": "monthly",
      "period_display": "Oylik",
      "payment_date": "2024-01-01T00:00:00Z",
      "period_start": "2024-01-01",
      "period_end": "2024-01-31",
      "transaction": "uuid",
      "notes": "Eslatmalar",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### To'lov yaratish
```
POST /api/v1/school/finance/payments/
```

**Request Body:**
```json
{
  "student_profile": "uuid",
  "branch": "uuid",
  "subscription_plan": "uuid",
  "base_amount": 1400000,
  "discount": "uuid",  // optional
  "payment_method": "cash",
  "period": "monthly",
  "payment_date": "2024-01-01T00:00:00Z",
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "cash_register": "uuid",  // required
  "notes": "Eslatmalar"
}
```

**Note:** 
- `cash_register` - Kassa ID (required, Transaction yaratish uchun)
- `discount_amount` va `final_amount` avtomatik hisoblanadi
- Tranzaksiya avtomatik yaratiladi
- O'quvchi balansi avtomatik yangilanadi

#### To'lov ma'lumotlari
```
GET /api/v1/school/finance/payments/{id}/
```

---

### Statistika (Statistics)

#### Moliya statistikasi
```
GET /api/v1/school/finance/statistics/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `start_date` (date, optional): Boshlanish sanasi
- `end_date` (date, optional): Tugash sanasi

**Response:**
```json
{
  "summary": {
    "total_income": 50000000,
    "total_expense": 20000000,
    "net_balance": 30000000,
    "total_cash_balance": 10000000,
    "total_student_balance": 5000000,
    "total_payments": 45000000,
    "payments_count": 30
  },
  "monthly_stats": [
    {
      "month": "2024-01-01T00:00:00Z",
      "income": 15000000,
      "expense": 5000000
    },
    {
      "month": "2024-02-01T00:00:00Z",
      "income": 20000000,
      "expense": 8000000
    }
  ]
}
```

---

## Xatoliklar

### 400 Bad Request
```json
{
  "detail": "Filial ID talab qilinadi."
}
```

### 403 Forbidden
```json
{
  "detail": "Ruxsat yo'q."
}
```

### 404 Not Found
```json
{
  "detail": "Kassa topilmadi yoki bu filialga tegishli emas."
}
```

---

## Eslatmalar

1. **Valyuta**: Barcha summalar so'm (butun sonlar) formatida.
2. **Umumiy Tariflar va Chegirmalar**: Agar `branch` `null` bo'lsa, bu umumiy (barcha filiallar uchun).
3. **Tranzaksiyalar**: Har bir to'lov avtomatik tranzaksiya yaratadi va kassa balansini yangilaydi.
4. **O'quvchi Balansi**: 
   - Har bir to'lov o'quvchi balansini avtomatik yangilaydi
   - `StudentProfile` yaratilganda `StudentBalance` avtomatik yaratiladi (signal orqali)
5. **Chegirmalar**: Chegirmalar foiz yoki aniq summa bo'lishi mumkin. Sana cheklovlari ham mavjud.
6. **Pagination**: Barcha list endpointlar pagination qo'llab-quvvatlaydi (default: 20, max: 100)
7. **Filtering, Search, Ordering**: Barcha list endpointlar filtering, search va ordering qo'llab-quvvatlaydi

## Misol So'rovlar

### 1. Kassa yaratish va to'lov qilish

```bash
# 1. Kassa yaratish
POST /api/v1/school/finance/cash-registers/
{
  "branch": "uuid",
  "name": "Asosiy kassa",
  "description": "Asosiy kassa",
  "location": "1-qavat",
  "is_active": true
}

# 2. Abonement tarifi yaratish
POST /api/v1/school/finance/subscription-plans/
{
  "branch": "uuid",
  "name": "1-4 sinflar oylik tarifi",
  "grade_level_min": 1,
  "grade_level_max": 4,
  "period": "monthly",
  "price": 1400000,
  "is_active": true
}

# 3. Chegirma yaratish (optional)
POST /api/v1/school/finance/discounts/
{
  "branch": "uuid",
  "name": "Yangi o'quvchilar uchun chegirma",
  "discount_type": "percentage",
  "amount": 10,
  "is_active": true,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": "2024-12-31T23:59:59Z"
}

# 4. To'lov yaratish
POST /api/v1/school/finance/payments/
{
  "student_profile": "uuid",
  "branch": "uuid",
  "subscription_plan": "uuid",
  "base_amount": 1400000,
  "discount": "uuid",
  "payment_method": "cash",
  "period": "monthly",
  "payment_date": "2024-01-01T00:00:00Z",
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "cash_register": "uuid",
  "notes": "Yanvar oyi uchun to'lov"
}

# Natija:
# - Transaction avtomatik yaratiladi
# - Kassa balansi yangilanadi
# - O'quvchi balansi yangilanadi
```

### 2. Tranzaksiya yaratish (to'lovdan tashqari)

```bash
# Kirim
POST /api/v1/school/finance/transactions/
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "income",
  "amount": 5000000,
  "payment_method": "cash",
  "description": "Qo'shimcha kirim",
  "reference_number": "REF-001",
  "transaction_date": "2024-01-01T00:00:00Z"
}

# Chiqim (masalan, maosh)
POST /api/v1/school/finance/transactions/
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "salary",
  "amount": 3000000,
  "payment_method": "bank_transfer",
  "description": "O'qituvchi maoshi",
  "employee_membership": "uuid",
  "transaction_date": "2024-01-01T00:00:00Z"
}
```

### 3. Statistika olish

```bash
# Umumiy statistika
GET /api/v1/school/finance/statistics/?branch_id=uuid

# Sana oralig'ida statistika
GET /api/v1/school/finance/statistics/?branch_id=uuid&start_date=2024-01-01&end_date=2024-12-31
```

### 4. Filtering va Search

```bash
# Faol tariflar
GET /api/v1/school/finance/subscription-plans/?branch_id=uuid&is_active=true

# Faol chegirmalar
GET /api/v1/school/finance/discounts/?branch_id=uuid&is_active=true

# O'quvchi to'lovlari
GET /api/v1/school/finance/payments/?branch_id=uuid&student_profile=uuid

# Tranzaksiyalar (kirim)
GET /api/v1/school/finance/transactions/?branch_id=uuid&transaction_type=income&status=completed

# Qidirish
GET /api/v1/school/finance/cash-registers/?branch_id=uuid&search=asosiy

# Tartiblash
GET /api/v1/school/finance/transactions/?branch_id=uuid&ordering=-amount
GET /api/v1/school/finance/payments/?branch_id=uuid&ordering=-payment_date
```

## Avtomatik Yaratiladigan Modellar

Quyidagi modellar signallar orqali avtomatik yaratiladi:

1. **StudentBalance** - `StudentProfile` yaratilganda avtomatik yaratiladi
   - Default balance: 0 so'm
   - Signal: `apps.school.finance.signals.create_student_balance`

2. **BranchSettings** - `Branch` yaratilganda avtomatik yaratiladi
   - Signal: `apps.branch.signals.create_branch_settings`

## Xavfsizlik va Ruxsatlar

- Barcha endpointlar JWT autentifikatsiyani talab qiladi
- `CanManageFinance` permission talab qilinadi (Super Admin, Branch Admin)
- Har bir so'rovda `branch_id` talab qilinadi (JWT claim, header yoki query param)
- Filialga tegishli ma'lumotlar faqat o'sha filial adminlari ko'ra oladi

