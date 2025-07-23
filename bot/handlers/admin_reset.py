# File: bot/handlers/admin_reset.py
# Letak: bot/handlers/admin_reset.py

from aiogram import Router, types, F
from core.config import ADMIN_IDS
from bot.models import ReferralEarnings, WithdrawRequests, Users  # ✅ Import models

router = Router()

@router.message(F.text.startswith("/resetbonus"))
async def reset_bonus_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses.")

    cmd = msg.text.strip().split()
    if len(cmd) != 2 or cmd[1] != "all":
        return await msg.answer("Gunakan format: /resetbonus all")

    # 1. Hapus semua data ReferralEarnings
    ReferralEarnings.objects.all().delete()

    # 2. Hapus semua data WithdrawRequests
    WithdrawRequests.objects.all().delete()

    # 3. Reset bonus_balance dan withdrawn_bonus ke 0
    Users.objects.all().update(bonus_balance=0.0, total_bonus=0.0)

    await msg.answer("✅ Semua data bonus referral dan withdrawal berhasil di-reset.")
