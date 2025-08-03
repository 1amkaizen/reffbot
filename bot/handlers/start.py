# Letak: bot/handlers/start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from bot.models import Users, Settings  # ReferralEarnings tidak dipakai di sini
from datetime import datetime
from asgiref.sync import sync_to_async
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from core.config import REQUIRED_CHANNEL

router = Router()
logger = logging.getLogger("bot.start")

@router.message(CommandStart())
async def start_handler(msg: types.Message):
    user_id = msg.from_user.id
    fullname = msg.from_user.full_name
    username = msg.from_user.username

    logger.info(f"👤 Start command from user: {user_id} ({username})")

    # Ambil kode referral dari parameter
    parts = msg.text.split(" ")
    ref_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    logger.info(f"🔗 Referral code: {ref_code}" if ref_code else "ℹ️ No referral code provided")

    # Cek apakah user sudah terdaftar
    user_exists = await sync_to_async(Users.objects.filter(id=user_id).exists)()

    if user_exists:
        logger.info(f"✅ User {user_id} already registered")

        # Pastikan fullname dan username terisi
        await sync_to_async(Users.objects.filter(id=user_id).update)(
            fullname=fullname,
            username=username,
        )

        return await check_and_prompt_join(msg)


    # Register user baru
    try:
        await sync_to_async(Users.objects.create)(
            id=user_id,
            fullname=fullname,
            username=username,
            ref_by=ref_code,
            joined_at=datetime.utcnow().isoformat()
        )
        logger.info(f"🆕 New user registered: {user_id} ({username})")
        if ref_code:
            logger.info(f"👥 Referral recorded: {user_id} was referred by {ref_code}")
    except Exception as e:
        logger.error(f"❌ Error inserting new user: {e}")
        return await msg.answer("Terjadi kesalahan saat mendaftar.")

    return await check_and_prompt_join(msg)

# Cek apakah user sudah join channel
async def check_and_prompt_join(msg: types.Message):
    try:
        chat_member = await msg.bot.get_chat_member(chat_id=f"@{REQUIRED_CHANNEL}", user_id=msg.from_user.id)
        if chat_member.status in ("member", "administrator", "creator"):
            welcome_text = await get_welcome_message()
            return await msg.answer(welcome_text or "Kamu sudah terdaftar!")  # fallback jika tidak ada
    except TelegramBadRequest as e:
        logger.warning(f"⚠️ Gagal cek keanggotaan channel: {e}")

    # User belum join, tampilkan tombol join
    join_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL}")]
    ])
    return await msg.answer(
        "Untuk melanjutkan, silakan join channel terlebih dahulu.",
        reply_markup=join_keyboard
    )

# Ambil welcome message dari database
async def get_welcome_message():
    try:
        setting = await sync_to_async(Settings.objects.filter(key="welcome_message").first)()
        return setting.value if setting else None
    except Exception as e:
        logger.warning(f"⚠️ Gagal ambil welcome message dari DB: {e}")
        return None
