# 📍 Letak: bot/handlers/admin_rate.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import ADMIN_IDS
from bot.models import Settings
from asgiref.sync import sync_to_async
import logging

router = Router()

@router.message(Command("setrates"))
async def set_multi_rates(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses untuk perintah ini.")

    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return await msg.answer("Format salah.\nContoh: /setrates TRX:13.8 BDT:69.1")

    entries = parts[1].split()
    success, failed = [], []

    for entry in entries:
        try:
            symbol, rate_str = entry.split(":", 1)
            rate = float(rate_str)  # validasi

            await sync_to_async(Settings.objects.update_or_create)(
                key=f"rate_{symbol.upper()}",
                defaults={"value": str(rate)}
            )
            success.append(f"{symbol.upper()} = {rate}")
        except Exception:
            logging.exception(f"Gagal parsing rate entry: {entry}")
            failed.append(entry)

    result = ""
    if success:
        result += "✅ Rate berhasil disimpan untuk:\n" + "\n".join(success)
    if failed:
        result += f"\n⚠️ Gagal parsing untuk: {', '.join(failed)}"

    await msg.answer(result)
