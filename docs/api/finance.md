# Moliya Tizimi API

Moliya tizimi o'quvchilar va xodimlar uchun balans, tranzaksiyalar, to'lovlar, abonement tariflari, chegirmalar va dinamik kategoriyalarni boshqarish uchun API'lar.

## Umumiy Ma'lumotlar

- **Base URL**: `/api/v1/school/finance/`
- **Authentication**: JWT Token talab qilinadi
- **Permissions**: `CanManageFinance`, `CanViewFinanceReports`, `CanManageCategories`
- **Valyuta**: So'm (butun sonlar, `BigIntegerField`)

## Yangiliklar (2026-01-02)

✅ **Test Coverage (26 ta yangi test):**
- **Race Conditions** (5 tests): Concurrent operations, StudentBalance thread-safety, select_for_update() locks
- **Privacy/Isolation** (4 tests): Branch data isolation, global categories, discount validation
- **Permissions** (7 tests): CAN_AUTO_APPROVE, CAN_APPROVE_MANUALLY, auto-approval logic
- **Export Functionality** (10 tests): Excel export API, Celery tasks, task status tracking

✅ **Critical Bug Fixes:**
- **StudentBalance.subtract_amount()**: Race condition fix - qo'shildi select_for_update() lock
- **BaseFinanceView**: `_get_user_membership()` methodi qo'shildi
- **Permissions**: `role_model` → `role_ref` ga o'zgartirildi (BranchMembership)
- **Auto-Approval Logic**: Permission-based transaction approval (Branch Admin, Super Admin, Accountant)

✅ **Excel Export System:**
- Celery task orqali asinxron export
- Transaction va Payment export endpoints
- Task status tracking (PENDING, SUCCESS, FAILURE)
- File URL generation va download

## Yangiliklar (2025-12-22)

✅ **Dinamik Kategoriyalar Tizimi:**
- 28 ta default global kategoriya (10 kirim, 18 chiqim)
- Branch-specific kategoriyalar yaratish imkoniyati
- Ierarxik tuzilma (parent/child relationships)
- Transaction modelda category FK field

✅ **Ruxsatlar Tizimi:**
- `VIEW_FINANCE_REPORTS` - Hisobotlarni ko'rish
- `MANAGE_FINANCE` - Moliyani boshqarish
- `MANAGE_CATEGORIES` - Kategoriyalarni boshqarish
- `CAN_AUTO_APPROVE` - Avtomatik tasdiq ruxsati
- `CAN_APPROVE_MANUALLY` - Manual tasdiq ruxsati

✅ **Bug Fixes:**
- Permission classes: MultipleObjectsReturned xatosi tuzatildi
- Middleware: Branch isolation yangilandi
- Role field: select_for_related xatosi tuzatildi
- StudentBalance race condition: select_for_update() qo'shildi

✅ **Auto Branch Assignment:**
- Obyekt yaratishda `branch` berilmasa, avtomatik `request.branch` dan olinadi
- `X-Branch-Id` header yoki JWT tokendan branch aniqlash
- Super admin global obyektlar (branch=null) yaratishi mumkin

## Modellar

### 1. FinanceCategory (Moliya Kategoriyasi) 🆕
Dinamik kategoriyalar tizimi. Global va branch-specific kategoriyalar.

**Xususiyatlar:**
- Global kategoriyalar (branch=null): 28 ta default
- Filial kategoriyalari: Har bir filial o'z kategoriyalarini yaratishi mumkin
- Ierarxiya: parent/child relationships
- Unique constraint: (branch, type, code)

### 2. CashRegister (Kassa)
Har bir filial o'ziga bir nechta kassa yaratishi mumkin.

### 3. Transaction (Tranzaksiya)
Barcha moliyaviy operatsiyalar uchun asosiy model.

**Yangi field:** `category` (ForeignKey to FinanceCategory)

