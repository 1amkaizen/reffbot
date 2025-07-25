# File: bot/bot.py

from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Import semua handler
from .handlers import (
    invite, start, bonus, team, withdraw, channel,
    admin_withdraw, admin_rate, admin_bonus,
    withdraw_callback, admin_welcome, admin_addbalance,admin_resetteam
)

# ✅ Daftarkan semua router
dp.include_router(admin_welcome.router)
dp.include_router(withdraw_callback.router)
dp.include_router(admin_addbalance.router)  # ⬅️ tambahkan ini
dp.include_router(invite.router)
dp.include_router(withdraw.router)
dp.include_router(start.router)
dp.include_router(bonus.router)
dp.include_router(team.router)
dp.include_router(channel.router)
dp.include_router(admin_withdraw.router)
dp.include_router(admin_rate.router)
dp.include_router(admin_bonus.router)
dp.include_router(admin_resetteam.router)


from bot.middlewares.reset_fsm_on_command import ResetFSMOnCommand

dp.message.middleware(ResetFSMOnCommand())

# ⬇️ Hanya dipakai jika jalankan polling, bukan webhook
async def run_bot():
    await dp.start_polling(bot)
