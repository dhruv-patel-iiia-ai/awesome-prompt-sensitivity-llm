"""Evaluation of real generation records (Prompt 13).

Every check runs before any metric is computed and fails loudly. Nothing here
invents values: every number comes from a record file, the gold labels in
ori_pqal.json, or a declared reference that names its source.
"""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from src import metrics as M
from src.parse import parse_decision

# Metric direction, declared before computing (protocol v1, section 7).
DIRECTION = {
    "accuracy": "higher",
    "macro_f1": "higher",
    "invalid_rate": "lower",
    "maybe_predicted": "closer to gold count",
}

# Settings that must be the same for every method in one comparison,
# unless the method declares the difference as intended.
SETTINGS = ("model_id", "model_revision", "decoding", "quantisation",
            "sample_idx", "seed", "prompt_text")


class CheckError(ValueError):
    """A data check failed; no metric may be computed."""


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path):
    recs = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise CheckError(f"{path}: line {n} is not JSON ({e})")
    return recs


# ---------- checks (each returns a short text for the log) ----------
def check_missing(recs, name):
    """No empty raw text, no missing key fields, no duplicate run_ids."""
    need = ("run_id", "key", "prompt_id", "sample_idx", "raw_text")
    bad = [r.get("run_id", "?") for r in recs
           if any(r.get(f) is None for f in need)
           or not str(r.get("raw_text", "")).strip()]
    if bad:
        raise CheckError(f"{name}: {len(bad)} records with missing "
                         f"fields or empty text, e.g. {bad[:3]}")
    ids = [r["run_id"] for r in recs]
    dup = [k for k, n in Counter(ids).items() if n > 1]
    if dup:
        raise CheckError(f"{name}: duplicate run_ids {dup[:3]}")
    return f"{len(recs)} records, no missing values, no duplicates"


def select(recs, prompt_id, sample_idx=0):
    return [r for r in recs
            if r["prompt_id"] == prompt_id and r["sample_idx"] == sample_idx]


def check_alignment(recs, expected_ids, name):
    """Exactly one record per expected item: none missing, extra or doubled."""
    keys = Counter(r["key"] for r in recs)
    missing = sorted(set(expected_ids) - set(keys))
    extra = sorted(set(keys) - set(expected_ids))
    dup = sorted(k for k, n in keys.items() if n > 1)
    if missing or extra or dup:
        raise CheckError(
            f"{name}: {len(missing)} missing, {len(extra)} unexpected, "
            f"{len(dup)} duplicated items (e.g. {missing[:2]} {extra[:2]} "
            f"{dup[:2]})")
    return f"{len(recs)} records = {len(expected_ids)} expected items"


def check_gold(gold, ids):
    """Gold labels exist for every item and are one of yes/no/maybe."""
    bad = [k for k in ids if gold.get(k) not in M.GOLD_LABELS]
    if bad:
        raise CheckError(f"gold label missing or not yes/no/maybe: "
                         f"{bad[:3]}")
    return f"{len(ids)} gold labels, counts {dict(Counter(gold[k] for k in ids))}"


def check_partition(ids, dev_ids, test_ids, name):
    """Development items only; no test-pool item (leakage audit)."""
    ids = set(ids)
    leak = ids & set(test_ids)
    outside = ids - set(dev_ids)
    if leak or outside:
        raise CheckError(f"{name}: {len(leak)} test-pool items, "
                         f"{len(outside)} items outside the dev pool")
    return f"{len(ids)} items, all in the dev pool, 0 test-pool items"


def check_labels(pred, name):
    bad = {k: v for k, v in pred.items() if v not in M.ALL_LABELS}
    if bad:
        raise CheckError(f"{name}: unknown predicted labels {bad}")
    return f"labels {dict(Counter(pred.values()))}"


def check_reparse(recs, name):
    """For JSON-scored methods the stored decision must equal a re-parse."""
    diff = [r["run_id"] for r in recs
            if parse_decision(r["raw_text"])["decision"] != r.get("decision")]
    if diff:
        raise CheckError(f"{name}: stored decision differs from re-parse "
                         f"in {len(diff)} records, e.g. {diff[:3]}")
    return "stored decision = re-parse of raw text"


def check_direction():
    """Metric code points the right way on cases with known answers."""
    g = ["yes", "no", "maybe", "yes"]
    if M.accuracy(g, g) != 1.0 or M.macro_f1(g, g) != 1.0:
        raise CheckError("perfect predictions do not score 1")
    wrong = ["no", "maybe", "yes", "no"]
    if M.accuracy(g, wrong) != 0.0 or M.macro_f1(g, wrong) != 0.0:
        raise CheckError("all-wrong predictions do not score 0")
    return "perfect = 1, all wrong = 0; " + ", ".join(
        f"{k}: {v}" for k, v in DIRECTION.items())


