"""Intent Handler - Xử lý các intent được nhận diện từ NLP."""  # Docstring mô tả nhiệm vụ file

from typing import Any, Dict, List  # Type hints cho dữ liệu vào/ra

from services.processors import (  # Import các hàm xử lý dữ liệu chuyên biệt
    infer_major_from_message,  # Suy đoán ngành từ câu hỏi người dùng
    find_standard_score,  # Truy vấn điểm chuẩn
    list_majors,  # Lấy thông tin ngành
    list_tuition,  # Lấy học phí
    list_scholarships,  # Lấy học bổng
    list_admission_conditions,  # Điều kiện xét tuyển
    list_admission_quota,  # Chỉ tiêu tuyển sinh
    list_admission_methods_general,  # Phương thức chung
    list_admission_methods,  # Phương thức theo ngành
    list_admissions_schedule,  # Lịch tuyển sinh
    get_admission_targets,  # Bản ghi chương trình/tổ hợp
    get_combination_codes,  # Danh sách mã tổ hợp
    get_combination_by_code,  # Chi tiết 1 mã tổ hợp
    format_data_to_text,  # Chuyển dữ liệu thành văn bản Markdown
    add_contact_suggestion,  # Thêm gợi ý liên hệ
    clean_program_name,  # Chuẩn hóa tên chương trình
)

DEFAULT_OUTRO = "Nếu cần thêm thông tin nào nữa, bạn cứ nhắn mình nhé."  # Câu kết thúc mặc định
SOFT_APOLOGY = "Mình chưa tìm thấy thông tin phù hợp trong dữ liệu hiện tại. Bạn thử mô tả cụ thể hơn hoặc hỏi sang nội dung gần nhất xem sao nhé."  # Thông điệp xin lỗi nhẹ nhàng


def _compose_message(intro: str = "", formatted_text: str = "", outro: str = "", include_contact: bool = False) -> str:
    """Ghép các phần của phản hồi thành một đoạn hội thoại."""  # Docstring mô tả helper
    segments = [s.strip() for s in [intro, formatted_text, outro] if s]  # Loại bỏ chuỗi rỗng và trim từng phần
    message = "\n\n".join(segments)  # Nối các đoạn bằng khoảng trắng đôi để dễ đọc
    return add_contact_suggestion(message) if include_contact else message  # Tùy chọn chèn gợi ý liên hệ cuối câu


def _build_data_response(
        response_type: str,
        results: list,
        intro: str,
        formatted_text: str,
        empty_hint: str,
        outro: str = DEFAULT_OUTRO,
) -> Dict[str, Any]:
    """Tạo response cho intent có dữ liệu."""  # Docstring mô tả helper trả dữ liệu
    if results:  # Nếu có thông tin
        message = _compose_message(intro, formatted_text, outro)  # Ghép intro + nội dung + outro
    else:  # Không có dữ liệu
        message = _compose_message(empty_hint or SOFT_APOLOGY, "", "", include_contact=True)  # Thông điệp xin lỗi
    return {"type": response_type, "data": results, "message": message}  # Payload chuẩn trả về UI


