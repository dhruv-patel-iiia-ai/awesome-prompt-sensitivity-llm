"""Environment test for the prompt-stability study (Prompt 08).

Level 1 (default): system, packages, GPU, seed controls and dataset files. No model download.
Level 2 (--with-model): loads Qwen2.5-7B-Instruct in 4-bit and runs two greedy generations
and two seeded sampled generations on one development item.

Every check prints one line: [PASS] / [WARN] / [FAIL] name: detail.
A JSON report is written to results/env/env_report.json and package versions to results/env/env.txt.
Exit code is 0 when there is no FAIL, otherwise 1.
"""
import argparse
import hashlib
import importlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.seeds import set_all_seeds  # noqa: E402

# Values measured on the pinned files on 2026-10-28 (see research_decisions.md).
PQAL_SHA256 = "8b3276be8942ebbd77f3ddcda12c1749bf0e490045a736fd8438ee40cf37a41d"
GT_SHA256 = "939fe566f09017d13b1ca64d2ddfee0bc2374b366048152997669cccedc44d51"
GSM8K_TEST_SHA256 = "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14"
PQAL_LABELS = {"yes": 552, "no": 338, "maybe": 110}
TEST_LABELS = {"yes": 276, "no": 169, "maybe": 55}
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
PACKAGES = ["torch", "transformers", "accelerate", "bitsandbytes", "numpy", "pandas", "scipy", "sklearn", "yaml"]

results = []


