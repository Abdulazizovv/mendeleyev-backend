# O'quvchilar API

O'quvchilar va ularning yaqinlarini boshqarish uchun API'lar.

## Umumiy Ma'lumotlar

- **Base URL**: `/api/v1/school/students/`
- **Authentication**: JWT Token talab qilinadi
- **Permissions**: 
  - O'quvchi yaratish: `CanCreateStudent` (Super Admin, Branch Admin, Class Teacher)
  - O'quvchilar ro'yxati: Branch Admin, Teacher
- **Pagination**: Default 20, max 100
- **Filtering, Search, Ordering**: Qo'llab-quvvatlanadi

## API Endpoints

### User Mavjudligini Tekshirish

```
GET /api/v1/school/students/check-user/
POST /api/v1/school/students/check-user/
```

**Query Params / Body:**
- `phone_number` (string, required): Telefon raqami (masalan: +998901234567)
- `branch_id` (UUID, optional): Filial ID (agar berilmasa, barcha filiallarda qidiriladi)

**Response:**
```json
{
  "exists_in_branch": true,
  "exists_globally": true,
  "branch_data": {
    "branch_id": "uuid",
    "branch_name": "Filial nomi",
    "role": "student",
    "role_display": "O'quvchi",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "student_profile": {
      "id": "uuid",
      "personal_number": "ST-2024-0001",
      "full_name": "Ali Olim o'g'li Valiyev",
      "status": "active",
      "status_display": "Aktiv",
      "gender": "male",
      "date_of_birth": "2010-05-15"
    }
  },
  "all_branches_data": [
    {
      "branch_id": "uuid",
      "branch_name": "Filial nomi",
      "role": "student",
      "role_display": "O'quvchi",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "student_profile": {
        "id": "uuid",
        "personal_number": "ST-2024-0001",
        "full_name": "Ali Olim o'g'li Valiyev",
        "status": "active",
        "status_display": "Aktiv",
        "gender": "male",
        "date_of_birth": "2010-05-15"
      }
    }
  ]
}
```

**Eslatmalar:**
- Agar user topilmasa: `exists_in_branch: false`, `exists_globally: false`, `branch_data: null`, `all_branches_data: []`
- Agar user boshqa filialda bo'lsa: `exists_in_branch: false`, `exists_globally: true`, `branch_data: null`, `all_branches_data: [...]`
- Agar user berilgan filialda bo'lsa: `exists_in_branch: true`, `exists_globally: true`, `branch_data: {...}`, `all_branches_data: [...]`

---

### O'quvchi Yaqinlari Mavjudligini Tekshirish

```
GET /api/v1/school/students/check-relative/
POST /api/v1/school/students/check-relative/
```

**Query Params / Body:**
- `phone_number` (string, required): Telefon raqami (masalan: +998901234567)
- `branch_id` (UUID, optional): Filial ID (agar berilmasa, barcha filiallarda qidiriladi)

