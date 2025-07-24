# File: polling_runner.py

import os
import django
import asyncio

# 1. Set Django settings dan jalankan setup dulu
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reffbot.settings")
django.setup()

# 2. Baru import setelah setup selesai
from bot.bot import run_bot

if __name__ == "__main__":
    asyncio.run(run_bot())
