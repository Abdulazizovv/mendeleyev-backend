# O'quvchilar API

O'quvchilar va ularning yaqinlarini boshqarish uchun API'lar.

## Versiya Ma'lumotlari

### v2.2.0 (2025-12-23)
**Yangiliklar:**
- ✅ **Student Detail API takomillashtirildi**:
  - `recent_transactions` - Oxirgi 10 ta tranzaksiya
  - To'liq employee ma'lumotlari (avatar, role, phone)
  - To'liq kategori va kassa ma'lumotlari
- 📝 To'liq ma'lumot: [student-detail.md](./student-detail.md), [transactions.md](./transactions.md)

### v2.1.0 (2025-12-23)
**Yangiliklar:**
- ✅ Student yaratishda abonement sanalarini qo'lda belgilash:
  - `subscription_start_date` - Abonement boshlanish sanasini o'zingiz belgilang
  - `subscription_next_payment_date` - Keyingi to'lov sanasini o'zingiz belgilang
- ✅ **Chegirmalar tizimi**:
  - `discount_id` - Abonementga chegirma qo'llash
  - Foiz yoki aniq summa (Discount model)
  - Amal qilish muddati (valid_from, valid_until)
  - Avtomatik hisoblash (payment_due API'da)
- ✅ Moslashuvchan sana boshqaruvi (sana berilmasa avtomatik hisoblanadi)
- 📝 Use case'lar: Oyning boshidan abonement boshlash, maxsus to'lov jadvallar, chegirmalar

### v2.0.0 (2025-01-20)
**Yangiliklar:**
- ✅ Student yaratishda abonement avtomatik biriktiriladi (`subscription_plan_id`)
- ✅ `StudentSubscription` yaratish va boshqarish
- ✅ `next_payment_date` avtomatik hisoblash (tarif davriga ko'ra)
- ✅ Student Detail API: `subscriptions`, `payment_due`, `relatives` maydonlari
- ✅ To'lov workflow: Subscription → Payment → Transaction
- 📝 To'liq ma'lumot: [student-detail.md](./student-detail.md)

### v1.0.0
- Asosiy CRUD operatsiyalari
- Yaqinlar boshqaruvi
- Balance tracking

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
      "personal_number": "TAS-24-0001",
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
        "personal_number": "TAS-24-0001",
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
      "personal_number": "TAS-24-0001",
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
        "personal_number": "TAS-24-0001",
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
      "personal_number": "TAS-24-0001",
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
  "birth_certificate": "<file>",
  "passport_number": "AB1234567",
  "nationality": "UZ",
  "additional_fields": {
    "passport_issued_date": "2020-01-15",
    "passport_expiry_date": "2030-01-15"
  },
  "class_id": "uuid",
  "subscription_plan_id": "uuid",
  "subscription_start_date": "2025-12-23",
  "subscription_next_payment_date": "2026-01-23",
  "discount_id": "uuid",
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
- **Hujjatlar**: 
  - `birth_certificate` - Tu'gilganlik guvohnoma rasmi (file)
  - `passport_number` - Pasport yoki ID karta raqami
  - `nationality` - Millati (masalan: UZ, RU)
  - `additional_fields` - Qo'shimcha hujjat ma'lumotlari (JSON)

- **Abonement tizimi** (v2.0.0):
  - `subscription_plan_id` - Abonement tarifi ID (ixtiyoriy)
  - `subscription_start_date` - Abonement boshlanish sanasi (ixtiyoriy, agar berilmasa bugungi sana ishlatiladi)
  - `subscription_next_payment_date` - Keyingi to'lov sanasi (ixtiyoriy, agar berilmasa avtomatik hisoblanadi)
  - `discount_id` - Chegirma ID (ixtiyoriy, abonementga chegirma qo'llash uchun)
  
  - **Avtomatik amallar**:
    - `StudentSubscription` yaratiladi (o'quvchi va tarif orasida bog'lanish)
    - `start_date` = subscription_start_date yoki hozirgi sana
    - `next_payment_date` = subscription_next_payment_date yoki avtomatik hisoblangan sana
    - `total_debt` = 0 (boshlang'ich qarz yo'q)
  
  - **Qo'lda sana belgilash** (v2.0.0):
    - Abonement boshlanish sanasini o'zingiz belgilashingiz mumkin
    - Keyingi to'lov sanasini o'zingiz belgilashingiz mumkin
    - Agar sana berilmasa, avtomatik hisoblash ishlatiladi
  
  - **Avtomatik hisoblash** (sana berilmagan holda):
    - `monthly`: Keyingi to'lov = +1 oy
    - `quarterly`: Keyingi to'lov = +3 oy
    - `yearly`: Keyingi to'lov = +1 yil
  - **Muhim**: Abonement yaratiladi, lekin to'lov hali qilinmaydi (to'lov keyinchalik payment API orqali amalga oshiriladi)
  - **Student Detail API**: Yaratilgan abonement darhol student detail API'da ko'rinadi (`subscriptions`, `payment_due` maydonlari orqali)
  
- **Yaqinlar**: `relatives` array - bir vaqtning o'zida bir nechta yaqin qo'shish mumkin
  - Har bir yaqin uchun avtomatik `User` va `BranchMembership` (role=PARENT) yaratiladi
  - Agar yaqin allaqachon boshqa rolda bo'lsa, xatolik qaytariladi
  
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

**Response Eslatmalari:**
- Response'da abonement ma'lumotlari ko'rinmaydi (faqat asosiy student ma'lumotlari)
- **Abonement ma'lumotlarini ko'rish uchun**: Student Detail API'sini chaqiring:
  ```
  GET /api/v1/school/students/{student_id}/
  ```
  - Bu API `subscriptions`, `payment_due`, `relatives` va boshqa to'liq ma'lumotlarni qaytaradi
  - To'liq hujjat: [student-detail.md](./student-detail.md)

**Response Maydonlari:**
- Telefon raqam tasdiqlash shart emas
- Agar user allaqachon mavjud bo'lsa, ma'lumotlar yangilanadi
- `StudentBalance` avtomatik yaratiladi (signal orqali)
- `personal_number` avtomatik generatsiya qilinadi
- **Fayllar**: `birth_certificate` va `birth_certificate_url` - nisbiy va to'liq URL
  - `birth_certificate`: Nisbiy URL (masalan: `/media/students/birth_certificates/cert_123.pdf`)
  - `birth_certificate_url`: To'liq URL (masalan: `https://api.example.com/media/students/birth_certificates/cert_123.pdf`)

**Abonement yaratish misollari** (v2.0.0):

**1. Avtomatik sana hisoblash:**
```json
// Request
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "plan-uuid"  // Tarif ID
}

// Backend'da avtomatik bajariladi:
// 1. StudentSubscription yaratiladi:
//    - student_profile: ali (student)
//    - subscription_plan: plan-uuid
//    - start_date: 2025-12-23 (bugungi sana)
//    - next_payment_date: 2026-01-23 (agar monthly bo'lsa)
//    - total_debt: 0
//    - is_active: true
```

**2. Qo'lda sana belgilash:**
```json
// Request
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "plan-uuid",
  "subscription_start_date": "2025-12-01",
  "subscription_next_payment_date": "2026-01-01"
}

// Backend'da bajariladi:
// 1. StudentSubscription yaratiladi:
//    - start_date: 2025-12-01 (sizning berilgan sanangiz)
//    - next_payment_date: 2026-01-01 (sizning berilgan sanangiz)
//    - Boshqa maydonlar avtomatik to'ldiriladi
```

**3. Aralash (faqat start_date belgilash):**
```json
// Request
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "plan-uuid",
  "subscription_start_date": "2025-12-01"
  // next_payment_date berilmagan
}

// Backend'da bajariladi:
// 1. start_date = 2025-12-01 (sizning berilgan sanangiz)
// 2. next_payment_date = 2026-01-01 (start_date + 1 oy, agar monthly bo'lsa)
```

**Student Detail API'da ko'rinishi:**
```json
GET /api/v1/school/students/{ali-uuid}/
Response:
{
  ...
  "subscriptions": [
    {
      "id": "sub-uuid",
      "subscription_plan": {
        "id": "plan-uuid",
        "name": "Premium Oylik",
        "price": 500000,
        "period_type": "monthly"
      },
      "start_date": "2025-12-01",
      "next_payment_date": "2026-01-01",
      "is_active": true
    }
  ],
  "payment_due": [
    {
      "subscription_id": "sub-uuid",
      "current_amount": 500000,
      "debt_amount": 0,
      "total_amount": 500000,
      "next_due_date": "2026-01-01",
      "overdue_months": 0,
      "is_expired": false
    }
  ]
}
```

**Abonement yaratish use case'lari** (v2.1.0):

**Use Case 1: Oyning birinchi kunidan boshlamoqchi bo'lsangiz**
```json
// Masalan, hozir 2025-12-23, lekin siz abonementni 2026-01-01 dan boshlamoqchisiz
{
  "phone_number": "+998901234567",
  "first_name": "Sardor",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "subscription_start_date": "2026-01-01",
  "subscription_next_payment_date": "2026-02-01"
}

// Natija: Abonement 2026-01-01 dan boshlanadi, keyingi to'lov 2026-02-01
```

**Use Case 2: O'quvchi o'rtada kelgan (mid-month subscription)**
```json
// O'quvchi 2025-12-15 da keldi, lekin to'lovni yanvarning 10-kunida olmoqchisiz
{
  "phone_number": "+998901234567",
  "first_name": "Malika",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "subscription_start_date": "2025-12-15",
  "subscription_next_payment_date": "2026-01-10"
}

// Natija: Abonement 2025-12-15 dan, keyingi to'lov 2026-01-10
```

**Use Case 3: Chegirma/Imtiyoz (3 oy bepul kabi)**
```json
// Student 3 oy bepul oldi, to'lov 3 oydan keyin
{
  "phone_number": "+998901234567",
  "first_name": "Javohir",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "subscription_start_date": "2025-12-23",
  "subscription_next_payment_date": "2026-03-23"  // 3 oy keyingi
}

// Natija: Abonement bugun boshlanadi, lekin to'lov 3 oydan keyin
```

**Use Case 4: Maxsus to'lov jadvali (har 2 oyda to'lov)**
```json
// O'quvchi har 2 oyda to'laydi (quarterly emas, custom)
{
  "phone_number": "+998901234567",
  "first_name": "Dilshod",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "subscription_start_date": "2025-12-01",
  "subscription_next_payment_date": "2026-02-01"  // 2 oy keyingi
}

// Natija: Custom to'lov jadvali
```

