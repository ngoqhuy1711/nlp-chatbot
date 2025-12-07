"""
Text Preprocessing Module - Tiền xử lý văn bản tiếng Việt

Module này xử lý:
- Chuẩn hóa Unicode và ký tự đặc biệt
- Tách từ bằng Underthesea
- Mapping từ đồng nghĩa
- Loại bỏ stopwords
"""  # Docstring mô tả nhiệm vụ module

import re  # Dùng regex để loại bỏ ký tự đặc biệt, nén khoảng trắng
from typing import Dict, List, Set  # Type hints cho map/tập kết quả

import unicodedata  # Hỗ trợ chuẩn hóa Unicode (NFC)

# Import Underthesea cho tokenization tiếng Việt
try:
    from underthesea import word_tokenize  # Tokenizer chính
except ImportError:  # fallback nếu không cài đặt được

    def word_tokenize(text: str):
        return text.split()  # Tách đơn giản bằng split khi thiếu thư viện

# Từ dừng tiếng Việt (có thể mở rộng)
VI_STOPWORDS: Set[str] = {
    "là",
    "làm",
    "và",
    "hoặc",
    "nhưng",
    "thì",
    "lúc",
    "khi",
    "ở",
    "của",
    "cho",
    "với",
    "đến",
    "tới",
    "từ",
    "có",
    "được",
    "nhé",
    "ạ",
    "à",
    "ư",
    "mình",
    "bạn",
    "xin",
    "chào",
    "ơi",
    "giúp",
    "hỏi",
    "cho",
    "xem",
    "bao",
}


def normalize_text(text) -> str:
    """
    Chuẩn hóa văn bản tiếng Việt

    Args:
        text: Văn bản cần chuẩn hóa

    Returns:
        Văn bản đã được chuẩn hóa:
        - Lowercase
        - Unicode normalization (NFC)
        - Loại bỏ ký tự đặc biệt (giữ lại chữ cái, số, khoảng trắng)
        - Chuẩn hóa khoảng trắng
    """  # Docstring mô tả pipeline chuẩn hóa
    if not isinstance(text, str):
        text = str(text) if text is not None else ""  # Chuyển về chuỗi để tránh crash

    # Chuyển về lowercase và strip
    text = text.lower().strip()

    # Chuẩn hóa Unicode (NFC - Canonical Composition)
    text = unicodedata.normalize("NFC", text)

    # Loại bỏ ký tự đặc biệt, giữ lại chữ cái, số, khoảng trắng và ký tự tiếng Việt
    text = re.sub(
        r"[^\w\sáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]",
        " ",
        text,
    )

    # Chuẩn hóa khoảng trắng (nhiều space thành 1 space)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_and_map(text: str, synonym_map: Dict[str, str]) -> List[str]:
    """
    Tách từ và mapping từ đồng nghĩa

    Args:
        text: Văn bản cần xử lý
        synonym_map: Dict mapping từ đồng nghĩa -> từ chuẩn

    Returns:
        List tokens đã được xử lý:
        - Chuẩn hóa văn bản
        - Tách từ bằng Underthesea
        - Mapping từ đồng nghĩa
        - Loại bỏ stopwords
    """
    # Bước 1: Chuẩn hóa văn bản
    norm = normalize_text(text)

    # Bước 2: Tách từ bằng Underthesea
    try:
        raw = word_tokenize(norm)  # Underthesea trả về string
        toks = raw.split()  # Split thành list
    except (ValueError, TypeError, AttributeError):
        # Fallback: split đơn giản
        toks = norm.split()

    # Bước 3: Mapping từ đồng nghĩa
    mapped = [synonym_map.get(tok, tok) for tok in toks]

    # Bước 4: Loại bỏ stopwords
    filtered = [t for t in mapped if t not in VI_STOPWORDS]

    return filtered
