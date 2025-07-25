# Letak: bot/handlers/withdraw.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from bot.models import Users, ReferralEarnings, WithdrawRequests, Settings
from asgiref.sync import sync_to_async

router = Router()

# ========== FIXRATE UTILITY ==========
# Ambil setting rate dari Settings
async def get_all_rates():
    keys = ["TRX", "BDT", "PKR", "IDR"]
    defaults = {"TRX": 1, "BDT": 1, "PKR": 1, "IDR": 16000}
    data = await sync_to_async(list)(
        Settings.objects.filter(key__in=keys).values("key", "value")
    )
    rates = {"USDT": 1.0}
    for item in data:
        try:
            rates[item["key"].upper()] = float(item["value"])
        except:
            rates[item["key"].upper()] = defaults[item["key"].upper()]
    for key in keys:
        rates.setdefault(key, defaults[key])
    return rates

# Konversi list withdrawal ke USD
def sum_usd(data, rates):
    total = 0.0
    for item in data:
        amount = float(item.get("amount", 0))
        currency = item.get("currency", "USD")
        rate = rates.get(currency.upper(), 1)
        total += amount / rate
    return total


# ========== WITHDRAW COMMAND ==========
@router.message(Command("withdraw"))
async def handle_withdraw(msg: types.Message):
    user_id = msg.from_user.id

    user_exists = await sync_to_async(Users.objects.filter(id=user_id).exists)()
    if not user_exists:
        return await msg.answer("❌ Data akun kamu tidak ditemukan.")

    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount")
    )
    total_bonus = sum(float(row["amount"]) for row in bonus_data)

    pending = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").values("amount", "currency")
    )

    approved = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="approved").values("amount", "currency")
    )

    rates = await get_all_rates()
    pending_usd = sum_usd(pending, rates)
    withdrawn_usd = sum_usd(approved, rates)
    can_be_withdrawn = max(total_bonus - pending_usd - withdrawn_usd, 0.0)


    msg_text = (
        "📊 <b>Details of your funds (USD)</b>\n"
        "------------------\n"
        f"💰 <b>total amount obtained:</b> {total_bonus:.2f}\n"
        "------------------\n"
        f"✅ Amount that can be withdrawn: {can_be_withdrawn:.2f}\n"
        f"⏳ Amount being withdrawn: {pending_usd:.2f}\n"
        f"📤 Amount already withdrawn: {withdrawn_usd:.2f}\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Withdraw Sekarang", callback_data="withdraw_now")]
    ])

    await msg.answer(msg_text, parse_mode="HTML", reply_markup=keyboard)
