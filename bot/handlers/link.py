# Letak: bot/handlers/link_referral.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import BOT_USERNAME
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("linkreferral"))
async def link_referral_handler(msg: types.Message):
    user_id = msg.from_user.id
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    text = (
        "Recommend you a good way to make money at home, you can easily earn $100 a day.\n"
        f"{referral_link}"
    )

    info_text = (
        "\n\nYou can click the button directly to send the invitation link to your friends, "
        "or you can copy the text above the button and send it to your friends.\n"
        "------------------\n"
        "The commission ratio corresponding to different levels of sub-users\n"
        "Level1: 5.0%\n"
        "Level2: 3.0%\n"
        "Level3: 2.0%"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Kirim ke Teman", switch_inline_query=referral_link)]
    ])

    await msg.answer(text, reply_markup=keyboard)
    await msg.answer(info_text)
