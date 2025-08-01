# 📍 bot/handlers/admin_botstatus.py

from aiogram import Router, types
from aiogram.filters import Command
from core.config import ADMIN_IDS
import json
import os

router = Router()
BOT_STATUS_PATH = "config/bot_status.json"

# ✅ Fungsi dipakai bersama
def is_bot_active() -> bool:
    if not os.path.exists(BOT_STATUS_PATH):
        return True  # Default aktif
    with open(BOT_STATUS_PATH, "r") as f:
        data = json.load(f)
    return data.get("is_active", True)

def set_bot_status(active: bool):
    with open(BOT_STATUS_PATH, "w") as f:
        json.dump({"is_active": active}, f)

# ✅ Command admin untuk atur status bot
@router.message(Command("botstatus"))
async def toggle_bot_status(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Kamu tidak punya akses untuk fitur ini.")
    
    args = msg.text.strip().split()
    if len(args) != 2 or args[1] not in ("on", "off"):
        return await msg.answer("⚠️ Usage: /botstatus <on|off>")

    status = args[1] == "on"
    set_bot_status(status)
    await msg.answer(f"✅ Bot status set to: {'ON' if status else 'OFF'}")
