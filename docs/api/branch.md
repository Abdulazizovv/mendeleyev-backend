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
  - Response: `[{"id": "<uuid>", "name": "Director", "salary_type": "monthly", "monthly_salary": "5000000", ...}]`

- **POST** `/api/branches/{branch_id}/roles/` — Yangi rol yaratish
  - SuperAdmin: istalgan filialga rol qo'sha oladi
  - BranchAdmin: faqat o'z filialiga rol qo'sha oladi
  - Request:
    ```json
    {
      "name": "Director",
      "salary_type": "monthly",
      "monthly_salary": "5000000",
      "permissions": {"academic": ["view_grades", "edit_grades"]},
      "description": "Maktab direktori",
      "is_active": true
    }
    ```
  - Response: `{"id": "<uuid>", "name": "Director", ...}`

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
        "balance": "1500000.00",
        "salary": "5000000.00",
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
      "amount": "500000.00",
      "note": "Ish haqi to'lovi"
    }
    ```
  - `amount` musbat bo'lsa qo'shadi, manfiy bo'lsa ayiradi
  - Response: Yangilangan membership ma'lumotlari

## Ruxsatlar

- `IsSuperAdmin` — Platforma bo'ylab barcha huquqlar
- `IsBranchAdmin` — Faqat o'z filialida admin huquqlari
- `HasBranchRole` — Filial kontekstida rol tekshirish

## Role Model

Har bir rol quyidagi maydonlarga ega:

- `name` — Rol nomi (masalan: "Director", "Teacher", "Guard")
- `branch` — Filial (null bo'lishi mumkin — umumiy rollar uchun)
- `salary_type` — Maosh turi: `monthly`, `hourly`, `per_item`
- `monthly_salary` — Oylik maosh (so'm)
- `hourly_rate` — Soatlik stavka (keyinroq)
- `per_item_rate` — Har bir uchun stavka (keyinroq)
- `permissions` — JSON formatida ruxsatlar
- `description` — Rol tavsifi
- `is_active` — Faol/faol emas

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
- `balance` — Balans (so'm)
- `salary` — Maosh (role_ref dan olinadi)
- Audit trail: `created_by`, `updated_by`
