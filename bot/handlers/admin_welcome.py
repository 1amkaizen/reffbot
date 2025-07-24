# File: bot/handlers/admin_welcome.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import ADMIN_IDS
from bot.models import Settings
from asgiref.sync import sync_to_async  # ⬅️ tambahkan ini

router = Router()

@router.message(Command("setwelcome"))
async def set_welcome_message(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses ke perintah ini.")

    new_text = msg.text.replace("/setwelcome", "").strip()
    if not new_text:
        return await msg.answer("Kirim pesan seperti ini:\n`/setwelcome Selamat datang di bot ini...`", parse_mode="Markdown")

    await sync_to_async(Settings.objects.update_or_create)(
        key="welcome_message",
        defaults={"value": new_text}
    )

    await msg.answer("✅ Pesan sambutan berhasil diupdate.")
