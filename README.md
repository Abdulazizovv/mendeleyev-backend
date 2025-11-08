<div align="center">

# Mendeleyev Backend

Ta'lim platformasi uchun filiallar (branch), foydalanuvchilar va rollarni (RBAC) boshqarishga mo'ljallangan Django + DRF backend.

</div>

## Umumiy ma'lumot
Mendeleyev bir nechta filiallarni boshqaradi. Foydalanuvchilar filial(lar)ga rollar (teacher, branch_admin, student, parent, super_admin) bilan biriktiriladi. Autentifikatsiya telefon raqami orqali OTP tasdiqlash va parol bilan amalga oshiriladi. Oddiy foydalanuvchilar tokenlari tanlangan filialga scope qilinadi (JWT claims: `br`, `br_role`), admin/superadmin esa global token oladi yoki ixtiyoriy ravishda filialga scope qilishi mumkin.

### Asosiy imkoniyatlar
- Telefon raqami + OTP verifikatsiya, parol o'rnatish va login holatlari (NOT_VERIFIED, NEEDS_PASSWORD, READY, MULTI_BRANCH, NO_BRANCH)
- Branch-scoped JWT (SimpleJWT) — `br`, `br_role` claims
- RBAC: `BranchRole` (super_admin, branch_admin, teacher, student, parent)
- Celery + Redis: OTP yuborish, ma'murlarga xabar berish, background vazifalar
- Aiogram v3: Telegram bot (webhook)
- DRF + drf-spectacular: OpenAPI schema va Swagger UI
- Structured logging, ixtiyoriy Telegram error alertlar

### Stack
- Python 3.11+, Django 5.x, DRF
- PostgreSQL, Redis, Celery
- SimpleJWT, Aiogram v3
- Nginx (reverse proxy), Docker Compose

## Tez boshlash (Docker)
Quyidagi buyruqlar bilan loyihani ishga tushiring:

```bash
cp .env.example .env          # Muhit sozlamalarini to'ldiring
make build                    # Image larni build qilish
make up                       # Servislarni ko'tarish (django, db, redis, nginx, celery...)
make migrate                  # Django migratsiyalar
make createsuperuser          # Superuser yaratish
# Ixtiyoriy: Telegram webhook
make setwebhook

# Testlar (auth + branch + bot webhook)
make test
```

Swagger/Redoc:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## Muhit o'zgaruvchilari (asosiylari)
| O'zgaruvchi | Tavsif |
|---|---|
| DJANGO_SECRET_KEY | Majburiy. Django uchun yashirin kalit |
| DEBUG | `true/false` |
| DATABASE_URL yoki POSTGRES_* | PostgreSQL ulanishi (yoki `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`) |
| REDIS_* | Redis (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`) |
| BOT_TOKEN | Telegram bot token |
| TELEGRAM_WEBHOOK_DOMAIN | Webhook public domeni |
| TELEGRAM_WEBHOOK_SECRET | Webhook request sirlari (header) |
| ALLOWED_HOSTS | Ruxsat etilgan xostlar (vergul bilan) |
| ERROR_ALERTS_ENABLED | Prod xatoliklarini Telegramga yuborish `true/false` |

Qo'shimcha sozlamalar: `LOG_FORMAT`, SimpleJWT lifetime'lari, OTP (`OTP_CODE_TTL_SECONDS`, `OTP_REQUEST_COOLDOWN_SECONDS`, ...) — batafsil `docs/` ga qarang.

## API va hujjatlar
- Markaziy hujjatlar: `docs/index.md`
- Auth va branch flow: `docs/architecture/auth-flow.md`
- API Overview: `docs/api/overview.md`, Auth: `docs/api/auth.md`, Branch: `docs/api/branch.md`
- Testing: `docs/testing.md`

## Testlar
`make test` quyidagi test paketlarini ishga tushiradi: `auth.users.tests`, `apps.botapp.tests`.
Modul/klass/donani alohida ishlatish:

```bash
docker compose exec django python manage.py test auth.users.tests.test_auth_flow -v 2
docker compose exec django python manage.py test auth.users.tests.test_branch_jwt -v 2
docker compose exec django python manage.py test apps.botapp.tests -v 2
```

## Minimal arxitektura
- Django monolit: `auth/` (users, profiles), `apps/` (branch, botapp, common)
- JWT (SimpleJWT) — branch-scope, refreshda scope validatsiyasi
- Celery + Redis — OTP va alertlar
- Telegram webhook — Aiogram v3

## Litsenziya va aloqa
Hozircha ichki loyiha (private). Keyinchalik OSS litsenziyasi qo'shilishi mumkin.

Savollar/takliflar uchun loyiha adminiga murojaat qiling.