# Letak: bot/scripts/reset_team_auto.py

import os
import sys
from datetime import datetime, timedelta, timezone

# ✅ Tambahkan path ke root project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reffbot.settings")
django.setup()

from bot.models import Users, ReferralEarnings, Settings

def main():
    setting = Settings.objects.filter(key="team_reset_expire_months").first()
    if not setting:
        print("⚠️ Setting team_reset_expire_months belum diset.")
        return

    try:
        expire_months = int(setting.value)
    except ValueError:
        print("⛔ Format bulan tidak valid di Settings.")
        return

    now = datetime.now(timezone.utc)
    cutoff_days = expire_months * 30

    all_users = Users.objects.all()
    total_reset = 0

    for user in all_users:
        if not user.joined_at:
            continue

        try:
            joined_at = datetime.fromisoformat(user.joined_at).replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if user.team_reset_at:
            try:
                already_reset = datetime.fromisoformat(user.team_reset_at).replace(tzinfo=timezone.utc)
                if already_reset >= joined_at + timedelta(days=cutoff_days):
                    continue
            except Exception:
                pass

        if now < joined_at + timedelta(days=cutoff_days):
            continue

        ReferralEarnings.objects.filter(user=user).delete()
        user.ref_by = None
        user.team_reset_at = now.isoformat()
        user.save()
        total_reset += 1

    print(f"✅ Reset selesai. Total user yang di-reset: {total_reset}")

if __name__ == "__main__":
    main()
