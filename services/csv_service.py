from .handlers.fallback import handle_fallback_query
from .handlers.intent_handler import handle_intent_query
from .processors.academic import (
    list_tuition,
    list_scholarships,
)
from .processors.admissions import (
    list_admission_conditions,
    list_admission_quota,
    list_admission_methods_general,
    list_admission_methods,
    list_admissions_schedule,
    get_admission_targets,
    get_combination_codes,
)
from .processors.cache import read_csv as _read_csv, clear_cache
from .processors.cefr import (
    get_cefr_conversion,
    convert_certificate_score,
)
from .processors.contact import get_contact_info
from .processors.majors import list_majors
from .processors.scores import (
    find_standard_score,
    suggest_majors_by_score,
)
from .processors.utils import (
    format_data_to_text,
)


def _read_csv_cached(path: str):
    return _read_csv(path)


def _strip_diacritics(text: str) -> str:
    from .processors.utils import strip_diacritics
    return strip_diacritics(text)


def _normalize_text(text: str) -> str:
    from .processors.utils import normalize_text
    return normalize_text(text)


def _canonicalize_vi_ascii(text: str) -> str:
    from .processors.utils import canonicalize_vi_ascii
    return canonicalize_vi_ascii(text)


def _clean_program_name(name: str) -> str:
    from .processors.utils import clean_program_name
    return clean_program_name(name)


def _infer_major_from_message(message: str):
    from .processors.utils import infer_major_from_message
    return infer_major_from_message(message)


def _add_contact_suggestion(message: str) -> str:
    from .processors.utils import add_contact_suggestion
    return add_contact_suggestion(message)


__all__ = [
    "clear_cache",
    "list_majors",
    "find_standard_score",
    "suggest_majors_by_score",
    "list_admission_conditions",
    "list_admission_quota",
    "list_admission_methods_general",
    "list_admission_methods",
    "list_admissions_schedule",
    "get_admission_targets",
    "get_combination_codes",
    "list_tuition",
    "list_scholarships",
    "get_contact_info",
    "get_cefr_conversion",
    "convert_certificate_score",
    "format_data_to_text",
    "handle_intent_query",
    "handle_fallback_query",
]
