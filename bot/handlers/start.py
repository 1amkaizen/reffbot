# Letak: bot/handlers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from bot.models import Users, ReferralEarnings # ORM models
from datetime import datetime
from asgiref.sync import sync_to_async
import logging

router = Router()
logger = logging.getLogger("bot.start")

REFERRAL_BONUS_LEVEL1 = 1.0  # bisa diubah nanti

@router.message(CommandStart())
async def start_handler(msg: types.Message):
    user_id = msg.from_user.id
    fullname = msg.from_user.full_name
    username = msg.from_user.username

    logger.info(f"👤 Start command from user: {user_id} ({username})")

    parts = msg.text.split(" ")
    ref_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    logger.info(f"🔗 Referral code: {ref_code}" if ref_code else "ℹ️ No referral code provided")

    # Cek apakah user sudah ada
    user_exists = await sync_to_async(Users.objects.filter(id=user_id).exists)()
    if user_exists:
        logger.info(f"✅ User {user_id} already registered")
        return await msg.answer("Kamu sudah terdaftar!")

    try:
        # Simpan user baru
        await sync_to_async(Users.objects.create)(
            id=user_id,
            fullname=fullname,
            username=username,
            ref_by=ref_code,
            joined_at=datetime.utcnow().isoformat()
        )
        logger.info(f"🆕 New user registered: {user_id} ({username})")
    except Exception as e:
        logger.error(f"❌ Error inserting new user: {e}")
        return await msg.answer("Terjadi kesalahan saat mendaftar.")

    if ref_code:
        try:
            await sync_to_async(Referral_earnings.objects.create)(
                user_id=ref_code,
                from_user_id=user_id,
                amount=REFERRAL_BONUS_LEVEL1,
                level=1,
                date=datetime.utcnow().isoformat()
            )
            logger.info(f"🎁 Bonus referral diberikan ke {ref_code} dari {user_id}")
        except Exception as e:
            logger.error(f"[REFERRAL ERROR] Gagal insert referral bonus: {e}")

        await msg.answer("Selamat datang! Kamu terdaftar lewat referral.")
    else:
        await msg.answer("Selamat datang! Kamu sudah terdaftar.")
