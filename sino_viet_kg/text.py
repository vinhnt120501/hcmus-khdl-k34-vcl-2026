"""Chuẩn hoá chuỗi dùng chung."""
import unicodedata


def nfc(s: str) -> str:
    """Unicode NFC, bỏ khoảng trắng hai đầu."""
    return unicodedata.normalize("NFC", s or "").strip()


def norm_mention(s: str, casefold: bool = False) -> str:
    """NFC + gộp khoảng trắng (+ casefold nếu cần) — khoá so khớp mention."""
    s = " ".join(nfc(s).split())
    return s.casefold() if casefold else s
