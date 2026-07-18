# AGENTS.md — Piccle Specification

## 0. Mission

You are working in the specification repository for **Piccle**.

Piccle is an open, declarative format for describing short procedural audio experiences such as UI feedback, transitions, notifications, confirmations, errors, and other audio micro-interactions.

This repository defines:

- What a valid Piccle document looks like.
- What each field means.
- How compliant engines must interpret the format.
- How the format evolves.
- Which examples and test cases represent expected behavior.

This repository does **not** implement a playback engine.

### Core product promise

> Enable developers, designers, and AI agents to create high-quality, low-latency, lightweight, and expressive micro-audio using structured data.

Piccle aims to become the **“Lottie for audio”**: a portable and expressive format for audio animations and micro-interactions.

A Piccle asset should be:

- Small enough to ship with an application.
- Easy for humans to read and edit.
- Easy for AI systems to generate reliably.
- Deterministic enough for compatible engines to interpret consistently.
- Expressive enough to create polished UI audio without prerecorded WAV or MP3 assets.
- Safe and efficient enough for engines across interactive platforms, including constrained embedded devices.

---

## 1. Repository authority

This repository is the canonical source of truth for the Piccle format.

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

---

## 2. Scope of this repository

Changes belong in this repository when they affect the Piccle format itself, including:

- Top-level document structure.
- Field names, types, defaults, and constraints.
- Source, oscillator, envelope, filter, effect, modulation, sequencing, or timing semantics.
- Validation behavior.
- Compatibility requirements.
- Versioning rules.
- Normative terminology.
- Official examples.
- Conformance fixtures.
- Format evolution proposals.
- Specification changelogs.

Changes do not belong here when they are specific to one implementation, including:

- Rust engine internals.
- Android or iOS playback code.
- Flutter bindings.
- Platform-specific optimizations.
- Engine-specific public APIs.
- Application integration code.
- Implementation-specific benchmarks.
- Bugs that do not reveal an ambiguity or defect in the specification.

Implementation-specific work should go to the appropriate engine or SDK repository.

If an implementation issue exposes ambiguity in the format, clarify the format here and fix the implementation separately.

---

## 3. Product boundaries

Piccle is designed for short, synthetic micro-audio used in user interfaces.

### In scope

- Button presses and taps.
- Toggle states.
- Success, warning, and error feedback.
- Notifications.
- One-shot loading-start and progress-event cues.
- Navigation transitions.
- One-shot gesture-completion feedback.
- Short branded audio signatures.
- Audio synchronized with brief UI animations.
- Layered procedural sounds.

### Out of scope unless explicitly introduced by a future specification

- Music composition and full songs.
- Long-form audio timelines.
- Speech or voice synthesis.
- Recorded sample playback.
- Realistic environmental sound simulation.
- General-purpose digital audio workstations.
- Arbitrary executable audio graphs.
- Unbounded scripts or plugins inside Piccle documents.

Do not expand Piccle into a general-purpose audio production format without an accepted format proposal.

---

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

Never use vague requirements such as “make it sound good” as normative behavior.

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

---

## 5. Normative language

Use the following terms consistently in normative documentation:

- **MUST**: an absolute requirement.
- **MUST NOT**: an absolute prohibition.
- **SHOULD**: recommended unless a valid reason exists to do otherwise.
- **SHOULD NOT**: discouraged unless a valid reason exists.
- **MAY**: optional behavior.
- **Undefined behavior**: behavior on which the specification intentionally places no requirements.
- **Invalid document**: a document that violates a normative format requirement.
- **Unsupported document**: a valid document using a recognized feature that an implementation does not support.

Use uppercase normative terms only when expressing actual conformance requirements.

Avoid using “should” casually in normative sections. Use ordinary alternatives such as “is intended to” or “typically” for non-normative guidance.

---

## 6. Repository layout

```text
piccle-spec/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── LICENSE
│
├── schemas/
│   ├── <version>.json
│   └── ...
│
├── docs/
│   ├── ...
│   └── ...
│
├── examples/
│   ├── ...
│   └── ...
│
├── test-vectors/
    ├── valid/
    ├── invalid/
    └── ...

```

Not every directory must exist during the earliest repository stage. When introducing one, document its purpose in `README.md`.

### `schemas/`

Contains published JSON Schemas for Piccle versions.

Schemas are machine-readable validation contracts. They must match the normative specification but should not be the only place where semantics are explained.

The published schema file (e.g., `v1.json`) is self-contained — all reusable definitions live under `$defs` within the file. There is no separate `definitions/` directory; the schema can be validated offline without resolving remote references.

### `docs/`

Contains the human-readable specification and supporting documentation.

Clearly distinguish normative requirements from explanatory notes and recommendations.

### `examples/`

Contains small, polished, valid Piccle documents demonstrating real use cases.

