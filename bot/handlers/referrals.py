# Letak: bot/handlers/referrals.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import supabase

router = Router()

@router.message(Command("referrals"))
async def referral_list_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Ambil semua user yang direferensikan oleh user ini
    result = supabase.table("Users").select("username").eq("ref_by", user_id).execute()
    referrals = result.data

    if not referrals:
        return await msg.answer("Kamu belum mereferensikan siapa pun.")

    text = f"Kamu telah mereferensikan {len(referrals)} orang:\n"
    for user in referrals:
        mention = f"@{user['username']}" if user["username"] else "(tanpa username)"
        text += f"- {mention}\n"

    await msg.answer(text)