### 4. StudentBalance (O'quvchi Balansi)
Har bir o'quvchi uchun alohida balans.

### 5. SubscriptionPlan (Abonement Tarifi)
Sinf darajasi bo'yicha abonement tariflari. Agar `branch` bo'sh bo'lsa, umumiy tarif (barcha filiallar uchun).

### 6. Discount (Chegirma)
Foiz yoki aniq summa. Agar `branch` bo'sh bo'lsa, umumiy chegirma (barcha filiallar uchun).

### 7. Payment (To'lov)
O'quvchilarning to'lovlari.

## API Endpoints

### 🆕 Kategoriyalar (Categories)

> **To'liq dokumentatsiya:** [finance-category-api.md](../finance-category-api.md)

#### Kategoriyalar ro'yxati
```
GET /api/v1/school/finance/categories/
```

**Query Parameters:**
- `type` (string, optional): income | expense
- `is_active` (boolean, optional): true | false
- `is_global` (boolean, optional): true | false
- `parent` (UUID, optional): Ota kategoriya ID
- `search` (string, optional): Qidirish (nom, kod)

**Response:**
```json
{
  "count": 30,
  "results": [
    {
      "id": "uuid",
      "branch": null,
      "branch_name": "Global",
      "type": "income",
      "code": "student_payment",
      "name": "O'quvchi to'lovi",
      "description": "O'quvchilardan tushadigan asosiy to'lovlar",
      "parent": null,
      "parent_name": null,
      "subcategories_count": 0,
      "is_active": true,
      "created_at": "2025-12-22T10:00:00Z",
      "updated_at": "2025-12-22T10:00:00Z"
    }
  ]
}
```

#### Kategoriya yaratish
```
POST /api/v1/school/finance/categories/
```

**Request Body:**
```json
{
  "name": "Maxsus xarajat",
  "type": "expense",
  "code": "custom_expense",
  "description": "Filial uchun maxsus xarajat",
  "parent": null,
  "is_active": true
}
```

**Permissions:**
- Super Admin: Global va barcha filial kategoriyalarini boshqaradi
- Branch Admin: Faqat o'z filiali kategoriyalarini boshqaradi
- Xodim: `manage_categories` ruxsati kerak

---

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
- `category` (UUID, optional): Kategoriya ID 🆕
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
      "category": "uuid",
      "category_name": "O'quvchi to'lovi",
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
  "category": "uuid",
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

**Validatsiya:**
- ✅ `category.type` va `transaction_type` mos kelishi kerak (income → income, expense → expense)
- ✅ Kategoriya aktiv bo'lishi kerak (`is_active=true`)
- ✅ Kategoriya filialga tegishli yoki global bo'lishi kerak

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
      "student_personal_number": "TAS-24-0001",
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
      "student_personal_number": "TAS-24-0001",
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

### 📊 Excel Export (Yangi!)

#### Export Tranzaksiyalar
```
POST /api/v1/school/finance/export/transactions/
```

**Ruxsatlar:**
- **Branch Admin**: Faqat o'z filialidan export olishi mumkin. Branch ID avtomatik JWT/membership dan olinadi.
- **Super Admin**: Istalgan filialdan export olishi mumkin. Branch ID header yoki body da berilishi kerak.

**Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "X-Branch-Id": "uuid"  // Super Admin uchun REQUIRED. Branch Admin uchun ignore qilinadi.
}
```

**Request Body:**
```json
{
  "branch_id": "uuid",       // Super Admin uchun (optional, header dan ham olish mumkin)
  "transaction_type": "income",
  "status": "completed",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "cash_register": "uuid",
  "category": "uuid",
  "student_profile": "uuid"
}
```

**Frontend Misol:**
```javascript
// Branch Admin uchun (branch_id kerak emas)
const response = await fetch('/api/v1/school/finance/export/transactions/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${branchAdminToken}`,
    'Content-Type': 'application/json'
    // X-Branch-Id kerak emas - JWT dan avtomatik olinadi
  },
  body: JSON.stringify({
    date_from: '2026-01-01',
    date_to: '2026-01-04'
  })
});

