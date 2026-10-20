**English** | [Tiếng Việt](README.vi.md)

# sino_viet_kg.evaluation — Sections 4.4–4.6

| Module | Purpose | Input |
|---|---|---|
| `sample_gold` | Draws 400 pairs stratified by reign chapter, seed 13 | corpus + extraction output |
| `eval_ner` | IAA; P/R/F1 against the ≥ 2/3 majority gold with bootstrap CI, per label and per side (Tables 4–5) | `data/gold/annotator_*`, `llm_predictions.json` |
| `capture_recapture` | Lincoln–Petersen recall estimate, Flash vs Pro | `data/capture_recapture/` |
| `baselines.zh_sikubert`, `baselines.vi_phobert` | Supervised baselines trained on silver labels | `data/gold/gold_majority_vote.tsv` |
| `triple_link_precision` | Triple precision (closed / off-schema) and non-phonetic link precision | `data/triple_link_precision/` |
| `canon_purity` | Purity of canonical clusters per label | `data/canon_purity/` |

Confidence intervals: 5,000 pair-level bootstrap resamples (F1, recall); 95% Wilson intervals
(expert-judged proportions).
