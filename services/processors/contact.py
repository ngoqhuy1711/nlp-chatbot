"""
Contact Module - Xử lý thông tin liên hệ
"""

import os  # Dùng để ghép đường dẫn file
from typing import Any, Dict  # Kiểu trả về động

from config import DATA_DIR  # Đường dẫn thư mục data
from .cache import read_csv  # Hàm đọc CSV có cache


def get_contact_info() -> Dict[str, Any]:
    """
    Lấy thông tin liên hệ (hotline, email, fanpage)

    Returns:
        Dict chứa thông tin liên hệ
    """
    rows = read_csv(os.path.join(DATA_DIR, "contact_info.csv"))  # Đọc file liên hệ
    if rows:  # Nếu có dữ liệu
        contact = rows[0]  # File chỉ có một bản ghi, lấy dòng đầu tiên
        return {
            "university_name": contact.get("university_name", ""),  # Tên trường
            "address": contact.get("address", ""),  # Địa chỉ
            "email": contact.get("email", ""),  # Email liên hệ
            "phone": contact.get("phone", ""),  # Số điện thoại tổng đài
            "hotline": contact.get("hotline", ""),  # Hotline tuyển sinh
            "website": contact.get("website", ""),  # Website chính thức
            "fanpage": contact.get("fanpage", ""),  # Fanpage Facebook
            "note": contact.get("note", ""),  # Ghi chú thêm (ví dụ giờ làm việc)
        }
    return {}  # Không có dữ liệu → trả dict rỗng