// Super Admin uchun (istalgan branch)
const response = await fetch('/api/v1/school/finance/export/transactions/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${superAdminToken}`,
    'X-Branch-Id': branchId,  // Qaysi branchdan export olish
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    date_from: '2026-01-01',
    date_to: '2026-01-04'
  })
});
```

**Response:**
```json
{
  "message": "Export task boshlandi",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

#### Export To'lovlar
```
POST /api/v1/school/finance/export/payments/
```

**Request Body:**
```json
{
  "student_profile": "uuid",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "period": "2025-12"
}
```

#### Task Statusini Tekshirish
```
GET /api/v1/school/finance/export/task-status/{task_id}/
```

**Response (SUCCESS):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "message": "Export muvaffaqiyatli",
  "file_url": "/media/exports/finance/transactions_20260102_143022.xlsx",
  "filename": "transactions_20260102_143022.xlsx",
  "records_count": 523
}
```

**Eslatma:**
- Maksimal 50,000 ta yozuvni export qiladi
- Celery task orqali asinxron bajariladi
- Excel fayl avtomatik formatlanadi (bold headers, ranglar, auto-width)

**Troubleshooting:**

Agar `"error": "Export qilish uchun ma'lumot topilmadi"` xatoligi chiqsa:

1. **Branch to'g'ri tanlanganini tekshiring** - `X-Branch-Id` headerida tranzaksiya bor branchni yuboring
2. **Sana oralig'ini kengaytiring** - Tranzaksiyalar belgilangan sana oralig'ida bo'lishi kerak
3. **Filterlarni olib tashlang** - Filtrlar juda qattiq bo'lsa, hech narsa topilmasligi mumkin

```bash
# Misol: Barcha tranzaksiyalarni export qilish (filtersiz)
POST /api/v1/school/finance/export/transactions/
Headers:
  X-Branch-Id: <to'g'ri_branch_id>
Body: {}  # Filtersiz

# Faqat sana bilan
Body: {
  "date_from": "2025-01-01",  # Keng oraliq
  "date_to": "2026-12-31"
}
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
3. **Kategoriyalar**: 28 ta default global kategoriya mavjud. Har bir filial o'z kategoriyalarini yaratishi mumkin.
4. **Avtomatik Branch**: 
   - Obyekt yaratishda `branch` fieldini ko'rsatmasangiz, avtomatik requestdan olinadi
   - `X-Branch-Id` header, JWT token, yoki middleware orqali branch aniqlash
   - Super admin uchun: `branch` berilmasa, global obyekt yaratiladi (branch=null)
5. **Tranzaksiyalar**: 
   - Har bir to'lov avtomatik tranzaksiya yaratadi va kassa balansini yangilaydi
   - `category` field orqali kategoriyaga bog'lanadi
   - Kategoriya turi va tranzaksiya turi mos kelishi kerak
6. **O'quvchi Balansi**: 
   - Har bir to'lov o'quvchi balansini avtomatik yangilaydi
   - `StudentProfile` yaratilganda `StudentBalance` avtomatik yaratiladi (signal orqali)
7. **Chegirmalar**: Chegirmalar foiz yoki aniq summa bo'lishi mumkin. Sana cheklovlari ham mavjud.
8. **Pagination**: Barcha list endpointlar pagination qo'llab-quvvatlaydi (default: 20, max: 100)
9. **Filtering, Search, Ordering**: Barcha list endpointlar filtering, search va ordering qo'llab-quvvatlaydi
10. **Permissions**: 
    - `VIEW_FINANCE_REPORTS` - Hisobotlarni ko'rish
    - `MANAGE_FINANCE` - Moliyani boshqarish
    - `MANAGE_CATEGORIES` - Kategoriyalarni boshqarish
    - `CAN_AUTO_APPROVE` - Avtomatik tasdiq ruxsati
    - `CAN_APPROVE_MANUALLY` - Manual tasdiq ruxsati
