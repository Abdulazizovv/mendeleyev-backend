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
