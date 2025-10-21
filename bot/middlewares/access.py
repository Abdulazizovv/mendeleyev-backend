from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async

from apps.botapp.models import BotUser, BotUserStatuses


@sync_to_async
def _get_user_status(telegram_id: int) -> str | None:
    try:
        return BotUser.objects.only("status").get(telegram_id=telegram_id).status
    except BotUser.DoesNotExist:
        return None


class AccessControlMiddleware(BaseMiddleware):
    """Blocks banned users across all message/callback handlers and sends a warning."""

    warning_text = "Kirish taqiqlangan. Admin bilan bog'laning."

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        status = await _get_user_status(user.id)
        if status == BotUserStatuses.BANNED_BY_ADMIN:
            # Send warning and stop propagation
            if isinstance(event, Message):
                await event.answer(self.warning_text)
            elif isinstance(event, CallbackQuery):
                await event.answer(self.warning_text, show_alert=True)
            return None

        return await handler(event, data)
