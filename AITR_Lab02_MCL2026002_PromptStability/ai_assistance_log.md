# AI assistance log

Tool: Claude Code (Claude Opus 5.5), used through the terminal. Student: Patel Dhruv Rajendrakumar.

| # | Date | Task | AI proposal | Human decision | Verification | Outcome |
|---|---|---|---|---|---|---|
| 1 | 2026-10-21/22 | Prompts 01–02: workspace, gap matrix | Gap matrix with ranked gaps | Student kept the PDF versions as the record | Against Final_Paper.pdf | Prompt01/02 PDFs |
| 2 | 2026-10-28 | Prompt 03: methods map | Three methods; Study B | Student asked for website checks | AI's recollections were later checked online; several were labelled INFERRED until then | Prompt03 PDF, updated |
| 3 | 2026-10-28 | Prompt 04: novelty | Search strings; online search | — | The search found two close neighbours that the AI had not known about; the novelty claim was narrowed | Prompt04 PDF |
| 4 | 2026-10-28 | Prompts 05–07 | RQs, thresholds, protocol | Thresholds left for the student to approve | Internal consistency; C-001 logged | Prompt05–07 PDFs |
| 5 | 2026-10-28 | Prompt 08: repository and environment test | Repository layout, env_test.py, setup_data.sh | Pending | Data files downloaded and inspected with the AI's own read-only script. Running the PubMedQA repository's split script locally was blocked by the tool's safety check, so it is left to the Colab run. env_test.py was run locally without a GPU or torch, only to check it fails cleanly (see results/env/local_dryrun_*.txt) | Waiting for the Colab console output |
| 6 | 2026-10-29 | Prompt 08: run the test | — | Student ran the notebook on Colab (T4) and pasted the output | Real execution: 36/36 PASS | Environment VERIFIED; logs saved in results/env/ |
| 7 | 2026-10-29 | Prompt 09: baseline modules, cycles 1–6 | Data, prompt/parser, generation runner, metrics, evaluation and plot modules, each with tests and a notebook | Student ran each cycle on Colab (T4) before the next one was written | Every cycle's tests passed on Colab; metrics cross-checked against sklearn/SciPy; the AI recomputed every dev_b0 number from the confusion matrix | Working baseline (dev_b0 accuracy 0.588, macro-F1 0.553); prompt_to_code_log.md |
| 8 | 2026-10-29/30 | Prompt 10: baseline audit | Audit table, discrepancy analysis, 4 diagnostic checks with decision rules; src/audit.py, scripts/audit_baseline.py, notebook 06, cell 9 | Student ran notebook 06 and cell 9 on Colab; student chose B (keep P0) against the AI's recommendation A | 7/7 new tests and a full dry run with a fake model on the AI's machine; the published comparison number was read from the paper's PDF, not recalled | baseline_validation.md |
| 9 | 2026-11-04 | Prompt 11: debug using actual evidence | Root-cause table for the three real Colab failures (DBG-01 to DBG-03 below); `scripts/colab_preflight.py` (read-only checks: names with a leading/trailing space, Errno 107, long lines and `;`), `tests/test_preflight.py`, `notebooks/07_preflight_check.ipynb` | Student ran notebook 07 on Colab (2026-11-04) and pasted the output | 10/10 tests on the AI's machine, then on Colab: tests 10 pass, 0 fail; preflight on the real Drive folder 3/3 PASS; notebook 07 lint PASS. The Errno 107 path was tested only by simulation (the real mount was healthy) | Fix VERIFIED on Colab |
| 10 | 2026-11-04 | Prompt 12: contribution pathway | Comparison of pathways A/B/C, recommendation B, fair test plan, ablations, failure analysis, run order with GPU-h (comparison_plan.md) | Student confirmed B and declined C-005 (2026-11-04) | Every number traced to a file (dev_b0 console, experiment.yaml, Prompt 05/07 PDFs); projected hours computed from measured speeds and labelled INFERRED | Plan written; no code run |
| 11 | 2026-11-04 | Prompt 13: evaluate real outputs (dev pool) | `src/eval_real.py` (checks: missing values, ID alignment, gold labels, partition/leakage, re-parse, metric direction, comparator-settings audit), `scripts/evaluate_real_outputs.py` (results.csv, per-item CSVs, checks.json, results_table.md, 2 figures), `src/plots_eval.py`, `tests/test_eval_real.py`, notebook 08 | Student ran notebook 08 on Colab (3 runs: seed audit stop → DBG-04 fix; figure layout fixed twice from screenshots) | Colab: 15/15 tests; all 25 checks PASS; all 10 Prompt 10 values reproduced; the AI re-derived every paired difference, McNemar p and Holm p from the counts | VERIFIED; results/eval13/ |
| 12 | 2026-11-13 | Prompt 14: interpretation | Hypothesis-status table, direct observations vs mechanisms vs alternatives vs unsupported claims, metric scope, limitations, 3 ranked follow-ups (results_discussion_outline.md) | Student declined all follow-ups (2026-11-13) | Every number traced to E13/B0/A10; error split 170/13/23 re-derived from the B0 confusion matrix (sum 206 = 500 − 294). RQ1–RQ3 left [TO FILL], not interpreted | Outline written; no code run |
| 13 | 2026-11-13 | Prompt 15: manuscript | paper/main.tex, refs.bib (19 verified entries), evidence_checklist.md (outline, claim-to-evidence map, 9 inconsistencies); metadata of 6 new references checked on arXiv and Crossref | Student compiled on Overleaf: 5 pages, all citations resolved | Static checks on the AI's machine (cite keys, braces, environments, labels, figures, ASCII). Not compiled (no LaTeX locally) | Draft written |
| 14 | 2026-11-13 | Prompt 16: peer review | peer_review_report.md (8 major, 13 minor, unsupported-claims table), revision_log.md (prioritised checklist, author-response table) | Student cancelled the AI's refs.bib edit (arXiv numbers); C1, C2, C4, C6, C7 still to decide | C1 checked by simulation (20,000 null items × 3 label distributions → 0.172–0.173) and by formula; page locations taken from the compiled PDF. Conflict of interest noted: the AI also wrote the draft | Review written; manuscript not changed |
| 15 | 2026-11-13 | Prompt 17: GitHub documentation | README.md (setup, data, tests, runs, evaluation, compute, limitations, credits, citation, blockers, reproduction checklist); privacy scan; data/README fix | Pending: student resolves the 4 blockers | Each [RAN] label traced to a notebook command and its log; test counts from the Colab logs; no command marked as working that was not run | README written |
| 16 | 2026-11-13 | Prompt 18: AI-use and integrity audit | ai_provenance_report.md (provenance limits, 12 activities, 9 real limitations L1–L9, human-dependent conclusions, lessons, risks, reflective account) | Student to adapt the reflective account | Every item cites this log, the decision log or a results file; no new experience added | Report written |

