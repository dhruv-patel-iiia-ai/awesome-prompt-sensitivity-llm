# Technical peer review of the Paper 2 draft (Prompt 16)

**Reviewed:** `Paper2_overleaf.pdf` (compiled on Overleaf by the author, 5 pages, from `paper/main.tex` of 2026-11-13).
**Reviewer:** Claude Code. It also wrote the draft, which is a conflict of interest. To limit it, every concern below cites a page and section, and the one new technical claim (C1) was checked by simulation and by a formula, not asserted.
**Labels:** VERIFIED (checked in the PDF, the code or by a run), INFERRED (a reasoned judgement).

## Overall assessment

The draft is honest about its state, but **it is not yet a research paper**:
- The title, abstract and introduction promise a decomposition of prompt vs sampling instability.
- All the reported evidence is a baseline validation on development items. RQ1–RQ3, the paper's stated contribution, are empty (p. 3, §V-C to V-E).
- The one substantive empirical claim, the format effect, rests on a variant designed and tested on the same 100 items.
- The primary metric, as defined, is **biased toward finding a prompt effect** (C1).

**Recommendation:** major revision. Do not submit until C1 is fixed before the freeze and C2 is decided.

## MAJOR concerns

### C1. The primary metric S_prompt is biased upward, and its 0.5 decision rule is unfair (p. 2, §III-C, Eq. 2–4)

- **Problem:** W_i uses the plug-in Gini of only k = 5 samples per prompt, which underestimates the within-prompt impurity by the factor (k − 1)/k. Because G = W + B is an exact identity, B absorbs the missing part.
- **Size (VERIFIED by simulation, 20,000 null items per setting, 6 prompts × 5 samples, label distributions (0.5, 0.3, 0.2), (0.6, 0.4) and (0.8, 0.2)):** with no prompt effect at all, the plug-in S_prompt is 0.172 to 0.173. The formula (1/k − 1/mk) / (1 − 1/mk) gives 0.172.
- **Why it matters:**
  - Reporting "17% of the disagreement comes from the prompt" would be wrong when the true value is 0.
  - The rule "prompt-dominant if the CI lies above 0.5" is tilted toward prompt dominance.
  - The permutation test for H1 is still valid, because it compares against the same biased statistic. The **effect size and the dominance classification are not**.
- **History:** this is the issue the original Prompt 05 design addressed with the bias-corrected W. C-001 made the plug-in estimator primary.
- **Remedy (before the freeze, 0 GPU):**
  - Make the bias-corrected split primary: W* = W·k/(k − 1) and B* = G − W*.
  - Also report the null-expected S_prompt from the permutation distribution, alongside the observed value.
  - Log this as a protocol change. It is legitimate because no test output has been seen.
  - Add a unit test showing that S_prompt* ≈ 0 under the null.

### C2. The paper's contribution is missing (title and abstract p. 1; §V-C to V-E p. 3; §VIII p. 4)

- **Problem:** all three RQs are [TO FILL]. The only results are a baseline audit and a 100-item diagnostic.
- **Why it matters:** a reader cannot assess significance or validity, and the abstract's framing does not match the evidence.
- **Remedy:** choose one of these.
  - (a) Run the frozen main study (≈ 10.3 GPU-h planned) and fill §V-C to V-E.
  - (b) Re-frame it honestly as a *pre-registered protocol with baseline validation* (registered-report style). Change the title, abstract, contributions and conclusion to match, and move the RQ sections into a "Planned analyses" section.
- A mixed version (the full-study title with protocol-only evidence) should not be submitted.

### C3. The prompt factor is measured at a degenerate baseline, so it may not measure "prompt sensitivity" (§VI p. 4; §III-B p. 2)

- **Evidence:** P0 answers "maybe" on 202 of 500 dev items (gold: 55), and 170 of its 206 errors are hedges (p. 3, Table II). P1–P5 must keep P0's field order.
- **Why it matters:**
  - Most of the label disagreement may be "maybe ↔ committed" flips: noise in *whether the model hedges*, not in *which conclusion it draws*.
  - S_prompt would then mostly describe the hedging behaviour of one output format.
  - Calling it "prompt vs sampling instability in conclusions" would overreach. The paper admits this only as a conjecture (§VI).
