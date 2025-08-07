# 📍 Letak: bot/handlers/channel.py

from aiogram import Router, types
from aiogram.types import Message
from core.config import ADMIN_ID
from datetime import datetime
import re
import logging
from decimal import Decimal, InvalidOperation

from bot.models import Users, ReferralEarnings, Settings
from django.db import models
from asgiref.sync import sync_to_async

router = Router()
logger = logging.getLogger("bot.channel")

BONUS_PERCENT = {1: 0.05, 2: 0.03, 3: 0.02}
CURRENCIES = ["USDT", "TRX", "BDT", "PKR", "IDR", "USD"]

def extract_decimal(val: str):
    try:
        return Decimal(val.strip())
    except (InvalidOperation, AttributeError):
        return None

@router.channel_post()
async def handle_channel_post(msg: Message):
    if not msg.text:
        logger.warning("⚠️ Pesan dari channel kosong, dilewati.")
        return

    if not any(k in msg.text.lower() for k in ["id:", "username:", "name:"]):
        logger.info("🔕 Pesan tidak relevan, dilewati.")
        return

    logger.info(f"📨 Post channel masuk dari {msg.chat.id}")
    logger.debug(f"📝 Isi pesan:\n{msg.text}")

    try:
        # 🆔 Extract user data dari pesan
        user_id = None
        user_id_match = re.search(r"[•\-]?\s*ID:\s*(\d+)", msg.text, re.IGNORECASE)
        if user_id_match:
            user_id = int(user_id_match.group(1))

        username_match = re.search(r"[•\-]?\s*Username:\s*@?(\w+)", msg.text, re.IGNORECASE)
        username = username_match.group(1) if username_match else None

        name_match = re.search(r"[•\-]?\s*Name:\s*(.+)", msg.text, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else None

        # 🔍 Jika ID tidak ada, cari dari username atau nama
        if not user_id:
            if username:
                user = await sync_to_async(Users.objects.filter(username__iexact=username).first)()
                if user:
                    user_id = user.id
            if not user_id and name:
                user = await sync_to_async(Users.objects.filter(full_name__iexact=name).first)()
                if user:
                    user_id = user.id

        if not user_id:
            logger.warning("❌ Gagal temukan user ID.")
            return

        username = username or "unknown"

        # 💰 Extract nilai earnings per mata uang
        earnings = {}
        for currency in CURRENCIES:
            match = re.search(fr"{currency}:\s*([\d.,]+)", msg.text, re.IGNORECASE)
            if match:
                val = extract_decimal(match.group(1).replace(",", ""))
                if val:
                    earnings[currency.upper()] = val

        if not earnings:
            logger.warning("❌ Tidak ada nilai earnings ditemukan.")
            return


                # Ambil settings hanya yang berkaitan dengan CURRENCIES

        settings = await sync_to_async(list)(
            Settings.objects.filter(
                key__in=[f"rate_{c}" for c in CURRENCIES]
            )
        )

        rates = {}
        for s in settings:
            key = s.key.replace("rate_", "").upper()
            try:
                rates[key] = Decimal(str(s.value))
            except Exception as e:
                logger.warning(f"❌ Gagal parsing rate {s.key} = {s.value}: {e}")


        # 💵 Ambil hanya nominal USDT
        usdt_amount = earnings.get("USDT", Decimal("0.0"))
        if usdt_amount <= 0:
            logger.warning("❌ Tidak ada USDT dalam transaksi, bonus tidak diproses.")
            return

        total_usd = usdt_amount  # langsung anggap USDT = USD karena rate USDT = 1
        logger.info(f"💵 Total USD dari USDT saja: {total_usd}")


        total_usd = total_usd.quantize(Decimal("0.01"))
        if total_usd <= 0:
            logger.warning("❌ Total USD <= 0, tidak proses distribusi.")
            return

        # ✅ Konfirmasi ke user & admin
        await msg.bot.send_message(user_id, "✅ Transaksi kamu diproses & bonus referral didistribusikan.")
        await msg.bot.send_message(ADMIN_ID, f"📥 WD dari @{username} (ID: {user_id}) berhasil diproses.")

        # 🎯 Proses distribusi ke referrer chain (level 1-3)
        current_id = user_id
        for level in range(1, 4):
            user = await sync_to_async(Users.objects.filter(id=current_id).first)()
            if not user or not user.ref_by:
                break

            referrer_id = user.ref_by
            bonus = (total_usd * Decimal(str(BONUS_PERCENT[level]))).quantize(Decimal("0.01"))
            if bonus <= 0:
                current_id = referrer_id
                continue

            await sync_to_async(ReferralEarnings.objects.create)(
                user_id=referrer_id,
                from_user_id=user_id,
                amount=bonus,
                level=level,
                currency="USD",
                date=datetime.utcnow().isoformat(timespec="seconds") + "Z"
            )
            await sync_to_async(Users.objects.filter(id=referrer_id).update)(
                bonus_balance=models.F('bonus_balance') + bonus,
                total_bonus=models.F('total_bonus') + bonus
            )

            try:
                await msg.bot.send_message(
                    referrer_id,
                    f"💸 Kamu menerima bonus {bonus} USD dari referral @{username} (Level {level})."
                )
            except Exception as e:
                logger.warning(f"❌ Gagal kirim notifikasi ke referrer {referrer_id}: {e}")

            current_id = referrer_id

    except Exception as e:
        logger.error(f"❌ [CHANNEL ERROR] {e}")
