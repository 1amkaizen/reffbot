# 📍 bot/middlewares/bot_status.py

import logging
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from core.config import ADMIN_IDS
from bot.handlers.admin_botstatus import is_bot_active

logger = logging.getLogger(__name__)

class BotStatusMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        logger.warning(f"[Middleware] Incoming message: {event.text} from {event.from_user.id}")

        if event.from_user.id in ADMIN_IDS:
            logger.warning("[Middleware] Admin detected, bypassing bot status.")
            return await handler(event, data)

        if not is_bot_active():
            logger.warning("[Middleware] Bot is OFF. Blocking user command.")
            return await event.answer("⛔ Bot sedang maintenance. Coba lagi nanti.")

        logger.warning("[Middleware] Bot is ON. Passing to handler.")
        return await handler(event, data)
