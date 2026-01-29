from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from bot.loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = ("ℹ️ Buyruqlar: ",
            "/start — Ro'yxatdan o'tish yoki tekshirish",
            "/help — Yordam")
    
    await message.answer("\n".join(text))