def settings_of(recs, quant_default):
    """{key: settings dict} for one method's records."""
    out = {}
    for r in recs:
        out[r["key"]] = {
            "model_id": r.get("model_id"),
            "model_revision": r.get("model_revision"),
            "decoding": json.dumps(r.get("decoding"), sort_keys=True),
            "quantisation": r.get("quantisation", quant_default),
            "sample_idx": r.get("sample_idx"),
            "seed": r.get("seed"),
        }
    return out


def compare_settings(ref, other, intended, name):
    """Settings audit against the reference method on the same items.

    Returns {setting: "same" | "INTENDED: ..." }. Raises on any difference
    that the method did not declare (incompatible comparator).
    """
    report = {}
    for s in SETTINGS:
        if s == "prompt_text":
            report[s] = (f"INTENDED: {intended[s]}" if s in intended
                         else "same template")
            continue
        diff = [k for k in ref if ref[k][s] != other[k][s]]
        if not diff:
            report[s] = "same"
        elif s == "seed" and s in intended:
            # A seed difference is harmless only under greedy decoding.
            sampled = [k for k in diff
                       if json.loads(other[k]["decoding"]).get("do_sample")
                       or json.loads(ref[k]["decoding"]).get("do_sample")]
            if sampled:
                raise CheckError(f"{name}: seeds differ on {len(sampled)} "
                                 "sampled generations; a seed difference "
                                 "is only harmless under greedy decoding")
            report[s] = (f"DIFFERS on {len(diff)} items, no effect "
                         f"(greedy): {intended[s]}")
        elif s in intended:
            report[s] = f"INTENDED: {intended[s]}"
        else:
            a = ref[diff[0]][s]
            b = other[diff[0]][s]
            raise CheckError(f"{name}: setting {s!r} differs from the "
                             f"reference on {len(diff)} items "
                             f"(e.g. {a!r} vs {b!r}) and is not declared")
    return report


# ---------- metrics ----------
def score(gold, pred, n_boot=2000, seed=7):
    ids = sorted(gold)
    g = [gold[i] for i in ids]
    p = [pred[i] for i in ids]
    pairs = list(zip(g, p))

    def acc(xs):
        return sum(a == b for a, b in xs) / len(xs)

    def mf1(xs):
        return M.macro_f1([a for a, _ in xs], [b for _, b in xs])

    a, a_lo, a_hi = M.bootstrap_ci(pairs, acc, n_boot, seed)
    f, f_lo, f_hi = M.bootstrap_ci(pairs, mf1, n_boot, seed)
    return {
        "n": len(ids),
        "accuracy": (a, a_lo, a_hi),
        "macro_f1": (f, f_lo, f_hi),
        "invalid_rate": (p.count("invalid") / len(p), None, None),
        "maybe_predicted": (p.count("maybe"), None, None),
        "pred_counts": {c: p.count(c) for c in M.ALL_LABELS},
        "gold_counts": {c: g.count(c) for c in M.GOLD_LABELS},
    }


def paired(gold, pred_ref, pred_m, n_boot=2000, seed=7):
    """Exact McNemar and a paired bootstrap CI of the accuracy difference.

    Assumptions: the same items for both methods; items independent;
    correctness is binary. Not valid across different item sets.
    """
    ids = sorted(gold)
    if set(pred_ref) != set(gold) or set(pred_m) != set(gold):
        raise CheckError("paired test needs the same items for both")
    cr = [pred_ref[i] == gold[i] for i in ids]
    cm = [pred_m[i] == gold[i] for i in ids]
    only_ref, only_m, p = M.mcnemar_exact(cr, cm)
    units = list(zip(cr, cm))

    def diff(xs):
        return sum(b - a for a, b in xs) / len(xs)

    d, lo, hi = M.bootstrap_ci(units, diff, n_boot, seed)
    return {"only_ref_right": only_ref, "only_method_right": only_m,
            "p_exact": p, "acc_diff": (d, lo, hi),
            "agreement": sum(pred_ref[i] == pred_m[i] for i in ids) / len(ids)}


# ---------- export ----------
CSV_COLUMNS = [
    "item_set", "method", "role", "metric", "value", "ci_low", "ci_high",
    "n", "direction", "comparator", "only_comparator_right",
    "only_method_right", "p_exact_mcnemar", "p_holm", "test_note",
    "source_file", "source_sha256", "prompt_id",
]


def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r.get(k)) for k in CSV_COLUMNS})


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    return v
