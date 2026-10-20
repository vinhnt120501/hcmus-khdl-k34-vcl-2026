**English** | [Tiếng Việt](README.vi.md)

# Code for the VCL2026 paper

Code accompanying the paper *LLM-Based Named-Entity Recognition and Knowledge Graph Construction
for Sino-Vietnamese Feudal History*. It reproduces the whole pipeline and every number in
Sections 3–4 of the paper: extraction with Gemini 2.5 Flash, canonicalization, the gold-free
audit, evaluation against a three-annotator gold, capture–recapture, the supervised baselines,
and the expert judgments.

## 1. Installation

Requires Python 3.9 or later.

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

All commands below are run from the `code/` directory.

## 2. Data

### 2.1. Shipped with the code

`data/dictionary/`: the Sino-Vietnamese reading list `hanviet.csv` and the `kVietnamese` lines of
Unihan (Unicode 17.0.0), used by the gold-free audit. `data/` also contains the annotation
guideline (`data/gold/ANNOTATION_GUIDE.md`) and the Gemini 2.5 Pro prompt
(`data/capture_recapture/prompt_gemini_pro_extraction.md`).

### 2.2. Annotation data (available on request)

The three annotators' gold sheets, the expert judgment sheets, and the Gemini 2.5 Pro inputs and
outputs contain sentences of the CLC corpus, so they are not distributed with the code; contact
the author to obtain them. Copy them to:

| Directory | Files |
|---|---|
| `data/gold/` | `annotator_a.csv`, `annotator_b.csv`, `annotator_c.tsv`, `gold_majority_vote.tsv`, `llm_predictions.json`, `annotation_worksheet_blank.tsv`, `sample_manifest.json` |
| `data/capture_recapture/` | `input_gold_400_pairs.jsonl`, `gemini_pro_output_gold_400_pairs.json`, `input_corpus_sample_1200_pairs.jsonl`, `gemini_pro_output_corpus_sample_1200_pairs.json` |
| `data/triple_link_precision/` | `triples_human_judged.csv`, `hard_links_auto_confirmed.csv`, `hard_links_human_judged.csv` |
| `data/canon_purity/` | `canonical_clusters_human_judged.csv` |

### 2.3. CLC corpus (available on request)

The bilingual Đại Việt Sử Ký Toàn Thư corpus is provided by the Computational Linguistics Center
(CLC), University of Science, VNU-HCM, for research use; resources derived from it are not
redistributed either. Once you have the corpus, place the file at:

```
code/corpus/0_source/DVSKTT_aligned_at_sentence_level_20240520_concat_full_aligned_clc_preprocessed_manual_version.xlsx
```

To keep it elsewhere, point the environment variable `VCL_CORPUS_DIR` to the directory that
contains `0_source/`:

```bash
export VCL_CORPUS_DIR=/path/to/corpus
```

The steps in Section 3.2 create `corpus/1_sentence_pairs/` (sentence pairs) and
`corpus/2_llm_output/gemini-2.5-flash/` (extraction output). The extraction step needs an API key:

```bash
echo "GEMINI_API_KEY=<your key>" > .env
```

## 3. Running

### 3.1. With the annotation data (Section 2.2)

| Paper content | Command | Expected result |
|---|---|---|
| Tables 4–5, IAA (Sections 4.4–4.5) | `python3 -m sino_viet_kg.evaluation.eval_ner` | micro F1 0.937 [95% CI 0.919–0.953], mean IAA 0.861 |
| Capture–recapture on the 400 gold pairs (Section 4.5) | `python3 -m sino_viet_kg.evaluation.capture_recapture gold` | estimated recall 0.9783, recall against gold 0.9777 |
| Triple and link precision (Section 4.6) | `python3 -m sino_viet_kg.evaluation.triple_link_precision` | triples 0.735 (closed / off-schema 0.767 / 0.640); links 0.914 / 0.953 |
| Canonicalization purity (Section 4.6) | `python3 -m sino_viet_kg.evaluation.canon_purity` | 0.762 |

### 3.2. With the CLC corpus (Section 2.3)

Run in order. Step 6 also needs the capture–recapture data, and step 7 also needs
`data/gold/gold_majority_vote.tsv` (Section 2.2).

| Step | Paper content | Command | Expected result |
|---|---|---|---|
| 1 | Sentence-pair splitting | `python3 -m sino_viet_kg.extraction.sentence_pairs` | 2,578 rows, 20,867 sentence pairs |
| 2 | Extraction (Section 3.2) | `python3 -m sino_viet_kg.extraction.run` | 20,867 records |
| 3 | Canonicalization (Sections 3.3–3.4) | `python3 -m sino_viet_kg.canonicalization` | 14,719 / 14,094 entities; 15,457 candidates, 12,353 one-to-one links |
| 4 | Table 2, Figures 3–4 (Sections 4.1–4.2) | `python3 -m sino_viet_kg.resource_stats` | average degree 1.59 / 1.66 |
| 5 | Table 3 (Section 4.3) | `python3 -m sino_viet_kg.audit.run_all` | table written to `results/audit/05_summary/table3.md` |
| 6 | Capture–recapture on 1,200 pairs (Section 4.5) | `python3 -m sino_viet_kg.evaluation.capture_recapture corpus` | recall 0.982 [95% CI 0.978–0.986] |
| 7 | Baselines (Section 4.6) | `python3 -m sino_viet_kg.evaluation.baselines.zh_sikubert` then `python3 -m sino_viet_kg.evaluation.baselines.vi_phobert` | micro F1 0.632 / 0.605 |

Notes:

- Step 2 calls the API and incurs cost. Check the configuration first with `--dry-run` and try a
  small run with `--limit 40`. Results are cached by content, so rerunning the same command after
  an interruption continues where it stopped. Because LLM output is not deterministic, a new run
  may differ slightly from the paper's run; steps 3–7 reproduce the paper's numbers when run on
  the paper's extraction output (available on request together with the corpus).
- Step 7 should run on a GPU or Apple MPS; add `--cpu` for PhoBERT if memory is short.
- To redraw the 400-pair gold sample (seed 13): `python3 -m sino_viet_kg.evaluation.sample_gold --out <dir>`.

Code comments and console output are in Vietnamese.

## 4. Code layout

| Path | Contents |
|---|---|
| `sino_viet_kg/extraction/` | Sentence-pair splitting; Gemini 2.5 Flash calls in batches of 20 pairs, temperature 0.1, JSON mode; content-addressed cache |
| `sino_viet_kg/canonicalization.py` | Merges mentions into canonical entities, removes dangling triples, reduces links to a one-to-one set |
| `sino_viet_kg/resource_stats.py` | Table 2 statistics, label composition, degree distribution |
| `sino_viet_kg/audit/` | Gold-free audit: grounding, schema, reading dictionary, bilingual consistency |
| `sino_viet_kg/evaluation/` | Gold evaluation, capture–recapture, baselines, expert judgments |
| `sino_viet_kg/paths.py` | All data paths |
| `configs/gemini-2.5-flash.json` | Extraction parameters |
| `prompts/ner_with_relations.md` | Full extraction prompt, verbatim as run |
| `results/` | The paper's NER and baseline results (numbers only); reruns also write here (change with `VCL_RESULTS_DIR`) |
