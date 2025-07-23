# File: bot/handlers/bonus.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase

router = Router()

@router.message(Command("bonus"))
async def bonus_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Ambil total bonus user dari tabel Referral_earnings
    result = supabase.table("Referral_earnings") \
        .select("amount") \
        .eq("user_id", user_id) \
        .execute()

    earnings = result.data or []
    total = sum(e["amount"] for e in earnings)

    # Ambil bonus rate level 1–3 dari tabel Settings
    setting_keys = [f"bonus_level_{i}" for i in range(1, 4)]
    settings = supabase.table("Settings") \
        .select("key", "value") \
        .in_("key", setting_keys) \
        .execute()

    rates = {s["key"]: float(s["value"]) for s in (settings.data or [])}

    bonus_text = "\n".join(
        f"Level {i} → {rates.get(f'bonus_level_{i}', 0.0) * 100:.2f}%"
        for i in range(1, 4)
    )

    await msg.answer(
        f"💰 Total bonus kamu: ${total:.2f}\n\n"
        f"📊 Bonus Rate Referral:\n{bonus_text}"
    )
