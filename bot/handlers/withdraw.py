# Letak: bot/handlers/withdraw.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase
from datetime import datetime

router = Router()

@router.message(Command("withdraw"))
async def handle_withdraw(msg: types.Message):
    user_id = msg.from_user.id

    # Ambil data user
    user_res = supabase.table("Users").select("id").eq("id", user_id).execute()
    if not user_res.data:
        return await msg.answer("❌ Data akun kamu tidak ditemukan.")

    # Hitung total bonus dari Referral_earnings
    bonus_data = supabase.table("Referral_earnings")\
        .select("amount")\
        .eq("user_id", user_id)\
        .execute()
    total_bonus = sum(float(row["amount"]) for row in bonus_data.data)

    # Ambil total withdrawal yang sedang diproses
    pending_res = supabase.table("Withdraw_requests")\
        .select("amount, currency")\
        .eq("user_id", user_id)\
        .eq("status", "pending")\
        .execute()

    # Ambil total withdrawal yang sudah berhasil
    success_res = supabase.table("Withdraw_requests")\
        .select("amount, currency")\
        .eq("user_id", user_id)\
        .eq("status", "approved")\
        .execute()

    # Fungsi konversi ke USD
    def sum_usd(data):
        rates = {
            "USDT": 1.0,
            "TRX": float(get_setting("TRX") or 1),
            "BDT": float(get_setting("BDT") or 1),
            "PKR": float(get_setting("PKR") or 1),
            "IDR": float(get_setting("IDR") or 16000),
        }
        total = 0.0
        for item in data:
            amount = float(item.get("amount", 0))
            currency = item.get("currency", "USD")
            rate = rates.get(currency.upper(), 1)
            total += amount / rate
        return total

    pending_usd = sum_usd(pending_res.data)
    withdrawn_usd = sum_usd(success_res.data)
    can_be_withdrawn = total_bonus - pending_usd - withdrawn_usd

    msg_text = (
        "📊 <b>Details of your funds (USD)</b>\n"
        "------------------\n"
        f"💰 <b>total amount obtained:</b> {total_bonus:.2f}\n"
        "------------------\n"
        f"✅ Amount that can be withdrawn: {can_be_withdrawn:.2f}\n"
        f"⏳ Amount being withdrawn: {pending_usd:.2f}\n"
        f"📤 Amount already withdrawn: {withdrawn_usd:.2f}\n\n"
        "➡️ Click here to withdraw now → <code>/withdrawcash</code>"
    )

    await msg.answer(msg_text, parse_mode="HTML")


# Helper ambil setting dari tabel Settings
def get_setting(key: str) -> str:
    res = supabase.table("Settings").select("value").eq("key", key.upper()).limit(1).execute()
    if res.data:
        return res.data[0]["value"]
    return None
