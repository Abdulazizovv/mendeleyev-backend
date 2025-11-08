from __future__ import annotations

import logging
import os
from celery import shared_task
import httpx

from django.conf import settings

try:
    from aiogram import Bot
    from bot.data.config import BOT_TOKEN, ADMINS
except Exception:  # pragma: no cover - aiogram might not be installed in some envs
    Bot = None
    BOT_TOKEN = None
    ADMINS = []

logger = logging.getLogger("apps.auth")


@shared_task(bind=True, autoretry_for=(httpx.HTTPError,), retry_backoff=2, retry_kwargs={"max_retries": 3})
def send_sms_otp_task(self, phone: str, code: str) -> dict:
    """
    Send OTP via an SMS provider.

    The default implementation logs the event. If SMS_PROVIDER_URL and SMS_API_KEY are set,
    it will perform a POST request to that URL.
    """
    provider_url = os.getenv("SMS_PROVIDER_URL")
    api_key = os.getenv("SMS_API_KEY")

    payload = {"to": phone, "message": f"Your verification code: {code}"}

    if provider_url and api_key:
        timeout = float(os.getenv("SMS_PROVIDER_TIMEOUT", "5"))
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(provider_url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("OTP sent via provider", extra={"phone": phone})
            return {"status": "sent", "provider": provider_url}

    # Fallback: just log
    logger.info("OTP send (log-only)", extra={"phone": phone, "code": code})

    # Optional: send via Telegram bot to all admins (for dev/testing) if TELEGRAM_OTP_NOTIFY is enabled
    if os.getenv("TELEGRAM_OTP_NOTIFY", "false").lower() == "true" and Bot and BOT_TOKEN and ADMINS:
        try:
            send_telegram_otp_task.delay(phone, code)
        except Exception:
            logger.exception("Failed to enqueue telegram OTP notify task")

    return {"status": "logged"}


@shared_task(bind=True)
def send_telegram_otp_task(self, phone: str, code: str) -> dict:
    """Send OTP code to admins via Telegram bot for debugging/verification purposes.

    Controlled by TELEGRAM_OTP_NOTIFY env variable. Not for production end-users.
    """
    if not (Bot and BOT_TOKEN and ADMINS):
        logger.info("Telegram OTP notify skipped: missing bot config")
        return {"status": "skipped"}
    try:
        bot = Bot(token=BOT_TOKEN)
        text = f"OTP test\nPhone: {phone}\nCode: {code}"
        for admin_id in ADMINS:
            try:
                # Fire and forget individual messages
                import asyncio
                asyncio.get_event_loop().run_until_complete(bot.send_message(admin_id, text))
            except Exception:
                logger.exception("Failed sending OTP to admin", extra={"admin": admin_id})
        logger.info("OTP sent to admins via Telegram", extra={"phone": phone})
        return {"status": "telegram"}
    except Exception:
        logger.exception("Telegram OTP notify failure")
        return {"status": "error"}