Examples are part of the public developer experience. Keep them intentional and production-relevant.

### `test-vectors/`

Contains machine-verifiable conformance cases.

Use test vectors for edge cases, invalid inputs, defaults, numerical boundaries, version compatibility, and behaviors that examples should not be burdened with explaining.

### `CHANGELOG.md`

Records released, user-visible changes to the specification.

Do not use the changelog as a commit log.

---

## 7. Before making changes

Before editing:

1. Read `README.md`.
2. Locate the relevant normative documentation.
3. Inspect the current schema version.
4. Search examples and test vectors for the affected fields.
5. Check `CHANGELOG.md`.
6. Identify whether the requested change is:
   - Editorial.
   - A clarification.
   - Additive and backward-compatible.
   - Behavior-changing.
   - Breaking.

Do not assume that changing only the JSON Schema is sufficient.

Do not create a new format concept before checking whether an equivalent concept already exists under another name.

Preserve established terminology unless renaming is explicitly part of the task.

---

## 8. Change categories

### 8.1 Editorial change

Examples:

- Correcting grammar.
- Improving explanations.
- Fixing broken links.
- Reorganizing non-normative content.

An editorial change must not alter valid documents or rendered behavior.

Update only the affected documentation unless the edit reveals inconsistencies elsewhere.

### 8.2 Clarification

A clarification makes existing intended behavior more explicit without intentionally changing it.

For a clarification:

- Update the normative documentation.
- Add or update a test vector when ambiguity could affect implementations.
- Update schema descriptions when relevant.
- Mention the clarification in the changelog when users or implementers could notice it.

### 8.3 Additive feature

An additive feature introduces new optional behavior while preserving existing documents.

For an additive feature, normally update:

- Normative documentation.
- JSON Schema.
- At least one focused example.
- Relevant valid and invalid test vectors.
- Changelog.
- Proposal, when the feature is substantial.

### 8.4 Breaking change

A breaking change includes:

- Removing or renaming a field.
- Changing a field’s type.
- Changing a default in a way that alters existing playback.
- Making previously valid documents invalid.
- Changing the interpretation of an existing value.
- Tightening a constraint beyond the range allowed by the current version.
- Requiring engines to produce materially different output for existing assets.

Do not introduce a breaking change casually.

A breaking change requires:

- Explicit user authorization or an accepted proposal.
- A new major format version.
- Migration documentation.
- Updated schemas and test vectors.
- Changelog documentation.
- A clear compatibility analysis.

---

## 9. Schema rules

All JSON Schemas must be valid for the repository’s selected JSON Schema dialect.

### Required schema practices

- Include an explicit `$schema`.
- Give each published root schema a stable `$id`.
- Reuse common structures through `$ref`.
- Add a clear `description` to public properties.
- Define numerical bounds where the format has bounds.
- Use `enum` for finite value sets.
- Define required properties explicitly.
- Make unknown-property behavior intentional.
- Keep defaults aligned with normative documentation.
- Include units in property names or descriptions.
- Keep schemas deterministic and free of remote dependencies that may disappear.

### Unknown properties

The specification must intentionally decide whether unknown properties are:

- Rejected.
- Ignored.
- Reserved for extensions.

Do not change `additionalProperties` or equivalent behavior without considering forward compatibility.

### Defaults

A schema `default` is not automatically an engine requirement.

Every engine-applied default must also be stated in normative documentation.

When adding or changing a default, update:

- Schema.
- Normative documentation.
- Examples where the default matters.
- Test vectors.
- Changelog when behavior changes.

### Numerical fields

For every numerical field, define:

- Unit.
- Allowed range.
- Whether endpoints are inclusive.
- Default, when applicable.
- Behavior for zero.
- Precision expectations.
- Behavior for non-finite values, where relevant.

JSON does not permit `NaN` or infinity. Do not invent string representations for them without an explicit proposal.

### Reusable definitions

Place a definition under `$defs` within the schema file when it is genuinely shared or conceptually stable.

Do not fragment schemas into tiny files that make the format harder to understand.

### Schema descriptions

Descriptions should explain the field’s meaning, not merely restate its type.

Bad:

> A number representing duration.

Better:

> The event duration in milliseconds. It MUST be greater than zero and MUST not extend beyond the document timeline unless the event explicitly permits truncation.

---

## 10. Format naming rules

Use names that are clear to developers who are not audio engineers.

### Field names

- Use `snake_case`.
- Prefer complete, familiar words.
- Use the same suffix for the same unit.
- Avoid abbreviations unless universally understood.
- Do not encode types into names.
- Do not use different names for the same concept in different objects.

Examples:

- `duration_ms`
- `start_ms`
- `frequency_hz`
- `gain`
- `waveform`
- `attack_ms`

If the format establishes a different unit convention globally, follow that convention consistently instead of mixing styles.

