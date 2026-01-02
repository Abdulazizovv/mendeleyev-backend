# Moliya Tranzaksiyalari API (2025 Yangilangan)

## So'nggi O'zgarishlar

### ✅ 2025 Yangilanishlari

**Qo'shilgan:**
- ✅ `Transaction.category` - Dinamik kategoriya (ForeignKey → FinanceCategory)
- ✅ Django-filters - Kuchli filtrlash qobiliyatlari
- ✅ Excel Export - Celery orqali asinxron export
- ✅ Auto-approval - Permission-based avtomatik tasdiqlash
- ✅ Race condition fixes - F() expressions va select_for_update()
- ✅ Branch isolation - Har bir filial o'z ma'lumotlarigagina kiradi
- ✅ Discount branch validation - Chegirmalar faqat o'z filialida yoki globalda ishlaydi

**Deprecated:**
- ⚠️ `income_category` - Eski hardcoded (hali mavjud, lekin DEPRECATED)
- ⚠️ `expense_category` - Eski hardcoded (hali mavjud, lekin DEPRECATED)

---

## Endpoints

### 1. Tranzaksiyalar Ro'yxati

**GET** `/api/v1/finance/transactions/`

**Parametrlar (django-filter):**
- `branch_id` - UUID (super admin uchun ixtiyoriy)
- `transaction_type` - income/expense/transfer/payment/salary/refund (ko'plab qiymatlar: `?transaction_type=income&transaction_type=expense`)
- `status` - pending/approved/rejected/cancelled (ko'plab qiymatlar)
- `cash_register` - UUID
- `category` - UUID (ko'plab qiymatlar)
- `student_profile` - UUID
- `amount_min` - int (minimal summa)
- `amount_max` - int (maksimal summa)
- `date_from` - YYYY-MM-DD (boshlanish sanasi)
- `date_to` - YYYY-MM-DD (tugash sanasi)
- `search` - description, reference_number, student ismi bo'yicha qidiruv
- `ordering` - amount, -amount, transaction_date, -transaction_date, created_at, -created_at

**Javob:**
```json
{
  "count": 150,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "branch": "uuid",
      "branch_name": "Filial 1",
      "cash_register": "uuid",
      "cash_register_name": "Asosiy kassa",
      "transaction_type": "income",
      "transaction_type_display": "Kirim",
      "status": "completed",
      "status_display": "Bajarilgan",
      "category": "uuid",
      "category_name": "O'quvchi to'lovi",
      "category_code": "student_payment",
      "amount": 500000,
      "payment_method": "cash",
      "payment_method_display": "Naqd pul",
      "description": "Dekabr oyi uchun to'lov",
      "reference_number": "INV-2025-001",
      "student_profile": "uuid",
      "student_name": "Ali Valiyev",
      "employee_membership": null,
      "employee_name": null,
      "transaction_date": "2025-12-22T10:00:00Z",
      "metadata": {},
      "created_at": "2025-12-22T10:00:00Z",
      "updated_at": "2025-12-22T10:00:00Z"
    }
  ]
}
```

**Ruxsatlar:**
- `view_finance` yoki `manage_finance` permission
- Super admin: Barcha filiallar
- Branch admin: O'z filiali
- Oddiy xodim: Role permissions bo'yicha

---

### 2. Tranzaksiya Yaratish

**POST** `/api/v1/finance/transactions/`

**Request Body:**
```json
{
  "branch": "uuid",
  "cash_register": "uuid",
  "transaction_type": "income",
  "category": "uuid",
  "amount": 500000,
  "payment_method": "cash",
  "description": "Dekabr oyi uchun to'lov",
  "reference_number": "INV-2025-001",
  "student_profile": "uuid",
  "transaction_date": "2025-12-22T10:00:00Z",
  "metadata": {
    "processed_by": "Admin",
    "notes": "Qo'shimcha ma'lumot"
  }
}
```

**Validatsiya:**

1. **Amount:**
   - Min: 1 so'm
   - Max: 1,000,000,000 so'm (1 milliard)

2. **Category:**
   - Type mos kelishi kerak (income tranzaksiya → income kategoriya)
   - Faol (`is_active=true`) bo'lishi kerak
   - Branch uchun mavjud bo'lishi kerak (global yoki filial kategoriyasi)

3. **Cash Register Balance:**
   - Chiqim (`expense`, `salary`) uchun kassada yetarli mablag' bo'lishi kerak
   - Xatolik: `"Kassada yetarli mablag' yo'q. Mavjud: 1500000 so'm"`

**Javob:**
```json
{
  "id": "uuid",
  "branch": "uuid",
  "branch_name": "Filial 1",
  "cash_register": "uuid",
  "cash_register_name": "Asosiy kassa",
  "transaction_type": "income",
  "transaction_type_display": "Kirim",
  "status": "completed",
  "status_display": "Bajarilgan",
  "category": "uuid",
  "category_name": "O'quvchi to'lovi",
  "category_code": "student_payment",
  "amount": 500000,
  "payment_method": "cash",
  "payment_method_display": "Naqd pul",
  "description": "Dekabr oyi uchun to'lov",
  "reference_number": "INV-2025-001",
  "student_profile": "uuid",
  "student_name": "Ali Valiyev",
  "employee_membership": null,
  "employee_name": null,
  "transaction_date": "2025-12-22T10:00:00Z",
  "metadata": {"processed_by": "Admin", "notes": "Qo'shimcha ma'lumot"},
  "created_at": "2025-12-22T10:00:00Z",
  "updated_at": "2025-12-22T10:00:00Z"
}
```

**⚠️ Status Xatti-harakati (Permission-based):**

| Permission | Yaratilgan Status | Kassa Balansi | Izoh |
|-----------|-------------------|---------------|------|
| **CAN_AUTO_APPROVE** | `APPROVED` | ✅ Darhol yangilanadi | Avtomatik tasdiqlanadi |
| **CAN_APPROVE_MANUALLY** | `PENDING` | ⏳ Kutmoqda | Manual tasdiq talab qilinadi |
| **Boshqalar** | `PENDING` | ⏳ Kutmoqda | Manual tasdiq talab qilinadi |

**Auto-approval Logikasi:**
- User `can_auto_approve_transactions` permission ga ega bo'lsa → transaction darhol `APPROVED` holatida yaratiladi
- Aks holda → `PENDING` holatida yaratiladi va manual tasdiq kutiladi
- Kassa balansi faqat `APPROVED` holatda yangilanadi

**Ruxsatlar:**
- `create_transactions` yoki `manage_finance` permission
- Branch admin: O'z filiali uchun
- Super admin: Har qanday filial uchun

---

### 3. Tranzaksiya Detali

**GET** `/api/v1/finance/transactions/{id}/`

**Javob:** (Yuqoridagi struktura)

---

### 4. Tranzaksiya Yangilash

**PUT/PATCH** `/api/v1/finance/transactions/{id}/`

**Eslatma:** 
- Tranzaksiya immutability qisman - faqat `description` va `metadata` ni o'zgartirish mumkin
- `amount`, `transaction_type`, `category` o'zgartirib bo'lmaydi (ma'lumotlar yaxlitligi uchun)

**Request Body:**
```json
{
  "description": "Yangilangan tavsif",
  "metadata": {
    "updated_by": "Manager",
    "reason": "Ma'lumot to'ldirildi"
  }
}
```

**Ruxsatlar:**
- `edit_transactions` yoki `manage_finance` permission

---

### 5. Tranzaksiya O'chirish

**DELETE** `/api/v1/finance/transactions/{id}/`

**Javob:** `204 No Content`

**Eslatma:**
- Soft delete (deleted_at timestamp)
- Kassa balansi avtomatik teskari hisoblanadi
- Agar `status=completed` bo'lsa, balans qaytariladi

**Ruxsatlar:**
- `delete_transactions` yoki `manage_finance` permission

---

## Category Integration

### Kategoriya Tanlash

Tranzaksiya yaratishdan oldin kategoriyalarni olish:

```bash
# Kirim kategoriyalari
GET /api/v1/finance/categories/?type=income&is_active=true

# Chiqim kategoriyalari
GET /api/v1/finance/categories/?type=expense&is_active=true
```

### Kategoriya bo'yicha Filtrash

```bash
# Ma'lum kategoriya bo'yicha tranzaksiyalar
GET /api/v1/finance/transactions/?category=<category-uuid>

# Maosh to'lovlari (salary kategoriyasi)
GET /api/v1/finance/transactions/?category=<salary-category-uuid>&transaction_type=salary
```

---

## Permissions Matrix

| Rol | view_finance | create_transactions | edit_transactions | delete_transactions | manage_finance |
|-----|--------------|---------------------|-------------------|---------------------|----------------|
| **Super Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Branch Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Accountant** | ✅ | ✅ | ⚠️ Limited | ❌ | ❌ |
| **Cashier** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Teacher** | ⚠️ Limited | ❌ | ❌ | ❌ | ❌ |

**Eslatma:** Role.permissions JSONField orqali granular ruxsatlar.

---

## Foydalanish Misollari

### Frontend: Tranzaksiya Yaratish

```javascript
// 1. Kategoriyalarni olish
const categoriesResponse = await fetch(
  '/api/v1/finance/categories/?type=income&is_active=true',
  {
    headers: {
      'Authorization': 'Bearer <token>',
      'X-Branch-Id': '<branch-uuid>'
    }
  }
);
const categories = await categoriesResponse.json();

// 2. Tranzaksiya yaratish
const transactionResponse = await fetch('/api/v1/finance/transactions/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'X-Branch-Id': '<branch-uuid>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    cash_register: cashRegisterId,
    transaction_type: 'income',
    category: categories.results[0].id, // Student payment
    amount: 500000,
    payment_method: 'cash',
    description: 'Dekabr oyi uchun to\'lov',
    student_profile: studentId,
    transaction_date: new Date().toISOString()
  })
});

const transaction = await transactionResponse.json();
console.log('Created:', transaction);
```

### Backend: Statistika

```python
from django.db.models import Sum, Count
from apps.school.finance.models import Transaction

# Kategoriya bo'yicha statistika
category_stats = Transaction.objects.filter(
    branch_id=branch_id,
    status='completed',
    deleted_at__isnull=True
).values(
    'category__name',
    'category__type'
).annotate(
    total_amount=Sum('amount'),
    count=Count('id')
).order_by('-total_amount')

# Natija:
# [
#   {'category__name': 'Maosh', 'category__type': 'expense', 'total_amount': 50000000, 'count': 25},
#   {'category__name': 'O\'quvchi to\'lovi', 'category__type': 'income', 'total_amount': 45000000, 'count': 150},
# ]
```

---

## Migration Path

### Eski Koddan Yangi Kodga O'tish

**Eski (Deprecated):**
```python
# Income
transaction = Transaction.objects.create(
    transaction_type='income',
    income_category='student_payment',  # DEPRECATED
    amount=500000
)

# Expense
transaction = Transaction.objects.create(
    transaction_type='expense',
    expense_category='salary',  # DEPRECATED
    amount=3000000
)
```

**Yangi (Recommended):**
```python
# Kategoriyani topish
category = FinanceCategory.objects.get(
    code='student_payment',
    type='income',
    branch__isnull=True  # Global yoki filial
)

# Tranzaksiya yaratish
transaction = Transaction.objects.create(
    transaction_type='income',
    category=category,  # Dinamik kategoriya
    amount=500000
)
```

---

## Admin Panel

Django admin panelda yangi:
- ✅ `category` filter
- ✅ Kategoriya rangli ko'rsatkichi (income=yashil, expense=qizil)
- ✅ Category column list_display'da
- ✅ Fieldset'da category field

---

## Testing

```bash
# Kategoriyali tranzaksiya yaratish
curl -X POST http://localhost:8000/api/v1/finance/transactions/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Branch-Id: <branch-uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "cash_register": "<cash-register-uuid>",
    "transaction_type": "income",
    "category": "<category-uuid>",
    "amount": 500000,
    "payment_method": "cash",
    "description": "Test tranzaksiya"
  }'

# Kategoriya bo'yicha filtrash
curl -X GET "http://localhost:8000/api/v1/finance/transactions/?category=<category-uuid>" \
  -H "Authorization: Bearer <token>"
```

---

## Xatoliklar

### 400 Bad Request - Category Type Mismatch
```json
{
  "category": ["Kirim tranzaksiyasi uchun kirim kategoriyasini tanlang"]
}
```

### 400 Bad Request - Inactive Category
```json
{
  "category": ["Bu kategoriya faol emas"]
}
```

### 400 Bad Request - Insufficient Balance
```json
{
  "amount": ["Kassada yetarli mablag' yo'q. Mavjud: 1500000 so'm"]
}
```

### 403 Forbidden - No Permission
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Best Practices

1. **Har doim category ishlatish**
   - Eski `income_category`/`expense_category` emas
   - Dinamik kategoriyalar flexible va scalable

2. **Kategoriya validatsiyasi**
   - Frontend'da type mos kelishini tekshirish
   - Active kategoriyalarni tanlash

3. **Permissions tekshirish**
   - Har bir operatsiya uchun kerakli permission
   - Super admin va branch admin ajratish

4. **Branch isolation**
   - Middleware avtomatik filtrlaydi
   - Super admin barcha filiallarga kiradi

5. **Audit trail**
   - `metadata` fieldga qo'shimcha ma'lumot
   - `processed_by`, `updated_by`, `reason` saqlash

---

## Excel Export (Yangi!)

### Export Tranzaksiyalar

**POST** `/api/v1/finance/export/transactions/`

Tranzaksiyalarni Excel fayliga export qilish. Celery task orqali asinxron bajariladi.

**Request Body:**
```json
{
  "transaction_type": "income",
  "status": "approved",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "cash_register": "uuid",
  "category": "uuid",
  "student_profile": "uuid"
}
```

**Response:**
```json
{
  "message": "Export task boshlandi",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

**Eslatma:**
- Maksimal 50,000 ta yozuvni export qiladi
- Filtr parametrlari ixtiyoriy
- Excel fayl `media/exports/finance/` papkasida saqlanadi
- Fayl nomi: `transactions_YYYYMMDD_HHMMSS.xlsx`

---

### Export To'lovlar

**POST** `/api/v1/finance/export/payments/`

To'lovlarni Excel fayliga export qilish.

**Request Body:**
```json
{
  "student_profile": "uuid",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "period": "2025-12"
}
```

**Response:** (Yuqoridagidek)

---

### Task Statusini Tekshirish

**GET** `/api/v1/finance/export/task-status/{task_id}/`

Export task natijasini olish.

**Response (PENDING):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "Task kutilmoqda"
}
```

**Response (SUCCESS):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "message": "Export muvaffaqiyatli",
  "file_url": "/media/exports/finance/transactions_20250102_143022.xlsx",
  "filename": "transactions_20250102_143022.xlsx",
  "records_count": 1523
}
```

**Response (FAILURE):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "FAILURE",
  "message": "Task xatolik",
  "error": "Database connection error"
}
```

**Excel Fayl Tuzilishi:**
- Avtomatik formatlangan (header bold, ranglar)
- Summa formati: #,##0 so'm
- Sana formati: DD.MM.YYYY HH:MM
- Auto-width ustunlar

---

## Keyingi Yangilanishlar

- [x] Tranzaksiya hisobotlari (oylik, yillik)
- [x] Excel export (Celery bilan)
- [ ] CSV export
- [ ] Bulk import
- [ ] Tranzaksiya tags (qo'shimcha tashkilot uchun)
- [ ] Recurring transactions (qayta-qayta to'lovlar)
- [ ] Transaction approval workflow
- [ ] Advanced analytics va charts
