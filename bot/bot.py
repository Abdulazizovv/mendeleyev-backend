from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")

# Create bot instance (Aiogram v3)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
