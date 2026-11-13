# Results and Discussion outline (Prompt 14)

Labels: **VERIFIED** (from a results file or a logged Colab output), **INFERRED** (a mechanism or reading that is not tested), **UNKNOWN** (no evidence). Every number cites its source file.

**Status (2026-11-13).** The only real results are on the **development pool**:
- dev_b0: P0, 500 items
- the Prompt 10 diagnostics: P0 4-bit, P0 8-bit, D1 and D2 on 100 items
- the Prompt 10 repro checks

**No RQ1–RQ3 output exists yet.** P1–P5 are not written, the protocol is not frozen, and no test item has been run. RQ1–RQ3 are therefore **unresolved for lack of data**, not negative. Their sections below are empty shells, marked [TO FILL].

Sources:
- `results/eval13/results.csv` (= E13)
- `results/tables/dev_b0_colab_console.txt` (= B0)
- `results/audit/colab_console_summary.txt` (= A10)
- `baseline_validation.md` (= BV)

## 1. Hypotheses: status

| Hypothesis / pre-registered rule | Status | Evidence |
|---|---|---|
| H1 (RQ1): prompt wording adds disagreement beyond the permutation null | **Unresolved: no data** | Needs P1–P5 and the main sampled runs |
| H2 (RQ2): the 6 prompts' greedy accuracies spread by ≥ 5 points | **Unresolved: no data** | D1 and D2 change the *format*, so they are not paraphrases and do **not** count as evidence for H2 |
| H3 (RQ3): S1 parsing overstates instability against S3 | **Unresolved: no data** | Needs the judge and human coding |
| RQ1 contradicting observation: < 10% of items show any disagreement | **Unresolved** | Not measurable from greedy runs. Prompt 10's sampling control changed 5/5 items (A10), so sampled runs do vary, but 5 items say nothing about the share |
| Sanity bound N3 (proposed: point estimate above the majority control, plus exact McNemar) | **Point estimate met; not significant**. N3 still to be approved | 0.588 vs 0.552; Δ +0.036 [−0.022, +0.096]; McNemar 111 : 129, p = 0.27 (E13) |
| Prompt 10 rule, format check (≥ 5 points, p < 0.05, fewer "maybe") | **Met by D2** (on the items used to design it) | +0.160 [+0.070, +0.250], 4 : 20, p = 0.0015, Holm 0.0031; "maybe" 23 vs 41 (E13) |
| Prompt 10 rule, 4-bit vs 8-bit | **Not met**: no difference detected | +0.010 [−0.050, +0.070], 4 : 5, p = 1.0 (E13) |

## 2. Results (outline with the real values)

### R1. Baseline and controls (dev500): VERIFIED

**Direct observations:**
- B0: accuracy 0.588 [0.544, 0.628], macro-F1 0.553 [0.513, 0.590], 0 invalid (E13).
- Always-"yes" control: accuracy 0.552, macro-F1 0.237 (E13).
- Accuracy is above the control only in the point estimate (p = 0.27). Macro-F1 is far above it, because the control never predicts "no" or "maybe".
- **Error structure (B0 confusion matrix):** 206 errors in total.

| Error type | Count | Share of errors |
|---|---|---|
| Gold yes/no answered "maybe" (hedges) | 170 | 83% |
| Committed to the wrong side (yes ↔ no) | 13 | 6% |
| Gold "maybe" answered yes/no | 23 | 11% |

- When P0 commits, it is usually right: precision 0.864 for "yes" and 0.907 for "no". "Maybe" precision is 0.158 (B0).
- Self-reported certainty: accuracy 0.930 when certainty = "high" (n = 171). Every "maybe" answer was "moderate" or "low" (A10).

**What not to say:**
- "The model is calibrated": the certainty field is self-reported text, not a probability, and was not tested for calibration.
- "B0 beats the majority baseline": not significant.

### R2. Diagnostic checks on the same 100 dev items: VERIFIED

| Method | Accuracy [95% CI] | Macro-F1 | Pred. yes/no/maybe | vs P0 4-bit (only P0 right : only other right), Holm p |
|---|---|---|---|---|
| P0 (4-bit) | 0.560 [0.470, 0.660] | 0.529 | 36/23/41 | — |
| P0 (8-bit) | 0.570 [0.470, 0.670] | 0.541 | 37/20/43 | 4 : 5, 1.000 |
| D1 one word | 0.330 [0.240, 0.420] | 0.314 | 22/4/74 | 27 : 4, 0.0001 |
| D2 conclusion first | 0.720 [0.630, 0.810] | 0.649 | 49/28/23 | 4 : 20, 0.0031 |
| always yes | 0.550 | 0.237 | 100/0/0 | — |

Gold labels on these items: 55/34/11 (E13).

### R3. RQ1, prompt vs sampling decomposition: [TO FILL]

Tables 2, Figures 2 and 4 of protocol v1, from the main sampled runs.

### R4. RQ2, estimators E1/E2/E3, plus the equal-budget check: [TO FILL]

Tables 3 and 4, and Figure 3.

### R5. RQ3, scoring methods: [TO FILL]

Table 5.

### R6. Variation across runs and cost: VERIFIED

