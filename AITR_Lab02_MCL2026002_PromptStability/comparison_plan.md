# Contribution pathway and comparison plan (Prompt 12)

Labels: **VERIFIED** (checked in a file, a source or by execution), **INFERRED** (plan or estimate, still to be tested), **UNKNOWN** (no evidence). No result is predicted here. Timings come from measured speeds: 3.71 s per PubMedQA answer (dev_b0, 500 answers) and 16.6 s per GSM8K answer (2 answers, Prompt 09 cycle 3). Projected hours are INFERRED.

**Status (2026-11-04):** pathway B **confirmed** by the student. The optional ablation C-005 (§5) is **not adopted**: the format effect stays a dev-pool finding and a limitation (D-20).

## 1. Starting point (VERIFIED)

- Baseline B0: Qwen2.5-7B-Instruct `a09a3545`, 4-bit NF4, prompt P0, greedy. dev_b0 (500 dev items): accuracy 0.588 [0.544, 0.628], macro-F1 0.553, 0 invalid; always-"yes" control 0.552 (McNemar p = 0.27). Audit (Prompt 10): split, metrics, greedy decoding and reproducibility all VERIFIED.
- Known artifact: P0's decision-first JSON order produces too many "maybe" answers (202 predicted vs 55 gold). On 100 dev items, conclusion-first D2 gave 0.72 vs 0.56 (p = 0.002). D-20: P0 stays as it is, and P1–P5 keep its field order.
- RQ1 (primary): what share of label disagreement is between prompts (S_prompt = ΣB / ΣG)? RQ2: do E1 greedy, E2 self-consistency (k = 5) and E3 6-prompt majority differ? RQ3: does the measured stability depend on the scorer (S1 parser, S2 judge, S3 human)?
- Literature: Hariprasad 2026 (arXiv 2603.00917) measured cross-prompt consistency on PubMedQA with small models at T = 0, one run per prompt. Haase et al. 2026 (arXiv 2601.21339) split prompt vs sampling variance on creative tasks with no ground truth. Self-consistency [17]; multi-prompt evaluation [13]; scoring artifacts [8] (all at abstract level, VERIFIED web in Prompts 03–04). The S1–S9 novelty search is **not finished**.

## 2. Three pathways

| | A. Reproduce under a new condition | B. Controlled comparison (current design) | C. One targeted modification |
|---|---|---|---|
| Scientific question | Does Hariprasad's cross-prompt consistency for PubMedQA hold when the model sees the full abstract and gives a structured answer, scored against the expert label? | How much of the conclusion disagreement comes from rewording the prompt vs re-sampling it (RQ1), and does this change what a single-prompt evaluation reports (RQ2, RQ3)? | Does writing the conclusion before the label (D2) change accuracy and the prompt/sampling split, compared with P0? |
| Code changes | Their 5 prompt styles in prompts.yaml; one new condition; a scorer for their consistency measure | P1–P5 and the judge prompt (text only); `src/judge.py` (S2); `scripts/analyse.py`; a blind S3 coding sheet. Baseline code unchanged | One new template (P0 with the field order of D2) plus the same for P1–P5; one new condition. Baseline unchanged |
| Compute (INFERRED) | 500 generations ≈ 0.5 h | ≈ 5,060 PubMedQA + 1,100 GSM8K ≈ 10.3 h (§6), under the 15-h trigger and the 20-h cap | B plus 3,600 generations ≈ +3.7 h, total ≈ 14 h: close to the 15-h trigger |
| Advantages | Cheap; a direct comparison with a published number | Answers the top-ranked gap (Gap 2) directly; pre-registered rules; the baseline is validated; analyses reuse the same outputs | Built on real evidence (Prompt 10), not a guess |
| Failure risks | Their prompts, models and scoring may not be public enough to copy (UNKNOWN until the full paper is read). Has no repeated sampling, so cannot answer RQ1 | Paraphrases not truly equivalent; n = 100 limits power; one model; possible contamination; the P0 format artifact is shared by all 6 prompts (see §4) | The idea was chosen on the same dev items where it was measured, so the gain is likely optimistic. "Answer after reasoning" is a known idea (close to chain-of-thought), so it is not novel by itself. Goes against D-20 |
| Evidence needed | Their full method; our number next to theirs | Signed-off paraphrases; frozen protocol; per-item decomposition with permutation null; McNemar with Holm; κ for scorers | Pre-registered rule; test-set result; the same RQ1 analysis run twice |

## 3. Recommendation: B

B is the most defensible pathway for one free T4 and an unknown deadline:

1. It is the only pathway that answers RQ1. A cannot separate the prompt part from the sampling part. C only adds a factor to B.
2. It fits the budget with room to spare (≈ 10 h of 20). C would bring it close to the 15-h trigger.
3. It keeps the validated baseline unchanged (D-20). No modification is needed, so no "isolated change" is made to B0.
4. Novelty is qualified. E1 vs E2 vs E3 alone is a **routine comparison** of known estimators [13, 17]. The proposed difference is narrower: splitting prompt vs sampling variance for evidence-based conclusions with an expert reference, which neither close paper does as far as their pages show. This claim stays "to be confirmed" until S1–S9 are finished. B is a measurement study, not a new method.

What is kept from A and C:
- A: Hariprasad 2026 is reported only as a reference point. The GSM8K check stays as a code sanity check of self-consistency (the size is decided in C-003).
- C: offered as one small ablation (C-005, §5); not adopted by the student, so the format effect stays a limitation.

