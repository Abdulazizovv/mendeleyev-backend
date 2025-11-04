# Telegram Bot va Webhook

Loyiha aiogram v3 bilan integratsiya qilingan va Django ichida webhook endpoint mavjud.

- Webhook: `apps/botapp/views.py` — `/api/telegram/webhook/<token>/`
- Tokenlar: `.env` — `BOT_TOKEN`, `TELEGRAM_WEBHOOK_DOMAIN`, `TELEGRAM_WEBHOOK_PATH`, `TELEGRAM_WEBHOOK_SECRET`
- Dispatcher: `bot/dispatcher.py`, routerlar: `bot/routers/`

## Ishga tushirish

```bash
make setwebhook
```

- Ngrok yoki haqiqiy domain orqali `TELEGRAM_WEBHOOK_DOMAIN` ni to'ldiring.
- `deletewebhook` va `webhookinfo` targetlari mavjud.

## Handler qo'shish

- `bot/routers` ichiga yangi modul qo'shing va `bot/routers/__init__.py` da ro'yxatdan o'tkazing.
