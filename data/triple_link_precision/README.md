**English** | [Tiếng Việt](README.vi.md)

# Triple precision and hard-link precision (Section 4.6)

A Classical Chinese–Vietnamese expert reads the source sentence and fills in the `verdict`
column (1 = correct, 0 = wrong, empty = not judged). The sheets contain corpus sentences and are
available on request (README, Section 2.2). Run
`python3 -m sino_viet_kg.evaluation.triple_link_precision` to compute precision with 95% Wilson
intervals.

## Files

| File | Contents |
|---|---|
| `triples_human_judged.csv` | 200 triples with `evidence` and `sentence`. `verdict = 1` if the source sentence states (head, predicate, tail) in that direction. |
| `hard_links_auto_confirmed.csv` | Non-phonetic links where each side has only one candidate of that type in the sentence, so the alignment confirms them. |
| `hard_links_human_judged.csv` | The remaining 81 non-phonetic links (several candidates of the same type), judged by the expert. `verdict = 1` if both entities denote the same referent. |
