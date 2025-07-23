# File: bot/handlers/stats.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase, USD_RATE

router = Router()

@router.message(Command("stats"))
async def stats_handler(msg: types.Message):
    user_id = msg.from_user.id

    # ========================
    # Ambil Level 1
    # ========================
    level1_result = supabase.table("Users").select("id").eq("ref_by", user_id).execute()
    level1_users = [user["id"] for user in level1_result.data]
    
    # ========================
    # Ambil Level 2
    # ========================
    level2_users = []
    for uid in level1_users:
        result = supabase.table("Users").select("id").eq("ref_by", uid).execute()
        level2_users.extend([user["id"] for user in result.data])

    # ========================
    # Ambil Level 3
    # ========================
    level3_users = []
    for uid in level2_users:
        result = supabase.table("Users").select("id").eq("ref_by", uid).execute()
        level3_users.extend([user["id"] for user in result.data])

    # ========================
    # Hitung bonus per level
    # ========================
    def total_bonus_for_level(level: int):
        result = supabase.table("Referral_earnings").select("amount").eq("user_id", user_id).eq("level", level).execute()
        return sum(item["amount"] for item in result.data) if result.data else 0.0

    bonus_level_1 = total_bonus_for_level(1)
    bonus_level_2 = total_bonus_for_level(2)
    bonus_level_3 = total_bonus_for_level(3)

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
