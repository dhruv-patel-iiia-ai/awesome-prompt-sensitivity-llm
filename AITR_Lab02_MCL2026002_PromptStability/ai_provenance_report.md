# AI-use and research-integrity report (Prompt 18)

Student: Patel Dhruv Rajendrakumar (MCL2026002). Period: 2026-10-21 to 2026-11-13.
Tool: **Claude Code** (Anthropic; model Claude Opus 5.5) in a terminal on the student's computer. It used a web-fetch sub-agent to read arXiv and Crossref pages.
Execution: **all GPU work was run by the student** on free Google Colab (Tesla T4). The AI never had access to Colab or Drive.

Sources of this report:
- `ai_assistance_log.md` (rows 1–15, limitations, DBG-01 to DBG-04)
- `research_decisions.md` (D-01 to D-27)
- `protocol_changes.md`
- `prompt_to_code_log.md`
- the Colab output pasted by the student and saved in `results/`
- the 17 prompt PDFs

Nothing here is reconstructed from memory: each item cites its record.

## 1. Provenance limits (stated first)

- **No version control.** The project is not a git repository yet, so there are no commits or diffs. Code changes are traceable only through:
  - `prompt_to_code_log.md` (Prompt 09 cycles)
  - `protocol_changes.md` (C-001 to C-002e)
  - the debugging log (DBG-01 to DBG-04)
  - the decision log
- **Prompt log.** The handbook prompts (atr.pdf) are quoted verbatim in each PromptNN PDF. The student's own chat messages are not stored in the repository; the decision log records only the decisions they led to.
- **Execution evidence** is the console output the student pasted, saved as text files. The AI could not see Colab directly, so a result is "VERIFIED" only if that output exists.

## 2. Significant AI-assisted activities

| # | Task (prompt) | AI proposal | Human decision | Verification | Change / outcome |
|---|---|---|---|---|---|
| 1 | Gaps, methods, novelty (01–04) | Gap matrix; three methods; Study B; search strings | Student asked for website checks of AI claims | arXiv pages read; recollections labelled INFERRED until checked | Two close neighbours found (Hariprasad 2026, Haase et al. 2026), which narrowed the novelty claim (D-04) |
| 2 | RQs and protocol (05–07) | RQ1–RQ3, thresholds, protocol v1, C-001 | Thresholds left for the student to approve (N3 still open) | Internal consistency only | Protocol v1-draft |
| 3 | Environment (08) | Repository layout, env_test.py, setup_data.sh | Student ran it on Colab | **36/36 PASS** on the T4 | results/env/ |
| 4 | Baseline code, 6 cycles (09) | One module + tests + notebook per cycle | Student ran each cycle before the next was written | Tests on Colab; metrics cross-checked against scikit-learn/SciPy (largest difference 3.6e-16); AI recomputed dev_b0 from the confusion matrix | dev_b0: 0.588 / 0.553 |
| 5 | Baseline audit (10) | 4 checks with decision rules fixed in advance; **recommended A (adopt conclusion-first format)** | **Student chose B (keep P0)**, against the AI's recommendation (D-20) | Colab: repro 20/20; greedy 5/5 across seeds; 8-bit p = 1.0; D2 p = 0.002 | P0 unchanged; format effect reported as a limitation |
| 6 | Debugging (11) | Root causes for 3 real failures; read-only preflight script | Student ran notebook 07 | 10/10 tests + 3/3 checks on Colab | DBG-01 to DBG-03 logged |
| 7 | Pathway (12) | A/B/C compared; recommended B; optional C-005 | **Student confirmed B, declined C-005** (D-22) | Hours computed from measured speeds, labelled INFERRED | comparison_plan.md |
| 8 | Evaluation (13) | Checks-first evaluation script, figures | Student ran it 3 times; sent figure screenshots | Colab: all checks PASS; 10/10 Prompt 10 values reproduced; AI re-derived every p-value from counts | results/eval13/; DBG-04 |
| 9 | Interpretation (14) | Hypothesis status; 3 follow-ups | **Student declined all follow-ups** | Every number traced to a file | H1–H3 "unresolved: no data" |
| 10 | Manuscript (15) | main.tex, refs.bib, evidence checklist | Student compiled it on Overleaf | Compiled: 5 pages, all citations resolved | Draft v0 |
| 11 | Peer review (16) | 8 major, 13 minor concerns | **Student cancelled the AI's edit to refs.bib**; C1/C2 decisions open | C1 checked by simulation and formula | Review + revision log |
| 12 | Repository docs (17) | README with [RAN]/[TEST REQUIRED] labels; privacy scan | Blockers left to the student (licence, files on Drive) | Each [RAN] traced to a log | README.md |

## 3. Real AI limitations, corrections and purposeful verifications

More than three occurred. All are in the logs, and none was invented here.

