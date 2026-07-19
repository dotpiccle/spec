#!/usr/bin/env python3
"""Validate the Piccle schema, documents, contracts, fixtures, and repository."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft201909Validator

from format_json import (
    DuplicateKeyError,
    NonFiniteNumberError,
    NumberOutOfRangeError,
    parse_finite_float,
    reject_duplicate_keys,
    reject_non_finite_constant,
)

import reverb_metrics


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "v1.json"
EXPECTATIONS_PATH = ROOT / "test-vectors" / "invalid-expectations.json"
NUMERIC_PATH = ROOT / "test-vectors" / "numeric" / "dsp-values.json"
BEHAVIOR_PATH = ROOT / "test-vectors" / "behavior" / "render-cases.json"
REVERB_REF_IR_DIR = ROOT / "test-vectors" / "numeric" / "reverb-reference-irs"
NUMERIC_DIR = ROOT / "test-vectors" / "numeric"
CANONICAL_SCHEMA_URI = "https://spec.dotpiccle.com/schema/v1.json"
MAX_SAFE_INTEGER = 9007199254740991


@dataclass(frozen=True)
class Issue:
    stage: str
    code: str
    path: str
    message: str


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_non_finite_constant,
        parse_float=parse_finite_float,
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
        start = layer.get("start_ms", 0)
        if start + duration > MAX_SAFE_INTEGER:
            issues.append(Issue(
                "semantic", "semantic.layer_end_out_of_range",
                f"$.layers[{layer_index}].duration_ms",
                f"start_ms + duration_ms exceeds {MAX_SAFE_INTEGER}",
            ))
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
            fade_out = min(volume.get("fade_out", {}).get("ms", 5), duration)
            elapsed = volume.get("fade_in", {}).get("ms", 0) + contour_time(volume["levels"]) + fade_out
            if elapsed > duration:
                issues.append(Issue(
                    "semantic", "semantic.volume_timing_exceeds_duration",
                    f"$.layers[{layer_index}].volume",
                    f"scheduled {elapsed} ms exceeds layer duration {duration} ms",
                ))
    document_duration = document.get(
        "duration_ms",
        max(layer.get("start_ms", 0) + layer["duration_ms"] for layer in layers),
    )
    reverb = document.get("reverb")
    if reverb is not None and document_duration + reverb["tail_ms"] > MAX_SAFE_INTEGER:
        issues.append(Issue(
            "semantic", "semantic.output_end_out_of_range", "$.reverb.tail_ms",
            f"document duration + tail_ms exceeds {MAX_SAFE_INTEGER}",
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
    except NonFiniteNumberError as error:
        return Issue("parse", "json.non_finite_number", "$", str(error))
    except NumberOutOfRangeError as error:
        return Issue("parse", "json.number_out_of_range", "$", str(error))
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
    expect(set(properties), {"$schema", "piccle", "name", "description", "duration_ms", "master_volume_level", "reverb", "layers"}, "root properties")
    expect(schema["required"], ["piccle", "layers"], "root required fields")
    expect(properties["$schema"].get("const"), CANONICAL_SCHEMA_URI, "instance $schema")
    expect(properties["piccle"].get("enum"), ["1.0"], "piccle versions")
    expect((properties["duration_ms"].get("type"), properties["duration_ms"].get("minimum")), ("integer", 1), "root duration type/minimum")
    expect((properties["master_volume_level"].get("type"), properties["master_volume_level"].get("minimum"), properties["master_volume_level"].get("maximum"), properties["master_volume_level"].get("default")), ("number", 0, 1, 1), "root master_volume_level contract")
    expect("safe-integer bound" in properties["duration_ms"]["description"], True, "root duration derived-bound description")

    layer = defs["layer"]
    expect(layer["required"], ["id", "duration_ms", "source"], "layer required fields")
    expect(layer["properties"]["start_ms"].get("default"), 0, "start default")
    expect(layer["properties"]["balance"].get("default"), 0, "balance default")
    expect(layer["properties"]["filters"].get("default"), [], "filters default")
    expect_property(layer, "start_ms", kind="integer", minimum=0, default=0, has_default=True)
    expect_property(layer, "duration_ms", kind="integer", minimum=1)
    expect_property(layer, "balance", kind="number", minimum=-1, maximum=1, default=0, has_default=True)
    expect("start_ms plus duration_ms" in layer["properties"]["duration_ms"]["description"], True, "layer derived-end description")
    expect(defs["curves"]["enum"], ["linear", "exponential", "easeIn", "easeOut", "easeInOut"], "curve enum")
    expect(defs["filter"]["properties"]["type"]["enum"], ["lowpass", "highpass", "bandpass"], "filter enum")
    expect(defs["filter"]["properties"]["resonance"].get("default"), 0, "resonance default")
    expect(defs["pitch"]["properties"]["offset_cents"].get("default"), 0, "pitch offset default")
    expect(defs["pitch"]["required"], ["frequencies"], "pitch required fields")
    expect_property(defs["pitch"], "offset_cents", kind="integer", minimum=-1200, maximum=1200, default=0, has_default=True)
    expect("after contour interpolation" in defs["pitch"]["properties"]["offset_cents"]["description"], True, "pitch operation-order description")

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
    expect("safe-integer bound" in reverb["properties"]["tail_ms"]["description"], True, "reverb derived-end description")

    noise = defs["source"]["oneOf"][1]["properties"]
    expect(noise["character"]["enum"], ["soft", "neutral", "sharp"], "noise character enum")
    expect((noise["seed"].get("minimum"), noise["seed"].get("maximum"), noise["seed"].get("default")), (0, 4294967295, 0), "seed contract")
    tone_schema, noise_schema = defs["source"]["oneOf"]
    expect(tone_schema["required"], ["type", "wave", "pitch"], "tone required fields")
    expect(tone_schema["properties"]["wave"]["enum"], ["sine", "triangle", "square", "saw"], "wave enum")
    expect(noise_schema["required"], ["type", "character"], "noise required fields")

    volume_object = defs["volume"]["oneOf"][1]
    expect(volume_object["required"], ["levels"], "volume required fields")
    expect(volume_object["properties"]["fade_in"].get("default"), {"ms": 0, "curve": "linear"}, "layer fade-in default")
    expect(volume_object["properties"]["fade_out"].get("default"), {"ms": 5, "curve": "linear"}, "layer fade-out default")
    fade_stage = defs["fade_stage"]
    expect(fade_stage["properties"]["ms"].get("minimum"), 0, "fade_stage ms minimum")
    expect(fade_stage["required"], ["ms"], "fade_stage required fields")
    expect(fade_stage["properties"]["curve"].get("default"), "linear", "fade_stage curve default")
    expect(fade_stage["properties"]["curve"].get("$ref"), "#/$defs/curves", "fade_stage curve $ref")
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
        "docs/01-document-structure.md": {"$schema", "piccle", "name", "description", "duration_ms", "master_volume_level", "reverb", "layers", "id", "start_ms", "source", "balance", "filters"},
        "docs/03-sources.md": {"type", "wave", "pitch", "character", "seed"},
        "docs/04-pitch.md": {"frequencies", "hz", "hold_ms", "transition_ms", "transition_curve", "offset_cents"},
        "docs/05-layer-volume.md": {"fade_in", "fade_out", "levels", "level", "hold_ms", "transition_ms", "transition_curve"},
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
        "docs/01-document-structure.md": ["`duration_ms` | integer", "`master_volume_level` | number  | 1        | No"],
        "docs/05-layer-volume.md": ["`fade_in`  | object | `{\"ms\": 0", "`fade_out` | object | `{\"ms\": 5"],
        "docs/06-filters.md": ["`resonance`   | number | 0", "20-20000 Hz"],
        "docs/07-reverb.md": ["`amount`    | number", "`tail_ms`   | integer | `1` or more", "`soften_hz` | number  | `200`–`12000`"],
        "docs/11-engine-safety.md": ["at least 8000 Hz", "min(20000, 0.49 × sample_rate)", "48000 Hz", "frame(S + b) - frame(S + a)"],
        "docs/04-pitch.md": ["Evaluate the `frequencies` contour", "Apply the cents offset", "Clamp `offset_hz`"],
        "docs/07-reverb.md": ["five_ms_frames", "DSP conformance harness", "1 + floor(0.9 × N)", "Perceptual-equivalence metric algorithms", "next_power_of_two", "hop = max(1, floor(W_m / 4))", "is excluded", "magnitude weighting"],
        "docs/08-output.md": ["Visit active layers in document array order", "[0, F(D + tail_ms))"],
        "docs/14-conformance.md": ["start_ms + duration_ms", "document duration plus `reverb.tail_ms`"],
        "docs/15-engine-build-guide.md": ["schemas/v1.json", "test-vectors/invalid-expectations.json", "test-vectors/numeric/dsp-values.json", "test-vectors/behavior/render-cases.json", "Definition of done"],
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
        "zero_duration_transition_chain": {"declared_targets": [.1, .2, .3], "transition_frames": [0, 0], "first_emitted_target": .3},
        "oscillator_coefficients": {"sine_k1": 1.0, "square_k1": 4/math.pi, "square_k3": 4/(3*math.pi), "saw_k1": 2/math.pi, "saw_k2": -1/math.pi, "triangle_k1": 8/math.pi**2, "triangle_k3": -8/(9*math.pi**2)},
        "balance": {"center_left": math.sqrt(.5), "center_right": math.sqrt(.5), "center_then_mono": 1.0},
        "lowpass_1000_hz_48000_resonance_0": {},
        "render_frequency_max_hz": {str(rate): min(20000, .49*rate) for rate in (8000, 16000, 22050, 44100, 48000)},
        "absolute_boundary_frames_at_44100": {"frame_4_ms": 176, "frame_8_ms": 353, "span_4_to_8_ms": 177, "independently_rounded_4_ms": 176},
        "pitch_transform_order": {"20_hz_minus_1200_cents_canonical": 20.0, "20000_hz_plus_1200_cents_canonical": 20000.0, "10000_hz_at_8000_sample_rate": 3920.0},
        "canonical_mix_order": {"samples_in_array_order": [1.0, 2**-53, -1.0], "binary64_result": 0.0},
        "dft_sine_reference": {"real": 0.0, "imaginary": -1.0, "amplitude": 1.0, "phase_from_sine": 0.0},
        "reverb_terminal_window_frames_at_48000": {f"tail_{tail}_ms": max(2, min(240, math.ceil((48*tail)/10))) for tail in (1, 10, 20, 500)},
        "reverb_tail_1_ms_terminal_gains": {"window_start_frame_in_tail": 43, "gains": [1.0, .75, .5, .25, 0.0]},
        "reverb_absolute_tail_frames_at_44100": {"document_duration_ms": 4, "tail_ms": 4, "dry_end_frame": 176, "output_end_frame": 353, "tail_frames": 177},
    }

    def baseline_lengths(tail_ms: int, caps_ms: list[float] | None, ratios: list[float]) -> list[int]:
        response_frames = 48 * tail_ms
        lengths: list[int] = []
        for i, ratio in enumerate(ratios):
            proportional = math.floor(response_frames * ratio + .5)
            if caps_ms is not None:
                cap_frames = math.floor(caps_ms[i] * 48 + .5)
                raw = max(1, min(cap_frames, proportional))
            else:
                raw = max(1, proportional)
            lengths.append(min(response_frames, max(raw, lengths[-1] + 1 if lengths else 1)))
        return lengths

    allpass_ratios = [.003, .006, .012, .024]
    fdn_ratios = [.004, .006, .009, .013, .019, .027, .038, .053]
    baseline = {}
    for tail_ms in (1, 20, 220, 500):
        baseline[f"tail_{tail_ms}_ms"] = {
            "allpass_left_frames": baseline_lengths(tail_ms, [.17, .31, .53, .89], allpass_ratios),
            "allpass_right_frames": baseline_lengths(tail_ms, [.23, .41, .67, 1.07], allpass_ratios),
            "fdn_frames": baseline_lengths(tail_ms, None, fdn_ratios),
            "direct_gain": min(1.5, max(.7, .7 * math.sqrt(220 / tail_ms))),
        }
    expected["reverb_baseline_at_48000"] = baseline
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
            # Float comparison uses isclose to accommodate last-bit differences in
            # sin/cos-derived entries (lowpass coefficients). All other floats are
            # deterministic (sqrt is correctly-rounded per IEEE-754; constants are exact)
            # and pass isclose trivially. See docs/15-engine-build-guide.md step 3
            # and docs/14-conformance.md §Role of repository fixtures.
            if not math.isclose(float(left), right, rel_tol=1e-14, abs_tol=1e-15):
                failures.append(f"numeric aid {path}: {left!r} != {right!r}")
        elif left != right:
            failures.append(f"numeric aid {path}: {left!r} != {right!r}")
    compare(actual, expected, "$")
    return failures


def behavior_aid_errors() -> list[str]:
    manifest = load_json(BEHAVIOR_PATH)
    failures: list[str] = []
    if manifest.get("status") != "non-normative":
        failures.append("behavior aids: status must be non-normative")

    for case in manifest.get("cases", []):
        rate = case["sample_rate"]
        document_path = (BEHAVIOR_PATH.parent / case["document"]).resolve()
        if not document_path.is_relative_to(ROOT) or not document_path.exists():
            failures.append(f"behavior aid {case['id']}: missing document {case['document']}")
            continue
        document = load_json(document_path)

        def frame(milliseconds: int | float) -> int:
            return math.floor(milliseconds * rate / 1000 + 0.5)

        duration = document.get(
            "duration_ms",
            max(layer.get("start_ms", 0) + layer["duration_ms"] for layer in document["layers"]),
        )
        dry_end = frame(duration)
        reverb = document.get("reverb")
        output_end = frame(duration + reverb["tail_ms"]) if reverb else dry_end
        tail_frames = output_end - dry_end
        terminal_frames = (
            max(2, min(frame(5), math.ceil(tail_frames / 10))) if reverb else 0
        )
        layers: list[dict[str, Any]] = []
        for layer in document["layers"]:
            start = layer.get("start_ms", 0)
            end = start + layer["duration_ms"]
            volume = layer.get("volume", 1)
            fade_ms = volume.get("fade_out", {}).get("ms", 5) if isinstance(volume, dict) else 5
            fade_start = end - min(fade_ms, layer["duration_ms"])
            declared_start_frame = frame(start)
            declared_end_frame = frame(end)
            layers.append({
                "id": layer["id"],
                "declared_start_frame": declared_start_frame,
                "declared_end_frame": declared_end_frame,
                "active_end_frame": min(declared_end_frame, dry_end),
                "fade_start_frame": frame(fade_start),
                "fade_frames": declared_end_frame - frame(fade_start),
            })
        actual = {
            "document_duration_ms": duration,
            "dry_end_frame": dry_end,
            "output_end_frame": output_end,
            "tail_frames": tail_frames,
            "terminal_window_frames": terminal_frames,
            "layers": layers,
        }
        if actual != case["expected"]:
            failures.append(
                f"behavior aid {case['id']}: computed {actual!r}, expected {case['expected']!r}"
            )
    return failures


def reverb_reference_ir_errors() -> list[str]:
    failures: list[str] = []
    manifest_path = REVERB_REF_IR_DIR / "manifest.json"
    if not manifest_path.exists():
        failures.append(f"reverb reference IR manifest not found: {manifest_path}")
        return failures
    manifest = load_json(manifest_path)
    if manifest.get("status") != "non-normative":
        failures.append("reverb reference IR manifest: status must be non-normative")
    for entry in manifest.get("fixtures", []):
        path = REVERB_REF_IR_DIR / entry["filename"]
        if not path.exists():
            failures.append(f"reverb reference IR fixture missing: {path}")
            continue
        data = path.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != entry["sha256"]:
            failures.append(f"reverb reference IR fixture {entry['filename']}: SHA-256 mismatch (expected {entry['sha256']}, got {actual_sha})")
        expected_size = entry["sample_count"] * entry["channels"] * 8
        if len(data) != expected_size:
            failures.append(f"reverb reference IR fixture {entry['filename']}: size {len(data)} != expected {expected_size}")

        N = entry["sample_count"] - 1
        T = N + 1
        samples = struct.unpack(f"<{T * 2}d", data)
        L = list(samples[0::2])
        R = list(samples[1::2])
        E = [L[k] ** 2 + R[k] ** 2 for k in range(T)]
        suffix = [0.0] * T
        s = 0.0
        for k in range(T - 1, -1, -1):
            s += E[k]
            suffix[k] = s
        E0 = suffix[0] if T > 0 else 0.0
        crossing = T - 1
        for k in range(T - 1):
            if suffix[k] <= 1e-6 * E0:
                crossing = k
                break
        min_c = 1 + int(math.floor(0.9 * N))
        if not (min_c <= crossing <= N):
            tail_ms = entry["tail_ms"]
            failures.append(
                f"reverb reference IR fixture {entry['filename']}: "
                f"RT60 crossing frame {crossing} outside permitted range "
                f"[{min_c}, {N}] (tail_ms={tail_ms}, N={N}, "
                f"docs/07-reverb.md requires 1 + floor(0.9 · N) <= c <= N)"
            )
    return failures


def reverb_reference_ir_metrics_errors() -> list[str]:
    failures: list[str] = []
    manifest_path = REVERB_REF_IR_DIR / "manifest.json"
    if not manifest_path.exists():
        return failures
    manifest = load_json(manifest_path)
    for entry in manifest.get("fixtures", []):
        if "metrics" not in entry:
            failures.append(f"{entry['filename']}: no metrics block in manifest")
            continue
        path = REVERB_REF_IR_DIR / entry["filename"]
        if not path.exists():
            continue
        data = path.read_bytes()
        T = entry["sample_count"]
        samples = struct.unpack(f"<{T * 2}d", data)
        L = list(samples[0::2])
        R = list(samples[1::2])
        computed = reverb_metrics.compute_all(L, R, entry)
        published = entry["metrics"]
        for key in sorted(computed):
            engine_val = computed[key]
            ref_val = published.get(key)
            ok, desc = reverb_metrics.check_metric(key, engine_val, ref_val)
            if not ok:
                failures.append(f"{entry['filename']}: {desc}")
    return failures


def reverb_matrix_vector_errors() -> list[str]:
    """Verify the reverb matrix test vector matches the generator."""
    failures: list[str] = []
    vector_path = NUMERIC_DIR / "reverb-matrix-vector.json"
    if not vector_path.exists():
        failures.append(f"missing matrix test vector: {vector_path}")
        return failures

    vector = load_json(vector_path)
    config = vector["configuration"]
    tail_ms = config["tail_ms"]
    soften_hz = config["soften_hz"]

    from generate_reverb_reference_irs import _config_seed, _pcg32, _random_orthogonal_matrix

    # Verify seed
    expected_seed = _config_seed(tail_ms, soften_hz)
    if vector["seed"] != expected_seed:
        failures.append(f"matrix vector: seed mismatch, expected {expected_seed}, got {vector['seed']}")

    # Verify first 8 PCG32 outputs
    rng = _pcg32(expected_seed)
    for i, expected_u in enumerate(vector["pcg32_first_8_u32"]):
        actual_u = rng()
        if actual_u != expected_u:
            failures.append(f"matrix vector: pcg32 output {i} mismatch, expected {expected_u}, got {actual_u}")
            break

    # Verify feedback matrix Q
    Q = _random_orthogonal_matrix(8, expected_seed)
    for i in range(8):
        for j in range(8):
            if Q[i][j] != vector["feedback_matrix_q"][i][j]:
                failures.append(f"matrix vector: Q[{i}][{j}] mismatch, expected {vector['feedback_matrix_q'][i][j]}, got {Q[i][j]}")
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
    failures.extend(reverb_reference_ir_errors())
    failures.extend(reverb_reference_ir_metrics_errors())
    failures.extend(reverb_matrix_vector_errors())
    failures.extend(behavior_aid_errors())
    formatter = subprocess.run([sys.executable, str(ROOT / "scripts" / "format_json.py")], cwd=ROOT, text=True, capture_output=True)
    if formatter.returncode:
        failures.extend(line[2:] for line in formatter.stderr.splitlines() if line.startswith("- "))

    if failures:
        print(f"Piccle validation failed with {len(failures)} issue(s):", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"Piccle validation passed: schema, {len(valid_paths)} accepted documents, {len(invalid_paths)} rejected documents with stable codes and paths, semantic rules, numeric and behavior aids, reverb metric baselines, documentation parity, inventories, canonical JSON, anchors, and links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
