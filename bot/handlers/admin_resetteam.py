# Letak: bot/handlers/admin_resetteam.py

from aiogram import Router, types, F
from core.config import ADMIN_IDS
from bot.models import Settings
from asgiref.sync import sync_to_async

router = Router()

@router.message(F.text.startswith("/resetteam"))
async def reset_team_setting_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses.")

    # Format: /resetteam <jumlah_bulan>
    parts = msg.text.strip().split()
    if len(parts) != 2:
        return await msg.answer("⚠️ Format salah.\nGunakan: /resetteam <jumlah_bulan>")

    try:
        months = int(parts[1])
        if months <= 0:
            return await msg.answer("⛔ Jumlah bulan harus lebih dari 0.")
    except ValueError:
        return await msg.answer("⛔ Jumlah bulan harus berupa angka.")

    setting_key = "team_reset_expire_months"

    # Update atau buat setting di DB
    existing = await sync_to_async(lambda: Settings.objects.filter(key=setting_key).first())()
    if existing:
        existing.value = str(months)
        await sync_to_async(existing.save)()
    else:
        await sync_to_async(Settings.objects.create)(key=setting_key, value=str(months))

    await msg.answer(f"✅ Sistem akan reset otomatis team & reward user setelah {months} bulan dari tanggal mereka join.")
