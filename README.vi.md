[English](README.md) | **Tiếng Việt**

# Tài nguyên thực thể định danh Hán–Việt cho *Đại Việt Sử Ký Toàn Thư*

Tài nguyên thực thể định danh và đồ thị tri thức song ngữ cho lịch sử phong kiến Việt Nam, xây
dựng từ bộ sử song ngữ chữ Hán – tiếng Việt *Đại Việt Sử Ký Toàn Thư* (20,867 cặp câu đã gióng
hàng). Mỗi phía được gán 5 loại thực thể (người, địa danh, chức danh, sự kiện, triều đại) cùng
quan hệ giữa chúng, và hai phía được nối bằng liên kết liên ngôn ngữ như 黎利 ↔ Lê Lợi.

Tài nguyên được trích xuất bằng mô hình ngôn ngữ lớn (Gemini 2.5 Flash), kiểm chứng không cần gold
(cấu trúc, lược đồ, từ điển âm Hán–Việt, nhất quán song ngữ), rồi đối chiếu với mẫu gold do ba
người gán nhãn.

**Điểm chính**

- 14,719 thực thể chữ Hán và 14,094 thực thể tiếng Việt, 11,666 / 11,698 bộ ba quan hệ, 12,353 liên kết liên ngôn ngữ một–một.
- Nhận diện thực thể: micro F1 0.937 so với gold, recall ước lượng 0.982 (cận trên).
- Liên kết liên ngôn ngữ: precision 0.953 trên các liên kết không theo phiên âm; lớp quan hệ ở mức khám phá (precision bộ ba 0.735).
- Mọi con số trong bài đều tái lập được bằng các lệnh bên dưới.

Bài báo: *LLM-Based Named-Entity Recognition and Knowledge Graph Construction for Sino-Vietnamese
Feudal History*, Hội thảo Quốc gia lần thứ 4 về Ngôn ngữ học Tính toán (VCL 2026).

## 1. Tổng quan

Tài nguyên gồm hai đồ thị tri thức có kiểu dựng từ bộ sử song ngữ *Đại Việt Sử Ký Toàn Thư*,
một đồ thị chữ Hán và một đồ thị tiếng Việt, nối với nhau bằng liên kết liên ngôn ngữ giữa các
mention cùng chỉ một đối tượng (ví dụ 黎利 ↔ Lê Lợi).

![Hình 1. Tài nguyên thực thể định danh song ngữ](docs/figures/fig1_resource.png)

*Hình 1. Mũi tên liền là quan hệ trong từng đồ thị; liên kết đứt `same_as` là tương đương liên
ngôn ngữ. Nhiều tên tiếng Việt là âm Hán Việt của dạng chữ Hán (升龍 → Thăng Long); audit
gold-free dùng chính quy luật này để kiểm tra liên kết.*

Quy trình chạy một lượt qua toàn bộ bộ sử:

![Hình 2. Quy trình xây dựng tài nguyên](docs/figures/fig2_pipeline.png)

*Hình 2. Gemini 2.5 Flash đọc từng cặp câu đã gióng hàng theo một lược đồ cố định, gán 5 loại
thực thể (PER, LOC, TIT, EVT, DYNA), bộ ba quan hệ và liên kết liên ngôn ngữ ở mỗi phía. Hai đồ
thị được canonicalization, liên kết được lọc còn tập một–một, rồi kết quả được chuyên gia và
audit gold-free bằng từ điển âm kiểm tra.*

| Bước | Mục trong bài | Mã |
|---|---|---|
| Tách cặp câu và trích xuất bằng LLM | 3.2 | `sino_viet_kg/extraction/` |
| Canonicalization và tập liên kết một–một | 3.3–3.4 | `sino_viet_kg/canonicalization.py` |
| Thống kê tài nguyên | 4.1–4.2 | `sino_viet_kg/resource_stats.py` |
| Audit gold-free | 3.5, 4.3 | `sino_viet_kg/audit/` |
| Gold người gán, capture–recapture, baseline, chấm của chuyên gia | 4.4–4.6 | `sino_viet_kg/evaluation/` |

## 2. Kết quả

Mọi con số dưới đây là kết quả trong bài; lệnh ghi ở mỗi phần dùng để tái lập (yêu cầu dữ liệu
xem mục 4).

### 2.1. Ví dụ: một cặp câu đi qua quy trình (Bảng 1)

Đầu vào (cặp `3-2`):

