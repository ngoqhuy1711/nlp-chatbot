from typing import Any, Dict, List

from services.processors import (
    infer_major_from_message,
    find_standard_score,
    list_majors,
    list_tuition,
    list_scholarships,
    list_admission_conditions,
    list_admission_quota,
    list_admission_methods_general,
    list_admission_methods,
    list_admissions_schedule,
    get_admission_targets,
    get_combination_codes,
    get_combination_by_code,
    format_data_to_text,
    add_contact_suggestion,
    clean_program_name,
)

DEFAULT_OUTRO = "Nếu cần thêm thông tin nào nữa, bạn cứ nhắn mình nhé."
SOFT_APOLOGY = "Mình chưa tìm thấy thông tin phù hợp trong dữ liệu hiện tại. Bạn thử mô tả cụ thể hơn hoặc hỏi sang nội dung gần nhất xem sao nhé."


def _compose_message(intro: str = "", formatted_text: str = "", outro: str = "", include_contact: bool = False) -> str:
    segments = [s.strip() for s in [intro, formatted_text, outro] if s]
    message = "\n\n".join(segments)
    return add_contact_suggestion(message) if include_contact else message


def _build_data_response(
        response_type: str,
        results: list,
        intro: str,
        formatted_text: str,
        empty_hint: str,
        outro: str = DEFAULT_OUTRO,
) -> Dict[str, Any]:
    if results:
        message = _compose_message(intro, formatted_text, outro)
    else:
        message = _compose_message(empty_hint or SOFT_APOLOGY, "", "", include_contact=True)
    return {"type": response_type, "data": results, "message": message}


def handle_intent_query(analysis: Dict[str, Any], context: Dict[str, Any], original_message: str = "") -> Dict[
    str, Any]:
    intent = analysis.get("intent", "fallback")
    entities = analysis.get("entities", [])

    major_info, year_info = None, None
    for entity in entities:
        label, text = entity.get("label", ""), entity.get("text", "")
        if label in ["MA_NGANH", "TEN_NGANH", "CHUYEN_NGANH"]:
            major_info = text
        elif label in ["NAM_HOC", "NAM_TUYEN_SINH"]:
            year_info = text

    msg_lower = original_message.lower() if original_message else ""
    is_general_query = any(
        kw in msg_lower
        for kw in ["tất cả", "tat ca", "các ngành", "cac nganh", "chung", "toàn bộ", "toan bo"]
    ) if original_message else False
    is_followup = any(
        kw in msg_lower
        for kw in ["còn", "con", "thêm", "them", "nữa", "nua", "khác", "khac"]
    ) if original_message else False
    has_context_reference = any(
        kw in msg_lower
        for kw in ["ngành này", "nganh nay", "ngành đó", "nganh do", "ngành ấy", "nganh ay",
                   "chuyên ngành này", "chuyen nganh nay", "chuyên ngành đó", "chuyen nganh do",
                   "nó", "của nó", "cua no", "ngành trên", "nganh tren"]
    ) if original_message else False

    def _get_major_from_context() -> str:
        if not context:
            return None
        for e in context.get("last_entities", []):
            if e.get("label") in ["MA_NGANH", "TEN_NGANH", "CHUYEN_NGANH"] and e.get("text"):
                return e.get("text")
        return None

    if not major_info:
        if is_general_query:
            pass
        elif has_context_reference:
            major_info = _get_major_from_context()
        elif is_followup and context:
            major_info = _get_major_from_context()
        elif original_message:
            major_info = infer_major_from_message(original_message) or None
            if not major_info and intent in ["hoi_diem_chuan", "hoi_hoc_phi", "hoi_chi_tieu", "hoi_to_hop_mon", "hoi_khoi_thi"]:
                major_info = _get_major_from_context()

    if intent.startswith("hoi_diem_chuan"):
        return _handle_diem_chuan(major_info, year_info)
    elif intent.startswith("hoi_nganh_hoc"):
        return _handle_nganh_hoc(major_info)
    elif intent.startswith("hoi_hoc_phi"):
        return _handle_hoc_phi(major_info, year_info)
    elif intent.startswith("hoi_hoc_bong"):
        return _handle_hoc_bong()
    elif intent.startswith("hoi_dieu_kien"):
        return _handle_dieu_kien(year_info)
    elif intent.startswith("hoi_chi_tieu"):
        return _handle_chi_tieu(major_info, year_info)
    elif intent.startswith("hoi_phuong_thuc"):
        return _handle_phuong_thuc(major_info, original_message)
    elif intent.startswith("hoi_thoi_gian_dk"):
        return _handle_thoi_gian_dk(entities)
    elif intent.startswith("hoi_to_hop_mon") or intent.startswith("hoi_khoi_thi"):
        return _handle_to_hop_mon(major_info, original_message)
    elif intent.startswith("hoi_kenh_nop_ho_so"):
        return _handle_kenh_nop_ho_so()
    else:
        return {
            "type": "fallback",
            "message": _compose_message(
                "Xin lỗi, mình chưa hiểu rõ bạn muốn hỏi gì. Bạn thử nói rõ hơn (ví dụ: điểm chuẩn, học phí, ngành học...) nhé.",
                include_contact=True,
            ),
        }


