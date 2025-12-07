import os
from typing import Any, Dict

from config import DATA_DIR
from .cache import read_csv


def get_contact_info() -> Dict[str, Any]:
    rows = read_csv(os.path.join(DATA_DIR, "contact_info.csv"))
    if rows:
        contact = rows[0]
        return {
            "university_name": contact.get("university_name", ""),
            "address": contact.get("address", ""),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "hotline": contact.get("hotline", ""),
            "website": contact.get("website", ""),
            "fanpage": contact.get("fanpage", ""),
            "note": contact.get("note", ""),
        }
    return {}
