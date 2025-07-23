# Letak: bot/handlers/admin_rate.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase, ADMIN_IDS

router = Router()

@router.message(Command("setrate"))
async def set_usd_rate(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:  # ✅ FIXED
        return await msg.answer("❌ Kamu tidak punya akses untuk perintah ini.")

    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await msg.answer("Format salah. Contoh: /setrate 16500")

    new_rate = int(parts[1])

    # Cek apakah key "usd_rate" sudah ada
    existing = supabase.table("Settings").select("key").eq("key", "usd_rate").execute()
    if existing.data:
        supabase.table("Settings").update({"value": str(new_rate)}).eq("key", "usd_rate").execute()
    else:
        supabase.table("Settings").insert({"key": "usd_rate", "value": str(new_rate)}).execute()

    await msg.answer(f"✅ Rate USD berhasil diupdate ke Rp {new_rate}")
