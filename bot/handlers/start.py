# File: bot/handlers/start.py
# Letak: bot/handlers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from core.config import supabase
from datetime import datetime
import logging

router = Router()
logger = logging.getLogger("bot.start")  # ⬅️ setup logger lokal

REFERRAL_BONUS_LEVEL1 = 1.0  # bisa diubah nanti sesuai kebutuhan

@router.message(CommandStart())
async def start_handler(msg: types.Message):
    user_id = msg.from_user.id
    fullname = msg.from_user.full_name
    username = msg.from_user.username

    logger.info(f"👤 Start command from user: {user_id} ({username})")

    # Ambil kode referral jika ada
    parts = msg.text.split(" ")
    ref_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    logger.info(f"🔗 Referral code: {ref_code}" if ref_code else "ℹ️ No referral code provided")

    # Cek apakah user sudah ada
    existing = supabase.table("Users").select("id").eq("id", user_id).execute()
    if existing.data:
        logger.info(f"✅ User {user_id} already registered")
        return await msg.answer("Kamu sudah terdaftar!")

    # Simpan user baru ke tabel 'Users'
    try:
        supabase.table("Users").insert({
            "id": user_id,
            "fullname": fullname,
            "username": username,
            "ref_by": ref_code,
            "joined_at": datetime.utcnow().isoformat()
        }).execute()
        logger.info(f"🆕 New user registered: {user_id} ({username})")
    except Exception as e:
        logger.error(f"❌ Error inserting new user: {e}")
        return await msg.answer("Terjadi kesalahan saat mendaftar.")

    # Jika ada kode referral, tambahkan bonus
    if ref_code:
        try:
            supabase.table("Referral_earnings").insert({
                "user_id": ref_code,
                "from_user_id": user_id,
                "amount": REFERRAL_BONUS_LEVEL1,
                "level": 1,
                "date": datetime.utcnow().isoformat()
            }).execute()
            logger.info(f"🎁 Bonus referral diberikan ke {ref_code} dari {user_id}")
        except Exception as e:
            logger.error(f"[REFERRAL ERROR] Gagal insert referral bonus: {e}")

        await msg.answer("Selamat datang! Kamu terdaftar lewat referral.")
    else:
        await msg.answer("Selamat datang! Kamu sudah terdaftar.")
