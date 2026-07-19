#!/usr/bin/env python3
"""Regression test: validate.py exit code reflects validation failures.

Guards against the bug where validate.py printed a failure summary but
exited 0, making CI accept a failing spec checkout.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_INVALID = '{\n  "invalid": true\n}\n'


def run_validate() -> int:
    return subprocess.run(
        [sys.executable, "scripts/validate.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).returncode


def test_clean_repo_passes() -> None:
    rc = run_validate()
    assert rc == 0, f"clean repo should exit 0, got {rc}"


def test_injected_failure_exits_nonzero() -> None:
    bad = ROOT / "examples" / "_test_invalid_example.json"
    try:
        bad.write_text(CANONICAL_INVALID, encoding="utf-8")
        rc = run_validate()
        assert rc != 0, f"broken repo should exit non-zero, got {rc}"
    finally:
        bad.unlink(missing_ok=True)


if __name__ == "__main__":
    test_clean_repo_passes()
    test_injected_failure_exits_nonzero()
    print("validate.py exit-code regression test: PASS")
