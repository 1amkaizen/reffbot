# Letak: bot/handlers/channel.py

from aiogram import Router, types
from aiogram.types import Message
from core.config import supabase, ADMIN_ID

from datetime import datetime
import re
import logging

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
        # Ekstrak user ID Telegram
        user_id_match = re.search(r"ID:\s*(\d+)", msg.text)
        if not user_id_match:
            logger.warning("❌ Tidak ditemukan user ID di pesan channel.")
            return
        user_id = int(user_id_match.group(1))
        logger.info(f"👤 ID pengguna yang ditemukan: {user_id}")

        # Ekstrak nama & username
        username_match = re.search(r"Username:\s*@?(\w+)", msg.text)
        username = username_match.group(1) if username_match else "unknown"
        logger.info(f"🔍 Username ditemukan: @{username}")

        # Ekstrak earnings dari pesan
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

        # Ambil rate konversi dari Settings Supabase
        settings = supabase.table("Settings").select("key", "value").execute()
        rates = {}
        for s in settings.data:
            k = s["key"].upper()
            try:
                rates[k] = float(s["value"])
            except:
                continue

        # Hitung total earning dalam USD
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

        # Notifikasi ke user
        try:
            await msg.bot.send_message(
                chat_id=user_id,
                text="✅ Transaksi kamu telah diproses dan bonus referral sudah didistribusikan."
            )
        except Exception as e:
            logger.warning(f"❌ Gagal kirim notifikasi ke user {user_id}: {e}")

        # Notifikasi ke admin
        try:
            await msg.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📥 Withdrawal dari @{username} (ID: {user_id}) berhasil diproses."
            )
        except Exception as e:
            logger.warning(f"❌ Gagal kirim notifikasi ke admin: {e}")

        # Distribusi bonus ke referrer chain
        current_id = user_id
        for level in range(1, 4):
            user = supabase.table("Users").select("ref_by").eq("id", current_id).execute()
            if not user.data:
                logger.info(f"🔚 User ID {current_id} tidak ditemukan di database.")
                break

            referrer_id = user.data[0].get("ref_by")
            if not referrer_id:
                logger.info(f"🔚 Tidak ada referrer di level {level} untuk ID {current_id}")
                break

            bonus = round(total_usd * BONUS_PERCENT[level], 2)
            if bonus <= 0:
                logger.info(f"⚠️ Bonus USD untuk level {level} = 0, dilewati.")
                current_id = referrer_id
                continue

            # Simpan ke database
            supabase.table("Referral_earnings").insert({
                "user_id": referrer_id,
                "from_user_id": user_id,
                "amount": bonus,
                "level": level,
                "currency": "USD",
                "date": datetime.utcnow().isoformat(timespec="seconds") + "Z"
            }).execute()
            logger.info(f"✅ Bonus {bonus} USD disimpan untuk user {referrer_id} dari level {level}")


            # Update bonus_balance di tabel Users
            supabase.rpc("increment_bonus_balance", {
                "uid": referrer_id,
                "amount": bonus
            }).execute()
            logger.info(f"⬆️ bonus_balance user {referrer_id} ditambah {bonus} USD")

            # Update total_bonus juga
            supabase.rpc("increment_total_bonus", {
                "uid": referrer_id,
                "amount": bonus
            }).execute()
            logger.info(f"📈 total_bonus user {referrer_id} ditambah {bonus} USD")


            # Kirim notif ke referrer
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
