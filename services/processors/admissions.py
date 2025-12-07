import os
from typing import Any, Dict, List, Optional

from config import DATA_DIR
from .cache import read_csv


def list_admission_conditions(phuong_thuc: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "admission_conditions.csv"))
    return [
        {"condition_name": r.get("condition_name", "").strip(),
         "description": r.get("description", "").strip(),
         "is_required": r.get("is_required", "").strip()}
        for r in rows if r.get("condition_name", "").strip() and r.get("description", "").strip()
    ]


def list_admission_quota(major: Optional[str] = None, year: Optional[str] = None) -> List[Dict[str, Any]]:
    targets = get_admission_targets(
        ma_nganh=major if major and len(major) == 7 else None)

    if major and len(major) != 7:
        from .utils import strip_diacritics
        mq = strip_diacritics(major.lower())
        targets = [t for t in targets if mq in strip_diacritics(t.get("major_name", "").lower())
                   or mq in strip_diacritics(t.get("program_name", "").lower())]

    major_quotas = {}
    for t in targets:
        key = (t.get("major_code", ""), t.get("major_name", ""))
        if key not in major_quotas:
            major_quotas[key] = {"major_code": key[0], "major_name": key[1], "nam": year or "2025", "chi_tieu": 0,
                                 "chi_tiet": []}
        try:
            chi_tieu = int(t.get("quota", "0"))
        except ValueError:
            chi_tieu = 0
        major_quotas[key]["chi_tiet"].append({
            "admission_method": t.get("admission_method", ""),
            "subject_combination": t.get("subject_combination", ""),
            "chi_tieu": chi_tieu
        })

    results = []
    for key, data in major_quotas.items():
        ma_xt_quotas = {}
        for t in targets:
            if t.get("major_code") == data["major_code"]:
                ma_xt = t.get("admission_code", "")
                try:
                    chi_tieu = int(t.get("quota", "0"))
                    if ma_xt and ma_xt not in ma_xt_quotas:
                        ma_xt_quotas[ma_xt] = chi_tieu
                except ValueError:
                    continue
        data["chi_tieu"] = sum(ma_xt_quotas.values())
        results.append(data)
    return results


def list_admission_methods_general() -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "admission_methods.csv"))
    return [
        {
            "method_code": r.get("method_code"),
            "abbreviation": r.get("abbreviation"),
            "method_name": r.get("method_name"),
            "description": r.get("description"),
            "requirements": r.get("requirements"),
        }
        for r in rows
    ]


def list_admission_methods(major: Optional[str] = None) -> List[Dict[str, Any]]:
    targets = get_admission_targets(ma_nganh=major if major and len(major) == 7 else None)

    if major and len(major) != 7:
        from .utils import strip_diacritics
        mq = strip_diacritics(major.lower())
        targets = [t for t in targets if mq in strip_diacritics(t.get("major_name", "").lower())
                   or mq in strip_diacritics(t.get("program_name", "").lower())]

    method_mapping: Dict[str, List[Dict[str, str]]] = {}
    for m in list_admission_methods_general():
        code = str(m.get("method_code", ""))
        if code:
            method_mapping.setdefault(code, []).append({
                "method_name": m.get("method_name", ""),
                "abbreviation": m.get("abbreviation", ""),
                "description": m.get("description", ""),
            })

    methods_map = {}
    for t in targets:
        key = (t.get("major_code", ""), t.get("admission_method", ""))
        if key not in methods_map:
            ml = method_mapping.get(key[1], [])
            if len(ml) > 1:
                method_name = " / ".join(
                    [f"{m['abbreviation']} - {m['method_name']}" for m in ml if
                     m['abbreviation'] and m['method_name']])
                abbreviation = " / ".join([m['abbreviation'] for m in ml if m['abbreviation']])
                method_desc = " / ".join([m['description'] for m in ml if m['description']])
            elif len(ml) == 1:
                method_name, abbreviation, method_desc = ml[0]["method_name"], ml[0]["abbreviation"], ml[0][
                    "description"]
            else:
                method_name, abbreviation, method_desc = "", "", ""
            methods_map[key] = {
                "major_code": key[0],
                "major_name": t.get("major_name", ""),
                "admission_method": key[1],
                "method_code": key[1],
                "method_name": method_name,
                "abbreviation": abbreviation,
                "description": method_desc,
                "subject_combination": [],
            }
        to_hop = t.get("subject_combination", "").strip()
        if to_hop and to_hop not in methods_map[key]["subject_combination"]:
            methods_map[key]["subject_combination"].append(to_hop)

    return [dict(d, subject_combination=", ".join(d["subject_combination"])) for d in
            methods_map.values()]


