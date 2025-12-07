import os
from typing import Any, Dict, List, Optional

from config import DATA_DIR
from .cache import read_csv


def get_cefr_conversion() -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "cefr_conversion.csv"))
    return rows


def convert_certificate_score(cert_type: str, score: float) -> Optional[float]:
    rows = get_cefr_conversion()

    for row in rows:
        try:
            if cert_type.upper() == "IELTS":
                ielts_range = row.get("IELTS", "").strip()
                if "-" in ielts_range:
                    min_score, max_score = map(float, ielts_range.split("-"))
                    if min_score <= score <= max_score:
                        return float(row.get("Điểm quy đổi", 0))
                else:
                    if float(ielts_range) == score:
                        return float(row.get("Điểm quy đổi", 0))

            elif cert_type.upper() == "TOEFL IBT" or cert_type.upper() == "TOEFL":
                toefl_range = row.get("TOEFL iBT", "").strip()
                if "trở lên" in toefl_range:
                    min_score = float(toefl_range.replace("trở lên", "").strip())
                    if score >= min_score:
                        return float(row.get("Điểm quy đổi", 0))
                elif "-" in toefl_range:
                    min_score, max_score = map(float, toefl_range.split("-"))
                    if min_score <= score <= max_score:
                        return float(row.get("Điểm quy đổi", 0))

        except (ValueError, AttributeError):
            continue

    return None
