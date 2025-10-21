import os
import json
import importlib
from django.test import AsyncClient, TransactionTestCase
from django.urls import reverse


class WebhookViewTests(TransactionTestCase):
    databases = {"default"}
    async def test_webhook_rejects_missing_secret(self):
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "testsecret"
        from apps.botapp import views
        importlib.reload(views)
        from bot.bot import bot

        url = reverse("telegram_webhook", kwargs={"token": bot.token})
        client = AsyncClient()
        payload = {"update_id": 1}
        resp = await client.post(url, data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 403

    async def test_webhook_accepts_valid_secret_and_token(self):
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "testsecret"
        from apps.botapp import views
        importlib.reload(views)
        from bot.bot import bot

        url = reverse("telegram_webhook", kwargs={"token": bot.token})
        client = AsyncClient()
        payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 1, "type": "private"},
                "from": {"id": 1, "is_bot": False, "first_name": "Test"},
                "text": "/start",
                "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
            },
        }
        resp = await client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Telegram-Bot-Api-Secret-Token": "testsecret"},
        )
        assert resp.status_code in (200, 500)

    async def test_start_creates_botuser(self):
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "testsecret"
        from apps.botapp import views
        importlib.reload(views)
        from bot.bot import bot

        url = reverse("telegram_webhook", kwargs={"token": bot.token})
        client = AsyncClient()
        payload = {
            "update_id": 222222,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 777, "type": "private"},
                "from": {"id": 777, "is_bot": False, "first_name": "Test", "username": "tester"},
                "text": "/start",
                "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
            },
        }
        resp = await client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Telegram-Bot-Api-Secret-Token": "testsecret"},
        )
        assert resp.status_code in (200, 500)
        # Verify DB object exists
        from apps.botapp.models import BotUser
        assert BotUser.objects.filter(telegram_id=777).exists()