def handle_intent_query(analysis: Dict[str, Any], context: Dict[str, Any], original_message: str = "") -> Dict[
    str, Any]:
    """Xử lý câu hỏi dựa trên intent được nhận diện."""  # Docstring cho hàm chính
    intent = analysis.get("intent", "fallback")  # Lấy intent dự đoán hoặc fallback
    entities = analysis.get("entities", [])  # Lấy danh sách entity

    major_info, year_info = None, None  # Biến lưu thông tin ngành và năm
    for entity in entities:  # Duyệt toàn bộ entity
        label, text = entity.get("label", ""), entity.get("text", "")  # Lấy nhãn và nội dung
        if label in ["MA_NGANH", "TEN_NGANH", "CHUYEN_NGANH"]:  # Nếu entity là ngành
            major_info = text  # Ghi nhận ngành
        elif label in ["NAM_HOC", "NAM_TUYEN_SINH"]:  # Nếu entity là năm
            year_info = text  # Ghi nhận năm

    # Context inference
    msg_lower = original_message.lower() if original_message else ""
    is_general_query = any(  # Kiểm tra xem câu hỏi có phải kiểu liệt kê/tất cả
        kw in msg_lower
        for kw in ["tất cả", "tat ca", "các ngành", "cac nganh", "chung", "toàn bộ", "toan bo"]
    ) if original_message else False
    is_followup = any(  # Kiểm tra câu hỏi nối tiếp (còn/thêm/nữa)
        kw in msg_lower
        for kw in ["còn", "con", "thêm", "them", "nữa", "nua", "khác", "khac"]
    ) if original_message else False
    # Kiểm tra câu hỏi có tham chiếu context (ngành này, ngành đó, nó, ...)
    has_context_reference = any(
        kw in msg_lower
        for kw in ["ngành này", "nganh nay", "ngành đó", "nganh do", "ngành ấy", "nganh ay",
                   "chuyên ngành này", "chuyen nganh nay", "chuyên ngành đó", "chuyen nganh do",
                   "nó", "của nó", "cua no", "ngành trên", "nganh tren"]
    ) if original_message else False

    def _get_major_from_context() -> str:
        """Lấy thông tin ngành từ context (last_entities hoặc conversation_history)."""
        if not context:
            return None
        # Tìm trong last_entities trước
        for e in context.get("last_entities", []):
            if e.get("label") in ["MA_NGANH", "TEN_NGANH", "CHUYEN_NGANH"] and e.get("text"):
                return e.get("text")
        # Nếu không có, tìm trong lịch sử hội thoại
        for hist_entry in reversed(context.get("conversation_history", [])):
            hist_msg = hist_entry.get("message", "")
            if hist_msg:
                inferred = infer_major_from_message(hist_msg)
                if inferred:
                    return inferred
        return None

    if not major_info:  # Nếu chưa có ngành
        if is_general_query:  # Câu hỏi dạng liệt kê
            pass  # Không cần cố đoán ngành
        elif has_context_reference:  # Nếu câu hỏi tham chiếu đến ngành trước đó
            major_info = _get_major_from_context()  # Lấy ngành từ context
        elif is_followup and context:  # Nếu là câu hỏi nối tiếp
            major_info = _get_major_from_context()  # Lấy ngành từ context
        elif original_message:  # Nếu có câu hỏi gốc
            major_info = infer_major_from_message(original_message) or None  # Suy luận ngành từ câu hỏi tự nhiên
            # Nếu không tìm thấy ngành trong câu hỏi, thử lấy từ context cho các intent cần ngành
            if not major_info and intent in ["hoi_diem_chuan", "hoi_hoc_phi", "hoi_chi_tieu", "hoi_to_hop_mon", "hoi_khoi_thi"]:
                major_info = _get_major_from_context()

    # Route to handler
    if intent.startswith("hoi_diem_chuan"):  # Điều hướng đến handler điểm chuẩn
        return _handle_diem_chuan(major_info, year_info)
    elif intent.startswith("hoi_nganh_hoc"):  # Handler ngành học
        return _handle_nganh_hoc(major_info)
    elif intent.startswith("hoi_hoc_phi"):  # Handler học phí
        return _handle_hoc_phi(major_info, year_info)
    elif intent.startswith("hoi_hoc_bong"):  # Handler học bổng
        return _handle_hoc_bong()
    elif intent.startswith("hoi_dieu_kien"):  # Handler điều kiện xét tuyển
        return _handle_dieu_kien(year_info)
    elif intent.startswith("hoi_chi_tieu"):  # Handler chỉ tiêu
        return _handle_chi_tieu(major_info, year_info)
    elif intent.startswith("hoi_phuong_thuc"):  # Handler phương thức xét tuyển
        return _handle_phuong_thuc(major_info, original_message)
    elif intent.startswith("hoi_thoi_gian_dk"):  # Handler thời gian đăng ký
        return _handle_thoi_gian_dk(entities)
    elif intent.startswith("hoi_to_hop_mon") or intent.startswith("hoi_khoi_thi"):  # Handler tổ hợp môn/khối thi
        return _handle_to_hop_mon(major_info, original_message)
    elif intent.startswith("hoi_kenh_nop_ho_so"):  # Handler kênh nộp hồ sơ
        return _handle_kenh_nop_ho_so()
    else:  # Intent không được hỗ trợ kịch bản riêng
        return {
            "type": "fallback",
            "message": _compose_message(
                "Xin lỗi, mình chưa hiểu rõ bạn muốn hỏi gì. Bạn thử nói rõ hơn (ví dụ: điểm chuẩn, học phí, ngành học...) nhé.",
                include_contact=True,
            ),
        }


