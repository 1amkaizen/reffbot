# Letak: bot/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import sync_and_async_middleware
from aiogram import types
from .bot import bot, dp

# Konfigurasi logger
logger = logging.getLogger("telegram_webhook")
logger.setLevel(logging.DEBUG)  # pastikan level cukup tinggi

# Kalau belum ada handler (misal saat run dari gunicorn), tambahkan
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@csrf_exempt
@sync_and_async_middleware
async def telegram_webhook(request):
    if request.method == "POST":
        try:
            raw = request.body.decode("utf-8")
            logger.info("📥 Webhook received")
            logger.debug(f"RAW JSON: {raw}")  # log full raw body

            data = json.loads(raw)
            update = types.Update(**data)
            await dp.feed_update(bot, update)

            logger.info("✅ Webhook processed successfully")
        except Exception as e:
            logger.exception("❌ Error while processing webhook:")
        return JsonResponse({"ok": True})
    
    logger.warning("⚠️ Webhook accessed with non-POST method")
    return JsonResponse({"detail": "Method not allowed"}, status=405)
