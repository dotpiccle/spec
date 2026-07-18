#!/usr/bin/env python3
"""Validate the Piccle schema, documents, contracts, fixtures, and repository."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft201909Validator

from format_json import DuplicateKeyError, reject_duplicate_keys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1.json"
EXPECTATIONS_PATH = ROOT / "test-vectors" / "invalid-expectations.json"
NUMERIC_PATH = ROOT / "test-vectors" / "numeric" / "dsp-values.json"
CANONICAL_SCHEMA_URI = "https://spec.dotpiccle.com/schema/v1.json"


@dataclass(frozen=True)
class Issue:
    stage: str
    code: str
    path: str
    message: str


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
    )


def json_path(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        elif re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$-]*", str(part)):
            result += f".{part}"
        else:
            result += f"[{json.dumps(str(part))}]"
    return result


def contour_time(entries: list[dict[str, Any]]) -> int:
    return sum(
        entry.get("hold_ms", 0) + entry.get("transition_ms", 0)
        for entry in entries[:-1]
    )


def semantic_issues(document: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    layers = document["layers"]
    seen: dict[str, int] = {}
    for index, layer in enumerate(layers):
        identifier = layer["id"]
        if identifier in seen:
            issues.append(Issue(
                "semantic", "semantic.duplicate_layer_id", f"$.layers[{index}].id",
                f"duplicates $.layers[{seen[identifier]}].id",
            ))
        else:
            seen[identifier] = index

    for layer_index, layer in enumerate(layers):
        duration = layer["duration_ms"]
        source = layer["source"]
        if source["type"] == "tone":
            elapsed = contour_time(source["pitch"]["frequencies"])
            if elapsed > duration:
                issues.append(Issue(
                    "semantic", "semantic.pitch_timing_exceeds_duration",
                    f"$.layers[{layer_index}].source.pitch.frequencies",
                    f"scheduled {elapsed} ms exceeds layer duration {duration} ms",
                ))

        for filter_index, filter_value in enumerate(layer.get("filters", [])):
            elapsed = contour_time(filter_value["frequencies"])
            if elapsed > duration:
                issues.append(Issue(
                    "semantic", "semantic.filter_timing_exceeds_duration",
                    f"$.layers[{layer_index}].filters[{filter_index}].frequencies",
                    f"scheduled {elapsed} ms exceeds layer duration {duration} ms",
                ))

        volume = layer.get("volume", 1)
        if isinstance(volume, dict):
            fade_out = min(volume.get("fade_out_ms", 5), duration)
            elapsed = volume.get("fade_in_ms", 0) + contour_time(volume["levels"]) + fade_out
            if elapsed > duration:
                issues.append(Issue(
                    "semantic", "semantic.volume_timing_exceeds_duration",
                    f"$.layers[{layer_index}].volume",
                    f"scheduled {elapsed} ms exceeds layer duration {duration} ms",
                ))
    return issues


def select_schema_error(error: Any) -> Any:
    if not error.context:
        return error
    contexts = list(error.context)
    if error.validator == "oneOf":
        instance = error.instance
        selected_branch: int | None = None
        if isinstance(instance, dict) and instance.get("type") == "tone":
            selected_branch = 0
        elif isinstance(instance, dict) and instance.get("type") == "noise":
            selected_branch = 1
        elif isinstance(instance, dict):
            selected_branch = 1
        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            selected_branch = 0
        if selected_branch is not None:
            def belongs(candidate: Any) -> bool:
                parts = list(candidate.absolute_schema_path)
                return "oneOf" in parts and parts[parts.index("oneOf") + 1] == selected_branch
            matching = [candidate for candidate in contexts if belongs(candidate)]
            if matching:
                contexts = matching
    leaves = [select_schema_error(candidate) for candidate in contexts]
    return max(leaves, key=lambda candidate: (len(list(candidate.absolute_path)), len(list(candidate.absolute_schema_path))))


def schema_issue(error: Any) -> Issue:
    error = select_schema_error(error)
    parts = list(error.absolute_path)
    if error.validator == "additionalProperties" and isinstance(error.instance, dict):
        allowed = set(error.schema.get("properties", {}))
        extras = sorted(set(error.instance) - allowed)
        if extras:
            parts.append(extras[0])
    elif error.validator == "required" and isinstance(error.instance, dict):
        missing = [key for key in error.validator_value if key not in error.instance]
        if missing:
            parts.append(missing[0])
    return Issue(
        "schema",
        f"schema.{error.validator}",
        json_path(parts),
        error.message,
    )


def first_document_issue(path: Path, validator: Draft201909Validator) -> Issue | None:
    try:
        document = load_json(path)
    except DuplicateKeyError as error:
        return Issue("parse", "json.duplicate_member", "$", str(error))
    except (ValueError, UnicodeError) as error:
        return Issue("parse", "json.invalid", "$", str(error))
    errors = list(validator.iter_errors(document))
    if errors:
        return schema_issue(errors[0])
    semantics = semantic_issues(document)
    return semantics[0] if semantics else None


def check_schema_contract(schema: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def expect(actual: Any, expected: Any, label: str) -> None:
        if actual != expected:
            failures.append(f"schema contract: {label} is {actual!r}, expected {expected!r}")

    properties = schema["properties"]
    defs = schema["$defs"]

    def expect_property(node: dict[str, Any], name: str, *, kind: str | None = None,
                        minimum: Any = None, maximum: Any = None,
                        default: Any = None, has_default: bool = False) -> None:
        prop = node["properties"][name]
        if kind is not None:
            expect(prop.get("type"), kind, f"{name} type")
        if minimum is not None:
            expect(prop.get("minimum"), minimum, f"{name} minimum")
        if maximum is not None:
            expect(prop.get("maximum"), maximum, f"{name} maximum")
        if has_default:
            expect(prop.get("default"), default, f"{name} default")
    expect(schema["$schema"], "https://json-schema.org/draft/2019-09/schema", "$schema")
    expect(schema["$id"], CANONICAL_SCHEMA_URI, "$id")
    expect(set(properties), {"$schema", "piccle", "name", "description", "duration_ms", "volume", "reverb", "layers"}, "root properties")
    expect(schema["required"], ["piccle", "layers"], "root required fields")
    expect(properties["$schema"].get("const"), CANONICAL_SCHEMA_URI, "instance $schema")
    expect(properties["piccle"].get("enum"), ["1.0"], "piccle versions")
    expect((properties["duration_ms"].get("type"), properties["duration_ms"].get("minimum")), ("integer", 1), "root duration type/minimum")
    expect((properties["volume"].get("type"), properties["volume"].get("minimum"), properties["volume"].get("maximum"), properties["volume"].get("default")), ("number", 0, 1, 1), "root volume contract")

    layer = defs["layer"]
    expect(layer["required"], ["id", "duration_ms", "source"], "layer required fields")
    expect(layer["properties"]["start_ms"].get("default"), 0, "start default")
    expect(layer["properties"]["balance"].get("default"), 0, "balance default")
    expect(layer["properties"]["filters"].get("default"), [], "filters default")
    expect_property(layer, "start_ms", kind="integer", minimum=0, default=0, has_default=True)
    expect_property(layer, "duration_ms", kind="integer", minimum=1)
    expect_property(layer, "balance", kind="number", minimum=-1, maximum=1, default=0, has_default=True)
    expect(defs["curves"]["enum"], ["linear", "exponential", "easeIn", "easeOut", "easeInOut"], "curve enum")
    expect(defs["filter"]["properties"]["type"]["enum"], ["lowpass", "highpass", "bandpass"], "filter enum")
    expect(defs["filter"]["properties"]["resonance"].get("default"), 0, "resonance default")
    expect(defs["pitch"]["properties"]["offset_cents"].get("default"), 0, "pitch offset default")
    expect(defs["pitch"]["required"], ["frequencies"], "pitch required fields")
    expect_property(defs["pitch"], "offset_cents", kind="integer", minimum=-1200, maximum=1200, default=0, has_default=True)

    pitch_entry = defs["pitch"]["properties"]["frequencies"]["items"]
    filter_entry = defs["filter"]["properties"]["frequencies"]["items"]
    for label, entry in (("pitch", pitch_entry), ("filter", filter_entry)):
        expect(entry["required"], ["hz"], f"{label} entry required fields")
        expect_property(entry, "hz", kind="number", minimum=20, maximum=20000)
        expect_property(entry, "hold_ms", kind="integer", minimum=0, default=0, has_default=True)
        expect_property(entry, "transition_ms", kind="integer", minimum=0, default=0, has_default=True)
        expect(entry["properties"]["transition_curve"].get("default"), "linear", f"{label} transition curve default")

    reverb = defs["reverb"]
    expect(reverb["required"], ["amount", "tail_ms", "soften_hz"], "reverb required fields")
    expect((reverb["properties"]["amount"].get("minimum"), reverb["properties"]["amount"].get("maximum")), (0, 1), "reverb amount range")
    expect((reverb["properties"]["tail_ms"].get("minimum"), reverb["properties"]["soften_hz"].get("minimum"), reverb["properties"]["soften_hz"].get("maximum")), (1, 200, 12000), "reverb ranges")
    expect_property(reverb, "amount", kind="number", minimum=0, maximum=1)
    expect_property(reverb, "tail_ms", kind="integer", minimum=1)
    expect_property(reverb, "soften_hz", kind="number", minimum=200, maximum=12000)

    noise = defs["source"]["oneOf"][1]["properties"]
    expect(noise["character"]["enum"], ["soft", "neutral", "sharp"], "noise character enum")
    expect((noise["seed"].get("minimum"), noise["seed"].get("maximum"), noise["seed"].get("default")), (0, 4294967295, 0), "seed contract")
    tone_schema, noise_schema = defs["source"]["oneOf"]
    expect(tone_schema["required"], ["type", "wave", "pitch"], "tone required fields")
    expect(tone_schema["properties"]["wave"]["enum"], ["sine", "triangle", "square", "saw"], "wave enum")
    expect(noise_schema["required"], ["type", "character"], "noise required fields")

    volume_object = defs["volume"]["oneOf"][1]
    expect(volume_object["required"], ["levels"], "volume required fields")
    expect(volume_object["properties"]["fade_in_ms"].get("default"), 0, "layer fade-in default")
    expect(volume_object["properties"]["fade_out_ms"].get("default"), 5, "layer fade-out default")
    expect_property(volume_object, "fade_in_ms", kind="integer", minimum=0, default=0, has_default=True)
    expect_property(volume_object, "fade_out_ms", kind="integer", minimum=0, default=5, has_default=True)
    level_entry = volume_object["properties"]["levels"]["items"]
    expect(level_entry["required"], ["level"], "volume level required fields")
    expect_property(level_entry, "level", kind="number", minimum=0, maximum=1)
    expect_property(level_entry, "hold_ms", kind="integer", minimum=0, default=0, has_default=True)
    expect_property(level_entry, "transition_ms", kind="integer", minimum=0, default=0, has_default=True)
    expect(level_entry["properties"]["transition_curve"].get("default"), "linear", "volume transition curve default")

    def inspect(node: Any, location: str = "schema") -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("additionalProperties") is not False:
                failures.append(f"schema contract: open object at {location}")
            properties_value = node.get("properties")
            if isinstance(properties_value, dict):
                for key, value in properties_value.items():
                    if isinstance(value, dict) and "description" not in value:
                        failures.append(f"schema contract: property {location}/{key} lacks description")
                    if key.endswith("_ms") and isinstance(value, dict):
                        expect(value.get("maximum"), 9007199254740991, f"{location}/{key} maximum")
            for key, value in node.items():
                inspect(value, f"{location}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                inspect(value, f"{location}/{index}")

    inspect(schema)
    return failures


def documentation_parity_errors() -> list[str]:
    requirements = {
        "docs/01-document-structure.md": {"$schema", "piccle", "name", "description", "duration_ms", "volume", "reverb", "layers", "id", "start_ms", "source", "balance", "filters"},
        "docs/03-sources.md": {"type", "wave", "pitch", "character", "seed"},
        "docs/04-pitch.md": {"frequencies", "hz", "hold_ms", "transition_ms", "transition_curve", "offset_cents"},
        "docs/05-volume.md": {"fade_in_ms", "fade_out_ms", "levels", "level", "hold_ms", "transition_ms", "transition_curve"},
        "docs/06-filters.md": {"type", "frequencies", "hz", "hold_ms", "transition_ms", "transition_curve", "resonance"},
        "docs/07-reverb.md": {"amount", "tail_ms", "soften_hz"},
    }
    failures: list[str] = []
    for relative, fields in requirements.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for field in sorted(fields):
            if f"`{field}`" not in text:
                failures.append(f"documentation parity: {relative} does not document `{field}`")

    exact_tokens = {
        "docs/01-document-structure.md": ["`duration_ms` | integer", "`volume`      | number  | 1        | No"],
        "docs/05-volume.md": ["`fade_in_ms`  | integer | 0", "`fade_out_ms` | integer | 5"],
        "docs/06-filters.md": ["`resonance`   | number | 0", "20-20000 Hz"],
        "docs/07-reverb.md": ["`amount`    | number", "`tail_ms`   | integer | `1` or more", "`soften_hz` | number  | `200`–`12000`"],
        "docs/11-engine-safety.md": ["at least 8000 Hz", "min(20000, 0.49 × sample_rate)", "48000 Hz"],
    }
    for relative, tokens in exact_tokens.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                failures.append(f"documentation parity: {relative} lacks contract text {token!r}")
    return failures


def fixture_inventory_errors(directory: Path) -> list[str]:
    readme = directory / "README.md"
    documented = set(re.findall(r"`([^`]+\.json)`", readme.read_text(encoding="utf-8")))
    present = {path.name for path in directory.glob("*.json")}
    failures: list[str] = []
    if documented - present:
        failures.append(f"{readme.relative_to(ROOT)} lists missing fixtures: {sorted(documented-present)}")
    if present - documented:
        failures.append(f"{readme.relative_to(ROOT)} omits fixtures: {sorted(present-documented)}")
    return failures


def github_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", text, re.MULTILINE):
        heading = re.sub(r"<[^>]+>", "", heading)
        heading = re.sub(r"[`*_~]", "", heading).lower()
        slug = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE).replace(" ", "-")
        slug = re.sub(r"-+", "-", slug).strip("-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        anchors.add(slug if count == 0 else f"{slug}-{count}")
    return anchors


def link_errors() -> list[str]:
    failures: list[str] = []
    markdown_files = sorted([
        *ROOT.glob("*.md"),
        *ROOT.glob("docs/*.md"),
        *ROOT.glob("test-vectors/**/*.md"),
    ])
    markdown_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    html_pattern = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
    anchor_cache: dict[Path, set[str]] = {}
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        destinations = [match.group(1).strip().strip("<>") for match in markdown_pattern.finditer(text)]
        destinations.extend(match.group(1).strip() for match in html_pattern.finditer(text))
        for destination in destinations:
            local, separator, fragment = destination.partition("#")
            if "://" in local or local.startswith(("mailto:", "data:")):
                continue
            target = (path.parent / local).resolve() if local else path.resolve()
            if not target.exists():
                failures.append(f"{path.relative_to(ROOT)}: missing link target {destination}")
                continue
            if separator and target.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(target, github_anchors(target.read_text(encoding="utf-8")))
                if fragment not in anchors:
                    failures.append(f"{path.relative_to(ROOT)}: missing Markdown anchor {destination}")
    return failures


def numeric_aid_errors() -> list[str]:
    actual = load_json(NUMERIC_PATH)
    mask64, mask32 = (1 << 64) - 1, (1 << 32) - 1

    def pcg(seed: int) -> list[int]:
        state = 0
        def step() -> int:
            nonlocal state
            old = state
            state = (old * 6364136223846793005 + 1442695040888963407) & mask64
            x = (((old >> 18) ^ old) >> 27) & mask32
            rotation = old >> 59
            return ((x >> rotation) | (x << ((-rotation) & 31))) & mask32
        step()
        state = (state + seed) & mask64
        step()
        return [step() for _ in range(5)]

    expected = {
        "status": "non-normative",
        "pcg32": {"seed_0_first_u32": pcg(0), "seed_1_first_u32": pcg(1), "seed_max_first_u32": pcg(4294967295)},
        "curve_progress_at_half": {"linear": .5, "exponential_0_1_to_1": math.sqrt(.1), "easeIn": .25, "easeOut": .75, "easeInOut": .5},
        "oscillator_coefficients": {"sine_k1": 1.0, "square_k1": 4/math.pi, "square_k3": 4/(3*math.pi), "saw_k1": 2/math.pi, "saw_k2": -1/math.pi, "triangle_k1": 8/math.pi**2, "triangle_k3": -8/(9*math.pi**2)},
        "balance": {"center_left": math.sqrt(.5), "center_right": math.sqrt(.5), "center_then_mono": 1.0},
        "lowpass_1000_hz_48000_resonance_0": {},
        "render_frequency_max_hz": {str(rate): min(20000, .49*rate) for rate in (8000, 16000, 22050, 44100, 48000)},
        "reverb_terminal_window_frames_at_48000": {f"tail_{tail}_ms": max(2, min(240, math.ceil((48*tail)/10))) for tail in (1, 10, 20, 500)},
        "reverb_tail_1_ms_terminal_gains": {"window_start_frame_in_tail": 43, "gains": [1.0, .75, .5, .25, 0.0]},
    }
    omega = 2*math.pi*1000/48000
    c, alpha = math.cos(omega), math.sin(omega)/(2*.707)
    a0 = 1 + alpha
    expected["lowpass_1000_hz_48000_resonance_0"] = {"b0": ((1-c)/2)/a0, "b1": (1-c)/a0, "b2": ((1-c)/2)/a0, "a1": (-2*c)/a0, "a2": (1-alpha)/a0}

    failures: list[str] = []
    def compare(left: Any, right: Any, path: str) -> None:
        if isinstance(right, dict) and isinstance(left, dict):
            if set(left) != set(right):
                failures.append(f"numeric aid {path}: keys differ")
                return
            for key in right:
                compare(left[key], right[key], f"{path}.{key}")
        elif isinstance(right, list) and isinstance(left, list):
            if left != right:
                failures.append(f"numeric aid {path}: values differ")
        elif isinstance(right, float) and isinstance(left, (int, float)):
            if not math.isclose(float(left), right, rel_tol=1e-14, abs_tol=1e-15):
                failures.append(f"numeric aid {path}: {left!r} != {right!r}")
        elif left != right:
            failures.append(f"numeric aid {path}: {left!r} != {right!r}")
    compare(actual, expected, "$")
    return failures


def main() -> int:
    failures: list[str] = []
    schema = load_json(SCHEMA_PATH)
    Draft201909Validator.check_schema(schema)
    validator = Draft201909Validator(schema)
    failures.extend(check_schema_contract(schema))
    failures.extend(documentation_parity_errors())

    valid_paths = sorted((ROOT / "examples").glob("*.json")) + sorted((ROOT / "test-vectors" / "valid").glob("*.json"))
    for path in valid_paths:
        issue = first_document_issue(path, validator)
        if issue:
            failures.append(f"{path.relative_to(ROOT)}: {issue.stage} {issue.code} at {issue.path}: {issue.message}")

    invalid_paths = sorted((ROOT / "test-vectors" / "invalid").glob("*.json"))
    expectations = load_json(EXPECTATIONS_PATH)
    if set(expectations) != {path.name for path in invalid_paths}:
        failures.append("invalid expectations inventory does not exactly match invalid fixtures")
    for path in invalid_paths:
        issue = first_document_issue(path, validator)
        expected = expectations.get(path.name)
        if issue is None:
            failures.append(f"{path.relative_to(ROOT)}: unexpectedly accepted")
        elif expected and {"stage": issue.stage, "code": issue.code, "path": issue.path} != expected:
            failures.append(f"{path.relative_to(ROOT)}: got {issue.stage}/{issue.code}/{issue.path}, expected {expected}")

    failures.extend(fixture_inventory_errors(ROOT / "test-vectors" / "valid"))
    failures.extend(fixture_inventory_errors(ROOT / "test-vectors" / "invalid"))
    failures.extend(link_errors())
    failures.extend(numeric_aid_errors())
    formatter = subprocess.run([sys.executable, str(ROOT / "scripts" / "format_json.py")], cwd=ROOT, text=True, capture_output=True)
    if formatter.returncode:
        failures.extend(line[2:] for line in formatter.stderr.splitlines() if line.startswith("- "))

    if failures:
        print(f"Piccle validation failed with {len(failures)} issue(s):", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Piccle validation passed: schema, {len(valid_paths)} accepted documents, {len(invalid_paths)} rejected documents with stable codes and paths, semantic rules, numeric aids, documentation parity, inventories, canonical JSON, anchors, and links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
