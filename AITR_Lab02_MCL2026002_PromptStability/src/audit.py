"""Baseline audit helpers (Prompt 10). Development pool only; nothing here changes B0 or the protocol.

Checks the saved dev_b0 records against the configuration, and defines two diagnostic prompt formats used
to explain the gap to the published zero-shot number. The diagnostic templates live here, not in
configs/prompts.yaml, so the recorded prompts.yaml hash is unchanged.
"""
import re
from collections import Counter

from src import metrics as M
from src.data import format_context, stratified_sample
from src.generate import decoding_for
from src.parse import parse_decision
from src.seeds import generation_seed

DIAG_SEED = 31          # seed for the 100-item diagnostic sample (development pool); not a protocol seed
DIAG_SIZE = 100

_HEAD = ("Evidence (abstract without its conclusion):\n{context}\n\nResearch question: {question}\n\n"
         "Based only on this evidence, answer the research question")
DIAG_PROMPTS = {
    # D1: the "basic setting" of the published comparison, a direct answer with no JSON.
    "D1_one_word": _HEAD + " with exactly one word: yes, no, or maybe.",
    # D2: P0 with the JSON fields reordered, so the model writes its conclusion before the decision.
    "D2_conclusion_first": _HEAD + ". Reply with one JSON object:\n"
    '{{"conclusion": "<one sentence>", "decision": "yes" | "no" | "maybe", "certainty": "high" | "moderate" | "low"}}',
}
_ONE_WORD = re.compile(r"^\W*(yes|no|maybe)\b", re.I)


def parse_one_word(raw):
    m = _ONE_WORD.match(raw)
    return m.group(1).lower() if m else "invalid"


def diag_decision(prompt_id, raw):
    return parse_one_word(raw) if prompt_id == "D1_one_word" else parse_decision(raw)["decision"]


def diag_messages(item, prompt_id, prompts):
    user = DIAG_PROMPTS[prompt_id].format(context=format_context(item.contexts), question=item.question)
    if item.long_answer.strip() and item.long_answer.strip() in user:
        raise ValueError(f"{item.pubid}: long_answer found in prompt {prompt_id}")
    return [{"role": "system", "content": prompts["system"]}, {"role": "user", "content": user}]


def diag_ids(dev_ids, labels):
    return stratified_sample(dev_ids, labels, DIAG_SIZE, DIAG_SEED)


def record_checks(recs, cfg, dev_ids, test_ids):
    """{check name: (passed, detail)} for the dev_b0 records."""
    dev_index = {k: i for i, k in enumerate(dev_ids)}
    keys = [r["key"] for r in recs]
    greedy = decoding_for(cfg, "greedy", "pubmedqa")
    max_new = greedy["max_new_tokens"]
    bad_seed = [r["run_id"] for r in recs if r["key"] in dev_index and
                (r["item_index"] != dev_index[r["key"]] or r["seed"] != generation_seed(dev_index[r["key"]], 0, 0))]
    reparsed = [r["run_id"] for r in recs if parse_decision(r["raw_text"])["decision"] != r["decision"]]
    m = cfg["model"]
    c = {
        "one record per dev item": (len(recs) == len(dev_ids) and set(keys) == set(dev_ids) and len(set(keys)) == len(keys),
                                    f"{len(recs)} records, {len(set(keys))} distinct items, {len(dev_ids)} expected"),
        "no test-pool item": (not set(keys) & set(test_ids), f"{len(set(keys) & set(test_ids))} test items found"),
        "prompt P0, sample 0": (all(r["prompt_id"] == "P0" and r["sample_idx"] == 0 for r in recs), ""),
        "decoding = protocol greedy": (all(r["decoding"] == greedy for r in recs), str(greedy)),
        "model id and revision": (all(r.get("model_id") == m["id"] and r.get("model_revision") == m["revision"]
                                      for r in recs), f"{m['id']} @ {m['revision'][:8]}"),
        "item index and seed formula": (not bad_seed, f"{len(bad_seed)} mismatches {bad_seed[:3]}"),
        "stored decision = re-parse of raw text": (not reparsed, f"{len(reparsed)} mismatches {reparsed[:3]}"),
        "no output cut at max_new_tokens": (all(r["n_out_tokens"] < max_new for r in recs),
                                            f"{sum(r['n_out_tokens'] >= max_new for r in recs)} hit {max_new}"),
    }
    return c


def certainty_table(recs):
    """{decision: {certainty: count}} with None shown as 'missing'."""
    t = {}
    for r in recs:
        t.setdefault(r["decision"], Counter())[r.get("certainty") or "missing"] += 1
    return {d: dict(v) for d, v in sorted(t.items())}


def compare(gold, pred_a, pred_b):
    """Paired comparison on the same items: accuracy, macro-F1, 'maybe' count, agreement, exact McNemar p."""
    ids = sorted(gold)
    g = [gold[i] for i in ids]
    a = [pred_a[i] for i in ids]
    b = [pred_b[i] for i in ids]
    ca = [x == y for x, y in zip(g, a)]
    cb = [x == y for x, y in zip(g, b)]
    only_a, only_b, p_value = M.mcnemar_exact(ca, cb)
    out = {"n": len(ids), "agreement": sum(x == y for x, y in zip(a, b)) / len(ids),
           "only_a_right": only_a, "only_b_right": only_b, "mcnemar_p": p_value}
    for name, p, c in (("a", a, ca), ("b", b, cb)):
        out[name] = {"accuracy": sum(c) / len(c), "macro_f1": M.macro_f1(g, p),
                     "pred_counts": {k: p.count(k) for k in M.ALL_LABELS}}
    return out
