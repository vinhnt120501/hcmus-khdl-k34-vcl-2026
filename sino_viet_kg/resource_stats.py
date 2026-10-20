"""Thống kê tài nguyên (Mục 4.1–4.2): Bảng 2, tỉ lệ nhãn (Hình 3), phân bố bậc (Hình 4).

Đọc các tệp TSV do `sino_viet_kg.canonicalization` ghi ra và kết quả trích xuất thô.

    python3 -m sino_viet_kg.resource_stats
"""
import argparse
import collections
from pathlib import Path

from sino_viet_kg import paths
from sino_viet_kg.kg import entities, iter_extractions
from sino_viet_kg.labels import ENTITY_LABELS, SIDES


def _read_tsv(path: Path) -> list[list[str]]:
    return [line.rstrip("\n").split("\t") for line in open(path, encoding="utf-8") if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon", default=str(paths.CANON_OUT_DIR), help="thư mục TSV của canonicalization")
    args = ap.parse_args()
    d = Path(args.canon)

    n_links = len(_read_tsv(d / "links.tsv"))
    n_rels = len(_read_tsv(d / "relations.tsv"))
    print("Bảng 2\n| | zh | vi |\n|---|---|---|")
    stats = {}
    for side in SIDES:
        ents = [r[0] for r in _read_tsv(d / f"entities_{side}.tsv")]
        triples = _read_tsv(d / f"triples_{side}.tsv")
        degree = collections.Counter({e: 0 for e in ents})
        for h, _, t in triples:
            degree[h] += 1
            degree[t] += 1
        stats[side] = (len(ents), len(triples), degree)
    for name, fn in [
        ("Entities", lambda e, t, deg: f"{e:,}"),
        ("Triples", lambda e, t, deg: f"{t:,}"),
        ("Avg. degree (2|T|/|E|)", lambda e, t, deg: f"{2 * t / e:.2f}"),
        ("Relation types", lambda e, t, deg: f"{n_rels}"),
        ("Isolated entities", lambda e, t, deg: f"{100 * sum(v == 0 for v in deg.values()) / e:.1f}%"),
        ("Cross-lingual links", lambda e, t, deg: f"{n_links:,}"),
    ]:
        print(f"| {name} | {fn(*stats['zh'])} | {fn(*stats['vi'])} |")

    print("\nHình 4 — phân bố bậc thực thể (% thực thể)")
    for side in SIDES:
        n, _, deg = stats[side]
        dist = collections.Counter(min(v, 5) for v in deg.values())
        print(f"  {side}: " + "  ".join(f"{'≥5' if k == 5 else k}: {100 * dist[k] / n:.1f}%"
                                         for k in range(6)))

    labels = collections.Counter()
    for ex in iter_extractions():
        for side in SIDES:
            for e in entities(ex, side):
                if e.get("text", "").strip():
                    labels[e.get("label", "").strip().upper()] += 1
    total = sum(labels.values())
    print(f"\nHình 3 — tỉ lệ nhãn trên {total:,} mention (gộp hai phía)")
    for lab in ENTITY_LABELS:
        print(f"  {lab:<5} {100 * labels[lab] / total:.1f}%")
    other = total - sum(labels[lab] for lab in ENTITY_LABELS)
    print(f"  other {100 * other / total:.1f}%")


if __name__ == "__main__":
    main()
