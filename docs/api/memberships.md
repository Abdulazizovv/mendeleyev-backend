# Memberships API — Filial A'zoliklari

Filialdagi xodimlar va o'quvchilarning a'zoliklarini (BranchMembership) boshqarish va ko'rish uchun API.

## Authentication

- JWT talab qilinadi: `Authorization: Bearer <access_token>`
- Filial konteksti: `X-Branch-Id: <branch_uuid>` header orqali (yo'l parametrida `branch_id` ham bor).

## Permissions

- Read: `branch_admin`, `super_admin` (hozircha ro'yxatni faqat adminlar ko'radi)
- Create: `super_admin` (faqat super admin API orqali a'zolik yaratadi)
- Balance update: `branch_admin`, `super_admin`

## Endpoint

**GET** `/api/v1/branches/{branch_id}/memberships/`

Filial a'zoliklari ro'yxati.

### Query Parameters

- `role`: Filtrlash roli bo'yicha (`teacher`, `student`, `branch_admin`, `super_admin`, `parent`, `other`).
- `salary_type`: `monthly`, `hourly`, `per_lesson`.
- `user_id`: Foydalanuvchi UUID bo'yicha filtrlash.
- `is_active`: `true`/`false` — `deleted_at is null` bo'yicha filtrlash.
- `balance`: numeric filter, qo'llab-quvvatlaydi `exact`, `lt`, `lte`, `gt`, `gte`.
- `created_at`, `updated_at`: sana bo'yicha (`date`, `date__lt`, `date__lte`, `date__gt`, `date__gte`).
- `search`: Foydalanuvchi ism/familiya/telefon va a'zolik `title` bo'yicha qidiruv.
- `ordering`: `created_at`, `updated_at`, `role`, `salary_type`, `balance` (prefiks `-` uchun kamayish tartibi).

### Response

Paginatsiyalangan javob:
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "...",
      "user": {"id": "...", "first_name": "Ali", "last_name": "Usta", "phone_number": "+9989..."},
      "branch": "...",
      "role": "teacher",
      "title": "Fizika",
      "salary_type": "monthly",
      "balance": 0,
      "created_at": "2025-11-30T12:00:00Z",
      "updated_at": "2025-11-30T12:00:00Z"
    }
  ]
}
```

## Examples

- Role bo'yicha filtrlash:
```
GET /api/v1/branches/{branch_id}/memberships/?role=teacher
```

- Qidiruv (ism):
```
GET /api/v1/branches/{branch_id}/memberships/?search=Ali
```

- Ordering (balans kamayish tartibida):
```
GET /api/v1/branches/{branch_id}/memberships/?ordering=-balance
```

## Notes

- `is_active=true` — `deleted_at is null` degani; soft-delete qilingan a'zoliklar ro'yxatdan chiqariladi.
- Ko'proq filterlar kerak bo'lsa (masalan, lavozim bo'yicha), `title` ustuni uchun qidiruvdan foydalaning.
