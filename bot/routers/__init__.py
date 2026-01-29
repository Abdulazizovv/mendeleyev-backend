from aiogram import Dispatcher, Router, F
import logging
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ChatMemberUpdated, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ChatMemberStatus
from asgiref.sync import sync_to_async
from auth.users.models import User
from apps.common.otp import OTPService
from apps.botapp.services import upsert_bot_user_from_aiogram, set_user_status
from apps.botapp.models import BotUserStatuses
from bot.handlers.errors.error_handler import error_router

user_router = Router(name="user-router")
OTP_PURPOSES = ("register", "reset", "verify", "generic")
OTP_PURPOSE_LABELS = {
    "register": "Ro'yxatdan o'tish",
    "reset": "Parolni tiklash",
    "verify": "Telefonni tasdiqlash",
    "generic": "Tasdiqlash",
}


def _contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _normalize_phone(phone: str) -> str:
    return str(phone).strip().replace(" ", "")


@sync_to_async
def _get_or_create_user_by_phone(phone: str) -> User:
    user = User.objects.filter(phone_number=phone).first()
    if user:
        return user
    alt_phone = None
    if phone.startswith("+"):
        alt_phone = phone.lstrip("+")
    else:
        alt_phone = f"+{phone}"
    if alt_phone:
        user = User.objects.filter(phone_number=alt_phone).first()
        if user:
            return user
    user = User.objects.create_user(phone)
    return user


@sync_to_async
def _link_bot_user_to_user(telegram_id: int, user: User) -> None:
    from apps.botapp.models import BotUser
    BotUser.objects.filter(telegram_id=telegram_id).update(user=user)


@user_router.message(CommandStart())
async def cmd_start(message: Message):
    # Register or update user on /start
    user = await upsert_bot_user_from_aiogram(message.from_user)
    if user.status == BotUserStatuses.BANNED_BY_ADMIN:
        await message.answer("🚫 Kirish cheklangan. Iltimos, admin bilan bog'laning.")
        return
    if not user.user_id:
        await message.answer(
            "👋 Assalomu alaykum!\nRo'yxatdan o'tish uchun telefon raqamingizni pastdagi Contact tugmasi orqali yuboring.",
            reply_markup=_contact_keyboard(),
        )
        return
    await message.answer("✅ Xush kelibsiz! Tasdiqlash kodlari aynan shu chatga yuboriladi.")


@user_router.message(Command("help"))
async def cmd_help(message: Message):
    text = [
        "ℹ️ Buyruqlar:",
        "/start — Botni qayta ishga tushurish",
        "/help — Yordam",
    ]
    await message.answer("\n".join(text))


@user_router.message(F.text)
async def echo(message: Message):
    # Update last_seen for any message
    user = await upsert_bot_user_from_aiogram(message.from_user)
    if user.status == BotUserStatuses.BANNED_BY_ADMIN:
        return
    if not user.user_id:
        await message.answer(
            "📲 Iltimos, telefon raqamingizni faqat pastdagi tugma orqali yuboring.",
            reply_markup=_contact_keyboard(),
        )
        return
    await message.answer("✅ Xabaringiz qabul qilindi. OTP so'rasangiz, kod shu yerga keladi.")


@user_router.message(F.contact)
async def on_contact(message: Message):
    user = await upsert_bot_user_from_aiogram(message.from_user)
    if user.status == BotUserStatuses.BANNED_BY_ADMIN:
        return
    if message.chat.type != "private":
        return
    if not message.contact or not message.contact.user_id or message.contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Iltimos, faqat pastdagi tugma orqali o'zingizning telefon raqamingizni yuboring.",
            reply_markup=_contact_keyboard(),
        )
        return

    phone = _normalize_phone(message.contact.phone_number)
    user_obj = await _get_or_create_user_by_phone(phone)
    await _link_bot_user_to_user(message.from_user.id, user_obj)

    await message.answer(
        "🎉 Rahmat! Ro'yxatdan o'tish yakunlandi. Tasdiqlash kodlari shu chatga yuboriladi.",
        reply_markup=ReplyKeyboardRemove(),
    )

    # If an OTP was requested earlier and still valid, send it now.
    for purpose in OTP_PURPOSES:
        code, ttl = await sync_to_async(OTPService.peek_code)(phone, purpose=purpose)
        if code and ttl > 0:
            purpose_label = OTP_PURPOSE_LABELS.get(purpose, "Tasdiqlash")
            await message.answer(
                f"🔐 Tasdiqlash kodi: <code>{code}</code>\n🧾 Sabab: {purpose_label}\n⏳ Amal qilish muddati: {ttl} soniya"
            )


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