**Variation across runs:**
- Greedy runs repeat exactly: 20/20 identical in a new session, and 5/5 identical under 3 seeds (BV V7, V8).
- So for greedy methods the only uncertainty is item sampling, which the bootstrap CIs report.
- Seeded sampling at Qwen's default settings changed 5/5 items (A10). Re-sampling does create variation, which is the premise of RQ1.

**Cost (measured):**

| Run | Seconds per answer | Notes |
|---|---|---|
| P0, 4-bit | 3.71 | 13.7 tokens/s; 31 GPU-min for 500 items (B0) |
| P0, 8-bit | 12.6 | ≈ 3.4× slower than 4-bit, with no accuracy difference detected (A10) |
| Format diagnostic (D1 + D2 together) | 2.5 | D1's one-word answers pull the average down (A10) |

**Do not say:** "8-bit is no better". The data only show that no difference was detected, at a power that only finds large effects.

## 3. Discussion (outline)

### D1. Main dev-pool finding: P0's "maybe" habit is a format effect

**Direct observations:**
- P0 hedges a lot: it predicts 202 "maybe" against 55 gold.
- Moving "conclusion" before "decision" (D2) cuts this to 23 "maybe" against 11 gold, and raises accuracy by 16 points on the same items.

**Possible mechanism (INFERRED, not tested):**
- With P0, the model commits to a label before it has written any reasoning, and hedges.
- Writing the conclusion first acts like a one-sentence reasoning step.
- Consistent with this, D1 (no reasoning at all) hedges most: 74 "maybe".

**Alternative explanations to state:**
1. **Selection bias:** D2 was designed after seeing P0's errors, and measured on the same 100 items. The gain is likely overstated (BV U3).
2. **Real ambiguity:** some abstracts with the conclusion removed may truly support "maybe". PubMedQA's own single-human accuracy is 78% (Jin et al. 2019). Not every hedge is an error of reasoning.
3. **Instruction wording:** "Based only on this evidence" may push toward caution. This is not tested, and it is shared by all prompts.
4. **Quantisation: ruled out.** 8-bit gives the same pattern (+0.01, p = 1.0).
5. **Parsing: ruled out.** 0 invalid answers, and every stored decision equals a re-parse.

**Unsupported claims (do not make):**
- "D2 is a better prompt in general."
- "Reordering fields improves PubMedQA accuracy by 16 points."
- "Our D2 replicates Thapa et al.'s 73.9%." Their prompt, items and precision differ.

**Effect on the study (decided, D-20):** P0 stays the baseline, and P1–P5 keep its field order. So RQ1's S_prompt will measure **instruction wording only**, at a baseline that hedges a lot. The "maybe" habit may inflate the within-prompt part, because samples can swap between "maybe" and yes/no (INFERRED). The per-prompt "maybe" share has to be reported with RQ1.

### D2. Negative and null results, stated as such

- B0 accuracy is not significantly above always-"yes".
- 8-bit vs 4-bit: no difference detected. This is not equivalence: the CI of Δ is [−0.05, +0.07].
- D1 (one-word answers) is much worse: −0.23. This is a real, large negative effect for that format.

### D3. Scope of the metrics

- **Accuracy and macro-F1** measure agreement with the expert's yes/no/maybe label, not the quality of the model's reasoning or of its free-text conclusion.
- **Macro-F1** gives the "maybe" class (55 items on dev500, 11 on diag100) the same weight as the others. Its per-class F1 rests on few items and moves a lot. On diag100, one "maybe" item changes "maybe" recall by 9 points.
- **"Maybe" count** measures how often the model hedges, not calibration.
- **Certainty** is self-reported.

### D4. Limitations of the dataset and protocol

- Development pool only. Nothing here may be reported as a test-set result.
- One model (Qwen2.5-7B-Instruct, 4-bit), one dataset and one language.
- n = 100 for the paired diagnostics: only large differences are detectable.
- PubMedQA is public, so contamination is possible. The question-only control has not been run on dev items (UNKNOWN).
- The "maybe" class is small and possibly the least reliable label.
- There is no inter-annotator agreement for the gold labels in our subset.
- Six hand-written prompts are a sample of all possible wordings, not the population (protocol §11).

## 4. Follow-up experiments (at most three, ranked)

All three use development items only and leave D-20 unchanged, because P0 stays the baseline.

| Rank | Experiment | Cost (INFERRED from measured speeds) | What it would tell us |
|---|---|---|---|
| 1 | **Read and categorise the 170 hedges** (gold yes/no, predicted "maybe"). Categories: the abstract really is inconclusive / the model ignored a clear result / other. Done blind to the gold label where possible | 0 GPU; about 3–4 h of reading | Separates alternative 2 (real ambiguity) from a model habit. Highest information per hour |
| 2 | **Question-only control on the 100 diagnostic items** (the template exists; it needs a small dev-pool condition, because `question_only` is defined on the test items) | 100 generations ≈ 0.1 GPU-h | Is accuracy driven by memorised abstracts (contamination)? Needed to read any accuracy number |
| 3 | **D2 on all 500 dev items** (diagnostic only, not adopted) | ≈ 400 new generations ≈ 0.4 GPU-h | How much of the +0.16 survives outside the items D2 was designed on (selection bias, U3) |

Ranked by cost, lowest first. All three together are under 1 GPU-h, which fits the budget (≈ 10.3 of 20 GPU-h planned). None is required for the freeze. If GPU time is short, do 1 and 2 only.
