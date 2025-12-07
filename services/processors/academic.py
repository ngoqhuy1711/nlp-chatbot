import os
from typing import Any, Dict, List, Optional

from config import DATA_DIR
from .cache import read_csv


def list_tuition(
        year: Optional[str] = None, program_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "tuition.csv"))
    results: List[Dict[str, Any]] = []

    for r in rows:
        nh = (r.get("academic_year") or "").strip()
        ct = (r.get("program_type") or "").strip()

        if year and year not in nh:
            continue

        if program_query and program_query.lower() not in ct.lower():
            continue

        results.append(
            {
                "academic_year": nh,
                "program_type": ct,
                "tuition_fee": r.get("tuition_fee"),
                "unit": r.get("unit"),
                "note": r.get("note"),
            }
        )
    return results


def list_scholarships(name_query: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "scholarships.csv"))

    if name_query:
        q = name_query.lower()
        rows = [r for r in rows if q in (r.get("scholarship_name") or "").lower()]

    return [
        {
            "scholarship_name": r.get("scholarship_name"),
            "value": r.get("value"),
            "quantity": r.get("quantity"),
            "academic_year": r.get("academic_year"),
            "requirements": r.get("requirements"),
            "note": r.get("note"),
        }
        for r in rows
    ]
