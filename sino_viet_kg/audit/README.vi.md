[English](README.md) | **Tiếng Việt**

# sino_viet_kg.audit — Audit gold-free (Mục 3.5, 4.3 — Bảng 3)

Chạy trên toàn bộ kết quả trích xuất trước canonicalization (20,867 cặp câu). Không dùng
embedding, nhãn gold hay mô hình học.

```bash
python3 -m sino_viet_kg.audit.run_all
```

| Bước | Module | Chỉ số trong Bảng 3 |
|---|---|---|
| 00 | `step00_load` | gộp `row_*.json` thành `pairs.jsonl` |
| 01 | `step01_structural` | entity grounding, label validity, label consistency, predicate validity, triple-ID integrity |
| 02 | `step02_dictionary` | links phonetically confirmed (từ điển âm Hán–Việt) |
| 03 | `step03_recall` | proxy precision, proxy recall miss |
| 04 | `step04_consistency` | alignment symmetry, triple parallelism |
| 05 | `step05_summary` | ghi Bảng 3 ra `results/audit/05_summary/table3.md` |

Từ điển âm (`reading_dictionary.py`) dùng `data/dictionary/hanviet.csv` và trường `kVietnamese`
của Unihan (`data/dictionary/unihan_kvietnamese.txt`). Dòng recall (capture–recapture) của Bảng 3 tính bằng
`python3 -m sino_viet_kg.evaluation.capture_recapture corpus`.
