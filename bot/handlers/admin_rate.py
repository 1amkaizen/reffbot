# File: bot/handlers/admin_rate.py
# Letak: bot/handlers/admin_rate.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import ADMIN_IDS
from bot.models import Settings  # ✅ Import model Settings

router = Router()

@router.message(Command("setrate"))
async def set_usd_rate(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses untuk perintah ini.")

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await msg.answer("Format salah. Contoh: /setrate 16500")

    new_rate = int(parts[1])

    # Update atau insert usd_rate
    Settings.objects.update_or_create(key="usd_rate", defaults={"value": str(new_rate)})

    await msg.answer(f"✅ Rate USD berhasil diupdate ke Rp {new_rate}")
