"""Prompt 13: evaluate the real development-pool outputs. No GPU needed.

From the project folder (Drive run copy):

    !python scripts/evaluate_real_outputs.py

Inputs (all produced on Colab in Prompts 09-10, development items only):
    results/generations/dev_b0.jsonl   P0, 4-bit, 500 dev items
    results/audit/format.jsonl         D1 and D2 on the 100 diagnostic items
    results/audit/quant8.jsonl         P0 in 8-bit on the same 100 items
Gold labels and the split come from data/raw (official files).

Writes results/eval13/: results.csv, per_item_*.csv, checks.json,
results_table.md and figures/*.png|pdf. Stops before any metric if a
check fails.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import eval_real as E  # noqa: E402
from src import metrics as M  # noqa: E402

QUANT_DEFAULT = "4-bit NF4 (experiment.yaml)"

# Declared before any metric is computed. "intended" lists the only
# settings allowed to differ from the reference method P0 (4-bit).
# SEED_NOTE (Prompt 13, found by this script on Colab): the Prompt 10
# audit runs numbered items within the 100-item list, dev_b0 within the
# 500 dev items, so seeds differ. All are greedy, and greedy output does
# not depend on the seed (Prompt 10, V7). eval_real refuses a declared
# seed difference if any of those generations was sampled.
SEED_NOTE = ("audit seeds count items within the 100-item list; "
             "greedy output is seed-independent (Prompt 10, V7)")
METHODS = [
    {"name": "P0 (4-bit)", "file": "results/generations/dev_b0.jsonl",
     "prompt_id": "P0", "parser": "json", "intended": {}},
    {"name": "P0 (8-bit)", "file": "results/audit/quant8.jsonl",
     "prompt_id": "P0_8bit", "parser": "json",
     "intended": {"quantisation": "8-bit instead of 4-bit",
                  "seed": SEED_NOTE}},
    {"name": "D1 one word", "file": "results/audit/format.jsonl",
     "prompt_id": "D1_one_word", "parser": "one_word",
     "intended": {"prompt_text": "one-word answer, no JSON",
                  "seed": SEED_NOTE}},
    {"name": "D2 conclusion first", "file": "results/audit/format.jsonl",
     "prompt_id": "D2_conclusion_first", "parser": "json",
     "intended": {"prompt_text": "JSON fields reordered",
                  "seed": SEED_NOTE}},
]
REF = "P0 (4-bit)"

# Values printed on Colab in Prompt 10 (results/audit/
# colab_console_summary.txt and dev_b0_colab_console.txt). Used only to
# check that this script reproduces them; never written as results.
PROMPT10 = {
    ("diag100", "P0 (4-bit)"): {"accuracy": 0.560, "macro_f1": 0.529},
    ("diag100", "P0 (8-bit)"): {"accuracy": 0.570, "macro_f1": 0.541},
    ("diag100", "D1 one word"): {"accuracy": 0.330, "macro_f1": 0.314},
    ("diag100", "D2 conclusion first"): {"accuracy": 0.720,
                                         "macro_f1": 0.649},
    ("dev500", "P0 (4-bit)"): {"accuracy": 0.588, "macro_f1": 0.552855},
}


def decisions(recs, parser):
    if parser == "one_word":
        from src.audit import parse_one_word
        return {r["key"]: parse_one_word(r["raw_text"]) for r in recs}
    return {r["key"]: r["decision"] for r in recs}


def run(gold, dev_ids, test_ids, diag_ids, root, out_dir, message_fn,
        make_figures=True):
    """All checks first, then metrics, then export. Returns the CSV rows."""
    root, out = Path(root), Path(out_dir)
    log = {"checks": [], "settings_audit": {}, "inputs": {}}

    def ok(text):
        log["checks"].append(text)
        print(f"[PASS] {text}")

    sets = {"dev500": sorted(dev_ids), "diag100": sorted(diag_ids)}
    ok("metric direction: " + E.check_direction())
    ok("gold dev500: " + E.check_gold(gold, sets["dev500"]))
    if not set(sets["diag100"]) <= set(sets["dev500"]):
        raise E.CheckError("diag100 is not inside the dev pool")
    ok("diag100 is a subset of dev500")

    files, preds, settings, srcinfo = {}, {}, {}, {}
    for m in METHODS:
        path = root / m["file"]
        if m["file"] not in files:
            files[m["file"]] = E.load_jsonl(path)
            sha = E.file_sha256(path)
            log["inputs"][m["file"]] = sha
            ok(f"{m['file']}: " + E.check_missing(files[m["file"]],
                                                  m["file"]))
        recs = E.select(files[m["file"]], m["prompt_id"])
        name = m["name"]
        keys = sets["dev500"] if name == REF else sets["diag100"]
        ok(f"{name}: " + E.check_alignment(recs, keys, name))
        ok(f"{name}: " + E.check_partition(keys, dev_ids, test_ids, name))
        if m["parser"] == "json":
            ok(f"{name}: " + E.check_reparse(recs, name))
        for k in keys:
            message_fn(k, m["prompt_id"])   # raises if long_answer leaks
        ok(f"{name}: prompts rebuilt for {len(keys)} items, "
           "authors' conclusion absent from every prompt")
        preds[name] = decisions(recs, m["parser"])
        ok(f"{name}: " + E.check_labels(preds[name], name))
        settings[name] = E.settings_of(recs, QUANT_DEFAULT)
        srcinfo[name] = (m["file"], log["inputs"][m["file"]],
                         m["prompt_id"])

    ref_diag = {k: settings[REF][k] for k in sets["diag100"]}
    for m in METHODS:
        rep = E.compare_settings(ref_diag, settings[m["name"]],
                                 m["intended"], m["name"])
        log["settings_audit"][m["name"]] = rep
    ok("settings audit: every difference from P0 (4-bit) is declared")
    for name, rep in log["settings_audit"].items():
        print(f"       {name}: {rep}")

    # ---------- metrics ----------
    rows, scores = [], {}
    yes_label = "yes"
    for set_name, keys in sets.items():
        g = {k: gold[k] for k in keys}
        names = [REF] if set_name == "dev500" else [m["name"]
                                                     for m in METHODS]
        for name in names:
            p = {k: preds[name][k] for k in keys}
            s = E.score(g, p)
            scores[(set_name, name)] = s
            f, sha, pid = srcinfo[name]
            for metric in E.DIRECTION:
                v, lo, hi = s[metric]
                rows.append({"item_set": set_name, "method": name,
                             "role": "model", "metric": metric,
                             "value": v, "ci_low": lo, "ci_high": hi,
                             "n": s["n"], "direction": E.DIRECTION[metric],
                             "source_file": f, "source_sha256": sha,
                             "prompt_id": pid})
        ctrl = {k: yes_label for k in keys}
        s = E.score(g, ctrl)
        scores[(set_name, "always yes")] = s
        for metric in ("accuracy", "macro_f1"):
            v, lo, hi = s[metric]
            rows.append({"item_set": set_name, "method": "always yes",
                         "role": "control", "metric": metric, "value": v,
                         "ci_low": lo, "ci_high": hi, "n": s["n"],
                         "direction": E.DIRECTION[metric],
                         "source_file": "gold labels only"})

    # paired tests: same items only
    tests = []
    g500 = {k: gold[k] for k in sets["dev500"]}
    t = E.paired(g500, {k: yes_label for k in g500},
                 {k: preds[REF][k] for k in g500})
    tests.append(("dev500", REF, "always yes", t, "single test"))
    g100 = {k: gold[k] for k in sets["diag100"]}
    p_ref = {k: preds[REF][k] for k in g100}
    fam = []
    for m in METHODS[1:]:
        t = E.paired(g100, p_ref, {k: preds[m["name"]][k] for k in g100})
        fam.append((m["name"], t))
    adj = M.holm([t["p_exact"] for _, t in fam])
    for (name, t), pa in zip(fam, adj):
        t["p_holm"] = pa
        tests.append(("diag100", name, REF, t, "Holm over 3 tests"))
    for set_name, name, comp, t, note in tests:
        d, lo, hi = t["acc_diff"]
        rows.append({
            "item_set": set_name, "method": name, "role": "paired test",
            "metric": "accuracy_difference", "value": d, "ci_low": lo,
            "ci_high": hi, "n": len(sets[set_name]),
            "direction": "method minus comparator",
            "comparator": comp,
            "only_comparator_right": t["only_ref_right"],
            "only_method_right": t["only_method_right"],
            "p_exact_mcnemar": t["p_exact"], "p_holm": t.get("p_holm"),
            "test_note": note + "; exact two-sided McNemar on paired "
                         "correctness; items assumed independent; "
                         "paired bootstrap CI (2000, seed 7)",
            "source_file": srcinfo[name][0]})

    # ---------- reproduce the Prompt 10 numbers ----------
    repro = []
    for (set_name, name), ref in PROMPT10.items():
        for metric, val in ref.items():
            got = scores[(set_name, name)][metric][0]
            tol = 0.0005 if len(str(val)) <= 5 else 1e-6
            same = abs(got - val) <= tol
            repro.append((set_name, name, metric, val, got, same))
            print(f"[{'PASS' if same else 'DIFF'}] Prompt 10 value "
                  f"{set_name} {name} {metric}: {val} vs {got:.6f}")
    log["prompt10_reproduced"] = all(r[-1] for r in repro)

    # ---------- export ----------
    out.mkdir(parents=True, exist_ok=True)
    E.write_csv(rows, out / "results.csv")
    for set_name, keys in sets.items():
        names = [REF] if set_name == "dev500" else [m["name"]
                                                     for m in METHODS]
        with open(out / f"per_item_{set_name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["key", "gold"] + names)
            for k in keys:
                w.writerow([k, gold[k]] + [preds[n][k] for n in names])
    (out / "checks.json").write_text(json.dumps(log, indent=2))
    write_table(scores, tests, out / "results_table.md")
    if make_figures:
        figures(scores, out / "figures")
    print(f"saved {out}/results.csv ({len(rows)} rows), per-item CSVs, "
          "checks.json, results_table.md" +
          (", figures/" if make_figures else ""))
    return rows


def write_table(scores, tests, path):
    lines = ["| Item set | Method | n | Accuracy [95% CI] | Macro-F1 "
             "[95% CI] | Invalid | Predicted yes/no/maybe |",
             "|---|---|---|---|---|---|---|"]
    for (set_name, name), s in scores.items():
        a, al, ah = s["accuracy"]
        f, fl, fh = s["macro_f1"]
        c = s["pred_counts"]
        lines.append(f"| {set_name} | {name} | {s['n']} | {a:.3f} "
                     f"[{al:.3f}, {ah:.3f}] | {f:.3f} [{fl:.3f}, {fh:.3f}]"
                     f" | {c['invalid']} | {c['yes']}/{c['no']}/"
                     f"{c['maybe']} |")
    lines += ["", "| Item set | Method vs comparator | Δ accuracy "
              "[95% CI] | only comparator right : only method right | "
              "exact McNemar p | Holm p |", "|---|---|---|---|---|---|"]
    for set_name, name, comp, t, _ in tests:
        d, lo, hi = t["acc_diff"]
        ph = t.get("p_holm")
        lines.append(f"| {set_name} | {name} vs {comp} | {d:+.3f} "
                     f"[{lo:+.3f}, {hi:+.3f}] | {t['only_ref_right']} : "
                     f"{t['only_method_right']} | {t['p_exact']:.4f} | "
                     f"{'' if ph is None else f'{ph:.4f}'} |")
    Path(path).write_text("\n".join(lines) + "\n")


def figures(scores, fig_dir):
    from src import plots_eval as P
    order = [m["name"] for m in METHODS]
    rows = [(n,) + scores[("diag100", n)]["accuracy"] for n in order]
    ctrl = ("always yes", scores[("diag100", "always yes")]["accuracy"][0])
    P.accuracy_ci(rows, ctrl, fig_dir / "accuracy_diag100",
                  "Accuracy on the same 100 development items")
    gold = scores[("diag100", REF)]["gold_counts"]
    mix = [("Gold (expert)", gold)] + [
        (n, scores[("diag100", n)]["pred_counts"]) for n in order]
    P.label_mix(mix, fig_dir / "labels_diag100",
                "Predicted labels on the same 100 development items")


def main():
    from src import data, prompts
    from src.audit import diag_ids, diag_messages
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out", default=str(ROOT / "results" / "eval13"))
    args = ap.parse_args()
    cfg = data.load_config()
    items = data.load_pqal(args.data_root, cfg["data"]["ori_pqal_sha256"])
    dev_ids, test_ids = data.load_official_split(args.data_root)
    gold = {k: v.final_decision for k, v in items.items()}
    diag = diag_ids(dev_ids, gold)
    p_cfg = prompts.load_prompts()

    def message_fn(key, prompt_id):
        if prompt_id in ("P0", "P0_8bit"):
            return prompts.build_messages(items[key], "P0", p_cfg)
        return diag_messages(items[key], prompt_id, p_cfg)

    try:
        run(gold, dev_ids, test_ids, diag, ROOT, args.out, message_fn)
    except E.CheckError as e:
        print(f"[FAIL] {e}")
        print("Stopped: no metric was computed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