**Use Case 5: Standart rejim (sanalar berilmagan)**
```json
// Eng oddiy variant - hamma narsa avtomatik
{
  "phone_number": "+998901234567",
  "first_name": "Aziza",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid"
}

// Natija: 
// - start_date = 2025-12-23 (bugungi sana)
// - next_payment_date = 2026-01-23 (agar monthly bo'lsa)
```

**Use Case 6: Chegirma qo'llash (foiz chegirma)**
```json
// 20% chegirma bilan abonement
{
  "phone_number": "+998901234567",
  "first_name": "Umid",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "discount_id": "discount-uuid"  // 20% chegirma
}

// Misol:
// - subscription_plan.price = 500,000 so'm
// - discount.discount_type = "percentage"
// - discount.amount = 20 (20%)
// - Chegirma summasi = 100,000 so'm
// - To'lanadigan summa = 400,000 so'm
```

**Use Case 7: Chegirma qo'llash (aniq summa)**
```json
// 50,000 so'm chegirma bilan abonement
{
  "phone_number": "+998901234567",
  "first_name": "Nodira",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "discount_id": "fixed-discount-uuid"  // 50,000 so'm chegirma
}

// Misol:
// - subscription_plan.price = 500,000 so'm
// - discount.discount_type = "fixed"
// - discount.amount = 50000 (aniq summa)
// - Chegirma summasi = 50,000 so'm
// - To'lanadigan summa = 450,000 so'm
```

