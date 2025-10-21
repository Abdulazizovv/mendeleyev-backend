from __future__ import annotations

import time
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    """Very simple in-memory throttling per user for messages.

    Note: For production, prefer Redis-based throttling.
    """

    def __init__(self, rate_limit: float = 1.0):
        super().__init__()
        self.rate_limit = rate_limit
        self._last_time: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else 0
        now = time.monotonic()
        last = self._last_time.get(user_id, 0.0)
        if now - last < self.rate_limit:
            # Skip handling silently (or send a warning)
            return
        self._last_time[user_id] = now
        return await handler(event, data)