> 神農氏之後帝明得鶩僊女而生涇陽王是爲百粤始祖。
>
> Con cháu Thần Nông thị là Đế Minh lấy con gái Vụ Tiên mà sinh Kinh Dương Vương, tức là thuỷ tổ của Bách Việt.

Đầu ra của LLM (một bản ghi JSON cho mỗi cặp):

<table>
  <tr><th></th><th>Chữ Hán</th><th>Tiếng Việt</th></tr>
  <tr><td>PER</td><td>神農氏, 帝明, 鶩僊女, 涇陽王</td><td>Thần Nông thị, Đế Minh, Vụ Tiên, Kinh Dương Vương</td></tr>
  <tr><td>LOC</td><td>百粤</td><td>Bách Việt</td></tr>
  <tr><td>Bộ ba</td><td>(帝明, descendant_of, 神農氏); (帝明, spouse_of, 鶩僊女); (帝明, father_of, 涇陽王); (涇陽王, other_relation, 百粤)</td><td>cùng bốn bộ ba ở phía tiếng Việt</td></tr>
  <tr><td>Liên kết (độ tin)</td><td colspan="2">神農氏↔Thần Nông thị (1.0); 帝明↔Đế Minh (1.0); 鶩僊女↔Vụ Tiên (0.90); 涇陽王↔Kinh Dương Vương (1.0); 百粤↔Bách Việt (1.0)</td></tr>
</table>

Đầu ra sau canonicalization (id số nguyên toàn cục; id tiếng Việt bắt đầu từ 14,719):

```text
entities (zh): 73 神農氏, 30 帝明, 33 鶩僊女, 74 涇陽王, 10 百粤
entities (vi): 14792 thần nông thị, 14750 đế minh, 14753 vụ tiên, 14793 kinh dương vương, 14728 bách việt
relations:     15 descendant_of, 20 father_of, 37 other_relation, 53 spouse_of
triples (zh):  30 15 73 | 30 53 33 | 30 20 74 | 74 37 10      (head rel tail)
links:         (73, 14792) (30, 14750) (33, 14753) (74, 14793) (10, 14728)
```

### 2.2. Thống kê tài nguyên (Bảng 2, Hình 3–4)

Lệnh: `python3 -m sino_viet_kg.canonicalization` rồi `python3 -m sino_viet_kg.resource_stats`

| Chỉ số | Chữ Hán | Tiếng Việt |
|---|---:|---:|
| Thực thể | 14,719 | 14,094 |
| Bộ ba | 11,666 | 11,698 |
| Bậc trung bình | 1.59 | 1.66 |
| Loại quan hệ | 62 | 62 |
| Thực thể cô lập | ≈ 33% | ≈ 33% |
| Liên kết liên ngôn ngữ (một–một) | 12,353 | 12,353 |

Canonicalization gộp 75,732 mention thô thành 28,813 thực thể (tỉ lệ 2.6:1), loại 522 / 505 bộ
ba dangling, và lọc 35,716 đề xuất liên kết thô (15,457 cặp ứng viên khác nhau) còn 12,353 liên
kết một–một.

| Tỉ lệ nhãn (Hình 3) | Phân bố bậc thực thể (Hình 4) |
|---|---|
| ![Hình 3](docs/figures/fig3_label_composition.png) | ![Hình 4](docs/figures/fig4_degree_distribution.png) |
| Người chiếm đa số (45.2%), tiếp đến địa danh (21.3%) và chức danh (17.7%); 5 loại trong lược đồ chiếm 98.8% số mention. | Khoảng một phần ba thực thể có bậc 0 và hơn 40% có bậc 1: trích xuất theo từng câu tạo ra đồ thị thưa. |

### 2.3. Audit gold-free (Bảng 3)

Lệnh: `python3 -m sino_viet_kg.audit.run_all` (ghi ra `results/audit/05_summary/table3.md`).
Tính trên toàn bộ kết quả trích xuất trước canonicalization (20,867 cặp câu); chỉ dùng từ điển
âm, không dùng nhãn gold và không dùng embedding.

| Phép kiểm tra | Kết quả |
|---|---:|
| Entity grounding | 97.5% |
| Label validity | 98.8% |
| Label consistency | 94.8% |
| Predicate validity | 99.5% |
| Triple-ID integrity | 96.1% |
| Entity recall (capture–recapture, mục 2.5) | 98.2% |
| Liên kết được từ điển xác nhận ngữ âm | 68.8% |
| Proxy precision (từ điển làm chuẩn) | 98.8% |
| Proxy recall miss | 1.3% |
| Alignment symmetry (zh / vi) | 94.5 / 93.9% |
| Triple parallelism (zh / vi) | 98.0 / 98.6% |

