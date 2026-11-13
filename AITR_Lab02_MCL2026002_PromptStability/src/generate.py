"""Generation runner with append-only checkpointing and resume (protocol v1, sections 1 and 4-6).

The model call is injected as generate_fn(messages, decoding) -> (text, n_in_tokens, n_out_tokens),
so the bookkeeping (tasks, seeds, resume, records) is testable without a GPU.
"""
import json
import os
import time
from pathlib import Path

from src import parse
from src.prompts import build_gsm8k_messages, build_messages
from src.seeds import generation_seed, set_all_seeds

ROOT = Path(__file__).resolve().parents[1]
# Fixed prompt indices for the seed formula, independent of which prompts a run uses.
PROMPT_INDEX = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5, "question_only": 9, "gsm8k_cot": 8}
# condition -> (id set, uses test pool, decoding name, samples per prompt, parser)
CONDITIONS = {
    "pilot_greedy":  ("pilot", False, "greedy", 1, "pubmedqa"),
    "pilot_sampled": ("pilot", False, "sampled", 5, "pubmedqa"),
    "dev_b0":        ("dev_all", False, "greedy", 1, "pubmedqa"),
    "b0":            ("test_all", True, "greedy", 1, "pubmedqa"),
    "main_greedy":   ("main", True, "greedy", 1, "pubmedqa"),
    "main_sampled":  ("main", True, "sampled", 5, "pubmedqa"),
    "question_only": ("main", True, "greedy", 1, "pubmedqa"),
    "gsm8k_greedy":  ("gsm8k", False, "greedy", 1, "gsm8k"),
    "gsm8k_sampled": ("gsm8k", False, "sampled", 10, "gsm8k"),
}


def check_condition_allowed(condition, cfg):
    """Test-pool conditions may only run once the protocol is frozen (protocol v1, section 12)."""
    if condition not in CONDITIONS:
        raise KeyError(f"unknown condition {condition!r}")
    uses_test = CONDITIONS[condition][1]
    if uses_test and not str(cfg.get("protocol_version", "")).startswith("v1-frozen"):
        raise PermissionError(f"{condition} uses the test pool; protocol_version is "
                              f"{cfg.get('protocol_version')!r}, not v1-frozen")


def decoding_for(cfg, name, parser):
    d = dict(cfg["decoding"][name])
    d.pop("samples_per_prompt", None)
    if parser == "gsm8k":
        d["max_new_tokens"] = cfg["decoding"]["gsm8k"]["max_new_tokens"]
    return d


def run_id(condition, key, prompt_id, sample_idx):
    return f"{condition}|{key}|{prompt_id}|s{sample_idx}"


def build_tasks(condition, ids, cfg, prompts, items=None, gsm8k=None, prompt_ids=("P0",)):
    """List of task dicts in a fixed order: item, then prompt, then sample.

    Greedy runs use sample_idx 0; sampled runs use 1..k, so their seeds never coincide.
    """
    _, _, dec_name, k, parser = CONDITIONS[condition]
    if condition == "question_only":
        prompt_ids = ("question_only",)
    if parser == "gsm8k":
        prompt_ids = ("gsm8k_cot",)
    decoding = decoding_for(cfg, dec_name, parser)
    samples = [0] if dec_name == "greedy" else list(range(1, k + 1))
    tasks = []
    for item_index, key in enumerate(ids):
        for prompt_id in prompt_ids:
            if parser == "gsm8k":
                messages = build_gsm8k_messages(gsm8k[int(key)], prompts)
            else:
                messages = build_messages(items[key], prompt_id, prompts)
            for s in samples:
                tasks.append({"run_id": run_id(condition, key, prompt_id, s), "condition": condition, "key": str(key),
                              "prompt_id": prompt_id, "item_index": item_index, "sample_idx": s,
                              "seed": generation_seed(item_index, PROMPT_INDEX[prompt_id], s),
                              "decoding": decoding, "parser": parser, "messages": messages})
    return tasks


