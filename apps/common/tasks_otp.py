from __future__ import annotations

import logging
import os
from celery import shared_task
import httpx
from asgiref.sync import async_to_sync

try:
    from aiogram import Bot
    from bot.data.config import BOT_TOKEN, ADMINS
except Exception:  # pragma: no cover - aiogram might not be installed in some envs
    Bot = None
    BOT_TOKEN = None
    ADMINS = []

logger = logging.getLogger("apps.auth")
OTP_PURPOSE_LABELS = {
    "register": "Ro'yxatdan o'tish",
    "reset": "Parolni tiklash",
    "verify": "Telefonni tasdiqlash",
    "generic": "Tasdiqlash",
}


@shared_task(bind=True, autoretry_for=(httpx.HTTPError,), retry_backoff=2, retry_kwargs={"max_retries": 3})
def send_sms_otp_task(self, phone: str, code: str, purpose: str = "generic") -> dict:
    """
    Send OTP via Telegram (primary) and optionally SMS provider.

    The default implementation logs the event. If SMS_PROVIDER_URL and SMS_API_KEY are set,
    it will perform a POST request to that URL.
    """
    logger.info("OTP code issued", extra={"phone": phone, "code": code, "purpose": purpose})

    telegram_status = _send_telegram_otp_to_user(phone, code, purpose=purpose)
    if telegram_status.get("status") == "telegram":
        return telegram_status

    provider_url = os.getenv("SMS_PROVIDER_URL")
    api_key = os.getenv("SMS_API_KEY")

    payload = {"to": phone, "message": f"🔐 Tasdiqlash kodi: <code>{code}</code>"}
    
    # Fallback: just log
    logger.info("OTP send (log-only)", extra={"phone": phone, "code": code, "purpose": purpose})

    if provider_url and api_key:
        timeout = float(os.getenv("SMS_PROVIDER_TIMEOUT", "5"))
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(provider_url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info("OTP sent via provider", extra={"phone": phone, "purpose": purpose})
            return {"status": "sent", "provider": provider_url}


    # Optional: send via Telegram bot to all admins (for dev/testing) if TELEGRAM_OTP_NOTIFY is enabled
    if os.getenv("TELEGRAM_OTP_NOTIFY", "false").lower() == "true" and Bot and BOT_TOKEN and ADMINS:
        try:
            send_telegram_otp_task.delay(phone, code, purpose)
        except Exception:
            logger.exception("Failed to enqueue telegram OTP notify task")

    return {"status": "logged"}


@shared_task(bind=True)
def send_telegram_otp_task(self, phone: str, code: str, purpose: str = "generic") -> dict:
    """Send OTP code to admins via Telegram bot for debugging/verification purposes.

    Controlled by TELEGRAM_OTP_NOTIFY env variable. Not for production end-users.
    """
    if not (Bot and BOT_TOKEN and ADMINS):
        logger.info("Telegram OTP notify skipped: missing bot config")
        return {"status": "skipped"}
    try:
        purpose_label = OTP_PURPOSE_LABELS.get(purpose, "Tasdiqlash")
        text = f"🧪 OTP (test)\n📞 Telefon: {phone}\n🔐 Kod: {code}\n🧾 Sabab: {purpose_label}"
        async def _send_all():
            bot = Bot(token=BOT_TOKEN)
            try:
                for admin_id in ADMINS:
                    try:
                        await bot.send_message(int(admin_id), text)
                    except Exception:
                        logger.exception("Failed sending OTP to admin", extra={"admin": admin_id})
            finally:
                await bot.session.close()

        async_to_sync(_send_all)()
        logger.info("OTP sent to admins via Telegram", extra={"phone": phone})
        return {"status": "telegram"}
    except Exception:
        logger.exception("Telegram OTP notify failure")
        return {"status": "error"}


def _send_telegram_otp_to_user(phone: str, code: str, *, purpose: str = "generic") -> dict:
    try:
        from apps.botapp.models import BotUser, BotUserStatuses
        from apps.botapp.services import send_message_safe
    except Exception:
        logger.info("Telegram OTP skipped: missing bot app")
        return {"status": "skipped"}

    try:
        token = os.getenv("BOT_TOKEN")
        if not token:
            logger.info("Telegram OTP skipped: BOT_TOKEN missing")
            return {"status": "missing_token"}
        bot_user = BotUser.objects.select_related("user").filter(user__phone_number=phone).first()
        if not bot_user:
            return {"status": "no_bot_user"}
        if bot_user.status in (
            BotUserStatuses.BLOCKED_BY_USER,
            BotUserStatuses.DEACTIVATED,
            BotUserStatuses.BANNED_BY_ADMIN,
        ):
            return {"status": "blocked"}

        purpose_label = OTP_PURPOSE_LABELS.get(purpose, "Tasdiqlash")
        text = f"🔐 Tasdiqlash kodi: {code}\n🧾 Sabab: {purpose_label}"

        async def _send() -> bool:
            from aiogram import Bot

            bot = Bot(token=token)
            try:
                return await send_message_safe(bot, bot_user.telegram_id, text)
            finally:
                await bot.session.close()

        delivered = async_to_sync(_send)()
        if delivered:
            logger.info("OTP sent via Telegram to user", extra={"phone": phone, "telegram_id": bot_user.telegram_id, "purpose": purpose})
            return {"status": "telegram"}
        return {"status": "blocked"}
    except Exception:
        logger.exception("Telegram OTP user send failed")
        return {"status": "error"}
