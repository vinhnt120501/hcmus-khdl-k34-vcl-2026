"""Độ thuần của canonicalization (Mục 4.6): chuyên gia chấm 80 cụm nhiều mention.

verdict = 1 nếu mọi mention trong cụm cùng một referent, 0 nếu cụm gộp nhầm (homonym).

    python3 -m sino_viet_kg.evaluation.canon_purity
"""
from sino_viet_kg import paths
from sino_viet_kg.evaluation.judged_csv import load, report


def main():
    rows = load(paths.CANON_PURITY_DIR / "canonical_clusters_human_judged.csv")
    report(rows, "Canonicalization purity", group=lambda r: r["label"])


if __name__ == "__main__":
    main()
