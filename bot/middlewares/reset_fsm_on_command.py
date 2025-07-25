# Letak: bot/middlewares/reset_fsm_on_command.py

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from typing import Callable, Dict, Any, Awaitable


class ResetFSMOnCommand(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        state: FSMContext = data["state"]
        if event.text and event.text.startswith("/"):
            await state.clear()  # Reset semua state jika ada command
        return await handler(event, data)
