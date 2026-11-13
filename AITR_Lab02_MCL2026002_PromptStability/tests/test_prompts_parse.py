"""Tests for src/prompts.py and src/parse.py. Run from the repository root:  python tests/test_prompts_parse.py
Part A: parser cases (no data). Part B: prompts built from real PQA-L items (needs data/raw).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data, parse, prompts  # noqa: E402

DATA_ROOT = Path(os.environ.get("DATA_ROOT", ROOT / "data" / "raw"))


# ---------- Part A: parser ----------
def test_parse_clean_json():
    r = parse.parse_decision('{"decision": "yes", "conclusion": "It helps.", "certainty": "high"}')
    assert r == {"decision": "yes", "conclusion": "It helps.", "certainty": "high", "parse_status": "json"}, r


def test_parse_real_qwen_output_from_env_test():
    # Exact greedy output from the Colab environment test, 2026-10-29 (dev PMID 10354335).
    raw = ('{"decision": "yes", "conclusion": "Medical students can contribute to quality assurance programmes in '
           'day surgery by identifying issues and making recommendations.", "certainty": "high"}')
    r = parse.parse_decision(raw)
    assert (r["decision"], r["certainty"], r["parse_status"]) == ("yes", "high", "json"), r


def test_parse_case_punctuation_and_fence():
    r = parse.parse_decision('```json\n{"decision": "No.", "conclusion": "x", "certainty": "Moderate"}\n```')
    assert (r["decision"], r["certainty"], r["parse_status"]) == ("no", "moderate", "json"), r


def test_parse_extra_text_falls_back_to_regex():
    r = parse.parse_decision('Here is my answer: {"decision": "maybe", "conclusion": "Unclear \\"so far\\"."} Thanks')
    assert (r["decision"], r["parse_status"]) == ("maybe", "regex"), r
    assert r["conclusion"] == 'Unclear \\"so far\\".', r


def test_parse_invalid_cases():
    for raw in ["", "Yes, it does.", '{"decision": "probably"}', '{"answer": "yes"}', "not json {"]:
        r = parse.parse_decision(raw)
        assert r["decision"] == "invalid" and r["parse_status"] == "invalid", (raw, r)


def test_parse_missing_optional_fields():
    r = parse.parse_decision('{"decision": "yes"}')
    assert (r["decision"], r["conclusion"], r["certainty"]) == ("yes", None, None), r


def test_parse_gsm8k():
    assert parse.parse_gsm8k("3 + 4 = 7. The answer is 7.") == "7"
    assert parse.parse_gsm8k("The answer is 5. Wait, no. The answer is $1,250.") == "1250"
    assert parse.parse_gsm8k("The answer is 18.00") == "18"
    assert parse.parse_gsm8k("The answer is -3.5") == "-3.5"
    assert parse.parse_gsm8k("I think it is 7.") is None
    assert parse.normalise_number("1,234") == "1234"
    assert parse.normalise_number("abc") is None


# ---------- Part B: prompts from real items ----------
def _items():
    return data.load_pqal(DATA_ROOT)


def test_prompts_file():
    p = prompts.load_prompts()
    assert "P0" in prompts.available_prompt_ids(p)
    assert "{context}" in p["prompts"]["P0"] and "{question}" in p["prompts"]["P0"]
    assert "{context}" not in p["question_only"]


def test_build_messages_all_items_no_leak():
    p = prompts.load_prompts()
    for it in _items().values():
        for pid in prompts.available_prompt_ids(p) + ["question_only"]:
            msgs = prompts.build_messages(it, pid, p)       # raises if long_answer leaks
            assert [m["role"] for m in msgs] == ["system", "user"]
            assert it.question in msgs[1]["content"]
            if pid == "question_only":
                assert data.format_context(it.contexts) not in msgs[1]["content"]
            else:
                assert data.format_context(it.contexts) in msgs[1]["content"]
                assert '{"decision": "yes" | "no" | "maybe"' in msgs[1]["content"]


def test_build_messages_unknown_prompt():
    it = next(iter(_items().values()))
    try:
        prompts.build_messages(it, "P9", prompts.load_prompts())
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_gsm8k_messages():
    p = prompts.load_prompts()
    msgs = prompts.build_gsm8k_messages({"question": "What is 2+2?"}, p)
    assert "What is 2+2?" in msgs[1]["content"] and "The answer is" in msgs[1]["content"]


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
