"""Utility Functions - Text normalization và formatting."""  # Module mô tả chức năng tiện ích

import os  # Làm việc với đường dẫn file/directory
import re  # Dùng cho biểu thức chính quy trong xử lý chuỗi
from typing import Any, Dict, List, Optional  # Type hints cho dữ liệu linh hoạt

import unicodedata  # Hỗ trợ chuẩn hóa unicode và loại bỏ dấu

from config import DATA_DIR  # Đường dẫn thư mục data phục vụ đọc CSV


def strip_diacritics(text: str) -> str:
    """Loại bỏ dấu tiếng Việt."""  # Docstring mô tả công dụng
    if not isinstance(text, str):  # Nếu input không phải chuỗi
        return text  # Trả nguyên giá trị (caller tự xử lý)
    norm = unicodedata.normalize("NFD", text)  # Chuẩn hóa về dạng phân tách để dễ loại bỏ dấu
    return "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")  # Ghép lại các ký tự không thuộc nhóm dấu


def normalize_text(text: str) -> str:
    """Chuẩn hóa text: bỏ dấu, lowercase, strip."""  # Docstring mô tả pipeline normalize
    if not isinstance(text, str):  # Không phải chuỗi → trả rỗng
        return ""
    return strip_diacritics(text).lower().strip()  # Bỏ dấu → hạ chữ thường → cắt khoảng trắng dư


def canonicalize_vi_ascii(text: str) -> str:
    """Chuẩn hóa biến thể thường gặp sau khi bỏ dấu."""  # Docstring mô tả xử lý
    if not isinstance(text, str):  # Nếu không phải chuỗi
        return ""
    t = text.replace("ki thuat", "ky thuat").replace(" nganh ", " ")  # Thay thế các biến thể dễ sai chính tả
    return " ".join(t.split())  # Nén khoảng trắng còn dư


def clean_program_name(name: str) -> str:
    """Nếu tên ở dạng 'Ngành/Chuyên ngành' → chỉ giữ 'Chuyên ngành'."""  # Docstring mô tả logic
    if not isinstance(name, str):  # Không phải chuỗi thì trả nguyên
        return name
    parts = [p.strip() for p in name.split("/") if p is not None]  # Tách theo dấu "/" và loại khoảng trắng
    return parts[-1] if len(parts) >= 2 else name.strip()  # Nếu có phần chuyên ngành thì lấy phần cuối


def infer_major_from_message(message: str) -> Optional[str]:
    """Suy luận tên ngành từ message khi entity extractor không bắt được."""  # Docstring mô tả mục tiêu
    from .cache import read_csv  # Import lazy để tránh vòng import

    if not message:
        return None  # Không có câu hỏi → không suy luận

    msg_norm = normalize_text(message)  # Chuẩn hóa câu hỏi để so khớp
    if not msg_norm:
        return None  # Chuỗi rỗng sau normalize → trả None

    variants = {msg_norm}  # Tập hợp biến thể câu hỏi để tăng khả năng match
    base = msg_norm  # Biến trung gian cho chuỗi đang thay thế
    for repl in [
        (" ki thuat ", " ky thuat "), (" ki thuat", " ky thuat"),  # Chuẩn hóa Kĩ/Kỹ
        ("ky thuat", " ki thuat"), (" nganh ", " "), (" ngành ", " "),  # Gom cụm ngành
        (" diem chuan ", " "), (" diem ", " "), (" chuan ", " "), (" nam ", " "),  # Bỏ bớt từ khóa phụ
    ]:
        base = base.replace(repl[0], repl[1])  # Áp dụng thay thế
        variants.add(base)  # Lưu phiên bản mới
    variants.add(re.sub(r"\b(19|20)\d{2}\b", " ", msg_norm))  # Loại bỏ năm cụ thể
    variants.add(re.sub(r"\d+", " ", msg_norm))  # Loại bỏ số đứng riêng lẻ
    variants = {" ".join(v.split()) for v in variants if v}  # Chuẩn hóa khoảng trắng

    candidates: List[str] = []  # Danh sách tên ngành/CTĐT để so khớp
    for r in read_csv(os.path.join(DATA_DIR, "majors.csv")):
        if name := (r.get("major_name") or "").strip():
            candidates.append(name)
    for r in read_csv(os.path.join(DATA_DIR, "admission_scores.csv")):
        if pname := (r.get("program_name") or "").strip():
            candidates.append(pname)
    for r in read_csv(os.path.join(DATA_DIR, "admission_targets.csv")):
        if pname := (r.get("program_name") or "").strip():
            candidates.append(pname)
        if mname := (r.get("major_name") or "").strip():
            candidates.append(mname)

    best_match, best_len = None, 0  # Biến lưu kết quả tốt nhất
    for cand in candidates:
        cnorm = normalize_text(cand)  # Chuẩn hóa tên ngành
        if not cnorm:
            continue
        for vn in variants:
            if cnorm in vn or vn in cnorm:  # Nếu có sự trùng nhau
                overlap_len = len(cnorm) if cnorm in vn else len(vn)  # Độ dài phần trùng
                if overlap_len > best_len:
                    best_match, best_len = cand, overlap_len  # Cập nhật ngành phù hợp hơn
    return best_match  # Có thể None nếu không tìm thấy