def _handle_diem_chuan(major_info, year_info):
    if major_info:
        results = find_standard_score(major=major_info, year=year_info)
        year_label = year_info or "các năm gần đây"
        intro = (
            f"Mình tìm được {len(results)} kết quả điểm chuẩn của ngành {major_info} năm {year_label}."
            if results
            else ""
        )
        empty_hint = (
            f"Mình chưa thấy dữ liệu điểm chuẩn cho ngành {major_info}. Bạn thử kiểm tra lại tên ngành hoặc hỏi mình về năm khác."
        )
        return _build_data_response(
            "standard_score",
            results,
            intro,
            format_data_to_text(results, "standard_score"),
            empty_hint,
        )
    return {
        "type": "clarification",
        "message": _compose_message(
            "Bạn cho mình xin tên ngành bạn quan tâm để mình tra điểm chuẩn giúp nhé?", include_contact=True
        ),
    }


def _handle_nganh_hoc(major_info):
    if major_info:
        results = list_majors(major_info)
        intro = f"Đây là những thông tin nổi bật về ngành {major_info}." if results else ""
        empty_hint = f"Mình chưa tìm thấy ngành có tên {major_info}. Bạn thử kiểm tra lại tên ngành."
        return _build_data_response(
            "major_info",
            results,
            intro,
            format_data_to_text(results, "major_info"),
            empty_hint,
        )
    return {
        "type": "clarification",
        "message": _compose_message(
            "Bạn đang tìm hiểu ngành nào vậy? Cho mình xin tên ngành để hỗ trợ chi tiết nhé.", include_contact=True
        ),
    }


def _handle_hoc_phi(major_info, year_info):
    results = list_tuition(year=year_info)
    intro_parts = ["Đây là thông tin học phí"]
    if major_info:
        intro_parts.append(f"cho ngành {major_info}")
    if year_info:
        intro_parts.append(f"năm {year_info}")
    intro = (
        " ".join(intro_parts) + " mà mình tìm được." if results else "Đây là thông tin học phí mới nhất mà mình có."
    )
    empty_hint = "Mình chưa có dữ liệu học phí để chia sẻ ngay lúc này."
    return _build_data_response("tuition", results, intro, format_data_to_text(results, "tuition"),
                                empty_hint)


def _handle_hoc_bong():
    results = list_scholarships()
    international_kw = [
        "Anh", "Bỉ", "Ý", "Pháp", "Đức", "Slovakia", "Hoa Kỳ", "Mexico", "Canada", "Australia",
        "New Zealand", "Nhật Bản", "Hàn Quốc", "Singapore", "Thái Lan", "Trung Quốc", "quốc tế",
        "Chevening", "DAAD", "MEXT", "Fulbright", "KGSP", "ARES", "VEF", "AMEXCID", "AID", "JDS",
    ]
    domestic = [s for s in results if
                not any(kw in s.get("scholarship_name", "") for kw in international_kw)]
    international = [s for s in results if
                     any(kw in s.get("scholarship_name", "") for kw in international_kw)]

    lines = []
    if domestic:
        lines.append("### Học bổng trong nước (HUCE)\n")
        lines.append(format_data_to_text(domestic, "scholarships"))
    if international:
        lines.append("### Học bổng quốc tế\n")
        lines.append(format_data_to_text(international, "scholarships"))

    intro = f"Mình tìm thấy {len(results)} suất học bổng ({len(domestic)} trong nước, {len(international)} quốc tế)."
    return _build_data_response(
        "scholarships",
        results,
        intro,
        "\n".join(lines),
        "Hiện mình chưa có thông tin học bổng cập nhật.",
    )


