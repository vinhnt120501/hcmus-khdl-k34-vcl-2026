"""Đọc phiếu chấm tay (CSV, cột `verdict(...)` = 1 đúng / 0 sai / trống chưa chấm) và tính tỉ lệ đúng."""
import collections
import csv
from pathlib import Path

from sino_viet_kg import paths
from sino_viet_kg.metrics import wilson_ci


def load(path: Path) -> list[dict]:
    with open(paths.require(path, "phiếu chấm"), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def verdict(row: dict) -> str:
    for k in row:
        if k.startswith("verdict"):
            return row[k].strip()
    return ""


def judged(rows: list[dict]) -> list[dict]:
    return [r for r in rows if verdict(r) in ("0", "1")]


def report(rows: list[dict], title: str, group=None) -> None:
    """In tỉ lệ đúng kèm Wilson 95% CI trên các dòng đã chấm; `group(row)` để tách theo nhóm."""
    done = judged(rows)
    n = len(done)
    p = sum(verdict(r) == "1" for r in done) / n
    lo, hi = wilson_ci(p, n)
    print(f"{title}: {p:.3f} [95% CI {lo:.3f}–{hi:.3f}] (n={n})")
    if group:
        by = collections.defaultdict(lambda: [0, 0])
        for r in done:
            by[group(r)][0] += 1
            by[group(r)][1] += verdict(r) == "1"
        for g in sorted(by, key=lambda x: -by[x][0]):
            tot, ok = by[g]
            print(f"    {g:<12} {ok}/{tot} = {ok/tot:.3f}")
