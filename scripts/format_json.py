#!/usr/bin/env python3
"""Check or rewrite repository JSON using Piccle's canonical presentation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class DuplicateKeyError(ValueError):
    pass


class NonFiniteNumberError(ValueError):
    pass


class NumberOutOfRangeError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object member {key!r}")
        result[key] = value
    return result


def reject_non_finite_constant(token: str) -> None:
    raise NonFiniteNumberError(f"non-JSON numeric token {token!r}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise NumberOutOfRangeError(
            f"JSON number is outside finite binary64 range: {token}"
        )
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def json_paths() -> list[Path]:
    paths = [ROOT / "schemas" / "v1.json"]
    paths.extend(sorted((ROOT / "examples").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "valid").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "invalid").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "numeric").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "behavior").glob("*.json")))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite non-canonical files")
    args = parser.parse_args()
    failures: list[str] = []

    for path in json_paths():
        raw = path.read_text(encoding="utf-8")
        try:
            value = json.loads(
                raw,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_non_finite_constant,
                parse_float=parse_finite_float,
            )
        except (DuplicateKeyError, NonFiniteNumberError, NumberOutOfRangeError):
            if path.name in {
                "duplicate-member.json",
                "non-finite-number.json",
                "number-out-of-range.json",
            }:
                continue
            raise
        expected = canonical_json(value)
        if raw == expected:
            continue
        if args.write:
            path.write_text(expected, encoding="utf-8")
        else:
            failures.append(str(path.relative_to(ROOT)))

    if failures:
        print("Non-canonical JSON files:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print("Run: python3 scripts/format_json.py --write", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
