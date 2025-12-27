# Moliya Kategoriyalari API

## Umumiy Ma'lumot

Dinamik moliya kategoriyalari tizimi har bir filialga o'z kategoriyalarini yaratish imkonini beradi. Global kategoriyalar (branch=null) barcha filiallar uchun mavjud.

**Asosiy Xususiyatlar:**
- ✅ Branch-specific va global kategoriyalar
- ✅ Ierarxik tuzilma (parent/child relationships)
- ✅ Unique constraint: (branch, type, code)
- ✅ Soft delete support (BaseModel)
- ✅ Role-based access control
- ✅ Super admin multi-branch access

## Model Strukturasi

```python
class FinanceCategory(BaseModel):
    id = UUIDField(primary_key=True, default=uuid4)
    branch = ForeignKey(Branch, null=True, blank=True, on_delete=CASCADE)
    type = CharField(max_length=10, choices=CategoryType.choices)
    code = CharField(max_length=50)
    name = CharField(max_length=100)
    description = TextField(blank=True)
    parent = ForeignKey('self', null=True, blank=True, on_delete=CASCADE)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    deleted_at = DateTimeField(null=True, blank=True)
    
    unique_together = [['branch', 'type', 'code']]
    
class Meta:
    db_table = 'finance_category'
    ordering = ['type', 'name']
```

