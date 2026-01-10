# Branch API

Filiallar ikki turda: `school` yoki `center`. Har bir branch umumiy tizimga bog'langan, lekin user-rol munosabatlari per-branch saqlanadi.

## Model (qisqacha)

- `id`, `name`, `type` (school|center), `slug`, `address`, `phone_number`, `email`, `status`, timestamps, soft-delete, audit trail (created_by, updated_by).

## Endpointlar

### Managed Branches

- **GET** `/api/branches/managed/` — Admin uchun boshqariladigan filiallar ro'yxati
  - SuperAdmin: barcha faol filiallar
  - BranchAdmin: faqat o'z filiallari
  - Response: `[{"id": "<uuid>", "name": "...", "status": "active", "type": "school"}]`

- **PATCH** `/api/branches/managed/` — SuperAdmin uchun boshqa adminning managed branches ro'yxatini yangilash
  - Request: `{"user_id": "<uuid>", "branch_ids": ["<uuid>", ...]}`
  - Response: `{"detail": "Managed branches updated successfully."}`

### Roles (Rollar)

- **GET** `/api/branches/{branch_id}/roles/` — Filialdagi rollar ro'yxati
  - SuperAdmin: barcha rollar
  - BranchAdmin: faqat o'z filialidagi rollar
  - Response: `[{"id": "<uuid>", "name": "Director", "permissions": {...}, "description": "...", ...}]`

- **POST** `/api/branches/{branch_id}/roles/` — Yangi rol yaratish
  - SuperAdmin: istalgan filialga rol qo'sha oladi
  - BranchAdmin: faqat o'z filialiga rol qo'sha oladi
  - Request:
    ```json
    {
      "name": "Director",
      "permissions": {"academic": ["view_grades", "edit_grades"]},
      "description": "Maktab direktori",
      "is_active": true
    }
    ```
  - Response: `{"id": "<uuid>", "name": "Director", ...}`
  
  **Eslatma**: Maosh endi Role modelida emas, balki BranchMembership modelida saqlanadi.

- **GET** `/api/branches/{branch_id}/roles/{id}/` — Rol detallari
- **PATCH** `/api/branches/{branch_id}/roles/{id}/` — Rolni tahrirlash
- **DELETE** `/api/branches/{branch_id}/roles/{id}/` — Rolni o'chirish

### Memberships (A'zoliklar)

- **GET** `/api/branches/{branch_id}/memberships/` — Filialdagi a'zoliklar ro'yxati
  - SuperAdmin: barcha a'zoliklar
  - BranchAdmin: faqat o'z filialidagi a'zoliklar
  - Response:
    ```json
    [
      {
        "id": "<uuid>",
        "user": "<uuid>",
        "user_phone": "+998901234567",
        "user_name": "John Doe",
        "branch": "<uuid>",
        "branch_name": "Alpha School",
        "role": "teacher",
        "role_ref": "<uuid>",
        "role_name": "Math Teacher",
        "effective_role": "Math Teacher",
        "title": "Senior Teacher",
        "monthly_salary": 5000000,
        "balance": 1500000,
        "salary": 5000000,
        "created_at": "...",
        "updated_at": "..."
      }
    ]
    ```

### Balance Management (Balans boshqaruvi)

- **POST** `/api/branches/{branch_id}/memberships/{membership_id}/balance/` — Balansni yangilash
  - SuperAdmin: istalgan a'zolikning balansini yangilay oladi
  - BranchAdmin: faqat o'z filialidagi a'zoliklarning balansini yangilay oladi
  - Request:
    ```json
    {
      "amount": 500000,
      "note": "Ish haqi to'lovi"
    }
    ```
  - `amount` musbat bo'lsa qo'shadi, manfiy bo'lsa ayiradi (butun son, so'm)
  - Response: Yangilangan membership ma'lumotlari

### Branch Settings (Filial sozlamalari)

- **GET** `/api/branches/{branch_id}/settings/` — Filial sozlamalarini ko'rish
  - SuperAdmin: istalgan filial sozlamalarini ko'rishi mumkin
  - BranchAdmin: faqat o'z filiali sozlamalarini ko'rishi mumkin
  - Response:
    ```json
    {
      "id": "<uuid>",
      "branch": "<uuid>",
      "branch_name": "Alpha School",
      "lesson_duration_minutes": 45,
      "break_duration_minutes": 10,
      "school_start_time": "08:00:00",
      "school_end_time": "17:00:00",
      "lunch_break_start": "12:00:00",
      "lunch_break_end": "13:00:00",
      "academic_year_start_month": 9,
      "academic_year_end_month": 6,
      "currency": "UZS",
      "currency_symbol": "so'm",
      "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
      "holidays": ["2026-01-01", "2026-03-08"],
      "daily_lesson_start_time": "08:00:00",
      "daily_lesson_end_time": "14:00:00",
      "max_lessons_per_day": 7,
      "additional_settings": {},
      "created_at": "...",
      "updated_at": "..."
    }
    ```

