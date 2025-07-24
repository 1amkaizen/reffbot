# File: bot/handlers/withdraw_callback.py

from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.models import Users, ReferralEarnings, WithdrawRequests
from asgiref.sync import sync_to_async
from datetime import datetime
import pytz

router = Router()

class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_card = State()

# Start withdraw (USD only)
@router.callback_query(F.data == "withdraw_now")
async def withdraw_now_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("💵 Please enter the amount you want to withdraw (USD):")
    await state.set_state(WithdrawState.waiting_for_amount)

# Receive amount
@router.message(WithdrawState.waiting_for_amount)
async def amount_received(msg: types.Message, state: FSMContext):
    try:
        amount = float(msg.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await msg.answer("❌ Invalid amount format. Please send a number, e.g., 10")

    user_id = msg.from_user.id

    # Check if user exists
    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ Your account data was not found.")

    # Get bonus data
    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount", "currency")
    )
    total_bonus = sum(float(row["amount"]) for row in bonus_data)

    pending = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").values("amount", "currency")
    )
    approved = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="approved").values("amount", "currency")
    )

    # Convert all to USD
    def sum_usd(data):
        return sum(float(row.get("amount", 0)) for row in data if row.get("currency", "USD") == "USD")

    pending_usd = sum_usd(pending)
    approved_usd = sum_usd(approved)
    can_withdraw = total_bonus - pending_usd - approved_usd

    if amount > can_withdraw:
        return await msg.answer(f"❌ Insufficient balance.\nAvailable: ${can_withdraw:.2f}")

    await state.update_data(amount=amount)
    await msg.answer("💳 Please enter your Card Name or Wallet Address:")
    await state.set_state(WithdrawState.waiting_for_card)

@router.message(WithdrawState.waiting_for_card)
async def card_received(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    card_name = msg.text.strip()
    user_id = msg.from_user.id

    if not card_name:
        return await msg.answer("❌ Invalid input. Please enter a valid Card Name or Wallet Address.")

    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ User not found.")

    # ⬇️ Hitung ulang total saldo bisa withdraw
    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount", "currency")
    )
    total_bonus = sum(float(row["amount"]) for row in bonus_data)

    pending = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").values("amount", "currency")
    )
    approved = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="approved").values("amount", "currency")
    )

    def sum_usd(data):
        return sum(float(row.get("amount", 0)) for row in data if row.get("currency", "USD") == "USD")

    pending_usd = sum_usd(pending)
    approved_usd = sum_usd(approved)
    can_withdraw = total_bonus - pending_usd - approved_usd

    # ⛔ Jika gagal withdraw, stop sampai sini (tidak buat request dan tidak kirim channel)
    if amount > can_withdraw:
        await state.clear()
        return await msg.answer(f"❌ Withdraw failed. You don't have enough balance.\nAvailable: ${can_withdraw:.2f}")

    # ✅ Simpan withdraw ke DB
    now = datetime.now(pytz.timezone("Asia/Dhaka"))  # UTC+6
    date_str = now.strftime("%m/%d/%y %H:%M:%S")
    time_str = now.strftime("%H:%M:%S")

    await sync_to_async(WithdrawRequests.objects.create)(
        user=user,
        amount=amount,
        currency="USD",
        status="pending",
        created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        card_name=card_name,
    )

    # ✅ Balas ke user
    await msg.answer(
        f"📤 Your transfer has been successful ✅\n\n"
        f"• Name: {user.fullname or msg.from_user.full_name}\n"
        f"• Card Name: {card_name}\n"
        f"• Total Balance: ${user.bonus_balance:.2f}\n"
        f"• Total Account: {amount:.2f}\n"
        f"• User ID: {user_id}\n\n"
        f"• Date: {date_str}\n"
        f"• Time: {time_str} (UTC +6:00)\n\n"
        f"🎉 It may take up to 24 hours to process your withdraw. Please wait.",
        parse_mode="HTML"
    )

    # 🧼 Clear FSM state
    await state.clear()