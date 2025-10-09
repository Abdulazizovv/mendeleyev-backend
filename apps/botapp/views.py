from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from environs import Env
import json

from aiogram.types import Update
from bot.dispatcher import dp
from bot.bot import bot

env = Env(); env.read_env()
WEBHOOK_SECRET = env.str("TELEGRAM_WEBHOOK_SECRET", default="")


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint for monitoring"""
    try:
        # You can add more sophisticated health checks here
        # like database connectivity, external services, etc.
        
        return JsonResponse({
            "status": "healthy",
            "service": "django-bot-app",
            "timestamp": request.META.get('HTTP_DATE')
        })
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)


@require_http_methods(["GET"])
def bot_status(request):
    """Check if bot is running and accessible"""
    try:
        # Basic bot info
        bot_info = {
            "status": "running",
            "bot_id": bot.id if hasattr(bot, 'id') else None,
            "username": getattr(bot, 'username', None)
        }
        
        return JsonResponse(bot_info)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
async def telegram_webhook(request, token: str):
    """Telegram webhook endpoint. Token segment must match bot token.
    Validates secret header then forwards update to aiogram dispatcher.
    """
    if token != bot.token:
        return HttpResponseForbidden("Invalid token")

    # Verify Telegram secret header
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if WEBHOOK_SECRET and secret_header != WEBHOOK_SECRET:
        return HttpResponseForbidden("Invalid secret token")

    try:
        raw_body = request.body.decode("utf-8")
        update = Update.model_validate_json(raw_body)
    except Exception as e:
        return JsonResponse({"status": "bad_request", "error": str(e)}, status=400)

    try:
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)
    return JsonResponse({"status": "ok"})
