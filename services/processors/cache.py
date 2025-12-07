import csv
import os
from typing import Any, Dict, List, Tuple

_CSV_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}


def _read_csv_cached(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []

    mtime = os.path.getmtime(path)
    cached = _CSV_CACHE.get(path)

    if cached and cached[0] == mtime:
        return cached[1]

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    _CSV_CACHE[path] = (mtime, rows)
    return rows


def read_csv(path: str) -> List[Dict[str, Any]]:
    return _read_csv_cached(path)


def clear_cache():
    global _CSV_CACHE
    _CSV_CACHE.clear()
