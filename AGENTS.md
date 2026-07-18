# AGENTS.md — Piccle Specification

## 1. Mission

You are working in the specification repository for **Piccle** — the declarative micro-audio format. This repository defines what makes a valid Piccle document and how conforming engines interpret it.

The Piccle format describes short procedural audio experiences: UI feedback, transitions, notifications, confirmations, errors, and other audio micro-interactions.

This repository does **not** implement a playback engine — Piccle's reference engine lives in a separate repository.

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

Changes belong here when they affect the Piccle format itself: top-level document structure, field names/types/defaults/constraints, source/oscillator/envelope/filter/effect/modulation/sequencing/timing semantics, validation behavior, compatibility requirements, versioning rules, normative terminology, official examples, conformance fixtures, format evolution proposals, and specification changelogs.

Changes do not belong here when they are specific to one implementation: Engine internals, Android/iOS playback code, Flutter bindings, platform-specific optimizations, engine-specific public APIs, application integration code, implementation-specific benchmarks, or bugs that do not reveal an ambiguity or defect in the specification. Implementation-specific work belongs in the appropriate engine or SDK repository.

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
| Normative specification                                                                           | `docs/00-overview.md` through `docs/14-conformance.md` |
| JSON naming, units, timing, contours, normative-language glossary                                 | `docs/02-conventions.md`                               |
| Schema-authoring rules                                                                            | `schemas/AGENTS.md`                                    |
| Example-authoring rules                                                                           | `examples/AGENTS.md`                                   |
| Conformance and test-vector rules                                                                 | `docs/14-conformance.md` and `test-vectors/AGENTS.md`  |
| Doc-authoring rules (single canonical source, writing style, audio semantics)                     | `docs/AGENTS.md`                                       |
| Engine safety, resource limits, render profiles                                                   | `docs/11-engine-safety.md`                             |
| Validation gate                                                                                   | `python3 scripts/validate.py` (see `README.md`)        |

## 4. Design principles

Use the following principles when reviewing or proposing changes.

### 4.1 Declarative

A Piccle document describes the intended sound. It must not contain executable code.

Prefer structured, bounded configuration over expressions, scripts, or implementation-specific instructions.

### 4.2 AI-friendly

Field names and structures should be predictable, explicit, and easy to generate correctly.

Prefer:

- Clear words over obscure audio engineering abbreviations.
- Consistent object shapes.
- Explicit units.
- Enumerated values where the valid set is finite.
- Reusable definitions.
- Helpful schema descriptions.
- Small, focused examples.

Avoid:

- Context-dependent field meanings.
- Multiple names for the same concept.
- Clever shorthand.
- Positional arrays whose elements have unrelated meanings.
- Values that require undocumented inference.
- Ambiguous unitless numbers.

### 4.3 Human-readable

A developer should be able to understand the broad behavior of a Piccle asset by reading its JSON.

Do not optimize for a few bytes at the cost of readability. Transport compression can be handled separately.

### 4.4 Portable

Format semantics must not depend on a particular operating system, language, audio framework, or engine.

Do not expose platform-specific concepts in the core format.

### 4.5 Deterministic where practical

Compatible engines should produce perceptually equivalent output from the same document.

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

Piccle exists to produce polished micro-audio.

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
- Do not duplicate normative rules across many files when a canonical section can be referenced.
- Do not create speculative abstractions without an immediate format need.
- Do not add fields merely because another audio format has them.
- Prefer explicit TODOs or open questions over pretending an unresolved behavior is defined.

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

Add subdirectory AGENTS.md files only when those directories develop specialized workflows that cannot be expressed clearly here.

## 7. Final principle

The quality of Piccle depends on the reference engine and any independent engine interpreting the same document consistently.

Optimize every change for:

> Clear documents, predictable generation, safe validation, portable playback, and perceptually expressive micro-audio.

When forced to choose between a clever format and a clear format, choose the clear format.
