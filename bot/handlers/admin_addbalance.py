# File: bot/handlers/admin_addbalance.py

from aiogram import Router, types
from aiogram.filters import Command
from bot.models import Users, ReferralEarnings
from asgiref.sync import sync_to_async
from core.config import ADMIN_IDS
from datetime import datetime

router = Router()

@router.message(Command("addbalance"))
async def add_balance_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ You are not authorized to use this command.")

    args = msg.text.strip().split()
    if len(args) != 3:
        return await msg.answer("⚠️ Usage: /addbalance <user_id> <amount>")

    try:
        user_id = int(args[1])
        amount = float(args[2])
    except ValueError:
        return await msg.answer("❌ Invalid format. Make sure user_id is a number and amount is numeric.")

    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ User not found.")

    # Tambahkan balance
    user.bonus_balance += amount
    user.total_bonus += amount
    await sync_to_async(user.save)()

    # Log ke referral earnings (manual topup)
    await sync_to_async(ReferralEarnings.objects.create)(
        user=user,
        from_user_id=0,
        amount=amount,
        level=0,
        date=datetime.now().strftime("%Y-%m-%d"),
        currency="USD"
    )

    await msg.answer(f"✅ Successfully added ${amount:.2f} to user {user_id}.")
