# Backend Setup (Dev)

Ushbu bo'lim lokal rivojlantirish muhiti va Docker Compose orqali ishga tushirishni ko'rsatadi.

## Talablar

- Python 3.10+
- Docker & Docker Compose
- Git

## Muhit fayli

```bash
cp .env.example .env
```

Kerakli o'zgaruvchilarni to'ldiring: `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, Postgres sozlamalari, bot tokeni va webhook domeni.

## Docker bilan ishga tushirish

```bash
make build
make up
make migrate
```

- Django API: http://localhost:8001
- Nginx (agar yoqsangiz): http://localhost:8080
- Postgres: localhost:5433
- Redis: localhost:6379

Webhook o'rnatish (ixtiyoriy, agar bot ishlatsa):

```bash
make setwebhook
```

## Lokal (Docker'siz) ishga tushirish (ixtiyoriy)

- `python -m venv venv && source venv/bin/activate`
- `pip install -r requirements.txt`
- `python manage.py migrate`
- `python manage.py runserver 0.0.0.0:8001`

## Foydali buyruqlar

- `make logs` — loglarni kuzatish
- `make test` — Django testlar
- `make deletewebhook` — webhookni o'chirish
