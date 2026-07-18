#!/usr/bin/env python3
"""Validate the Piccle schema, documents, semantic rules, and repository links."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft201909Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1.json"
CANONICAL_SCHEMA_URI = "https://spec.dotpiccle.com/schema/v1.json"


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object member {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
    )


def contour_time(entries: list[dict[str, Any]]) -> int:
    return sum(
        entry.get("hold_ms", 0) + entry.get("transition_ms", 0)
        for entry in entries[:-1]
    )


def semantic_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    layers = document["layers"]
    ids = [layer["id"] for layer in layers]
    if len(ids) != len(set(ids)):
        errors.append("layer IDs must be unique")

    for layer in layers:
        duration = layer["duration_ms"]
        source = layer["source"]
        if source["type"] == "tone":
            elapsed = contour_time(source["pitch"]["frequencies"])
            if elapsed > duration:
                errors.append(f"layer {layer['id']}: pitch contour exceeds duration")

        for index, filter_value in enumerate(layer.get("filters", [])):
            elapsed = contour_time(filter_value["frequencies"])
            if elapsed > duration:
                errors.append(
                    f"layer {layer['id']}: filter {index} contour exceeds duration"
                )

        volume = layer.get("volume", 1)
        if isinstance(volume, dict):
            fade_out = min(volume.get("fade_out_ms", 5), duration)
            elapsed = (
                volume.get("fade_in_ms", 0)
                + contour_time(volume["levels"])
                + fade_out
            )
            if elapsed > duration:
                errors.append(f"layer {layer['id']}: volume contour exceeds duration")

    return errors


def check_schema_contract(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def expect(actual: Any, expected: Any, label: str) -> None:
        if actual != expected:
            errors.append(f"schema contract: {label} is {actual!r}, expected {expected!r}")

    properties = schema["properties"]
    defs = schema["$defs"]
    expect(schema["$schema"], "https://json-schema.org/draft/2019-09/schema", "$schema")
    expect(schema["$id"], CANONICAL_SCHEMA_URI, "$id")
    expect(properties["$schema"].get("const"), CANONICAL_SCHEMA_URI, "instance $schema")
    expect(properties["piccle"].get("enum"), ["1.0"], "piccle versions")
    expect(properties["volume"].get("default"), 1, "root volume default")
    expect(properties["fade_in_ms"].get("default"), 0, "root fade-in default")
    expect(properties["fade_out_ms"].get("default"), 5, "root fade-out default")
    expect(defs["layer"]["properties"]["start_ms"].get("default"), 0, "start default")
    expect(defs["layer"]["properties"]["balance"].get("default"), 0, "balance default")
    expect(defs["layer"]["properties"]["filters"].get("default"), [], "filters default")

    noise = defs["source"]["oneOf"][1]["properties"]
    expect(noise["seed"].get("minimum"), 0, "seed minimum")
    expect(noise["seed"].get("maximum"), 4294967295, "seed maximum")
    expect(noise["seed"].get("default"), 0, "seed default")

    def bounded_times(node: Any, location: str = "schema") -> None:
        if isinstance(node, dict):
            properties_value = node.get("properties")
            if isinstance(properties_value, dict):
                for key, value in properties_value.items():
                    if key.endswith("_ms") and isinstance(value, dict):
                        expect(value.get("maximum"), 9007199254740991, f"{location}/{key} maximum")
            for key, value in node.items():
                bounded_times(value, f"{location}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                bounded_times(value, f"{location}/{index}")

    bounded_times(schema)

    def closed_objects(node: Any, location: str = "schema") -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("additionalProperties") is not False:
                errors.append(f"schema contract: open object at {location}")
            properties_value = node.get("properties")
            if isinstance(properties_value, dict):
                for key, value in properties_value.items():
                    if isinstance(value, dict) and "description" not in value:
                        errors.append(f"schema contract: property {location}/{key} lacks description")
            for key, value in node.items():
                closed_objects(value, f"{location}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                closed_objects(value, f"{location}/{index}")

    closed_objects(schema)
    return errors


def documentation_parity_errors() -> list[str]:
    requirements = {
        "docs/01-document-structure.md": {
            "$schema", "piccle", "name", "description", "duration_ms", "volume",
            "fade_in_ms", "fade_out_ms", "reverb", "layers", "id", "start_ms",
            "source", "balance", "filters",
        },
        "docs/03-sources.md": {"type", "wave", "pitch", "character", "seed"},
        "docs/04-pitch.md": {"frequencies", "hz", "hold_ms", "transition_ms", "transition_curve", "offset_cents"},
        "docs/05-volume.md": {"fade_in_ms", "fade_out_ms", "levels", "level", "hold_ms", "transition_ms", "transition_curve"},
        "docs/06-filters.md": {"type", "frequencies", "hz", "hold_ms", "transition_ms", "transition_curve", "resonance"},
        "docs/07-reverb.md": {"amount", "tail_ms", "soften_hz"},
    }
    errors: list[str] = []
    for relative, fields in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for field in sorted(fields):
            if f"`{field}`" not in text:
                errors.append(f"documentation parity: {relative} does not document `{field}`")
    return errors


def fixture_inventory_errors(directory: Path) -> list[str]:
    readme = directory / "README.md"
    documented = set(re.findall(r"`([^`]+\.json)`", readme.read_text(encoding="utf-8")))
    present = {path.name for path in directory.glob("*.json")}
    errors: list[str] = []
    if documented - present:
        errors.append(f"{readme.relative_to(ROOT)} lists missing fixtures: {sorted(documented-present)}")
    if present - documented:
        errors.append(f"{readme.relative_to(ROOT)} omits fixtures: {sorted(present-documented)}")
    return errors


def link_errors() -> list[str]:
    errors: list[str] = []
    markdown_files = [*ROOT.glob("*.md"), *ROOT.glob("docs/*.md"), *ROOT.glob("test-vectors/*/*.md")]
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            destination = match.group(1).strip()
            local = destination.split("#", 1)[0]
            if not local or "://" in local or local.startswith("mailto:"):
                continue
            target = (path.parent / local).resolve()
            if not target.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{path.relative_to(ROOT)}:{line}: missing link target {destination}"
                )
    return errors


def formatting_errors(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        if not raw.endswith("\n"):
            errors.append(f"{path.relative_to(ROOT)}: missing final newline")
        if "\t" in raw:
            errors.append(f"{path.relative_to(ROOT)}: contains tab indentation")
        for line_number, line in enumerate(raw.splitlines(), 1):
            if line.endswith(" "):
                errors.append(f"{path.relative_to(ROOT)}:{line_number}: trailing whitespace")
    return errors


def main() -> int:
    failures: list[str] = []
    schema = load_json(SCHEMA_PATH)
    Draft201909Validator.check_schema(schema)
    validator = Draft201909Validator(schema)
    failures.extend(check_schema_contract(schema))
    failures.extend(documentation_parity_errors())

    valid_paths = sorted((ROOT / "examples").glob("*.json")) + sorted(
        (ROOT / "test-vectors" / "valid").glob("*.json")
    )
    for path in valid_paths:
        try:
            document = load_json(path)
        except (ValueError, UnicodeError) as error:
            failures.append(f"{path.relative_to(ROOT)}: parsing failed: {error}")
            continue
        schema_errors = list(validator.iter_errors(document))
        if schema_errors:
            failures.append(
                f"{path.relative_to(ROOT)}: schema rejected valid document: {schema_errors[0].message}"
            )
            continue
        for error in semantic_errors(document):
            failures.append(f"{path.relative_to(ROOT)}: {error}")

    parse_invalid = {"duplicate-member.json"}
    semantic_invalid = {
        "duplicate-layer-id.json",
        "filter-timing-exceeds-duration.json",
        "pitch-timing-exceeds-duration.json",
        "volume-fade-exceeds-duration.json",
        "volume-timing-exceeds-duration.json",
    }
    invalid_paths = sorted((ROOT / "test-vectors" / "invalid").glob("*.json"))
    for path in invalid_paths:
        expected_stage = (
            "parse"
            if path.name in parse_invalid
            else "semantic"
            if path.name in semantic_invalid
            else "schema"
        )
        try:
            document = load_json(path)
        except (ValueError, UnicodeError) as error:
            actual_stage = "parse"
            detail = str(error)
        else:
            schema_errors = list(validator.iter_errors(document))
            if schema_errors:
                actual_stage = "schema"
                detail = schema_errors[0].message
            else:
                semantics = semantic_errors(document)
                actual_stage = "semantic" if semantics else "accepted"
                detail = semantics[0] if semantics else "no validation error"
        if actual_stage != expected_stage:
            failures.append(
                f"{path.relative_to(ROOT)}: failed at {actual_stage}, expected {expected_stage}: {detail}"
            )

    failures.extend(fixture_inventory_errors(ROOT / "test-vectors" / "valid"))
    failures.extend(fixture_inventory_errors(ROOT / "test-vectors" / "invalid"))
    failures.extend(link_errors())
    failures.extend(formatting_errors([SCHEMA_PATH, *valid_paths, *invalid_paths]))

    if failures:
        print(f"Piccle validation failed with {len(failures)} issue(s):", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(
        f"Piccle validation passed: schema, {len(valid_paths)} accepted documents, "
        f"{len(invalid_paths)} rejected documents, semantic rules, documentation parity, "
        "inventories, formatting, and links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
