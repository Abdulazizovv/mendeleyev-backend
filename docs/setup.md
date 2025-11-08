# Setup (Docker & Local)

## Quick Docker Start
```bash
cp .env.example .env
make build
make up
make migrate
make createsuperuser  # create admin for provisioning users
```
Optional:
```bash
make setwebhook  # Telegram bot webhook
```

## Environment Variables (Core)
| Name | Purpose |
|------|---------|
| DJANGO_SECRET_KEY | Signing key (must be long & random) |
| DEBUG | true/false |
| POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, DB_HOST, DB_PORT | Database connectivity |
| REDIS_HOST, REDIS_PORT, REDIS_DB | Celery + OTP store |
| BOT_TOKEN | Telegram bot token |
| TELEGRAM_WEBHOOK_DOMAIN | Public domain for webhook |
| TELEGRAM_WEBHOOK_SECRET | Header secret for verification |
| ERROR_ALERTS_ENABLED | Enable Telegram error handler |
| OTP_CODE_TTL_SECONDS | Code validity window |
| OTP_REQUEST_COOLDOWN_SECONDS | Anti-spam cooldown |
| OTP_MAX_ATTEMPTS | Max verify attempts before invalidation |
| JWT_ACCESS_MINUTES | Access token lifetime |
| JWT_REFRESH_DAYS | Refresh token lifetime |

## Local (SQLite) Dev
Add to `.env`:
```
USE_SQLITE=1
DJANGO_SECRET_KEY=dev-key
DEBUG=true
```
Then:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8001
```

## Celery
Start workers via Docker:
```bash
make celery
make celery-beat
```
Logs:
```bash
make celery-logs
make beat-logs
```

## Static & Media
- Collected to `staticfiles/` (production) via `make collectstatic`.
- Media served via Django in DEBUG; Nginx handles in production.

## Health Checks
- `/health/` simple OK response.
- Future: metrics endpoint (Prometheus) proposal.

## Updating Dependencies
Pinned in `requirements.txt`. After change:
```bash
pip install -r requirements.txt
# or inside container
docker compose exec django pip install -r requirements.txt
```

---
Next: [Testing](./testing.md)
