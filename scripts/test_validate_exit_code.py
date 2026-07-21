#!/usr/bin/env python3
"""Regression test: validate.py exit code reflects validation failures.

Guards against the bug where validate.py printed a failure summary but
exited 0, making CI accept a failing spec checkout.
"""
import subprocess
import sys
from pathlib import Path

from validate import numeric_aid_uses_transcendental_tolerance

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


def test_exponential_fade_checkpoints_use_transcendental_tolerance() -> None:
    assert numeric_aid_uses_transcendental_tolerance(
        "$.fade_values_at_half.fade_in.exponential"
    ) and numeric_aid_uses_transcendental_tolerance(
        "$.fade_values_at_half.fade_out.exponential"
    )


def test_nontranscendental_fade_checkpoints_remain_exact() -> None:
    assert not any(
        numeric_aid_uses_transcendental_tolerance(path)
        for path in (
            "$.fade_values_at_half.fade_in.linear",
            "$.fade_values_at_half.fade_in.exponential_extra",
        )
    )


if __name__ == "__main__":
    test_clean_repo_passes()
    test_injected_failure_exits_nonzero()
    test_exponential_fade_checkpoints_use_transcendental_tolerance()
    test_nontranscendental_fade_checkpoints_remain_exact()
    print("validate.py exit-code regression test: PASS")