- **Remedy (0 GPU, pre-register before the freeze):**
  - (i) The split on a committed-vs-hedge binary label.
  - (ii) The split restricted to yes/no answers (hedges as a separate category, or excluded).
  - (iii) The per-prompt "maybe" share.
  - State in the title or abstract that the prompts share one output format.
  - A conclusion-first arm (the declined C-005) would directly test whether the results depend on the format. If it stays declined, this must be listed as a scope limit, not only in the Discussion.

### C4. The causal claim about the format effect is stronger than the evidence (abstract p. 1; §V-B p. 3; §VIII p. 4)

The abstract says "the output format, not the quantisation, therefore drives the baseline's hedging". Problems:
- **(a) Selection bias:** D2 was designed after seeing P0's errors and evaluated on the same 100 items (the paper says so, but the abstract still uses causal language).
- **(b) D1 differs from P0 in more than one way:** it has no JSON, no conclusion field and no certainty field, so D1 vs P0 does not isolate one factor.
- **(c) Small sample:** n = 100 with 11 gold "maybe" items.

**Why it matters:** this is the paper's only positive empirical finding, and it is stated causally.

**Remedy:**
- Text: change "drives" to "is associated with, on the items used to design the variant".
- Or test D2 on the 400 dev items it was not designed on (≈ 0.4 GPU-h; follow-up 3 of Prompt 14, which was declined). If it stays declined, the claim must stay descriptive.

### C5. The novelty claim is not established (§I p. 1; §II p. 1–2)

- **Problem:** the Introduction says neither close paper splits prompt and sampling variation for evidence-based conclusions with an expert reference. This rests on two papers, and the paper itself admits the search (S1–S9) is unfinished.
- Haase et al. [9] already perform exactly this partition. The difference is only the domain (evidence conclusions) and the presence of a reference label.
- **Why it matters:** an unsupported novelty claim is a common reason for rejection.
- **Remedy:**
  - Finish and report S1–S9: databases, strings, dates, hits, inclusion. Put the counts in an appendix or the repository.
  - Phrase the claim as "within the search reported in Appendix A".
  - Frame the contribution as an *application and measurement* of a known partition, with an explicit statement of what Haase et al. already did.

### C6. Statistical power is not analysed, and the 5-point rule may be undetectable (§III-D p. 2; Table I p. 3)

- **Problem:** RQ2 compares estimators on 100 paired items and needs ≥ 5 points with Holm-adjusted McNemar p < 0.05. Prompt 05 itself estimated that only differences of about 10 points or more are likely to be detected (INFERRED there). RQ3 uses 20 items × 6 outputs, with a κ threshold of 0.6.
- **Why it matters:** a pre-registered rule that cannot be met at this n turns into a guaranteed null.
- **Remedy (0–2 GPU-h):**
  - Add a power or minimum-detectable-effect calculation for each RQ before the freeze.
  - Raise n where it is cheap. For example, E1 and E3 (greedy, P0–P5) on all 500 test items is ≈ 2,000 more generations ≈ 2.1 GPU-h, within the 20-h cap. Self-consistency (E2) stays on 100 items.
  - Report CIs and the minimum detectable effect next to every "no difference" result.

### C7. Contamination is not checked for any reported number (§VII p. 4)

- **Problem:** all accuracy figures are reported without the question-only control, which is planned only for the test runs. Qwen2.5's training data is not documented in the paper.
- **Why it matters:** if the model has memorised PubMedQA, the accuracies, and the hedge-vs-commit pattern, may reflect recall, not reading of the evidence.
- **Remedy:** run the question-only control on the 100 diagnostic dev items (≈ 0.1 GPU-h) and report it next to Table III. If it is not run, remove any interpretation that assumes the model reasons from the evidence.

### C8. Reproducibility gaps in the text (§III-B and IV p. 2; Data and Code p. 4)

Three problems:
- **(a)** The exact P0 text, the paper's central object, is not in the paper. Only the field order is described.
- **(b)** The seed formula 1000 i + 10 j + s does not define i. In the code it is the item's *position in the list of the run*. The diagnostic runs used positions in the 100-item list and dev_b0 used positions in the 500-item list (DBG-04).
- **(c)** The repository URL is missing.

**Remedy:**
- Add the full P0 text, plus P1–P5, D1, D2 and the judge prompt, in an appendix.
- Define i precisely, and point to the ID files and their SHA-256 hashes.
- Add the URL and a release tag.

## MINOR concerns