11. **Test Coverage**: 26 ta yangi test (race conditions, privacy, permissions, export)
12. **Thread Safety**: StudentBalance operatsiyalari select_for_update() bilan himoyalangan

## Test Coverage (2026-01-02)

Moliya tizimi uchun 26 ta yangi test yaratildi:

### 1. Race Conditions (5 tests)
- `test_concurrent_add_amount` - 10 ta thread bir vaqtda add_amount()
- `test_concurrent_subtract_amount` - 20 ta thread bir vaqtda subtract_amount()
- `test_concurrent_mixed_operations` - 50 ta aralash operatsiya
- `test_transaction_rollback_on_error` - Xatolik yuz berganda rollback
- `test_concurrent_cash_register_updates` - 20 ta parallel kassa yangilash

**Critical Fix**: `StudentBalance.subtract_amount()` metodida select_for_update() lock qo'shildi - race condition oldini oladi.

### 2. Privacy/Isolation (4 tests)
- `test_transaction_queryset_filters_by_branch` - Tranzaksiyalar branch bo'yicha filtrlangan
- `test_cash_register_queryset_filters_by_branch` - Kassa branch isolation
- `test_category_includes_branch_and_global` - Kategoriyalar (branch + global)
- `test_discount_branch_validation` - Chegirma branch validatsiyasi

### 3. Permissions (7 tests)
- `test_branch_admin_auto_approves_income` - Branch Admin kirim avtomatik tasdiqlanadi
- `test_branch_admin_auto_approves_expense` - Branch Admin chiqim avtomatik tasdiqlanadi
- `test_super_admin_with_auto_approve_creates_completed` - Super Admin CAN_AUTO_APPROVE ruxsati bilan
- `test_super_admin_without_auto_approve_creates_pending` - Super Admin ruxsatsiz PENDING yaratadi
- `test_accountant_with_auto_approve_creates_completed` - Accountant CAN_AUTO_APPROVE bilan
- `test_accountant_without_auto_approve_creates_pending` - Accountant ruxsatsiz PENDING
- `test_pending_transaction_does_not_affect_balance` - PENDING tranzaksiya balansni o'zgartirmaydi

**Permission Logic**:
- Branch Admin: Har doim avtomatik tasdiq (auto-approve)
- Super Admin: Permission-based (CAN_AUTO_APPROVE kerak)
- Accountant/Other: Permission-based (CAN_AUTO_APPROVE kerak)

### 4. Export Functionality (10 tests)
- `test_export_transactions_starts_task` - Export task boshlash
- `test_export_transactions_with_filters` - Filtrlar bilan export
- `test_export_requires_authentication` - Autentifikatsiya talab qilinadi
- `test_export_requires_branch_id` - Branch ID validation
- `test_task_status_pending` - Task status PENDING
- `test_task_status_success` - Task status SUCCESS va file URL
- `test_task_status_failure` - Task status FAILURE va error
- `test_export_task_creates_excel_file` - Real Excel fayl yaratish (integration)
- `test_export_task_with_no_records` - Ma'lumot yo'q bo'lsa xatolik
- `test_export_task_applies_date_filter` - Sana filtrlari to'g'ri qo'llanadi

**Export Features**:
- Celery task orqali asinxron export
- Maksimal 50,000 yozuv
- Excel formatting (bold headers, ranglar, auto-width)
- Task status tracking va file URL

---

## Eslatmalar

