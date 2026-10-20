[English](ANNOTATION_GUIDE.md) | **Tiếng Việt**

# Hướng dẫn gán nhãn gold cho NER Hán–Việt

Tập gold do người gán độc lập dùng để đo NER-F1 của tài nguyên (Mục 4.4–4.5).
Mẫu gồm 400 cặp câu phân tầng theo kỷ/triều (`annotation_worksheet_blank.tsv`), do 3 người gán
(`annotator_a.csv`, `annotator_b.csv`, `annotator_c.tsv`); gold cuối là đồng thuận ≥ 2/3
(`gold_majority_vote.tsv`). Các tệp này chứa câu của ngữ liệu nên cung cấp theo yêu cầu.

## Quy trình
1. Mở `annotation_worksheet_blank.tsv` (phân tách bằng Tab).
2. Mỗi dòng là một câu (`side=zh`: Hán văn, `side=vi`: bản dịch tiếng Việt).
   Gán độc lập, không xem dự đoán của LLM.
3. Điền cột `gold_entities` theo cú pháp `chuỗi:NHÃN; chuỗi:NHÃN; ...`
   - `chuỗi` là mặt chữ của thực thể đúng như trong câu.
   - Câu không có thực thể ghi `NONE`; ô trống được hiểu là chưa gán và bị bỏ qua.
4. Lưu thành `data/gold/annotator_<tên>.tsv`; chấm cả 3 người gán bằng
   `python3 -m sino_viet_kg.evaluation.eval_ner`.

## Bộ nhãn
| Nhãn | Nghĩa | Ví dụ Hán | Ví dụ Việt |
|---|---|---|---|
| `PER`  | Nhân danh | 黎利, 吳士連 | Lê Lợi, Ngô Sĩ Liên |
| `LOC`  | Địa danh | 升龍, 土磊鄉 | Thăng Long, hương Thổ Lỗi |
| `TIT`  | Tước hiệu / chức quan | 元妃, 朝列大夫 | Nguyên Phi, Triều Liệt Đại Phu |
| `EVT`  | Sự kiện (gồm mốc thời gian của sự kiện) | 壬戌, 秋七月 | Nhâm Tuất, mùa thu tháng 7 |
| `DYNA` | Triều đại | 周, 宋 | nhà Chu, nhà Tống |

## Quy ước biên
- Giữ nguyên mặt chữ trong câu; không thêm/bớt dấu cách, không chuẩn hoá.
- Tiếng Việt giữ nguyên hoa/thường và dấu (khi chấm, chuỗi phải khớp tuyệt đối, phân biệt hoa/thường).
- Tên và tước đi liền (vd `臣吳士連`) tách thành hai mention: `吳士連:PER` và `臣:TIT`.
- Chuỗi lặp lại trong câu chỉ ghi một lần (chấm ở mức tập mention trong câu).
- Mốc thời gian gắn với sự kiện (can chi, "mùa thu tháng 7") gán `EVT`.