| # | Location | Concern | Remedy |
|---|---|---|---|
| m1 | p. 5, refs [6, 8, 9, 13, 16, 18, 19] | arXiv preprints print only author, title and year. The arXiv number is missing because IEEEtran ignores the `eprint` field, which hurts citation traceability | Add `note = {arXiv preprint arXiv:XXXX.XXXXX}` (or `howpublished`) to each @misc entry |
| m2 | p. 2, §III-D | Holm correction cited without a reference ([TO VERIFY]) | Add a verified Holm (1979) entry, or cite a textbook source that has been checked |
| m3 | p. 2, Eq. 1–3 | "invalid" counts as a fourth label, so a parse failure counts as disagreement. This choice is not justified in the text | One sentence of justification, plus the invalid-excluded sensitivity analysis (already in the protocol) |
| m4 | p. 3, Table III | Header "P0 : var., p_Holm" and "y/n/m" are cryptic; the table caption explains them, but the header should stand alone | Spell out: "Only P0 right : only variant right", "Pred. yes/no/maybe" |
| m5 | p. 4, Fig. 2 | Raster PNG; the dashed control line still crosses the D1 value label | Use the vector PDFs from Drive; the label patch is already fixed in `plots_eval.py` (re-run on Colab) |
| m6 | p. 1, abstract | 228 words including a [TO FILL]. IEEE guidance is usually 150–250 words (INFERRED; check the target venue), so it will exceed this once the RQ results are added | Cut the validation detail to one sentence when the RQ sentences are added |
| m7 | p. 3, Table I | The GSM8K "code check" appears without any explanation of why a math dataset is in a PubMedQA study | One sentence (it checks the self-consistency code on a task with a known gain), or move it to the repository |
| m8 | p. 2, §II | Thapa et al. 73.9%: the table locator (Table S5) and "full precision" come from the author's reading of their PDF; no page or table is cited | Cite "Table S5 of [16]" |
| m9 | p. 3, §V-A | "Greedy decoding was in effect … identical under three seeds (5/5 items)" rests on 5 items | Also report the 20/20 new-session rerun as the main evidence (it is there; reorder) |
| m10 | p. 2, §III-B | Paraphrase equivalence is checked by "one peer", with no agreement measure or record | Publish the sign-off sheet; report agreement on the equivalence rule |
| m11 | p. 3, Table II | The majority control is "always yes", but its basis is not stated (the dev-pool majority) | State it in the caption |
| m12 | p. 1–4 | 5 pages; the 6–10-page target is reached only with the RQ sections | No action until C2 is decided |
| m13 | p. 4, Use of AI Tools | Says "every reference was checked", but the record shows two AI citation mistakes were caught late (the Thapa first author; the POSIX names) | Keep the sentence, and point to the assistance log that lists these corrections |

## Unsupported novelty and performance claims

| Claim (location) | Problem | Fix |
|---|---|---|
| "neither splits prompt and sampling variation for evidence-based conclusions …" (p. 1) | Search unfinished (C5) | Qualify by the reported search |
| "the output format … drives the baseline's hedging" (abstract, p. 1) | Causal claim from a selection-biased comparison (C4) | Associational wording |
| "a validated, reproducible baseline" (p. 1) | Validated on dev only; B0 is not significantly above majority (p = 0.27) | "audited and reproducible; not above the majority control in accuracy" |
| S_prompt as "the share of disagreement from rewording" (p. 2) | Biased by ≈ 0.17 under the null (C1) | Bias-corrected definition |
| Its 0.72 "is close to the 73.9% reported by Thapa et al." (p. 4) | Correctly hedged, but the comparison invites a reading as replication | Move to a footnote, or keep with the "settings differ" clause first |

No unsupported performance claim was found in the tables: every number in Tables II–III and Fig. 2 matches `results/eval13/results.csv` (VERIFIED in Prompt 13).

## Checks that passed

- **Data leakage:** no test item was used (code guard, partition check). Every prompt was rebuilt, and the authors' conclusion is absent from all 800 prompts.
- **Fair baselines:** the always-yes control is included. The planned question-only control exists, but has not been run yet (C7). The RQ2 equal-budget comparison (E2 vs a 5-prompt E3) is a good addition.
- **Figure and table accuracy:** Tables II and III and Fig. 2 match the CSV, including the McNemar and Holm values.
- **Citation traceability:** all 19 cited works resolve, and every in-text claim about them matches the abstract-level record. The exception is m1.