Từ điển âm là `hanviet.csv`, các chữ không có trong đó lấy âm `kVietnamese` của Unihan; nếu chỉ
dùng Unihan thì chỉ xác nhận được 45.0% số liên kết.

### 2.4. Đánh giá trên gold người gán (Bảng 4–5)

Lệnh: `python3 -m sino_viet_kg.evaluation.eval_ner`. Ba người gán độc lập trên mẫu 400 cặp câu
phân tầng; một thực thể là gold khi ít nhất 2/3 người gán đánh dấu.

| Loại | P | R | F1 |
|---|---:|---:|---:|
| PER | 0.899 | 0.998 | 0.946 |
| LOC | 0.933 | 0.961 | 0.947 |
| TIT | 0.881 | 0.948 | 0.913 |
| EVT | 0.963 | 0.988 | 0.975 |
| DYNA | 0.985 | 0.931 | 0.957 |
| **Micro (tất cả)** | **0.899** | **0.978** | **0.937** |

- Số đếm: TP = 1,313, FP = 147, FN = 30; micro F1 95% CI [0.919, 0.953]; macro F1 0.948.
- Theo phía: chữ Hán 0.966, tiếng Việt 0.907.
- Độ đồng thuận giữa người gán (F1 khớp chính xác ở mức mention, theo cặp): a–b 0.970, a–c 0.795, b–c 0.820, trung bình 0.861.

### 2.5. Ước lượng recall bằng capture–recapture (Mục 4.5)

Lệnh: `python3 -m sino_viet_kg.evaluation.capture_recapture gold` (400 cặp gold) và
`... capture_recapture corpus` (mẫu 1,200 cặp). Bộ trích A là Gemini 2.5 Flash, bộ trích B là
Gemini 2.5 Pro; N̂ = N_A·N_B / N_AB và recall_A = N_AB / N_B.

| Mẫu | N_A | N_B | N_AB | N̂ | Recall ước lượng |
|---|---:|---:|---:|---:|---:|
| 400 cặp gold | 1,460 | 1,380 | 1,350 | 1,492.4 | 0.9783 (đo trên gold: 0.9777) |
| Mẫu 1,200 cặp | 4,149 | 3,899 | 3,830 | 4,223.7 | 0.982 [0.978–0.986] |

Hai bộ trích cùng họ Gemini nên lỗi có thể tương quan; vì vậy recall là cận trên.

### 2.6. Chất lượng theo bốn lớp của đồ thị (Bảng 6)

| Lớp | Chỉ số (cách đo) | Điểm | Lệnh |
|---|---|---:|---|
| Thực thể | micro F1 so với gold | 0.937 | `evaluation.eval_ner` |
| Thực thể | recall, capture–recapture | 0.982 | `evaluation.capture_recapture corpus` |
| Thực thể | baseline có giám sát (zh / vi) | 0.632 / 0.605 | `evaluation.baselines.zh_sikubert`, `...vi_phobert` |
| Liên kết | precision, liên kết không theo phiên âm | 0.953 | `evaluation.triple_link_precision` |
| Quan hệ | precision bộ ba (chuyên gia chấm) | 0.735 | `evaluation.triple_link_precision` |
| Canonicalization | độ thuần cụm (chuyên gia chấm) | 0.762 | `evaluation.canon_purity` |

Chi tiết phía sau bảng:

| Baseline theo loại (F1) | PER | LOC | TIT | EVT | DYNA | Micro |
|---|---:|---:|---:|---:|---:|---:|
| SikuBERT (zh, BIO mức ký tự) | 0.700 | 0.744 | 0.487 | 0.426 | 0.746 | 0.632 |
| PhoBERT (vi, BIO mức từ) | 0.791 | 0.635 | 0.330 | 0.382 | 0.575 | 0.605 |

- Liên kết: 0.914 trên nhóm nhập nhằng, 0.953 [0.907–0.977] trên toàn bộ liên kết không theo phiên âm.
- Bộ ba: 0.735 [0.670–0.791] trên 200 bộ ba; 0.767 với 24 vị từ trong lược đồ, 0.640 với vị từ ngoài lược đồ.
- Độ thuần: 0.762 [0.659–0.842] trên 80 cụm; PER 0.857, LOC 0.944, DYNA 1.0, TIT 0.333, EVT 0.333
  (chức quan lặp lại và năm can chi bị gộp thành các nút mang tính "loại").

