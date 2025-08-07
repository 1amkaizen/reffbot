# 📍 Letak: bot/handlers/withdraw_callback.py

from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.models import Users, ReferralEarnings, WithdrawRequests, Settings
from asgiref.sync import sync_to_async
from datetime import datetime
from core.config import ADMIN_CHANNEL_ID
import pytz
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)
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

    logger.info(f"[Withdraw:Step1] User {user_id} | total_bonus={total_bonus:.2f} | pending={sum_usd(pending):.2f} | approved={sum_usd(approved):.2f} | can_withdraw={can_withdraw:.2f}")

    if amount > can_withdraw:
        return await msg.answer(f"❌ Insufficient balance.\nAvailable: ${can_withdraw:.2f}")

    await state.update_data(amount=amount)
    await msg.answer("💳 Please enter your Card Name or Wallet Address:")
    await state.set_state(WithdrawState.waiting_for_card)

@router.message(WithdrawState.waiting_for_card)
async def card_received(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = float(data.get("amount", 0))
    card_name = msg.text.strip()
    user_id = msg.from_user.id

    if not card_name:
        return await msg.answer("❌ Invalid input. Please enter a valid Card Name or Wallet Address.")

    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ User not found.")

    # 🔐 Cek apakah masih ada withdraw pending
    already_pending = await sync_to_async(
        WithdrawRequests.objects.filter(user_id=user_id, status="pending").exists
    )()
    if already_pending:
        return await msg.answer("❗ You already have a pending withdrawal request. Please wait for it to be processed first.")

    now = datetime.now(pytz.timezone("Asia/Dhaka"))
    date_str = now.strftime("%m/%d/%y %H:%M:%S")
    time_str = now.strftime("%H:%M:%S")

    withdraw = await sync_to_async(WithdrawRequests.objects.create)(
        user=user,
        amount=amount,
        currency="USD",
        status="pending",
        created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        card_name=card_name,
    )

    logger.info(f"[Withdraw:Create] Withdraw #{withdraw.id} created for user {user.id} amount ${amount}")

    # === Referral Reward ===
    try:
        already_given = await sync_to_async(ReferralEarnings.objects.filter(
            from_user_id=user.id,
            amount=amount,
            currency="USD",
            date=now.strftime("%Y-%m-%d")
        ).exists)()

        logger.info(f"[Referral:Check] WD #{withdraw.id} | User={user.id} | already_given={already_given} | ref_by={user.ref_by}")

        if not already_given and user.ref_by:
            level_1_user = await sync_to_async(Users.objects.filter(id=user.ref_by).first)()
            if level_1_user:
                reward_1 = round(amount * 0.05, 2)
                level_1_user.bonus_balance += reward_1
                level_1_user.total_bonus += reward_1
                await sync_to_async(level_1_user.save)()
                await sync_to_async(ReferralEarnings.objects.create)(
                    user=level_1_user,
                    from_user_id=user.id,
                    amount=reward_1,
                    level=1,
                    date=now.strftime("%Y-%m-%d"),
                    currency="USD"
                )
                logger.info(f"[Referral] Level 1 reward ${reward_1:.2f} → {level_1_user.id} (ref_by {user.id})")

                if level_1_user.ref_by:
                    level_2_user = await sync_to_async(Users.objects.filter(id=level_1_user.ref_by).first)()
                    if level_2_user:
                        reward_2 = round(amount * 0.03, 2)
                        level_2_user.bonus_balance += reward_2
                        level_2_user.total_bonus += reward_2
                        await sync_to_async(level_2_user.save)()
                        await sync_to_async(ReferralEarnings.objects.create)(
                            user=level_2_user,
                            from_user_id=user.id,
                            amount=reward_2,
                            level=2,
                            date=now.strftime("%Y-%m-%d"),
                            currency="USD"
                        )
                        logger.info(f"[Referral] Level 2 reward ${reward_2:.2f} → {level_2_user.id} (ref_by {user.id})")

                        if level_2_user.ref_by:
                            level_3_user = await sync_to_async(Users.objects.filter(id=level_2_user.ref_by).first)()
                            if level_3_user:
                                reward_3 = round(amount * 0.02, 2)
                                level_3_user.bonus_balance += reward_3
                                level_3_user.total_bonus += reward_3
                                await sync_to_async(level_3_user.save)()
                                await sync_to_async(ReferralEarnings.objects.create)(
                                    user=level_3_user,
                                    from_user_id=user.id,
                                    amount=reward_3,
                                    level=3,
                                    date=now.strftime("%Y-%m-%d"),
                                    currency="USD"
                                )
                                logger.info(f"[Referral] Level 3 reward ${reward_3:.2f} → {level_3_user.id} (ref_by {user.id})")
    except Exception as e:
        logger.exception(f"[Referral:ERROR] Failed to distribute referral reward | user={user.id} | wd={withdraw.id} | err={e}")

    # === User Notif ===
    bonus_data = await sync_to_async(list)(
        ReferralEarnings.objects.filter(user_id=user_id).values("amount", "currency")
    )
    total_bonus = sum(float(r["amount"]) for r in bonus_data)

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

    # === Rate Conversion ===
    async def get_rate(symbol: str, default: float = 0.0) -> float:
        try:
            setting = await sync_to_async(Settings.objects.get)(key=f"rate_{symbol.upper()}")
            return float(setting.value)
        except Settings.DoesNotExist:
            logger.warning(f"⚠️ Rate tidak ditemukan untuk {symbol.upper()}")
            return default
        except Exception as e:
            logger.exception(f"Gagal ambil rate untuk {symbol.upper()}: {e}")
            return default

    trx = amount * await get_rate("TRX", 0.0)
    bdt = amount * await get_rate("BDT", 0.0)
    pkr = amount * await get_rate("PKR", 0.0)
    idr = amount * await get_rate("IDR", 0.0)
    usdt = amount

    username = msg.from_user.username or "❌"
    withdraw_counts = await sync_to_async(
        lambda: list(
            WithdrawRequests.objects.filter(status__in=["pending", "approved"])
            .values("user__country_code")
            .annotate(count=Count("id"))
        )
    )()
    country_lines = [f"Country {row['user__country_code'] or 'Unknown'} => {row['count']}" for row in withdraw_counts]
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

    # 🔒 Kirim notifikasi ke channel admin dengan try-except
    try:
        await msg.bot.send_message(chat_id=int(ADMIN_CHANNEL_ID), text=withdraw_info)
    except Exception as e:
        logger.exception(f"[AdminNotif:ERROR] Failed to send withdraw info to admin channel | err={e}")

    await state.clear()
