# File: bot/handlers/admin_bonus.py
# Letak: bot/handlers/admin_bonus.py

from aiogram import Router, types, F
from aiogram.types import Message
from core.config import ADMIN_IDS
from bot.models import Settings  # Import model Settings

router = Router()

@router.message(F.text.startswith("/setbonus"))
async def handle_set_bonus(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Kamu tidak punya akses untuk perintah ini.")
        return

    parts = msg.text.strip().split()
    if len(parts) != 3:
        await msg.answer("❗ Format salah. Gunakan: /setbonus <level> <persentase>\nContoh: /setbonus 1 0.07")
        return

    try:
        level = int(parts[1])
        value = float(parts[2])
        if level not in (1, 2, 3) or not (0 <= value <= 1):
            raise ValueError
    except ValueError:
        await msg.answer("❗ Level harus 1–3 dan persentase antara 0.0 hingga 1.0")
        return

    key = f"bonus_level_{level}"
    # Simpan atau update ke DB pakai Django ORM
    Settings.objects.update_or_create(key=key, defaults={"value": str(value)})

    await msg.answer(f"✅ Bonus level {level} berhasil diset ke {value * 100:.2f}%")
