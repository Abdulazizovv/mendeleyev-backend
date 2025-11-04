# Xavfsizlik siyosati

- Secretlarni `.env` faylda saqlang; hech qachon repoga push qilmang.
- `DEBUG=false` prod muhitda. `ALLOWED_HOSTS` ni to'g'ri belgilang.
- CSRF: DRF API uchun Session-based emas, JWT ishlatiladi. Webhook view uchun CSRF exempt, ammo `X-Telegram-Bot-Api-Secret-Token` tekshiruvi bor.
- OTP: throttling, TTL, validatsiya. SMS providerga ratio-limit qo'llang.
- JWT: qisqa living access (masalan 5–15 min), refresh 7–30 kun. Blacklist ixtiyoriy.
- Database: minimal permissionli user, SSL (hostga qarab), zaxira nusxalar.
- Nginx: HTTPS, `X-Forwarded-Proto` header, fayl o'lcham cheklovi.
- Loglar: PII (telefon) ni maskalash.
