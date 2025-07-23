# Letak: bot/handlers/withdraw_cash.py

from aiogram import Router, types
from aiogram.filters import Command
from datetime import datetime
from core.config import USD_RATE
from bot.models import Users, WithdrawRequests, Settings
from asgiref.sync import sync_to_async

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
    rates = await get_currency_rates()

    rate = rates.get(currency)
    if not rate:
        return await msg.answer(f"❌ Rate untuk mata uang {currency} belum diatur di Settings.")

    # Ambil bonus_balance user
    user = await sync_to_async(Users.objects.filter(id=user_id).first)()
    if not user:
        return await msg.answer("❌ Akun kamu belum memiliki saldo bonus.")

    bonus_balance = float(user.bonus_balance)

    # Hitung nilai dalam USD dari jumlah withdraw yang diminta
    requested_usd = amount if currency == "USD" else amount / rate

    if bonus_balance < requested_usd:
        return await msg.answer("❌ Saldo kamu tidak cukup untuk withdraw jumlah tersebut.")

    # Kurangi saldo user
    user.bonus_balance = bonus_balance - requested_usd
    await sync_to_async(user.save)()

    # Simpan permintaan withdraw
    await sync_to_async(WithdrawRequests.objects.create)(
        user_id=user_id,
        amount=amount,
        currency=currency,
        status="pending",
        created_at=datetime.utcnow().isoformat()
    )

    await msg.answer("✅ Permintaan withdraw kamu sudah dicatat dan akan diproses oleh admin.")


# Ambil semua rate dari Settings
async def get_currency_rates():
    items = await sync_to_async(list)(
        Settings.objects.filter(key__in=VALID_CURRENCIES).values("key", "value")
    )
    rates = {}
    for item in items:
        try:
            rates[item["key"].upper()] = float(item["value"])
        except (KeyError, ValueError):
            continue
    return rates
