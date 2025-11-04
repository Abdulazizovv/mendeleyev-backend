# Auth — OTP va JWT

Telefon raqami asosiy identifikator. OTP orqali tasdiqlashdan so'ng JWT beriladi.

## Oqim

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API
  participant R as Redis/Celery

  C->>A: POST /api/v1/auth/request-otp { phone_number }
  A->>R: Generate & store OTP (TTL 3-5 min); enqueue SMS send
  A-->>C: 200 { message }

  C->>A: POST /api/v1/auth/verify-otp { phone_number, otp }
  A->>R: Validate OTP
  A->>A: Create user if not exists
  A-->>C: 200 { access, refresh, user }

  C->>A: GET /api/v1/auth/me (Authorization: Bearer)
  A-->>C: 200 { user, branches_roles }
```

## Endpointlar (rejalashtirilgan)

- POST `/api/v1/auth/request-otp`
  - Body: `{ "phone_number": "+998901234567" }`
  - Javob: `200 OK` `{ "message": "OTP sent" }`

- POST `/api/v1/auth/verify-otp`
  - Body: `{ "phone_number": "+998901234567", "otp": "123456" }`
  - Javob: `200 OK` `{ "access": "...", "refresh": "...", "user": { ... } }`

- POST `/api/v1/auth/refresh`
  - Body: `{ "refresh": "..." }`
  - Javob: `200 OK` `{ "access": "..." }`

- GET `/api/v1/auth/me`
  - Header: `Authorization: Bearer <access>`
  - Javob: `200 OK` `{ "id": 1, "phone_number": "...", "branches": [{"id": ... , "role": "branch_admin"}] }`

## Xavfsizlik

- OTP TTL: 3–5 daqiqa.
- Bir raqam uchun throttling: masalan 3 urinish / 5 daqiqa.
- OTP hash saqlash (plain emas) yoki kamida bekor qilingandan so'ng darhol o'chirish.
- JWT refresh blacklist (ixtiyoriy) yoki qisqa living access tokenlar.