**Use Case 8: Kompleks (sanalar + chegirma)**
```json
// Oyning 1-kunidan boshlanuvchi, chegirma bilan abonement
{
  "phone_number": "+998901234567",
  "first_name": "Shohruh",
  "branch_id": "branch-uuid",
  "subscription_plan_id": "monthly-plan-uuid",
  "subscription_start_date": "2026-01-01",
  "subscription_next_payment_date": "2026-02-01",
  "discount_id": "new-student-discount-uuid"  // Yangi o'quvchilar uchun 15%
}

// Natija:
// - Abonement 2026-01-01 dan boshlanadi
// - To'lov 2026-02-01 da kutilmoqda
// - 15% chegirma qo'llanadi
// - Student Detail API'da barcha ma'lumotlar ko'rinadi
```

**Chegirma Student Detail API'da ko'rinishi:**
```json
GET /api/v1/school/students/{student-uuid}/
Response:
{
  ...
  "subscriptions": [
    {
      "id": "sub-uuid",
      "subscription_plan": {
        "id": "plan-uuid",
        "name": "Premium Oylik",
        "price": 500000,
        "period_type": "monthly"
      },
      "discount": {
        "id": "discount-uuid",
        "name": "Yangi o'quvchilar uchun chegirma",
        "discount_type": "percentage",
        "amount": 20
      },
      "start_date": "2025-12-23",
      "next_payment_date": "2026-01-23",
      "is_active": true
    }
  ],
  "payment_due": [
    {
      "subscription_id": "sub-uuid",
      "current_amount": 500000,        // Asosiy narx
      "discount_amount": 100000,       // Chegirma summasi (20%)
      "amount_after_discount": 400000, // Chegirmadan keyingi narx
      "debt_amount": 0,
      "total_amount": 400000,          // Jami to'lanadigan
      "next_due_date": "2026-01-23",
      "overdue_months": 0,
      "is_expired": false,
      "has_discount": true             // Chegirma bormi
    }
  ]
}
```
// - next_payment_date = 2026-01-23 (agar monthly bo'lsa)
```

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
    "updated_at": "2024-01-15T10:30:00Z",
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
        "period": "monthly",
        "period_display": "Oylik"
      }
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Fayllar:**

- **birth_certificate**: Nisbiy URL (Django FileField)
- **birth_certificate_url**: To'liq URL (request.build_absolute_uri orqali yaratiladi)
  - Agar fayl bo'lmasa: `null`
  - Agar fayl bo'lsa: To'liq URL (masalan: `https://api.example.com/media/students/birth_certificates/cert_123.pdf`)

