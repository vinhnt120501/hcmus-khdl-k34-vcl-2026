**English** | [Tiếng Việt](README.vi.md)

# Capture–recapture: corpus-scale recall estimate (Section 4.5)

Two independent extractors "capture" entities on the same sentences: Gemini 2.5 Flash (A, the
paper's extraction run) and Gemini 2.5 Pro (B). Mentions are matched on (side, normalized text,
label).

- Lincoln–Petersen estimate: N̂ = N_A · N_B / N_AB
- Recall of A: recall_A ≈ N_AB / N_B

Both extractors belong to the Gemini family, so their errors are correlated: N̂ is a lower bound
and recall_A an upper bound.

## Files

Except for the prompt, these files contain corpus sentences and are available on request
(README, Section 2.2).

| File | Contents |
|---|---|
| `prompt_gemini_pro_extraction.md` | Prompt for Gemini 2.5 Pro |
| `input_gold_400_pairs.jsonl` | The 400 gold sentence pairs (`pair_id`, `chinese`, `vietnamese`) |
| `gemini_pro_output_gold_400_pairs.json` | Gemini 2.5 Pro output on the 400 gold pairs |
| `input_corpus_sample_1200_pairs.jsonl` | Random sample of 1,200 of the 20,867 pairs |
| `gemini_pro_output_corpus_sample_1200_pairs.json` | Gemini 2.5 Pro output on the 1,200-pair sample |

## Running

```bash
python3 -m sino_viet_kg.evaluation.capture_recapture gold     # estimate vs. recall measured on gold
python3 -m sino_viet_kg.evaluation.capture_recapture corpus   # 1,200-pair sample, with 95% bootstrap CI
```

On the 400 gold pairs the estimate gives recall_A = 0.9783 against 0.9777 measured on gold
(difference +0.0006). On the 1,200-pair sample: N_A = 4,149, N_B = 3,899, N_AB = 3,830,
N̂ = 4,223.7, recall_A = 0.982 [95% CI 0.978–0.986], as reported in Section 4.5 of the paper.
