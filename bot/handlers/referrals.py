# Letak: bot/handlers/referrals.py

from aiogram import Router, types
from aiogram.filters import Command
from bot.models import Users  # model ORM
from asgiref.sync import sync_to_async  # untuk jalankan query ORM di async handler

router = Router()

@router.message(Command("referrals"))
async def referral_list_handler(msg: types.Message):
    user_id = msg.from_user.id

    # Ambil semua user yang direferensikan oleh user ini
    referrals = await sync_to_async(list)(
        Users.objects.filter(ref_by=user_id).only("username")
    )

    if not referrals:
        return await msg.answer("Kamu belum mereferensikan siapa pun.")

    text = f"Kamu telah mereferensikan {len(referrals)} orang:\n"
    for user in referrals:
        mention = f"@{user.username}" if user.username else "(tanpa username)"
        text += f"- {mention}\n"

    await msg.answer(text)
