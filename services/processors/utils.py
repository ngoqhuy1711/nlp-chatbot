import os
import re
from typing import Any, Dict, List, Optional

import unicodedata

from config import DATA_DIR


def strip_diacritics(text: str) -> str:
    if not isinstance(text, str):
        return text
    norm = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return strip_diacritics(text).lower().strip()


def canonicalize_vi_ascii(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.replace("ki thuat", "ky thuat").replace(" nganh ", " ")
    return " ".join(t.split())


def clean_program_name(name: str) -> str:
    if not isinstance(name, str):
        return name
    parts = [p.strip() for p in name.split("/") if p is not None]
    return parts[-1] if len(parts) >= 2 else name.strip()


def infer_major_from_message(message: str) -> Optional[str]:
    from .cache import read_csv

    if not message:
        return None

    msg_norm = normalize_text(message)
    if not msg_norm:
        return None

    variants = {msg_norm}
    base = msg_norm
    for repl in [
        (" ki thuat ", " ky thuat "), (" ki thuat", " ky thuat"),
        ("ky thuat", " ki thuat"), (" nganh ", " "), (" ngành ", " "),
        (" diem chuan ", " "), (" diem ", " "), (" chuan ", " "), (" nam ", " "),
    ]:
        base = base.replace(repl[0], repl[1])
        variants.add(base)
    variants.add(re.sub(r"\b(19|20)\d{2}\b", " ", msg_norm))
    variants.add(re.sub(r"\d+", " ", msg_norm))
    variants = {" ".join(v.split()) for v in variants if v}

    candidates: List[str] = []
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

    best_match, best_len = None, 0
    for cand in candidates:
        cnorm = normalize_text(cand)
        if not cnorm:
            continue
        for vn in variants:
            if cnorm in vn or vn in cnorm:
                overlap_len = len(cnorm) if cnorm in vn else len(vn)
                if overlap_len > best_len:
                    best_match, best_len = cand, overlap_len
    return best_match


def _get_method_name_mapping() -> Dict[str, str]:
    from .admissions import list_admission_methods_general

    method_mapping = {}
    code_methods: Dict[str, List[Dict[str, str]]] = {}

    for m in list_admission_methods_general():
        code = m.get("method_code", "")
        if code:
            if code not in code_methods:
                code_methods[code] = []
            code_methods[code].append({
                "abbreviation": m.get("abbreviation", ""),
                "method_name": m.get("method_name", ""),
            })

    for code, method_list in code_methods.items():
        if len(method_list) == 1:
            abbr = method_list[0].get("abbreviation", "")
            name = method_list[0].get("method_name", "")
            if abbr and name:
                method_mapping[code] = f"{abbr} - {name}"
            elif abbr:
                method_mapping[code] = abbr
            elif name:
                method_mapping[code] = name
            else:
                method_mapping[code] = code
        else:
            parts = [m.get("abbreviation", "") for m in method_list if m.get("abbreviation")]
            method_mapping[code] = " / ".join(parts) if parts else code

    return method_mapping


def format_data_to_text(data: List[Dict[str, Any]], data_type: str) -> str:
    if not data:
        return "Không tìm thấy dữ liệu phù hợp."

    lines = []

    if data_type == "standard_score":
        grouped = {}
        for item in data:
            program = item.get('program_name', 'N/A')
            if program not in grouped:
                grouped[program] = {'combination': item.get('subject_combination', 'N/A'),
                                    'scores': []}
            grouped[program]['scores'].append(
                {'year': item.get('nam', 'N/A'), 'score': item.get('diem_chuan', 'N/A')})

        for idx, (program, info) in enumerate(grouped.items(), 1):
            lines.append(f"**{idx}. {program}**\n")
            lines.append(f"• **Tổ hợp xét tuyển:** {info['combination']}\n")
            lines.append("• **Điểm chuẩn qua các năm:**")
            for score_info in sorted(info['scores'], key=lambda x: x['year'], reverse=True):
                lines.append(f"  - Năm {score_info['year']}: **{score_info['score']} điểm**")
            lines.append("")

    elif data_type == "scholarships":
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('scholarship_name', 'N/A')}**\n")
            if item.get('value'):
                lines.append(f"• **Giá trị:** {item.get('value')}")
            if item.get('quantity'):
                lines.append(f"• **Số lượng:** {item.get('quantity')}")
            if item.get('academic_year'):
                lines.append(f"• **Năm học:** {item.get('academic_year')}")
            if item.get('requirements'):
                lines.append(f"\n• **Yêu cầu:**\n  {item.get('requirements')}")
            if item.get('note'):
                lines.append(f"\n• **Ghi chú:** {item.get('note')}")
            lines.append("")

    elif data_type == "tuition":
        for idx, item in enumerate(data, 1):
            unit = item.get('unit') or "VNĐ"
            lines.append(f"**{idx}. {item.get('program_type', 'N/A')}**\n")
            lines.append(f"• **Học phí:** {item.get('tuition_fee', 'N/A')} {unit}")
            if item.get('academic_year'):
                lines.append(f"• **Năm học:** {item.get('academic_year')}")
            if item.get('note'):
                lines.append(f"\n• **Lưu ý:** {item.get('note')}")
            lines.append("")

    elif data_type == "major_info":
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('major_name', 'N/A')}**\n")
            lines.append(f"• **Mã ngành:** {item.get('major_code', 'N/A')}\n")
            if desc := item.get('description', ''):
                lines.append("• **Giới thiệu:**\n")
                for line in desc.split('\n'):
                    if line.strip():
                        lines.append(f"  {line}")
                lines.append("")
            if info := item.get('additional_info', ''):
                lines.append("• **Thông tin bổ sung:**\n")
                for line in info.split('\n'):
                    if line.strip():
                        lines.append(f"  {line}")
                lines.append("")

    elif data_type == "admission_conditions":
        for idx, item in enumerate(data, 1):
            required = " _(Bắt buộc)_" if item.get('is_required', '').lower() in ['có', 'yes', 'true', '1'] else ""
            lines.append(f"**{idx}. {item.get('condition_name', 'N/A')}**{required}\n")
            lines.append(f"  {item.get('description', 'N/A')}\n")

    elif data_type == "admission_quota":
        method_mapping = _get_method_name_mapping()
        for idx, item in enumerate(data, 1):
            lines.append(f"**{idx}. {item.get('major_name', 'N/A')}**\n")
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

    elif data_type == "admission_methods":
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

    elif data_type == "admission_methods_general":
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

    elif data_type == "admissions_schedule":
        from .admissions import list_admission_methods_general
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

    elif data_type == "combination_details":
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

    else:
        for idx, item in enumerate(data, 1):
            lines.append(f"{idx}. {str(item)}")

    return "\n".join(lines)


def add_contact_suggestion(message: str) -> str:
    from .contact import get_contact_info
    contact_info = get_contact_info()
    if contact_info and contact_info.get("fanpage"):
        return (f"{message}\n\n---\n\n**Nếu câu hỏi chưa được giải đáp đầy đủ, bạn có thể liên hệ:**\n\n"
                f"• **Fanpage:** {contact_info.get('fanpage')}\n"
                f"• **Hotline:** {contact_info.get('hotline')}\n"
                f"• **Email:** {contact_info.get('email')}")
    return message