def _get_method_name_mapping() -> Dict[str, str]:
    """Tạo mapping từ method_code sang tên phương thức đầy đủ."""  # Docstring mô tả nhiệm vụ
    from .admissions import list_admission_methods_general  # Import động để tránh circular import

    method_mapping = {}  # Kết quả cuối: code → tên hiển thị
    code_methods: Dict[str, List[Dict[str, str]]] = {}  # Gom tất cả bản ghi cùng code

    for m in list_admission_methods_general():  # Duyệt danh sách phương thức tổng
        code = m.get("method_code", "")  # Mã phương thức
        if code:
            if code not in code_methods:  # Nếu chưa có, tạo list mới
                code_methods[code] = []
            code_methods[code].append({
                "abbreviation": m.get("abbreviation", ""),
                "method_name": m.get("method_name", ""),
            })  # Lưu lại viết tắt và tên đầy đủ

    for code, method_list in code_methods.items():  # Duyệt từng mã phương thức đã gom
        if len(method_list) == 1:  # Nếu chỉ có một bản ghi
            abbr = method_list[0].get("abbreviation", "")
            name = method_list[0].get("method_name", "")
            if abbr and name:
                method_mapping[code] = f"{abbr} - {name}"  # Kết hợp dạng "AB - Tên"
            elif abbr:
                method_mapping[code] = abbr  # Chỉ có viết tắt
            elif name:
                method_mapping[code] = name  # Chỉ có tên
            else:
                method_mapping[code] = code  # Không có gì → dùng code
        else:  # Nhiều bản ghi cùng code → ghép viết tắt lại
            parts = [m.get("abbreviation", "") for m in method_list if m.get("abbreviation")]
            method_mapping[code] = " / ".join(parts) if parts else code

    return method_mapping  # Trả mapping cuối cùng


