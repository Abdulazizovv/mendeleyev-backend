# Branch API

Filiallar ikki turda: `school` yoki `learning_center`. Har bir branch umumiy tizimga bog'langan, lekin user-rol munosabatlari per-branch saqlanadi.

## Model (qisqacha)

- `id`, `name`, `type` (school|learning_center), `slug`, `location` (city/address), timestamps, soft-delete.

## Endpointlar (rejalashtirilgan)

- GET `/api/v1/branches/` — ro'yxat (RBAC: super_admin ko'radi hammasini, branch_admin faqat o'zini)
- POST `/api/v1/branches/` — yaratish (RBAC: super_admin)
- GET `/api/v1/branches/{id}/` — detallar (RBAC: branch_admin o'zi, super_admin hammasi)
- PATCH `/api/v1/branches/{id}/` — tahrirlash (RBAC: branch_admin o'zi, super_admin)
- DELETE `/api/v1/branches/{id}/` — soft-delete (RBAC)

## Ruxsatlar

- `IsSuperAdmin`, `IsBranchAdmin`, `HasBranchAccess` (read-only)
- Query param `active_branch` orqali kontekst o'rnatish (ixtiyoriy)
