"""Turn generation records into checked predictions and baseline metrics (protocol v1, sections 7 and 10).

Every check fails loudly: a missing, duplicated or unexpected item raises instead of being skipped.
"""
import csv
import json
from collections import Counter
from pathlib import Path

from src import metrics as M


def load_records(path):
    recs = [json.loads(line) for line in open(path) if line.strip()]
    ids = [r["run_id"] for r in recs]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate run_ids")
    return recs


def single_predictions(records, expected_ids, prompt_id="P0", sample_idx=0):
    """{item id: decision} for one prompt and one sample. Raises on missing, duplicate or extra items."""
    sel = [r for r in records if r["prompt_id"] == prompt_id and r["sample_idx"] == sample_idx]
    keys = Counter(r["key"] for r in sel)
    dup = sorted(k for k, n in keys.items() if n > 1)
    missing = sorted(set(expected_ids) - set(keys))
    extra = sorted(set(keys) - set(expected_ids))
    if dup or missing or extra:
        raise ValueError(f"{len(missing)} missing, {len(dup)} duplicated, {len(extra)} unexpected items "
                         f"(e.g. missing {missing[:3]}, duplicated {dup[:3]}, unexpected {extra[:3]})")
    return {r["key"]: r["decision"] for r in sel}


def evaluate_predictions(gold, pred, n_boot=2000, seed=7):
    """Metrics for paired {id: label} dicts with identical keys."""
    if set(gold) != set(pred):
        raise ValueError("gold and pred must cover the same ids")
    ids = sorted(gold)
    g = [gold[i] for i in ids]
    p = [pred[i] for i in ids]
    per_class = {}
    for c in M.GOLD_LABELS:
        tp = sum(a == c and b == c for a, b in zip(g, p))
        fp = sum(a != c and b == c for a, b in zip(g, p))
        fn = sum(a == c and b != c for a, b in zip(g, p))
        per_class[c] = {"precision": tp / (tp + fp) if tp + fp else 0.0, "recall": tp / (tp + fn) if tp + fn else 0.0,
                        "f1": 2 * tp / (2 * tp + fp + fn) if tp else 0.0, "support": tp + fn}
    confusion = {a: {b: sum(x == a and y == b for x, y in zip(g, p)) for b in M.ALL_LABELS} for a in M.GOLD_LABELS}
    majority = Counter(g).most_common(1)[0][0]
    pairs = list(zip(g, p))
    acc, lo, hi = M.bootstrap_ci(pairs, lambda xs: sum(a == b for a, b in xs) / len(xs), n_boot, seed)
    return {"n": len(ids), "accuracy": acc, "accuracy_ci95": [lo, hi], "macro_f1": M.macro_f1(g, p),
            # official evaluation.py: sklearn macro over the labels present, so "invalid" becomes a 4th class
            "macro_f1_official": M.macro_f1(g, p, labels=tuple(c for c in M.ALL_LABELS if c in set(g) | set(p))),
            "invalid_rate": sum(x == "invalid" for x in p) / len(p), "per_class": per_class,
            "confusion": confusion, "gold_counts": {c: g.count(c) for c in M.GOLD_LABELS},
            "pred_counts": {c: p.count(c) for c in M.ALL_LABELS},
            "majority_label": majority, "majority_accuracy": g.count(majority) / len(g)}


def efficiency(records):
    lat = [r["latency_s"] for r in records]
    out = [r["n_out_tokens"] for r in records]
    return {"generations": len(records), "gpu_seconds": round(sum(lat), 1), "mean_latency_s": sum(lat) / len(lat),
            "mean_out_tokens": sum(out) / len(out), "tokens_per_s": sum(out) / sum(lat)}


def write_outputs(condition, pred, result, out_root):
    """predictions/<condition>.json ({PMID: label}, the format evaluation.py reads),
    tables/<condition>_metrics.json and tables/<condition>_confusion.csv."""
    out_root = Path(out_root)
    (out_root / "predictions").mkdir(parents=True, exist_ok=True)
    (out_root / "tables").mkdir(parents=True, exist_ok=True)
    (out_root / "predictions" / f"{condition}.json").write_text(json.dumps(dict(sorted(pred.items())), indent=0))
    (out_root / "tables" / f"{condition}_metrics.json").write_text(json.dumps(result, indent=2))
    with open(out_root / "tables" / f"{condition}_confusion.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gold \\ predicted"] + list(M.ALL_LABELS))
        for a in M.GOLD_LABELS:
            w.writerow([a] + [result["confusion"][a][b] for b in M.ALL_LABELS])
