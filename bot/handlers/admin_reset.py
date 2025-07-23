# File: bot/handlers/admin_reset.py

from aiogram import Router, types, F
from core.config import supabase, ADMIN_IDS

router = Router()

@router.message(F.text.startswith("/resetbonus"))
async def reset_bonus_handler(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses.")

    cmd = msg.text.strip().split()
    if len(cmd) != 2 or cmd[1] != "all":
        return await msg.answer("Gunakan format: /resetbonus all")

    # 1. Hapus semua isi dari tabel Referral_earnings
    supabase.table("Referral_earnings").delete().neq("user_id", 0).execute()

    # 2. Hapus semua data withdraw
    supabase.table("Withdraw_requests").delete().neq("user_id", 0).execute()

    # 3. Reset kolom saldo bonus jika memang ada
    try:
        supabase.table("Users").update({
            "bonus_balance": 0.0,
            "withdrawn_bonus": 0.0
        }).neq("id", 0).execute()
    except Exception:
        # Abaikan jika kolom bonus_balance atau withdrawn_bonus memang tidak ada
        pass

    await msg.answer("✅ Semua data bonus referral dan withdrawal berhasil di-reset.")