def _handle_dieu_kien(year_info):
    results = list_admission_conditions()
    year_label = year_info or "2025"
    intro = f"Dưới đây là các điều kiện xét tuyển của trường năm {year_label}:" if results else ""
    return _build_data_response(
        "admission_conditions",
        results,
        intro,
        format_data_to_text(results, "admission_conditions"),
        "Hiện mình chưa có thông tin về điều kiện xét tuyển.",
    )


def _handle_chi_tieu(major_info, year_info):
    results = list_admission_quota(major=major_info, year=year_info)
    year_label = year_info or "2025"
    if major_info:
        intro = f"Đây là chỉ tiêu tuyển sinh ngành {major_info} năm {year_label}." if results else ""
        empty_hint = f"Mình chưa tìm thấy chỉ tiêu cho ngành {major_info} năm {year_label}."
    else:
        intro = f"Dưới đây là tổng quan chỉ tiêu tuyển sinh năm {year_label}." if results else ""
        empty_hint = f"Mình chưa có dữ liệu chỉ tiêu năm {year_label}."
    return _build_data_response(
        "admission_quota",
        results,
        intro,
        format_data_to_text(results, "admission_quota"),
        empty_hint,
    )


def _handle_phuong_thuc(major_info, original_message):
    search_major = major_info or (
        infer_major_from_message(original_message) if original_message else None)
    if not search_major:
        results = list_admission_methods_general()
        intro = "Đây là danh sách các phương thức xét tuyển hiện có của trường." if results else ""
        return _build_data_response(
            "admission_methods_general",
            results,
            intro,
            format_data_to_text(results, "admission_methods_general"),
            "Mình chưa lấy được danh sách phương thức xét tuyển.",
        )
    results = list_admission_methods(major=search_major)
    intro = f"Ngành {search_major} đang tuyển sinh theo những phương thức sau." if results else ""
    return _build_data_response(
        "admission_methods",
        results,
        intro,
        format_data_to_text(results, "admission_methods"),
        f"Mình chưa thấy phương thức cho ngành {search_major}.",
    )


def _handle_thoi_gian_dk(entities):
    phuong_thuc = None
    for e in entities:
        if e.get("label") in ["PHUONG_THUC", "PHUONG_THUC_XET_TUYEN",
                              "PHUONG_THUC_TUYEN_SINH"]:
            phuong_thuc = e.get("text", "")
            break
    results = list_admissions_schedule(phuong_thuc=phuong_thuc)
    if phuong_thuc:
        intro = f"Đây là mốc thời gian dành cho phương thức {phuong_thuc}." if results else ""
        empty_hint = f"Mình chưa thấy lịch dành cho phương thức {phuong_thuc}."
    else:
        intro = "Đây là lịch trình tuyển sinh chung mà mình ghi nhận được." if results else ""
        empty_hint = "Hiện mình chưa có lịch tuyển sinh cập nhật."
    return _build_data_response(
        "admissions_schedule",
        results,
        intro,
        format_data_to_text(results, "admissions_schedule"),
        empty_hint,
    )