## Limitations observed

- Prompt 03: the AI first wrote dataset and metric details from memory. They were marked INFERRED and corrected against the papers in Prompt 04. One wrong guess was GSM8K's test size: it was recalled as 1K but the file has 1,319 problems.
- Prompt 05 → 07: the AI changed its own proposed estimator before any run (C-001).
- Prompt 08: the AI's failure-diagnostics table expected "bfloat16 supported = False" on a T4. The real run printed True. The protocol choice (float16) is unaffected, but the prediction about the flag was wrong.
- Prompt 09, cycle 1: Colab did not see a file uploaded through the Drive web page. The AI suggested `drive.mount(..., force_remount=True)` inside the same session while the working directory was on Drive. This broke the session with `OSError: [Errno 107] Transport endpoint is not connected`. The correct fix was Runtime → Restart session. No files were affected.
- Prompt 08: the AI's budget estimate of "4–14 GPU-hours" (Prompt 04) was not based on any measurement. The first measurement (8.7 tokens/s) puts the plan near the upper end, mainly because of the GSM8K check.
- Prompt 09, cycles 5–6: when logging the dev_b0 result, the AI first wrote it into the wrong column of prompt_to_code_log.md (over its own test notes). It noticed and corrected this before reporting.
- Prompt 10: the audit found an error in the AI's own Prompt 09 PDF (it described `load_official_split` as returning (test, dev); the code returns (dev, test)). The code was right; the PDF text was corrected.
- Prompt 10: the AI's first repro check (identical reruns) could not by itself prove greedy decoding, because seeded sampling would also repeat. This was noticed after the results came back; cell 9 (different seeds plus a sampling control) closed the gap.
- Prompt 10, cell 9: the AI's code put two statements on one line with `;` and used long lines; copy-paste into Colab broke them (SyntaxError twice). Rewritten with one short statement per line. Lesson: give Colab code with short lines only.
- Prompts 10–14: the AI cited arXiv 2505.11462 as "Wu et al. 2025". The first author is Rahul Thapa. Found when the arXiv page was read for the .bib in Prompt 15; corrected (D-25).
- Prompt 15: in refs.bib the AI first wrote full first names for the POSIX authors, which no source it had checked contained. It noticed and replaced them with the review's initials before reporting.

