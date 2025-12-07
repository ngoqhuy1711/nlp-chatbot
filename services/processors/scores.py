"""
Scores Module - Xử lý điểm chuẩn, điểm sàn
"""  # Docstring mô tả module chuyên về điểm số

import os  # Làm việc với đường dẫn file
from typing import Any, Dict, List, Optional  # Type hints cấu trúc linh hoạt

from config import DATA_DIR  # Đường dẫn thư mục data
from .cache import read_csv  # Hàm đọc CSV có cache
from .utils import strip_diacritics, canonicalize_vi_ascii, clean_program_name  # Tiện ích xử lý chuỗi


def find_standard_score(
        major: Optional[str] = None, year: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm điểm chuẩn (theo ngành và/hoặc năm học)

    Args:
        major: Tên hoặc mã ngành
        year: Năm học (vd: "2020", "2021", "2022", "2023", "2024", "2025")

    Returns:
        List điểm chuẩn theo ngành và năm
    """
    rows = read_csv(os.path.join(DATA_DIR, "admission_scores.csv"))  # Đọc toàn bộ bảng điểm chuẩn từ CSV
    if not rows:  # Nếu file rỗng hoặc đọc thất bại
        return []  # Dừng sớm và trả danh sách trống

    # Lấy danh sách các cột năm từ header
    year_columns = []  # Danh sách lưu các cột thể hiện năm tuyển sinh
    if rows:  # Khi có ít nhất một dòng dữ liệu
        first_row_keys = list(rows[0].keys())  # Lấy tên cột từ dòng đầu tiên
        for key in first_row_keys:  # Duyệt từng cột
            if key.isdigit() and len(key) == 4:  # Chỉ giữ cột có định dạng số 4 chữ số
                year_num = int(key)  # Ép sang int để so sánh
                if 2020 <= year_num <= 2025:  # Giới hạn khoảng năm được hỗ trợ
                    year_columns.append(key)  # Thêm cột năm hợp lệ
        year_columns.sort()  # Sắp xếp cột năm để xử lý theo thứ tự

    results: List[Dict[str, Any]] = []  # Chuẩn bị list kết quả trả về

    for r in rows:  # Duyệt từng bản ghi điểm chuẩn
        program_name = (r.get("program_name") or "").strip()  # Lấy tên chương trình/ngành và loại bỏ khoảng trắng
        if not program_name:  # Nếu dòng không có tên
            continue  # Bỏ qua vì không thể kiểm tra

        program_name_cleaned = clean_program_name(program_name)  # Chuẩn hóa để loại bỏ dư thừa/viết tắt
        program_name_lower = program_name_cleaned.lower()  # Hạ chữ thường phục vụ so khớp
        program_name_ascii = strip_diacritics(program_name_lower)  # Bỏ dấu tiếng Việt
        program_name_ascii = canonicalize_vi_ascii(program_name_ascii)  # Chuẩn hóa thêm các ký tự đặc biệt

        # Lọc theo ngành nếu có
        if major:  # Nếu người dùng cung cấp từ khóa ngành
            mq = major.lower()  # Dạng lowercase để so khớp trực tiếp
            mq_ascii = strip_diacritics(mq)  # Bỏ dấu khỏi query
            mq_ascii = canonicalize_vi_ascii(mq_ascii)  # Chuẩn hóa alias
            if (mq not in program_name_lower) and (mq_ascii not in program_name_ascii):  # Không match ở cả hai dạng
                continue  # Bỏ qua vì không liên quan tới ngành cần tìm

        # Lấy điểm cho từng năm
        for year_key in year_columns:  # Duyệt từng cột năm
            if year and year != year_key:  # Nếu người dùng chỉ định năm cụ thể
                continue  # Bỏ qua các năm khác

            score_value = r.get(year_key, "")  # Lấy giá trị điểm tại cột năm đó
            if not score_value:
                continue  # Không có điểm → bỏ qua

            score_str = str(score_value).strip()  # Chuẩn hóa thành chuỗi gọn
            score_lower = score_str.lower()  # Tạo bản lowercase để kiểm tra chuỗi đặc biệt

            # Bỏ qua các giá trị đặc biệt
            if score_lower in ["chưa tuyển", "chua tuyen", ""]:  # Giá trị không biểu diễn điểm số
                continue  # Tránh đưa vào kết quả
            if "tuyển chung" in score_lower or "tuyen chung" in score_lower:  # Mô tả chung chung
                continue
            if "chưa" in score_lower and "tuyển" in score_lower:  # Câu mô tả thiếu dữ liệu
                continue

            # Thử chuyển đổi sang số
            try:
                score_str_clean = score_str.replace(",", ".")  # Chuẩn hóa dấu thập phân
                score_float = float(score_str_clean)  # Ép sang float

                results.append(
                    {
                        "program_name": program_name_cleaned,  # Lưu tên chương trình chuẩn hóa
                        "nam": year_key,  # Lưu năm tương ứng
                        "diem_chuan": score_float,  # Điểm chuẩn dạng số
                        "subject_combination": r.get("subject_combination", ""),  # Tổ hợp môn liên quan
                    }
                )  # Ghi lại bản ghi hợp lệ
            except (ValueError, TypeError):  # Không chuyển được sang số
                continue  # Bỏ qua bản ghi lỗi

    return results  # Trả danh sách điểm chuẩn đã lọc


def suggest_majors_by_score(request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Gợi ý ngành học dựa trên điểm số hoặc chứng chỉ

    Args:
        request_data: Dict chứa điểm số và chứng chỉ

    Returns:
        List các ngành phù hợp với điểm số
    """
    diem_thpt = request_data.get("diem_thpt")  # Điểm tổng hợp thi THPT 3 môn
    diem_tsa = request_data.get("diem_tsa")  # Điểm kỳ thi TSA
    diem_dgnl = request_data.get("diem_dgnl")  # Điểm đánh giá năng lực
    chung_chi = request_data.get("chung_chi")  # Chứng chỉ ưu tiên (đặt placeholder, chưa dùng)
    nam = request_data.get("nam", "2025")  # Năm tuyển sinh cần so sánh, default 2025

    suggestions = []  # Danh sách gợi ý tạm thời

    # Lấy điểm chuẩn để so sánh
    standard_scores = find_standard_score(year=nam)  # Chỉ đọc dữ liệu của năm mong muốn

    for score_data in standard_scores:  # So từng bản ghi điểm chuẩn
        diem_chuan = score_data.get("diem_chuan")  # Lấy điểm chuẩn
        if not diem_chuan:
            continue  # Bỏ qua nếu thiếu dữ liệu

        try:
            diem_chuan_float = float(str(diem_chuan).replace(",", "."))  # Ép sang float để so sánh
        except (ValueError, TypeError):
            continue  # Không chuyển được thì bỏ

        # So sánh điểm THPT
        if diem_thpt and diem_thpt >= diem_chuan_float:  # Điểm THPT đủ cao
            suggestions.append(
                {
                    "program_name": score_data.get("program_name"),  # Ghi tên chương trình
                    "diem_chuan": diem_chuan,  # Lưu lại điểm chuẩn để hiển thị
                    "diem_thpt": diem_thpt,  # Điểm người dùng cung cấp
                    "subject_combination": score_data.get("subject_combination"),  # Tổ hợp áp dụng
                    "nam": score_data.get("nam"),  # Năm dữ liệu
                    "match_type": "thpt",  # Ghi chú kiểu so khớp
                    "confidence": min(
                        1.0, (diem_thpt - diem_chuan_float) / diem_chuan_float + 1.0
                        # Confidence dựa trên khoảng cách điểm
                    ),
                }
            )

        # So sánh điểm TSA
        if diem_tsa and diem_tsa >= diem_chuan_float:  # Điểm TSA đáp ứng
            suggestions.append(
                {
                    "program_name": score_data.get("program_name"),  # Tên chương trình
                    "diem_chuan": diem_chuan,  # Điểm chuẩn tham chiếu
                    "diem_tsa": diem_tsa,  # Điểm TSA người dùng
                    "subject_combination": score_data.get("subject_combination"),  # Tổ hợp đi kèm
                    "nam": score_data.get("nam"),  # Năm dữ liệu
                    "match_type": "tsa",  # Kiểu so khớp
                    "confidence": min(
                        1.0, (diem_tsa - diem_chuan_float) / diem_chuan_float + 1.0  # Confidence tương tự
                    ),
                }
            )

        # So sánh điểm ĐGNL
        if diem_dgnl and diem_dgnl >= diem_chuan_float:  # Điểm ĐGNL đủ cao
            suggestions.append(
                {
                    "program_name": score_data.get("program_name"),  # Lưu chương trình
                    "diem_chuan": diem_chuan,  # Điểm chuẩn
                    "diem_dgnl": diem_dgnl,  # Điểm ĐGNL đầu vào
                    "subject_combination": score_data.get("subject_combination"),  # Tổ hợp tham chiếu
                    "nam": score_data.get("nam"),  # Năm dữ liệu
                    "match_type": "dgnl",  # Loại khớp
                    "confidence": min(
                        1.0, (diem_dgnl - diem_chuan_float) / diem_chuan_float + 1.0  # Tính confidence
                    ),
                }
            )

    # Sắp xếp theo confidence giảm dần
    suggestions.sort(key=lambda x: x.get("confidence", 0), reverse=True)  # Sắp xếp giảm dần theo độ tin cậy

    # Loại bỏ trùng lặp (giữ ngành có confidence cao nhất)
    seen_programs = set()  # Theo dõi các chương trình đã thêm
    unique_suggestions = []  # Danh sách kết quả cuối cùng
    for suggestion in suggestions:  # Lọc trùng
        program_name = suggestion.get("program_name")  # Lấy tên chương trình
        if program_name and program_name not in seen_programs:  # Chỉ thêm nếu chưa có
            seen_programs.add(program_name)  # Đánh dấu đã thấy
            unique_suggestions.append(suggestion)  # Ghi vào danh sách cuối

    return unique_suggestions[:20]  # Trả về tối đa 20 gợi ý tốt nhất
