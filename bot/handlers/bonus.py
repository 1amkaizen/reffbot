# Letak: bot/handlers/bonus.py

from aiogram import Router, types
from aiogram.filters import Command
from bot.models import ReferralEarnings, Settings
from django.db.models import Sum
from asgiref.sync import sync_to_async  # <- penting!

router = Router()

@router.message(Command("bonus"))
async def bonus_handler(msg: types.Message):
    user_id = msg.from_user.id

    @sync_to_async
    def get_total_bonus():
        return (
            ReferralEarnings.objects
            .filter(user_id=user_id)
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

    @sync_to_async
    def get_bonus_rates():
        setting_keys = [f"bonus_level_{i}" for i in range(1, 4)]
        settings = Settings.objects.filter(key__in=setting_keys)
        return {s.key: float(s.value) for s in settings}

    total = await get_total_bonus()
    rates = await get_bonus_rates()

    bonus_text = "\n".join(
        f"Level {i} → {rates.get(f'bonus_level_{i}', 0.0) * 100:.2f}%"
        for i in range(1, 4)
    )

    await msg.answer(
        f"💰 Total bonus kamu: ${total:.2f}\n\n"
        f"📊 Bonus Rate Referral:\n{bonus_text}"
    )