def _handle_diem_chuan(major_info, year_info):
    if major_info:  # Cần biết ngành mới tra được điểm chuẩn
        results = find_standard_score(major=major_info, year=year_info)  # Truy vấn điểm chuẩn theo ngành/năm
        year_label = year_info or "các năm gần đây"  # Nhãn hiển thị nếu người dùng không chỉ định năm
        intro = (
            f"Mình tìm được {len(results)} kết quả điểm chuẩn của ngành {major_info} năm {year_label}."
            if results
            else ""
        )  # Câu giới thiệu khi có dữ liệu
        empty_hint = (
            f"Mình chưa thấy dữ liệu điểm chuẩn cho ngành {major_info}. Bạn thử kiểm tra lại tên ngành hoặc hỏi mình về năm khác."
        )  # Gợi ý khi không có dữ liệu
        return _build_data_response(
            "standard_score",
            results,
            intro,
            format_data_to_text(results, "standard_score"),
            empty_hint,
        )  # Trả về response chuẩn
    return {
        "type": "clarification",
        "message": _compose_message(
            "Bạn cho mình xin tên ngành bạn quan tâm để mình tra điểm chuẩn giúp nhé?", include_contact=True
        ),
    }  # Nếu thiếu ngành thì xin người dùng bổ sung


def _handle_nganh_hoc(major_info):
    if major_info:  # Phải biết tên ngành
        results = list_majors(major_info)  # Lấy thông tin chi tiết của ngành
        intro = f"Đây là những thông tin nổi bật về ngành {major_info}." if results else ""  # Intro khi có dữ liệu
        empty_hint = f"Mình chưa tìm thấy ngành có tên {major_info}. Bạn thử kiểm tra lại tên ngành."  # Gợi ý khi rỗng
        return _build_data_response(
            "major_info",
            results,
            intro,
            format_data_to_text(results, "major_info"),
            empty_hint,
        )  # Đóng gói response
    return {
        "type": "clarification",
        "message": _compose_message(
            "Bạn đang tìm hiểu ngành nào vậy? Cho mình xin tên ngành để hỗ trợ chi tiết nhé.", include_contact=True
        ),
    }  # Hỏi lại nếu thiếu thông tin


def _handle_hoc_phi(major_info, year_info):
    results = list_tuition(year=year_info)  # Truy vấn bảng học phí, có thể lọc theo năm
    intro_parts = ["Đây là thông tin học phí"]  # Khởi tạo câu dẫn
    if major_info:  # Nếu người dùng hỏi ngành cụ thể
        intro_parts.append(f"cho ngành {major_info}")  # Gắn tên ngành vào câu dẫn
    if year_info:  # Nếu có yêu cầu năm
        intro_parts.append(f"năm {year_info}")  # Gắn năm vào câu dẫn
    intro = (
        " ".join(intro_parts) + " mà mình tìm được." if results else "Đây là thông tin học phí mới nhất mà mình có."
    )  # Chốt câu dẫn tùy theo dữ liệu
    empty_hint = "Mình chưa có dữ liệu học phí để chia sẻ ngay lúc này."  # Thông điệp khi không có dữ liệu
    return _build_data_response("tuition", results, intro, format_data_to_text(results, "tuition"),
                                empty_hint)  # Trả kết quả


