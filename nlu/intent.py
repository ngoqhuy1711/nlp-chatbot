"""
Intent Detection Module - Nhận diện ý định người dùng

Module này sử dụng TF-IDF + Cosine Similarity để nhận diện intent:
1. Tính TF-IDF vector cho mỗi mẫu câu
2. Tính centroid (trọng tâm) cho mỗi intent
3. So sánh câu hỏi với các centroid bằng cosine similarity
4. Fallback bằng keyword matching nếu không đạt ngưỡng
"""  # Docstring mô tả pipeline intent detection

import math  # Dùng cho log, sqrt trong TF-IDF
from typing import Dict, List, Tuple  # Type hints cho cấu trúc dữ liệu

from .preprocess import tokenize_and_map  # Tokenizer và mapping synonym tái sử dụng

# Ngưỡng confidence cho intent detection
DEFAULT_INTENT_THRESHOLD = 0.35  # Score tối thiểu để chấp nhận intent TF-IDF


def _compute_idf(samples: List[List[str]]) -> Dict[str, float]:
    """
    Tính IDF (Inverse Document Frequency) cho tất cả tokens

    Args:
        samples: List các câu đã được tokenize

    Returns:
        Dict mapping token -> IDF score
    """
    df: Dict[str, int] = {}  # Document frequency cho từng token
    n_docs = len(samples)  # Tổng số document (mẫu)

    # Đếm số document chứa mỗi token
    for toks in samples:
        seen = set(toks)  # Tránh đếm trùng trong cùng 1 document
        for t in seen:
            df[t] = df.get(t, 0) + 1

    # Tính IDF với smoothing
    idf: Dict[str, float] = {}
    for t, c in df.items():
        idf[t] = math.log((1 + n_docs) / (1 + c)) + 1.0  # Công thức thêm 1 để tránh chia 0
    return idf


def _tf(toks: List[str]) -> Dict[str, float]:
    """
    Tính TF (Term Frequency) cho một câu

    Args:
        toks: List tokens của câu

    Returns:
        Dict mapping token -> TF score (normalized)
    """
    counts: Dict[str, int] = {}  # Số lần xuất hiện mỗi token
    for t in toks:
        counts[t] = counts.get(t, 0) + 1  # Tăng count

    total = float(len(toks)) or 1.0  # Tránh chia 0 cho câu rỗng
    return {t: c / total for t, c in counts.items()}  # Chuẩn hóa về tần suất tương đối


