"""Prompt 10 baseline audit on the development pool. From the repository root:

    python scripts/audit_baseline.py --check static    # CPU: records, split, decoding, re-scoring, 'maybe' pattern
    python scripts/audit_baseline.py --check repro     # GPU: 20 pilot items rerun; exact match; attention mask; config
    python scripts/audit_baseline.py --check format    # GPU: 100 items x 2 diagnostic answer formats (D1, D2)
    python scripts/audit_baseline.py --check quant8    # GPU: the same 100 items with P0 in 8-bit instead of 4-bit

Each check writes results/audit/<check>.json; the GPU checks also keep their generations in
results/audit/<check>.jsonl (resumable). No test-pool item is used.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import audit, data, evaluate, generate, prompts  # noqa: E402
from src import metrics as M  # noqa: E402

OUT = ROOT / "results" / "audit"


def setup(data_root):
    cfg = data.load_config()
    items = data.load_pqal(data_root, cfg["data"]["ori_pqal_sha256"])
    dev_ids, test_ids = data.load_official_split(data_root)
    recs = evaluate.load_records(ROOT / "results" / "generations" / "dev_b0.jsonl")
    gold = {i: items[i].final_decision for i in dev_ids}
    return cfg, items, dev_ids, test_ids, recs, gold


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2))
    print(f"saved results/audit/{name}.json")


def check_static(cfg, items, dev_ids, test_ids, recs, gold, data_root):
    rep = {"record_checks": {}}
    print("A. Records, split and configuration")
    for name, (ok, detail) in audit.record_checks(recs, cfg, dev_ids, test_ids).items():
        rep["record_checks"][name] = {"pass": ok, "detail": detail}
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")

    print("B. Independent re-scoring with scikit-learn")
    from sklearn.metrics import accuracy_score, f1_score
    pred = evaluate.single_predictions(recs, dev_ids)
    g = [gold[i] for i in dev_ids]
    p = [pred[i] for i in dev_ids]
    sk = {"accuracy": accuracy_score(g, p), "macro_f1": f1_score(g, p, average="macro", labels=list(M.GOLD_LABELS))}
    saved = json.load(open(ROOT / "results" / "tables" / "dev_b0_metrics.json"))
    rep["sklearn"] = sk
    for k in sk:
        print(f"  {k}: sklearn {sk[k]:.6f}   saved {saved[k]:.6f}   {'MATCH' if abs(sk[k] - saved[k]) < 1e-12 else 'DIFFERENT'}")

    print("C. Exact prompt: token counts rebuilt with the tokenizer (first 20 items)")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(cfg["model"]["id"], revision=cfg["model"]["revision"])
    p_cfg = prompts.load_prompts()
    by_key = {r["key"]: r for r in recs}
    same = 0
    for k in dev_ids[:20]:
        ids = tok.apply_chat_template(prompts.build_messages(items[k], "P0", p_cfg), add_generation_prompt=True)
        ids = ids["input_ids"] if not isinstance(ids, list) else ids
        same += len(ids) == by_key[k]["n_in_tokens"]
    rep["prompt_token_counts_match"] = f"{same}/20"
    print(f"  {same}/20 prompts rebuild to the same number of input tokens as recorded")
    lens = sorted(r["n_in_tokens"] for r in recs)
    print(f"  input tokens: min {lens[0]}, median {lens[len(lens) // 2]}, max {lens[-1]}")

    print("D. The 'maybe' pattern")
    rep["certainty_by_decision"] = audit.certainty_table(recs)
    print("  certainty by predicted decision:", rep["certainty_by_decision"])
    hi = [r for r in recs if r.get("certainty") == "high"]
    if hi:
        print(f"  accuracy when certainty = high: {sum(gold[r['key']] == r['decision'] for r in hi) / len(hi):.3f} (n = {len(hi)})")
    moved = [r for r in recs if r["decision"] == "maybe" and gold[r["key"]] != "maybe"]
    print(f"  {len(moved)} gold yes/no items predicted 'maybe'. First 8 (gold | certainty | model's conclusion):")
    for r in moved[:8]:
        print(f"   - {r['key']} | gold {gold[r['key']]} | {r.get('certainty')} | {r.get('conclusion')}")
    rep["maybe_examples"] = [{"key": r["key"], "gold": gold[r["key"]], "raw_text": r["raw_text"]} for r in moved[:8]]

    print("E. Official evaluation script (printed so its metric can be compared with ours)")
    ev = Path(data_root) / "pubmedqa" / "evaluation.py"
    print(ev.read_text() if ev.exists() else f"  not found at {ev}")
    save("static", rep)


def rerun(fn, msgs, decoding, explicit_mask):
    import torch
    tok, model = fn.tokenizer, fn.model
    enc = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    ids = (enc if hasattr(enc, "shape") else enc["input_ids"]).to(model.device)
    kw = {"attention_mask": torch.ones_like(ids)} if explicit_mask else {}
    with torch.no_grad():
        out = model.generate(ids, pad_token_id=tok.eos_token_id, **kw, **decoding)
    return tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)


def check_repro(cfg, items, dev_ids, test_ids, recs, gold):
    from src.seeds import set_all_seeds
    fn, meta = generate.make_hf_generate_fn(cfg)
    print("Effective generation config of the loaded model:")
    print(fn.model.generation_config)
    print("pad_token_id used:", fn.tokenizer.eos_token_id, repr(fn.tokenizer.eos_token),
          "| tokenizer pad token:", fn.tokenizer.pad_token_id, repr(fn.tokenizer.pad_token))
    by_key = {r["key"]: r for r in recs}
    decoding = generate.decoding_for(cfg, "greedy", "pubmedqa")
    p_cfg = prompts.load_prompts()
    pilot = json.load(open(ROOT / "configs" / "ids_pilot.json"))
    rows, same_runner, same_mask = [], 0, 0
    for k in pilot:
        msgs = prompts.build_messages(items[k], "P0", p_cfg)
        set_all_seeds(by_key[k]["seed"])
        a, _, _ = fn(msgs, decoding)
        set_all_seeds(by_key[k]["seed"])
        b = rerun(fn, msgs, decoding, explicit_mask=True)
        same_runner += a == by_key[k]["raw_text"]
        same_mask += b == by_key[k]["raw_text"]
        rows.append({"key": k, "runner_identical": a == by_key[k]["raw_text"], "mask_identical": b == by_key[k]["raw_text"],
                     "saved": by_key[k]["decision"], "rerun": audit.parse_decision(a)["decision"]})
    print(f"Rerun with the runner's own call: {same_runner}/{len(pilot)} raw texts identical to dev_b0")
    print(f"Rerun with an explicit attention mask: {same_mask}/{len(pilot)} identical to dev_b0")
    for r in rows:
        if not (r["runner_identical"] and r["mask_identical"]):
            print("  differs:", r)
    save("repro", {"runner_identical": same_runner, "mask_identical": same_mask, "n": len(pilot), "rows": rows,
                   "generation_config": fn.model.generation_config.to_dict(), "meta": meta})


def diag_tasks(name, cfg, items, keys, prompt_ids, message_fn, parser="pubmedqa"):
    base = generate.build_tasks("dev_b0", keys, cfg, prompts.load_prompts(), items=items)
    tasks = []
    for t in base:
        for pid in prompt_ids:
            tasks.append(dict(t, run_id=f"audit_{name}|{t['key']}|{pid}|s0", condition=f"audit_{name}",
                              prompt_id=pid, messages=message_fn(items[t["key"]], pid), parser=parser))
    return tasks


def summarise(name, cfg, gold, recs, keys, prompt_ids, out_recs):
    p0 = {r["key"]: r["decision"] for r in recs}
    g = {k: gold[k] for k in keys}
    res = {}
    for pid in prompt_ids:
        pred = {r["key"]: audit.diag_decision(pid, r["raw_text"]) for r in out_recs if r["prompt_id"] == pid}
        c = audit.compare(g, {k: p0[k] for k in keys}, pred)
        res[pid] = c
        print(f"{pid} vs P0 (4-bit) on the same {c['n']} items:")
        print(f"   P0   accuracy {c['a']['accuracy']:.3f}  macro-F1 {c['a']['macro_f1']:.3f}  predicted {c['a']['pred_counts']}")
        print(f"   {pid} accuracy {c['b']['accuracy']:.3f}  macro-F1 {c['b']['macro_f1']:.3f}  predicted {c['b']['pred_counts']}")
        print(f"   same label on {c['agreement']:.0%} of items; only P0 right {c['only_a_right']}, "
              f"only {pid} right {c['only_b_right']}, exact McNemar p = {c['mcnemar_p']:.3f}")
    save(name, res)


def check_format(cfg, items, dev_ids, test_ids, recs, gold):
    labels = {k: v.final_decision for k, v in items.items()}
    keys = audit.diag_ids(dev_ids, labels)
    print(f"diagnostic sample: {len(keys)} dev items, labels {dict((l, sum(labels[k] == l for k in keys)) for l in M.GOLD_LABELS)}")
    pids = list(audit.DIAG_PROMPTS)
    p_cfg = prompts.load_prompts()
    tasks = diag_tasks("format", cfg, items, keys, pids, lambda it, pid: audit.diag_messages(it, pid, p_cfg))
    print("Note: the 'invalid so far' counter below uses the JSON parser, so it counts every D1 one-word answer. "
          "Ignore it; D1 is scored with its own one-word parser in the summary.")
    fn, meta = generate.make_hf_generate_fn(cfg)
    generate.run_tasks(tasks, fn, OUT / "format.jsonl", meta)
    summarise("format", cfg, gold, recs, keys, pids, evaluate.load_records(OUT / "format.jsonl"))


def check_quant8(cfg, items, dev_ids, test_ids, recs, gold):
    from transformers import BitsAndBytesConfig
    labels = {k: v.final_decision for k, v in items.items()}
    keys = audit.diag_ids(dev_ids, labels)
    p_cfg = prompts.load_prompts()
    tasks = diag_tasks("quant8", cfg, items, keys, ["P0_8bit"], lambda it, pid: prompts.build_messages(it, "P0", p_cfg))
    fn, meta = generate.make_hf_generate_fn(cfg, quantization_config=BitsAndBytesConfig(load_in_8bit=True))
    meta["quantisation"] = "8-bit (audit only)"
    generate.run_tasks(tasks, fn, OUT / "quant8.jsonl", meta)
    summarise("quant8", cfg, gold, recs, keys, ["P0_8bit"], evaluate.load_records(OUT / "quant8.jsonl"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, choices=["static", "repro", "format", "quant8"])
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    args = ap.parse_args()
    ctx = setup(args.data_root)
    if args.check == "static":
        check_static(*ctx, args.data_root)
    else:
        {"repro": check_repro, "format": check_format, "quant8": check_quant8}[args.check](*ctx)


if __name__ == "__main__":
    main()
