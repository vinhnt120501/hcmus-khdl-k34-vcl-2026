"""Tách ngữ liệu CLC thành cặp câu Hán–Việt (đầu vào của Mục 3.2).

Mỗi dòng của tệp xlsx là một đoạn; cột `Chinese_Vietnamese_alignment` chứa bảng Markdown
`| Hán | Việt |` đã gióng hàng theo câu. Mỗi hàng của bảng là một cặp câu, mã
`pair_id = <dòng>-<thứ tự>`. Kết quả ghi ra `<VCL_CORPUS_DIR>/1_sentence_pairs/rows/`.

    python3 -m sino_viet_kg.extraction.sentence_pairs
"""
from __future__ import annotations

import json
import re
import unicodedata

from sino_viet_kg import paths

ALIGNMENT_COLUMN = "Chinese_Vietnamese_alignment"
METADATA_COLUMNS = ["ID", "Link", "Period", "Num_pages"]

_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_HEADER_LEFT = {"literary chinese", "chinese"}
_HEADER_RIGHT = {"vietnamese"}


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def parse_alignment_table(text: str) -> list[dict]:
    """Bảng Markdown `| Hán | Việt |` -> [{raw, chinese, vietnamese}], bỏ tiêu đề và dòng kẻ."""
    pairs = []
    for raw_line in str(text).splitlines():
        line = raw_line.rstrip()
        if not line.strip() or _SEPARATOR_RE.match(line) or "|" not in line:
            continue
        cells = line.strip().removeprefix("|").removesuffix("|").split("|")
        cells = [c.strip() for c in cells]
        if len(cells) < 2:
            continue
        if cells[0].lower() in _HEADER_LEFT and cells[1].lower() in _HEADER_RIGHT:
            continue
        if not cells[0] and not cells[1]:
            continue
        pairs.append({"raw": _nfc(line), "chinese": _nfc(cells[0]), "vietnamese": _nfc(cells[1])})
    return pairs


def _plain(value):
    """Ô pandas -> kiểu Python (NaN -> None, chuỗi -> NFC)."""
    import pandas as pd
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return _nfc(value)
    return value.item() if hasattr(value, "item") else value


def split_corpus(xlsx=paths.SOURCE_XLSX) -> list[dict]:
    """-> mỗi dòng ngữ liệu một bản ghi {source_row, metadata, alignment_raw, pairs}."""
    import pandas as pd
    df = pd.read_excel(paths.require(xlsx, "tệp ngữ liệu xlsx của CLC"))
    meta_cols = [c for c in METADATA_COLUMNS if c in df.columns]
    rows = []
    for src_idx, row in df.iterrows():
        src = int(src_idx)
        meta = {c: _plain(row[c]) for c in meta_cols}
        block = row[ALIGNMENT_COLUMN]
        has_block = not pd.isna(block)
        pairs = []
        if has_block:
            for i, p in enumerate(parse_alignment_table(block)):
                pairs.append({"source_row": src, "pair_index": i, "pair_id": f"{src}-{i}",
                              **meta, **p})
        rows.append({"source_row": src, **meta,
                     "alignment_raw": _nfc(str(block)) if has_block else "", "pairs": pairs})
    return rows


def main():
    rows = split_corpus()
    out_dir = paths.SENTENCE_ROWS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        (out_dir / f"row_{r['source_row']:04d}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(rows):,} đoạn, {sum(len(r['pairs']) for r in rows):,} cặp câu -> {out_dir}")


if __name__ == "__main__":
    main()
