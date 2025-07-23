# File: core/db/users.py

from core.config import supabase
from datetime import datetime

def get_user(telegram_id: int):
    res = supabase.table("Users").select("*").eq("id", telegram_id).execute()
    return res.data[0] if res.data else None

def create_user(telegram_id: int, fullname: str, username: str, ref_by: int | None = None):
    data = {
        "id": telegram_id,
        "fullname": fullname,
        "username": username,
        "ref_by": ref_by,
        "joined_at": datetime.utcnow().isoformat()
    }
    supabase.table("Users").insert(data).execute()
