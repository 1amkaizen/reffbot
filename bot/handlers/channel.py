# Letak: bot/handlers/channel.py

from aiogram import Router, types
from aiogram.types import Message
from core.config import ADMIN_ID
from datetime import datetime
import re
import logging

from bot.models import Users, ReferralEarnings, Settings

router = Router()
logger = logging.getLogger("bot.channel")

BONUS_PERCENT = {1: 0.05, 2: 0.03, 3: 0.02}
CURRENCIES = ["USDT", "TRX", "BDT", "PKR", "IDR"]

@router.channel_post()
async def handle_channel_post(msg: Message):
    if not msg.text:
        logger.warning("⚠️ Pesan dari channel kosong, dilewati.")
        return

    logger.info(f"📨 Channel post diterima dari {msg.chat.id}")
    logger.debug(f"📝 Isi pesan:\n{msg.text}")

    try:
        user_id_match = re.search(r"ID:\s*(\d+)", msg.text)
        if not user_id_match:
            logger.warning("❌ Tidak ditemukan user ID di pesan channel.")
            return
        user_id = int(user_id_match.group(1))
        logger.info(f"👤 ID pengguna yang ditemukan: {user_id}")

        username_match = re.search(r"Username:\s*@?(\w+)", msg.text)
        username = username_match.group(1) if username_match else "unknown"
        logger.info(f"🔍 Username ditemukan: @{username}")

        earnings = {}
        for currency in CURRENCIES:
            match = re.search(fr"{currency}:\s*([\d.]+)", msg.text)
            if match:
                value = float(match.group(1))
                earnings[currency] = value
                logger.info(f"💰 Ditemukan {currency}: {value}")

        if not earnings:
            logger.warning("❌ Tidak ada earnings yang ditemukan di pesan channel.")
            return

        # Ambil rate dari Settings
        settings = Settings.objects.all()
        rates = {}
        for s in settings:
            try:
                rates[s.key.upper()] = float(s.value)
            except:
                continue

        total_usd = 0.0
        for currency, amount in earnings.items():
            rate = rates.get(currency.upper())
            if rate:
                usd_value = amount / rate
                total_usd += usd_value
                logger.info(f"🔄 {amount} {currency} → {usd_value:.2f} USD (rate: {rate})")
            else:
                logger.warning(f"⚠️ Tidak ada rate untuk {currency}, dilewati.")

        total_usd = round(total_usd, 2)
        logger.info(f"💵 Total earnings (USD): {total_usd}")

        if total_usd <= 0:
            logger.warning("❌ Total USD <= 0, tidak ada bonus yang didistribusikan.")
            return

        try:
            await msg.bot.send_message(
                chat_id=user_id,
                text="✅ Transaksi kamu telah diproses dan bonus referral sudah didistribusikan."
            )
        except Exception as e:
            logger.warning(f"❌ Gagal kirim notifikasi ke user {user_id}: {e}")

        try:
            await msg.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📥 Withdrawal dari @{username} (ID: {user_id}) berhasil diproses."
            )
        except Exception as e:
            logger.warning(f"❌ Gagal kirim notifikasi ke admin: {e}")

        current_id = user_id
        for level in range(1, 4):
            try:
                user = Users.objects.get(id=current_id)
                referrer_id = user.ref_by
                if not referrer_id:
                    logger.info(f"🔚 Tidak ada referrer di level {level} untuk ID {current_id}")
                    break
            except Users.DoesNotExist:
                logger.info(f"🔚 User ID {current_id} tidak ditemukan.")
                break

            bonus = round(total_usd * BONUS_PERCENT[level], 2)
            if bonus <= 0:
                logger.info(f"⚠️ Bonus USD untuk level {level} = 0, dilewati.")
                current_id = referrer_id
                continue

            # Simpan ReferralEarnings
            ReferralEarnings.objects.create(
                user_id=referrer_id,
                from_user_id=user_id,
                amount=bonus,
                level=level,
                currency="USD",
                date=datetime.utcnow().isoformat(timespec="seconds") + "Z"
            )
            logger.info(f"✅ Bonus {bonus} USD disimpan untuk user {referrer_id} dari level {level}")

            # Update bonus_balance dan total_bonus
            Users.objects.filter(id=referrer_id).update(
                bonus_balance=models.F('bonus_balance') + bonus,
                total_bonus=models.F('total_bonus') + bonus
            )
            logger.info(f"⬆️ bonus_balance dan total_bonus user {referrer_id} ditambah {bonus} USD")

            try:
                await msg.bot.send_message(
                    chat_id=referrer_id,
                    text=f"💸 Kamu menerima bonus {bonus} USD dari referral @{username} (Level {level})."
                )
            except Exception as e:
                logger.warning(f"❌ Gagal kirim notifikasi ke referrer {referrer_id}: {e}")

            current_id = referrer_id

    except Exception as e:
        logger.error(f"❌ [CHANNEL ERROR] {e}")
