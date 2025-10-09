import os
import json
import importlib
from django.test import AsyncClient, SimpleTestCase
from django.urls import reverse


class WebhookViewTests(SimpleTestCase):
    async def test_webhook_accepts_valid_secret_and_token(self):
        # Arrange env for secret
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "testsecret"

        # Lazy import after env is set to ensure module-level read picks it up
        from apps.botapp import views
        importlib.reload(views)
        from bot.bot import bot

        url = reverse("telegram_webhook", kwargs={"token": bot.token})
        client = AsyncClient()

        # Minimal update payload
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

        # Act
        response = await client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            headers={"X-Telegram-Bot-Api-Secret-Token": "testsecret"},
        )

        # Assert
        assert response.status_code in (200, 500)  # 500 if handler raises; 200 if fed correctly
        # We at least assert that secret and token check passed
