"""
Majors Module - Xử lý thông tin ngành học
"""  # Docstring mô tả module chuyên về ngành

import os  # Dùng để ghép đường dẫn CSV
from typing import Any, Dict, List, Optional  # Type hints cho dữ liệu trả về

from config import DATA_DIR  # Thư mục chứa dữ liệu CSV
from .cache import read_csv  # Hàm đọc CSV có cache
from .utils import strip_diacritics  # Tiện ích bỏ dấu phục vụ so khớp mềm


def list_majors(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm thông tin ngành học (lọc theo tên/mã ngành nếu có)

    Args:
        query: Từ khóa tìm kiếm (tên ngành hoặc mã ngành)

    Returns:
        List các ngành học phù hợp
    """
    rows = read_csv(os.path.join(DATA_DIR, "majors.csv"))  # Đọc toàn bộ bảng majors

    # Lọc theo từ khóa nếu có
    if query:
        q = query.lower()  # Hạ chữ thường để so khớp không phân biệt case
        q_ascii = strip_diacritics(q)  # Tạo thêm phiên bản bỏ dấu cho tìm kiếm mềm
        rows = [
            r
            for r in rows
            if q in (r.get("major_name") or "").lower()
               or q in (r.get("major_code") or "").lower()
               or q_ascii in strip_diacritics((r.get("major_name") or "").lower())
        ]  # Giữ lại dòng có tên/mã chứa query (có hoặc không dấu)

    # Trả về format chuẩn
    return [
        {
            "major_code": r.get("major_code"),  # Mã ngành
            "major_name": r.get("major_name"),  # Tên ngành
            "description": r.get("description"),  # Mô tả tổng quan
            "additional_info": r.get("additional_info"),  # Thông tin bổ sung
        }
        for r in rows
    ]  # Chuẩn hóa format trả về
