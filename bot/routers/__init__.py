from aiogram import Dispatcher, Router, F
import logging
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from apps.botapp.services import upsert_bot_user_from_aiogram, set_user_status
from apps.botapp.models import BotUserStatuses
from bot.handlers.errors.error_handler import error_router

user_router = Router(name="user-router")


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    # Register or update user on /start
    user = await upsert_bot_user_from_aiogram(message.from_user)
    if user.status == BotUserStatuses.BANNED_BY_ADMIN:
        await message.answer("Kirish taqiqlangan. Admin bilan bog'laning.")
        return
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
    # Update last_seen for any message
    user = await upsert_bot_user_from_aiogram(message.from_user)
    if user.status == BotUserStatuses.BANNED_BY_ADMIN:
        return
    await message.answer(message.text)


def register_routers(dp: Dispatcher):
    dp.include_router(error_router)
    dp.include_router(user_router)
    dp.include_router(membership_router)


# Detect block/unblock via my_chat_member updates (no message needed)
membership_router = Router(name="membership-router")


@membership_router.my_chat_member()
async def on_my_chat_member(event: ChatMemberUpdated):
    # Only private chats matter for user->bot relations
    if event.chat.type != "private":
        return
    new_status = event.new_chat_member.status
    logging.info("my_chat_member: chat=%s new_status=%s from_user=%s", event.chat.id, new_status, getattr(event, 'from_user', None))
    user_id = event.from_user.id if event.from_user else None
    if not user_id:
        return
    if new_status == ChatMemberStatus.KICKED:
        await set_user_status(user_id, BotUserStatuses.BLOCKED_BY_USER)
    elif new_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        await set_user_status(user_id, BotUserStatuses.ACTIVE)