**Moliya Ma'lumotlari:**

Detail view da `balance` field to'liq moliyaviy ma'lumotlarni o'z ichiga oladi:

- **balance**: O'quvchi balansi va moliyaviy statistikalar
  - `id`: Balans ID
  - `balance`: Joriy balans (so'm)
  - `notes`: Eslatmalar
  - `updated_at`: Oxirgi yangilanish vaqti
  - `transactions_summary`: Tranzaksiyalar statistikasi
    - `total_income`: Jami kirim (so'm) - INCOME va PAYMENT turlari
    - `total_expense`: Jami chiqim (so'm) - EXPENSE, SALARY, REFUND turlari
    - `net_balance`: Sof balans (kirim - chiqim)
    - `transactions_count`: Tranzaksiyalar soni (faqat COMPLETED status)
  - `payments_summary`: To'lovlar statistikasi
    - `total_payments`: Jami to'lovlar (so'm)
    - `payments_count`: To'lovlar soni
    - `last_payment`: Oxirgi to'lov ma'lumotlari
      - `id`: To'lov ID
      - `amount`: To'lov summasi (final_amount)
      - `date`: To'lov sanasi (ISO format)
      - `period`: To'lov davri (monthly, yearly, va h.k.)
      - `period_display`: To'lov davri ko'rinishi (Oylik, Yillik, va h.k.)

---

### O'quvchini Yangilash

```
PATCH /api/v1/school/students/{student_id}/
```

**Permissions:** Super Admin, Branch Admin (o'z filialida)

**Qo'llab-quvvatlanadigan formatlar:** `multipart/form-data` yoki `application/json`

**Yangilanishi mumkin bo'lgan maydonlar:**
- `phone_number` (string): Foydalanuvchi telefon raqami (unikal, normalize qilinadi)
- `first_name`, `last_name`, `email`: Foydalanuvchi ma'lumotlari
- `avatar` (file): Global profil rasmi (User -> Profile.avatar)
- `middle_name`, `gender`, `date_of_birth`, `address`, `status`: O'quvchi profil maydonlari
- `birth_certificate` (file): Tu'gilganlik guvohnomasi
- `additional_fields` (object): Qo'shimcha ma'lumotlarni birlashtirib yangilash (merge)

**Misol (multipart/form-data):**
```
Content-Type: multipart/form-data

phone_number=+998901234567
first_name=Ali
last_name=Valiyev
avatar=@/path/to/avatar.jpg
middle_name=Olim o'g'li
gender=male
date_of_birth=2010-05-15
address=Toshkent shahri
status=active
birth_certificate=@/path/to/birth_certificate.pdf
additional_fields={"passport_number":"AB1234567","nationality":"UZ"}
```

**Misol (JSON):**
```json
{
  "phone_number": "+998901234567",
  "first_name": "Ali",
  "last_name": "Valiyev",
  "email": "ali@example.com",
  "middle_name": "Olim o'g'li",
  "gender": "male",
  "date_of_birth": "2010-05-15",
  "address": "Toshkent shahri",
  "status": "active",
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ"
  }
}
```

**Response:** `200 OK` — yangilangan o'quvchi ma'lumotlari (avatar/birth_certificate uchun nisbiy va to'liq URL'lar):

- `avatar`, `avatar_url`
- `birth_certificate`, `birth_certificate_url`

**Eslatmalar:**
- `additional_fields` mavjud ma'lumotlar bilan birlashtiriladi (merge)
- `avatar` va `birth_certificate` fayllari uchun multipart foydalaning
- Telefon raqam unikal bo'lishi shart; agar boshqa foydalanuvchida mavjud bo'lsa xatolik qaytariladi

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
      "photo": "/media/students/relatives/photo_123.jpg",
      "photo_url": "https://api.example.com/media/students/relatives/photo_123.jpg",
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

### O'quvchi Hujjatlarini Yangilash

```
PATCH /api/v1/school/students/{student_id}/documents/
```

**Permissions:** IsAuthenticated (o'quvchi yaratish ruxsatiga ega bo'lganlar)

**Request Body:**
```json
{
  "birth_certificate": "<file>",
  "passport_number": "AB1234567",
  "nationality": "UZ",
  "additional_fields": {
    "passport_issued_date": "2020-01-15",
    "passport_expiry_date": "2030-01-15"
  }
}
```

**Eslatmalar:**
- Barcha maydonlar ixtiyoriy
- `passport_number` va `nationality` `additional_fields` ga saqlanadi
- `additional_fields` mavjud ma'lumotlar bilan birlashtiriladi (update, merge)

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "personal_number": "ST-2024-0001",
  "birth_certificate": "/media/students/birth_certificates/...",
  "additional_fields": {
    "passport_number": "AB1234567",
    "nationality": "UZ",
    "passport_issued_date": "2020-01-15",
    "passport_expiry_date": "2030-01-15"
  },
  ...
}
```

---

## Misol So'rovlar

### 1. O'quvchilarni qidirish

```bash
# Shaxsiy raqam bo'yicha
GET /api/v1/school/students/?branch_id=uuid&search=TAS-24

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
   - `personal_number` - Avtomatik generatsiya qilinadi
     - **Format**: `{BRANCH_CODE}-{ACADEMIC_YEAR_SHORT}-{ORDER}`
     - **Misol**: `TAS-24-0001`, `SAM-24-0001`
     - **Tushuntirish**:
       - `BRANCH_CODE`: Filial kodi (masalan: TAS, SAM, BUK) - agar yo'q bo'lsa, "ST" ishlatiladi
       - `ACADEMIC_YEAR_SHORT`: Akademik yil qisqa versiyasi (masalan: "2024-2025" -> "24")
       - `ORDER`: Tartib raqami (4 xonali, masalan: 0001, 0002)
     - Har bir filial va akademik yil uchun alohida raqamlar

2. **O'quvchi Yaratish Xususiyatlari:**
   - **Nested Serializer**: Yaqinlarni bir vaqtning o'zida yaratish mumkin
   - **Atomic Operatsiyalar**: Barcha operatsiyalar bir xatoda bajariladi (xato bo'lsa rollback)
   - **Ixtiyoriy Maydonlar**: Faqat `phone_number`, `first_name`, `branch_id` majburiy
   - **To'liq Ma'lumotlar**: Adminlar barcha ma'lumotlarni bir vaqtda to'ldirish imkoniyatiga ega
   - **Sinfga Biriktirish**: O'quvchini yaratishda sinfga biriktirish mumkin
   - **Abonement Tanlash**: `subscription_plan_id` orqali abonement tanlash mumkin
     - Abonement tanlansa, avtomatik `Payment` va `Transaction` yaratiladi
     - Agar kassa bo'lmasa, avtomatik "Asosiy kassa" yaratiladi
   - **Yaqinlar Avtomatik Yaratish**: Yaqinlar belgilanganda:
     - Har bir yaqin uchun `User` yaratiladi/yangilanadi
     - Har bir yaqin uchun `BranchMembership` (role=PARENT) yaratiladi
     - `StudentRelative` yaratiladi
   - **Hujjat Ma'lumotlari**: 
     - `birth_certificate` - Tu'gilganlik guvohnoma rasmi
     - `passport_number` - Pasport yoki ID karta raqami
     - `nationality` - Millati
     - `additional_fields` - Qo'shimcha hujjat ma'lumotlari

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

