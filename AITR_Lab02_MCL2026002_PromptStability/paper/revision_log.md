# Manuscript revision log (Prompt 16 onward)

Reviewed version: `Paper2_overleaf.pdf` (2026-11-13, 5 pages). Concerns are in `peer_review_report.md`.

Status values:
- **open**: not started
- **author decides**: touches an earlier decision of yours
- **done**: changed and checked
- **declined**: with a reason

## 1. Prioritised revision checklist

Order: anything that must happen before the freeze first, then by severity, then by cost.

| Priority | ID | Action | Cost | Must be before freeze? | Status |
|---|---|---|---|---|---|
| 1 | C1 | Make the bias-corrected split (W* = W·k/(k−1)) primary for S_prompt; report the null-expected S_prompt; add a unit test (S_prompt* ≈ 0 under the null); log a protocol change | 0 GPU; code + test | **Yes** | author decides (reverses C-001) |
| 2 | C2 | Decide: run the main study, or re-frame as a pre-registered protocol + baseline validation | — | Yes (sets the paper's shape) | author decides |
| 3 | C3 | Pre-register hedging-aware analyses: binary committed-vs-hedge split, yes/no-only split, per-prompt "maybe" share; state the shared output format as a scope limit | 0 GPU | **Yes** | open |
| 4 | C6 | Power / minimum detectable effect for each RQ; optionally E1 and E3 on all 500 test items | 0 GPU (or ≈ 2.1 GPU-h) | **Yes** | author decides |
| 5 | C4 | Change "drives" to associational wording in the abstract, §V-B and §VIII; optionally D2 on the 400 non-design dev items | text (or ≈ 0.4 GPU-h) | No | author decides (follow-up 3 was declined) |
| 6 | C7 | Question-only control on the 100 dev items, or remove reasoning-based interpretation | ≈ 0.1 GPU-h | No | author decides (follow-up 2 was declined) |
| 7 | C5 | Finish S1–S9; report the search; qualify the novelty claim | about 4 h of searching | Before submission | open |
| 8 | C8 | Appendix with all prompt texts; define the item index i; repository URL and tag | text | Before submission | open |
| 9 | m1 | arXiv numbers for the 7 preprints in refs.bib | text | No | open (your earlier edit to refs.bib was cancelled; do it when you choose) |
| 10 | m2–m13 | Minor fixes (table headers, Holm reference, invalid-label justification, vector figures, abstract length, GSM8K sentence, Table S5 locator, peer sign-off, control basis, AI-tools sentence) | text / re-run figures | No | open |

## 2. Author-response table

The responses are drafts for you to edit. Wherever a response depends on your decision, it is marked **[your decision]**.

| ID | Reviewer concern (short) | Draft response | Planned change (location) |
|---|---|---|---|
| C1 | Plug-in S_prompt ≈ 0.17 under no prompt effect; the 0.5 rule is biased | We thank the reviewer and confirm the bias by simulation (0.172, matching (1/k − 1/mk)/(1 − 1/mk)). **[your decision]** We make the bias-corrected split primary and report the null-expected value. No test output had been seen | §III-C Eq. 2–4; protocol change C-006; `src/metrics.py` + test |
| C2 | No RQ results | **[your decision: (a) or (b)]** (a) The frozen study has been run and §V-C to V-E report it; or (b) we re-framed the manuscript as a pre-registered protocol with baseline validation | Title, abstract, §I contributions, §V, §VIII |
| C3 | Prompt factor measured at a hedging baseline | We agree this limits what S_prompt measures. We pre-registered three hedging-aware analyses and state the shared output format as a scope limit. A second output format was not added **[or: was added]** because … | §III-C, §VI, §VII; protocol |
| C4 | Causal wording about format | Agreed. The wording is now associational, and the selection bias is stated in the abstract. **[optional]** D2 on the 400 non-design dev items gives … | Abstract, §V-B, §VIII |
| C5 | Novelty not established | We completed the search (Appendix A: databases, strings, dates, hits) and now state the contribution as an application of the partition of Haase et al. to evidence conclusions with expert labels | §I, §II, Appendix A |
| C6 | Power | We added the minimum detectable effect per RQ. **[your decision]** We extended the greedy estimators to all 500 test items | §III-D, Table I |
| C7 | Contamination | **[your decision]** The question-only control on dev gives … ; or we removed interpretations that assume reading of the evidence | §V-B / §VII |
| C8 | Reproducibility | Added the prompt appendix, the definition of i with ID-file hashes, and the repository URL with tag | §III-B, §IV, Appendix B |
| m1–m13 | Minor | All addressed as listed | References, tables, figures, abstract |

## 3. Change history

| Date | Version | Change | By | Evidence |
|---|---|---|---|---|
| 2026-11-13 | draft v0 | First compile on Overleaf: 5 pages, all citations resolved | student | Paper2_overleaf.pdf |
| 2026-11-13 | review | Peer review (8 major, 13 minor); C1 checked by simulation | AI | peer_review_report.md |