def _centroid(vecs: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Tính centroid (trọng tâm) từ list các vector

    Args:
        vecs: List các TF-IDF vectors

    Returns:
        Centroid vector đã được normalize
    """
    # Cộng tất cả vectors
    agg: Dict[str, float] = {}  # Vector tổng chưa normalize
    for v in vecs:
        for k, val in v.items():
            agg[k] = agg.get(k, 0.0) + val  # Cộng từng chiều

    # Normalize bằng L2 norm
    norm = math.sqrt(sum(v * v for v in agg.values())) or 1.0  # Chuẩn hóa độ dài vector
    return {k: v / norm for k, v in agg.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """
    Tính cosine similarity giữa 2 vectors

    Args:
        a, b: Hai TF-IDF vectors

    Returns:
        Cosine similarity score (0-1)
    """
    # Tối ưu: iterate qua vector ngắn hơn
    if len(a) > len(b):
        a, b = b, a  # Hoán đổi để duyệt vector ít chiều hơn

    s = 0.0
    for k, va in a.items():
        vb = b.get(k)
        if vb is not None:
            s += va * vb  # Cộng tích từng chiều chung
    return s


class IntentDetector:
    """
    Intent Detector sử dụng TF-IDF + Cosine Similarity

    Quy trình:
    1. Precompute TF-IDF vectors và centroids cho mỗi intent
    2. Với câu hỏi mới: tính TF-IDF vector
    3. So sánh với tất cả centroids bằng cosine similarity
    4. Nếu không đạt ngưỡng: fallback bằng keyword matching
    """

    def __init__(
            self,
            intent_samples: Dict[str, List[List[str]]],
            intent_keyword_backoff: Dict[str, str],
            threshold: float = DEFAULT_INTENT_THRESHOLD,
    ) -> None:
        """
        Khởi tạo Intent Detector

        Args:
            intent_samples: Dict mapping intent -> list of tokenized samples
            intent_keyword_backoff: Dict mapping keyword -> intent (fallback)
            threshold: Ngưỡng confidence cho TF-IDF matching
        """
        self.intent_samples = intent_samples  # Tập mẫu đã tokenize cho từng intent
        self.intent_keyword_backoff = intent_keyword_backoff  # Mapping keyword → intent fallback
        self.threshold = threshold  # Ngưỡng confidence tối thiểu

        # Precompute TF-IDF và centroids
        self.idf: Dict[str, float] = {}  # Lưu IDF toàn corpus
        self.intent_centroids: Dict[str, Dict[str, float]] = {}  # Vector centroid cho mỗi intent
        self._build_intent_centroids()  # Tính toán trước để inference nhanh

    # ---------- TF-IDF utilities ----------

    def _tfidf_vec(self, toks: List[str]) -> Dict[str, float]:
        """
        Tính TF-IDF vector cho một câu

        Args:
            toks: List tokens của câu

        Returns:
            TF-IDF vector đã được normalize
        """
        tf = _tf(toks)  # Term frequency
        # TF-IDF = TF * IDF
        vec = {t: tf[t] * self.idf.get(t, 0.0) for t in tf}
        # Normalize bằng L2 norm
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def _build_intent_centroids(self) -> None:
        """
        Precompute centroids cho tất cả intents
        """
        # Gom tất cả samples để tính IDF
        all_samples: List[List[str]] = []
        for samples in self.intent_samples.values():
            all_samples.extend(samples)

        # Tính IDF cho toàn bộ corpus
        self.idf = _compute_idf(all_samples) if all_samples else {}

        # Tính centroid cho mỗi intent
        centroids: Dict[str, Dict[str, float]] = {}
        for intent, samples in self.intent_samples.items():
            # Tính TF-IDF vector cho mỗi sample
            vecs = [self._tfidf_vec(s) for s in samples]
            # Tính centroid từ các vectors
            centroids[intent] = _centroid(vecs) if vecs else {}

        self.intent_centroids = centroids

    # ---------- Public API ----------
    def detect(
            self, text: str, synonym_map: Dict[str, str], normalize_for_kw_fn
    ) -> Tuple[str, float]:
        """
        Nhận diện intent của câu hỏi

        Args:
            text: Câu hỏi từ người dùng
            synonym_map: Mapping từ đồng nghĩa
            normalize_for_kw_fn: Function chuẩn hóa văn bản cho keyword matching

        Returns:
            Tuple (intent, confidence_score)
        """
        # Bước 1: TF-IDF + Cosine Similarity
        q_tokens = tokenize_and_map(text, synonym_map)  # Tokenize và map synonyms
        q_vec = self._tfidf_vec(q_tokens)  # Tính TF-IDF vector

        # So sánh với tất cả centroids
        best_intent = ""
        best_score = 0.0
        for intent, centroid in self.intent_centroids.items():
            score = (
                    _cosine(q_vec, centroid) * 1.05
            )  # Bonus cho intent bắt đầu bằng "hoi_"
            if score > best_score:
                best_score = score
                best_intent = intent

        # Nếu đạt ngưỡng: trả về kết quả TF-IDF
        if best_intent and best_score >= self.threshold:
            return best_intent, best_score

        # Bước 2: Fallback bằng keyword matching
        norm_text = normalize_for_kw_fn(text)  # Chuẩn hóa câu hỏi cho việc search keyword
        for kw, mapped_intent in self.intent_keyword_backoff.items():
            if kw in norm_text:  # Nếu chứa keyword đặc biệt
                # Trả về score cao hơn threshold để pass check
                # Score = threshold + 0.01 để đảm bảo được chấp nhận
                return mapped_intent, self.threshold + 0.01

        # Nếu không match gì: trả về fallback
        return "fallback", best_score
