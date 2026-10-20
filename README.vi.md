[English](README.md) | **Tiếng Việt**

# Mã nguồn bài VCL2026

Mã nguồn kèm bài *LLM-Based Named-Entity Recognition and Knowledge Graph Construction for
Sino-Vietnamese Feudal History*. Mã tái lập toàn bộ quy trình và các con số ở Mục 3–4 của bài:
trích xuất bằng Gemini 2.5 Flash, canonicalization, audit gold-free, đánh giá trên gold
3 người gán, capture–recapture, baseline có giám sát và các phép chấm của chuyên gia.

## 1. Cài đặt

Yêu cầu Python 3.9 trở lên.

```bash
cd code
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Mọi lệnh bên dưới chạy từ thư mục `code/`.

## 2. Dữ liệu

### 2.1. Đi kèm mã

`data/dictionary/`: từ điển âm Hán–Việt `hanviet.csv` và các dòng `kVietnamese` của Unihan
(Unicode 17.0.0), dùng cho audit gold-free. Ngoài ra `data/` có hướng dẫn gán nhãn
(`data/gold/ANNOTATION_GUIDE.md`) và prompt của Gemini 2.5 Pro
(`data/capture_recapture/prompt_gemini_pro_extraction.md`).

### 2.2. Dữ liệu gán nhãn (cung cấp theo yêu cầu)

Phiếu gán gold của 3 người, phiếu chuyên gia chấm, đầu vào và đầu ra Gemini 2.5 Pro đều chứa
câu của ngữ liệu CLC nên không phân phối kèm mã; liên hệ tác giả để nhận. Chép vào đúng vị trí:

| Thư mục | Tệp |
|---|---|
| `data/gold/` | `annotator_a.csv`, `annotator_b.csv`, `annotator_c.tsv`, `gold_majority_vote.tsv`, `llm_predictions.json`, `annotation_worksheet_blank.tsv`, `sample_manifest.json` |
| `data/capture_recapture/` | `input_gold_400_pairs.jsonl`, `gemini_pro_output_gold_400_pairs.json`, `input_corpus_sample_1200_pairs.jsonl`, `gemini_pro_output_corpus_sample_1200_pairs.json` |
| `data/triple_link_precision/` | `triples_human_judged.csv`, `hard_links_auto_confirmed.csv`, `hard_links_human_judged.csv` |
| `data/canon_purity/` | `canonical_clusters_human_judged.csv` |

### 2.3. Ngữ liệu CLC (cung cấp theo yêu cầu)

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

Các bước ở mục 3.2 tự tạo `corpus/1_sentence_pairs/` (cặp câu) và
`corpus/2_llm_output/gemini-2.5-flash/` (kết quả trích xuất). Bước trích xuất cần khoá API:

```bash
echo "GEMINI_API_KEY=<khoá của bạn>" > .env
```

## 3. Chạy

### 3.1. Cần dữ liệu gán nhãn (mục 2.2)

| Nội dung trong bài | Lệnh | Kết quả mong đợi |
|---|---|---|
| Bảng 4–5, IAA (Mục 4.4–4.5) | `python3 -m sino_viet_kg.evaluation.eval_ner` | micro F1 0.937 [95% CI 0.919–0.953], IAA trung bình 0.861 |
| Capture–recapture trên 400 cặp gold (Mục 4.5) | `python3 -m sino_viet_kg.evaluation.capture_recapture gold` | recall ước lượng 0.9783, recall đo trên gold 0.9777 |
| Precision bộ ba và liên kết (Mục 4.6) | `python3 -m sino_viet_kg.evaluation.triple_link_precision` | bộ ba 0.735 (trong / ngoài schema 0.767 / 0.640); liên kết 0.914 / 0.953 |
| Canonicalization purity (Mục 4.6) | `python3 -m sino_viet_kg.evaluation.canon_purity` | 0.762 |

### 3.2. Cần ngữ liệu CLC (mục 2.3)

Chạy theo thứ tự. Bước 6 cần thêm dữ liệu capture–recapture, bước 7 cần thêm
`data/gold/gold_majority_vote.tsv` (mục 2.2).

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

## 4. Cấu trúc mã

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
