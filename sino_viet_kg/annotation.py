"""Phiếu gán nhãn gold: cột `pair_id, side, [period,] sentence, gold_entities`.

Ô `gold_entities` có dạng `chuỗi:NHÃN; chuỗi:NHÃN`, câu không có thực thể ghi `NONE`,
ô trống = chưa gán (không tính). Tự nhận CSV (phẩy) hay TSV (tab).
"""
import collections
import csv
import json
from pathlib import Path

from sino_viet_kg import paths
from sino_viet_kg.labels import ENTITY_LABELS, SIDES
from sino_viet_kg.text import norm_mention


def parse_mentions(cell: str) -> list[tuple[str, str]]:
    """Ô gold -> [(chuỗi, nhãn)] giữ nguyên thứ tự, chuỗi chỉ strip."""
    out = []
    if cell.strip().upper() == "NONE":
        return out
    for chunk in cell.split(";"):
        chunk = chunk.strip()
        if ":" in chunk:
            text, label = chunk.rsplit(":", 1)
            label = label.strip().upper()
            if label in ENTITY_LABELS:
                out.append((text.strip(), label))
    return out


def parse_entities(cell: str) -> set[tuple[str, str]]:
    """Ô gold -> tập (chuỗi đã chuẩn hoá, nhãn)."""
    return {(norm_mention(t), l) for t, l in parse_mentions(cell) if norm_mention(t)}


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    """-> (header, rows) của phiếu CSV/TSV."""
    raw = paths.require(path, "phiếu gán nhãn").read_text(encoding="utf-8-sig").splitlines()
    delim = "\t" if "\t" in raw[0] else ","
    rows = list(csv.reader(raw, delimiter=delim))
    return [h.strip() for h in rows[0]], rows[1:]


def load_worksheet(path: Path) -> dict:
    """-> {(pair_id, side): tập (chuỗi, nhãn)}; chỉ các dòng đã gán."""
    hdr, rows = read_rows(path)
    gi, pi, si = hdr.index("gold_entities"), hdr.index("pair_id"), hdr.index("side")
    gold = {}
    for r in rows:
        if len(r) <= gi or not r[gi].strip():
            continue
        gold[(r[pi].strip(), r[si].strip())] = parse_entities(r[gi])
    return gold


def load_sentences(path: Path, side: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """-> [(câu, [(chuỗi, nhãn)])] cho một phía, chỉ các dòng đã gán."""
    hdr, rows = read_rows(path)
    gi, si, se = hdr.index("gold_entities"), hdr.index("side"), hdr.index("sentence")
    out = []
    for r in rows:
        if len(r) <= gi or r[si] != side or not r[gi].strip():
            continue
        out.append((r[se], parse_mentions(r[gi])))
    return out


def annotator_files(gold_dir: Path = paths.GOLD_DIR) -> list[Path]:
    files = sorted(Path(gold_dir).glob("annotator_*"))
    if not files:
        paths.require(Path(gold_dir) / "annotator_a.csv", "phiếu của người gán")
    return files


def annotator_name(path: Path) -> str:
    return Path(path).stem.replace("annotator_", "")


def majority_vote(annots: list[dict], min_votes: int = 2) -> dict:
    """Gold đồng thuận: mention được ít nhất `min_votes` người gán."""
    consensus = {}
    for k in set().union(*[set(a) for a in annots]):
        cnt = collections.Counter(m for a in annots for m in a.get(k, set()))
        consensus[k] = {m for m, c in cnt.items() if c >= min_votes}
    return consensus


def load_predictions(path: Path = paths.GOLD_PREDICTIONS) -> dict:
    """llm_predictions.json -> {(pair_id, side): tập (chuỗi đã chuẩn hoá, nhãn)} của LLM."""
    raw = json.loads(paths.require(path, "dự đoán LLM trên mẫu gold").read_text(encoding="utf-8"))
    return {(pid, side): {(norm_mention(t), l) for t, l in sides.get(side, [])}
            for pid, sides in raw.items() for side in SIDES}
