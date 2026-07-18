#!/usr/bin/env python3
"""Check or rewrite repository JSON using Piccle's canonical presentation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object member {key!r}")
        result[key] = value
    return result


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def json_paths() -> list[Path]:
    paths = [ROOT / "schemas" / "v1.json"]
    paths.extend(sorted((ROOT / "examples").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "valid").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "invalid").glob("*.json")))
    paths.extend(sorted((ROOT / "test-vectors" / "numeric").glob("*.json")))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="rewrite non-canonical files")
    args = parser.parse_args()
    failures: list[str] = []

    for path in json_paths():
        raw = path.read_text(encoding="utf-8")
        try:
            value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        except DuplicateKeyError:
            if path.name == "duplicate-member.json":
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
