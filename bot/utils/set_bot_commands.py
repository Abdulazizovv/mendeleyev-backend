from aiogram import types
from aiogram import Bot


async def set_default_commands(bot: Bot):
    await bot.set_my_commands(
        [
            types.BotCommand(command="start", description="Ro'yxatdan o'tish yoki tekshirish"),
            types.BotCommand(command="help", description="Yordam va ko'rsatmalar"),
        ]
    )
