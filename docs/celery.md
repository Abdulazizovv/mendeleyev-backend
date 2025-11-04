# Celery integratsiyasi

Celery asinxron vazifalar uchun ishlatiladi (masalan, OTP/SMS yuborish, background hisob-kitoblar). Broker va natija backend sifatida Redis ishlatiladi.

## Arxitektura

- Broker: Redis (`redis://redis:6379/0`)
- Worker: `celery -A core worker -l info`
- Beat: `celery -A core beat -l info`
- Django app: `django_celery_results`

## Konfiguratsiya

- `core/celery.py` — Celery app va autodiscovery
- `core/__init__.py` — `celery_app` export
- `settings.py` — `CELERY_*` sozlamalari, INSTALLED_APPS ga `django_celery_results` qo'shilgan
- `.env` — broker/result URL va limitlar

## Docker Compose

- `celery` va `celery-beat` xizmatlari qo'shilgan (default scheduler)
- `make celery`, `make celery-beat`, `make celery-logs` targetlari mavjud

## Task yozish

Har bir Django app ichida `tasks.py` yarating va `@shared_task` bilan funksiya belgilang.

Misol (`apps/common/tasks.py`):

```python
from celery import shared_task

@shared_task
def ping(delay: int = 0) -> str:
    if delay:
        import time; time.sleep(delay)
    return "pong"
```

Ishga tushirish:

```bash
make build
make up
make migrate
make celery
make celery-beat
make celery-logs
```

Keyin Django shell orqali test qilishingiz mumkin:

```python
from apps.common.tasks import ping
ping.delay(1)
```

Eslatma: Django 5.2.x bilan mosligi uchun `django-celery-beat` (DB-based scheduler) ulanmagan. Agar keyinroq mos versiya chiqsa yoki Django versiyasini pasaytirish rejangiz bo'lsa, DB scheduler’ni qo'shish mumkin.
