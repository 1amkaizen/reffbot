# 📍 File: bot/bot.py

from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
from bot.middlewares.bot_status import BotStatusMiddleware
from bot.middlewares.reset_fsm_on_command import ResetFSMOnCommand

# Init bot dan dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Import semua handler
from .handlers import (
    invite, start, bonus, team, withdraw, channel,
    admin_withdraw, admin_rate, admin_bonus,
    withdraw_callback, admin_welcome, admin_addbalance,
    admin_resetteam, admin_botstatus
)

# ✅ Middleware: Reset FSM di setiap command
dp.message.middleware(ResetFSMOnCommand())

# ✅ Router USER → pakai BotStatusMiddleware
user_routers = [
    invite.router,
    withdraw.router,
    start.router,
    bonus.router,
    team.router,
    channel.router,
]

for r in user_routers:
    r.message.middleware(BotStatusMiddleware())
    dp.include_router(r)

# ✅ Router ADMIN → tidak dibatasi oleh status bot
admin_routers = [
    admin_welcome.router,
    withdraw_callback.router,
    admin_addbalance.router,
    admin_withdraw.router,
    admin_rate.router,
    admin_bonus.router,
    admin_resetteam.router,
    admin_botstatus.router,
]

for r in admin_routers:
    dp.include_router(r)

# ✅ Run polling
async def run_bot():
    await dp.start_polling(bot)
