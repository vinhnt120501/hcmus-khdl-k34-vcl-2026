"""Từ điển âm Hán–Việt cho kiểm tra liên kết (Mục 3.5, 4.3).

Âm của mỗi chữ lấy từ `data/dictionary/hanviet.csv`; chữ không có trong đó lấy trường
`kVietnamese` của Unihan (`data/dictionary/unihan_kvietnamese.txt`). Ghép âm từng chữ thành các cách đọc của thực thể Hán
rồi so với tên Việt được liên kết.
"""
from __future__ import annotations

import ast
import csv
import re
import unicodedata
from itertools import product

from sino_viet_kg.paths import HANVIET_CSV, UNIHAN_TXT

_HV: dict[str, list[str]] | None = None
_UNI: dict[str, list[str]] | None = None
_WS = re.compile(r"\s+")

# Các mức khớp được tính là "xác nhận ngữ âm"
CONFIRMED_LEVELS = {"EXACT", "NO_DIACRITIC", "REORDERED", "EXPANDED"}
MATCH_LEVELS = ("EXACT", "NO_DIACRITIC", "REORDERED", "EXPANDED", "PARTIAL")


def load_dict() -> dict[str, list[str]]:
    global _HV
    if _HV is None:
        out: dict[str, list[str]] = {}
        with open(HANVIET_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ch = (row.get("char") or "").strip()
                raw = (row.get("hanviet") or "").strip()
                if not ch or not raw:
                    continue
                try:
                    reads = ast.literal_eval(raw)
                except (ValueError, SyntaxError):
                    continue
                if not isinstance(reads, (list, tuple)):
                    continue
                b = out.setdefault(ch, [])
                for r in reads:
                    if isinstance(r, str) and r.strip() and r.strip().lower() not in b:
                        b.append(r.strip().lower())
        _HV = out
    return _HV


def load_unihan() -> dict[str, list[str]]:
    global _UNI
    if _UNI is None:
        out: dict[str, list[str]] = {}
        with open(UNIHAN_TXT, encoding="utf-8") as f:
            for line in f:
                if "kVietnamese" not in line:
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 3 and parts[1] == "kVietnamese":
                    try:
                        ch = chr(int(parts[0][2:], 16))
                    except ValueError:
                        continue
                    out[ch] = [w.lower() for w in parts[2].split()]
        _UNI = out
    return _UNI


def char_readings(ch: str) -> list[str]:
    r = load_dict().get(ch)
    if r:
        return r
    return load_unihan().get(ch, [])


def hv_candidates(zh_text: str, cap: int = 256) -> tuple[list[str], list[str]]:
    """Sinh tổ hợp âm Hán-Việt. Trả (candidates, missing_chars)."""
    text = (zh_text or "").strip()
    if not text:
        return [], []
    per_char: list[list[str]] = []
    missing: list[str] = []
    for ch in text:
        if ch.isspace():
            continue
        rs = char_readings(ch)
        if not rs:
            missing.append(ch)
            continue
        per_char.append(rs)
    if missing or not per_char:
        return [], missing
    seen: dict[str, None] = {}
    for combo in product(*per_char):
        seen.setdefault(" ".join(combo), None)
        if len(seen) >= cap:
            break
    return list(seen.keys()), []


def normalize_vi(text: str) -> str:
    return _WS.sub(" ", unicodedata.normalize("NFC", str(text or "")).strip().lower())


def strip_diacritics(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _tokens(s: str) -> list[str]:
    return [t for t in s.split() if t]


def _result(match_type: str, candidate: str = "", n: int = 0, missing=None) -> dict:
    return {"match_type": match_type, "matched_candidate": candidate, "n_candidates": n,
            "missing_chars": missing or [], "confirmed": match_type in CONFIRMED_LEVELS}


def dictionary_match(zh_text: str, vi_text: str) -> dict:
    """So tên Việt với các cách đọc Hán–Việt của thực thể Hán.

    match_type: EXACT | NO_DIACRITIC | REORDERED | EXPANDED | PARTIAL | NO_MATCH | OUT_OF_DICT
    (OUT_OF_DICT: có chữ không tra được âm). confirmed = match_type thuộc CONFIRMED_LEVELS.
    """
    cands, missing = hv_candidates(zh_text)
    vi = normalize_vi(vi_text)
    if missing:
        return _result("OUT_OF_DICT", missing=missing)
    if not cands or not vi:
        return _result("NO_MATCH", n=len(cands))
    vi_nd = strip_diacritics(vi)
    vtok = set(_tokens(vi))
    for level in MATCH_LEVELS:
        for c in cands:
            ok = False
            if level == "EXACT":
                ok = (c == vi)
            elif level == "NO_DIACRITIC":
                ok = (strip_diacritics(c) == vi_nd and c != vi)
            elif level == "REORDERED":
                a = sorted(_tokens(c)); b = sorted(_tokens(vi))
                ok = (len(a) > 0 and a == b and c != vi)
            elif level == "EXPANDED":
                a = _tokens(c)
                ok = (0 < len(a) < len(vtok) and all(t in vtok for t in a))
            elif level == "PARTIAL":
                a = set(_tokens(c))
                if a and vtok:
                    ok = (len(a & vtok) / len(a | vtok)) >= 0.5
            if ok:
                return _result(level, c, len(cands))
    return _result("NO_MATCH", n=len(cands))
