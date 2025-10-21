import logging
from aiogram import Router
from aiogram.types.error_event import ErrorEvent


error_router = Router(name="error-router")


@error_router.errors()
async def errors_handler(event: ErrorEvent):
    exc = event.exception
    update = event.update
    logging.exception("Aiogram error: %s\nUpdate: %s", exc, update)
    # Returning True prevents further propagation
    return True

