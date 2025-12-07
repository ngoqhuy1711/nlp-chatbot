"""Admissions Module - Xử lý thông tin xét tuyển."""  # Docstring mô tả module

import os  # Làm việc với đường dẫn file
from typing import Any, Dict, List, Optional  # Type hints cho dữ liệu đa dạng

from config import DATA_DIR  # Đường dẫn thư mục dữ liệu
from .cache import read_csv  # Hàm đọc CSV có cache để tránh I/O lặp


def list_admission_conditions(phuong_thuc: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lấy danh sách điều kiện xét tuyển chung."""  # Docstring mô tả
    rows = read_csv(os.path.join(DATA_DIR, "admission_conditions.csv"))  # Đọc toàn bộ file điều kiện
    return [
        {"condition_name": r.get("condition_name", "").strip(),  # Tên điều kiện
         "description": r.get("description", "").strip(),  # Nội dung mô tả
         "is_required": r.get("is_required", "").strip()}  # Đánh dấu bắt buộc hay không
        for r in rows if r.get("condition_name", "").strip() and r.get("description", "").strip()
        # Bỏ các dòng thiếu dữ liệu chính
    ]


def list_admission_quota(major: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tìm kiếm chỉ tiêu tuyển sinh."""  # Docstring mô tả
    targets = get_admission_targets(
        ma_nganh=major if major and len(major) == 7 else None)  # Nếu nhập mã ngành đủ 7 ký tự thì lọc theo mã

    if major and len(major) != 7:  # Người dùng nhập tên ngành
        from .utils import strip_diacritics  # Import tại chỗ để tránh vòng lặp phụ thuộc
        mq = strip_diacritics(major.lower())  # Chuẩn hóa để so khớp không dấu
        targets = [t for t in targets if mq in strip_diacritics(t.get("major_name", "").lower())
                   or mq in strip_diacritics(t.get("program_name", "").lower())]  # Lọc theo tên ngành/chương trình

    major_quotas = {}  # Map (mã ngành, tên ngành) -> dữ liệu tổng hợp
    for t in targets:  # Duyệt từng bản ghi chỉ tiêu
        key = (t.get("major_code", ""), t.get("major_name", ""))  # Khóa duy nhất cho ngành
        if key not in major_quotas:  # Nếu ngành chưa có trong map
            major_quotas[key] = {"major_code": key[0], "major_name": key[1], "nam": year or "2025", "chi_tieu": 0,
                                 "chi_tiet": []}  # Khởi tạo cấu trúc dữ liệu
        try:
            chi_tieu = int(t.get("quota", "0"))  # Chuyển quota sang số nguyên
        except ValueError:
            chi_tieu = 0  # Nếu dữ liệu hỏng thì coi như 0
        major_quotas[key]["chi_tiet"].append({
            "admission_method": t.get("admission_method", ""),  # Mã phương thức
            "subject_combination": t.get("subject_combination", ""),  # Tổ hợp môn
            "chi_tieu": chi_tieu  # Chỉ tiêu của dòng hiện tại
        })

    results = []  # Danh sách kết quả cuối
    for key, data in major_quotas.items():  # Tổng hợp mỗi ngành thành một record
        ma_xt_quotas = {}  # Map mã xét tuyển → chỉ tiêu
        for t in targets:  # Duyệt toàn bộ chỉ tiêu để gom theo mã xét tuyển
            if t.get("major_code") == data["major_code"]:  # Gom các dòng cùng mã ngành
                ma_xt = t.get("admission_code", "")  # Mã xét tuyển cụ thể
                try:
                    chi_tieu = int(t.get("quota", "0"))  # Chuyển chỉ tiêu sang int
                    if ma_xt and ma_xt not in ma_xt_quotas:  # Chỉ ghi nhận mỗi mã một lần
                        ma_xt_quotas[ma_xt] = chi_tieu  # Lưu giá trị
                except ValueError:
                    continue  # Bỏ qua dòng lỗi
        data["chi_tieu"] = sum(ma_xt_quotas.values())  # Tổng hợp chỉ tiêu
        results.append(data)  # Thêm bản ghi vào danh sách trả về
    return results  # Trả kết quả cuối


def list_admission_methods_general() -> List[Dict[str, Any]]:
    """Lấy danh sách tổng quát các phương thức xét tuyển."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "admission_methods.csv"))  # Đọc toàn bộ bảng phương thức
    return [
        {
            "method_code": r.get("method_code"),  # Mã phương thức
            "abbreviation": r.get("abbreviation"),  # Viết tắt (nếu có)
            "method_name": r.get("method_name"),  # Tên đầy đủ
            "description": r.get("description"),  # Mô tả chi tiết
            "requirements": r.get("requirements"),  # Điều kiện kèm theo
        }
        for r in rows
    ]  # Trả dữ liệu nguyên dạng để UI tự trình bày


def list_admission_methods(major: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tìm kiếm phương thức xét tuyển theo ngành."""  # Docstring
    targets = get_admission_targets(ma_nganh=major if major and len(major) == 7 else None)  # Lọc theo mã ngành nếu có

    if major and len(major) != 7:  # Khi người dùng nhập tên ngành
        from .utils import strip_diacritics  # Import helper bỏ dấu
        mq = strip_diacritics(major.lower())  # Tạo query bỏ dấu
        targets = [t for t in targets if mq in strip_diacritics(t.get("major_name", "").lower())
                   or mq in strip_diacritics(t.get("program_name", "").lower())]  # Lọc theo tên ngành/chương trình

    method_mapping: Dict[str, List[Dict[str, str]]] = {}  # Map mã phương thức → danh sách alias
    for m in list_admission_methods_general():  # Duyệt bảng phương thức tổng quát
        code = str(m.get("method_code", ""))  # Lấy mã (có thể là số hoặc chuỗi)
        if code:
            method_mapping.setdefault(code, []).append({
                "method_name": m.get("method_name", ""),  # Tên phương thức
                "abbreviation": m.get("abbreviation", ""),  # Viết tắt (nếu có)
                "description": m.get("description", ""),  # Mô tả
            })  # Gom tất cả alias cùng mã

    methods_map = {}  # Map (mã ngành, phương thức) → thông tin hiển thị
    for t in targets:  # Duyệt từng bản ghi chỉ tiêu
        key = (t.get("major_code", ""), t.get("admission_method", ""))  # Ghép thành khóa duy nhất
        if key not in methods_map:  # Nếu chưa khởi tạo entry
            ml = method_mapping.get(key[1], [])  # Lấy danh sách alias của phương thức
            if len(ml) > 1:  # Khi có nhiều biến thể tên
                method_name = " / ".join(
                    [f"{m['abbreviation']} - {m['method_name']}" for m in ml if
                     m['abbreviation'] and m['method_name']])  # Hiển thị dạng đầy đủ
                abbreviation = " / ".join([m['abbreviation'] for m in ml if m['abbreviation']])  # Gom viết tắt
                method_desc = " / ".join([m['description'] for m in ml if m['description']])  # Gom mô tả
            elif len(ml) == 1:  # Chỉ có một alias
                method_name, abbreviation, method_desc = ml[0]["method_name"], ml[0]["abbreviation"], ml[0][
                    "description"]  # Dùng trực tiếp
            else:
                method_name, abbreviation, method_desc = "", "", ""  # Không có mô tả
            methods_map[key] = {
                "major_code": key[0],  # Mã ngành
                "major_name": t.get("major_name", ""),  # Tên ngành
                "admission_method": key[1],  # Mã phương thức
                "method_code": key[1],  # Trùng với admission_method
                "method_name": method_name,  # Tên phương thức hiển thị
                "abbreviation": abbreviation,  # Viết tắt hiển thị
                "description": method_desc,  # Mô tả
                "subject_combination": [],  # Danh sách tổ hợp môn
            }
        to_hop = t.get("subject_combination", "").strip()  # Lấy chuỗi tổ hợp ở bản ghi hiện tại
        if to_hop and to_hop not in methods_map[key]["subject_combination"]:  # Tránh trùng
            methods_map[key]["subject_combination"].append(to_hop)  # Bổ sung tổ hợp vào danh sách

    return [dict(d, subject_combination=", ".join(d["subject_combination"])) for d in
            methods_map.values()]  # Chuyển list tổ hợp sang chuỗi


def list_admissions_schedule(phuong_thuc: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tìm kiếm lịch trình xét tuyển."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "admissions_schedule.csv"))  # Đọc bảng lịch tuyển sinh

    method_mapping = {}  # Map nhiều dạng viết → viết tắt chuẩn
    for m in list_admission_methods_general():  # Duyệt từng phương thức chuẩn
        code, abbr = m.get("method_code", ""), m.get("abbreviation", "").strip().upper()  # Lấy mã và viết tắt
        name = m.get("method_name", "").lower()  # Lấy tên để tìm keyword
        if abbr:
            method_mapping[abbr.lower()] = abbr  # Cho phép match lowercase
            method_mapping[abbr] = abbr  # Và dạng uppercase
        if code and code not in method_mapping:
            method_mapping[code] = abbr  # Map mã → viết tắt
        for kw, target in [("học bạ", abbr), ("hoc ba", abbr), ("tuyển thẳng", abbr), ("tuyen thang", abbr),
                           ("chứng chỉ quốc tế", abbr), ("chung chi quoc te", abbr), ("ccqt", abbr),
                           ("v-sat", abbr), ("vsat", abbr), ("tsa", abbr), ("spt", abbr)]:  # Các keyword phổ biến
            if kw in name and kw not in method_mapping:
                method_mapping[kw] = abbr  # Map keyword → viết tắt
        if "thpt" in name and "năng khiếu" not in name and "thpt" not in method_mapping:
            method_mapping["thpt"] = abbr  # Riêng THPT cần loại trừ năng khiếu

    search_methods = set()  # Tập các viết tắt cần lọc
    if phuong_thuc:
        pl, pu = phuong_thuc.lower().strip(), phuong_thuc.upper().strip()  # Tạo hai dạng chữ
        if pl in method_mapping:
            search_methods.add(method_mapping[pl].upper())  # Dùng viết tắt chuẩn
        elif pu in method_mapping:
            search_methods.add(method_mapping[pu].upper())
        else:
            search_methods.add(pu)  # Không map được thì dùng nguyên chuỗi

    results = []  # Danh sách lịch trả về
    for r in rows:  # Duyệt từng dòng lịch
        event_name = (r.get("event_name") or "").strip()  # Lấy tên mốc thời gian
        if not event_name:
            continue  # Bỏ qua dòng thiếu tên
        pt_raw = (r.get("admission_method") or "").strip()  # Chuỗi mô tả phương thức
        if phuong_thuc:  # Nếu người dùng yêu cầu lọc
            if pt_raw.lower() in ["tất cả", "tat ca"]:  # Dòng áp dụng cho mọi phương thức
                pass  # Giữ lại
            elif search_methods:  # Có map cụ thể
                methods_in_row = [m.strip().upper() for m in pt_raw.split(",") if m.strip()]  # Chuẩn hóa danh sách
                if not any(m in search_methods for m in methods_in_row):  # Không trùng phương thức cần tìm
                    continue  # Bỏ dòng
            else:  # Không map được -> so khớp trực tiếp
                if phuong_thuc.lower() not in pt_raw.lower():
                    continue
        results.append({"event_name": event_name,  # Tên sự kiện
                        "timeline": r.get("timeline") or "",  # Thời gian thực hiện
                        "admission_method": pt_raw,  # Phương thức áp dụng
                        "note": r.get("note") or ""})  # Ghi chú thêm
    return results  # Trả lịch sau khi lọc


def get_admission_targets(ma_nganh: Optional[str] = None, phuong_thuc: Optional[str] = None,
                          to_hop: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lấy chỉ tiêu tuyển sinh theo ngành, phương thức, tổ hợp môn."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "admission_targets.csv"))  # Đọc bảng chỉ tiêu
    results = []  # Danh sách trả về
    for row in rows:  # Duyệt từng bản ghi
        if ma_nganh and row.get("major_code", "").strip() != ma_nganh.strip():
            continue  # Lọc theo mã ngành
        if phuong_thuc and row.get("admission_method", "").strip() != phuong_thuc.strip():
            continue  # Lọc theo phương thức
        if to_hop:
            to_hop_list = [x.strip() for x in
                           row.get("subject_combination", "").split(",")]  # Chuẩn hóa danh sách tổ hợp
            if to_hop.strip() not in to_hop_list:
                continue  # Lọc theo tổ hợp
        results.append(row)  # Bản ghi đạt tiêu chí
    return results  # Trả danh sách đã lọc


def get_combination_codes(ky_thi: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lấy danh sách tổ hợp môn thi."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))  # Đọc bảng tổ hợp
    if ky_thi:
        return [r for r in rows if
                ky_thi.strip() in [x.strip() for x in r.get("exam_type", "").split(",")]]  # Lọc theo kỳ thi
    return rows  # Trả toàn bộ khi không lọc


def get_combination_by_code(combo_code: str) -> List[Dict[str, Any]]:
    """Tìm thông tin chi tiết tổ hợp môn theo mã."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))  # Đọc bảng tổ hợp
    code_upper = combo_code.strip().upper()  # Chuẩn hóa mã cần tìm
    return [r for r in rows if
            (r.get("combination_code") or "").strip().upper() == code_upper]  # Tìm các dòng có mã khớp


def search_combinations(query: str) -> List[Dict[str, Any]]:
    """Tìm kiếm tổ hợp môn theo mã hoặc tên môn."""  # Docstring
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))  # Đọc bảng tổ hợp
    qu, ql = query.strip().upper(), query.strip().lower()  # Chuẩn hóa query
    return [r for r in rows if qu in (r.get("combination_code") or "").strip().upper()
            or ql in (r.get("subject_names") or "").lower()]  # Kiểm tra theo mã hoặc tên môn
