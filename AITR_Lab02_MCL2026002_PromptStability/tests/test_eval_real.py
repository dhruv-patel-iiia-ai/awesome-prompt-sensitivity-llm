"""Tests for src/eval_real.py and scripts/evaluate_real_outputs.py.

Toy records only (they test the code; they are never results).
No GPU, no data files. Run:  python tests/test_eval_real.py
"""
import csv
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src import eval_real as E  # noqa: E402
import evaluate_real_outputs as S  # noqa: E402

DEV = ["d1", "d2", "d3", "d4", "d5", "d6"]
TEST = ["t1", "t2"]
DIAG = ["d1", "d2", "d3", "d4"]
GOLD = {"d1": "yes", "d2": "no", "d3": "maybe", "d4": "yes",
        "d5": "no", "d6": "yes", "t1": "yes", "t2": "no"}
DEC = {"do_sample": False, "max_new_tokens": 128}


def js(decision):
    return json.dumps({"decision": decision, "conclusion": "c",
                       "certainty": "high"})


def rec(cond, key, pid, raw, decision, **extra):
    r = {"run_id": f"{cond}|{key}|{pid}|s0", "key": key, "prompt_id": pid,
         "sample_idx": 0, "seed": DEV.index(key) * 1000,
         "decoding": DEC, "raw_text": raw, "decision": decision,
         "model_id": "m", "model_revision": "r"}
    r.update(extra)
    return r


