"""
CEFR Module - Xử lý quy đổi điểm chứng chỉ tiếng Anh
"""

import os  # Dùng để ghép đường dẫn tới file CSV
from typing import Any, Dict, List, Optional  # Kiểu dữ liệu trả về đa dạng

from config import DATA_DIR  # Thư mục chứa dữ liệu
from .cache import read_csv  # Đọc CSV có cache


def get_cefr_conversion() -> List[Dict[str, Any]]:
    """
    Lấy bảng quy đổi điểm chứng chỉ tiếng Anh quốc tế (IELTS, TOEFL, etc.)

    Returns:
        List các dòng quy đổi điểm chứng chỉ
    """
    rows = read_csv(os.path.join(DATA_DIR, "cefr_conversion.csv"))  # Đọc toàn bộ bảng quy đổi
    return rows  # Trả nguyên dữ liệu để caller sử dụng


def convert_certificate_score(cert_type: str, score: float) -> Optional[float]:
    """
    Quy đổi điểm chứng chỉ sang điểm HUCE

    Args:
        cert_type: Loại chứng chỉ (IELTS, TOEFL iBT, TOEIC, TCF, DELF B2)
        score: Điểm chứng chỉ

    Returns:
        Điểm quy đổi HUCE, hoặc None nếu không tìm thấy
    """
    rows = get_cefr_conversion()  # Lấy bảng quy đổi

    for row in rows:  # Duyệt từng dòng quy đổi
        try:
            if cert_type.upper() == "IELTS":
                ielts_range = row.get("IELTS", "").strip()  # Mỗi dòng chứa ngưỡng IELTS
                if "-" in ielts_range:  # Dạng khoảng điểm
                    min_score, max_score = map(float, ielts_range.split("-"))
                    if min_score <= score <= max_score:  # Nếu điểm nằm trong khoảng
                        return float(row.get("Điểm quy đổi", 0))  # Trả điểm HUCE
                else:
                    if float(ielts_range) == score:  # Dạng giá trị đơn lẻ
                        return float(row.get("Điểm quy đổi", 0))

            elif cert_type.upper() == "TOEFL IBT" or cert_type.upper() == "TOEFL":
                toefl_range = row.get("TOEFL iBT", "").strip()  # Chuỗi mô tả ngưỡng TOEFL
                if "trở lên" in toefl_range:  # Dạng "X trở lên"
                    min_score = float(toefl_range.replace("trở lên", "").strip())
                    if score >= min_score:
                        return float(row.get("Điểm quy đổi", 0))
                elif "-" in toefl_range:  # Dạng khoảng
                    min_score, max_score = map(float, toefl_range.split("-"))
                    if min_score <= score <= max_score:
                        return float(row.get("Điểm quy đổi", 0))

        except (ValueError, AttributeError):  # Đề phòng giá trị không hợp lệ
            continue

    return None  # Không tìm thấy quy đổi phù hợp
