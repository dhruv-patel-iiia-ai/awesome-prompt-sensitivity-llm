"""Evaluate a single-prompt greedy condition (dev_b0 now; b0 after the freeze). From the repository root:

    python scripts/evaluate_condition.py --condition dev_b0

Writes results/predictions/<condition>.json, results/tables/<condition>_metrics.json and _confusion.csv,
results/figures/<condition>_confusion.{png,pdf} and <condition>_labels.{png,pdf}.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data, evaluate, plots  # noqa: E402

ID_SOURCES = {"dev_b0": "dev_all", "b0": "test_all", "pilot_greedy": "pilot"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=sorted(ID_SOURCES))
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    args = ap.parse_args()

    cfg = data.load_config()
    items = data.load_pqal(args.data_root, cfg["data"]["ori_pqal_sha256"])
    src = ID_SOURCES[args.condition]
    ids = data.load_official_split(args.data_root)[0] if src == "dev_all" else \
        json.load(open(ROOT / "configs" / f"ids_{src}.json"))

    recs = evaluate.load_records(ROOT / "results" / "generations" / f"{args.condition}.jsonl")
    pred = evaluate.single_predictions(recs, ids)
    gold = {i: items[i].final_decision for i in ids}
    res = evaluate.evaluate_predictions(gold, pred)
    res["efficiency"] = evaluate.efficiency([r for r in recs if r["key"] in pred])
    res["parse_status_counts"] = {s: sum(r["parse_status"] == s for r in recs) for s in ("json", "regex", "invalid")}
    res["invalid_run_ids"] = [r["run_id"] for r in recs if r["parse_status"] == "invalid"]
    evaluate.write_outputs(args.condition, pred, res, ROOT / "results")
    figs = ROOT / "results" / "figures"
    plots.confusion_heatmap(res["confusion"], figs / f"{args.condition}_confusion",
                            f"{args.condition}: gold vs. predicted (n = {res['n']})")
    plots.label_distribution(res["gold_counts"], res["pred_counts"], figs / f"{args.condition}_labels",
                             f"{args.condition}: label counts (n = {res['n']})")

    lo, hi = res["accuracy_ci95"]
    print(f"{args.condition}: n = {res['n']}")
    print(f"  accuracy  {res['accuracy']:.3f}  (95% bootstrap CI {lo:.3f}-{hi:.3f})")
    print(f"  macro-F1  {res['macro_f1']:.3f}   (evaluation.py style, invalid as a 4th class: {res['macro_f1_official']:.3f})")
    print(f"  invalid   {res['invalid_rate']:.3f}   parse status {res['parse_status_counts']}")
    print(f"  majority-class control ('{res['majority_label']}') accuracy {res['majority_accuracy']:.3f}")
    print(f"  predicted {res['pred_counts']}  gold {res['gold_counts']}")
    for c, v in res["per_class"].items():
        print(f"  {c:6s} precision {v['precision']:.3f} recall {v['recall']:.3f} f1 {v['f1']:.3f} support {v['support']}")
    e = res["efficiency"]
    print(f"  efficiency: {e['generations']} generations, {e['gpu_seconds']} GPU-s, {e['mean_latency_s']:.2f} s each, "
          f"{e['tokens_per_s']:.1f} tokens/s")


if __name__ == "__main__":
    main()