def report(status, name, detail=""):
    results.append({"status": status, "check": name, "detail": str(detail)})
    print(f"[{status}] {name}: {detail}", flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def version_tuple(v):
    out = []
    for part in v.split("+")[0].split(".")[:3]:
        digits = "".join(c for c in part if c.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out)


def check_system():
    v = sys.version_info
    report("PASS" if v >= (3, 10) else "WARN", "python", platform.python_version())
    report("PASS", "platform", f"{platform.platform()} | CPUs {os.cpu_count()}")
    try:
        mem = {l.split(":")[0]: l.split()[1] for l in open("/proc/meminfo")}
        gb = int(mem["MemTotal"]) / 1e6
        report("PASS" if gb >= 12 else "WARN", "RAM", f"{gb:.1f} GB")
    except OSError:
        report("WARN", "RAM", "could not read /proc/meminfo")
    free = shutil.disk_usage(ROOT).free / 1e9
    report("PASS" if free >= 25 else "WARN", "disk free", f"{free:.1f} GB (model needs about 15 GB)")


def check_packages():
    lines = [f"python=={platform.python_version()}"]
    for name in PACKAGES:
        try:
            mod = importlib.import_module(name)
            ver = getattr(mod, "__version__", "unknown")
            lines.append(f"{name}=={ver}")
            report("PASS", f"import {name}", ver)
        except Exception as e:  # report every failure, keep going
            report("FAIL", f"import {name}", f"{type(e).__name__}: {e}")
    try:
        import transformers
        ok = version_tuple(transformers.__version__) >= (4, 37, 0)
        report("PASS" if ok else "FAIL", "transformers >= 4.37 (Qwen2 support)", transformers.__version__)
    except Exception:
        pass
    out = ROOT / "results" / "env"
    out.mkdir(parents=True, exist_ok=True)
    (out / "env.txt").write_text("\n".join(lines) + "\n")


def check_gpu():
    try:
        smi = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=20)
        report("PASS" if smi.returncode == 0 else "WARN", "nvidia-smi", smi.stdout.strip() or smi.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as e:
        report("WARN", "nvidia-smi", f"not available ({type(e).__name__})")
    try:
        import torch
    except Exception:
        report("FAIL", "torch.cuda", "torch not importable")
        return
    if not torch.cuda.is_available():
        report("FAIL", "torch.cuda", f"no CUDA device (torch {torch.__version__}, built for CUDA {torch.version.cuda})")
        return
    p = torch.cuda.get_device_properties(0)
    report("PASS", "torch.cuda", f"{p.name} | compute capability {p.major}.{p.minor} | "
                                 f"{p.total_memory / 1e9:.1f} GB | CUDA {torch.version.cuda}")
    report("PASS" if p.total_memory / 1e9 >= 14 else "WARN", "GPU memory >= 14 GB", f"{p.total_memory / 1e9:.1f} GB")
    report("PASS", "bfloat16 supported", torch.cuda.is_bf16_supported())


def check_seeds():
    set_all_seeds(123)
    a = [random.random() for _ in range(3)]
    set_all_seeds(123)
    b = [random.random() for _ in range(3)]
    report("PASS" if a == b else "FAIL", "python random seed", "reproducible" if a == b else f"{a} != {b}")
    try:
        import numpy as np
        set_all_seeds(123); x = np.random.rand(3)
        set_all_seeds(123); y = np.random.rand(3)
        report("PASS" if (x == y).all() else "FAIL", "numpy seed", "reproducible")
    except Exception as e:
        report("FAIL", "numpy seed", e)
    try:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        set_all_seeds(123); x = torch.randn(3, device=dev)
        set_all_seeds(123); y = torch.randn(3, device=dev)
        report("PASS" if torch.equal(x, y) else "FAIL", f"torch seed ({dev})", "reproducible")
    except Exception as e:
        report("FAIL", "torch seed", e)


def check_data(data_root):
    pq = data_root / "pubmedqa" / "data"
    ori = pq / "ori_pqal.json"
    if not ori.exists():
        report("FAIL", "PubMedQA ori_pqal.json", f"missing at {ori}; run scripts/setup_data.sh")
        return
    digest = sha256(ori)
    report("PASS" if digest == PQAL_SHA256 else "FAIL", "ori_pqal.json sha256", digest[:16] + "...")
    d = json.load(open(ori))
    counts = {k: sum(v["final_decision"] == k for v in d.values()) for k in PQAL_LABELS}
    report("PASS" if len(d) == 1000 and counts == PQAL_LABELS else "FAIL", "PQA-L items and labels",
           f"{len(d)} items, {counts}")
    fields = set(next(iter(d.values())))
    need = {"QUESTION", "CONTEXTS", "final_decision", "LONG_ANSWER"}
    report("PASS" if need <= fields else "FAIL", "PQA-L fields", sorted(fields))
    leaked = sum(v["LONG_ANSWER"].strip() in " ".join(v["CONTEXTS"]) for v in d.values())
    report("PASS" if leaked == 0 else "FAIL", "long answer absent from contexts", f"{leaked} items contain it")

    gt_path = pq / "test_ground_truth.json"
    test_path = pq / "test_set.json"
    if gt_path.exists():
        gd = sha256(gt_path)
        report("PASS" if gd == GT_SHA256 else "FAIL", "test_ground_truth.json sha256", gd[:16] + "...")
    if not test_path.exists():
        report("FAIL", "official split", f"{test_path} missing; run split_dataset.py pqal (scripts/setup_data.sh)")
        return
    t = json.load(open(test_path))
    tcounts = {k: sum(v["final_decision"] == k for v in t.values()) for k in TEST_LABELS}
    report("PASS" if len(t) == 500 and tcounts == TEST_LABELS else "FAIL", "test split", f"{len(t)} items, {tcounts}")
    if gt_path.exists():
        gt = json.load(open(gt_path))
        same = set(gt) == set(t) and all(gt[p] == t[p]["final_decision"] for p in t)
        report("PASS" if same else "FAIL", "test split == test_ground_truth.json", same)
    dev = set()
    for i in range(10):
        f = pq / f"pqal_fold{i}" / "dev_set.json"
        if f.exists():
            dev |= set(json.load(open(f)))
    report("PASS" if len(dev) == 500 and not dev & set(t) else "FAIL", "CV dev folds",
           f"{len(dev)} items, overlap with test = {len(dev & set(t))}")


def check_gsm8k(data_root):
    gsm = data_root / "gsm8k" / "test.jsonl"
    if gsm.exists():
        rows = [json.loads(l) for l in open(gsm)]
        ok = sha256(gsm) == GSM8K_TEST_SHA256 and len(rows) == 1319 and all("####" in r["answer"] for r in rows)
        report("PASS" if ok else "FAIL", "GSM8K test.jsonl", f"{len(rows)} problems, sha256 match "
                                                             f"{sha256(gsm) == GSM8K_TEST_SHA256}")
    else:
        report("FAIL", "GSM8K test.jsonl", f"missing at {gsm}; run scripts/setup_data.sh")


def check_model(data_root):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    t0 = time.time()
    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=MODEL_REVISION, quantization_config=quant,
                                                 device_map="auto")
    report("PASS", "model load", f"{MODEL_ID}@{MODEL_REVISION[:8]} in {time.time() - t0:.0f} s, "
                                 f"GPU allocated {torch.cuda.memory_allocated() / 1e9:.1f} GB")

    # One development item (never a test item): first PMID of fold 0's dev set.
    pq = data_root / "pubmedqa" / "data"
    dev = json.load(open(pq / "pqal_fold0" / "dev_set.json"))
    pmid = sorted(dev)[0]
    item = dev[pmid]
    context = "\n\n".join(item["CONTEXTS"])
    user = ("Evidence (abstract without its conclusion):\n" + context + "\n\nResearch question: " + item["QUESTION"] +
            "\n\nBased only on this evidence, answer the research question. Reply with one JSON object:\n"
            '{"decision": "yes" | "no" | "maybe", "conclusion": "<one sentence>", '
            '"certainty": "high" | "moderate" | "low"}')
    messages = [{"role": "system", "content": "You are a careful biomedical research assistant. "
                                              "Answer only from the evidence provided."},
                {"role": "user", "content": user}]
    assert item["LONG_ANSWER"].strip() not in user
    inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
    if not hasattr(inputs, "shape"):  # some transformers versions return a dict-like BatchEncoding
        inputs = inputs["input_ids"]
    inputs = inputs.to(model.device)
    report("PASS", "prompt built", f"dev PMID {pmid}, {inputs.shape[1]} input tokens")

    def run(**kw):
        t = time.time()
        out = model.generate(inputs, max_new_tokens=128, repetition_penalty=1.0, pad_token_id=tok.eos_token_id, **kw)
        new = out[0, inputs.shape[1]:]
        return tok.decode(new, skip_special_tokens=True), len(new), time.time() - t

    g1, n1, s1 = run(do_sample=False)
    g2, _, _ = run(do_sample=False)
    report("PASS" if g1 == g2 else "WARN", "greedy determinism", "identical" if g1 == g2 else "outputs differ")
    report("PASS", "greedy throughput", f"{n1} tokens in {s1:.1f} s = {n1 / s1:.1f} tokens/s")
    print("----- greedy output -----\n" + g1 + "\n-------------------------")
    try:
        parsed = json.loads(g1[g1.index("{"):g1.rindex("}") + 1])
        report("PASS", "JSON output parses", parsed.get("decision"))
    except ValueError:
        report("WARN", "JSON output parses", "not parseable (parser fallback will be needed)")

    sk = dict(do_sample=True, temperature=0.7, top_p=1.0, top_k=0)
    set_all_seeds(1000 * 0 + 10 * 0 + 1); a, _, _ = run(**sk)
    set_all_seeds(1000 * 0 + 10 * 0 + 1); b, _, _ = run(**sk)
    report("PASS" if a == b else "WARN", "seeded sampling reproducible", "identical" if a == b else "outputs differ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-model", action="store_true", help="also run Level 2 (downloads about 15 GB)")
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    args = ap.parse_args()
    data_root = Path(args.data_root)

    print(f"Environment test started {time.strftime('%Y-%m-%d %H:%M:%S')} in {ROOT}")
    for fn in (check_system, check_packages, check_gpu, check_seeds):
        fn()
    check_data(data_root)
    check_gsm8k(data_root)
    if args.with_model:
        try:
            check_model(data_root)
        except Exception as e:
            report("FAIL", "Level 2 model test", f"{type(e).__name__}: {e}")

    n = {k: sum(r["status"] == k for r in results) for k in ("PASS", "WARN", "FAIL")}
    print(f"SUMMARY: {n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail")
    out = ROOT / "results" / "env"
    out.mkdir(parents=True, exist_ok=True)
    (out / "env_report.json").write_text(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                                     "with_model": args.with_model, "summary": n,
                                                     "checks": results}, indent=2))
    sys.exit(1 if n["FAIL"] else 0)


if __name__ == "__main__":
    main()
