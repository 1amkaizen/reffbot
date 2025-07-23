# File: core/config.py

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME")

# Admin ID bisa lebih dari 1, pisahkan dengan koma di .env
ADMIN_ID = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_ID.split(",") if x.strip().isdigit()]

# Default rate USD → IDR jika tidak diset di Settings
USD_RATE = float(os.getenv("USD_RATE", 16000))
