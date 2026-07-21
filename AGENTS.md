# AGENTS.md — Piccle Specification

## 1. Mission

You are working in the specification repository for **Piccle** — the declarative micro-audio format. This repository defines what makes a valid Piccle document and exactly how the official Piccle engine parses, validates, schedules, and renders it.

The Piccle format describes short procedural audio signals for UI feedback, transitions, notifications, confirmations, errors, and other audio micro-interactions.

This repository is technical infrastructure for audio engineers, DSP engineers, maintainers of [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs), validation-tool authors, and AI systems operating on the normative format. Consumer-facing tutorials and simplified sound-design documentation live outside this repository.

This repository does **not** contain playback code. The official implementation lives in [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs), and its externally observable document, validation, timing, DSP, and output behavior is defined here.

See `docs/00-overview.md` for the full mission, product promise, and glossary.

## 2. Repository authority

This repository is the canonical specification for Piccle.

When files disagree, use the following priority:

1. The normative specification in `docs/`.
2. The published JSON Schema in `schemas/`.
3. Conformance fixtures and test vectors.
4. Official examples in `examples/`.
5. Explanatory content in `README.md`.

Do not silently resolve contradictions.

When you find a conflict:

1. Identify the conflicting files.
2. Determine the intended behavior from the issue, proposal, or existing normative language.
3. Update every affected artifact in the same change.
4. Explicitly mention the resolved inconsistency in the final summary.

The specification, schema, examples, and changelog must remain synchronized.

## 3. What this repository owns

### Scope of this repository

Changes belong here when they affect the Piccle format or required engine behavior: top-level document structure, field names/types/defaults/constraints, source/oscillator/envelope/filter/effect/modulation/sequencing/timing semantics, validation behavior, calculation order, DSP topology, state initialization, tolerances, compatibility requirements, versioning rules, normative terminology, official examples, qualification fixtures, format evolution proposals, and specification changelogs.

Changes do not belong here when they affect only private code structure: Rust module layout, crate APIs, Android/iOS playback adapters, Flutter bindings, platform I/O, implementation-specific optimizations, application integration code, or benchmarks. Those changes belong in the engine or SDK repository unless they change behavior defined by this specification.

If an implementation issue exposes ambiguity in the format, clarify the format here and fix the implementation separately.

### Product boundaries

Piccle is designed for short, synthetic micro-audio used in user interfaces.

**In scope:** button presses and taps, toggle states, success/warning/error feedback, notifications, one-shot loading-start and progress-event cues, navigation transitions, one-shot gesture-completion feedback, short branded audio signatures, audio synchronized with brief UI animations, layered procedural sounds.

**Out of scope** unless explicitly introduced by a future specification: music composition and full songs, long-form audio timelines, speech or voice synthesis, recorded sample playback, realistic environmental sound simulation, general-purpose digital audio workstations, arbitrary executable audio graphs, unbounded scripts or plugins inside Piccle documents.

Do not expand Piccle into a general-purpose audio production format without an accepted format proposal.

### Repository layout

```
piccle-spec/
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── schemas/          JSON Schema (schema-authoring rules in schemas/AGENTS.md)
├── docs/             Normative specification and supporting docs
├── examples/         Valid Piccle documents (example-authoring rules in examples/AGENTS.md)
└── test-vectors/     Conformance fixtures (rules in test-vectors/AGENTS.md and docs/14-conformance.md)
```

### Where things live

| What                                                                                              | Where                                                  |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Contribution workflow, change categories, versioning, compatibility checklist, definition of done | `CONTRIBUTING.md`                                      |
| Normative format and engine contract                                                               | `docs/00-overview.md` through `docs/15-engine-build-guide.md`, except the explicitly non-normative technical patterns in chapter 12 |
| JSON naming, units, timing, contours, normative-language glossary                                 | `docs/02-conventions.md`                               |
| Schema-authoring rules                                                                            | `schemas/AGENTS.md`                                    |
| Example-authoring rules                                                                           | `examples/AGENTS.md`                                   |
| Conformance and test-vector rules                                                                 | `docs/14-conformance.md` and `test-vectors/AGENTS.md`  |
| Doc-authoring rules (single canonical source, writing style, audio semantics)                     | `docs/AGENTS.md`                                       |
| Engine safety, resource limits, render profiles                                                   | `docs/11-engine-safety.md`                             |
| Required DSP runtime algorithms and state                                                         | `docs/13-implementer-notes.md`                         |
| Official engine implementation and qualification contract                                        | `docs/15-engine-build-guide.md`                        |
| Validation gate                                                                                   | `python3 scripts/validate.py` (see `README.md`)        |

## 4. Design principles

Use the following principles when reviewing or proposing changes.

### 4.1 Declarative

A Piccle document describes the intended sound. It must not contain executable code.

Prefer structured, bounded configuration over expressions, scripts, or implementation-specific instructions.

### 4.2 Machine-explicit

Field names and structures must be predictable, explicit, and mechanically generatable. Optimize for unambiguous parsing, validation, synthesis, and automated authoring rather than introductory readability.

Prefer:

