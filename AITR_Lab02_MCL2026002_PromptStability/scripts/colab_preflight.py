"""Colab preflight check (Prompt 11).

Run from the project folder, after drive.mount:

    !python scripts/colab_preflight.py
    !python scripts/colab_preflight.py --lint NOTEBOOK.ipynb

It checks the three failures seen on Colab in Prompts 09-10:
  1. a file or folder name that starts or ends with a space
     (the Drive folder "tests ")
  2. a lost Drive connection (OSError Errno 107 after force_remount)
  3. code lines that break when pasted into Colab (long lines, ";")

It only reads; it never renames, deletes or remounts anything.
"""
import argparse
import errno
import io
import json
import os
import sys
import tokenize
from pathlib import Path

REQUIRED = ["src", "tests", "scripts", "configs", "notebooks",
            "configs/experiment.yaml", "configs/prompts.yaml"]
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints"}
MAX_LINE = 79

FIX_107 = ("Drive connection is broken (Errno 107). "
           "Do NOT run force_remount. Use Runtime -> Restart session, "
           "then run cell 1 (drive.mount + %cd) again.")


def check_drive_alive(root):
    """Return None if the folder can be read, or a message if it cannot."""
    try:
        os.getcwd()
        os.listdir(root)
    except OSError as e:
        if e.errno == errno.ENOTCONN:
            return FIX_107
        return f"Cannot read {root}: {e}"
    return None


def whitespace_names(root):
    """Paths (relative to root) whose own name has a leading/trailing space."""
    bad = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in dirnames + filenames:
            if name != name.strip():
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                bad.append(rel)
    return sorted(bad)


def missing_required(root, required=REQUIRED):
    """Required paths that do not exist exactly, with any near-match found."""
    out = []
    for rel in required:
        if (Path(root) / rel).exists():
            continue
        parent = (Path(root) / rel).parent
        target = Path(rel).name
        near = []
        if parent.is_dir():
            for p in parent.iterdir():
                if p.name.strip() == target:
                    near.append(repr(p.name))
        out.append((rel, near))
    return out


def lint_source(src, max_len=MAX_LINE):
    """Problems in one code cell: long lines, and ';' used in Python code."""
    problems = []
    lines = src.splitlines()
    for i, line in enumerate(lines, 1):
        if len(line) > max_len:
            problems.append((i, f"line has {len(line)} characters"))
    # ';' check only on Python lines (skip ! shell and % magic lines)
    py = []
    for line in lines:
        s = line.lstrip()
        if s.startswith("!") or s.startswith("%"):
            py.append("")
        else:
            py.append(line)
    text = "\n".join(py) + "\n"
    try:
        toks = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in toks:
            if tok.type == tokenize.OP and tok.string == ";":
                problems.append((tok.start[0], "';' joins two statements"))
    except (tokenize.TokenError, IndentationError, SyntaxError) as e:
        problems.append((0, f"cannot tokenize: {e}"))
    return problems


def lint_notebook(path, max_len=MAX_LINE):
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for c, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        for line_no, msg in lint_source(src, max_len):
            out.append((c, line_no, msg))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lint", nargs="*", default=[])
    args = ap.parse_args(argv)
    root = args.root
    n_fail = 0

    msg = check_drive_alive(root)
    if msg:
        print(f"[FAIL] drive connection: {msg}")
        print("SUMMARY: 0 pass, 1 fail (stopped)")
        return 1
    print(f"[PASS] drive connection: {os.path.abspath(root)} is readable")

    bad = whitespace_names(root)
    if bad:
        n_fail += 1
        print("[FAIL] names with a leading/trailing space:")
        for b in bad:
            print(f"       {b!r}  -> rename in Drive to {b.strip()!r}")
    else:
        print("[PASS] no file or folder name starts/ends with a space")

    miss = missing_required(root)
    if miss:
        n_fail += 1
        for rel, near in miss:
            hint = f" (found {', '.join(near)})" if near else ""
            print(f"[FAIL] missing: {rel}{hint}")
    else:
        print(f"[PASS] all {len(REQUIRED)} required paths exist")

    for nb in args.lint:
        probs = lint_notebook(nb)
        if probs:
            n_fail += 1
            print(f"[FAIL] {nb}: {len(probs)} paste problem(s)")
            for c, ln, m in probs:
                print(f"       cell {c}, line {ln}: {m}")
        else:
            print(f"[PASS] {nb}: short lines, no ';'")

    n_checks = 3 + len(args.lint)
    print(f"SUMMARY: {n_checks - n_fail} pass, {n_fail} fail")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
