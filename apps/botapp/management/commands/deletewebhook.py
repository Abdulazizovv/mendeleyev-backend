from django.core.management.base import BaseCommand
import asyncio
from bot.bot import bot


class Command(BaseCommand):
    help = "Delete Telegram webhook"

    def handle(self, *args, **options):
        async def _del():
            try:
                await bot.delete_webhook(drop_pending_updates=False)
            finally:
                await bot.session.close()
        asyncio.run(_del())
        self.stdout.write(self.style.SUCCESS("Webhook deleted."))