def toy_files(root, mutate=None):
    """dev_b0: P0 right on d1, d2, d4, d5 (4/6); diag: d1-d4."""
    p0 = {"d1": "yes", "d2": "no", "d3": "yes", "d4": "yes",
          "d5": "no", "d6": "maybe"}
    files = {
        "results/generations/dev_b0.jsonl":
            [rec("dev_b0", k, "P0", js(v), v) for k, v in p0.items()],
        "results/audit/quant8.jsonl":
            [rec("q8", k, "P0_8bit", js(p0[k]), p0[k],
                 quantisation="8-bit") for k in DIAG],
        "results/audit/format.jsonl":
            [rec("f", k, "D1_one_word", "maybe", "invalid") for k in DIAG]
            + [rec("f", k, "D2_conclusion_first", js(GOLD[k]), GOLD[k])
               for k in DIAG],
    }
    if mutate:
        mutate(files)
    for rel, recs in files.items():
        p = Path(root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("".join(json.dumps(r) + "\n" for r in recs))


def no_leak(key, pid):
    return None


def run_toy(mutate=None, message_fn=no_leak):
    t = tempfile.mkdtemp()
    toy_files(t, mutate)
    out = Path(t) / "out"
    rows = S.run(GOLD, DEV, TEST, DIAG, t, out, message_fn,
                 make_figures=False)
    return rows, out


def expect_fail(mutate=None, message_fn=no_leak, exc=E.CheckError):
    try:
        _, out = run_toy(mutate, message_fn)
    except exc:
        return
    raise AssertionError("expected a failed check")


def value(rows, set_name, method, metric):
    hit = [r for r in rows if r["item_set"] == set_name
           and r["method"] == method and r["metric"] == metric]
    assert len(hit) == 1, hit
    return hit[0]


# ---------- the full run on clean toy data ----------
def test_clean_run_hand_computed_values():
    rows, out = run_toy()
    assert value(rows, "dev500", "P0 (4-bit)", "accuracy")["value"] == 4 / 6
    assert value(rows, "diag100", "P0 (4-bit)", "accuracy")["value"] == 0.75
    assert value(rows, "diag100", "D2 conclusion first",
                 "accuracy")["value"] == 1.0
    # D1 is scored with its own one-word parser: "maybe" everywhere
    assert value(rows, "diag100", "D1 one word",
                 "accuracy")["value"] == 0.25
    assert value(rows, "diag100", "always yes", "accuracy")["value"] == 0.5
    for f in ("results.csv", "per_item_dev500.csv", "per_item_diag100.csv",
              "checks.json", "results_table.md"):
        assert (out / f).exists(), f


def test_csv_is_traceable():
    _, out = run_toy()
    with open(out / "results.csv") as f:
        rows = list(csv.DictReader(f))
    model_rows = [r for r in rows if r["role"] == "model"]
    assert all(len(r["source_sha256"]) == 64 for r in model_rows)
    assert all(r["direction"] for r in rows)
    log = json.loads((out / "checks.json").read_text())
    assert log["settings_audit"]["P0 (8-bit)"]["quantisation"].startswith(
        "INTENDED")
    assert log["settings_audit"]["D2 conclusion first"]["decoding"] == "same"


def test_paired_test_values():
    rows, _ = run_toy()
    r = value(rows, "diag100", "D2 conclusion first", "accuracy_difference")
    # P0 wrong only on d3; D2 right everywhere -> 0 : 1, p = 1.0
    assert (r["only_comparator_right"], r["only_method_right"]) == (0, 1)
    assert r["p_exact_mcnemar"] == 1.0 and r["p_holm"] == 1.0
    assert r["value"] == 0.25


# ---------- each check stops the run ----------
def test_missing_item_fails():
    def m(f):
        f["results/audit/quant8.jsonl"].pop()
    expect_fail(m)


def test_duplicate_run_id_fails():
    def m(f):
        recs = f["results/generations/dev_b0.jsonl"]
        recs.append(dict(recs[0]))
    expect_fail(m)


def test_empty_text_fails():
    def m(f):
        f["results/audit/format.jsonl"][0]["raw_text"] = "  "
    expect_fail(m)


def test_stored_decision_must_match_reparse():
    def m(f):
        f["results/generations/dev_b0.jsonl"][0]["decision"] = "no"
    expect_fail(m)


def test_undeclared_setting_difference_fails():
    def m(f):
        for r in f["results/audit/format.jsonl"]:
            r["decoding"] = dict(DEC, do_sample=True)
    expect_fail(m)


def test_undeclared_seed_difference_fails():
    a = [rec("x", "d1", "P0", js("yes"), "yes")]
    b = [dict(a[0], seed=99)]
    ref = E.settings_of(a, "q")
    other = E.settings_of(b, "q")
    try:
        E.compare_settings(ref, other, {}, "m")
    except E.CheckError as e:
        assert "'seed'" in str(e)
        return
    raise AssertionError("undeclared seed difference not caught")


def test_declared_seed_difference_ok_only_for_greedy():
    # The real case: audit seeds counted within the 100-item list
    def greedy(f):
        for r in f["results/audit/quant8.jsonl"]:
            r["seed"] = 7
    rows, out = run_toy(greedy)
    log = json.loads((out / "checks.json").read_text())
    assert log["settings_audit"]["P0 (8-bit)"]["seed"].startswith("DIFFERS")

    # Edge case: the same seed difference on sampled generations must fail
    def sampled(f):
        for name in ("results/generations/dev_b0.jsonl",
                     "results/audit/quant8.jsonl"):
            for r in f[name]:
                r["decoding"] = dict(DEC, do_sample=True)
        for r in f["results/audit/quant8.jsonl"]:
            r["seed"] = 7
    expect_fail(sampled)


def test_leakage_in_prompt_fails():
    def leak(key, pid):
        raise ValueError(f"{key}: long_answer found in prompt {pid}")
    expect_fail(message_fn=leak, exc=ValueError)


def test_failed_check_writes_no_results():
    t = tempfile.mkdtemp()
    toy_files(t, lambda f: f["results/audit/quant8.jsonl"].pop())
    out = Path(t) / "out"
    try:
        S.run(GOLD, DEV, TEST, DIAG, t, out, no_leak, make_figures=False)
    except E.CheckError:
        pass
    assert not (out / "results.csv").exists()


def test_partition_catches_test_item():
    try:
        E.check_partition(["d1", "t1"], DEV, TEST, "x")
    except E.CheckError as e:
        assert "1 test-pool items" in str(e)
        return
    raise AssertionError("test-pool item not caught")


def test_gold_label_check():
    try:
        E.check_gold({"a": "yes", "b": "unclear"}, ["a", "b"])
    except E.CheckError:
        return
    raise AssertionError("bad gold label not caught")


def test_direction_check_passes():
    assert "accuracy: higher" in E.check_direction()


def run_all():
    tests = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
    failed_n = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            failed_n += 1
            print(f"[FAIL] {name}: {type(e).__name__}: {e}")
    print(f"SUMMARY: {len(tests) - failed_n} pass, {failed_n} fail")
    sys.exit(1 if failed_n else 0)


if __name__ == "__main__":
    run_all()