- **PATCH** `/api/branches/{branch_id}/settings/` — Filial sozlamalarini yangilash
  - SuperAdmin: istalgan filial sozlamalarini yangilashi mumkin
  - BranchAdmin: faqat o'z filiali sozlamalarini yangilashi mumkin
  - Request (barcha maydonlar ixtiyoriy):
    ```json
    {
      "lesson_duration_minutes": 45,
      "break_duration_minutes": 10,
      "school_start_time": "08:00",
      "school_end_time": "17:00",
      "lunch_break_start": "12:00",
      "lunch_break_end": "13:00",
      "working_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "holidays": ["2026-01-01", "2026-03-21"],
      "max_lessons_per_day": 7
    }
    ```
  - **Validation**:
    - `lunch_break_start` va `lunch_break_end` ikkalasi ham kiritilishi yoki ikkalasi ham bo'sh bo'lishi kerak
    - Tushlik tanaffusi boshlanish vaqti tugash vaqtidan oldin bo'lishi kerak
    - Tushlik tanaffusi maktab ish vaqti ichida bo'lishi kerak
    - Dars davomiyligi 0 dan katta bo'lishi kerak
    - Tanaffus davomiyligi 0 dan kichik bo'lmasligi kerak

## BranchSettings Model

Har bir filial sozlamalari quyidagi maydonlarga ega:

### Dars jadvali sozlamalari:
- `lesson_duration_minutes` — Dars davomiyligi (daqiqa, default: 45)
- `break_duration_minutes` — Tanaffus davomiyligi (daqiqa, default: 10)
- `school_start_time` — Maktab boshlanish vaqti (default: "08:00")
- `school_end_time` — Maktab tugash vaqti (default: "17:00")
- `lunch_break_start` — Tushlik tanaffusi boshlanish vaqti (ixtiyoriy)
- `lunch_break_end` — Tushlik tanaffusi tugash vaqti (ixtiyoriy)

### Akademik sozlamalar:
- `academic_year_start_month` — Akademik yil boshlanish oyi (1-12, default: 9)
- `academic_year_end_month` — Akademik yil tugash oyi (1-12, default: 6)
- `working_days` — Ish kunlari ro'yxati (JSON, masalan: ["monday", "tuesday", ...])
- `holidays` — Bayram kunlari (JSON, masalan: ["2026-01-01", "2026-03-08"])
- `daily_lesson_start_time` — Birinchi dars boshlanish vaqti (default: "08:00")
- `daily_lesson_end_time` — Oxirgi dars tugash vaqti (default: "14:00")
- `max_lessons_per_day` — Kunlik maksimal darslar soni (default: 7)

### Moliya sozlamalari:
- `currency` — Valyuta (default: "UZS")
- `currency_symbol` — Valyuta belgisi (default: "so'm")

### Qo'shimcha:
- `additional_settings` — Qo'shimcha sozlamalar (JSON)

**Eslatma**: Tushlik tanaffusi ixtiyoriy. Agar tushlik tanaffusi kerak bo'lsa, `lunch_break_start` va `lunch_break_end` ikkalasi ham kiritilishi kerak.

## Ruxsatlar

- `IsSuperAdmin` — Platforma bo'ylab barcha huquqlar
- `IsBranchAdmin` — Faqat o'z filialida admin huquqlari
- `HasBranchRole` — Filial kontekstida rol tekshirish

## Role Model

Har bir rol quyidagi maydonlarga ega:

- `name` — Rol nomi (masalan: "Director", "Teacher", "Guard")
- `branch` — Filial (null bo'lishi mumkin — umumiy rollar uchun)
- `permissions` — JSON formatida ruxsatlar
- `description` — Rol tavsifi
- `is_active` — Faol/faol emas

**Eslatma**: Maosh endi Role modelida emas, balki BranchMembership modelida saqlanadi. Bu har bir xodim uchun alohida maosh belgilash imkonini beradi.

## Permissions Format

Permissions JSON formatida saqlanadi:

```json
{
  "academic": ["view_grades", "edit_grades", "view_schedule"],
  "finance": ["view_payments", "edit_payments"],
  "schedule": ["view_schedule", "edit_schedule"],
  "attendance": ["view_attendance", "edit_attendance"]
}
```

## BranchMembership Model

Har bir a'zolik quyidagi maydonlarga ega:

- `user` — Foydalanuvchi
- `branch` — Filial
- `role` — Legacy rol (CharField)
- `role_ref` — Yangi rol (ForeignKey to Role)
- `effective_role` — Samarali rol nomi (role_ref.name yoki role)
- `title` — Lavozim
- `monthly_salary` — Oylik maosh (so'm, butun son). Har bir xodim uchun alohida belgilanadi.
- `balance` — Balans (so'm, butun son). Ish haqini ko'rish va boshqarish uchun.
- `salary` — Maosh (monthly_salary dan olinadi, computed field)
- Audit trail: `created_by`, `updated_by`

**Eslatma**: Maosh va balans butun sonlar (IntegerField) sifatida saqlanadi, chunki valyuta so'm va kasr qismlar kerak emas.
