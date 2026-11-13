"""Tests for src/evaluate.py and src/plots.py. Run:  python tests/test_evaluate.py
Plot tests run only where matplotlib is installed (Colab); elsewhere they are reported as SKIP.
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import evaluate  # noqa: E402

close = lambda a, b: abs(a - b) < 1e-9  # noqa: E731


class Skip(Exception):
    pass


def rec(key, decision, prompt="P0", s=0, status="json"):
    return {"run_id": f"c|{key}|{prompt}|s{s}", "key": key, "prompt_id": prompt, "sample_idx": s,
            "decision": decision, "parse_status": status, "latency_s": 2.0, "n_out_tokens": 40}


GOLD = {"1": "yes", "2": "yes", "3": "no", "4": "maybe"}


def test_single_predictions_ok_and_filters_other_prompts():
    recs = [rec("1", "yes"), rec("2", "no"), rec("3", "no"), rec("4", "invalid", status="invalid"),
            rec("1", "no", prompt="P1"), rec("1", "maybe", s=1)]
    assert evaluate.single_predictions(recs, list(GOLD)) == {"1": "yes", "2": "no", "3": "no", "4": "invalid"}


def test_single_predictions_detects_problems():
    for recs in ([rec("1", "yes"), rec("2", "no"), rec("3", "no")],                      # missing 4
                 [rec("1", "yes"), rec("2", "no"), rec("3", "no"), rec("4", "no"), rec("9", "no")],  # extra 9
                 [rec("1", "yes"), dict(rec("1", "no"), run_id="dup"), rec("2", "no"), rec("3", "no"),
                  rec("4", "no")]):                                                     # duplicate 1
        try:
            evaluate.single_predictions(recs, list(GOLD))
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_load_records_rejects_duplicate_run_ids():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.jsonl"
        p.write_text(json.dumps(rec("1", "yes")) + "\n" + json.dumps(rec("1", "no")) + "\n")
        try:
            evaluate.load_records(p)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_evaluate_predictions_by_hand():
    pred = {"1": "yes", "2": "no", "3": "no", "4": "invalid"}
    r = evaluate.evaluate_predictions(GOLD, pred, n_boot=200)
    assert close(r["accuracy"], 0.5) and close(r["invalid_rate"], 0.25)
    assert close(r["macro_f1"], 4 / 9)                       # as in test_metrics: 2/3, 2/3, 0
    assert close(r["macro_f1_official"], 1 / 3)              # evaluation.py style: 2/3, 2/3, 0, 0 (invalid)
    assert r["confusion"]["yes"] == {"yes": 1, "no": 1, "maybe": 0, "invalid": 0}
    assert r["confusion"]["maybe"]["invalid"] == 1
    assert r["per_class"]["no"] == {"precision": 0.5, "recall": 1.0, "f1": 2 / 3, "support": 1}
    assert r["majority_label"] == "yes" and close(r["majority_accuracy"], 0.5)
    lo, hi = r["accuracy_ci95"]
    assert lo <= 0.5 <= hi


def test_evaluate_predictions_requires_same_ids():
    try:
        evaluate.evaluate_predictions(GOLD, {"1": "yes"})
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_write_outputs_formats():
    pred = {"2": "no", "1": "yes", "3": "no", "4": "maybe"}
    r = evaluate.evaluate_predictions(GOLD, pred, n_boot=50)
    with tempfile.TemporaryDirectory() as d:
        evaluate.write_outputs("x", pred, r, d)
        p = json.load(open(Path(d) / "predictions" / "x.json"))
        assert p == pred and list(p) == ["1", "2", "3", "4"]     # {PMID: label}, the evaluation.py format
        rows = (Path(d) / "tables" / "x_confusion.csv").read_text().splitlines()
        assert rows[0] == "gold \\ predicted,yes,no,maybe,invalid" and rows[1] == "yes,1,1,0,0"
        assert json.load(open(Path(d) / "tables" / "x_metrics.json"))["n"] == 4


def test_efficiency():
    e = evaluate.efficiency([rec("1", "yes"), rec("2", "no")])
    assert e["generations"] == 2 and close(e["gpu_seconds"], 4.0) and close(e["tokens_per_s"], 20.0)


def test_plots_if_matplotlib():
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        raise Skip("matplotlib not installed here")
    from src import plots
    pred = {"1": "yes", "2": "no", "3": "no", "4": "invalid"}
    r = evaluate.evaluate_predictions(GOLD, pred, n_boot=50)
    with tempfile.TemporaryDirectory() as d:
        files = plots.confusion_heatmap(r["confusion"], Path(d) / "c", "test") + \
            plots.label_distribution(r["gold_counts"], r["pred_counts"], Path(d) / "l", "test")
        assert all(Path(f).stat().st_size > 1000 for f in files), files


def run_all():
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = skipped = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Skip as e:
            skipped += 1
            print(f"[SKIP] {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {type(e).__name__}: {e}")
    print(f"SUMMARY: {len(tests) - failed - skipped} pass, {failed} fail, {skipped} skip")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run_all()
