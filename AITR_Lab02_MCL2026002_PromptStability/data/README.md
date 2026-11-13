# Data

Raw data is **not** committed. `bash scripts/setup_data.sh` downloads it into `data/raw/` (git-ignored).

| Dataset | Source | Pinned version | Licence | Used for |
|---|---|---|---|---|
| PubMedQA PQA-L (Jin et al., EMNLP-IJCNLP 2019) | github.com/pubmedqa/pubmedqa | commit `1cbae8e9` | MIT | All PubMedQA results |
| GSM8K (Cobbe et al. 2021) | github.com/openai/grade-school-math | commit `3101c7d5` | MIT | Self-consistency code check only |

Checked by the assistant on 2026-10-28, by downloading the data files and inspecting them with its own read-only script:

- `ori_pqal.json`: 1,000 items; labels yes 552 / no 338 / maybe 110. Fields: `QUESTION, CONTEXTS, LABELS, MESHES, YEAR, reasoning_required_pred, reasoning_free_pred, final_decision, LONG_ANSWER`. `YEAR` ranges from 1989 to 2017 and is missing for 58 items.
- `test_ground_truth.json`: 500 items; labels yes 276 / no 169 / maybe 55.
- No `LONG_ANSWER` appears verbatim inside its `CONTEXTS`. Contexts are at most 398 words (median 201).
- GSM8K `test.jsonl`: 1,319 problems. Every answer contains `####`.

The official split script (`preprocess/split_dataset.py`) was run unchanged on Colab by `scripts/setup_data.sh` on 2026-10-29. Its test split equals `test_ground_truth.json` exactly (environment test, 36/36 PASS).

Rules:

- Use `final_decision` as the gold label. `reasoning_required_pred` and `reasoning_free_pred` are model predictions, not labels.
- Never put `LONG_ANSWER` into a prompt.
- Share PMIDs, scripts and model outputs. Do not redistribute the abstract text.