def _handle_hoc_bong():
    results = list_scholarships()  # Lấy toàn bộ học bổng
    international_kw = [  # Danh sách từ khóa nhận diện học bổng quốc tế
        "Anh", "Bỉ", "Ý", "Pháp", "Đức", "Slovakia", "Hoa Kỳ", "Mexico", "Canada", "Australia",
        "New Zealand", "Nhật Bản", "Hàn Quốc", "Singapore", "Thái Lan", "Trung Quốc", "quốc tế",
        "Chevening", "DAAD", "MEXT", "Fulbright", "KGSP", "ARES", "VEF", "AMEXCID", "AID", "JDS",
    ]
    domestic = [s for s in results if
                not any(kw in s.get("scholarship_name", "") for kw in international_kw)]  # Phân nhóm trong nước
    international = [s for s in results if
                     any(kw in s.get("scholarship_name", "") for kw in international_kw)]  # Phân nhóm quốc tế

    lines = []  # Chuẩn bị dữ liệu trình bày
    if domestic:  # Nếu có học bổng trong nước
        lines.append("### Học bổng trong nước (HUCE)\n")  # Heading nhóm
        lines.append(format_data_to_text(domestic, "scholarships"))  # Dữ liệu dạng bảng
    if international:  # Nếu có học bổng quốc tế
        lines.append("### Học bổng quốc tế\n")  # Heading nhóm
        lines.append(format_data_to_text(international, "scholarships"))  # Dữ liệu dạng bảng

    intro = f"Mình tìm thấy {len(results)} suất học bổng ({len(domestic)} trong nước, {len(international)} quốc tế)."  # Intro tổng quan
    return _build_data_response(
        "scholarships",
        results,
        intro,
        "\n".join(lines),
        "Hiện mình chưa có thông tin học bổng cập nhật.",
    )  # Trả response


def _handle_dieu_kien(year_info):
    results = list_admission_conditions()  # Lấy danh sách điều kiện hiện hành
    year_label = year_info or "2025"  # Nếu người dùng không nêu năm thì dùng mặc định
    intro = f"Dưới đây là các điều kiện xét tuyển của trường năm {year_label}:" if results else ""  # Intro hiển thị
    return _build_data_response(
        "admission_conditions",
        results,
        intro,
        format_data_to_text(results, "admission_conditions"),
        "Hiện mình chưa có thông tin về điều kiện xét tuyển.",
    )  # Trả response


def _handle_chi_tieu(major_info, year_info):
    results = list_admission_quota(major=major_info, year=year_info)  # Lấy dữ liệu chỉ tiêu
    year_label = year_info or "2025"  # Nhãn năm hiển thị
    if major_info:  # Nếu người dùng chỉ rõ ngành
        intro = f"Đây là chỉ tiêu tuyển sinh ngành {major_info} năm {year_label}." if results else ""  # Intro cụ thể
        empty_hint = f"Mình chưa tìm thấy chỉ tiêu cho ngành {major_info} năm {year_label}."  # Gợi ý khi rỗng
    else:  # Không chỉ rõ ngành
        intro = f"Dưới đây là tổng quan chỉ tiêu tuyển sinh năm {year_label}." if results else ""  # Intro chung
        empty_hint = f"Mình chưa có dữ liệu chỉ tiêu năm {year_label}."  # Gợi ý khi rỗng
    return _build_data_response(
        "admission_quota",
        results,
        intro,
        format_data_to_text(results, "admission_quota"),
        empty_hint,
    )  # Đóng gói response


def _handle_phuong_thuc(major_info, original_message):
    search_major = major_info or (
        infer_major_from_message(original_message) if original_message else None)  # Xác định ngành cần tra
    if not search_major:  # Chưa biết ngành cụ thể
        results = list_admission_methods_general()  # Lấy danh sách phương thức chung
        intro = "Đây là danh sách các phương thức xét tuyển hiện có của trường." if results else ""  # Intro
        return _build_data_response(
            "admission_methods_general",
            results,
            intro,
            format_data_to_text(results, "admission_methods_general"),
            "Mình chưa lấy được danh sách phương thức xét tuyển.",
        )
    results = list_admission_methods(major=search_major)  # Lấy phương thức theo ngành
    intro = f"Ngành {search_major} đang tuyển sinh theo những phương thức sau." if results else ""  # Intro
    return _build_data_response(
        "admission_methods",
        results,
        intro,
        format_data_to_text(results, "admission_methods"),
        f"Mình chưa thấy phương thức cho ngành {search_major}.",
    )


