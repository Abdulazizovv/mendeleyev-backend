from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .routers import register_routers
from .middlewares.throttling import ThrottlingMiddleware
from .middlewares.access import AccessControlMiddleware


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    # Access control first to block banned users early
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    register_routers(dp)
    return dp


# A global dispatcher instance (can be imported where needed)
dp = create_dispatcher()
