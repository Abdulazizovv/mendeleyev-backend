# Logging

Professional logging konfiguratsiyasi JSON yoki matn (text) formatida, fayl rotatsiyasi bilan va Docker stdout/stderr oqimlariga yo'naltirilgan.

## Formati

- `LOG_FORMAT=text` (default) — `%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(message)s`
- `LOG_FORMAT=json` — `python-json-logger` orqali strukturalangan loglar
- `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`
 - `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`
 - `ERROR_ALERTS_ENABLED=true|false` — ERROR loglar Telegram adminlarga yuborilsinmi

## Fayllar

- `logs/app.log` — umumiy ilova loglari
- `logs/requests.log` — har bir HTTP so'rov/response uchun natijalar (latency bilan)
- `logs/celery.log` — Celery worker loglari

Rotatsiya: har kuni (midnight), 14 ta backup saqlanadi.

## Middleware

`apps.common.middlewares.request_logging.RequestLoggingMiddleware` — har bir so'rov uchun quyidagilarni log qiladi:

- method, path, status, ms (kechikish), user_id, ip, user-agent

## Docker va Gunicorn

- Gunicorn access/error loglari STDOUT/SERROR_ALERTS_ENABLED=true
TDERR ga chiqariladi (`docker logs` orqali ko'rinadi)
- Konteyner ishga tushganda `/usr/src/app/logs` papkasi yaratiladi

## Konfiguratsiya (`settings.py`)

- `LOGGING` dict — formatters, handlers (console, TimedRotatingFileHandler, telegram_admins), loggers (`django`, `django.request`, `celery`, `apps`)
- `CELERY_WORKER_HIJACK_ROOT_LOGGER=False` — Celery root loggerni egallamaydi

### Telegramga xatolik ogohlantirishlari (Celery orqali)

- Handler: `apps.common.logging_handlers.TelegramAdminHandler` — ERROR+ loglarni Celery task orqali yuboradi
- Task: `apps.common.tasks_alerts.send_telegram_alert_task` — retry (exponential backoff), chunk, multi-admin
- Filter: `ProductionErrorFilter` — faqat ERROR+ va 500+ statuslar; 404/CancelledError/DisallowedHost kabi shovqinlarni cheklaydi
- Manzillar: `.env` dan `BOT_TOKEN` va `ADMINS` o‘qiladi
- Throttle: `.env` `ALERT_THROTTLE_SECONDS` (default 120s), Redis orqali bir xil xabarlarni qisqa muddatda takror yubormaydi
- Eslatma: prod’da albatta `ERROR_ALERTS_ENABLED=true` bo‘lsin

## Muhit o'zgaruvchilari (`.env`)

```env
LOG_LEVEL=INFO
# LOG_FORMAT=json  # ixtiyoriy
```

## Tahlil bo'yicha tavsiya

- Prod muhitda `LOG_FORMAT=json` ni yoqing va observability stack (ELK/EFK) bilan yig'ing
- `django.db.backends` loglarini DEBUG'ga olish ehtiyotkorlik bilan (faqat lokal)
