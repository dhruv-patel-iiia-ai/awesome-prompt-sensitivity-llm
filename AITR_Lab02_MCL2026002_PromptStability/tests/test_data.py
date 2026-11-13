"""Tests for src/data.py. Run from the repository root:  python tests/test_data.py
Part A uses small hand-made inputs (no data needed). Part B checks the real files in data/raw/.
"""
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data  # noqa: E402

DATA_ROOT = ROOT / "data" / "raw"


# ---------- Part A: unit tests on toy inputs ----------
def test_stratified_allocation():
    labels = {f"y{i}": "yes" for i in range(552)}
    labels.update({f"n{i}": "no" for i in range(338)})
    labels.update({f"m{i}": "maybe" for i in range(110)})
    s = data.stratified_sample(labels, labels, 100, seed=1)
    c = Counter(labels[i] for i in s)
    assert len(s) == 100 and len(set(s)) == 100
    assert (c["yes"], c["no"], c["maybe"]) == (55, 34, 11), c   # 55.2 / 33.8 / 11.0 -> largest remainder


def test_stratified_deterministic_and_order_free():
    labels = {str(i): ("yes", "no", "maybe")[i % 3] for i in range(90)}
    a = data.stratified_sample(list(labels), labels, 30, seed=7)
    b = data.stratified_sample(list(reversed(list(labels))), labels, 30, seed=7)
    c = data.stratified_sample(list(labels), labels, 30, seed=8)
    assert a == b, "result must not depend on input order"
    assert a != c, "different seed should give a different draw"
    assert a == sorted(a)


def test_stratified_too_large():
    try:
        data.stratified_sample(["a"], {"a": "yes"}, 2, seed=0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_format_context():
    assert data.format_context(["  A  b\nc ", "D"]) == "A b c\n\nD"


def test_gsm8k_parser():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "t.jsonl"
        p.write_text(json.dumps({"question": "q", "answer": "work\n#### 1,234"}) + "\n")
        assert data.load_gsm8k(p)[0]["answer_number"] == "1234"
        p.write_text(json.dumps({"question": "q", "answer": "work\n#### ten"}) + "\n")
        try:
            data.load_gsm8k(p)
        except ValueError:
            return
        raise AssertionError("expected ValueError for a non-numeric answer")


# ---------- Part B: checks on the real files ----------
def test_real_pqal():
    cfg = data.load_config()
    items = data.load_pqal(DATA_ROOT, cfg["data"]["ori_pqal_sha256"])
    c = Counter(i.final_decision for i in items.values())
    assert dict(c) == {"yes": 552, "no": 338, "maybe": 110}, c
    for it in items.values():
        ctx = data.format_context(it.contexts)
        assert it.long_answer.strip() not in ctx, f"{it.pubid}: long answer leaks into context"
        assert it.question.strip(), f"{it.pubid}: empty question"


def test_real_split_and_sets():
    cfg = data.load_config()
    dev, test = data.load_official_split(DATA_ROOT)
    with tempfile.TemporaryDirectory() as d:
        s1 = data.make_sets(cfg, DATA_ROOT, d)
        s2 = data.make_sets(cfg, DATA_ROOT, d)
        main = json.load(open(Path(d) / "ids_main.json"))
        rq3 = json.load(open(Path(d) / "ids_rq3.json"))
        pilot = json.load(open(Path(d) / "ids_pilot.json"))
    assert {k: v["sha256"] for k, v in s1.items()} == {k: v["sha256"] for k, v in s2.items()}, "not reproducible"
    assert s1["main"]["labels"] == {"yes": 55, "no": 34, "maybe": 11}, s1["main"]
    assert set(main) <= set(test) and set(rq3) <= set(main) and set(pilot) <= set(dev)
    assert not set(pilot) & set(test), "pilot items must come from the dev pool only"
    assert len(set(main)) == 100 and len(set(rq3)) == 20 and len(set(pilot)) == 20
    assert s1["gsm8k"]["n"] == 100


def run_all():
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {type(e).__name__}: {e}")
    print(f"SUMMARY: {len(tests) - failed} pass, {failed} fail")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run_all()
