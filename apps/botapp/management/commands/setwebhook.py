from django.core.management.base import BaseCommand
from environs import Env
import asyncio
from bot.bot import bot


class Command(BaseCommand):
    help = "Set Telegram webhook"

    def add_arguments(self, parser):
        parser.add_argument("--drop-pending", action="store_true", help="Drop pending updates on Telegram side")

    def handle(self, *args, **options):
        env = Env(); env.read_env()
        domain = env.str("TELEGRAM_WEBHOOK_DOMAIN")
        path = env.str("TELEGRAM_WEBHOOK_PATH", "/api/telegram/webhook")
        secret = env.str("TELEGRAM_WEBHOOK_SECRET")
        url = domain.rstrip("/") + path.rstrip("/") + f"/{bot.token}/"  # Final webhook url includes token

        self.stdout.write(f"Setting webhook to: {url}")

        async def _set():
            try:
                await bot.set_webhook(url=url, secret_token=secret, drop_pending_updates=options["drop_pending"])
                await bot.delete_my_commands()  # reset before re-setting
                from bot.utils.set_bot_commands import set_default_commands
                await set_default_commands(bot)
            finally:
                await bot.session.close()
        asyncio.run(_set())
        self.stdout.write(self.style.SUCCESS("Webhook set successfully."))
