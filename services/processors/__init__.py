"""Processors module - Các hàm xử lý dữ liệu CSV."""

from .academic import list_tuition, list_scholarships  # Học phí và học bổng
from .admissions import (
    list_admission_conditions,
    list_admission_quota,
    list_admission_methods_general,
    list_admission_methods,
    list_admissions_schedule,
    get_admission_targets,
    get_combination_codes,
    get_combination_by_code,
    search_combinations,
)
from .cache import read_csv, clear_cache  # Helper đọc CSV có cache
from .cefr import get_cefr_conversion, convert_certificate_score  # Quy đổi chứng chỉ
from .contact import get_contact_info  # Thông tin liên hệ
from .majors import list_majors  # Danh sách ngành
from .scores import find_standard_score, suggest_majors_by_score  # Điểm chuẩn / gợi ý ngành
from .utils import (
    strip_diacritics,
    normalize_text,
    canonicalize_vi_ascii,
    clean_program_name,
    infer_major_from_message,
    format_data_to_text,
    add_contact_suggestion,
)

__all__ = [
    "read_csv", "clear_cache",  # Hàm cache CSV
    "strip_diacritics", "normalize_text", "canonicalize_vi_ascii",  # Tiện ích xử lý chuỗi
    "clean_program_name", "infer_major_from_message", "format_data_to_text", "add_contact_suggestion",
    "list_majors",
    "find_standard_score", "suggest_majors_by_score",
    "list_admission_conditions", "list_admission_quota", "list_admission_methods_general",
    "list_admission_methods", "list_admissions_schedule", "get_admission_targets",
    "get_combination_codes", "get_combination_by_code", "search_combinations",
    "list_tuition", "list_scholarships",
    "get_contact_info",
    "get_cefr_conversion", "convert_certificate_score",
]