| # | What happened (record) | How it was found | Effect |
|---|---|---|---|
| L1 | **Wrong citation:** arXiv 2505.11462 cited as "Wu et al. 2025" in Prompts 10–14; the first author is Rahul Thapa (D-25) | Reading the arXiv page while building the .bib (purposeful verification) | Corrected in 3 files and the Prompt 14 PDF. The Prompt 10 PDF still has the error (builder lost) |
| L2 | **Harmful environment advice:** `force_remount=True` while working on Drive broke the Colab session (Errno 107; DBG-02) | The student's real error output | Fix: restart session. A preflight check now catches it. No data lost |
| L3 | **Hidden seed mismatch in the AI's own audit code** (DBG-04) | The AI's Prompt 13 settings audit stopped the run on Colab (`13000 vs 0`) | No effect on answers (greedy, VERIFIED); found only because the checks run before any metric |
| L4 | **The AI's own design change made the primary metric biased.** C-001 (Prompt 07, the AI's change) made the plug-in estimator primary. Its rationale covered the p-value but missed that the effect size and the 0.5 rule are biased: S_prompt ≈ 0.17 with no prompt effect (D-26, C1) | The AI's own critical review, checked by simulation (0.172–0.173) and formula | Must be fixed before the freeze; decision open |
| L5 | Unchecked metadata written into refs.bib (full first names for the POSIX authors) | The AI noticed before reporting | Replaced with the review's initials |
| L6 | Pasted code broke Colab (`;` and long lines → SyntaxError twice; DBG-03) | The student's error output | Short-line rule; lint check added |
| L7 | Facts from memory were wrong (GSM8K test size recalled as 1K; it has 1,319) and predictions were wrong (bfloat16 flag; 4–14 GPU-h budget not measured) | Downloads, the real run, measurement | Corrected; budget re-estimated from measured speed (10.3 GPU-h) |
| L8 | A weak verification design: identical reruns cannot prove greedy decoding, because seeded sampling would also repeat | Noticed after results came back | Cell 9 added different seeds + a sampling control (5/5 changed) |
| L9 | The AI could not run LaTeX or render matplotlib locally | — | Figures were fixed twice from the student's screenshots; the paper was compiled by the student |

## 4. Which conclusions depended on human reasoning

- **Keeping P0 as the baseline (D-20):** a methodological judgement made against the AI's recommendation. It keeps the baseline the protocol froze, at the cost of a hedging-prone format. This shapes what RQ1 can measure.
- **Scope choices:** pathway B without the extra format arm (D-22), and no follow-up experiments (D-24). These choices also mean that, after the peer review, the format claim and any reading-of-evidence claim must stay weak.
- **Resources:** free Colab only (decision log, "Open" notes, 2026-10-29); rules for reporting (VERIFIED/INFERRED/UNKNOWN; short Colab lines; one PDF per prompt; no local execution of external code).
- **What counts as a result:** only output the student ran and pasted. The student, not the AI, was the only source of execution evidence. The student also rejected an AI edit (refs.bib) during Prompt 16.
- **Still to come, and human by design:** writing P1–P5, the peer equivalence check, the S3 blind coding, approving N3 and the C1 fix, and freezing the protocol.

## 5. What was learned about vibe coding

1. **Small cycles with real execution worked.** One module + tests + a Colab run per cycle (Prompt 09) passed every cycle and gave numbers the AI could re-derive. Generating everything at once would not have shown where errors came from.
2. **Checks before metrics pay off.** The settings audit caught an error in the AI's own earlier code (L3) that the test suite had missed.
3. **The AI is weakest at the edges of the code:** environment advice (L2), paste formatting (L6), memory of facts and citations (L1, L7). Each of these was caught by real output or a source, never by the AI's confidence.
4. **An AI reviewing its own work found a real flaw (L4), but only late.** Self-review is useful, but a conflict of interest remains. A human or an independent reviewer should check C1 and the review itself.
5. **"VERIFIED" needs a named source.** The labelling rule set by the student made several unsupported claims visible early: the budget, the citations, the novelty.

## 6. Remaining risks

| Risk | Status |
|---|---|
| Main study not run; P1–P5 not written | RQ1–RQ3 unanswered |
| S_prompt bias (C1) not yet fixed | Must be fixed before the freeze |
| Self-review: the AI wrote and reviewed the paper | Independent review needed |
| Web checks were done by an AI sub-agent; the student did not re-open the pages | Spot-check the 7 web-verified references |
| No git history; requirements-lock.txt and raw results only on Drive | README blockers 1–4 |
| Prompt 10 PDF still has the "Wu et al." error | Corrected in D-25 only |
| No second person has reproduced the results | Reproduction checklist ready (README §11) |
| AI-written prose may carry subtle errors not yet found | Student reads the manuscript line by line before submission |

## 7. Reflective account (for the student to adapt)

The AI wrote most of the code and text quickly. The decisions that define the study were made by me, and the evidence came only from runs I executed:
- keeping the frozen baseline (against the AI's advice)
- choosing the scope
- refusing unverified claims

The most useful practice was to accept nothing as VERIFIED without a file, a log or a source. That rule exposed several things:
- a wrong citation
- an environment instruction that broke my session
- a bias in the very metric the AI had proposed as primary

The main lesson is that the AI was fluent even when it was wrong. The safeguards that worked were external to it: running the code myself, reading the original sources, and writing checks before computing results.