def list_admissions_schedule(phuong_thuc: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "admissions_schedule.csv"))

    method_mapping = {}
    for m in list_admission_methods_general():
        code, abbr = m.get("method_code", ""), m.get("abbreviation", "").strip().upper()
        name = m.get("method_name", "").lower()
        if abbr:
            method_mapping[abbr.lower()] = abbr
            method_mapping[abbr] = abbr
        if code and code not in method_mapping:
            method_mapping[code] = abbr
        for kw, target in [("học bạ", abbr), ("hoc ba", abbr), ("tuyển thẳng", abbr), ("tuyen thang", abbr),
                           ("chứng chỉ quốc tế", abbr), ("chung chi quoc te", abbr), ("ccqt", abbr),
                           ("v-sat", abbr), ("vsat", abbr), ("tsa", abbr), ("spt", abbr)]:
            if kw in name and kw not in method_mapping:
                method_mapping[kw] = abbr
        if "thpt" in name and "năng khiếu" not in name and "thpt" not in method_mapping:
            method_mapping["thpt"] = abbr

    search_methods = set()
    if phuong_thuc:
        pl, pu = phuong_thuc.lower().strip(), phuong_thuc.upper().strip()
        if pl in method_mapping:
            search_methods.add(method_mapping[pl].upper())
        elif pu in method_mapping:
            search_methods.add(method_mapping[pu].upper())
        else:
            search_methods.add(pu)

    results = []
    for r in rows:
        event_name = (r.get("event_name") or "").strip()
        if not event_name:
            continue
        pt_raw = (r.get("admission_method") or "").strip()
        if phuong_thuc:
            if pt_raw.lower() in ["tất cả", "tat ca"]:
                pass
            elif search_methods:
                methods_in_row = [m.strip().upper() for m in pt_raw.split(",") if m.strip()]
                if not any(m in search_methods for m in methods_in_row):
                    continue
            else:
                if phuong_thuc.lower() not in pt_raw.lower():
                    continue
        results.append({"event_name": event_name,
                        "timeline": r.get("timeline") or "",
                        "admission_method": pt_raw,
                        "note": r.get("note") or ""})
    return results


def get_admission_targets(ma_nganh: Optional[str] = None, phuong_thuc: Optional[str] = None,
                          to_hop: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "admission_targets.csv"))
    results = []
    for row in rows:
        if ma_nganh and row.get("major_code", "").strip() != ma_nganh.strip():
            continue
        if phuong_thuc and row.get("admission_method", "").strip() != phuong_thuc.strip():
            continue
        if to_hop:
            to_hop_list = [x.strip() for x in
                           row.get("subject_combination", "").split(",")]
            if to_hop.strip() not in to_hop_list:
                continue
        results.append(row)
    return results


def get_combination_codes(ky_thi: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))
    if ky_thi:
        return [r for r in rows if
                ky_thi.strip() in [x.strip() for x in r.get("exam_type", "").split(",")]]
    return rows


def get_combination_by_code(combo_code: str) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))
    code_upper = combo_code.strip().upper()
    return [r for r in rows if
            (r.get("combination_code") or "").strip().upper() == code_upper]


def search_combinations(query: str) -> List[Dict[str, Any]]:
    rows = read_csv(os.path.join(DATA_DIR, "subject_combinations.csv"))
    qu, ql = query.strip().upper(), query.strip().lower()
    return [r for r in rows if qu in (r.get("combination_code") or "").strip().upper()
            or ql in (r.get("subject_names") or "").lower()]
