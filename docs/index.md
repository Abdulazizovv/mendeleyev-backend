# Mendeleyev — Ta'lim boshqaruv platformasi

Ushbu hujjatlar Mendeleyev backend loyihasining arxitekturasi, ishga tushirish jarayoni, API dizayni, xavfsizlik siyosati va rivojlanish yo'l xaritasini qamrab oladi. Backend Django + DRF + PostgreSQL asosida, autentifikatsiya telefon raqami va OTP orqali, JWT (SimpleJWT) bilan.

- Loyihaning maqsadi: filiallar (School/Learning Center), o'qituvchilar, talabalar va adminlarni RBAC asosida boshqarish.
- MVP fokus: Branch app, OTP autentifikatsiya, JWT, minimal RBAC, Swagger (drf-spectacular), Telegram bot webhook.

## Tez start

- Docker bilan ishlatish: `README.md` dagi Quickstart bo'limiga qarang.
- Muhit: `.env.example` ni `.env` ga ko'chiring va qiymatlarni to'ldiring.

## Navigatsiya

- Arxitektura: [architecture.md](architecture.md)
- Backend setup (dev): [backend-setup.md](backend-setup.md)
- API (v1): [api/index.md](api/index.md)
  - Auth/OTP/JWT: [api/auth.md](api/auth.md)
  - Filiallar (Branch): [api/branch.md](api/branch.md)
- RBAC va ruxsatlar: [permissions-rbac.md](permissions-rbac.md)
- Ma'lumotlar bazasi: [database.md](database.md)
- Xavfsizlik: [security.md](security.md)
- Telegram bot webhook: [bot.md](bot.md)
- Celery (async jobs): [celery.md](celery.md)
- Deployment: [deployment.md](deployment.md)
- Testlar: [testing.md](testing.md)
- Hissa qo'shish: [contributing.md](contributing.md)
- Makefile qo'llanma: [makefile.md](makefile.md)
- Roadmap: [roadmap.md](roadmap.md)