## 4. Fair test plan

**Fairness rules (apply to every comparison):** same 100 main items (55/34/11, seed 2026); same model, revision, quantisation and dtype; same parser S1; same `max_new_tokens`; seeds from the fixed formula; batch size 1; all prompts frozen and hashed before any test output is seen. P1–P5 change only the instruction wording, never `{question}`, `{context}`, the JSON schema or the field order.

| Comparison | Arms | Metric | Test / decision rule (Prompt 05/07) |
|---|---|---|---|
| Sanity | B0 vs always-"yes" vs question-only | accuracy, macro-F1 | N3: point estimate above the majority control, plus exact McNemar (to approve at freeze) |
| RQ1 | Between- vs within-prompt parts of G (6 prompts × 5 samples, T = 0.7) | S_prompt [bootstrap 95% CI, 2000, seed 7] | H1 if permutation p < 0.05 (1000, seed 11). Prompt-dominant / sampling-dominant only if the CI lies wholly above / below 0.5; otherwise "neither dominates" |
| RQ2 | E1 (1 call) vs E2 (5 calls) vs E3 (6 calls) | accuracy, macro-F1, flip rate | Difference only if \|Δacc\| ≥ 5 points and Holm-adjusted McNemar p < 0.05 |
| RQ2 budget check | E2 (5 calls) vs E3 on 5 prompts (each leave-one-out set, 5 calls) | accuracy | Same rule; makes E2 and E3 equal in calls (from existing outputs) |
| RQ3 | S1, S2 vs S3 (20 items × 6 greedy outputs) | CS, ΔCS, κ | Scoring artifact if S1 − S3 ≤ −0.05 with CI excluding 0; S2 usable if κ ≥ 0.6 |

**Ablations (reuse outputs, no extra generations):**
- k = 1, 3, 5 for self-consistency.
- Leave-one-paraphrase-out S_prompt (6 values).
- S_prompt with invalid answers excluded.
- Bias-corrected W (k/(k−1)).
- T = 0 prompt-only CS against the T = 0.7 design.

**Failure analysis:**
- Confusion matrix per prompt, and the "maybe" share per prompt. P0's known habit could inflate the within-prompt part, because T = 0.7 samples may move between "maybe" and "yes"/"no" (INFERRED). Reporting the share makes this visible.
- The 20 items with the highest G, read and sorted into: evidence ambiguity, maybe vs no confusion, format failure, other.
- Every invalid output listed.

**Scope stated in the paper:** because all six prompts share P0's decision-first order, S_prompt measures the effect of *instruction wording*, not of output format.

## 5. Optional ablation C-005 (NOT adopted, student decision 2026-11-04; kept for the record)

- **Question:** does P0's format effect (seen on dev) also appear on the main test items?
- **One isolated change:** a new template `P0_D2` equal to P0 except for the JSON field order. It is the same text as the D2 already in `src/audit.py`. It runs in a new condition, `main_greedy_d2` (100 greedy generations ≈ 6 min).
- **Not touched:** B0, P0–P5, the parser and every RQ result.
- **Compared with:** P0 greedy on the same 100 items (already produced by B0).
- **Rule (the same as Prompt 10):** a format effect only if ≥ 5 points with McNemar p < 0.05 and clearly fewer "maybe".
- **Report:** as a secondary finding, never as the main result.
- **If not approved:** the format effect stays a dev-pool finding and a limitation (D-20).

## 6. Executable run order

Steps 1–5 use dev items only. Steps 6–8 run only after the freeze (the code guard blocks them before that).

| Step | What | Command / file | Generations | GPU-h (INFERRED) |
|---|---|---|---|---|
| 1 | Student writes P1–P5 on dev items; one peer checks equivalence | `configs/prompts.yaml` | 0 | 0 |
| 2 | Code: S2 judge, analysis script, S3 coding sheet (with tests, AI's machine first) | `src/judge.py`, `scripts/analyse.py` | 0 | 0 |
| 3 | Pilot, 20 dev items, P0–P5 | `run_generation.py --condition pilot_greedy --prompts P0,P1,P2,P3,P4,P5`, then `pilot_sampled` | 120 + 600 | 0.74 |
| 4 | Judge prompt checked on pilot outputs; analyse.py run end to end on the pilot | `analyse.py` | ≤ 120 | ≤ 0.12 |
| 5 | Decide C-003 (GSM8K size), N3; tick the freeze checklist; `protocol_version: v1-frozen`; tag | `experiment.yaml`, `protocol_changes.md` | — | — |
| 6 | B0 on 500 test items; P1–P5 greedy; P0–P5 sampled; question-only | conditions `b0`, `main_greedy`, `main_sampled`, `question_only` | 500 + 500 + 3,000 + 100 | 4.23 |
| 7 | S2 judge on the RQ3 subset; S3 blind coding by the student | judge condition (new); coding sheet | 120 | ≤ 0.12 |
| 8 | GSM8K code check (size from C-003) | `gsm8k_greedy`, `gsm8k_sampled` | 1,100 (or less) | 5.07 (or less) |
| — | **Total** | | ≈ 6,160 (protocol's 6,040 + ≤ 120 judge-pilot calls) | ≈ 10.3 + model loads (~1 min per command) |


Checkpoints:
- Every condition resumes after a disconnect (VERIFIED in Prompt 09).
- Run `scripts/colab_preflight.py` in cell 1 of each new notebook (Prompt 11).
- Stop and re-plan if the pilot projects more than 15 GPU-h.
