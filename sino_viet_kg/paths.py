"""Mọi đường dẫn của mã nguồn.

- `CORPUS_DIR` (biến môi trường `VCL_CORPUS_DIR`, mặc định `code/corpus/`): ngữ liệu CLC và
  kết quả trích xuất — không phân phối kèm mã.
    0_source/                  tệp xlsx của CLC
    1_sentence_pairs/rows/     cặp câu đã tách
    2_llm_output/<mô hình>/rows/   kết quả trích xuất
- `DATA_DIR` (`code/data/`): từ điển âm Hán–Việt (đi kèm mã); phiếu gán nhãn, phiếu chấm tay và
  đầu ra Gemini 2.5 Pro sinh từ ngữ liệu (cung cấp theo yêu cầu, chép vào đúng thư mục con).
- `RESULTS_DIR` (biến `VCL_RESULTS_DIR`, mặc định `code/results/`): kết quả sinh ra.
"""
import os
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]

MODEL_CONFIG = CODE_ROOT / "configs" / "gemini-2.5-flash.json"
EXTRACTION_PROMPT = CODE_ROOT / "prompts" / "ner_with_relations.md"
ENV_FILE = CODE_ROOT / ".env"

DATA_DIR = CODE_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
GOLD_PREDICTIONS = GOLD_DIR / "llm_predictions.json"
GOLD_MAJORITY = GOLD_DIR / "gold_majority_vote.tsv"
CANON_PURITY_DIR = DATA_DIR / "canon_purity"
TRIPLE_LINK_DIR = DATA_DIR / "triple_link_precision"
CAPTURE_RECAPTURE_DIR = DATA_DIR / "capture_recapture"
HANVIET_CSV = DATA_DIR / "dictionary" / "hanviet.csv"
UNIHAN_TXT = DATA_DIR / "dictionary" / "unihan_kvietnamese.txt"

RESULTS_DIR = Path(os.getenv("VCL_RESULTS_DIR", str(CODE_ROOT / "results")))
AUDIT_OUT_DIR = RESULTS_DIR / "audit"
CANON_OUT_DIR = RESULTS_DIR / "canonicalization"
NER_REPORT_DIR = RESULTS_DIR / "ner"
BASELINE_OUT_DIR = RESULTS_DIR / "baselines"

CORPUS_DIR = Path(os.getenv("VCL_CORPUS_DIR", str(CODE_ROOT / "corpus")))
SOURCE_DIR = CORPUS_DIR / "0_source"
SOURCE_XLSX = SOURCE_DIR / (
    "DVSKTT_aligned_at_sentence_level_20240520_concat_full_aligned_clc"
    "_preprocessed_manual_version.xlsx"
)
SENTENCE_ROWS_DIR = CORPUS_DIR / "1_sentence_pairs" / "rows"
LLM_OUTPUT_DIR = CORPUS_DIR / "2_llm_output"

# Lượt trích xuất dùng trong bài (session kg_p20260507_091906_691f88_7c04b089).
PAPER_MODEL = "gemini-2.5-flash"


def require(path: Path, what: str) -> Path:
    """Dừng với thông báo rõ ràng nếu thiếu dữ liệu đầu vào."""
    path = Path(path)
    if not path.exists():
        hint = "mục 2.2 (dữ liệu gán nhãn, cung cấp theo yêu cầu)" if DATA_DIR in path.parents \
            else "mục 2.3 (ngữ liệu CLC, VCL_CORPUS_DIR)"
        raise SystemExit(f"Không thấy {what}: {path}\nXem README, {hint}.")
    return path


def llm_dir(model: str) -> Path:
    return LLM_OUTPUT_DIR / model


def llm_rows_dir(model: str = PAPER_MODEL) -> Path:
    return LLM_OUTPUT_DIR / model / "rows"