## Debugging log (Prompt 11)

Each case uses only evidence that was recorded at the time. The exact error text was saved for DBG-02 only; for DBG-01 and DBG-03 it is **UNKNOWN** (the Colab output was described in chat but not saved in the repository).

### DBG-01: Drive folder named `tests ` (Prompt 09, cycle 1, 2026-10-29)

- **Code:** notebook 01, cell 2: `!python tests/test_data.py`.
- **Observed (VERIFIED, prompt_to_code_log.md cycle 1):** the first test run failed; the Drive folder was named `tests ` with a trailing space. Exact error text: UNKNOWN.
- **Expected:** 7 tests run.
- **Cause (VERIFIED):** the folder name. After renaming it to `tests`, the same command gave 7 pass, 0 fail, and make_sets printed the same five hashes. How the space got there (typed when the folder was created in the Drive web page?) is UNKNOWN.
- **Smallest correction:** rename the folder in Drive (done). Prevention: `colab_preflight.py` lists every file or folder whose name starts or ends with a space, and says when a required folder is missing but a near-match exists.
- **Edge case:** `tests` and a stale `tests ` both exist. The required-path check passes, so only the space check catches it (`test_edge_case_both_names_present`).
- **Rerun needed:** no. The failure happened before any result was produced, and every later result came from the corrected folder.

### DBG-02: `OSError: [Errno 107] Transport endpoint is not connected` (Prompt 09, cycle 1, 2026-10-29)

