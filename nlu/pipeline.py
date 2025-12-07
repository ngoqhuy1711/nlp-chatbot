"""NLP Pipeline - Intent detection và Entity extraction."""  # Docstring mô tả pipeline

import csv  # Đọc dữ liệu intent từ CSV
import os  # Ghép đường dẫn
from typing import List, Dict, Tuple, Any, Optional  # Type hints

try:
    from underthesea import word_tokenize  # Tokenizer tiếng Việt
except ImportError:
    def word_tokenize(text: str):
        return text.split()  # Fallback đơn giản nếu thiếu thư viện

try:
    from underthesea import ner as uts_ner  # NER dùng cho entity fallback
except ImportError:
    uts_ner = None  # Nếu không cài đặt thì disable NER

try:
    from .preprocess import normalize_text as ext_normalize_text
    from .preprocess import tokenize_and_map as ext_tokenize_and_map
except ImportError:
    ext_normalize_text = None  # Giữ None, pipeline sẽ fallback logic đơn giản
    ext_tokenize_and_map = None

try:
    from .intent import IntentDetector  # Bộ nhận diện intent
except ImportError:
    IntentDetector = None

try:
    from .entities import EntityExtractor  # Bộ trích xuất entity
except ImportError:
    EntityExtractor = None

from config import DATA_DIR, get_intent_threshold  # Đọc config từ hệ thống

DEFAULT_INTENT_THRESHOLD = get_intent_threshold()  # Ngưỡng intent mặc định lấy từ config


def _normalize_text(text) -> str:
    """Chuẩn hóa văn bản."""  # Docstring
    if ext_normalize_text is not None:  # Nếu module preprocess khả dụng
        return ext_normalize_text(text)  # Dùng logic chuẩn
    if not isinstance(text, str):
        text = str(text) if text is not None else ""  # Fallback convert chuỗi
    return text.lower().strip()  # Chuẩn hóa cơ bản


def _load_synonyms(path: str) -> Dict[str, str]:
    """Load từ điển từ đồng nghĩa từ file CSV."""  # Docstring mô tả
    mapping: Dict[str, str] = {}
    if not os.path.isfile(path):
        return mapping  # File không tồn tại → trả dict rỗng

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Bỏ header
        for row in reader:
            if not row or (row[0] and row[0].strip().startswith('#')) or len(row) < 3:
                continue  # Bỏ comment hoặc dòng thiếu cột
            entity, canonical, alias = row[0].strip(), row[1].strip(), row[2].strip()
            if entity == "entity" or not alias or not canonical:
                continue  # Bỏ dòng header cũ hoặc thiếu dữ liệu
            alias_norm, canonical_norm = _normalize_text(alias), _normalize_text(canonical)
            if alias_norm and canonical_norm:
                mapping[alias_norm] = canonical_norm  # Lưu mapping alias → canonical
    return mapping


