"""Tests for src/generate.py with a fake model (no GPU, no data). Run:  python tests/test_generate.py"""
import json
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import generate  # noqa: E402
from src.data import Item, load_config  # noqa: E402

CFG = load_config()
PROMPTS = {"system": "sys", "prompts": {"P0": "E: {context} Q: {question} A0", "P1": "Q: {question} E: {context} A1"},
           "question_only": "Q: {question} only", "gsm8k_system": "m", "gsm8k_cot": "{question} The answer is"}
ITEMS = {f"{i}": Item(f"{i}", f"question {i}?", (f"ctx {i}",), "yes", f"secret conclusion {i}", "2000")
         for i in range(4)}
IDS = sorted(ITEMS)


def fake_generate_fn(fail_after=None):
    """Deterministic in the seed set by run_tasks: output depends on random.random()."""
    calls = {"n": 0}

    def fn(messages, decoding):
        calls["n"] += 1
        if fail_after is not None and calls["n"] > fail_after:
            raise RuntimeError("simulated Colab disconnect")
        dec = "yes" if random.random() < 0.5 else "no"
        return json.dumps({"decision": dec, "conclusion": "c", "certainty": "low"}), 10, 5
    return fn


META = {"model_id": "fake", "model_revision": "0"}


def test_guard_blocks_test_pool_before_freeze():
    draft = {"protocol_version": "v1-draft"}
    for cond in ("b0", "main_greedy", "main_sampled", "question_only"):
        try:
            generate.check_condition_allowed(cond, draft)
            raise AssertionError(f"{cond} should be blocked")
        except PermissionError:
            pass
    for cond in ("pilot_greedy", "pilot_sampled", "dev_b0", "gsm8k_greedy", "gsm8k_sampled"):
        generate.check_condition_allowed(cond, draft)
    generate.check_condition_allowed("b0", {"protocol_version": "v1-frozen"})


def test_task_counts_and_unique_ids_and_seeds():
    g = generate.build_tasks("pilot_greedy", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0", "P1"))
    s = generate.build_tasks("pilot_sampled", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0", "P1"))
    assert len(g) == 4 * 2 * 1 and len(s) == 4 * 2 * 5, (len(g), len(s))
    allt = g + s
    assert len({t["run_id"] for t in allt}) == len(allt)
    assert len({t["seed"] for t in s}) == len(s), "sampled seeds must be unique within a condition"
    t = s[7]   # item 0, P1, sample 3 -> 1000*0 + 10*1 + 3
    assert (t["key"], t["prompt_id"], t["sample_idx"], t["seed"]) == ("0", "P1", 3, 13), t
    assert g[0]["decoding"]["do_sample"] is False and s[0]["decoding"]["do_sample"] is True
    assert "samples_per_prompt" not in s[0]["decoding"]
    assert s[0]["decoding"]["temperature"] == 0.7 and s[0]["decoding"]["top_k"] == 0


def test_question_only_and_no_leak():
    q = generate.build_tasks("question_only", IDS, CFG, PROMPTS, items=ITEMS)
    assert {t["prompt_id"] for t in q} == {"question_only"}
    assert all("ctx" not in t["messages"][1]["content"] for t in q)
    for t in generate.build_tasks("pilot_sampled", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0", "P1")):
        assert "secret conclusion" not in t["messages"][1]["content"]


def test_gsm8k_tasks_use_longer_limit():
    gsm = [{"idx": i, "question": f"q{i}", "answer_text": "", "answer_number": "1"} for i in range(3)]
    t = generate.build_tasks("gsm8k_sampled", [0, 2], CFG, PROMPTS, gsm8k=gsm)
    assert len(t) == 2 * 10 and t[0]["decoding"]["max_new_tokens"] == 384 and t[0]["parser"] == "gsm8k"


def test_resume_after_disconnect_no_duplicates():
    tasks = generate.build_tasks("pilot_sampled", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0", "P1"))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.jsonl"
        try:
            generate.run_tasks(tasks, fake_generate_fn(fail_after=13), out, META)
        except RuntimeError:
            pass
        assert len(out.read_text().splitlines()) == 13
        s = generate.run_tasks(tasks, fake_generate_fn(), out, META)
        assert (s["skipped"], s["generated"]) == (13, len(tasks) - 13), s
        ids = [json.loads(l)["run_id"] for l in out.read_text().splitlines()]
        assert len(ids) == len(set(ids)) == len(tasks)
        s2 = generate.run_tasks(tasks, fake_generate_fn(), out, META)
        assert s2["generated"] == 0


def test_seeded_outputs_reproducible_and_independent_of_resume():
    tasks = generate.build_tasks("pilot_sampled", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0",))
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.jsonl", Path(d) / "b.jsonl"
        generate.run_tasks(tasks, fake_generate_fn(), a, META)
        try:
            generate.run_tasks(tasks, fake_generate_fn(fail_after=7), b, META)
        except RuntimeError:
            pass
        generate.run_tasks(tasks, fake_generate_fn(), b, META)
        da = {json.loads(l)["run_id"]: json.loads(l)["decision"] for l in a.read_text().splitlines()}
        db = {json.loads(l)["run_id"]: json.loads(l)["decision"] for l in b.read_text().splitlines()}
        assert da == db, "an interrupted and resumed run must give the same outputs"
        assert len(set(da.values())) > 1, "fake model should produce both labels"


def test_partial_last_line_is_repaired():
    tasks = generate.build_tasks("pilot_greedy", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0",))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.jsonl"
        generate.run_tasks(tasks[:2], fake_generate_fn(), out, META)
        with open(out, "a") as f:
            f.write('{"run_id": "half-writ')
        s = generate.run_tasks(tasks, fake_generate_fn(), out, META)
        lines = out.read_text().splitlines()
        assert s["skipped"] == 2 and len(lines) == 4 and all(json.loads(l) for l in lines)


def test_record_fields():
    tasks = generate.build_tasks("pilot_greedy", IDS, CFG, PROMPTS, items=ITEMS, prompt_ids=("P0",))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.jsonl"
        generate.run_tasks(tasks[:1], fake_generate_fn(), out, META)
        rec = json.loads(out.read_text())
    need = {"run_id", "condition", "key", "prompt_id", "item_index", "sample_idx", "seed", "decoding", "raw_text",
            "decision", "conclusion", "certainty", "parse_status", "n_in_tokens", "n_out_tokens", "latency_s",
            "timestamp", "model_id", "model_revision"}
    assert need <= set(rec), need - set(rec)


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