### Enumerated values

- Use `UPPERCASE`.
- Choose names based on audible or semantic meaning.
- Do not expose implementation class names.
- Do not create aliases without a compatibility reason.

---

## 11. Timing and unit rules

Timing behavior is a core interoperability surface.

Every timing-related feature must specify:

- Unit.
- Reference origin.
- Whether events may overlap.
- Boundary behavior.
- Ordering when multiple events share a timestamp.
- Truncation behavior.
- Duration calculation.
- Loop or repeat semantics, when applicable.

Do not rely on JSON property order to define playback order.

If event order matters when timestamps are equal, define an explicit deterministic rule.

Use one canonical unit for each concept across the format unless there is a strong reason not to.

---

## 12. Audio semantic rules

When introducing or changing an audio primitive, define enough behavior for independent engines to produce perceptually equivalent results.

Depending on the feature, document:

- Input and output range.
- Initial state.
- Time evolution.
- Curve or interpolation behavior.
- Combination behavior with other nodes or events.
- Clamping or normalization.
- Channel behavior.
- Randomness and seeding.
- Behavior at document boundaries.
- Whether the feature is required or optional for conforming engines.
- Allowed implementation tolerance.

Do not require one platform API, synthesis library, or DSP implementation.

Specify observable behavior, not internal architecture.

---

## 13. Examples

Every example must:

- Validate against its declared schema version.
- Demonstrate one primary concept or use case.
- Use realistic UI-sound durations and parameter values.
- Be understandable without unrelated complexity.
- Include `$schema` when that is part of the Piccle convention.
- Use canonical formatting.
- Avoid deprecated fields.
- Have a descriptive filename.

Prefer examples such as:

- `button-click.json`
- `toggle-on.json`
- `toggle-off.json`
- `success.json`
- `warning.json`
- `error.json`
- `notification.json`
- `transition.json`

Do not use examples as substitutes for normative definitions.

When adding a public feature, provide the smallest example that demonstrates its value.

When changing an existing example’s audible behavior, explain why.

---

## 14. Test vectors and conformance

Examples teach. Test vectors verify.

Add test vectors for:

- Minimum and maximum accepted values.
- Missing required properties.
- Unknown properties.
- Invalid enum values.
- Invalid nesting.
- Defaults.
- Simultaneous events.
- Boundary timestamps.
- Unsupported versions.
- Deprecated constructs.
- Deterministic random behavior.
- Features with implementation tolerances.

### Valid vectors

A valid vector should state:

- What behavior it tests.
- Which schema version applies.
- Expected validation result.
- Expected semantic result when practical.

### Invalid vectors

An invalid vector should fail for one primary reason.

Do not create a fixture containing many unrelated errors unless it specifically tests multi-error reporting.

### Rendered reference output

Do not treat a WAV render from one implementation as normative unless the specification explicitly defines sample-exact output.

Reference renders may be included as non-normative aids, but their role and generation method must be documented.

---

## 15. Documentation style

Write for three audiences:

1. Engine implementers.
2. Application developers and sound designers.
3. AI agents generating Piccle documents.

### Normative sections

Normative sections must be precise and testable.

Include:

- Valid types.
- Required behavior.
- Defaults.
- Units.
- Bounds.
- Error conditions.
- Compatibility behavior.

### Non-normative sections

Use notes and examples to explain intent, common patterns, and design guidance.

Clearly label non-normative content where confusion is possible.

### Writing style

- Use concise sentences.
- Prefer active voice.
- Define a term before using it.
- Use one term consistently.
- Avoid marketing language inside normative sections.
- Avoid words such as “simple,” “obvious,” “normal,” or “reasonable” when they replace a precise rule.
- Use examples after defining behavior, not instead of defining it.
- Include JSON snippets when they materially improve understanding.

### Single canonical source

Each normative rule, formula, constraint, or field definition MUST live in exactly one doc — its **canonical home**. Other docs that need to mention it MUST give a brief context-specific note plus a `See docs/XX` reference, not a restatement.

Why: restating a rule in two places guarantees they will drift. When the rule changes, one copy is updated and the other is forgotten, creating a silent contradiction.

When to reference vs. restate:

- **Reference**: the rule itself, the formula, the constraint, the default value, the behavior description.
- **Restate (briefly)**: only what the reader needs to understand the current doc's context — e.g., "the safety clipper runs at this signal-flow stage" without restating the full normative requirement.

Field tables are an exception: a table may include a brief one-line description of each field even if the full definition lives elsewhere, provided the table entry links to the canonical doc.

---

## 16. Versioning

Piccle format versions represent compatibility contracts, not repository release numbers.

Follow the versioning policy documented by the repository.

Until a more specific policy is established:

- Major versions may introduce breaking format changes.
- Minor versions may introduce backward-compatible optional features.
- Patch versions may clarify or correct the specification without intentionally changing valid document behavior.

