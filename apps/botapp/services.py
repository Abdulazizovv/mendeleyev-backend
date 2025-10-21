from __future__ import annotations

from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.botapp.models import BotUser, BotUserStatuses
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


@sync_to_async
def upsert_bot_user_from_aiogram(user) -> BotUser:
    obj, _ = BotUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={
            "is_bot": user.is_bot,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "username": user.username or "",
            "language_code": getattr(user, "language_code", "") or "",
            "started_at": timezone.now(),
            "last_seen_at": timezone.now(),
        },
    )
    # Update basic fields in case they changed (preserve proper types)
    changed = False
    # Boolean field
    new_is_bot = bool(getattr(user, "is_bot", False))
    if obj.is_bot != new_is_bot:
        obj.is_bot = new_is_bot
        changed = True
    # String fields
    str_fields = (
        ("first_name", "first_name"),
        ("last_name", "last_name"),
        ("username", "username"),
        ("language_code", "language_code"),
    )
    for user_attr, model_field in str_fields:
        val = getattr(user, user_attr, None) or ""
        if getattr(obj, model_field) != val:
            setattr(obj, model_field, val)
            changed = True
    # If user sends us a message, consider them active unless admin banned
    if obj.status in (BotUserStatuses.BLOCKED_BY_USER, BotUserStatuses.DEACTIVATED):
        obj.status = BotUserStatuses.ACTIVE
        changed = True

    obj.last_seen_at = timezone.now()
    if changed:
        obj.save(update_fields=["is_bot", "first_name", "last_name", "username", "language_code", "status", "last_seen_at", "updated_at"])
    else:
        obj.save(update_fields=["last_seen_at"])
    return obj


async def send_message_safe(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """Send a message and auto-update user's status on common errors.

    Returns True if delivered, False if user is blocked/deactivated.
    Raises for other errors.
    """
    try:
        await bot.send_message(chat_id, text, **kwargs)
        # Mark as active on successful delivery (unless banned by admin)
        await _mark_active_if_not_banned(chat_id)
        return True
    except TelegramForbiddenError as e:
        # Bot is blocked by the user
        await _set_status(chat_id, BotUserStatuses.BLOCKED_BY_USER)
        return False
    except TelegramBadRequest as e:
        msg = str(e).lower()
        if "deactivated" in msg or "chat not found" in msg:
            await _set_status(chat_id, BotUserStatuses.DEACTIVATED)
            return False
        raise


@sync_to_async
def _set_status(chat_id: int, status: str) -> None:
    try:
        obj = BotUser.objects.get(telegram_id=chat_id)
        # Don't override admin ban
        if obj.status != BotUserStatuses.BANNED_BY_ADMIN:
            obj.status = status
            obj.save(update_fields=["status", "updated_at"])
    except BotUser.DoesNotExist:
        return None


@sync_to_async
def _mark_active_if_not_banned(chat_id: int) -> None:
    try:
        obj = BotUser.objects.get(telegram_id=chat_id)
        if obj.status != BotUserStatuses.BANNED_BY_ADMIN and obj.status != BotUserStatuses.ACTIVE:
            obj.status = BotUserStatuses.ACTIVE
            obj.save(update_fields=["status", "updated_at"])
    except BotUser.DoesNotExist:
        return None


@sync_to_async
def set_user_status(telegram_id: int, status: str) -> None:
    try:
        obj = BotUser.objects.get(telegram_id=telegram_id)
        # do not override admin ban unless setting ban explicitly
        if obj.status == BotUserStatuses.BANNED_BY_ADMIN and status != BotUserStatuses.BANNED_BY_ADMIN:
            return None
        obj.status = status
        obj.save(update_fields=["status", "updated_at"])
    except BotUser.DoesNotExist:
        # Ignore silently if user not exists yet
        return None
