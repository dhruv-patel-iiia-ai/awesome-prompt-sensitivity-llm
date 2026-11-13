# Baseline validation (Prompt 10)

Baseline B0: Qwen2.5-7B-Instruct (revision `a09a3545`), 4-bit NF4 weights with float16 compute, bfloat16 for the
non-quantised layers, canonical prompt P0, greedy decoding (max 128 new tokens). Data: PubMedQA PQA-L in the
reasoning-required setting (question + abstract without its conclusion). Scored with accuracy and macro-F1 over
yes/no/maybe.

**Status (2026-10-30):** audited on the 500 **development** items (condition `dev_b0`). All checks were run on Colab
(Tesla T4) with `notebooks/06_baseline_audit.ipynb` plus cell 9. Results: `results/audit/*.json` and
`results/audit/colab_console_summary.txt`. The test pool is still locked.

## 1. Reference points

| Reference | Setting | Reported | Ours (dev_b0) |
|---|---|---|---|
| Jin et al. 2019 (PubMedQA paper) | test 500, reasoning-required | 55.2% majority; 78.0% single human; 68.1% best model (fine-tuned BioBERT) | 58.8% |
| Thapa et al. 2025 (first author Rahul Thapa; earlier logs wrongly said "Wu et al."), arXiv 2505.11462, Table S5 (PDF read 2026-10-29) | Qwen2.5-7B-Instruct, "basic setting" (asked to select an answer directly), no fine-tuning, PubMedQA 1,000 questions, vLLM, T = 0.2 | 73.9% | 58.8% (P0); **72.0%** with the conclusion-first format D2 (100-item dev sample) |

Thapa et al. do not state their prompt or whether they supply the contexts (UNKNOWN). Exact replication is not required.

## 2. VERIFIED

| # | Item | Evidence |
|---|---|---|
| V1 | Official split, run unchanged; test split = test_ground_truth.json; dev_b0 used only the 500 dev items, 0 test items | D-11; audit A |
| V2 | Gold = `final_decision`; 3 labels | D-09; code |
| V3 | Reasoning-required input; the long answer never reaches a prompt (all 1,000 items) | cycle 2 test |
| V4 | 500/500 records, one per item; P0, sample 0; model id and revision; seed formula; stored decision = re-parse; no output cut at 128 tokens | audit A, 8/8 PASS |
| V5 | Metrics: sklearn gives accuracy 0.588000 and macro-F1 0.552855, identical to ours. Official evaluation.py uses the same sklearn calls, so with 0 invalid answers our numbers equal the official ones | audit B and E |
| V6 | The exact prompt: 20/20 prompts rebuild to the recorded token counts | audit C |
| V7 | **Greedy decoding is effective**, even though Qwen's stored defaults are sampling (do_sample true, T 0.7, top_k 20, top_p 0.8, repetition_penalty 1.05). Greedy: 5/5 items identical under 3 different seeds. Control with the defaults: 5/5 changed | cell 9 |
| V8 | Reproducible in a new session: 20/20 pilot items identical to dev_b0 | audit R |
| V9 | Not passing an attention mask makes no difference (20/20 identical with an explicit mask) | audit R |
| V10 | **4-bit quantisation is not the cause of the gap**: 8-bit gives 0.57 vs 0.56 on the same 100 items, 90% same labels, McNemar 5 vs 4, p = 1.0 | audit Q |
| V11 | Printed numbers agree with the confusion matrix (294/500 by hand) | Prompt 09 |
| V12 | Macro-F1 well above the majority control (0.553 vs 0.237) | Prompt 09 |

## 3. UNCERTAIN

