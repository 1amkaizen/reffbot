# File: bot/bot.py

from aiogram import Bot, Dispatcher
from core.config import BOT_TOKEN
  # ⬅️ import file


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Daftarkan semua router yang kita pakai
from .handlers import start, referrals, bonus, withdraw, link,stats,channel,admin_withdraw,admin_rate,admin_bonus,admin_reset,withdraw_cash
dp.include_router(withdraw_cash.router)
dp.include_router(link.router)
dp.include_router(withdraw.router)
dp.include_router(start.router)
dp.include_router(referrals.router)
dp.include_router(bonus.router)
dp.include_router(stats.router)
dp.include_router(channel.router)
dp.include_router(admin_withdraw.router)
dp.include_router(admin_rate.router)
dp.include_router(admin_bonus.router)
dp.include_router(admin_reset.router)


# ⬇️ Hanya dipakai jika jalankan polling, bukan webhook
async def run_bot():
    await dp.start_polling(bot)
