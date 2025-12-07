""" 
Entity Extraction Module - Trích xuất thực thể từ câu hỏi 
 
Module này trích xuất các entity từ câu hỏi người dùng: 
- Pattern matching từ entity.json 
- Dictionary lookup từ các file CSV 
- NER (Named Entity Recognition) từ Underthesea 
- Deduplication và normalization 
"""

import csv  # Đọc dữ liệu entity từ CSV
import json  # Đọc entity patterns từ JSON
import os  # Ghép đường dẫn file
from typing import Any, Dict, List, Set, Tuple, Optional  # Kiểu dữ liệu tổng hợp

from .preprocess import normalize_text  # Hàm normalize chung cho pipeline

# Import NER từ Underthesea 
try:
    from underthesea import ner as uts_ner  # type: ignore  # Hàm NER chính 
except ImportError:
    uts_ner = None  # type: ignore  # Nếu không cài được Underthesea thì vô hiệu hóa NER 


def _load_entity_patterns(path: str) -> List[Tuple[str, str]]:
    """ 
    Load patterns từ file entity.json 
 
    Args: 
        path: Đường dẫn file entity.json 
 
    Returns: 
        List các tuple (label, pattern) 
    """
    patterns: List[Tuple[str, str]] = []  # Danh sách kết quả 
    if not os.path.isfile(path):  # Nếu file không tồn tại 
        return patterns  # Trả về list rỗng 

    with open(path, "r", encoding="utf-8") as f:  # Mở file JSON 
        data = json.load(f)  # Đọc nội dung 
        for item in data:  # Duyệt từng entry 
            label = (item.get("label") or "").strip()  # Lấy nhãn entity 
            # Chỉ lấy pattern dạng string (bỏ qua pattern phức tạp) 
            pat = item.get("pattern")  # Lấy pattern 
            if isinstance(pat, str):  # Nếu là chuỗi 
                pat = normalize_text(pat)  # Chuẩn hóa pattern 
            else:
                continue  # Bỏ qua nếu không phải chuỗi 
            if label and pat:  # Đảm bảo có đủ dữ liệu 
                patterns.append((label, pat))  # Lưu tuple (label, pattern) 
    return patterns  # Trả danh sách patterns 


def _extract_by_ner(text: str) -> List[Dict[str, Any]]:
    """ 
    Trích xuất entity bằng NER từ Underthesea 

    Args: 
        text: Văn bản cần xử lý 

    Returns: 
        List các entity được trích xuất 
    """
    if uts_ner is None:  # Nếu NER không khả dụng 
        return []  # Trả về rỗng 

    try:
        ner_result = uts_ner(text)  # List of (word, tag) 
    except (ValueError, RuntimeError):
        return []  # NER lỗi → bỏ qua 

    found: List[Dict[str, Any]] = []  # Danh sách entity tìm được 
    buffer_tokens: List[str] = []  # Tạm lưu tokens của entity hiện tại 
    current_tag: str = ""  # Nhãn entity hiện tại 

    def flush():
        """Ghi nhận entity đã hoàn thành"""
        nonlocal buffer_tokens, current_tag, found
        if buffer_tokens and current_tag:  # Khi có dữ liệu trong buffer 
            span = " ".join(buffer_tokens)  # Nối thành cụm từ 
            found.append({"label": current_tag, "text": span, "source": "ner"})  # Lưu entity 
        buffer_tokens = []  # Reset buffer 
        current_tag = ""  # Reset nhãn 

    # Xử lý kết quả NER theo format BIO 
    # Underthesea NER trả về list of tuples: [(word, pos_tag, ner_tag, chunk), ...] 
    # hoặc [(word, ner_tag), ...] tùy version 
    for item in ner_result:  # Duyệt từng phần tử 
        # Unpack an toàn: lấy phần tử đầu (word) và cuối (NER tag) 
        if isinstance(item, (list, tuple)):
            if len(item) >= 2:
                token = item[0]  # Word là phần tử đầu 
                tag = item[-1]  # NER tag thường là phần tử cuối 
            else:
                continue  # Skip nếu format không đúng 
        else:
            continue  # Skip nếu không phải tuple/list 

        # Xử lý theo BIO format 
        if isinstance(tag, str) and tag.startswith("B-"):  # Begin 
            flush()  # Kết thúc entity trước đó 
            current_tag = tag[2:]  # Lưu nhãn (bỏ tiền tố B-) 
            buffer_tokens = [token]  # Bắt đầu entity mới 
        elif (
                isinstance(tag, str) and tag.startswith("I-") and current_tag == tag[2:]
        ):  # Inside 
            buffer_tokens.append(token)  # Thêm token vào entity hiện tại 
        else:  # Other 
            flush()  # Kết thúc entity nếu đang theo dõi 

    flush()  # Flush entity cuối cùng 
    return found  # Trả danh sách entity tìm được 


