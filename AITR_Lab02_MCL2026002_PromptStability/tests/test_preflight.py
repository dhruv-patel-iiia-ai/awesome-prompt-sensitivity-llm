"""Tests for scripts/colab_preflight.py (no GPU, no Drive). Run:
    python tests/test_preflight.py
"""
import errno
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import colab_preflight as pf  # noqa: E402


def make_project(tmp, tests_name="tests"):
    for d in ["src", tests_name, "scripts", "configs", "notebooks"]:
        (Path(tmp) / d).mkdir()
    (Path(tmp) / "configs" / "experiment.yaml").write_text("x: 1\n")
    (Path(tmp) / "configs" / "prompts.yaml").write_text("x: 1\n")


def test_clean_project_passes():
    with tempfile.TemporaryDirectory() as t:
        make_project(t)
        assert pf.whitespace_names(t) == []
        assert pf.missing_required(t) == []
        assert pf.main(["--root", t]) == 0


def test_trailing_space_folder_is_found():
    # The real Prompt 09 case: Drive folder named "tests "
    with tempfile.TemporaryDirectory() as t:
        make_project(t, tests_name="tests ")
        assert pf.whitespace_names(t) == ["tests "]
        assert pf.missing_required(t) == [("tests", ["'tests '"])]
        assert pf.main(["--root", t]) == 1


def test_edge_case_both_names_present():
    # Edge case: "tests" exists, but a stale "tests " copy is still there.
    # The required check passes, so only the space check can catch it.
    with tempfile.TemporaryDirectory() as t:
        make_project(t)
        (Path(t) / "tests ").mkdir()
        assert pf.missing_required(t) == []
        assert pf.whitespace_names(t) == ["tests "]
        assert pf.main(["--root", t]) == 1


def test_space_in_file_name_inside_folder():
    with tempfile.TemporaryDirectory() as t:
        make_project(t)
        (Path(t) / "src" / "data.py ").write_text("")
        assert pf.whitespace_names(t) == [os.path.join("src", "data.py ")]


def test_errno_107_gives_restart_advice():
    err = OSError(errno.ENOTCONN, "Transport endpoint is not connected")
    with mock.patch.object(pf.os, "getcwd", side_effect=err):
        msg = pf.check_drive_alive(".")
    assert msg == pf.FIX_107
    assert "Restart session" in msg and "force_remount" in msg


def test_other_oserror_is_not_called_107():
    err = OSError(errno.ENOENT, "No such file")
    with mock.patch.object(pf.os, "listdir", side_effect=err):
        msg = pf.check_drive_alive(".")
    assert msg is not None and "107" not in msg


def test_lint_catches_semicolon_and_long_line():
    src = "a = 1; b = 2\n" + "x = '" + "y" * 90 + "'\n"
    probs = pf.lint_source(src)
    msgs = [m for _, m in probs]
    assert (1, "';' joins two statements") in probs
    assert any("characters" in m for m in msgs)


def test_lint_ignores_semicolon_in_strings_and_shell():
    src = "s = 'a;b'\n# c; d\n!echo a; echo b\n"
    assert pf.lint_source(src) == []


def test_lint_notebook_reports_cell_and_line():
    nb = {"cells": [
        {"cell_type": "markdown", "source": ["text; text"]},
        {"cell_type": "code", "source": ["x = 1\n", "y = 2; z = 3\n"]},
    ]}
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "n.ipynb"
        p.write_text(json.dumps(nb))
        assert pf.lint_notebook(p) == [(1, 2, "';' joins two statements")]


def test_preflight_script_follows_its_own_rule():
    src = (ROOT / "scripts" / "colab_preflight.py").read_text()
    long_ = [ln for ln in src.splitlines() if len(ln) > pf.MAX_LINE]
    assert long_ == [], long_


def run_all():
    tests = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
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
