"""
Academic Module - Xử lý học phí và học bổng
"""

import os  # Dùng để ghép đường dẫn tới file CSV
from typing import Any, Dict, List, Optional  # Kiểu dữ liệu trả về linh hoạt

from config import DATA_DIR  # Thư mục chứa toàn bộ dữ liệu CSV
from .cache import read_csv  # Hàm đọc CSV có cơ chế cache


def list_tuition(
        year: Optional[str] = None, program_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm thông tin học phí (lọc theo năm và/hoặc chương trình)

    Args:
        year: Năm học
        program_query: Chương trình đào tạo

    Returns:
        List học phí theo năm và chương trình
    """
    rows = read_csv(os.path.join(DATA_DIR, "tuition.csv"))  # Đọc toàn bộ bảng học phí
    results: List[Dict[str, Any]] = []  # Danh sách sẽ trả về

    for r in rows:  # Duyệt từng dòng dữ liệu
        nh = (r.get("academic_year") or "").strip()  # Chuẩn hóa năm học
        ct = (r.get("program_type") or "").strip()  # Chuẩn hóa loại chương trình

        # Lọc theo năm nếu có
        if year and year not in nh:  # Khi người dùng truyền năm nhưng dòng không khớp
            continue  # Bỏ qua dòng này

        # Lọc theo chương trình nếu có
        if program_query and program_query.lower() not in ct.lower():  # So sánh không phân biệt hoa thường
            continue  # Không khớp → bỏ qua

        results.append(
            {
                "academic_year": nh,  # Năm học áp dụng
                "program_type": ct,  # Loại chương trình
                "tuition_fee": r.get("tuition_fee"),  # Mức học phí
                "unit": r.get("unit"),  # Đơn vị tính (đồng/năm, đồng/tín chỉ…)
                "note": r.get("note"),  # Ghi chú bổ sung
            }
        )
    return results  # Trả về danh sách học phí đã lọc


def list_scholarships(name_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm thông tin học bổng (lọc theo tên học bổng nếu có)

    Args:
        name_query: Tên học bổng cần tìm

    Returns:
        List học bổng phù hợp
    """
    rows = read_csv(os.path.join(DATA_DIR, "scholarships.csv"))  # Đọc bảng học bổng

    # Lọc theo tên học bổng nếu có
    if name_query:  # Khi người dùng truyền từ khóa
        q = name_query.lower()  # Chuẩn hóa query
        rows = [r for r in rows if q in (r.get("scholarship_name") or "").lower()]  # Giữ những dòng chứa từ khóa

    return [
        {
            "scholarship_name": r.get("scholarship_name"),  # Tên học bổng
            "value": r.get("value"),  # Giá trị/học bổng
            "quantity": r.get("quantity"),  # Số lượng suất
            "academic_year": r.get("academic_year"),  # Năm áp dụng
            "requirements": r.get("requirements"),  # Điều kiện xét
            "note": r.get("note"),  # Ghi chú thêm (ví dụ hồ sơ cần nộp)
        }
        for r in rows
    ]  # Trả danh sách học bổng (đã lọc nếu có query)