## 3. Cài đặt

Yêu cầu Python 3.9 trở lên.

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Mọi lệnh bên dưới chạy từ thư mục `code/`.

## 4. Dữ liệu

### 4.1. Đi kèm mã

`data/dictionary/`: từ điển âm Hán–Việt `hanviet.csv` và các dòng `kVietnamese` của Unihan
(Unicode 17.0.0), dùng cho audit gold-free. Ngoài ra `data/` có hướng dẫn gán nhãn
(`data/gold/ANNOTATION_GUIDE.md`) và prompt của Gemini 2.5 Pro
(`data/capture_recapture/prompt_gemini_pro_extraction.md`).

### 4.2. Dữ liệu gán nhãn (cung cấp theo yêu cầu)

Phiếu gán gold của 3 người, phiếu chuyên gia chấm, đầu vào và đầu ra Gemini 2.5 Pro đều chứa
câu của ngữ liệu CLC nên không phân phối kèm mã; liên hệ tác giả để nhận. Chép vào đúng vị trí:

| Thư mục | Tệp |
|---|---|
| `data/gold/` | `annotator_a.csv`, `annotator_b.csv`, `annotator_c.tsv`, `gold_majority_vote.tsv`, `llm_predictions.json`, `annotation_worksheet_blank.tsv`, `sample_manifest.json` |
| `data/capture_recapture/` | `input_gold_400_pairs.jsonl`, `gemini_pro_output_gold_400_pairs.json`, `input_corpus_sample_1200_pairs.jsonl`, `gemini_pro_output_corpus_sample_1200_pairs.json` |
| `data/triple_link_precision/` | `triples_human_judged.csv`, `hard_links_auto_confirmed.csv`, `hard_links_human_judged.csv` |
| `data/canon_purity/` | `canonical_clusters_human_judged.csv` |

### 4.3. Ngữ liệu CLC (cung cấp theo yêu cầu)

Ngữ liệu song ngữ Đại Việt Sử Ký Toàn Thư do Trung tâm Ngôn ngữ học Tính toán (CLC), Trường
ĐH Khoa học Tự nhiên, ĐHQG-HCM cung cấp cho mục đích nghiên cứu; tài nguyên sinh ra từ ngữ liệu
cũng không được phân phối lại. Sau khi có ngữ liệu, đặt tệp vào:

```
code/corpus/0_source/DVSKTT_aligned_at_sentence_level_20240520_concat_full_aligned_clc_preprocessed_manual_version.xlsx
```

Nếu để ở chỗ khác, đặt biến môi trường `VCL_CORPUS_DIR` trỏ tới thư mục chứa `0_source/`:

```bash
export VCL_CORPUS_DIR=/đường/dẫn/tới/corpus
```

Các bước ở mục 5.2 tự tạo `corpus/1_sentence_pairs/` (cặp câu) và
`corpus/2_llm_output/gemini-2.5-flash/` (kết quả trích xuất). Bước trích xuất cần khoá API:

```bash
echo "GEMINI_API_KEY=<khoá của bạn>" > .env
```

## 5. Chạy

### 5.1. Cần dữ liệu gán nhãn (mục 4.2)

| Nội dung trong bài | Lệnh | Kết quả mong đợi |
|---|---|---|
| Bảng 4–5, IAA (Mục 4.4–4.5) | `python3 -m sino_viet_kg.evaluation.eval_ner` | micro F1 0.937 [95% CI 0.919–0.953], IAA trung bình 0.861 |
| Capture–recapture trên 400 cặp gold (Mục 4.5) | `python3 -m sino_viet_kg.evaluation.capture_recapture gold` | recall ước lượng 0.9783, recall đo trên gold 0.9777 |
| Precision bộ ba và liên kết (Mục 4.6) | `python3 -m sino_viet_kg.evaluation.triple_link_precision` | bộ ba 0.735 (trong / ngoài schema 0.767 / 0.640); liên kết 0.914 / 0.953 |
| Canonicalization purity (Mục 4.6) | `python3 -m sino_viet_kg.evaluation.canon_purity` | 0.762 |

