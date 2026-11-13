"""Tests for src/metrics.py. Expected values are worked out by hand in the comments.
Run from the repository root:  python tests/test_metrics.py
"""
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import metrics as M  # noqa: E402

close = lambda a, b: abs(a - b) < 1e-9  # noqa: E731


def test_accuracy_and_invalid_is_wrong():
    assert close(M.accuracy(["yes", "no", "maybe", "yes"], ["yes", "invalid", "maybe", "no"]), 0.5)


def test_macro_f1_by_hand():
    gold = ["yes", "yes", "no", "maybe"]
    pred = ["yes", "no", "no", "invalid"]
    # yes: tp1 fp0 fn1 -> 2/3 ; no: tp1 fp1 fn0 -> 2/3 ; maybe: tp0 -> 0 ; mean = 4/9
    assert close(M.macro_f1(gold, pred), 4 / 9)


def test_maxp_avgp_cps():
    r = M.maxp_avgp_cps([0.8, 0.6, 0.7])          # MaxP .8, AvgP .7, CPS .8 * .9 = .72
    assert close(r["MaxP"], 0.8) and close(r["AvgP"], 0.7) and close(r["CPS"], 0.72)


def test_majority_vote_rules():
    assert M.majority_vote(["yes", "yes", "no"], "no") == "yes"
    assert M.majority_vote(["yes", "no"], "maybe") == "maybe"              # tie -> tie_break
    assert M.majority_vote(["invalid", "invalid", "no"], "yes") == "no"    # invalid does not vote
    assert M.majority_vote(["invalid"] * 3, "yes") == "yes"                # nothing valid -> tie_break


def test_gini_by_hand():
    assert close(M.gini(["yes"] * 4), 0.0)
    assert close(M.gini(["yes", "yes", "no", "no"]), 0.5)
    assert close(M.gini(["yes", "no", "maybe", "invalid"]), 0.75)


def test_decompose_extremes():
    d = M.decompose({"A": ["yes"] * 5, "B": ["no"] * 5})          # all between-prompt
    assert close(d["G"], 0.5) and close(d["W"], 0.0) and close(d["B"], 0.5), d
    d = M.decompose({"A": ["yes", "yes", "no", "no"], "B": ["yes", "yes", "no", "no"]})   # all within
    assert close(d["G"], 0.5) and close(d["W"], 0.5) and close(d["B"], 0.0), d
    d = M.decompose({"A": ["yes"] * 3, "B": ["yes"] * 3})
    assert d == {"G": 0.0, "W": 0.0, "B": 0.0}


def test_decompose_identity_random():
    rng = random.Random(0)
    for _ in range(200):
        item = {p: [rng.choice(M.ALL_LABELS) for _ in range(5)] for p in ("P0", "P1", "P2", "P3", "P4", "P5")}
        d = M.decompose(item)
        assert close(d["G"], d["W"] + d["B"]), d


def test_decompose_rejects_unequal_groups():
    try:
        M.decompose({"A": ["yes"], "B": ["yes", "no"]})
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_s_prompt():
    items = [{"A": ["yes"] * 5, "B": ["no"] * 5},                       # G .5, B .5
             {"A": ["yes", "yes", "no", "no", "yes"], "B": ["yes", "yes", "no", "no", "yes"]},  # G .48, B 0
             {"A": ["yes"] * 5, "B": ["yes"] * 5}]                       # 0, 0
    assert close(M.s_prompt(items), 0.5 / (0.5 + 0.48))
    assert math.isnan(M.s_prompt([{"A": ["no"] * 2, "B": ["no"] * 2}]))


def test_bias_corrected_W():
    item = {"A": ["yes", "no"], "B": ["yes", "no"]}                      # W .5 -> * 2/1 = 1.0
    assert close(M.bias_corrected_W(item), 1.0)


def test_conclusion_stability_by_hand():
    assert close(M.conclusion_stability(["yes", "yes", "no"]), 1 / 3)  # 3 pairs, 2 mismatches
    assert close(M.conclusion_stability(["no"] * 6), 1.0)


def test_mcnemar_by_hand():
    a = [True] * 5 + [False] * 5
    b = [False] * 5 + [False] * 5
    assert M.mcnemar_exact(a, b) == (5, 0, 0.0625)                     # 2 * (1/2)^5
    a = [True] * 9 + [False] * 1
    b = [False] * 9 + [True] * 1
    _, _, p = M.mcnemar_exact(a, b)                                     # 2 * (1 + 10) / 1024
    assert close(p, 22 / 1024)
    assert M.mcnemar_exact([True, False], [True, False]) == (0, 0, 1.0)


def test_holm_by_hand():
    adj = M.holm([0.04, 0.01])                                          # 0.01*2 = .02 ; max(.02, .04*1) = .04
    assert close(adj[0], 0.04) and close(adj[1], 0.02)


def test_cohen_kappa_by_hand():
    assert close(M.cohen_kappa(["yes", "yes", "no", "no"], ["yes", "no", "no", "no"]), 0.5)   # po .75, pe .5
    assert close(M.cohen_kappa(["yes", "no"], ["yes", "no"]), 1.0)


def test_bootstrap_ci_deterministic_and_brackets_point():
    units = [0, 1, 1, 0, 1, 1, 1, 0, 1, 1]
    mean = lambda xs: sum(xs) / len(xs)  # noqa: E731
    p1 = M.bootstrap_ci(units, mean, n_resamples=500, seed=7)
    p2 = M.bootstrap_ci(units, mean, n_resamples=500, seed=7)
    assert p1 == p2 and p1[1] <= p1[0] <= p1[2] and close(p1[0], 0.7)


def test_permutation_test_behaviour():
    determined = [{"A": ["yes"] * 5, "B": ["no"] * 5} for _ in range(10)]   # label fixed by prompt
    obs, p = M.permutation_test_B(determined, n_perm=200, seed=11)
    assert close(obs, 5.0) and p < 0.01, (obs, p)
    exchangeable = [{"A": ["yes", "no", "yes", "no"], "B": ["yes", "no", "yes", "no"]} for _ in range(10)]
    obs, p = M.permutation_test_B(exchangeable, n_perm=200, seed=11)
    assert close(obs, 0.0) and close(p, 1.0), (obs, p)                    # B = 0 can never be exceeded


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
