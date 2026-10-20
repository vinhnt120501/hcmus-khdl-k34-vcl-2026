"""Precision của bộ ba và của liên kết không phải phiên âm (Mục 4.6), từ phiếu chuyên gia chấm.

- Bộ ba: 200 mẫu, tách theo vị từ thuộc / không thuộc 24 vị từ của schema.
- Liên kết không phải phiên âm: tập mơ hồ (người chấm) và toàn bộ (gồm phần gióng hàng tự xác nhận).

    python3 -m sino_viet_kg.evaluation.triple_link_precision
"""
from sino_viet_kg import paths
from sino_viet_kg.evaluation.judged_csv import load, report
from sino_viet_kg.labels import PREDICATES

D = paths.TRIPLE_LINK_DIR


def main():
    report(load(D / "triples_human_judged.csv"), "Triple precision",
           group=lambda r: "closed-schema" if r["predicate"] in PREDICATES else "off-schema")
    ambiguous = load(D / "hard_links_human_judged.csv")
    report(ambiguous, "Non-phonetic link precision — ambiguous subset")
    report(load(D / "hard_links_auto_confirmed.csv") + ambiguous, "Non-phonetic link precision — all")


if __name__ == "__main__":
    main()
