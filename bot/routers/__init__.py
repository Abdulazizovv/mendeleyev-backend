from aiogram import Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

user_router = Router(name="user-router")


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f"Hello, {message.from_user.full_name}!\nWelcome to the bot (webhook edition).")


@user_router.message(Command("help"))
async def cmd_help(message: Message):
    text = [
        "Commands:",
        "/start - Start the bot",
        "/help - This help message",
    ]
    await message.answer("\n".join(text))


@user_router.message(F.text)
async def echo(message: Message):
    await message.answer(message.text)


def register_routers(dp: Dispatcher):
    dp.include_router(user_router)
