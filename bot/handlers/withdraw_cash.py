# File: bot/handlers/withdraw_cash.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase
from datetime import datetime

router = Router()

VALID_CURRENCIES = {"USDT", "TRX", "BDT", "PKR", "IDR"}

@router.message(Command("withdrawcash"))
async def handle_withdraw_cash(msg: types.Message):
    args = msg.text.split()
    if len(args) != 3:
        return await msg.answer(
            "Format salah. Contoh:\n<code>/withdrawcash 10 USDT</code>",
            parse_mode="HTML"
        )

    try:
        amount = float(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await msg.answer(
            "Jumlah harus berupa angka positif. Contoh:\n<code>/withdrawcash 10 USDT</code>",
            parse_mode="HTML"
        )

    currency = args[2].upper()
    if currency not in VALID_CURRENCIES:
        return await msg.answer(
            f"Mata uang tidak valid.\nPilihan: {', '.join(VALID_CURRENCIES)}"
        )

    user_id = msg.from_user.id
    rates = get_currency_rates()

    rate = rates.get(currency)
    if not rate:
        return await msg.answer(f"❌ Rate untuk mata uang {currency} belum diatur di Settings.")

    # Ambil bonus_balance user
    user_res = supabase.table("Users").select("bonus_balance").eq("id", user_id).execute()
    if not user_res.data:
        return await msg.answer("❌ Akun kamu belum memiliki saldo bonus.")

    user_data = user_res.data[0]
    bonus_balance = float(user_data.get("bonus_balance", 0.0))

    # Hitung nilai dalam USD dari jumlah withdraw yang diminta
    requested_usd = amount if currency == "USD" else amount / rate

    if bonus_balance < requested_usd:
        return await msg.answer("❌ Saldo kamu tidak cukup untuk withdraw jumlah tersebut.")

    # Kurangi bonus_balance via RPC Supabase
    supabase.rpc("increment_bonus_balance", {
        "uid": user_id,
        "amount": -requested_usd
    }).execute()

    # Simpan permintaan withdraw ke tabel Withdraw_requests
    supabase.table("Withdraw_requests").insert({
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    await msg.answer("✅ Permintaan withdraw kamu sudah dicatat dan akan diproses oleh admin.")


# Ambil semua rate dari Settings
def get_currency_rates():
    result = supabase.table("Settings").select("key", "value").in_("key", list(VALID_CURRENCIES)).execute()
    rates = {}
    for item in result.data:
        try:
            rates[item["key"].upper()] = float(item["value"])
        except (KeyError, ValueError):
            continue
    return rates
