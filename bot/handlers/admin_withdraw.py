# Letak: bot/handlers/admin_withdraw.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.config import supabase, ADMIN_IDS
from datetime import datetime

router = Router()

# Cek apakah user adalah admin
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS  # ✅ FIXED: cek apakah user_id termasuk dalam ADMIN_IDS

@router.message(Command("listwithdraw"))
async def list_withdraw_handler(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("⛔ Akses ditolak.")

    data = supabase.table("Withdraw_requests").select("*").eq("status", "pending").execute()
    records = data.data

    if not records:
        return await msg.answer("Tidak ada permintaan withdraw yang pending.")

    for item in records:
        user_id = item["user_id"]
        amount = item["amount"]
        currency = item["currency"]
        withdraw_id = item["id"]

        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Tandai Selesai",
            callback_data=f"approve_withdraw:{withdraw_id}"
        )

        await msg.answer(
            f"📤 Permintaan Withdraw\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"💰 Jumlah: <b>{amount} {currency}</b>\n"
            f"🆔 ID Withdraw: {withdraw_id}",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("approve_withdraw:"))
async def approve_withdraw_callback(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Akses ditolak.", show_alert=True)

    withdraw_id = int(callback.data.split(":")[1])

    # Ambil data withdraw
    result = supabase.table("Withdraw_requests").select("*").eq("id", withdraw_id).single().execute()
    data = result.data

    if not data:
        return await callback.message.edit_text("Data withdraw tidak ditemukan.")

    # Update status jadi approved
    supabase.table("Withdraw_requests").update({
        "status": "approved",
        "approved_at": datetime.utcnow().isoformat()
    }).eq("id", withdraw_id).execute()

    user_id = data["user_id"]
    amount = data["amount"]
    currency = data["currency"]

    # Kirim pesan ke user bahwa WD sukses
    await callback.bot.send_message(
        chat_id=user_id,
        text=f"✅ Permintaan withdraw {amount} {currency} kamu telah berhasil diproses."
    )

    await callback.message.edit_text("✅ Withdraw ditandai berhasil dan user sudah diberi notifikasi.")
