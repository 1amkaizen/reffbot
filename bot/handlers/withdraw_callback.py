# Letak: bot/handlers/withdraw_callback.py

from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.models import Users, ReferralEarnings, WithdrawRequests
from asgiref.sync import sync_to_async
from datetime import datetime
from core.config import ADMIN_CHANNEL_ID
import pytz
import os
from django.db.models import Count

router = Router()

class WithdrawState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_card = State()

@router.callback_query(F.data == "withdraw_now")
async def withdraw_now_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("💵 Please enter the amount you want to withdraw (USD):")
    await state.set_state(WithdrawState.waiting_for_amount)

@router.message(WithdrawState.waiting_for_amount)
async def amount_received(msg: types.Message, state: FSMContext):
    try:
        amount = float(msg.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await msg.answer("❌ Invalid amount format. Please send a number, e.g., 10")

    user_id = msg.from_user.id
    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ Your account data was not found.")

    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount", "currency")
    )
    total_bonus = sum(float(r["amount"]) for r in bonus_data)

    pending = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").values("amount", "currency")
    )
    approved = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="approved").values("amount", "currency")
    )

    def sum_usd(data):
        return sum(float(row.get("amount", 0)) for row in data if row.get("currency", "USD") == "USD")

    can_withdraw = total_bonus - sum_usd(pending) - sum_usd(approved)

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

    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount", "currency")
    )
    total_bonus = sum(float(r["amount"]) for r in bonus_data)

    pending = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").values("amount", "currency")
    )
    approved = await sync_to_async(list)(
        WithdrawRequests.objects.filter(user_id=user_id, status="approved").values("amount", "currency")
    )

    def sum_usd(data):
        return sum(float(row.get("amount", 0)) for row in data if row.get("currency", "USD") == "USD")

    can_withdraw = total_bonus - sum_usd(pending) - sum_usd(approved)

    if amount > can_withdraw:
        await state.clear()
        return await msg.answer(f"❌ Withdraw failed. You don't have enough balance.\nAvailable: ${can_withdraw:.2f}")

    now = datetime.now(pytz.timezone("Asia/Dhaka"))
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

    await msg.answer(
        f"📤 Your transfer has been successful ✅\n\n"
        f"• Name: {user.fullname or msg.from_user.full_name}\n"
        f"• Card Name: {card_name}\n"
        f"• Total Balance: ${total_bonus:.2f}\n"
        f"• Total Account: ${amount:.2f}\n"
        f"• User ID: {user_id}\n\n"
        f"• Date: {date_str}\n"
        f"• Time: {time_str} (UTC +6:00)\n\n"
        f"🎉 It may take up to 24 hours to process your withdraw. Please wait.",
        parse_mode="HTML"
    )

    # Fixrate dari env
    trx_rate = float(os.getenv("TRX_RATE", "13.93"))
    bdt_rate = float(os.getenv("BDT_RATE", "69.57"))
    pkr_rate = float(os.getenv("PKR_RATE", "41.75"))
    idr_rate = float(os.getenv("USD_RATE", "16000"))

    usdt = amount
    trx = amount * trx_rate
    bdt = amount * bdt_rate
    pkr = amount * pkr_rate
    idr = amount * idr_rate

    username = msg.from_user.username or "❌"

    # Hitung jumlah withdraw per negara realtime
    withdraw_counts = await sync_to_async(
        lambda: list(
            WithdrawRequests.objects.filter(status__in=["pending", "approved"])
            .values("user__country_code")
            .annotate(count=Count("id"))
        )
    )()

    # Format negara + jumlah
    country_lines = []
    for item in withdraw_counts:
        country_code = item["user__country_code"] or "Unknown"
        count = item["count"]
        country_lines.append(f"Country {country_code} => {count}")

    country_info = "\n".join(country_lines) if country_lines else "No withdraw data"

    withdraw_info = (
        f"🌳 Withdrawal Information #reffbot\n\n"
        f"• Name: {user.fullname or msg.from_user.full_name}\n"
        f"• ID: {user_id}\n"
        f"• Username: {username}\n"
        f"• USDT: {usdt:.2f}\n"
        f"• TRX: {trx:.2f}\n"
        f"• BDT: {bdt:.2f}\n"
        f"• PKR: {pkr:.2f}\n"
        f"• IDR: {int(idr)}\n\n"
        f"• Card Info: {card_name}\n"
        f"• Date: {date_str}\n"
        f"• Time: {time_str} (UTC +6:00)\n\n"
        f"{country_info}"
    )
    await msg.bot.send_message(chat_id=int(ADMIN_CHANNEL_ID), text=withdraw_info)


    await state.clear()