def format_data_to_text(data: List[Dict[str, Any]], data_type: str) -> str:
    """Format data thành text để hiển thị."""  # Docstring mô tả output Markdown
    if not data:
        return "Không tìm thấy dữ liệu phù hợp."  # Thông báo khi không có dữ liệu

    lines = []  # Mảng dòng string sẽ join cuối cùng

    if data_type == "standard_score":  # Định dạng bảng điểm chuẩn
        grouped = {}  # Gom điểm theo chương trình
        for item in data:
            program = item.get('program_name', 'N/A')  # Lấy tên chương trình/ngành
            if program not in grouped:
                grouped[program] = {'combination': item.get('subject_combination', 'N/A'),
                                    'scores': []}  # Tạo entry mới
            grouped[program]['scores'].append(
                {'year': item.get('nam', 'N/A'), 'score': item.get('diem_chuan', 'N/A')})  # Lưu từng năm

        for idx, (program, info) in enumerate(grouped.items(), 1):
            lines.append(f"**{idx}. {program}**\n")  # Tiêu đề chương trình
            lines.append(f"• **Tổ hợp xét tuyển:** {info['combination']}\n")  # Tổ hợp môn
            lines.append("• **Điểm chuẩn qua các năm:**")  # Heading cho điểm từng năm
            for score_info in sorted(info['scores'], key=lambda x: x['year'], reverse=True):  # Sắp theo năm giảm dần
                lines.append(f"  - Năm {score_info['year']}: **{score_info['score']} điểm**")
            lines.append("")  # Dòng trống ngăn cách

    elif data_type == "scholarships":  # Định dạng học bổng
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('scholarship_name', 'N/A')}**\n")  # Tên học bổng
            if item.get('value'):
                lines.append(f"• **Giá trị:** {item.get('value')}")  # Giá trị học bổng
            if item.get('quantity'):
                lines.append(f"• **Số lượng:** {item.get('quantity')}")  # Số suất
            if item.get('academic_year'):
                lines.append(f"• **Năm học:** {item.get('academic_year')}")  # Năm áp dụng
            if item.get('requirements'):
                lines.append(f"\n• **Yêu cầu:**\n  {item.get('requirements')}")  # Điều kiện
            if item.get('note'):
                lines.append(f"\n• **Ghi chú:** {item.get('note')}")  # Ghi chú bổ sung
            lines.append("")  # Dòng trống ngăn block

    elif data_type == "tuition":  # Định dạng học phí
        for idx, item in enumerate(data, 1):
            unit = item.get('unit') or "VNĐ"  # Đơn vị hiển thị, mặc định VNĐ
            lines.append(f"**{idx}. {item.get('program_type', 'N/A')}**\n")  # Loại chương trình
            lines.append(f"• **Học phí:** {item.get('tuition_fee', 'N/A')} {unit}")  # Mức học phí
            if item.get('academic_year'):
                lines.append(f"• **Năm học:** {item.get('academic_year')}")  # Năm áp dụng
            if item.get('note'):
                lines.append(f"\n• **Lưu ý:** {item.get('note')}")  # Ghi chú nếu có
            lines.append("")

    elif data_type == "major_info":  # Định dạng thông tin ngành
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('major_name', 'N/A')}**\n")  # Tên ngành
            lines.append(f"• **Mã ngành:** {item.get('major_code', 'N/A')}\n")  # Mã ngành
            if desc := item.get('description', ''):
                lines.append("• **Giới thiệu:**\n")
                for line in desc.split('\n'):
                    if line.strip():
                        lines.append(f"  {line}")  # Thêm từng dòng mô tả
                lines.append("")
            if info := item.get('additional_info', ''):
                lines.append("• **Thông tin bổ sung:**\n")
                for line in info.split('\n'):
                    if line.strip():
                        lines.append(f"  {line}")  # Thêm thông tin bổ sung
                lines.append("")

    elif data_type == "admission_conditions":  # Điều kiện xét tuyển
        for idx, item in enumerate(data, 1):
            required = " _(Bắt buộc)_" if item.get('is_required', '').lower() in ['có', 'yes', 'true', '1'] else ""
            lines.append(f"**{idx}. {item.get('condition_name', 'N/A')}**{required}\n")  # Tên điều kiện + tag bắt buộc
            lines.append(f"  {item.get('description', 'N/A')}\n")  # Nội dung mô tả

    elif data_type == "admission_quota":  # Chỉ tiêu tuyển sinh
        method_mapping = _get_method_name_mapping()  # Map code → tên phương thức
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('major_name', 'N/A')}**\n")  # Tên ngành
            lines.append(f"• **Mã ngành:** {item.get('major_code', 'N/A')}")
            lines.append(f"• **Tổng chỉ tiêu:** {item.get('chi_tieu', 0)}")
            if chi_tiet := item.get('chi_tiet', []):
                method_combos = {}
                for detail in chi_tiet:
                    method_code = detail.get('admission_method', 'N/A')
                    combo = detail.get('subject_combination', '')
                    if method_code not in method_combos:
                        method_combos[method_code] = set()
                    if combo:
                        method_combos[method_code].add(combo)
                lines.append("\n• **Các phương thức xét tuyển:**")
                for method_code, combos in method_combos.items():
                    method_display = method_mapping.get(method_code, method_code)
                    if combos:
                        lines.append(f"  - {method_display} ({', '.join(sorted(combos))})")
                    else:
                        lines.append(f"  - {method_display}")
            lines.append("")

    elif data_type == "admission_methods":  # Phương thức xét tuyển theo ngành
        grouped = {}
        for item in data:
            nganh = item.get('major_name', 'N/A')
            method_name = item.get('method_name', '')
            abbreviation = item.get('abbreviation', '')
            if nganh not in grouped:
                grouped[nganh] = {'major_code': item.get('major_code', 'N/A'), 'methods': []}
            if abbreviation and method_name:
                display = f"{abbreviation} - {method_name}"
            elif method_name:
                display = method_name
            elif abbreviation:
                display = abbreviation
            else:
                display = item.get('method_code', 'N/A')
            if display not in grouped[nganh]['methods']:
                grouped[nganh]['methods'].append(display)
        for idx, (nganh, info) in enumerate(grouped.items(), 1):
            lines.append(f"**{idx}. {nganh}**\n")
            if info['major_code'] != 'N/A':
                lines.append(f"• **Mã ngành:** {info['major_code']}")
            lines.append("\n• **Các phương thức xét tuyển:**")
            for pt in info['methods']:
                lines.append(f"  - {pt}")
            lines.append("")

    elif data_type == "admission_methods_general":  # Phương thức chung
        for idx, item in enumerate(data, 1):
            abbr = item.get('abbreviation', '')
            name = item.get('method_name', 'N/A')
            display = f"{abbr} - {name}" if abbr and name else name or abbr or "N/A"
            lines.append(f"**{idx}. {display}**\n")
            if desc := item.get('description', ''):
                lines.append(f"• **Mô tả:**\n  {desc}\n")
            if req := item.get('requirements', ''):
                lines.append(f"• **Yêu cầu:**\n  {req}")
            lines.append("")

    elif data_type == "admissions_schedule":  # Lịch tuyển sinh
        from .admissions import list_admission_methods_general  # Import để map viết tắt → tên
        method_names_map = {m.get("abbreviation", "").strip().upper(): m.get("method_name", "")
                            for m in list_admission_methods_general() if m.get("abbreviation")}
        method_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in data:
            method = item.get('admission_method', 'Tất cả')
            method_groups.setdefault(method, []).append(item)

        idx = 1
        for method_key, items in method_groups.items():
            if method_key.lower() in ["tất cả", "tat ca"]:
                method_display = "Tất cả phương thức"
            else:
                codes = [m.strip().upper() for m in method_key.split(",") if m.strip()]
                names = [f"{c} - {method_names_map[c]}" if c in method_names_map else c for c in codes]
                method_display = ", ".join(names)
            for item in items:
                lines.append(f"**{idx}. {item.get('event_name', 'N/A')}**\n")
                lines.append(f"• **Phương thức:** {method_display}")
                lines.append(f"• **Thời gian:** {item.get('timeline', 'N/A')}")
                if note := item.get('note', ''):
                    lines.append(f"\n• **Ghi chú:** {note}")
                lines.append("")
                idx += 1

    elif data_type == "combination_details":  # Chi tiết tổ hợp xét tuyển
        from .admissions import list_admission_methods_general
        method_mapping = {m.get("abbreviation", "").strip(): m.get("method_name", "")
                          for m in list_admission_methods_general() if m.get("abbreviation")}
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. Tổ hợp {item.get('combination_code', 'N/A')}**\n")
            lines.append(f"• **Các môn thi:** {item.get('subject_names', 'N/A')}\n")
            if exam_types := item.get('exam_type', ''):
                exam_list = [e.strip() for e in exam_types.split(",") if e.strip()]
                method_names = [f"{e} - {method_mapping[e]}" if e in method_mapping else e for e in exam_list]
                lines.append("• **Áp dụng cho phương thức:**")
                for name in method_names:
                    lines.append(f"  - {name}")
                lines.append("")
            if note := item.get('note', ''):
                lines.append(f"• **Ghi chú:** _{note}_\n")

    else:  # Data type chưa được hỗ trợ cụ thể
        for idx, item in enumerate(data, 1):
            lines.append(f"{idx}. {str(item)}")  # In raw string

    return "\n".join(lines)  # Kết quả cuối cùng


def add_contact_suggestion(message: str) -> str:
    """Thêm gợi ý liên hệ vào cuối message."""  # Docstring mô tả mục đích
    from .contact import get_contact_info  # Import động để tránh vòng lặp
    contact_info = get_contact_info()  # Lấy thông tin liên hệ chuẩn
    if contact_info and contact_info.get("fanpage"):  # Chỉ thêm khi có fanpage (đảm bảo dữ liệu đầy đủ)
        return (f"{message}\n\n---\n\n**Nếu câu hỏi chưa được giải đáp đầy đủ, bạn có thể liên hệ:**\n\n"
                f"• **Fanpage:** {contact_info.get('fanpage')}\n"
                f"• **Hotline:** {contact_info.get('hotline')}\n"
                f"• **Email:** {contact_info.get('email')}")  # Chèn block liên hệ định dạng Markdown
    return message  # Nếu thiếu thông tin, giữ nguyên message gốc
