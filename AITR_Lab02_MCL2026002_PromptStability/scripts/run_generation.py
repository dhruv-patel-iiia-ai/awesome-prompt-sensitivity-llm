"""Run one generation condition with resume. From the repository root:

    python scripts/run_generation.py --condition pilot_greedy --prompts P0 --limit 3

Output: results/generations/<condition>.jsonl (one JSON record per generation).
Test-pool conditions refuse to run until configs/experiment.yaml says protocol_version: v1-frozen...
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data, generate, prompts  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=sorted(generate.CONDITIONS))
    ap.add_argument("--prompts", default="P0", help="comma-separated prompt ids, e.g. P0,P1,P2")
    ap.add_argument("--limit", type=int, default=None, help="only the first N tasks (smoke tests)")
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    args = ap.parse_args()

    cfg = data.load_config()
    generate.check_condition_allowed(args.condition, cfg)
    p = prompts.load_prompts()
    id_set, _, _, _, parser = generate.CONDITIONS[args.condition]

    items = gsm = None
    if parser == "gsm8k":
        gsm = data.load_gsm8k(Path(args.data_root) / "gsm8k" / "test.jsonl", cfg["data"]["gsm8k_test_sha256"])
    else:
        items = data.load_pqal(args.data_root, cfg["data"]["ori_pqal_sha256"])
    if id_set == "dev_all":
        ids = data.load_official_split(args.data_root)[0]
    else:
        ids = json.load(open(ROOT / "configs" / f"ids_{id_set}.json"))

    tasks = generate.build_tasks(args.condition, ids, cfg, p, items=items, gsm8k=gsm,
                                 prompt_ids=tuple(args.prompts.split(",")))
    if args.limit:
        tasks = tasks[:args.limit]
    generate_fn, meta = generate.make_hf_generate_fn(cfg)
    meta["prompts_sha256"] = data.sha256(ROOT / "configs" / "prompts.yaml")   # Prompt 10: record which prompt file was used
    out = ROOT / "results" / "generations" / f"{args.condition}.jsonl"
    summary = generate.run_tasks(tasks, generate_fn, out, meta)
    print("SUMMARY:", json.dumps(summary))
    print("output:", out)


if __name__ == "__main__":
    main()