- **Code (the AI's suggestion):** `drive.mount('/content/drive', force_remount=True)` in the same session, while the working directory (`%cd`) was inside Drive.
- **Observed (VERIFIED, ai_assistance_log.md):** the session broke with the error above. Before that, Colab did not show a file uploaded through the Drive web page.
- **Expected:** the new file becomes visible.
- **Cause:** VERIFIED that the error came right after the remount, and that Runtime → Restart session fixed it. INFERRED mechanism: the remount replaced the Drive filesystem under the running process, so its working directory pointed to a mount that no longer existed (Errno 107 = ENOTCONN). INFERRED for the original problem: a delay between the Drive web page and the Colab mount.
- **Smallest correction:** do not use `force_remount` while `%cd` is inside Drive. Use Runtime → Restart session, then cell 1 again. All notebooks already use a plain `drive.mount('/content/drive')`. Prevention: `colab_preflight.py` catches Errno 107 and prints this advice (`test_errno_107_gives_restart_advice`). Another `OSError` gives a different message (`test_other_oserror_is_not_called_107`).
- **Rerun needed:** no. No files were affected (logged then), and later results come from new sessions.

### DBG-03: SyntaxError after pasting cell 9 (Prompt 10, 2026-10-30)

- **Code (the AI's):** cell 9 with two statements joined by `;` and lines over 100 characters.
- **Observed (VERIFIED, ai_assistance_log.md):** SyntaxError twice when it was pasted into Colab. Exact text: UNKNOWN.
- **Expected:** the cell runs.
- **Cause:** VERIFIED that rewriting it with one short statement per line fixed it. INFERRED: copying from the terminal broke long lines into two, and the break landed inside a statement. A `;` on its own is valid Python, so the length is the more likely cause; one statement per line keeps any break harmless.
- **Smallest correction:** code given for pasting has short lines (≤ 79 characters), one statement per line, no `;`. Prevention: `colab_preflight.py --lint` checks a notebook; `;` inside strings, comments and `!` shell lines is ignored (`test_lint_ignores_semicolon_in_strings_and_shell`).
- **Finding (VERIFIED by running the lint on the AI's machine, 2026-11-04):** notebooks 00, 03, 04, 05 and 06 have lines over 79 characters (and three `;`). They ran correctly on Colab because they were **uploaded as files, not pasted**. They are left unchanged (editing working, verified notebooks gives no benefit). The rule applies to code that is pasted.
- **Rerun needed:** no. Cell 9 produced its results (V7) only after the fix.

### Colab verification (2026-11-04, notebook 07, VERIFIED)

- `tests/test_preflight.py`: 10 pass, 0 fail. The inner `[FAIL]` lines in that output are expected: three tests run the check on purpose-built broken folders.
- `colab_preflight.py` on the real Drive run copy: drive readable, no names with a leading/trailing space, all 7 required paths exist (3/3 PASS).
- `--lint notebooks/07_preflight_check.ipynb`: PASS.
- Not tested on real hardware: the Errno 107 message (only simulated with a mock, because the mount was healthy). Nobody should break the mount on purpose to test it.

### DBG-04: seed mismatch found by the Prompt 13 settings audit (2026-11-04)

- **Code:** `scripts/evaluate_real_outputs.py`, settings audit of P0 (8-bit) against P0 (4-bit) on the same 100 items.
- **Observed (VERIFIED, Colab output pasted by the student):** `[FAIL] P0 (8-bit): setting 'seed' differs from the reference on 100 items (e.g. 13000 vs 0) and is not declared`, then `Stopped: no metric was computed.` All 24 earlier checks passed.
- **Expected:** the run reaches the metrics. The audit runs were assumed to use the dev_b0 seeds.
- **Cause (VERIFIED in the code):** `diag_tasks` in `scripts/audit_baseline.py` (the AI's Prompt 10 code) calls `generate.build_tasks` with the 100 diagnostic IDs, and `build_tasks` numbers items within the list it is given. So the audit seeds are 1000 × (position in the 100-item list), while dev_b0 uses the position in the 500 dev items. Prompt 10's "seed formula" check covered only dev_b0, so this was missed.
- **Effect on results:** none. VERIFIED: all these runs are greedy (the decoding setting passed the same audit), and greedy output does not depend on the seed (Prompt 10, V7: 5/5 identical under 3 seeds). The Prompt 10 comparisons stay valid.
- **Smallest correction:** the scripts still refuse to compare runs whose settings differ. The seed difference is now declared for the 3 audit methods with this reason. `eval_real.compare_settings` accepts a declared seed difference **only** if every affected generation is greedy, and otherwise still raises.
- **Tests:** `test_declared_seed_difference_ok_only_for_greedy` (the real case passes; edge case: the same difference on sampled generations fails) and `test_undeclared_seed_difference_fails`. 15/15 on the AI's machine.
- **Rerun needed:** no generation rerun. Rerun notebook 08 only.

### AI mistakes in these cases

DBG-02, DBG-03 and DBG-04 were caused by the AI's own code or suggestions. DBG-01 was not, but the AI's notebooks had no check for it.