def _handle_thoi_gian_dk(entities):
    phuong_thuc = None  # Mặc định chưa xác định phương thức
    for e in entities:  # Duyệt danh sách entity
        if e.get("label") in ["PHUONG_THUC", "PHUONG_THUC_XET_TUYEN",
                              "PHUONG_THUC_TUYEN_SINH"]:  # Nếu entity là phương thức
            phuong_thuc = e.get("text", "")  # Lấy tên phương thức
            break  # Dừng lại sau khi tìm thấy
    results = list_admissions_schedule(phuong_thuc=phuong_thuc)  # Truy vấn lịch tuyển sinh, có thể lọc theo phương thức
    if phuong_thuc:  # Nếu người dùng hỏi phương thức cụ thể
        intro = f"Đây là mốc thời gian dành cho phương thức {phuong_thuc}." if results else ""  # Intro riêng
        empty_hint = f"Mình chưa thấy lịch dành cho phương thức {phuong_thuc}."  # Gợi ý khi không có dữ liệu
    else:  # Câu hỏi chung
        intro = "Đây là lịch trình tuyển sinh chung mà mình ghi nhận được." if results else ""  # Intro chung
        empty_hint = "Hiện mình chưa có lịch tuyển sinh cập nhật."  # Thông điệp khi rỗng
    return _build_data_response(
        "admissions_schedule",
        results,
        intro,
        format_data_to_text(results, "admissions_schedule"),
        empty_hint,
    )


