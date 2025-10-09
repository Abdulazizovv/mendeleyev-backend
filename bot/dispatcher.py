from aiogram import Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from .routers import register_routers


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage(), session=AiohttpSession())
    register_routers(dp)
    return dp


# A global dispatcher instance (can be imported where needed)
dp = create_dispatcher()