- Established audio-engineering and DSP terminology.
- Consistent object shapes.
- Explicit units.
- Enumerated values where the valid set is finite.
- Reusable definitions.
- Technically precise schema descriptions.
- Small, focused examples.

Avoid:

- Context-dependent field meanings.
- Multiple names for the same concept.
- Clever shorthand.
- Positional arrays whose elements have unrelated meanings.
- Values that require undocumented inference.
- Ambiguous unitless numbers.

### 4.3 Audio-engineering native

An audio engineer or DSP implementer should be able to infer the signal topology, control trajectories, gain staging, temporal boundaries, and spatial processing by inspecting a Piccle document.

Use standard terminology such as oscillator, phase accumulator, spectral centroid, biquad, Q, RT60, FDN, impulse response, wet path, contour, gain, and Nyquist without replacing it with consumer analogies. Define Piccle-specific terms and mathematically ambiguous conventions, but do not teach foundational audio engineering. Do not optimize for a few bytes at the cost of technical legibility; transport compression is separate.

### 4.4 Portable

Format semantics must not depend on a particular operating system, language, audio framework, or engine.

Do not expose platform-specific concepts in the core format.

### 4.5 Deterministic where practical

The Piccle engine MUST produce the defined output from a document in every supported render profile.

When exact sample-level equivalence is impractical, the specification must define:

- Required semantic behavior.
- Permitted implementation variance.
- Relevant bounds or tolerances.
- Whether randomness requires an explicit seed.

Never use vague requirements such as "make it sound good" as normative behavior.

### 4.6 Bounded

Every feature must be safe to validate and practical to render.

Prefer explicit limits for:

- Duration.
- Layer and event counts.
- Frequencies.
- Gain.
- Modulation depth.
- Repetition.
- Nesting.
- Computational complexity.

Do not introduce constructs that can produce infinite or uncontrolled processing.

### 4.7 Backward-compatible by default

Do not break previously valid documents without a major format-version change.

Prefer additive optional fields with well-defined defaults.

### 4.8 Small core, composable features

Prefer a small set of orthogonal primitives that can be combined over many highly specialized event types.

Before adding a new concept, determine whether existing primitives can represent it clearly.

### 4.9 Perceptual value over theoretical completeness

Piccle exists to produce perceptually controlled micro-audio.

Prioritize features that materially improve UI sound design over features added only for completeness or parity with professional synthesizers.

## 5. Agent behavior

When working in this repository:

- Make the smallest complete change that satisfies the task.
- Preserve compatibility unless breaking behavior is explicitly requested.
- Do not invent unstated format behavior.
- Do not redesign unrelated parts of the specification.
- Do not silently normalize inconsistent terminology; investigate it.
- Do not modify published historical versions casually.
- Do not add implementation-specific requirements to the core format.
- Treat “engine” in normative prose as the official Piccle engine in `dotpiccle/engine-rs`; do not write for a hypothetical ecosystem of independent implementations.
- State required calculations, state initialization, processing order, error behavior, and tolerances directly. Do not substitute recommendations when observable behavior is intended.
- Mark internal choices as implementation-defined only when they cannot affect specified output or validation behavior.
- Do not duplicate normative rules across many files when a canonical section can be referenced.
- Do not create speculative abstractions without an immediate format need.
- Do not add fields merely because another audio format has them.
- Prefer explicit TODOs or open questions over pretending an unresolved behavior is defined.
- Assume the reader understands digital audio, synthesis, filtering, gain staging, envelopes, sample frames, and spectral analysis.
- Use canonical audio-engineering and DSP jargon when it is more precise than general-language paraphrase.
- Do not add beginner analogies, consumer-device metaphors, note-frequency primers, or tutorial prose to the normative specification.
- Keep simplified end-user and introductory authoring documentation outside this repository.

When information is missing, inspect existing repository conventions first.

For substantial work, briefly identify:

- Files expected to change.
- Compatibility implications.
- Validation strategy.

## 6. Subdirectory instructions

Subdirectories may contain their own `AGENTS.md` files with more specific instructions. When present:

- `schemas/AGENTS.md` — schema authoring rules
- `examples/AGENTS.md` — example authoring rules
- `test-vectors/AGENTS.md` — conformance fixture guidance

Apply the root instructions first, then the nearest relevant subdirectory instructions next. Treat more specific instructions as overriding broader ones only within their directory scope. Do not copy large sections of this file into nested instruction files.

Subdirectory AGENTS.md files must not re-explain what the project is or what this repository contains. They should be closed in the context they own: a subdirectory AGENTS.md only instructs on how to work within that subdirectory. The root AGENTS.md is the single canonical source for project description, authority hierarchy, repository layout, and design principles.

Add subdirectory AGENTS.md files only when those directories develop specialized workflows that cannot be expressed clearly here.

## 7. Final principle

The quality of Piccle depends on this repository and `dotpiccle/engine-rs` remaining one synchronized product contract.

Optimize every change for:

> Technically exact documents, predictable generation, safe validation, portable DSP behavior, and perceptually expressive micro-audio.

When forced to choose between a clever format and a clear format, choose the clear format.
