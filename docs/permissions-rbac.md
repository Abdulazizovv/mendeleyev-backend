# RBAC va ruxsatlar

Maqsad: per-branch RBAC. User bir nechta filialga ulangan bo'lishi mumkin, har filialda roli alohida (super_admin — global).

## Rollar

- `super_admin` — butun tarmoq
- `branch_admin` — o'z filiallari
- `teacher` — darslar, davomat, baholar
- `student` — o'z natijalari, jadvali, to'lovlari

## Implementatsiya (reja)

- `User` — custom, phone_number USERNAME_FIELD
- `Branch` — type/slug/location
- `UserBranch` (through) — `user`, `branch`, `role`, `is_active`, timestamps
- DRF permissions: `IsSuperAdmin`, `IsBranchAdmin`, `HasBranchRole`
- Context: `active_branch` query/header orqali aniqlash

## Misollar

- Branch yaratish: faqat `super_admin`
- Branch profiling tahriri: `branch_admin` o'zida
- Talabalar ro'yxati: o'qituvchi — faqat o'zi dars beradigan guruhlar (kelajakdagi LMS modulida)
