# Django + Aiogram v3 Webhook Template

A production-ready template combining Django (5.x) and Aiogram v3 using webhooks (no polling). Includes Docker, Nginx, PostgreSQL, Redis, management commands, tests, and CI scaffold.

## Features
- Async Django webhook endpoint: `/api/telegram/webhook/<token>/`
- Telegram secret token header verification
- Aiogram v3 routers structure
- Management commands: `setwebhook`, `deletewebhook`
- Dockerized stack: Django + Postgres + Redis + Nginx
- Example Nginx config and `.env.example`
- Sample test for webhook

## Quickstart

1) Copy environment file

```bash
cp .env.example .env
```

Fill required values:
- BOT_TOKEN
- TELEGRAM_WEBHOOK_DOMAIN (e.g. https://<your-domain> or https://<ngrok-url>)
- TELEGRAM_WEBHOOK_SECRET
- DB credentials
- ALLOWED_HOSTS

2) Run database migrations

```bash
# Local host
python manage.py migrate
```

Or using Docker:

```bash
# Build and start services
docker-compose up -d --build
# Apply migrations inside the django container
docker-compose exec django python manage.py migrate
```

3) Set webhook

```bash
# Ensure TELEGRAM_WEBHOOK_DOMAIN and TELEGRAM_WEBHOOK_SECRET are set in .env
python manage.py setwebhook --drop-pending
# Docker
docker-compose exec django python manage.py setwebhook --drop-pending
```

4) Test webhook via ngrok (local dev)

- Install ngrok and run:

```bash
ngrok http http://localhost:8001
```

- Copy the HTTPS URL (e.g. `https://abcd1234.ngrok.io`).
- Put it into `.env` as TELEGRAM_WEBHOOK_DOMAIN, keep TELEGRAM_WEBHOOK_PATH as default `/api/telegram/webhook`.
- Re-run `setwebhook`.

5) Delete webhook when needed

```bash
python manage.py deletewebhook
```

## Development

- Code entry points:
  - Webhook view: `apps/botapp/views.py: telegram_webhook`
  - Aiogram bot/dispatcher: `bot/bot.py`, `bot/dispatcher.py`, `bot/routers/__init__.py`
- Add new handlers by creating new routers and including them in `bot/routers`.

## Security
- Webhook verifies `X-Telegram-Bot-Api-Secret-Token` header.
- CSRF is disabled only for the webhook view.
- Production security flags enabled when `DEBUG=false`.

## CI
- Add your GitHub Actions workflow under `.github/workflows/ci.yml` (not provided by default in this template but suggested below).

## Suggested Make targets (optional)

```Makefile
run:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

setwebhook:
	python manage.py setwebhook --drop-pending

deletewebhook:
	python manage.py deletewebhook

test:
	python manage.py test
```

## Notes
- Python 3.10+
- Aiogram v3
- Django 5.x

***

Happy building!