class EntityExtractor:
    """
    Entity Extractor - Trích xuất thực thể từ câu hỏi

    Sử dụng 3 phương pháp:
    1. Pattern matching từ entity.json
    2. Dictionary lookup từ các file CSV
    3. NER từ Underthesea
    """

    def __init__(self, data_dir: str, patterns_path: str, synonym_map: Optional[Dict[str, str]] = None) -> None:
        """
        Khởi tạo Entity Extractor

        Args:
            data_dir: Thư mục chứa dữ liệu CSV
            patterns_path: Đường dẫn file entity.json
            synonym_map: Dict mapping từ đồng nghĩa -> từ chuẩn (optional)
        """
        self.data_dir = data_dir  # Lưu thư mục chứa dữ liệu CSV
        self.synonym_map = synonym_map or {}  # Map đồng nghĩa để chuẩn hóa entity text

        # Load patterns từ entity.json
        self.entity_patterns: List[Tuple[str, str]] = _load_entity_patterns(
            patterns_path  # Đọc danh sách pattern thủ công
        )

        # Load dictionary phrases từ các file CSV
        self.dict_phrases: List[Tuple[str, str]] = self._load_dictionary_phrases()  # Sinh phrase từ CSV

        # Mapping alias cho entity labels (chuẩn hóa tên)
        self.entity_label_alias: Dict[str, str] = {
            "NAM_TUYEN_SINH": "NAM_HOC",
            "NAM": "NAM_HOC",
            "PHUONG_THUC_TUYEN_SINH": "PHUONG_THUC_XET_TUYEN",
            "CHUNG_CHI": "CHUNG_CHI_UU_TIEN",
            "TO_HOP": "TO_HOP_MON",
            "KHOI_THI": "TO_HOP_MON",
        }

    # ---------- Loaders - Load dữ liệu từ CSV ----------

    def _load_dictionary_phrases(self) -> List[Tuple[str, str]]:
        """
        Load tất cả phrases từ các file CSV để tạo dictionary lookup

        Returns:
            List các tuple (label, phrase) đã được normalize
        """
        phrases: List[Tuple[str, str]] = []  # Danh sách kết quả

        def add_file(path: str, handler):  # type: ignore
            """Helper function để đọc file CSV và xử lý"""  # Docstring
            if os.path.isfile(path):  # Kiểm tra file tồn tại
                with open(path, newline="", encoding="utf-8") as f:  # Mở file CSV
                    reader = csv.DictReader(f)  # Tạo reader
                    for r in reader:  # Duyệt từng dòng
                        handler(r, phrases)  # Áp dụng hàm xử lý

        base = self.data_dir  # Base path để ghép file

        # majors.csv - Thông tin ngành học
        add_file(
            os.path.join(base, "majors.csv"),
            lambda r, p: (
                (
                    p.append(("MA_NGANH", normalize_text(r.get("major_code") or "")))
                    if r.get("major_code")
                    else None
                ),
                (
                    p.append(("TEN_NGANH", normalize_text(r.get("major_name") or "")))
                    if r.get("major_name")
                    else None
                ),
            ),
        )

        # admission_methods.csv - Phương thức xét tuyển
        add_file(
            os.path.join(base, "admission_methods.csv"),
            lambda r, p: (
                (
                    p.append(
                        (
                            "PHUONG_THUC_XET_TUYEN",
                            normalize_text(r.get("admission_method") or ""),
                        )
                    )
                    if r.get("admission_method")
                    else None
                ),
            ),
        )

        # tuition.csv - Học phí
        add_file(
            os.path.join(base, "tuition.csv"),
            lambda r, p: (
                (
                    p.append(
                        (
                            "HOC_PHI_CATEGORY",
                            normalize_text(r.get("program_type") or ""),
                        )
                    )
                    if r.get("program_type")
                    else None
                ),
            ),
        )

        # scholarships.csv - Học bổng
        add_file(
            os.path.join(base, "scholarships.csv"),
            lambda r, p: (
                (
                    p.append(("HOC_BONG_TEN", normalize_text(r.get("scholarship_name") or "")))
                    if r.get("scholarship_name")
                    else None
                ),
            ),
        )

        # admission_scores.csv - Điểm chuẩn
        add_file(
            os.path.join(base, "admission_scores.csv"),
            lambda r, p: (
                (
                    p.append(
                        (
                            "TEN_NGANH",
                            normalize_text(r.get("program_name") or ""),
                        )
                    )
                    if r.get("program_name")
                    else None
                ),
                # Tổ hợp môn (có thể có nhiều, phân tách bằng dấu phẩy)
                [
                    p.append(("TO_HOP_MON", normalize_text(th.strip())))
                    for th in (r.get("subject_combination") or "").split(",")
                    if th.strip()
                ],
                # Năm học (các cột là số năm: 2020, 2021, 2022, 2023, 2024, 2025)
                [
                    p.append(("NAM_HOC", normalize_text(k)))
                    for k in r.keys()
                    if k and k.strip().isdigit() and len(k.strip()) == 4
                ],
            ),
        )

        # admission_targets.csv - Chỉ tiêu tuyển sinh
        add_file(
            os.path.join(base, "admission_targets.csv"),
            lambda r, p: (
                (
                    p.append(("MA_NGANH", normalize_text(r.get("major_code") or "")))
                    if r.get("major_code")
                    else None
                ),
                (
                    p.append(("MA_XET_TUYEN", normalize_text(r.get("admission_code") or "")))
                    if r.get("admission_code")
                    else None
                ),
                (
                    p.append(("TEN_NGANH", normalize_text(r.get("major_name") or "")))
                    if r.get("major_name")
                    else None
                ),
                (
                    p.append(("CHUYEN_NGANH", normalize_text(r.get("program_name") or "")))
                    if r.get("program_name")
                    else None
                ),
                # Tổ hợp môn (có thể có nhiều, phân tách bằng dấu phẩy)
                [
                    p.append(("TO_HOP_MON", normalize_text(th)))
                    for th in (normalize_text(r.get("subject_combination") or "")).split(",")
                    if th
                ],
            ),
        )

        # admissions_schedule.csv - Lịch tuyển sinh
        add_file(
            os.path.join(base, "admissions_schedule.csv"),
            lambda r, p: (
                (
                    p.append(
                        (
                            "PHUONG_THUC_XET_TUYEN",
                            normalize_text(r.get("admission_method") or ""),
                        )
                    )
                    if r.get("admission_method")
                    else None
                ),
                (
                    p.append(("THOI_GIAN_BUOC", normalize_text(r.get("timeline") or "")))
                    if r.get("timeline")
                    else None
                ),
            ),
        )

        # contact_info.csv - Thông tin liên hệ
        add_file(
            os.path.join(base, "contact_info.csv"),
            lambda r, p: (
                (
                    p.append(("DON_VI_LIEN_HE", normalize_text(r.get("university_name") or "")))
                    if r.get("university_name")
                    else None
                ),
                (
                    p.append(("DIA_CHI", normalize_text(r.get("address") or "")))
                    if r.get("address")
                    else None
                ),
                (
                    p.append(("EMAIL", normalize_text(r.get("email") or "")))
                    if r.get("email")
                    else None
                ),
                (
                    p.append(("DIEN_THOAI", normalize_text(r.get("phone") or "")))
                    if r.get("phone")
                    else None
                ),
                (
                    p.append(("HOTLINE", normalize_text(r.get("hotline") or "")))
                    if r.get("hotline")
                    else None
                ),
                (
                    p.append(("WEBSITE", normalize_text(r.get("website") or "")))
                    if r.get("website")
                    else None
                ),
            ),
        )

        # cefr_conversion.csv - Chứng chỉ ngoại ngữ quốc tế
        add_file(
            os.path.join(base, "cefr_conversion.csv"),
            lambda r, p: (
                (
                    p.append(("CHUNG_CHI_UU_TIEN", normalize_text("IELTS")))
                    if r.get("IELTS")
                    else None
                ),
                (
                    p.append(("CHUNG_CHI_UU_TIEN", normalize_text("TOEFL iBT")))
                    if r.get("TOEFL iBT")
                    else None
                ),
                (
                    p.append(("CHUNG_CHI_UU_TIEN", normalize_text("TOEIC")))
                    if r.get("TOEIC")
                    else None
                ),
            ),
        )

        # subject_combinations.csv - Tổ hợp môn thi
        add_file(
            os.path.join(base, "subject_combinations.csv"),
            lambda r, p: (
                (
                    p.append(("TO_HOP_MON", normalize_text(r.get("combination_code") or "")))
                    if r.get("combination_code")
                    else None
                ),
                (
                    p.append(("TO_HOP_MON_TEN", normalize_text(r.get("subject_names") or "")))
                    if r.get("subject_names")
                    else None
                ),
                # Các môn học riêng lẻ trong tổ hợp
                [
                    p.append(("MON_HOC", normalize_text(subject.strip())))
                    for subject in (r.get("subject_names") or "").split(",")
                    if subject.strip()
                ],
                # Loại kỳ thi (THPT, TSA, SPT, VSAT, etc.)
                [
                    p.append(("KY_THI", normalize_text(exam_type.strip())))
                    for exam_type in (r.get("exam_type") or "").split(",")
                    if exam_type.strip()
                ],
            ),
        )

        # admission_conditions.csv - Điều kiện tuyển sinh
        add_file(
            os.path.join(base, "admission_conditions.csv"),
            lambda r, p: (
                (
                    p.append(("NAM_HOC", normalize_text(r.get("nam") or "")))
                    if r.get("nam")
                    else None
                ),
                (
                    p.append(
                        (
                            "PHUONG_THUC_XET_TUYEN",
                            normalize_text(r.get("admission_method") or ""),
                        )
                    )
                    if r.get("admission_method")
                    else None
                ),
                (
                    p.append(
                        (
                            "DIEU_KIEN_XET_TUYEN",
                            normalize_text(r.get("requirements") or ""),
                        )
                    )
                    if r.get("requirements")
                    else None
                ),
            ),
        )

        # Loại bỏ phrases rỗng và trùng lặp
        cleaned: List[Tuple[str, str]] = []
        seen: Set[Tuple[str, str]] = set()
        for lbl, phr in phrases:
            if not lbl or not phr:
                continue
            key = (lbl, phr)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(key)
        return cleaned

    # ---------- Extract - Các phương pháp trích xuất entity ----------

    def _extract_by_patterns(self, norm_text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất entity bằng pattern matching từ entity.json

        Args:
            norm_text: Văn bản đã được normalize

        Returns:
            List các entity được tìm thấy
        """
        found: List[Dict[str, Any]] = []
        for label, pat in self.entity_patterns:
            if pat and pat in norm_text:
                norm_pat = normalize_text(pat)
                fixed_label = label

                # Xử lý đặc biệt cho điểm sàn/chuẩn
                if "điểm sàn" in norm_pat:
                    fixed_label = "DIEM_SAN"
                elif "điểm chuẩn" in norm_pat:
                    fixed_label = "DIEM_CHUAN"

                found.append({"label": fixed_label, "text": pat, "source": "pattern"})
        return found

    def _extract_by_dictionaries(self, norm_text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất entity bằng dictionary lookup từ CSV

        Hỗ trợ synonym expansion: nếu text chứa synonym (vd: "cntt"),
        sẽ tìm kiếm cả canonical form (vd: "công nghệ thông tin")

        Args:
            norm_text: Văn bản đã được normalize

        Returns:
            List các entity được tìm thấy
        """
        found: List[Dict[str, Any]] = []

        # Bước 1: Tìm kiếm trực tiếp trong text
        for label, phrase in self.dict_phrases:
            if phrase and phrase in norm_text:
                found.append({"label": label, "text": phrase, "source": "dictionary"})

        # Bước 2: Expand synonyms và tìm kiếm lại
        # Tokenize text và thay thế synonyms
        tokens = norm_text.split()
        expanded_tokens = []

        for token in tokens:
            # Nếu token là synonym, lấy canonical form
            canonical = self.synonym_map.get(token, token)
            expanded_tokens.append(canonical)

        # Tạo expanded text
        expanded_text = " ".join(expanded_tokens)

        # Tìm kiếm trong expanded text (nếu khác với original)
        if expanded_text != norm_text:
            for label, phrase in self.dict_phrases:
                if phrase and phrase in expanded_text:
                    # Check xem đã tìm thấy chưa
                    already_found = any(
                        e["label"] == label and e["text"] == phrase
                        for e in found
                    )
                    if not already_found:
                        found.append({"label": label, "text": phrase, "source": "dictionary"})

        return found

    def extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Trích xuất tất cả entities từ văn bản

        Args:
            text: Văn bản cần xử lý

        Returns:
            List các entity đã được deduplicate và normalize
        """
        # Chuẩn hóa văn bản
        norm = normalize_text(text)

        # Trích xuất bằng 3 phương pháp
        results: List[Dict[str, Any]] = []
        results.extend(self._extract_by_patterns(norm))  # Pattern matching
        results.extend(self._extract_by_dictionaries(norm))  # Dictionary lookup
        results.extend(_extract_by_ner(text))  # NER

        # Deduplication và normalization
        seen: Set[Tuple[str, str]] = set()
        dedup: List[Dict[str, Any]] = []

        for ent in results:
            raw_label = (ent.get("label") or "").strip()
            raw_text = ent.get("text") or ""
            norm_t = normalize_text(raw_text)

            # Chuẩn hóa label (alias mapping)
            canon_label = self.entity_label_alias.get(raw_label, raw_label)

            # Xử lý đặc biệt cho điểm chuẩn
            if "điểm chuẩn" in norm_t:
                canon_label = "DIEM_CHUAN"

            # Deduplication
            key = (canon_label, norm_t)
            if key not in seen:
                seen.add(key)
                dedup.append(
                    {
                        "label": canon_label,
                        "text": raw_text,
                        "source": ent.get("source"),
                    }
                )

        return dedup