1. **Valyuta**: Barcha summalar so'm (butun sonlar) formatida.
2. **Umumiy Tariflar va Chegirmalar**: Agar `branch` `null` bo'lsa, bu umumiy (barcha filiallar uchun).
3. **Kategoriyalar**: 28 ta default global kategoriya mavjud. Har bir filial o'z kategoriyalarini yaratishi mumkin.
4. **Avtomatik Branch**: 
   - Obyekt yaratishda `branch` fieldini ko'rsatmasangiz, avtomatik requestdan olinadi
   - `X-Branch-Id` header, JWT token, yoki middleware orqali branch aniqlash
   - Super admin uchun: `branch` berilmasa, global obyekt yaratiladi (branch=null)
5. **Tranzaksiyalar**: 
   - Har bir to'lov avtomatik tranzaksiya yaratadi va kassa balansini yangilaydi
   - `category` field orqali kategoriyaga bog'lanadi
   - Kategoriya turi va tranzaksiya turi mos kelishi kerak
   - **Auto-Approval**: Branch Admin har doim avtomatik, boshqalar permission-based
6. **O'quvchi Balansi**: 
   - Har bir to'lov o'quvchi balansini avtomatik yangilaydi
   - `StudentProfile` yaratilganda `StudentBalance` avtomatik yaratiladi (signal orqali)
   - **Thread-Safe**: select_for_update() lock bilan himoyalangan
7. **Chegirmalar**: Chegirmalar foiz yoki aniq summa bo'lishi mumkin. Sana cheklovlari ham mavjud.
8. **Pagination**: Barcha list endpointlar pagination qo'llab-quvvatlaydi (default: 20, max: 100)
9. **Filtering, Search, Ordering**: Barcha list endpointlar filtering, search va ordering qo'llab-quvvatlaydi

### 1. Kassa yaratish va to'lov qilish

```bash
```bash
# 1. Kassa yaratish (branch avtomatik olinadi)
POST /api/v1/school/finance/cash-registers/
Headers: 
  Authorization: Bearer <token>
  X-Branch-Id: <branch_uuid>
Body:
{
  "name": "Asosiy kassa",
  "description": "Asosiy kassa",
  "location": "1-qavat",
  "is_active": true
}
# branch fieldini ko'rsatmadingiz - avtomatik X-Branch-Id dan olinadi

# 2. Abonement tarifi yaratish (branch ko'rsatilgan)
POST /api/v1/school/finance/subscription-plans/
{
  "branch": "uuid",  # Agar berilmasa, X-Branch-Id dan olinadi
  "name": "1-4 sinflar oylik tarifi",
  "grade_level_min": 1,
  "grade_level_max": 4,
  "period": "monthly",
  "price": 1400000,
  "is_active": true
}

# 3. Global tarif yaratish (super admin)
POST /api/v1/school/finance/subscription-plans/
Headers: 
  Authorization: Bearer <super_admin_token>
Body:
{
  # branch fieldini berilmasa va super admin bo'lsa: global tarif (branch=null)
  "name": "Barcha filiallar uchun",
  "grade_level_min": 1,
  "grade_level_max": 11,
  "period": "monthly",
  "price": 1500000,
  "is_active": true
}

# 4. Chegirma yaratish (branch avtomatik)
POST /api/v1/school/finance/discounts/
Headers: 
  X-Branch-Id: <branch_uuid>
Body:
{
  "name": "Yangi o'quvchilar uchun chegirma",
  "discount_type": "percentage",
  "amount": 10,
  "is_active": true,
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": "2024-12-31T23:59:59Z"
}