Do not create a new schema version only because documentation wording changed.

Do create an appropriate new version when validation or engine interpretation changes incompatibly.

Every Piccle document must have an unambiguous way to identify the format version it targets.

Published schemas must remain available at stable canonical locations.

Never modify a published historical schema in a way that silently changes its validation contract. Correct serious defects through an explicitly documented revision process.

---

## 17. Changelog rules

Update `CHANGELOG.md` for user-visible specification changes.

Group entries under categories such as:

- Added
- Changed
- Deprecated
- Removed
- Fixed
- Security

A good changelog entry explains the user-facing or implementer-facing effect.

Bad:

> Updated envelope files.

Better:

> Clarified that zero-duration envelope stages transition immediately without consuming timeline duration.

Do not add changelog entries for formatting-only edits unless the repository’s release process requires them.

Do not claim a version is released unless it has actually been released.

---

## 18. Compatibility checklist

Before completing a format change, answer:

- Do existing valid documents remain valid?
- Do they retain the same meaning?
- Could existing engines reject the new document?
- Can engines safely ignore the new field?
- Is the default behavior explicit?
- Are unknown-field rules sufficient?
- Does this require a new version?
- Is migration guidance required?
- Could an AI generator confuse the new field with an existing field?
- Could this create unbounded CPU or memory use?
- Could different engines reasonably interpret it differently?

Document material compatibility decisions in the proposal, specification, or pull request.

---

## 19. Security and resource safety

Treat every Piccle document as untrusted input.

The specification must support implementations that can validate documents before rendering them.

Do not introduce features that require engines to:

- Execute arbitrary code.
- Access the network.
- Read arbitrary files.
- Load unbounded external resources.
- Allocate unbounded memory.
- Perform unbounded recursion.
- Render indefinitely.
- Trust undocumented extension behavior.

For new features, consider:

- Maximum document duration.
- Maximum events and layers.
- Maximum nesting depth.
- Numeric overflow.
- Excessive gain and clipping.
- Inaudible but computationally expensive content.
- Maliciously large JSON documents.
- Pathological modulation rates.
- Denial-of-service through expansion or repetition.

Where appropriate, define specification-level limits. Otherwise, explicitly permit implementations to enforce documented resource limits.

---

## 20. Required synchronized updates

Use this table to determine commonly affected files:

| Change                  | Schema | Docs | Examples | Test vectors |  Changelog |
| ----------------------- | -----: | ---: | -------: | -----------: | ---------: |
| Grammar only            |     No |  Yes |       No |           No | Usually no |
| Semantic clarification  |  Maybe |  Yes |    Maybe |      Usually |      Often |
| New optional field      |    Yes |  Yes |      Yes |          Yes |        Yes |
| New enum value          |    Yes |  Yes |      Yes |          Yes |        Yes |
| Default change          |    Yes |  Yes |      Yes |          Yes |        Yes |
| Constraint change       |    Yes |  Yes |    Maybe |          Yes |        Yes |
| Field rename or removal |    Yes |  Yes |      Yes |          Yes |        Yes |
| New major feature       |    Yes |  Yes |      Yes |          Yes |        Yes |

Treat this as guidance, not permission to omit an affected artifact.

---

## 21. Agent behavior

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

---

## 22. Definition of done

A change is complete only when:

- The requested behavior is addressed.
- Normative semantics are unambiguous.
- Schema and documentation agree.
- Defaults, units, ranges, and boundary behavior are defined.
- Relevant examples are valid and focused.
- Relevant positive and negative test vectors exist.
- Compatibility impact has been considered.
- Versioning impact has been considered.
- Security and resource implications have been considered.
- Changelog and proposal files are updated when required.
- Available validation commands pass.
- Unrelated files remain unchanged.
- The final summary states what changed and which checks were run.

For format additions, an independent engine implementer should be able to implement the feature without guessing.

An AI agent should be able to generate a valid example without relying on undocumented conventions.

---

## 23. Local instructions

Subdirectories may contain their own `AGENTS.md` files with more specific instructions.

When present:

- Apply the root instructions first.
- Apply the nearest relevant subdirectory instructions next.
- Treat more specific instructions as overriding broader ones only within their directory scope.
- Do not copy large sections of this file into nested instruction files.

Good candidates for future scoped instructions include:

```text
schemas/AGENTS.md
examples/AGENTS.md
test-vectors/AGENTS.md
```

Add them only when those directories develop specialized workflows that cannot be expressed clearly here.

---

## 24. Final principle

The quality of Piccle depends on independent engines interpreting the same document consistently.

Optimize every change for:

> Clear documents, predictable generation, safe validation, portable playback, and perceptually expressive micro-audio.

When forced to choose between a clever format and a clear format, choose the clear format.
