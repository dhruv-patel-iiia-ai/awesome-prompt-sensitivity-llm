# Prompt vs. Sampling Instability in LLM Research Conclusions

AI Tools for Research, Lab 02 · Patel Dhruv Rajendrakumar (MCL2026002) · M.Tech in CLIS · Topic 5

**Question.** When Qwen2.5-7B-Instruct draws a yes/no/maybe conclusion from a PubMed abstract with its conclusion removed (PubMedQA PQA-L), how much of the disagreement between answers comes from **rewording the prompt**, and how much from **re-sampling the same prompt**? Secondary questions:
- whether single-prompt, self-consistency and multi-prompt estimates report different conclusions (RQ2)
- whether the measured instability depends on how the answer is scored (RQ3)

**Status (2026-11-13).**

| Stage | State |
|---|---|
| Environment, data, baseline and evaluation code | Done and tested on Colab |
| Baseline B0 | Validated on the 500 **development** items |
| P1–P5 and judge prompt | Not written yet |
| Protocol | Not frozen (`protocol_version: v1-draft`) |
| Main experiment (RQ1–RQ3) | Not run. **No test item has been used** |

Every number below is from a development-pool run.

Command labels in this README:
- **[RAN]**: executed on Google Colab (Tesla T4), with the date and the log file
- **[TEST REQUIRED]**: written but not executed in that form
- **[NOT IMPLEMENTED]**: the code does not exist yet

## 1. Repository layout

```
configs/            experiment.yaml (all settings), prompts.yaml (prompt text), ids_*.json (frozen item lists)
data/README.md      data sources, licences and rules (raw data is downloaded, never committed)
src/                data.py, prompts.py, parse.py, generate.py, seeds.py, metrics.py, evaluate.py,
                    audit.py, eval_real.py, plots.py, plots_eval.py
scripts/            setup_data.sh, env_test.py, run_generation.py, evaluate_condition.py,
                    audit_baseline.py, evaluate_real_outputs.py, colab_preflight.py
tests/              one test file per module (plain Python, no pytest needed)
notebooks/          00–08: the Colab notebooks that produced every result below
results/            env/ (environment logs), tables/, audit/, eval13/ (results.csv, figures)
paper/              main.tex, refs.bib, figures/, evidence checklist, peer review, revision log
*.md (root)         research_decisions.md, protocol_changes.md, baseline_validation.md,
                    comparison_plan.md, results_discussion_outline.md,
                    prompt_to_code_log.md, ai_assistance_log.md
```

## 2. Compute and environment

| Item | Value | Source |
|---|---|---|
| Hardware used | Free Google Colab, **Tesla T4** 15.6 GB, 2 CPUs, 13.3 GB RAM | `results/env/env_report.json` |
| Python | 3.13.16 (Colab) | `results/env/env.txt` |
| Tested versions | torch 2.11.0+cu130, transformers 5.20.2, accelerate 1.15.0, bitsandbytes 0.50.2, numpy 2.1.3, pandas 2.2.3, scipy 1.16.3, scikit-learn 1.6.1, PyYAML 6.0.3 | `results/env/env.txt` |
| Model | `Qwen/Qwen2.5-7B-Instruct`, revision `a09a35458c702b33eeacc393d103063234e8bc28`, 4-bit NF4 (float16 compute; non-quantised layers bfloat16) | `configs/experiment.yaml` |
| GPU memory | 5.9 GB in 4-bit | env test |
| Model download | 15.2 GB, repeated in every new Colab session (≈ 8 min including loading) | env test |
| Speed | 3.71 s per PubMedQA answer (13.7 tokens/s); 8-bit: 12.6 s | `results/tables/dev_b0_colab_console.txt`, `results/audit/colab_console_summary.txt` |
| Planned budget | ≈ 10.3 GPU-h for the full study (hard cap 20) | `comparison_plan.md` (projected) |

The model weights are **not** in this repository. They are downloaded from Hugging Face at the pinned revision.

## 3. Setup

The commands are run from the repository root. On Colab, the notebooks mount Google Drive and `%cd` into the project folder. Change that path to your own Drive location.

```bash
pip install -q "transformers>=4.37.0" accelerate bitsandbytes pyyaml   # [RAN] 2026-10-29, keep Colab's torch
python scripts/colab_preflight.py        # [RAN] 2026-11-04: folder names, Drive connection, required files
```

`requirements.txt` holds minimum versions plus the tested combination. **`requirements-lock.txt` (the full `pip freeze`) is still only in the Drive copy and must be added before publishing** (see §10).

## 4. Data preparation

| Dataset | Source and pinned version | Licence | Use |
|---|---|---|---|
| PubMedQA PQA-L | github.com/pubmedqa/pubmedqa, commit `1cbae8e9` | MIT | all results |
| GSM8K test | github.com/openai/grade-school-math, commit `3101c7d5` | MIT | code check of self-consistency only |