def _handle_to_hop_mon(major_info, original_message=""):
    import re

    combo_pattern = r"\b([A-Z]\d{2}|[A-Z]{2}\d|SP\d|VS\d|TT)\b"
    combo_matches = re.findall(combo_pattern,
                               original_message.upper()) if original_message else []

    if combo_matches:
        results = []
        for code in combo_matches:
            results.extend(get_combination_by_code(code))
        if results:
            intro = f"Đây là thông tin chi tiết về tổ hợp {', '.join(combo_matches)}."
            return _build_data_response(
                "combination_details",
                results,
                intro,
                format_data_to_text(results, "combination_details"),
                "",
            )

    if not major_info:
        if original_message and any(
                kw in original_message.lower() for kw in
                ["tất cả", "tat ca", "danh sách", "danh sach", "các tổ hợp", "cac to hop"]
        ):
            results = get_combination_codes()
            intro = f"Đây là danh sách {len(results)} tổ hợp môn thi."
            return _build_data_response(
                "combination_details",
                results,
                intro,
                format_data_to_text(results, "combination_details"),
                "",
            )
        return {
            "type": "clarification",
            "message": _compose_message(
                "Bạn muốn mình tra tổ hợp môn cho ngành nào, hoặc cho mình mã tổ hợp cụ thể (ví dụ: A00, D01) để tra chi tiết nhé.",
                include_contact=True,
            ),
        }

    targets = get_admission_targets(ma_nganh=major_info if len(major_info) == 7 else None)
    if len(major_info) != 7:
        mq = major_info.lower()
        targets = [
            t for t in targets
            if mq in t.get("major_name", "").lower() or mq in t.get("program_name", "").lower()
        ]

    if not targets:
        return {
            "type": "major_combo",
            "data": [],
            "message": _compose_message(f"Mình chưa tìm thấy tổ hợp môn cho ngành {major_info}.", include_contact=True),
        }

    combo_details = {
        r.get("combination_code"): {"subjects": r.get("subject_names", ""), "note": r.get("note", "")}
        for r in get_combination_codes()
    }
    method_details: Dict[str, List[Dict[str, str]]] = {}
    for r in list_admission_methods_general():
        code = r.get("method_code", "")
        if code:
            method_details.setdefault(code, []).append(
                {"abbreviation": r.get("abbreviation", ""), "method_name": r.get("method_name", "")}
            )

    programs = {}
    for t in targets:
        prog_name = clean_program_name(t.get("program_name", "N/A"))
        if prog_name not in programs:
            programs[prog_name] = {
                "program_name": prog_name,
                "major_code": t.get("major_code", "N/A"),
                "methods": {},
            }
        combinations = t.get("subject_combination", "")
        method_code = t.get("admission_method", "")
        if combinations and combinations.strip() and combinations.strip().upper() != "TT":
            programs[prog_name]["methods"].setdefault(method_code, set())
            for c in combinations.split(","):
                if c.strip():
                    programs[prog_name]["methods"][method_code].add(c.strip())

    lines = []
    for idx, (prog_name, data) in enumerate(programs.items(), 1):
        lines.append(f"**{idx}. {prog_name}**\n")
        lines.append(f"• **Mã ngành:** {data['major_code']}\n")
        if data["methods"]:
            for method_code, combos in sorted(data["methods"].items()):
                ml = method_details.get(method_code, [])
                if len(ml) == 1:
                    abbr, name = ml[0].get("abbreviation", ""), ml[0].get("method_name", "")
                    method_display = (
                        f"{abbr} - {name}" if abbr and name else abbr or name or f"Phương thức {method_code}"
                    )
                elif len(ml) > 1:
                    parts = [m.get("abbreviation", "") for m in ml if m.get("abbreviation")]
                    method_display = " / ".join(parts) if parts else f"Phương thức {method_code}"
                else:
                    method_display = f"Phương thức {method_code}"
                lines.append(f"**{method_display}:**")
                for c in sorted(combos):
                    if c in combo_details:
                        lines.append(f"  • **{c}:** {combo_details[c]['subjects']}")
                        if combo_details[c]["note"]:
                            lines.append(f"    _{combo_details[c]['note']}_")
                    else:
                        lines.append(f"  • **{c}**")
                lines.append("")
        else:
            lines.append("• Xét tuyển thẳng hoặc chứng chỉ quốc tế\n")

    message = _compose_message(
        f"Các tổ hợp môn áp dụng cho ngành {major_info}.", "\n".join(lines), DEFAULT_OUTRO
    )
    return {"type": "major_combo", "data": targets, "message": message}


def _handle_kenh_nop_ho_so():
    results = list_admissions_schedule()
    intro = "Đây là các kênh nộp hồ sơ tương ứng với từng giai đoạn tuyển sinh." if results else ""
    return _build_data_response(
        "admissions_schedule",
        results,
        intro,
        format_data_to_text(results, "admissions_schedule"),
        "Hiện mình chưa cập nhật danh sách kênh nộp hồ sơ.",
    )
