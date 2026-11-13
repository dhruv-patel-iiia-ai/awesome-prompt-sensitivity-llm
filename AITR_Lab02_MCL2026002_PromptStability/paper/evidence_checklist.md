# Manuscript outline and evidence checklist (Prompt 15)

Files in this folder:
- `main.tex`: IEEE conference format (IEEEtran)
- `refs.bib`: verified entries only, each with its source in a comment
- `figures/`: the two Prompt 13 figures (PNG)

**Status:** the draft was not compiled on the AI's machine (no LaTeX installed). Static checks passed:
- every `\cite` has a .bib entry, and every entry is cited
- braces and environments balance
- figure files exist
- no non-ASCII characters
- every `\label` is referenced

Page count: UNKNOWN until it is compiled on Overleaf (target 6–10 pages once RQ1–RQ3 are filled).

Red `[TO FILL]` marks results that do not exist yet (9). Orange `[TO VERIFY]` marks facts that are not checked (8).

## 1. Section outline and evidence

| Section | What it states | Evidence | Type |
|---|---|---|---|
| Abstract | Written last; dev numbers only; RQ results [TO FILL] | E13, B0 | Measured (dev) |
| 1 Introduction | Gap: no prompt vs sampling split for evidence conclusions with an expert reference | Prompt 04 novelty matrix (arXiv pages, VERIFIED web) | Prior work + our framing; novelty provisional |
| 2 Related Work | 15 published works | refs.bib sources | Prior work |
| 3 Methodology | Data and split; P0; G = W + B; S_prompt; E1–E3; S1–S3; decision rules | data/README.md, D-09; src/metrics.py (equations match `decompose`, `s_prompt`); Prompt 05/07; C-001 | Published methods + our protocol |
| 4 Setup | Model, revision, NF4, bfloat16 layers, decoding, seeds, hardware, versions, budget | experiment.yaml; D-11, D-12, D-17, C-002e; env_report.json | Measured / configuration |
| 5.1 Baseline | 0.588 [0.544, 0.628]; macro-F1 0.553; control 0.552 / 0.237; McNemar 111 : 129, p = 0.27; errors 170/23/13; precision 0.864/0.907/0.158 | E13; B0 (confusion matrix, per-class) | Measured (dev) |
| 5.1 Audit | 20/20 prompts; sklearn = ours = official; greedy 5/5 across 3 seeds; control 5/5 changed; repro 20/20 | baseline_validation.md V5–V8; A10 | Measured (dev) |
| 5.2 Diagnostics | Table 3 and Fig. 2 values; Holm p | E13; results/eval13/figures | Measured (dev) |
| 5.3–5.5 RQ1–RQ3 | [TO FILL] | Main runs after the freeze | — |
| 5.6 Cost | 3.71 s per answer, 13.7 tokens/s, 31 GPU-min; 8-bit 12.6 s | B0; A10 | Measured |
| 6 Discussion | Format effect; mechanism marked *Conjecture*; alternatives; nulls | results_discussion_outline.md (Prompt 14) | Measured + conjecture (labelled) |
| 7 Limitations | Dev only; one model; n = 100; contamination; maybe class; metric scope | Prompt 14 D3–D4 | — |
| 8 Conclusion | Narrow lesson; RQ answers [TO FILL] | — | — |

Sources: E13 = results/eval13/results.csv; B0 = results/tables/dev_b0_colab_console.txt; A10 = results/audit/colab_console_summary.txt.

## 2. Keeping prior work, our contribution and conjecture apart

- **Published methods:** the Gini impurity measure; self-consistency (Wang et al.); multi-prompt metrics (Mizrahi et al.); scoring artifacts (Hua et al.); NF4 (Dettmers et al.); McNemar test.
- **This study:**
  - the pre-registered protocol
  - the validated baseline and its format finding (dev)
  - the RQ1–RQ3 measurements [TO FILL]
- **Conjecture (marked in the text):**
  - why the format changes hedging
  - whether hedging inflates the within-prompt part
- **Not claimed:**
  - D2 is better in general
  - our D2 reproduces Thapa et al.'s 73.9%
  - 8-bit and 4-bit are equivalent
  - B0 beats the majority class

## 3. [TO VERIFY] items (student)

1. Institute name, city, country
2. E-mail for the paper (not filled in by the AI)
3. Finish search strings S1–S9 before claiming novelty
4. Peer who checks P1–P5 (name or role)
5. Citation for Holm's step-down method (no verified metadata, so no .bib entry was made)
6. Final GSM8K check size (decision C-003)
7. Judge model for S2
8. Public repository URL

## 4. Inconsistencies found and how they are resolved

| # | Inconsistency | Resolution |
|---|---|---|
| I1 | **Wrong citation:** arXiv 2505.11462 was cited as "Wu et al. 2025" in Prompts 10, 13 and 14. Its first author is **Rahul Thapa** (arXiv page, read 2026-11-13) | Paper cites Thapa et al. Fixed in baseline_validation.md, results_discussion_outline.md and the Prompt 14 PDF. The Prompt 10 PDF cannot be rebuilt (its builder is lost), so the correction is logged instead (D-25) |
| I2 | Protocol v1 says "4-bit, float16"; the non-quantised layers run in bfloat16 | Paper states both (C-002e) |
| I3 | Prompt 05 made the bias-corrected W primary; C-001 made the plug-in split primary | Paper follows C-001; the bias-corrected W is a sensitivity analysis |
| I4 | Prompt 05 defines S_prompt over items with any disagreement; the code sums over all items | Equivalent, because items with G = 0 add 0 to both sums. Stated in the paper |
| I5 | The Prompt 10 audit runs used different seeds from dev_b0 (DBG-04) | No effect (greedy). The paper says "same model, decoding and items", not "same seeds" |
| I6 | Protocol §9 planned 4–14 GPU-h (not measured) | Paper uses the measured 3.71 s per answer, about 10.3 GPU-h |
| I7 | The pipeline figure in Prompt 07 includes the GSM8K check, but its size is open (C-003) | Paper marks the size [TO VERIFY] |
| I8 | Figures are PNG; vector PDFs exist only on Drive | For the final version, upload `results/eval13/figures/*.pdf` from Drive and change `.png` to `.pdf` in main.tex |
| I9 | POSIX authors: the AI first wrote full first names that it had not checked | Replaced with the review's initials before saving (logged as an AI mistake) |

## 5. Overleaf steps

1. Overleaf → New Project → Blank Project. Name it "Paper2".
2. Upload these files: `main.tex`, `refs.bib`, and the `figures` folder with its two PNGs (keep the folder name).
3. Menu → Compiler: pdfLaTeX. Main document: `main.tex`.
4. Click Recompile. IEEEtran is built into Overleaf.
5. If there are errors, copy the **first** error from the log (with its line number) and paste it into the chat.
6. Also report the page count.
