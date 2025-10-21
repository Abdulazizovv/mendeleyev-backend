from aiogram.filters import BaseFilter
from aiogram.types import Message
from bot.data import config


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return str(message.from_user.id) in config.ADMINS