**Response:**
```json
{
  "exists_in_branch": true,
  "exists_globally": true,
  "branch_data": {
    "id": "uuid",
    "relationship_type": "father",
    "relationship_type_display": "Otasi",
    "full_name": "Olim Karim o'g'li Valiyev",
    "phone_number": "+998901234568",
    "email": "olim@example.com",
    "is_primary_contact": true,
    "is_guardian": true,
    "student": {
      "id": "uuid",
      "personal_number": "ST-2024-0001",
      "full_name": "Ali Olim o'g'li Valiyev",
      "branch_id": "uuid",
      "branch_name": "Filial nomi"
    },
    "created_at": "2024-01-01T00:00:00Z"
  },
  "all_branches_data": [
    {
      "id": "uuid",
      "relationship_type": "father",
      "relationship_type_display": "Otasi",
      "full_name": "Olim Karim o'g'li Valiyev",
      "phone_number": "+998901234568",
      "email": "olim@example.com",
      "is_primary_contact": true,
      "is_guardian": true,
      "student": {
        "id": "uuid",
        "personal_number": "ST-2024-0001",
        "full_name": "Ali Olim o'g'li Valiyev",
        "branch_id": "uuid",
        "branch_name": "Filial nomi"
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Eslatmalar:**
- Agar yaqin topilmasa: `exists_in_branch: false`, `exists_globally: false`, `branch_data: null`, `all_branches_data: []`
- Agar yaqin boshqa filialda bo'lsa: `exists_in_branch: false`, `exists_globally: true`, `branch_data: null`, `all_branches_data: [...]`
- Agar yaqin berilgan filialda bo'lsa: `exists_in_branch: true`, `exists_globally: true`, `branch_data: {...}`, `all_branches_data: [...]`

---

### O'quvchilar Ro'yxati

```
GET /api/v1/school/students/
```

**Query Parameters:**
- `branch_id` (UUID, required): Filial ID
- `page` (integer, optional): Sahifa raqami (default: 1)
- `page_size` (integer, optional): Sahifadagi elementlar soni (default: 20, max: 100)
- `search` (string, optional): Qidirish (shaxsiy raqam, ism, telefon, email)
- `ordering` (string, optional): Tartiblash (`personal_number`, `first_name`, `last_name`, `created_at`, `date_of_birth`, `gender`, `status`, `-created_at`, `-first_name`, va boshqalar)
- `personal_number` (string, optional): Shaxsiy raqam bo'yicha qidirish
- `gender` (string, optional): Jinsi bo'yicha filter (`male`, `female`, `other`, `unspecified`)
- `status` (string, optional): O'quvchi holati (`active`, `archived`, `suspended`, `graduated`, `transferred`)
- `date_of_birth` (date, optional): Tu'gilgan sana bo'yicha filter
- `date_of_birth__gte` (date, optional): Tu'gilgan sana (dan)
- `date_of_birth__lte` (date, optional): Tu'gilgan sana (gacha)
- `first_name` (string, optional): Ism bo'yicha qidirish
- `last_name` (string, optional): Familiya bo'yicha qidirish
- `phone_number` (string, optional): Telefon raqam bo'yicha qidirish
- `email` (string, optional): Email bo'yicha qidirish
- `class_id` (UUID, optional): Sinf ID bo'yicha filter
- `grade_level` (integer, optional): Sinf darajasi bo'yicha filter (1-11)
- `created_at__gte` (datetime, optional): Yaratilgan sana (dan)
- `created_at__lte` (datetime, optional): Yaratilgan sana (gacha)

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8080/api/v1/school/students/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "personal_number": "ST-2024-0001",
      "user_id": "uuid",
      "phone_number": "+998901234567",
      "first_name": "Ali",
      "last_name": "Valiyev",
      "middle_name": "Olim o'g'li",
      "full_name": "Ali Olim o'g'li Valiyev",
      "email": "ali@example.com",
      "branch_id": "uuid",
      "branch_name": "Filial nomi",
      "gender": "male",
      "status": "active",
      "status_display": "Aktiv",
      "date_of_birth": "2010-05-15",
      "address": "Toshkent shahri, Chilonzor tumani",
      "birth_certificate": null,
      "additional_fields": {},
      "current_class": {
        "id": "uuid",
        "name": "5-A",
        "academic_year": "2024-2025"
      },
      "relatives_count": 2,
      "balance": {
        "balance": 500000
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Eslatma:** List view'da faqat balans summasi ko'rsatiladi. To'liq moliyaviy ma'lumotlar uchun detail API'sini ishlating.

**Student Status Values:**
- `active` - Aktiv
- `archived` - Arxivlangan
- `suspended` - Muzlatilgan
- `graduated` - Bitirgan
- `transferred` - O'tkazilgan

---

### O'quvchi Yaratish

```
POST /api/v1/school/students/create/
```

**Permissions:** Super Admin, Branch Admin (faqat o'z filialida), Class Teacher (faqat o'z sinfida)

**Request Body:**
```json
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "email": "ali@example.com",
  "password": "SecurePassword123",
  "branch_id": "uuid",
  "middle_name": "Olim o'g'li",
  "gender": "male",
  "status": "active",
  "date_of_birth": "2010-05-15",
  "address": "Toshkent shahri, Chilonzor tumani",
  "birth_certificate": null,
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ"
  },
  "class_id": "uuid",
  "relatives": [
    {
      "relationship_type": "father",
      "first_name": "Olim",
      "middle_name": "Karim o'g'li",
      "last_name": "Valiyev",
      "phone_number": "+998901234568",
      "email": "olim@example.com",
      "gender": "male",
      "date_of_birth": "1980-01-01",
      "address": "Toshkent shahri",
      "workplace": "Ish joyi",
      "position": "Lavozim",
      "passport_number": "AB1234568",
      "is_primary_contact": true,
      "is_guardian": true,
      "additional_info": {},
      "notes": "Eslatmalar"
    },
    {
      "relationship_type": "mother",
      "first_name": "Dilnoza",
      "middle_name": "Olim qizi",
      "last_name": "Valiyeva",
      "phone_number": "+998901234569",
      "email": "dilnoza@example.com",
      "gender": "female",
      "is_primary_contact": false,
      "is_guardian": true
    }
  ]
}
```

**Eslatmalar:**
- **Majburiy maydonlar**: `phone_number`, `first_name`, `branch_id`
- **Ixtiyoriy maydonlar**: Qolgan barcha maydonlar ixtiyoriy
- **Yaqinlar**: `relatives` array - bir vaqtning o'zida bir nechta yaqin qo'shish mumkin
- **Atomic operatsiyalar**: Barcha operatsiyalar bir xatoda bajariladi (agar xato bo'lsa, rollback)
- **Sinfga biriktirish**: `class_id` orqali sinfga biriktirish mumkin

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "personal_number": "ST-2024-0001",
  "user_id": "uuid",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "middle_name": "Olim o'g'li",
  "full_name": "Ali Olim o'g'li Valiyev",
  "email": "ali@example.com",
  "branch_id": "uuid",
  "branch_name": "Filial nomi",
  "gender": "male",
  "status": "active",
  "status_display": "Aktiv",
  "date_of_birth": "2010-05-15",
  "address": "Toshkent shahri, Chilonzor tumani",
  "birth_certificate": null,
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ"
  },
  "current_class": {
    "id": "uuid",
    "name": "5-A",
    "academic_year": "2024-2025"
  },
  "relatives_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Eslatmalar:**
- Telefon raqam tasdiqlash shart emas
- Agar user allaqachon mavjud bo'lsa, ma'lumotlar yangilanadi
- `StudentBalance` avtomatik yaratiladi (signal orqali)
- `personal_number` avtomatik generatsiya qilinadi

---

### O'quvchi Ma'lumotlari

```
GET /api/v1/school/students/{student_id}/
```

**Response:**
```json
{
  "id": "uuid",
  "personal_number": "ST-2024-0001",
  "user_id": "uuid",
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "middle_name": "Olim o'g'li",
  "full_name": "Ali Olim o'g'li Valiyev",
  "email": "ali@example.com",
  "branch_id": "uuid",
  "branch_name": "Filial nomi",
  "gender": "male",
  "status": "active",
  "status_display": "Aktiv",
  "date_of_birth": "2010-05-15",
  "address": "Toshkent shahri, Chilonzor tumani",
  "birth_certificate": null,
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ"
  },
  "current_class": {
    "id": "uuid",
    "name": "5-A",
    "academic_year": "2024-2025"
  },
  "relatives_count": 2,
  "balance": {
    "id": "uuid",
    "balance": 500000,
    "notes": "",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "transactions_summary": {
    "total_income": 2000000,
    "total_expense": 0,
    "net_balance": 2000000,
    "transactions_count": 5
  },
  "payments_summary": {
    "total_payments": 2000000,
    "payments_count": 2,
    "last_payment": {
      "id": "uuid",
      "amount": 1400000,
      "date": "2024-01-15T10:00:00Z",
      "period": "Oylik"
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Moliya Ma'lumotlari:**

- **balance**: O'quvchi balansi (StudentBalance)
  - `id`: Balans ID
  - `balance`: Joriy balans (so'm)
  - `notes`: Eslatmalar
  - `updated_at`: Oxirgi yangilanish vaqti

- **transactions_summary**: Tranzaksiyalar statistikasi
  - `total_income`: Jami kirim (so'm)
  - `total_expense`: Jami chiqim (so'm)
  - `net_balance`: Sof balans (kirim - chiqim)
  - `transactions_count`: Tranzaksiyalar soni

- **payments_summary**: To'lovlar statistikasi
  - `total_payments`: Jami to'lovlar (so'm)
  - `payments_count`: To'lovlar soni
  - `last_payment`: Oxirgi to'lov ma'lumotlari
    - `id`: To'lov ID
    - `amount`: To'lov summasi
    - `date`: To'lov sanasi
    - `period`: To'lov davri (Oylik, Yillik, va h.k.)

---

### O'quvchi Yaqinlari

#### Yaqinlar ro'yxati
```
GET /api/v1/school/students/{student_id}/relatives/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "student_profile": "uuid",
    "relationship_type": "father",
    "relationship_type_display": "Otasi",
    "first_name": "Olim",
    "last_name": "Valiyev",
    "middle_name": "Karim o'g'li",
    "full_name": "Olim Karim o'g'li Valiyev",
    "phone_number": "+998901234568",
    "email": "olim@example.com",
    "gender": "male",
    "date_of_birth": "1980-01-01",
    "address": "Toshkent shahri",
    "workplace": "Ish joyi",
    "position": "Lavozim",
    "passport_number": "AB1234568",
    "photo": null,
    "is_primary_contact": true,
    "is_guardian": true,
    "additional_info": {},
    "notes": "Eslatmalar",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### Yaqin qo'shish
```
POST /api/v1/school/students/{student_id}/relatives/
```

**Request Body:**
```json
{
  "relationship_type": "father",
  "first_name": "Olim",
  "last_name": "Valiyev",
  "middle_name": "Karim o'g'li",
  "phone_number": "+998901234568",
  "email": "olim@example.com",
  "gender": "male",
  "date_of_birth": "1980-01-01",
  "address": "Toshkent shahri",
  "workplace": "Ish joyi",
  "position": "Lavozim",
  "passport_number": "AB1234568",
  "is_primary_contact": true,
  "is_guardian": true,
  "additional_info": {},
  "notes": "Eslatmalar"
}
```

**Relationship Types:**
- `father` - Otasi
- `mother` - Onasi
- `brother` - Akasi
- `sister` - Opasi
- `grandfather` - Bobosi
- `grandmother` - Buvisi
- `uncle` - Amakisi/Tog'asi
- `aunt` - Xolasi/Teyzasi
- `guardian` - Vasiy
- `other` - Boshqa

---

## Misol So'rovlar

### 1. O'quvchilarni qidirish

```bash
# Shaxsiy raqam bo'yicha
GET /api/v1/school/students/?branch_id=uuid&search=ST-2024

# Ism bo'yicha
GET /api/v1/school/students/?branch_id=uuid&search=Ali

# Telefon bo'yicha
GET /api/v1/school/students/?branch_id=uuid&phone_number=+998901234567
```

### 2. Filtering

```bash
# Faqat aktiv o'quvchilar
GET /api/v1/school/students/?branch_id=uuid&status=active

# Faqat qizlar
GET /api/v1/school/students/?branch_id=uuid&gender=female

# Muayyan sinf
GET /api/v1/school/students/?branch_id=uuid&class_id=uuid

# Muayyan sinf darajasi
GET /api/v1/school/students/?branch_id=uuid&grade_level=5

# Tu'gilgan sana oralig'i
GET /api/v1/school/students/?branch_id=uuid&date_of_birth__gte=2010-01-01&date_of_birth__lte=2010-12-31
```

### 3. Ordering

```bash
# Ism bo'yicha tartiblash
GET /api/v1/school/students/?branch_id=uuid&ordering=first_name

# Teskari tartib
GET /api/v1/school/students/?branch_id=uuid&ordering=-created_at

# Bir nechta field bo'yicha
GET /api/v1/school/students/?branch_id=uuid&ordering=status,-created_at
```

### 4. Pagination

```bash
# 2-sahifa, 10 ta element
GET /api/v1/school/students/?branch_id=uuid&page=2&page_size=10
```

---

## Xatoliklar

### 400 Bad Request
```json
{
  "detail": "Filial ID talab qilinadi."
}
```

```json
{
  "phone_number": ["Bu telefon raqami allaqachon bu filialda o'quvchi sifatida ro'yxatdan o'tgan."]
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
  "detail": "O'quvchi topilmadi."
}
```

---

## Eslatmalar

1. **Avtomatik Yaratiladigan Modellar:**
   - `StudentBalance` - `StudentProfile` yaratilganda avtomatik yaratiladi (signal orqali)
   - `personal_number` - Avtomatik generatsiya qilinadi (masalan: ST-2024-0001)

2. **O'quvchi Yaratish Xususiyatlari:**
   - **Nested Serializer**: Yaqinlarni bir vaqtning o'zida yaratish mumkin
   - **Atomic Operatsiyalar**: Barcha operatsiyalar bir xatoda bajariladi (xato bo'lsa rollback)
   - **Ixtiyoriy Maydonlar**: Faqat `phone_number`, `first_name`, `branch_id` majburiy
   - **To'liq Ma'lumotlar**: Adminlar barcha ma'lumotlarni bir vaqtda to'ldirish imkoniyatiga ega
   - **Sinfga Biriktirish**: O'quvchini yaratishda sinfga biriktirish mumkin

2. **Moliya Integratsiyasi:**
   - **List View**: Faqat balans summasi ko'rsatiladi (`balance: { balance: 500000 }`)
   - **Detail View**: To'liq moliyaviy ma'lumotlar ko'rsatiladi:
     - `balance` - O'quvchi joriy balansi (to'liq ma'lumotlar)
     - `transactions_summary` - Tranzaksiyalar statistikasi (kirim, chiqim, sof balans)
     - `payments_summary` - To'lovlar statistikasi (jami to'lovlar, oxirgi to'lov)
   - Barcha moliyaviy ma'lumotlar so'm (butun sonlar) formatida
   - Optimizatsiya: List view'da faqat kerakli ma'lumotlar yuklanadi

2. **Permissions:**
   - Super Admin: Barcha filiallarda o'quvchi yaratishi mumkin
   - Branch Admin: Faqat o'z filialida
   - Class Teacher: Faqat o'z sinfida (sinf rahbar bo'lsa)

3. **Filtering va Search:**
   - Barcha list endpointlar filtering, search va ordering qo'llab-quvvatlaydi
   - Pagination mavjud (default: 20, max: 100)

4. **Student Status:**
   - Default: `active`
   - Status o'zgartirish orqali o'quvchini arxivlash, muzlatish yoki boshqa holatga o'tkazish mumkin

