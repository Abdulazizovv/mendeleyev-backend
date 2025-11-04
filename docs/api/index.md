# API — v1

- Bazaviy URL: `/api/v1/`
- Autentifikatsiya: Bearer JWT (SimpleJWT)
- Hujjatlar: Swagger/Redoc (drf-spectacular) — `/api/schema/`, `/api/docs/`

## Versiyalash

- Hozirgi: v1
- Yondashuv: path-based (`/api/v1/...`), breaking change bo'lsa v2 ga ko'tariladi.

## Resurslar

- Auth/OTP/JWT: [auth.md](auth.md)
- Filiallar (Branch): [branch.md](branch.md)
- Foydalanuvchilar/Profillar: (kelajakda)

## Xatolik formati

```json
{
  "detail": "Human-readable error message",
  "code": "error_code_optional"
}
```

## Rate limiting

- Webhooklar uchun alohida throttling.
- Auth/OTP endpointlari uchun qat'iy throttling (brute-force oldini olish) — settings orqali yoqiladi.