### 5.2. Cần ngữ liệu CLC (mục 4.3)

Chạy theo thứ tự. Bước 6 cần thêm dữ liệu capture–recapture, bước 7 cần thêm
`data/gold/gold_majority_vote.tsv` (mục 4.2).

| Bước | Nội dung trong bài | Lệnh | Kết quả mong đợi |
|---|---|---|---|
| 1 | Tách cặp câu | `python3 -m sino_viet_kg.extraction.sentence_pairs` | 2,578 đoạn, 20,867 cặp câu |
| 2 | Trích xuất (Mục 3.2) | `python3 -m sino_viet_kg.extraction.run` | 20,867 bản ghi |
| 3 | Canonicalization (Mục 3.3–3.4) | `python3 -m sino_viet_kg.canonicalization` | 14,719 / 14,094 thực thể; 15,457 ứng viên, 12,353 liên kết một–một |
| 4 | Bảng 2, Hình 3–4 (Mục 4.1–4.2) | `python3 -m sino_viet_kg.resource_stats` | bậc trung bình 1.59 / 1.66 |
| 5 | Bảng 3 (Mục 4.3) | `python3 -m sino_viet_kg.audit.run_all` | bảng ghi ở `results/audit/05_summary/table3.md` |
| 6 | Capture–recapture 1,200 cặp (Mục 4.5) | `python3 -m sino_viet_kg.evaluation.capture_recapture corpus` | recall 0.982 [95% CI 0.978–0.986] |
| 7 | Baseline (Mục 4.6) | `python3 -m sino_viet_kg.evaluation.baselines.zh_sikubert` rồi `python3 -m sino_viet_kg.evaluation.baselines.vi_phobert` | micro F1 0.632 / 0.605 |

Ghi chú:

- Bước 2 gọi API và tốn chi phí. Kiểm tra cấu hình trước bằng `--dry-run`, chạy thử bằng
  `--limit 40`. Kết quả được đệm theo nội dung, nên nếu dừng giữa chừng thì chạy lại cùng lệnh
  sẽ tiếp phần còn thiếu. Do LLM không tất định, lượt chạy mới có thể khác đôi chút với lượt
  của bài; các bước 3–7 cho đúng số trong bài khi chạy trên kết quả trích xuất của bài
  (cung cấp theo yêu cầu cùng ngữ liệu).
- Bước 7 nên chạy trên GPU hoặc Apple MPS; thêm `--cpu` cho PhoBERT nếu thiếu bộ nhớ.
- Lấy lại mẫu gold 400 cặp (seed 13): `python3 -m sino_viet_kg.evaluation.sample_gold --out <thư mục>`.

## 6. Cấu trúc mã

| Đường dẫn | Nội dung |
|---|---|
| `sino_viet_kg/extraction/` | Tách cặp câu; gọi Gemini 2.5 Flash theo lô 20 cặp, temperature 0.1, chế độ JSON; đệm theo nội dung |
| `sino_viet_kg/canonicalization.py` | Gộp mention thành thực thể canonical, loại bộ ba dangling, lọc liên kết một–một |
| `sino_viet_kg/resource_stats.py` | Thống kê Bảng 2, tỉ lệ nhãn, phân bố bậc |
| `sino_viet_kg/audit/` | Audit gold-free: grounding, schema, từ điển âm, nhất quán song ngữ |
| `sino_viet_kg/evaluation/` | Gold, capture–recapture, baseline, các phép chấm của chuyên gia |
| `sino_viet_kg/paths.py` | Mọi đường dẫn dữ liệu |
| `configs/gemini-2.5-flash.json` | Tham số trích xuất |
| `prompts/ner_with_relations.md` | Prompt trích xuất đầy đủ, nguyên văn bản đã chạy |
| `results/` | Kết quả đánh giá NER và baseline của bài (chỉ số liệu); kết quả chạy lại cũng ghi vào đây (đổi bằng `VCL_RESULTS_DIR`) |
| `docs/figures/` | Hình 1–4 của bài dùng trong README này |

## 7. Trích dẫn

```bibtex
@inproceedings{nguyen2026sinovietkg,
  title     = {{LLM}-Based Named-Entity Recognition and Knowledge Graph Construction for Sino-Vietnamese Feudal History},
  author    = {Nguyen, Thanh Vinh},
  booktitle = {Proceedings of the 4th National Workshop on Computational Linguistics (VCL 2026)},
  year      = {2026}
}
```
