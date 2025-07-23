# Letak: bot/handlers/stats.py

from aiogram import Router, types
from aiogram.filters import Command
from bot.models import Users, ReferralEarnings
from asgiref.sync import sync_to_async
from core.config import USD_RATE

router = Router()

@router.message(Command("stats"))
async def stats_handler(msg: types.Message):
    user_id = msg.from_user.id

    # ========================
    # Ambil Level 1
    # ========================
    level1_users = await sync_to_async(list)(
        Users.objects.filter(ref_by=user_id).values_list("id", flat=True)
    )

    # ========================
    # Ambil Level 2
    # ========================
    level2_users = []
    for uid in level1_users:
        sub_users = await sync_to_async(list)(
            Users.objects.filter(ref_by=uid).values_list("id", flat=True)
        )
        level2_users.extend(sub_users)

    # ========================
    # Ambil Level 3
    # ========================
    level3_users = []
    for uid in level2_users:
        sub_users = await sync_to_async(list)(
            Users.objects.filter(ref_by=uid).values_list("id", flat=True)
        )
        level3_users.extend(sub_users)

    # ========================
    # Hitung bonus per level
    # ========================
    async def total_bonus_for_level(level: int):
        entries = await sync_to_async(list)(
            Referral_earnings.objects.filter(user_id=user_id, level=level).values_list("amount", flat=True)
        )
        return sum(entries)

    bonus_level_1 = await total_bonus_for_level(1)
    bonus_level_2 = await total_bonus_for_level(2)
    bonus_level_3 = await total_bonus_for_level(3)

    total_bonus_usd = bonus_level_1 + bonus_level_2 + bonus_level_3
    total_bonus_idr = total_bonus_usd * USD_RATE

    # ========================
    # Format Teks
    # ========================
    text = (
        f"📊 Statistik Referral Kamu:\n\n"
        f"👥 Total team size: {len(level1_users) + len(level2_users) + len(level3_users)}\n\n"
        f"Level 1 sub-user: {len(level1_users)}\n"
        f"Level 2 sub-user: {len(level2_users)}\n"
        f"Level 3 sub-user: {len(level3_users)}\n"
        f"\n------------------\n"
        f"💰 Total team reward: ${total_bonus_usd:.2f}\n\n"
        f"Level 1: ${bonus_level_1:.2f}\n"
        f"Level 2: ${bonus_level_2:.2f}\n"
        f"Level 3: ${bonus_level_3:.2f}\n"
        f"\n💸 Total dalam IDR: Rp {int(total_bonus_idr):,}".replace(",", ".")
    )

    await msg.answer(text)
