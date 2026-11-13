"""Tests for src/audit.py (no GPU, no data). Run:  python tests/test_audit.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import audit, generate  # noqa: E402
from src.data import Item, load_config  # noqa: E402
from src.seeds import generation_seed  # noqa: E402

CFG = load_config()
DEV = ["10", "11", "12"]
TEST = ["20", "21"]


def good_records():
    out = []
    for i, k in enumerate(DEV):
        raw = json.dumps({"decision": "yes", "conclusion": "c", "certainty": "high"})
        out.append({"run_id": f"dev_b0|{k}|P0|s0", "key": k, "prompt_id": "P0", "sample_idx": 0, "item_index": i,
                    "seed": generation_seed(i, 0, 0), "decoding": generate.decoding_for(CFG, "greedy", "pubmedqa"),
                    "raw_text": raw, "decision": "yes", "certainty": "high", "n_out_tokens": 30,
                    "model_id": CFG["model"]["id"], "model_revision": CFG["model"]["revision"]})
    return out


def failed(recs):
    return sorted(n for n, (ok, _) in audit.record_checks(recs, CFG, DEV, TEST).items() if not ok)


def test_record_checks_pass_on_good_records():
    assert failed(good_records()) == []


def test_record_checks_catch_each_problem():
    r = good_records(); r[0]["key"] = "20"
    assert "no test-pool item" in failed(r) and "one record per dev item" in failed(r)
    r = good_records(); r[1]["decoding"] = dict(r[1]["decoding"], do_sample=True)
    assert failed(r) == ["decoding = protocol greedy"]
    r = good_records(); r[2]["seed"] = 5
    assert failed(r) == ["item index and seed formula"]
    r = good_records(); r[0]["decision"] = "no"
    assert failed(r) == ["stored decision = re-parse of raw text"]
    r = good_records(); r[0]["n_out_tokens"] = CFG["decoding"]["greedy"]["max_new_tokens"]
    assert failed(r) == ["no output cut at max_new_tokens"]
    r = good_records(); r[0]["model_revision"] = "main"
    assert failed(r) == ["model id and revision"]


def test_parse_one_word():
    assert audit.parse_one_word("Yes.") == "yes"
    assert audit.parse_one_word("  maybe") == "maybe"
    assert audit.parse_one_word("**No**, because") == "no"
    assert audit.parse_one_word("Nobody knows") == "invalid"
    assert audit.parse_one_word("The answer is yes") == "invalid"


def test_diag_prompts_fill_and_differ_from_p0_only_in_format():
    it = Item("1", "Does X help?", ("ctx a", "ctx b"), "yes", "X helps a lot.", "2000")
    p = {"system": "sys"}
    d1 = audit.diag_messages(it, "D1_one_word", p)[1]["content"]
    d2 = audit.diag_messages(it, "D2_conclusion_first", p)[1]["content"]
    for u in (d1, d2):
        assert "ctx a\n\nctx b" in u and "Does X help?" in u and "X helps a lot." not in u
    assert d1.endswith("exactly one word: yes, no, or maybe.")
    assert d2.index('"conclusion"') < d2.index('"decision"')
    bad = Item("2", "Q?", ("the conclusion is here",), "no", "the conclusion is here", "2000")
    try:
        audit.diag_messages(bad, "D1_one_word", p)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_diag_ids_stratified_and_deterministic():
    ids = [str(i) for i in range(500)]
    labels = {k: ("yes" if int(k) < 276 else "no" if int(k) < 445 else "maybe") for k in ids}
    a = audit.diag_ids(ids, labels)
    assert a == audit.diag_ids(list(reversed(ids)), labels)
    counts = [sum(labels[k] == l for k in a) for l in ("yes", "no", "maybe")]
    assert counts == [55, 34, 11], counts


def test_compare_by_hand():
    gold = {"1": "yes", "2": "no", "3": "maybe", "4": "yes"}
    a = {"1": "yes", "2": "maybe", "3": "maybe", "4": "maybe"}
    b = {"1": "yes", "2": "no", "3": "no", "4": "yes"}
    c = audit.compare(gold, a, b)
    assert c["a"]["accuracy"] == 0.5 and c["b"]["accuracy"] == 0.75
    assert c["only_a_right"] == 1 and c["only_b_right"] == 2 and c["agreement"] == 0.25
    assert c["a"]["pred_counts"]["maybe"] == 3 and c["mcnemar_p"] == 1.0


def test_certainty_table():
    r = good_records(); r[0]["certainty"] = None
    assert audit.certainty_table(r) == {"yes": {"missing": 1, "high": 2}}


def run_all():
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)]
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