| # | Item | Why it stays uncertain | What would settle it |
|---|---|---|---|
| U1 | B0 accuracy above the majority class | 0.588, but the CI (0.544–0.628) includes 0.552; McNemar vs always-"yes" p = 0.27 | Rerun with the chosen P0 (C-004) |
| U2 | Why the format matters | INFERRED: deciding before writing the conclusion pushes the model to hedge; writing the conclusion first works like a short reasoning step. Supported by D1 (one word, no reasoning): 0.33 with 74 "maybe". Not tested directly | Not needed for the study; report as an observation |
| U3 | Size of the D2 gain | +16 points on 100 dev items (20 vs 4, p = 0.002). Chosen on the same items it was measured on, so likely optimistic | The rerun of dev_b0 on all 500 dev items, and finally the test set |
| U4 | bfloat16 on a T4 | The T4 has no native bfloat16, so it is emulated. It works and is deterministic (V7, V8); whether float16 would change answers was not tested | Optional: not needed for internal comparisons |
| U5 | Comparison with Thapa et al. 2025 | Their prompt and item set are unknown | Report as a reference point only |

## 4. NEEDS CORRECTION

| # | Item | Fix | Status |
|---|---|---|---|
| N1 | The Prompt 09 PDF said `load_official_split` returns (test, dev); the code returns (dev, test) | PDF corrected | Fixed |
| N2 | Records did not name the prompt file | `prompts_sha256` stored in every new record | Fixed (C-002e) |
| N3 | The sanity bound "above 55.2%" has no test attached | State it as: point estimate above the majority control, and report the exact McNemar test | Student approves at the freeze |
| N4 | evaluation.py averages macro-F1 over the labels present, so an invalid answer would become a 4th class; ours averages over 3 | Both are now reported (`macro_f1`, `macro_f1_official`); identical when there are 0 invalid answers | Fixed (C-002e) |
| N5 | Protocol says "4-bit, float16"; the non-quantised layers actually run in bfloat16 (transformers default) | Protocol text corrected; `model.dtype: bfloat16` pinned in experiment.yaml | Fixed (C-002e) |
| N6 | **P0's decision-first JSON order produces a "maybe" artifact**: on 100 dev items, conclusion-first (D2) gives 0.72 vs 0.56, "maybe" 23 vs 41 (gold 11), McNemar 20 vs 4, p = 0.002. This meets the decision rule fixed before the check (≥ 5 points, p < 0.05, clearly fewer "maybe") | Student chose **B** (2026-10-30): P0 is kept unchanged; C-004 is not adopted. The format effect is reported as a limitation and a finding (D-20). P1–P5 keep P0's field order (decision first) | Decided: B |

## 5. Acceptable adaptations vs. changes that would invalidate comparison

- **Acceptable** (documented, do not affect the within-study comparisons): zero-shot instruction model instead of
  fine-tuned BioBERT; 4-bit weights (V10); greedy instead of T = 0.2; contexts without section headers; development
  items instead of all 1,000; bfloat16 non-quantised layers.
- **Would invalidate**: any use of the test items before the freeze; changing P0 or the scorer **after** seeing test
  results; mixing prompt files across conditions (now detectable through `prompts_sha256`).
- **N6 sits in between.** It does not break the study, because RQ1–RQ3 compare conditions under the same prompt family.
  But with P0 as it is, "maybe" answers caused by the format would inflate prompt-to-prompt changes in RQ1. That is why
  it is a decision for before the freeze.

## 6. Checks still required

1. Decision B: no dev_b0 rerun. Instead, confirm the pinned dtype reproduces dev_b0 (repro check, 20 items, about
   3 min) and re-evaluate dev_b0 to add the official-style macro-F1 (CPU, seconds).
2. At the freeze: N3 approved; P1–P5 written in the same JSON field order as the final P0; 20-item pilot; C-003.
3. Only after that: B0 on the 500 test items, then the main conditions.

## 7. Consequences of decision B

- B0 stays as measured: accuracy 0.588, macro-F1 0.553 (dev). P0's text and the prompts.yaml hash `e952005e…` are unchanged.
- In RQ1, part of the prompt-to-prompt change may come from P0's decision-first format pushing answers to "maybe".
  This is reported as a limitation, with the format diagnostic (0.56 vs 0.72 on 100 dev items) as evidence.
- The diagnostic itself is a development-pool observation about prompt format, on one model and 100 items. It can be
  mentioned in the paper as such, not as a test-set result.
- P1–P5 must keep P0's JSON field order, so they differ from P0 in instruction wording only.

