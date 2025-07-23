# Letak: bot/handlers/bonus.py

from aiogram import Router, types
from aiogram.filters import Command
from bot.models import ReferralEarnings, Settings

router = Router()

@router.message(Command("bonus"))
async def bonus_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Ambil total bonus dari tabel ReferralEarnings
    total = ReferralEarnings.objects.filter(user_id=user_id).aggregate_total()

    # Ambil bonus rate level 1–3 dari Settings
    setting_keys = [f"bonus_level_{i}" for i in range(1, 4)]
    settings = Settings.objects.filter(key__in=setting_keys)
    rates = {s.key: float(s.value) for s in settings}

    bonus_text = "\n".join(
        f"Level {i} → {rates.get(f'bonus_level_{i}', 0.0) * 100:.2f}%"
        for i in range(1, 4)
    )

    await msg.answer(
        f"💰 Total bonus kamu: ${total:.2f}\n\n"
        f"📊 Bonus Rate Referral:\n{bonus_text}"
    )
