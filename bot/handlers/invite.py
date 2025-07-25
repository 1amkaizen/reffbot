# Letak: bot/handlers/invite.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import BOT_USERNAME
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("invite"))
async def link_referral_handler(msg: types.Message):
    user_id = msg.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    text = (
        "Recommend you a good way to make money at home, you can easily earn $100 a day.\n"
        f"{referral_link}\n\n"
        "You can click the button below to send this invitation link to your friends, "
        "or simply copy the text above and share it manually.\n"
        "------------------\n"
        "Referral Commission Structure:\n"
        "Level 1: 5.0%\n"
        "Level 2: 3.0%\n"
        "Level 3: 2.0%"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Kirim ke Teman", switch_inline_query=referral_link)]
    ])

    await msg.answer(text, reply_markup=keyboard)
