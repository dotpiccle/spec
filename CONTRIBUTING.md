# Contributing to Piccle

Piccle is a company that ships a declarative micro-audio format. This repository is the specification for it. Changes must remain clear enough for the reference engine and any independent engine, and constrained enough for untrusted input across browsers, desktop and mobile systems, consoles, vehicles, kiosks, and embedded appliances.

## Design principles

Changes should preserve these properties:

- **Declarative:** documents contain data, never executable code.
- **AI-friendly:** fields are explicit, consistently shaped, and schema-constrained.
- **Readable:** JSON remains understandable without specialist tooling.
- **Portable:** semantics do not depend on a platform audio API.
- **Engine-neutral:** the format defines rendered results without prescribing live, offline, cached, or ahead-of-playback execution.
- **Deterministic where practical:** exact rules are used for validation, timing, and control behavior; measurable tolerances are used where DSP algorithms may vary.
- **Bounded by engines:** valid documents are finite, and engines publish resource limits before allocating render resources.
- **Backward-compatible:** released documents do not change meaning without a new major format version.
- **Small and composable:** new primitives require demonstrated one-shot UI-audio value.

## Documentation model

- `docs/00` through `docs/11` and `docs/14` are normative reference chapters unless a section says otherwise.
- `docs/12-cookbook.md` is a task-oriented authoring guide.
- `docs/13-implementer-notes.md` is non-normative implementation guidance.
- `schemas/v1.json` is the machine-readable structural contract.
- `test-vectors/` verifies parsing, schema, and semantic validation.
- `examples/` demonstrates authoring patterns but is not normative audio output.

Each rule has one canonical documentation home. Other pages link to that rule rather than restating it.

## Proposing a format change

Open an issue describing:

1. The UI-audio problem and concrete assets that cannot be expressed clearly today.
2. The proposed document shape and defaults.
3. Exact units, ranges, timing, boundary behavior, and DSP semantics.
4. Compatibility with every published version.
5. CPU, memory, malicious-input, and determinism implications.
6. At least one realistic example and positive and negative validation cases.

Looping, continuous playback, host-controlled parameters, gesture control, modulation, and theming inputs are intentionally deferred beyond v1 and require a format proposal. Platform support is not a new format feature: engines adapt rates, numeric modes, channels, and resources without changing document validity.

## Making a change

Keep all affected artifacts synchronized:

- normative documentation;
- JSON Schema;
- examples;
- valid and invalid test vectors;
- `CHANGELOG.md`.

Install the validation dependency and run the complete gate:

```bash
python3 -m pip install jsonschema==4.25.1
python3 scripts/validate.py
```

Every invalid fixture must fail for one documented primary reason. Do not alter playback semantics merely to make a fixture pass.

## Versioning

The document field uses `major.minor`, such as `"piccle": "1.0"`. Repository releases use semantic versions, such as `v1.0.0-rc.1` and `v1.0.0`.

- Major format versions may make breaking document changes.
- Minor format versions may add backward-compatible capabilities for newer engines.
- Patch repository releases may clarify text without changing validation or existing playback meaning.

A published schema URI is immutable. Release preparation must verify that the canonical URI serves the exact tagged schema and record its SHA-256 checksum in the release notes.

## Release process

1. Keep changes under the `Unreleased` changelog section.
2. Run repository validation in a clean checkout.
3. Verify the canonical schema URL.
4. Complete the clean-room implementation and listening gates in [Conformance](docs/14-conformance.md).
5. Create an RC tag while any external gate remains open.
6. Move changelog entries to `v1.0.0` only when every stable-release gate is complete.
