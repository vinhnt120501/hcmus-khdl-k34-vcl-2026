**English** | [Tiếng Việt](ANNOTATION_GUIDE.vi.md)

# Gold annotation guideline for Sino-Vietnamese NER

Translated from the Vietnamese guideline the annotators followed (`ANNOTATION_GUIDE.vi.md`).

The independently annotated gold set measures the NER F1 of the resource (Sections 4.4–4.5).
The sample has 400 sentence pairs stratified by reign chapter (`annotation_worksheet_blank.tsv`),
annotated by 3 annotators (`annotator_a.csv`, `annotator_b.csv`, `annotator_c.tsv`); the final
gold is the ≥ 2/3 majority (`gold_majority_vote.tsv`). These files contain corpus sentences and
are available on request.

## Procedure
1. Open `annotation_worksheet_blank.tsv` (tab-separated).
2. Each row is one sentence (`side=zh`: Literary Chinese, `side=vi`: Vietnamese translation).
   Annotate independently, without looking at the LLM predictions.
3. Fill in the `gold_entities` column as `string:LABEL; string:LABEL; ...`
   - `string` is the surface form of the entity exactly as it appears in the sentence.
   - A sentence with no entity is marked `NONE`; an empty cell means "not annotated" and is skipped.
4. Save as `data/gold/annotator_<name>.tsv`; score all three annotators with
   `python3 -m sino_viet_kg.evaluation.eval_ner`.

## Labels
| Label | Meaning | Chinese examples | Vietnamese examples |
|---|---|---|---|
| `PER`  | Person | 黎利, 吳士連 | Lê Lợi, Ngô Sĩ Liên |
| `LOC`  | Location | 升龍, 土磊鄉 | Thăng Long, hương Thổ Lỗi |
| `TIT`  | Title / office | 元妃, 朝列大夫 | Nguyên Phi, Triều Liệt Đại Phu |
| `EVT`  | Event (including the dating expressions that anchor it) | 壬戌, 秋七月 | Nhâm Tuất, mùa thu tháng 7 |
| `DYNA` | Dynasty | 周, 宋 | nhà Chu, nhà Tống |

## Span conventions
- Copy the surface form as it appears; do not add or remove spaces, do not normalize.
- Keep Vietnamese case and diacritics (scoring requires an exact, case-sensitive match).
- A name with an attached title (e.g. `臣吳士連`) is split into two mentions: `吳士連:PER` and `臣:TIT`.
- A string repeated within a sentence is recorded once (scoring uses the set of mentions per sentence).
- Dating expressions anchoring an event (sexagenary terms, "mùa thu tháng 7") are labeled `EVT`.