**Branch Logic:**
- `branch=NULL` → Global kategoriya (barcha filiallar ko'radi)
- `branch=UUID` → Filial-specific kategoriya (faqat o'sha filial ko'radi)

## API Endpoints

### 1. Kategoriyalar Ro'yxati

**GET** `/api/v1/school/finance/categories/`

**Query Parameters:**
- `type` - income | expense
- `is_active` - true | false
- `parent` - UUID (ota kategoriya ID)
- `search` - name, code, description bo'yicha qidiruv
- `ordering` - name | code | created_at | -name | -code | -created_at

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (majburiy)
- `X-Branch-Id: <BRANCH_UUID>` (ixtiyoriy, super admin uchun)

**Response (200 OK):**
```json
{
  "count": 30,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "branch_name": "Chilonzor Filiali",
      "type": "income",
      "type_display": "Kirim",
      "code": "student_payment",
      "name": "O'quvchi to'lovi",
      "is_active": true
    },
    {
      "id": "4fa85f64-5717-4562-b3fc-2c963f66afa7",
      "branch": null,
      "branch_name": null,
      "type": "expense",
      "type_display": "Chiqim",
      "code": "salary",
      "name": "Maosh",
      "is_active": true
    }
  ]
}
```

**Access Control:**
- **Super Admin:** Barcha kategoriyalarni ko'radi (global + barcha filiallar)
- **Branch Admin:** Global + o'z filiali kategoriyalari
- **Xodim (with view_finance):** Global + o'z filiali kategoriyalari
- **Ruxsatsiz:** 403 Forbidden

---

### 2. Kategoriya Yaratish

**POST** `/api/v1/school/finance/categories/`

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (majburiy)
- `X-Branch-Id: <BRANCH_UUID>` (ixtiyoriy)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "type": "expense",
  "code": "custom_expense",
  "name": "Maxsus chiqim",
  "description": "Filial uchun maxsus chiqim kategoriyasi",
  "parent": null,
  "is_active": true
}
```

**Field Descriptions:**
- `branch` (optional) - Filial UUID. Agar kiritilmasa:
  - Super admin global kategoriya yaratsa: `null`
  - Oddiy foydalanuvchi: Avtomatik o'z filiali (`X-Branch-Id` yoki JWT dan)
- `type` (required) - `income` yoki `expense`
- `code` (required) - Unikal kod (faqat harflar, raqamlar, `_`)
- `name` (required) - Kategoriya nomi
- `description` (optional) - Tavsif
- `parent` (optional) - Ota kategoriya UUID (ierarxiya uchun)
- `is_active` (optional, default: true) - Faol holati

**Response (201 Created):**
```json
{
  "id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "branch_name": "Chilonzor Filiali",
  "type": "expense",
  "type_display": "Chiqim",
  "code": "custom_expense",
  "name": "Maxsus chiqim",
  "description": "Filial uchun maxsus chiqim kategoriyasi",
  "parent": null,
  "parent_name": null,
  "subcategories_count": 0,
  "is_active": true,
  "created_at": "2025-12-22T14:30:00Z",
  "updated_at": "2025-12-22T14:30:00Z"
}
```

**Validatsiya Qoidalari:**
1. **Code format:**
   - Faqat harflar, raqamlar va `_` (pastki chiziq)
   - Avtomatik lowercase ga o'zgartiriladi
   - Misol: `"Custom_Expense123"` → `"custom_expense123"`

2. **Unique constraint:**
   - `(branch, type, code)` kombinatsiyasi unique bo'lishi kerak
   - Bir filialda bir xil turda bir xil kod bo'lishi mumkin emas
   - Global va filial kategoriyalarida bir xil kod bo'lishi mumkin

3. **Parent validation:**
   - Agar `parent` berilgan bo'lsa, ota kategoriya bir xil `type` da bo'lishi kerak
   - Income kategoriyaning parenti faqat income bo'lishi mumkin
   - Expense kategoriyaning parenti faqat expense bo'lishi mumkin

**Error Responses:**

**400 Bad Request - Invalid Code:**
```json
{
  "code": ["Kod faqat harflar, raqamlar va pastki chiziqdan iborat bo'lishi kerak."]
}
```

**400 Bad Request - Duplicate:**
```json
{
  "code": ["Chilonzor Filiali filialda expense turida 'custom_expense' kodi mavjud."]
}
```

**400 Bad Request - Parent Type Mismatch:**
```json
{
  "parent": ["Ota kategoriya Chiqim turida, lekin yangi kategoriya income turida."]
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Ruxsatlar:**
- **Super Admin:** Global va har qanday filial uchun yaratishi mumkin
- **Branch Admin:** Faqat o'z filiali uchun
- **Xodim (with manage_categories):** Faqat o'z filiali uchun
- **Boshqalar:** 403 Forbidden

---

### 3. Kategoriya Detali

**GET** `/api/v1/school/finance/categories/{id}/`

**Path Parameters:**
- `id` - Kategoriya UUID

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (majburiy)

**Response (200 OK):**
```json
{
  "id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "branch_name": "Chilonzor Filiali",
  "type": "income",
  "type_display": "Kirim",
  "code": "course_fee",
  "name": "Kurs to'lovi",
  "description": "Online va offline kurslar uchun to'lov",
  "parent": null,
  "parent_name": null,
  "subcategories_count": 3,
  "is_active": true,
  "created_at": "2025-12-22T10:00:00Z",
  "updated_at": "2025-12-22T14:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Ruxsatlar:**
- Super admin: Barcha kategoriyalarni ko'radi
- Branch admin: Global + o'z filiali
- Xodim: Global + o'z filiali (agar view_finance bo'lsa)

---

### 4. Kategoriya Yangilash

**PUT** `/api/v1/school/finance/categories/{id}/` (to'liq yangilash)
**PATCH** `/api/v1/school/finance/categories/{id}/` (qisman yangilash)

**Path Parameters:**
- `id` - Kategoriya UUID

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (majburiy)
- `Content-Type: application/json`

**Request Body (PATCH):**
```json
{
  "name": "Yangilangan nom",
  "description": "Yangilangan tavsif",
  "is_active": false
}
```

**Yangilanishi Mumkin:**
- `name` - Kategoriya nomi
- `description` - Tavsif
- `is_active` - Faol holati
- `parent` - Ota kategoriya (type mos kelsa)

**Yangilanishi MUMKIN EMAS:**
- `id` - UUID (o'zgarmas)
- `branch` - Filial tegishliligi (o'zgarmas)
- `type` - Kategoriya turi (unique constraint tufayli)
- `code` - Kategoriya kodi (unique constraint tufayli)
- `created_at` - Yaratilgan vaqt (read-only)
- `updated_at` - Avtomatik yangilanadi

**Response (200 OK):**
```json
{
  "id": "5fa85f64-5717-4562-b3fc-2c963f66afa8",
  "branch": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "branch_name": "Chilonzor Filiali",
  "type": "expense",
  "type_display": "Chiqim",
  "code": "custom_expense",
  "name": "Yangilangan nom",
  "description": "Yangilangan tavsif",
  "parent": null,
  "parent_name": null,
  "subcategories_count": 0,
  "is_active": false,
  "created_at": "2025-12-22T10:00:00Z",
  "updated_at": "2025-12-22T15:45:00Z"
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "type": ["Bu fieldni o'zgartirib bo'lmaydi."]
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Ruxsatlar:**
- **Super Admin:** Barcha kategoriyalarni o'zgartirishi mumkin
- **Branch Admin:** Faqat o'z filiali kategoriyalarini
- **Xodim (with manage_categories):** Faqat o'z filiali kategoriyalarini
- **Global kategoriyalarni:** Faqat super admin o'zgartirishi mumkin

---

### 5. Kategoriya O'chirish

**DELETE** `/api/v1/school/finance/categories/{id}/`

**Path Parameters:**
- `id` - Kategoriya UUID

**Headers:**
- `Authorization: Bearer <JWT_TOKEN>` (majburiy)

**Response (204 No Content):**
```
(Bo'sh response body)
```

**O'chirish Mexanizmi:**
1. **Soft Delete** - `deleted_at` timestamp o'rnatiladi
2. **Cascade** - Agar subcategories bo'lsa, ular ham soft delete bo'ladi
3. **PROTECT** - Agar tranzaksiyalarda ishlatilgan bo'lsa, o'chirib bo'lmaydi

**Error Responses:**

**400 Bad Request (Foreign Key Constraint):**
```json
{
  "detail": "Bu kategoriya tranzaksiyalarda ishlatilgan, o'chirib bo'lmaydi."
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Ruxsatlar:**
- **Super Admin:** Barcha kategoriyalarni o'chirishi mumkin
- **Branch Admin:** Faqat o'z filiali kategoriyalarini
- **Xodim (with manage_categories):** Faqat o'z filiali kategoriyalarini
- **Global kategoriyalarni:** Faqat super admin o'chirishi mumkin

**Eslatma:** Soft delete bo'lganligi uchun ma'lumotlar bazadan to'liq o'chirilmaydi. Kerak bo'lsa restore qilish mumkin (admin panel orqali).

---

## Default Kategoriyalar

Migration `0004_load_default_categories.py` orqali 28 ta global kategoriya avtomatik yuklangan:

### Kirim Kategoriyalari (10 ta)

| Code | Name | Description |
|------|------|-------------|
| `student_payment` | O'quvchi to'lovi | O'quvchilardan tushadigan asosiy to'lovlar |
| `course_fee` | Kurs to'lovi | Kurs va darsliklarga to'lovlar |
| `registration_fee` | Ro'yxatdan o'tish to'lovi | Yangi o'quvchilar ro'yxatdan o'tish to'lovi |
| `exam_fee` | Imtihon to'lovi | Imtihon topshirish to'lovi |
| `certificate_fee` | Sertifikat to'lovi | Sertifikat berish to'lovi |
| `book_sale` | Kitob sotish | Kitob va darsliklar sotishdan tushum |
| `material_sale` | Material sotish | O'quv materiallari sotishdan tushum |
| `sponsorship` | Homiylik | Homiylardan keladigan mablag'lar |
| `grant` | Grant | Grant dasturlari |
| `other_income` | Boshqa kirim | Boshqa turdagi kirimlar |

### Chiqim Kategoriyalari (18 ta)

| Code | Name | Description |
|------|------|-------------|
| `salary` | Maosh | Xodimlar maoshi |
| `rent` | Ijara | Bino/xona ijarasi |
| `utilities` | Kommunal xizmatlar | Suv, gaz, elektr |
| `internet` | Internet | Internet xizmati |
| `phone` | Telefon | Telefon aloqasi |
| `office_supplies` | Ofis materiallari | Qog'oz, qalam va boshqalar |
| `books_materials` | Kitoblar va materiallar | O'quv kitoblari va materiallar xaridi |
| `equipment` | Jihozlar | Kompyuter va boshqa jihozlar |
| `maintenance` | Ta'mirlash | Ta'mirlash ishlari |
| `cleaning` | Tozalash | Tozalash xizmatlari |
| `security` | Xavfsizlik | Xavfsizlik xizmatlari |
| `marketing` | Marketing | Reklama va marketing |
| `training` | O'qitish | O'qituvchilar treningi |
| `tax` | Soliq | Soliq to'lovlari |
| `insurance` | Sug'urta | Sug'urta to'lovlari |
| `transportation` | Transport | Transport xarajatlari |
| `food` | Oziq-ovqat | Oziq-ovqat xarajatlari |
| `other_expense` | Boshqa chiqim | Boshqa turdagi chiqimlar |

**Xususiyatlar:**
- ✅ Barcha kategoriyalar `branch=NULL` (global)
- ✅ Barcha kategoriyalar `is_active=True`
- ✅ Barcha kategoriyalar `parent=NULL` (root level)
- ✅ Migration rollback qo'llab-quvvatlanadi
- ✅ Filiallar bu kategoriyalarni o'zgartira olmaydi, faqat ko'ra oladi

---

## Ruxsatlar (Permissions)

### FinancePermissions Class

`apps/school/finance/permissions.py`da aniqlangan ruxsatlar:

```python
class FinancePermissions:
    VIEW_FINANCE_REPORTS = 'view_finance_reports'
    MANAGE_FINANCE = 'manage_finance'
    MANAGE_CATEGORIES = 'manage_categories'
```

### Ruxsatlar Tafsiloti

#### 1. `VIEW_FINANCE_REPORTS`
**Maqsad:** Moliyaviy hisobotlarni ko'rish

**Ruxsat beradi:**
- Kategoriyalar ro'yxatini ko'rish (GET `/api/v1/school/finance/categories/`)
- Kategoriya tafsilotlarini ko'rish (GET `/api/v1/school/finance/categories/{id}/`)
- Tranzaksiyalar ro'yxatini ko'rish
- Filtrlar va qidiruvdan foydalanish

**Ruxsat bermaydi:**
- Kategoriya yaratish, yangilash, o'chirish
- Tranzaksiya yaratish, yangilash, o'chirish

**Kim olishi mumkin:**
- Hisobchi (accountant)
- Moliya menejeri (finance manager)
- Rahbariyat a'zolari

---

#### 2. `MANAGE_FINANCE`
**Maqsad:** Moliya bilan to'liq ishlash

**Ruxsat beradi:**
- Tranzaksiya yaratish, yangilash, o'chirish
- Tranzaksiya tasdiqini o'zgartirish
- Kategoriyalarni ko'rish va filtrlash
- Barcha `VIEW_FINANCE_REPORTS` ruxsatlari

**Ruxsat bermaydi:**
- Kategoriyalarni yaratish, tahrirlash, o'chirish (alohida ruxsat kerak)

**Kim olishi mumkin:**
- Moliya direktori (finance director)
- Katta hisobchi (senior accountant)
- Filial direktori (ma'lum hollarda)

---

#### 3. `MANAGE_CATEGORIES`
**Maqsad:** Kategoriyalarni boshqarish

**Ruxsat beradi:**
- Filial kategoriyalarini yaratish (POST)
- Filial kategoriyalarini yangilash (PUT/PATCH)
- Filial kategoriyalarini o'chirish (DELETE)
- Ota-kategoriyalar yaratish (parent categories)
- Barcha `VIEW_FINANCE_REPORTS` ruxsatlari

**Ruxsat bermaydi:**
- Global kategoriyalarni o'zgartirish (`branch=NULL`)
- Boshqa filiallarning kategoriyalarini tahrirlash
- Kategoriya tipini o'zgartirish (type field immutable)

**Kim olishi mumkin:**
- Filial direktori
- Tizim administratori
- Moliya direktori

---

### Rol va Ruxsatlar Matritsasi

| Rol | VIEW_FINANCE_REPORTS | MANAGE_FINANCE | MANAGE_CATEGORIES |
|-----|----------------------|----------------|-------------------|
| **SUPER_ADMIN** | ✅ Avtomatik | ✅ Avtomatik | ✅ Avtomatik |
| **BRANCH_ADMIN** | ✅ Avtomatik | ⚠️ Filial doirasida | ⚠️ Filial doirasida |
| **XODIM** (Finance Director) | ✅ Ruxsat orqali | ✅ Ruxsat orqali | ✅ Ruxsat orqali |
| **XODIM** (Accountant) | ✅ Ruxsat orqali | ❌ Ruxsat kerak | ❌ Ruxsat kerak |
| **OQUVCHI** | ❌ | ❌ | ❌ |
| **OTA_ONA** | ❌ | ❌ | ❌ |

---

### Permission Checking Logic

#### CanManageCategories Class

```python
# apps/school/finance/permissions.py
class CanManageCategories(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        branch_id = request.headers.get('X-Branch-Id')
        
        # Get membership
        if branch_id:
            membership = BranchMembership.objects.filter(
                user=user, 
                branch_id=branch_id
            ).first()
        else:
            membership = BranchMembership.objects.filter(user=user).first()
        
        if not membership:
            return False
        
        # Super admin has full access
        if membership.role == BranchRole.SUPER_ADMIN:
            return True
        
        # Branch admin can manage categories in their branch
        if membership.role == BranchRole.BRANCH_ADMIN:
            return True
        
        # Check specific permission for staff
        if membership.role == BranchRole.XODIM:
            return 'manage_categories' in (membership.permissions or [])
        
        return False
```

#### Middleware Integration

`BranchIsolationMiddleware` avtomatik `X-Branch-Id` ni tekshiradi va `request.branch` o'rnatadi:

```python
# apps/school/finance/middleware.py
class BranchIsolationMiddleware:
    def __call__(self, request):
        if request.user.is_authenticated:
            branch_id = request.headers.get('X-Branch-Id')
            try:
                if branch_id:
                    membership = BranchMembership.objects.filter(
                        user=request.user,
                        branch_id=branch_id
                    ).first()
                else:
                    membership = BranchMembership.objects.filter(
                        user=request.user
                    ).first()
                
                if membership:
                    request.branch = membership.branch
                    request.membership = membership
            except Exception:
                pass
        
        return self.get_response(request)
```

---

### Ruxsatlarni Tekshirish

#### Django Shell orqali

```python
# Python shell
python manage.py shell

from auth.users.models import User
from apps.branch.models import BranchMembership

# Foydalanuvchini topish
user = User.objects.get(telegram_id=123456789)
membership = BranchMembership.objects.filter(user=user).first()

# Ruxsatlarni tekshirish
print(membership.permissions)
# ['view_finance_reports', 'manage_finance']

# Ruxsat borligini tekshirish
has_permission = 'manage_categories' in (membership.permissions or [])
print(has_permission)  # True or False
```

#### cURL orqali tekshirish

```bash
# Kategoriya yaratishga urinish (ruxsat bor/yo'qligi tekshiriladi)
curl -X POST http://localhost:8000/api/v1/school/finance/categories/ \
  -H "Authorization: Bearer <token>" \
  -H "X-Branch-Id: <branch_uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test kategoriya",
    "type": "income"
  }'

# 201 Created - Ruxsat bor
# 403 Forbidden - Ruxsat yo'q
```

---

### Xatolik Javoblari

#### 403 - Ruxsat yo'q
```json
{
  "detail": "Sizda bu amalni bajarish uchun ruxsat yo'q"
}
```

#### 401 - Autentifikatsiya kerak
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## Foydalanish Misollari

### Backend: Kategoriya Yaratish

```python
# Django View yoki Service Layer
from apps.school.finance.models import FinanceCategory
from apps.branch.models import Branch

# Global kategoriya (faqat super admin)
global_category = FinanceCategory.objects.create(
    branch=None,  # Global
    type='income',
    code='new_income_type',
    name='Yangi kirim turi',
    description='Tavsif',
    is_active=True
)

# Filial kategoriyasi (branch admin yoki xodim)
branch = Branch.objects.get(id='branch-uuid')
branch_category = FinanceCategory.objects.create(
    branch=branch,
    type='expense',
    code='custom_expense',
    name='Maxsus xarajat',
    description='Filial uchun maxsus xarajat kategoriyasi',
    parent=None,
    is_active=True
)
```

---

### Backend: Kategoriya Filtrlash

```python
# Django ORM Queries
from apps.school.finance.models import FinanceCategory

# 1. Faqat global kategoriyalar
global_categories = FinanceCategory.objects.filter(
    branch__isnull=True,
    is_active=True
)

# 2. Faqat filial kategoriyalari
branch = request.branch  # Middleware orqali
branch_categories = FinanceCategory.objects.filter(
    branch=branch,
    is_active=True
)

# 3. Global + filial kategoriyalari
from django.db.models import Q
all_categories = FinanceCategory.objects.filter(
    Q(branch__isnull=True) | Q(branch=branch),
    is_active=True
)

# 4. Faqat kirim kategoriyalari
income_categories = FinanceCategory.objects.filter(
    Q(branch__isnull=True) | Q(branch=branch),
    type='income',
    is_active=True
)

# 5. Ota-kategoriyalar (parent=NULL)
root_categories = FinanceCategory.objects.filter(
    Q(branch__isnull=True) | Q(branch=branch),
    parent__isnull=True,
    is_active=True
)

# 6. Bolalar kategoriyalari
parent_category = FinanceCategory.objects.get(code='salary')
subcategories = parent_category.subcategories.filter(is_active=True)
```

---

### Backend: Kategoriya bilan Tranzaksiya Yaratish

```python
# Transaction Service
from apps.school.finance.models import Transaction, FinanceCategory
from decimal import Decimal

# Kategoriya olish
category = FinanceCategory.objects.get(
    code='student_payment',
    branch__isnull=True
)

# Tranzaksiya yaratish
transaction = Transaction.objects.create(
    branch=request.branch,
    category=category,  # Yangi field
    type='income',  # category.type bilan mos kelishi kerak
    amount=Decimal('500000.00'),
    description='O\'quvchi oylik to\'lovi',
    date='2025-12-22',
    is_confirmed=False
)

# Validation: Category type va Transaction type mos kelishi kerak
if transaction.category and transaction.category.type != transaction.type:
    raise ValidationError("Kategoriya turi tranzaksiya turi bilan mos emas")
```

---

### Backend: Serializer Validation

```python
# apps/school/finance/serializers.py misol
from rest_framework import serializers
from apps.school.finance.models import FinanceCategory

class TransactionCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=FinanceCategory.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    
    def validate(self, attrs):
        category = attrs.get('category')
        transaction_type = attrs.get('type')
        
        # 1. Kategoriya aktiv bo'lishi kerak
        if category and not category.is_active:
            raise serializers.ValidationError({
                'category': 'Nofaol kategoriya tanlanmaydi'
            })
        
        # 2. Kategoriya turi va tranzaksiya turi mos kelishi kerak
        if category and category.type != transaction_type:
            raise serializers.ValidationError({
                'category': f'Kategoriya turi {transaction_type} bo\'lishi kerak'
            })
        
        # 3. Kategoriya filialga tegishli yoki global bo'lishi kerak
        branch = self.context['request'].branch
        if category and category.branch and category.branch != branch:
            raise serializers.ValidationError({
                'category': 'Bu kategoriyadan foydalanish mumkin emas'
            })
        
        return attrs
```

---
    'Authorization': 'Bearer <token>',
    'X-Branch-Id': '<branch-uuid>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    type: 'expense',
    code: 'custom_expense',
    name: 'Filial chiqimi',
    is_active: true
  })
});
```

### Backend: Kategoriya Filtrlash

```python
# Super admin - barcha kategoriyalar
categories = FinanceCategory.objects.all()

# Branch admin - global + o'z filiali
categories = FinanceCategory.objects.filter(
    Q(branch__isnull=True) | Q(branch_id=branch_id)
)

# Faqat faol kirim kategoriyalari
income_categories = FinanceCategory.objects.filter(
    type='income',
    is_active=True
)
```

---

## Middleware Integration

`BranchIsolationMiddleware` avtomatik ravishda branch_id ni aniqlaydi:

```python
# Request objectda:
request.branch_id = "uuid"  # Foydalanuvchi filiali
request.is_super_admin = True/False
```

**Branch ID Manbaalari (priority tartibi):**
1. JWT token (`br` yoki `branch_id` claim)
2. HTTP Header (`X-Branch-Id`)
3. Query parameter (`?branch_id=uuid`)
4. Default: Foydalanuvchi a'zolik filiali

---

## Xatoliklar

### 400 Bad Request
```json
{
  "code": ["Filial 1 filialda expense turida 'salary' kodi mavjud."]
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Admin Panel

Django admin panelda:
- Kategoriyalar ro'yxati (rangli type badges)
- Global/Filial ko'rsatkichi
- Ierarxiya ko'rinishi
- Faol/nofaol filtrlash
- Qidiruv (name, code, branch name)

---

## Keyingi Yangilanishlar

- [ ] Kategoriya statistikasi (nechta tranzaksiya ishlatgan)
- [ ] Kategoriya export/import (CSV, Excel)
- [ ] Kategoriya arxivlash (soft delete o'rniga)
- [ ] Kategoriya tarjimon (uz, ru, en)
- [ ] Kategoriya icon/rang sozlamalari
