# API Overview

Versioning: `v1` prefix (`/api/v1/...`). Future versions can coexist (`/api/v2/`) while keeping legacy stable.

Base URLs:
- Auth: `/api/v1/auth/`
- Profiles: `/api/v1/profile/`
- Bot webhook: `/api/telegram/webhook/<token>/`
- Schema: `/api/schema/` (OpenAPI JSON)
- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`

## Conventions
- JSON only (no browsable API in production).
- Timestamps: ISO8601 with timezone when applicable.
- Errors: `{ "detail": "message" }` minimal payload.
- State-based responses (login gating) use `{ "state": "NOT_VERIFIED" }` pattern with 200 status for UX-friendly flows.

## Auth States Returned
`NOT_FOUND`, `NOT_VERIFIED`, `NEEDS_PASSWORD`, `READY`, `NO_BRANCH`, `MULTI_BRANCH`.

## Pagination
Currently simple list endpoints (e.g., branches/mine) return `{ results: [...], count: N }`. For large datasets, plan to introduce DRF pagination style: `{ count, next, previous, results }`.

## Rate Limiting (Planned)
- OTP request endpoints: per phone cooldown (already implemented via Redis). Formal DRF Throttling layer can be added.
- Login attempts: future IP + phone composite throttle.

## Authentication
- JWT (SimpleJWT). Access/Refresh tokens; branch scope stored in claims.
- Authorization header: `Authorization: Bearer <access>`.

## Branch Scope
If token claims include:
```json
{
  "br": "<branch-id>",
  "br_role": "teacher"
}
```
Backend permissions use these claims directly. Admin/staff may have global token (no `br`).

## Error Codes Summary
| HTTP | Context | Notes |
|------|---------|-------|
| 200 | Stateful auth responses | With `state` field |
| 400 | Validation / wrong credentials | Also invalid branch selection |
| 401 | Invalid/expired refresh, revoked membership, inactive branch (refresh) | Hard auth failure |
| 403 | Switching to branch without membership | |
| 404 | User not found (verification endpoints) | Avoid enumeration except where safe |
| 429 | OTP cooldown / spam prevention | Redis-based cooldown |

## Typical Flow Examples
### Phone Check
Request:
```http
POST /api/v1/auth/phone/check
{ "phone_number": "+998901234567" }
```
Response:
```json
{ "state": "NOT_FOUND" }
```

### Multi-Branch Login
```http
POST /api/v1/auth/login
{ "phone_number": "+99890...", "password": "Secret!" }
```
Response:
```json
{
  "state": "MULTI_BRANCH",
  "branches": [ {"id": "...", "name": "Alpha", "role": "teacher"}, ... ]
}
```
Select branch:
```http
POST /api/v1/auth/login
{ "phone_number": "+99890...", "password": "Secret!", "branch_id": "<uuid>" }
```

### Switch Branch
```http
POST /api/v1/auth/branch/switch
{ "refresh": "<refresh-token>", "branch_id": "<uuid>" }
```
Response:
```json
{ "access": "...", "refresh": "...", "br": "<uuid>" }
```

## Version Evolution Strategy
- `v1`: core auth, branch scope, profiles.
- `v1.x`: additive fields non-breaking.
- `v2`: major model changes (e.g., consolidated roles, new academic entities) → maintain `v1` until clients migrate.

## Stability & Deprecation
Each endpoint will carry a stability tag in future docs (`stable`, `beta`, `deprecated`). Currently all listed endpoints are considered `stable` except future academic modules.

---
Next: [Auth details](./auth.md)