def _handle_to_hop_mon(major_info, original_message=""):
    import re  # Import cục bộ để tránh chi phí ở cấp module

    combo_pattern = r"\b([A-Z]\d{2}|[A-Z]{2}\d|SP\d|VS\d|TT)\b"  # Regex tìm các mã tổ hợp quen thuộc
    combo_matches = re.findall(combo_pattern,
                               original_message.upper()) if original_message else []  # Tìm mã trong câu hỏi

    # Specific combination query
    if combo_matches:  # Nếu người dùng nêu rõ mã tổ hợp
        results = []  # Danh sách kết quả trả về
        for code in combo_matches:  # Duyệt từng mã
            results.extend(get_combination_by_code(code))  # Lấy chi tiết tổ hợp
        if results:  # Nếu tìm được thông tin
            intro = f"Đây là thông tin chi tiết về tổ hợp {', '.join(combo_matches)}."  # Câu giới thiệu
            return _build_data_response(
                "combination_details",
                results,
                intro,
                format_data_to_text(results, "combination_details"),
                "",
            )

    # General list query
    if not major_info:  # Nếu chưa biết ngành cụ thể
        if original_message and any(  # Người dùng hỏi danh sách tổng quát
                kw in original_message.lower() for kw in
                ["tất cả", "tat ca", "danh sách", "danh sach", "các tổ hợp", "cac to hop"]
        ):
            results = get_combination_codes()  # Lấy toàn bộ mã tổ hợp
            intro = f"Đây là danh sách {len(results)} tổ hợp môn thi."  # Intro chung
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
        }  # Nếu thiếu thông tin thì hỏi lại

    # Major-specific query
    targets = get_admission_targets(ma_nganh=major_info if len(major_info) == 7 else None)  # Lấy dữ liệu theo mã ngành
    if len(major_info) != 7:  # Nếu người dùng nhập tên ngành
        mq = major_info.lower()  # Normalize
        targets = [
            t for t in targets
            if mq in t.get("major_name", "").lower() or mq in t.get("program_name", "").lower()
        ]  # Lọc theo tên ngành/chương trình

    if not targets:  # Không có dữ liệu phù hợp
        return {
            "type": "major_combo",
            "data": [],
            "message": _compose_message(f"Mình chưa tìm thấy tổ hợp môn cho ngành {major_info}.", include_contact=True),
        }

    combo_details = {
        r.get("combination_code"): {"subjects": r.get("subject_names", ""), "note": r.get("note", "")}
        for r in get_combination_codes()
    }  # Map mã tổ hợp → chi tiết môn/note
    method_details: Dict[str, List[Dict[str, str]]] = {}  # Map mã phương thức → danh sách alias
    for r in list_admission_methods_general():  # Duyệt bảng phương thức chung
        code = r.get("method_code", "")
        if code:
            method_details.setdefault(code, []).append(
                {"abbreviation": r.get("abbreviation", ""), "method_name": r.get("method_name", "")}
            )  # Gom lại alias

    programs = {}  # Map tên chương trình → dữ liệu hiển thị
    for t in targets:  # Duyệt từng bản ghi chỉ tiêu
        prog_name = clean_program_name(t.get("program_name", "N/A"))  # Chuẩn hóa tên chương trình
        if prog_name not in programs:  # Nếu chưa khởi tạo
            programs[prog_name] = {
                "program_name": prog_name,
                "major_code": t.get("major_code", "N/A"),
                "methods": {},
            }  # Tạo khung dữ liệu
        combinations = t.get("subject_combination", "")  # Lấy chuỗi tổ hợp
        method_code = t.get("admission_method", "")  # Mã phương thức tương ứng
        if combinations and combinations.strip() and combinations.strip().upper() != "TT":  # Bỏ trống/viet tat TT
            programs[prog_name]["methods"].setdefault(method_code, set())  # Khởi tạo set tổ hợp cho phương thức
            for c in combinations.split(","):  # Duyệt từng tổ hợp
                if c.strip():
                    programs[prog_name]["methods"][method_code].add(c.strip())  # Thêm tổ hợp vào set để tránh trùng

    lines = []  # Dòng mô tả hiển thị cho người dùng
    for idx, (prog_name, data) in enumerate(programs.items(), 1):  # Duyệt từng chương trình
        lines.append(f"**{idx}. {prog_name}**\n")  # Đánh số thứ tự chương trình
        lines.append(f"• **Mã ngành:** {data['major_code']}\n")  # Hiển thị mã ngành
        if data["methods"]:  # Nếu có phương thức và tổ hợp
            for method_code, combos in sorted(data["methods"].items()):  # Duyệt từng phương thức
                ml = method_details.get(method_code, [])  # Lấy alias/ tên phương thức
                if len(ml) == 1:  # Một alias duy nhất
                    abbr, name = ml[0].get("abbreviation", ""), ml[0].get("method_name", "")  # Lấy dữ liệu
                    method_display = (
                        f"{abbr} - {name}" if abbr and name else abbr or name or f"Phương thức {method_code}"
                    )  # Xây dựng chuỗi hiển thị
                elif len(ml) > 1:  # Nhiều alias
                    parts = [m.get("abbreviation", "") for m in ml if m.get("abbreviation")]  # Danh sách viết tắt
                    method_display = " / ".join(parts) if parts else f"Phương thức {method_code}"  # Ghép lại
                else:  # Không có alias
                    method_display = f"Phương thức {method_code}"  # Dùng mã làm fallback
                lines.append(f"**{method_display}:**")  # Thêm tiêu đề phương thức
                for c in sorted(combos):  # Duyệt từng tổ hợp
                    if c in combo_details:  # Có chi tiết môn học
                        lines.append(f"  • **{c}:** {combo_details[c]['subjects']}")  # Hiển thị môn thi
                        if combo_details[c]["note"]:  # Nếu có ghi chú
                            lines.append(f"    _{combo_details[c]['note']}_")  # Ghi chú italic
                    else:
                        lines.append(f"  • **{c}**")  # Tổ hợp chưa có mô tả chi tiết
                lines.append("")  # Dòng trống giữa các phương thức
        else:  # Chương trình không có tổ hợp (xét tuyển thẳng)
            lines.append("• Xét tuyển thẳng hoặc chứng chỉ quốc tế\n")  # Ghi chú chung

    message = _compose_message(
        f"Các tổ hợp môn áp dụng cho ngành {major_info}.", "\n".join(lines), DEFAULT_OUTRO
    )  # Tạo thông điệp cuối
    return {"type": "major_combo", "data": targets, "message": message}  # Trả payload


def _handle_kenh_nop_ho_so():
    results = list_admissions_schedule()  # Tận dụng bảng lịch tuyển sinh vì có cột kênh nộp
    intro = "Đây là các kênh nộp hồ sơ tương ứng với từng giai đoạn tuyển sinh." if results else ""  # Intro
    return _build_data_response(
        "admissions_schedule",
        results,
        intro,
        format_data_to_text(results, "admissions_schedule"),
        "Hiện mình chưa cập nhật danh sách kênh nộp hồ sơ.",
    )
