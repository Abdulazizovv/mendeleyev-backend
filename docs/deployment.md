# Deployment

Minimal yo'l-yo'riq (Docker asosida):

1) `.env` ni prod qiymatlar bilan to'ldiring: `DEBUG=false`, `ALLOWED_HOSTS`, kuchli `DJANGO_SECRET_KEY`, PostgreSQL manzili.
2) Database migratsiya: `python manage.py migrate` (konteyner ichida).
3) Statik fayllar: `python manage.py collectstatic --noinput`.
4) Nginx + HTTPS (Let's Encrypt) bilan serverni sozlang.

## Platformalar

- Docker Swarm/Kubernetes (kelajakda)
- Heroku/Render/AWS ECS (DATABASE_URL bilan)

## Sog'liq tekshiruvlar

- `/admin/login/` ochilishi
- Webhook `webhookinfo` OK
- `/api/` 200