class NLPPipeline:
    """Pipeline xử lý ngôn ngữ tự nhiên chính."""

    def __init__(self, data_dir: str = DATA_DIR, intent_threshold: float = DEFAULT_INTENT_THRESHOLD) -> None:
        self.data_dir = data_dir
        self.intent_threshold = intent_threshold
        self.syn_map = _load_synonyms(os.path.join(data_dir, "synonym.csv"))
        self.intent_samples = self._load_intent_samples(os.path.join(data_dir, "intent.csv"))

        # Keyword backoff rules
        self.intent_keyword_backoff: Dict[str, str] = {
            "điểm chuẩn": "hoi_diem_chuan", "diem chuan": "hoi_diem_chuan",
            "chỉ tiêu": "hoi_chi_tieu", "chi tieu": "hoi_chi_tieu",
            "học phí": "hoi_hoc_phi", "hoc phi": "hoi_hoc_phi", "phi": "hoi_hoc_phi",
            "học bổng": "hoi_hoc_bong", "hoc bong": "hoi_hoc_bong",
            "phương thức": "hoi_phuong_thuc", "phuong thuc": "hoi_phuong_thuc",
            "điều kiện": "hoi_dieu_kien", "dieu kien": "hoi_dieu_kien",
            "thời gian": "hoi_thoi_gian_dk", "thoi gian": "hoi_thoi_gian_dk", "deadline": "hoi_thoi_gian_dk",
            "kênh nộp": "hoi_kenh_nop_ho_so", "kenh nop": "hoi_kenh_nop_ho_so",
            "nộp hồ sơ": "hoi_kenh_nop_ho_so", "nop ho so": "hoi_kenh_nop_ho_so",
            "tổ hợp": "hoi_to_hop_mon", "to hop": "hoi_to_hop_mon",
            "khối thi": "hoi_to_hop_mon", "khoi thi": "hoi_to_hop_mon",
            "môn thi": "hoi_to_hop_mon", "mon thi": "hoi_to_hop_mon",
            "mã ngành": "hoi_ma_nganh", "ma nganh": "hoi_ma_nganh",
            # Mã tổ hợp cụ thể
            " a00": "hoi_to_hop_mon", " a01": "hoi_to_hop_mon", " a02": "hoi_to_hop_mon",
            " b00": "hoi_to_hop_mon", " c01": "hoi_to_hop_mon", " c02": "hoi_to_hop_mon",
            " d01": "hoi_to_hop_mon", " d07": "hoi_to_hop_mon", " d24": "hoi_to_hop_mon", " d29": "hoi_to_hop_mon",
            " h00": "hoi_to_hop_mon", " h07": "hoi_to_hop_mon",
            " v00": "hoi_to_hop_mon", " v01": "hoi_to_hop_mon", " v02": "hoi_to_hop_mon",
            " x05": "hoi_to_hop_mon", " x06": "hoi_to_hop_mon", " x26": "hoi_to_hop_mon",
            " k00": "hoi_to_hop_mon", " sp1": "hoi_to_hop_mon", " sp2": "hoi_to_hop_mon",
            " sp3": "hoi_to_hop_mon", " sp4": "hoi_to_hop_mon",
            " vs1": "hoi_to_hop_mon", " vs2": "hoi_to_hop_mon", " vs3": "hoi_to_hop_mon", " vs4": "hoi_to_hop_mon",
            # Major description
            "mô tả ngành": "hoi_nganh_hoc", "mo ta nganh": "hoi_nganh_hoc",
            "giới thiệu ngành": "hoi_nganh_hoc", "gioi thieu nganh": "hoi_nganh_hoc",
            "học gì": "hoi_nganh_hoc", "hoc gi": "hoi_nganh_hoc",
            "là gì": "hoi_nganh_hoc", "la gi": "hoi_nganh_hoc",
            "ra làm gì": "hoi_nganh_hoc", "ra lam gi": "hoi_nganh_hoc",
            "học những gì": "hoi_nganh_hoc", "hoc nhung gi": "hoi_nganh_hoc",
            "đào tạo gì": "hoi_nganh_hoc", "dao tao gi": "hoi_nganh_hoc",
            "chương trình đào tạo": "hoi_nganh_hoc", "chuong trinh dao tao": "hoi_nganh_hoc",
            "cho biết về ngành": "hoi_nganh_hoc", "cho biet ve nganh": "hoi_nganh_hoc",
            "thông tin về ngành": "hoi_nganh_hoc", "thong tin ve nganh": "hoi_nganh_hoc",
            "tìm hiểu về ngành": "hoi_nganh_hoc", "tim hieu ve nganh": "hoi_nganh_hoc",
            "về ngành": "hoi_nganh_hoc", "ve nganh": "hoi_nganh_hoc",
            "giới thiệu về": "hoi_nganh_hoc", "gioi thieu ve": "hoi_nganh_hoc",
            # Other
            "liên hệ": "hoi_lien_he", "v-sat": "hoi_phuong_thuc", "vsat": "hoi_phuong_thuc",
        }

        self._intent_detector: Optional[IntentDetector] = (
            IntentDetector(self.intent_samples, self.intent_keyword_backoff, self.intent_threshold)
            if IntentDetector is not None else None
        )
        self._entity_extractor: Optional[EntityExtractor] = (
            EntityExtractor(self.data_dir, os.path.join(data_dir, "entity.json"), self.syn_map)
            if EntityExtractor is not None else None
        )

    def _load_intent_samples(self, path: str) -> Dict[str, List[List[str]]]:
        """Load mẫu câu cho intent detection."""
        intent_to_samples: Dict[str, List[List[str]]] = {}
        if not os.path.isfile(path):
            return intent_to_samples  # File không tồn tại → trả dict rỗng

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                utt = _normalize_text(r.get("utterance") or "")  # Chuẩn hóa utterance
                intent = (r.get("intent") or "").strip()
                if not utt or not intent:
                    continue  # Bỏ dòng thiếu dữ liệu
                toks = ext_tokenize_and_map(utt, self.syn_map) if ext_tokenize_and_map else utt.split()  # Tokenize
                intent_to_samples.setdefault(intent, []).append(toks)  # Gom vào intent tương ứng
        return intent_to_samples

    def detect_intent(self, text: str) -> Tuple[str, float]:
        """Nhận diện intent của câu hỏi."""
        if self._intent_detector is None:
            return "fallback", 0.0  # Nếu IntentDetector chưa khởi tạo
        return self._intent_detector.detect(text, self.syn_map, _normalize_text)  # Trả intent + score

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Trích xuất các entity trong câu hỏi."""
        if self._entity_extractor is None:
            return []  # Không có extractor → trả danh sách rỗng
        return self._entity_extractor.extract(text)  # Kết quả entity

    def analyze(self, text: str) -> Dict[str, Any]:
        """Phân tích toàn diện câu hỏi từ người dùng."""
        intent, score = self.detect_intent(text)  # Intent + score
        entities = self.extract_entities(text)  # Danh sách entity

        # Heuristic: Override intent cho câu hỏi rõ ràng về ngành học
        norm_text = _normalize_text(text)
        uncertain_intents = ["fallback", "tro_giup", "chao_hoi"]
        is_uncertain = intent in uncertain_intents or score < (self.intent_threshold + 0.15)

        if is_uncertain and entities:
            has_major = any(e.get("label") in ["TEN_NGANH", "CHUYEN_NGANH"] for e in entities)
            has_nganh_keyword = "nganh" in norm_text
            exclusion_keywords = ["ma nganh", "mã ngành", "ma ", " ma", "diem chuan", "điểm chuẩn", "diem ", "điểm ",
                                  "hoc phi", "học phí", "tien hoc", "tiền học", "chi phi", "chi phí",
                                  "chi tieu", "chỉ tiêu", "tuyen sinh", "tuyển sinh", "tuyen", "tuyển",
                                  "to hop", "tổ hợp", "khoi thi", "khối thi", "mon thi", "môn thi",
                                  "phuong thuc", "phương thức", "xet tuyen", "xét tuyển"]
            has_exclusion = any(kw in norm_text for kw in exclusion_keywords)
            major_intro_keywords = ["gioi thieu", "tim hieu", "mo ta", "la gi", "hoc gi", "ve nganh", "thong tin ve",
                                    "cho biet ve", "muon biet"]
            has_intro_keyword = any(kw in norm_text for kw in major_intro_keywords)

            if (has_major or (has_nganh_keyword and has_intro_keyword)) and not has_exclusion:
                intent = "hoi_nganh_hoc"  # Gán intent ngành học
                score = self.intent_threshold + 0.15  # Boost score để vượt ngưỡng

        return {"intent": intent, "score": score, "entities": entities}
