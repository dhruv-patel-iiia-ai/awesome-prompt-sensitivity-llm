"""Data loading, validation and item-set selection (protocol v1, sections 1, 4 and 6).

Usage from the repository root:
    python -m src.data --make-sets      # validate files, write configs/ids_*.json
"""
import argparse
import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ("yes", "no", "maybe")


@dataclass(frozen=True)
class Item:
    pubid: str
    question: str
    contexts: tuple
    final_decision: str   # gold label
    long_answer: str      # loaded only to check it never reaches a prompt
    year: str


def load_config(path=ROOT / "configs" / "experiment.yaml"):
    import yaml
    return yaml.safe_load(open(path))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pqal_dir(data_root):
    return Path(data_root) / "pubmedqa" / "data"


def load_pqal(data_root, expected_sha256=None):
    """Return {pubid: Item} for the 1,000 PQA-L items, after integrity checks."""
    path = pqal_dir(data_root) / "ori_pqal.json"
    if expected_sha256 and sha256(path) != expected_sha256:
        raise ValueError(f"sha256 mismatch for {path}")
    raw = json.load(open(path))
    items = {}
    for pmid, r in raw.items():
        label = r["final_decision"]
        if label not in LABELS:
            raise ValueError(f"{pmid}: unexpected label {label!r}")
        items[str(pmid)] = Item(pubid=str(pmid), question=r["QUESTION"], contexts=tuple(r["CONTEXTS"]),
                                final_decision=label, long_answer=r["LONG_ANSWER"], year=str(r.get("YEAR") or ""))
    if len(items) != 1000:
        raise ValueError(f"expected 1000 items, found {len(items)}")
    return items


def load_official_split(data_root):
    """Return (dev_ids, test_ids) as sorted lists, read from split_dataset.py's own output files."""
    d = pqal_dir(data_root)
    test_ids = sorted(json.load(open(d / "test_set.json")))
    dev_ids = set()
    for i in range(10):
        dev_ids |= set(json.load(open(d / f"pqal_fold{i}" / "dev_set.json")))
    dev_ids = sorted(dev_ids)
    if len(test_ids) != 500 or len(dev_ids) != 500 or set(test_ids) & set(dev_ids):
        raise ValueError(f"bad split: {len(dev_ids)} dev, {len(test_ids)} test, "
                         f"overlap {len(set(test_ids) & set(dev_ids))}")
    gt_path = d / "test_ground_truth.json"
    if gt_path.exists() and set(json.load(open(gt_path))) != set(test_ids):
        raise ValueError("test_set.json does not match test_ground_truth.json")
    return dev_ids, test_ids


def stratified_sample(ids, labels, n, seed):
    """Draw n ids keeping label shares (largest-remainder rounding). Deterministic for a given seed.

    ids: iterable of ids; labels: {id: label}. Returns the sample sorted by id.
    """
    by_label = {lab: sorted(i for i in ids if labels[i] == lab) for lab in LABELS}
    total = sum(len(v) for v in by_label.values())
    if n > total:
        raise ValueError(f"n={n} larger than pool of {total}")
    exact = {lab: n * len(v) / total for lab, v in by_label.items()}
    alloc = {lab: int(x) for lab, x in exact.items()}
    for lab in sorted(LABELS, key=lambda l: (exact[l] - alloc[l], -LABELS.index(l)), reverse=True):
        if sum(alloc.values()) == n:
            break
        alloc[lab] += 1
    rng = random.Random(seed)
    out = []
    for lab in LABELS:          # fixed label order keeps the draw reproducible
        out += rng.sample(by_label[lab], alloc[lab])
    return sorted(out)


def format_context(contexts):
    """Abstract sections joined by a blank line, whitespace normalised, no headers added (protocol §1–2)."""
    return "\n\n".join(" ".join(c.split()) for c in contexts)


def load_gsm8k(path, expected_sha256=None):
    """Return a list of {idx, question, answer_text, answer_number} from GSM8K test.jsonl."""
    if expected_sha256 and sha256(path) != expected_sha256:
        raise ValueError(f"sha256 mismatch for {path}")
    rows = []
    for idx, line in enumerate(open(path)):
        r = json.loads(line)
        final = r["answer"].split("####")[-1].strip().replace(",", "")
        if not re.fullmatch(r"-?\d+(\.\d+)?", final):
            raise ValueError(f"GSM8K row {idx}: cannot read final answer {final!r}")
        rows.append({"idx": idx, "question": r["question"], "answer_text": r["answer"], "answer_number": final})
    return rows


def make_sets(cfg, data_root, out_dir):
    """Validate the data and write the frozen item-id lists. Returns a summary dict."""
    dc = cfg["data"]
    items = load_pqal(data_root, dc["ori_pqal_sha256"])
    dev_ids, test_ids = load_official_split(data_root)
    labels = {k: v.final_decision for k, v in items.items()}
    main = stratified_sample(test_ids, labels, dc["main_set_size"], dc["main_set_seed"])
    rq3 = stratified_sample(main, labels, dc["rq3_subset_size"], dc["rq3_subset_seed"])
    pilot = stratified_sample(dev_ids, labels, dc["pilot_size"], dc["pilot_seed"])
    gsm = load_gsm8k(Path(data_root) / "gsm8k" / "test.jsonl", dc["gsm8k_test_sha256"])
    gsm_ids = sorted(random.Random(dc["gsm8k_subset_seed"]).sample(range(len(gsm)), dc["gsm8k_subset_size"]))

    sets = {"test_all": test_ids, "main": main, "rq3": rq3, "pilot": pilot, "gsm8k": gsm_ids}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, ids in sets.items():
        path = out_dir / f"ids_{name}.json"
        path.write_text(json.dumps(ids, indent=0) + "\n")
        counts = {lab: sum(labels[i] == lab for i in ids) for lab in LABELS} if name != "gsm8k" else None
        summary[name] = {"n": len(ids), "labels": counts, "sha256": sha256(path)}
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-sets", action="store_true")
    ap.add_argument("--data-root", default=str(ROOT / "data" / "raw"))
    ap.add_argument("--out-dir", default=str(ROOT / "configs"))
    args = ap.parse_args()
    if args.make_sets:
        for name, s in make_sets(load_config(), args.data_root, args.out_dir).items():
            print(f"{name:9s} n={s['n']:4d} labels={s['labels']} sha256={s['sha256'][:16]}")


if __name__ == "__main__":
    main()