def repair_tail(path):
    """Drop a partially written last line (e.g. after a Colab disconnect). Returns bytes removed."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return 0
    raw = path.read_bytes()
    if raw.endswith(b"\n"):
        return 0
    cut = raw.rfind(b"\n") + 1
    path.write_bytes(raw[:cut])
    return len(raw) - cut


def done_run_ids(path):
    path = Path(path)
    if not path.exists():
        return set()
    return {json.loads(line)["run_id"] for line in open(path) if line.strip()}


def run_tasks(tasks, generate_fn, out_path, meta, fsync_every=50, log_every=25):
    """Generate every task not yet in out_path, appending one JSON line per result. Returns a summary."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    removed = repair_tail(out_path)
    done = done_run_ids(out_path)
    todo = [t for t in tasks if t["run_id"] not in done]
    print(f"{len(tasks)} tasks: {len(tasks) - len(todo)} already done, {len(todo)} to run"
          + (f" (repaired {removed} bytes of a partial last line)" if removed else ""), flush=True)
    n_invalid, t_start = 0, time.time()
    with open(out_path, "a") as f:
        for n, t in enumerate(todo, 1):
            set_all_seeds(t["seed"])
            t0 = time.time()
            text, n_in, n_out = generate_fn(t["messages"], t["decoding"])
            latency = time.time() - t0
            if t["parser"] == "gsm8k":
                ans = parse.parse_gsm8k(text)
                parsed = {"answer": ans, "parse_status": "ok" if ans is not None else "invalid"}
            else:
                parsed = parse.parse_decision(text)
            n_invalid += parsed["parse_status"] == "invalid"
            rec = {k: t[k] for k in ("run_id", "condition", "key", "prompt_id", "item_index", "sample_idx", "seed")}
            rec.update({"decoding": t["decoding"], "raw_text": text, **parsed, "n_in_tokens": n_in,
                        "n_out_tokens": n_out, "latency_s": round(latency, 3),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), **meta})
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if n % fsync_every == 0:
                os.fsync(f.fileno())
            if n % log_every == 0 or n == len(todo):
                el = time.time() - t_start
                print(f"  {n}/{len(todo)} done, {el / n:.1f} s each, invalid so far {n_invalid}", flush=True)
        os.fsync(f.fileno())
    return {"tasks": len(tasks), "skipped": len(tasks) - len(todo), "generated": len(todo), "invalid": n_invalid,
            "seconds": round(time.time() - t_start, 1)}


def make_hf_generate_fn(cfg, quantization_config=None):
    """Load the pinned model in 4-bit and return (generate_fn, meta). Imports torch lazily.

    quantization_config overrides the protocol's 4-bit setting (Prompt 10 audit only, never for protocol runs).
    generate_fn.model and generate_fn.tokenizer expose the loaded objects for the audit's checks.
    """
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    m = cfg["model"]
    q = m["quantisation"]
    quant = BitsAndBytesConfig(load_in_4bit=q["load_in_4bit"], bnb_4bit_quant_type=q["bnb_4bit_quant_type"],
                               bnb_4bit_compute_dtype=getattr(torch, q["bnb_4bit_compute_dtype"]))
    tok = AutoTokenizer.from_pretrained(m["id"], revision=m["revision"])
    quant = quantization_config or quant
    extra = {"dtype": getattr(torch, m["dtype"])} if "dtype" in m else {}
    model = AutoModelForCausalLM.from_pretrained(m["id"], revision=m["revision"], quantization_config=quant,
                                                 device_map="auto", **extra)

    def generate_fn(messages, decoding):
        inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
        if not hasattr(inputs, "shape"):
            inputs = inputs["input_ids"]
        inputs = inputs.to(model.device)
        with torch.no_grad():
            out = model.generate(inputs, pad_token_id=tok.eos_token_id, **decoding)
        new = out[0, inputs.shape[1]:]
        return tok.decode(new, skip_special_tokens=True), int(inputs.shape[1]), int(len(new))

    generate_fn.model, generate_fn.tokenizer = model, tok
    import bitsandbytes
    meta = {"model_id": m["id"], "model_revision": m["revision"], "torch": torch.__version__,
            "transformers": transformers.__version__, "bitsandbytes": bitsandbytes.__version__,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"}
    return generate_fn, meta
