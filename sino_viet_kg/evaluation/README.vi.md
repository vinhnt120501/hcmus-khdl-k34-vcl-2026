[English](README.md) | **Tiếng Việt**

# sino_viet_kg.evaluation — Mục 4.4–4.6

| Module | Nội dung | Đầu vào |
|---|---|---|
| `sample_gold` | Lấy mẫu 400 cặp, phân tầng theo kỷ, seed 13 | ngữ liệu + lượt trích xuất |
| `eval_ner` | IAA; P/R/F1 vs gold đồng thuận ≥ 2/3, CI bootstrap, theo nhãn, theo phía (Bảng 4–5) | `data/gold/annotator_*`, `llm_predictions.json` |
| `capture_recapture` | Recall bằng Lincoln–Petersen, Flash vs Pro | `data/capture_recapture/` |
| `baselines.zh_sikubert`, `baselines.vi_phobert` | Baseline có giám sát trên nhãn silver | `data/gold/gold_majority_vote.tsv` |
| `triple_link_precision` | Precision bộ ba (trong / ngoài schema) và liên kết không phải phiên âm | `data/triple_link_precision/` |
| `canon_purity` | Độ thuần cụm canonical theo nhãn | `data/canon_purity/` |

Khoảng tin cậy: bootstrap 5,000 lần theo cặp câu (F1, recall); Wilson 95% (các tỉ lệ chuyên gia chấm).
