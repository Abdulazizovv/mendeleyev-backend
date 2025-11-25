# API — v1

- Bazaviy URL: `/api/v1/`
- Autentifikatsiya: Bearer JWT (SimpleJWT)
- Hujjatlar: Swagger/Redoc (drf-spectacular) — `/api/schema/`, `/api/docs/`

## Versiyalash

- Hozirgi: v1
- Yondashuv: path-based (`/api/v1/...`), breaking change bo'lsa v2 ga ko'tariladi.

## Resurslar

### Asosiy
- Auth/OTP/JWT: [auth.md](auth.md)
- Filiallar (Branch): [branch.md](branch.md)
- Profillar: [profile.md](profile.md)

### Maktab Moduli
- Akademik yil va Choraklar: [academic.md](academic.md)
- Sinflar: [classes.md](classes.md)
- Fanlar: [subjects.md](subjects.md)
- Binolar va Xonalar: [rooms.md](rooms.md)
- Dars Jadvali: (kelajakda)
- Davomat: (kelajakda)
- Baholash: (kelajakda)
- Moliya: (kelajakda)

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