# 5. To'lov yaratish
POST /api/v1/school/finance/payments/
{
  "student_profile": "uuid",
  # branch berilmasa, headerdan olinadi
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

### 2. Kategoriya bilan Tranzaksiya yaratish 🆕

```bash
# Kirim - Kategoriya bilan
POST /api/v1/school/finance/transactions/
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "income",
  "category": "uuid",  # student_payment kategoriyasi
  "amount": 5000000,
  "payment_method": "cash",
  "description": "O'quvchi oylik to'lovi",
  "reference_number": "REF-001",
  "transaction_date": "2024-01-01T00:00:00Z"
}

# Chiqim - Kategoriya bilan (masalan, maosh)
POST /api/v1/school/finance/transactions/
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "expense",
  "category": "uuid",  # salary kategoriyasi
  "amount": 3000000,
  "payment_method": "bank_transfer",
  "description": "O'qituvchi maoshi",
  "employee_membership": "uuid",
  "transaction_date": "2024-01-01T00:00:00Z"
}

# Kategoriya bo'yicha filtrlash
GET /api/v1/school/finance/transactions/?branch_id=uuid&category=uuid
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
# Kategoriyalar - Faqat kirim
GET /api/v1/school/finance/categories/?type=income&is_active=true

# Kategoriyalar - Faqat global
GET /api/v1/school/finance/categories/?is_global=true

# Kategoriyalar - Qidiruv
GET /api/v1/school/finance/categories/?search=maosh

# Faol tariflar
GET /api/v1/school/finance/subscription-plans/?branch_id=uuid&is_active=true

# Faol chegirmalar
GET /api/v1/school/finance/discounts/?branch_id=uuid&is_active=true

# O'quvchi to'lovlari
GET /api/v1/school/finance/payments/?branch_id=uuid&student_profile=uuid

# Tranzaksiyalar (kirim, kategoriya bilan)
GET /api/v1/school/finance/transactions/?branch_id=uuid&transaction_type=income&category=uuid&status=completed

# Qidirish
GET /api/v1/school/finance/cash-registers/?branch_id=uuid&search=asosiy

# Tartiblash
GET /api/v1/school/finance/transactions/?branch_id=uuid&ordering=-amount
GET /api/v1/school/finance/payments/?branch_id=uuid&ordering=-payment_date
```

## Avtomatik Yaratiladigan Modellar

Quyidagi modellar signallar orqali avtomatik yaratiladi:

1. **FinanceCategory** - Migration orqali 28 ta global kategoriya yaratiladi
   - 10 ta kirim kategoriyasi (student_payment, course_fee, ...)
   - 18 ta chiqim kategoriyasi (salary, rent, utilities, ...)
   - Migration: `0004_load_default_categories.py`

2. **StudentBalance** - `StudentProfile` yaratilganda avtomatik yaratiladi
   - Default balance: 0 so'm
   - Signal: `apps.school.finance.signals.create_student_balance`

3. **BranchSettings** - `Branch` yaratilganda avtomatik yaratiladi
   - Signal: `apps.branch.signals.create_branch_settings`

## Xavfsizlik va Ruxsatlar

- Barcha endpointlar JWT autentifikatsiyani talab qiladi
- **Ruxsatlar:**
  - `CanViewFinanceReports` - Hisobotlarni ko'rish (Super Admin, Branch Admin, Xodim with permission)
  - `CanManageFinance` - Moliyani boshqarish (Super Admin, Branch Admin, Xodim with permission)
  - `CanManageCategories` - Kategoriyalarni boshqarish (Super Admin, Branch Admin, Xodim with permission)
- Har bir so'rovda `X-Branch-Id` header talab qilinadi (ba'zi endpointlar uchun)
- Filialga tegishli ma'lumotlar faqat o'sha filial adminlari ko'ra oladi
- Super admin barcha filiallarga kirishi mumkin
- **Branch Isolation Middleware:** Avtomatik ravishda `request.branch` va `request.membership` o'rnatadi

## Qo'shimcha Dokumentatsiya

- **Kategoriyalar API:** [finance-category-api.md](../finance-category-api.md) - To'liq dokumentatsiya
- **Bug Fixes:** Permission classes va middleware xatolari tuzatildi (2025-12-22)
- **Migration Path:** Eski CharField category → Yangi ForeignKey category

---

**Last Updated:** 2025-12-22  
**Version:** 1.1.0 (Dinamik Kategoriyalar Tizimi)

