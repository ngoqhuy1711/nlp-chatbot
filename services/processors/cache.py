"""CSV Cache - Cache CSV files theo modification time."""

import csv  # Đọc file CSV thành dict
import os  # Kiểm tra file và lấy thời gian sửa đổi
from typing import Any, Dict, List, Tuple  # Kiểu dữ liệu

_CSV_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}  # Map path -> (mtime, dữ liệu)


def _read_csv_cached(path: str) -> List[Dict[str, Any]]:
    """Đọc CSV với cache. Auto reload khi file thay đổi."""
    if not os.path.isfile(path):  # File không tồn tại
        return []  # Trả danh sách rỗng

    mtime = os.path.getmtime(path)  # Lấy thời gian sửa đổi mới nhất
    cached = _CSV_CACHE.get(path)  # Kiểm tra cache

    if cached and cached[0] == mtime:  # Cache còn hợp lệ (mtime không đổi)
        return cached[1]  # Trả dữ liệu cache

    with open(path, newline="", encoding="utf-8") as f:  # Mở file để đọc
        rows = list(csv.DictReader(f))  # Đọc toàn bộ nội dung thành list dict

    _CSV_CACHE[path] = (mtime, rows)  # Cập nhật cache với mtime mới
    return rows  # Trả dữ liệu vừa đọc


def read_csv(path: str) -> List[Dict[str, Any]]:
    """Public API để đọc CSV với cache."""
    return _read_csv_cached(path)  # Bao hàm logic cache


def clear_cache():
    """Xóa toàn bộ cache."""
    global _CSV_CACHE  # Khai báo để ghi vào biến module
    _CSV_CACHE.clear()  # Xóa hết các entry
