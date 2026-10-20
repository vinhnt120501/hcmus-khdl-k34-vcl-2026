**English** | [Tiếng Việt](README.vi.md)

# sino_viet_kg.audit — Gold-free audit (Sections 3.5, 4.3; Table 3)

Runs over the full extraction before canonicalization (20,867 sentence pairs). Uses no
embeddings, no gold labels and no learned model.

```bash
python3 -m sino_viet_kg.audit.run_all
```

| Step | Module | Table 3 metrics |
|---|---|---|
| 00 | `step00_load` | merges `row_*.json` into `pairs.jsonl` |
| 01 | `step01_structural` | entity grounding, label validity, label consistency, predicate validity, triple-ID integrity |
| 02 | `step02_dictionary` | links phonetically confirmed (Sino-Vietnamese reading dictionary) |
| 03 | `step03_recall` | proxy precision, proxy recall miss |
| 04 | `step04_consistency` | alignment symmetry, triple parallelism |
| 05 | `step05_summary` | writes Table 3 to `results/audit/05_summary/table3.md` |

The reading dictionary (`reading_dictionary.py`) uses `data/dictionary/hanviet.csv` and the
`kVietnamese` field of Unihan (`data/dictionary/unihan_kvietnamese.txt`). The recall row of
Table 3 (capture–recapture) is computed with
`python3 -m sino_viet_kg.evaluation.capture_recapture corpus`.
