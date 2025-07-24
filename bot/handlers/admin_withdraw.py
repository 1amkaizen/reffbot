# Letak: bot/handlers/admin_withdraw.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.config import ADMIN_IDS
from bot.models import WithdrawRequests
from datetime import datetime
from asgiref.sync import sync_to_async  # ⬅️ WAJIB untuk ORM

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("listwithdraw"))
async def list_withdraw_handler(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("⛔ Akses ditolak.")

    records = await sync_to_async(lambda: list(WithdrawRequests.objects.filter(status="pending")))()

    if not records:
        return await msg.answer("Tidak ada permintaan withdraw yang pending.")

    for item in records:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Tandai Selesai",
            callback_data=f"approve_withdraw:{item.id}"
        )

        await msg.answer(
            f"📤 Permintaan Withdraw\n\n"
            f"👤 User ID: <code>{item.user_id}</code>\n"
            f"💰 Jumlah: <b>{item.amount} {item.currency}</b>\n"
            f"🆔 ID Withdraw: {item.id}",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("approve_withdraw:"))
async def approve_withdraw_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Akses ditolak.", show_alert=True)

    withdraw_id = int(callback.data.split(":")[1])

    try:
        wd = await sync_to_async(WithdrawRequests.objects.get)(id=withdraw_id)
    except WithdrawRequests.DoesNotExist:
        return await callback.message.edit_text("Data withdraw tidak ditemukan.")

    wd.status = "approved"
    wd.approved_at = datetime.utcnow()
    await sync_to_async(wd.save)()  # ⬅️ simpan perubahan via sync_to_async

    await callback.bot.send_message(
        chat_id=wd.user_id,
        text=f"✅ Permintaan withdraw {wd.amount} {wd.currency} kamu telah berhasil diproses."
    )

    await callback.message.edit_text("✅ Withdraw ditandai berhasil dan user sudah diberi notifikasi.")
