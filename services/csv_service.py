"""
CSV Service
"""

# ============================================================================
# IMPORTS - Re-export từ các module con
# ============================================================================

from .handlers.fallback import handle_fallback_query  # Handler fallback
# Handlers
from .handlers.intent_handler import handle_intent_query  # Handler intent chính
# Academic functions
from .processors.academic import (
    list_tuition,  # Trả bảng học phí
    list_scholarships,  # Trả danh sách học bổng
)
# Admissions functions
from .processors.admissions import (
    list_admission_conditions,  # Điều kiện xét tuyển
    list_admission_quota,  # Chỉ tiêu
    list_admission_methods_general,  # Tổng quan phương thức
    list_admission_methods,  # Phương thức chi tiết
    list_admissions_schedule,  # Lịch tuyển sinh
    get_admission_targets,  # Thông tin chỉ tiêu theo ngành
    get_combination_codes,  # Lấy danh sách mã tổ hợp
)
# Cache functions
from .processors.cache import read_csv as _read_csv, clear_cache  # Cache đọc CSV
# CEFR functions
from .processors.cefr import (
    get_cefr_conversion,  # Đọc bảng quy đổi
    convert_certificate_score,  # Hàm quy đổi từng chứng chỉ
)
# Contact functions
from .processors.contact import get_contact_info  # Trả thông tin liên hệ
# Majors functions
from .processors.majors import list_majors  # Danh sách ngành
# Scores functions
from .processors.scores import (
    find_standard_score,  # Tìm điểm chuẩn
    suggest_majors_by_score,  # Gợi ý ngành theo điểm
)
# Utility functions
from .processors.utils import (
    format_data_to_text,  # Định dạng dữ liệu ra text
)


# ============================================================================
# BACKWARD COMPATIBILITY - Export private functions dưới tên cũ
# ============================================================================
# Những functions này được dùng internally, cần giữ để tương thích

def _read_csv_cached(path: str):
    """Backward compatibility wrapper"""  # Docstring ghi chú
    return _read_csv(path)  # Gọi hàm mới từ cache


def _strip_diacritics(text: str) -> str:
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import strip_diacritics  # Import cục bộ tránh vòng lặp
    return strip_diacritics(text)  # Trả về chuỗi đã bỏ dấu


def _normalize_text(text: str) -> str:
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import normalize_text  # Import cục bộ
    return normalize_text(text)  # Gọi hàm normalize


def _canonicalize_vi_ascii(text: str) -> str:
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import canonicalize_vi_ascii  # Import cục bộ
    return canonicalize_vi_ascii(text)  # Gọi hàm canonicalize


def _clean_program_name(name: str) -> str:
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import clean_program_name  # Import cục bộ
    return clean_program_name(name)  # Chuẩn hóa tên chương trình


def _infer_major_from_message(message: str):
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import infer_major_from_message  # Import cục bộ
    return infer_major_from_message(message)  # Suy đoán ngành từ text


def _add_contact_suggestion(message: str) -> str:
    """Backward compatibility - already imported above"""  # Docstring
    from .processors.utils import add_contact_suggestion  # Import cục bộ
    return add_contact_suggestion(message)  # Thêm gợi ý liên hệ


# ============================================================================
# PUBLIC API - Tất cả functions được export để dùng ở nơi khác
# ============================================================================
__all__ = [
    # Cache
    "clear_cache",
    # Majors
    "list_majors",
    # Scores
    "find_standard_score",
    "suggest_majors_by_score",
    # Admissions
    "list_admission_conditions",
    "list_admission_quota",
    "list_admission_methods_general",
    "list_admission_methods",
    "list_admissions_schedule",
    "get_admission_targets",
    "get_combination_codes",
    # Academic
    "list_tuition",
    "list_scholarships",
    # Contact
    "get_contact_info",
    # CEFR
    "get_cefr_conversion",
    "convert_certificate_score",
    # Formatting
    "format_data_to_text",
    # Handlers
    "handle_intent_query",
    "handle_fallback_query",
]