```bash
bash scripts/setup_data.sh          # [RAN] 2026-10-29: clones PubMedQA, runs the official split unchanged, downloads GSM8K
python scripts/env_test.py          # [RAN] 2026-10-29: Level 1 checks
python scripts/env_test.py --with-model   # [RAN] 2026-10-29: 36/36 PASS (results/env/)
python -m src.data --make-sets      # [RAN] 2026-10-29: writes configs/ids_*.json; printed the 5 hashes logged in prompt_to_code_log.md
```

Rules (from `data/README.md`):
- the gold label is `final_decision`
- `LONG_ANSWER` (the authors' conclusion) never enters a prompt
- abstract text is not redistributed; only PMIDs, code and model outputs are shared

## 5. Tests

```bash
python tests/test_data.py           # [RAN] 7/7     (needs data/raw)
python tests/test_prompts_parse.py  # [RAN] 11/11   (needs data/raw)
python tests/test_generate.py       # [RAN] 8/8     (fake model, no GPU)
python tests/test_metrics.py        # [RAN] 16/16
python tests/test_evaluate.py       # [RAN] 8/8     (incl. plot test)
python tests/test_audit.py          # [RAN] 7/7
python tests/test_preflight.py      # [RAN] 10/10
python tests/test_eval_real.py      # [RAN] 15/15
```

All of these ran on Colab between 2026-10-29 and 2026-11-04, and the logs are listed in `prompt_to_code_log.md` and `ai_assistance_log.md`. Without `data/raw/`, test_data and test_prompts_parse fail 2 tests each with `FileNotFoundError`. That is expected.

## 6. Baseline and experiment runs

Every generation run resumes after a disconnect: finished answers are skipped. Test-pool conditions **refuse to run** until `protocol_version: v1-frozen`.

```bash
# Baseline B0 on the 500 development items (≈ 31 GPU-min)
python scripts/run_generation.py --condition dev_b0 --prompts P0         # [RAN] 2026-10-29
python scripts/evaluate_condition.py --condition dev_b0                  # [RAN] 2026-10-29

# Baseline audit (development items only)
python scripts/audit_baseline.py --check static                          # [RAN] 2026-10-29/30
python scripts/audit_baseline.py --check repro                           # [RAN]
python scripts/audit_baseline.py --check format                          # [RAN]  (D1, D2 on 100 dev items)
python scripts/audit_baseline.py --check quant8                          # [RAN]  (P0 in 8-bit)

# Code guard check: must print a PermissionError
python scripts/run_generation.py --condition b0 --limit 1                # [RAN] 2026-10-29 (refused, as intended)

# Pilot (needs P1-P5 in configs/prompts.yaml)
python scripts/run_generation.py --condition pilot_greedy  --prompts P0,P1,P2,P3,P4,P5   # [TEST REQUIRED] (only P0 --limit 3 ran)
python scripts/run_generation.py --condition pilot_sampled --prompts P0,P1,P2,P3,P4,P5   # [TEST REQUIRED] (only P0 --limit 4 ran)

# Main study (after the freeze)
python scripts/run_generation.py --condition b0            --prompts P0              # [TEST REQUIRED]
python scripts/run_generation.py --condition main_greedy   --prompts P1,P2,P3,P4,P5  # [TEST REQUIRED]
python scripts/run_generation.py --condition main_sampled  --prompts P0,P1,P2,P3,P4,P5  # [TEST REQUIRED]
python scripts/run_generation.py --condition question_only                           # [TEST REQUIRED]
python scripts/run_generation.py --condition gsm8k_greedy                            # [TEST REQUIRED] (only --limit 2 ran)
python scripts/run_generation.py --condition gsm8k_sampled                           # [TEST REQUIRED]
# S2 LLM judge (src/judge.py) and the RQ1-RQ3 analysis (scripts/analyse.py)          # [NOT IMPLEMENTED]
```

## 7. Evaluation and key figures

```bash
python scripts/evaluate_real_outputs.py   # [RAN] 2026-11-04 (notebook 08)
```

This script runs the checks before computing any metric:
- ID alignment, missing values, gold labels
- partition (no test items)
- prompt leakage (the authors' conclusion absent from all 800 rebuilt prompts)
- re-parse of every stored answer
- metric direction
- a settings audit

It stops if any check fails. It writes `results/eval13/`:
- `results.csv` (each row carries its source file and SHA-256)
- `results_table.md`
- `checks.json`
- per-item CSVs
- `figures/accuracy_diag100.{png,pdf}` and `figures/labels_diag100.{png,pdf}`, which are Fig. 2 of the paper

Main development-pool results (`results/eval13/results.csv`):

| Items | Method | Accuracy [95% CI] | Macro-F1 | vs comparator (exact McNemar) |
|---|---|---|---|---|
| 500 dev | B0 (P0, greedy, 4-bit) | 0.588 [0.544, 0.628] | 0.553 | vs always "yes" (0.552): p = 0.27 |
| 100 dev | P0, 8-bit | 0.570 [0.470, 0.670] | 0.541 | vs P0 4-bit: Holm p = 1.0 |
| 100 dev | D1, one-word answer | 0.330 [0.240, 0.420] | 0.314 | Holm p = 0.0001 |
| 100 dev | D2, conclusion before decision | 0.720 [0.630, 0.810] | 0.649 | Holm p = 0.003 (designed on these items: likely optimistic) |

**Paper:** upload `paper/main.tex`, `paper/refs.bib` and `paper/figures/` to Overleaf (pdfLaTeX). It compiled on 2026-11-13 (5 pages).

## 8. Limitations

- Development pool only. The main experiment has not been run, so RQ1–RQ3 are unanswered.
- One model in 4-bit, one dataset, one language. Six hand-written prompts (not yet written).
- The baseline hedges heavily (202 "maybe" answers vs 55 gold). All prompts share its output format (decision D-20).
- Open before the freeze: the plug-in S_prompt is biased (≈ 0.17 with no prompt effect). The fix is pending (peer review C1, `paper/revision_log.md`).
- Contamination (the model may have seen PubMedQA) has not been checked yet.
- n = 100 for paired comparisons: only large differences are detectable.

## 9. Credits, licence and citation

- **Data:** PubMedQA (Jin et al., EMNLP 2019; MIT) and GSM8K (Cobbe et al. 2021; MIT).
- **Model:** Qwen2.5-7B-Instruct by the Qwen team (Apache 2.0, per the model card checked in Prompt 03).
- **Methods:** self-consistency (Wang et al., ICLR 2023), multi-prompt evaluation (Mizrahi et al., TACL 2024), scoring artifacts (Hua et al., EMNLP 2025). Full list: `paper/refs.bib`.
- **AI assistance:** Claude Code (Anthropic) drafted code, analyses and text. Every result came from code the author ran on Colab. Prompts, AI proposals, human decisions and AI mistakes are logged in `ai_assistance_log.md`.
- **Licence of this repository:** [TO VERIFY: the author chooses a licence (for example MIT) and adds a LICENSE file before publishing].
- **Citation:**

```bibtex
@misc{patel2026promptsampling,
  author = {Patel Dhruv Rajendrakumar},
  title  = {Rewording or Re-Sampling? Separating Prompt and Sampling Instability in LLM Conclusions on Biomedical Evidence},
  year   = {2026},
  note   = {AI Tools for Research, Lab 02. [TO VERIFY: repository URL]}
}
```

## 10. Before publishing (blockers)

1. Copy `requirements-lock.txt` from the Drive copy into the repository root.
2. Copy the Drive `results/` folder into the repository: generation records, predictions, audit JSON, `eval13/checks.json`, the per-item CSVs and the PDF figures. These hold model outputs and PMIDs only, never abstract text. Keep `data/raw/` out (it is in `.gitignore`).
3. Choose and add a LICENSE file. Fill in the repository URL here and in `paper/main.tex`.
4. `git init`, commit, push.

## 11. Minimum reproduction checklist (for a second student)

Goal: reproduce the B0 development-pool result and Fig. 2 on a free Colab T4 in about 1.5–2 hours. No test item is touched.

- [ ] Copy the repository to Google Drive. In each notebook, change the `%cd` path to your folder.
- [ ] Runtime → Change runtime type → **T4 GPU**.
- [ ] Notebook 00: environment test → expect **36/36 PASS**. Compare the versions with §2.
- [ ] Notebook 01: `make-sets` → the five printed hashes must match those in `prompt_to_code_log.md` (cycle 1).
- [ ] Notebook 07: preflight → 3/3 PASS. If you see "Errno 107", use Runtime → Restart session, not `force_remount`.
- [ ] Notebook 05: `dev_b0` (about 31 GPU-min) → expect accuracy **0.588**, macro-F1 **0.553**, 0 invalid. Greedy decoding was identical across sessions in our runs (20/20). Small differences on other GPU types are possible and must be reported.
- [ ] Notebook 06, `--check format` and `--check quant8` (about 30 min in total: 200 answers at ≈ 2.5 s, 100 at ≈ 12.6 s, plus model loading) → D1 0.33, D2 0.72, 8-bit 0.57 on the 100 diagnostic items.
- [ ] Notebook 08: evaluation → every check PASS, and all 10 "Prompt 10 value" lines PASS.
- [ ] Compare your `results/eval13/results.csv` with the one in this repository. Report any difference, with your GPU type and library versions.
