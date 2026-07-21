# Contributing to Piccle

Piccle is a company that ships a declarative micro-audio format and the official [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs) implementation. This repository is the normative format and engine-behavior contract. Changes must be unambiguous to audio engineers, engine maintainers, tooling authors, and AI infrastructure, and constrained enough for untrusted input across browsers, desktop and mobile systems, consoles, vehicles, kiosks, and embedded appliances.

## Design principles

Changes MUST preserve these properties:

- **Declarative:** documents contain data, never executable code.
- **Machine-explicit:** fields are structurally regular, schema-constrained, unit-explicit, and suitable for deterministic automated generation.
- **Audio-engineering native:** terminology describes synthesis, DSP topology, gain structure, timing, and perceptual constraints directly.
- **Portable:** semantics do not depend on a platform audio API.
- **Engine-neutral:** the format defines rendered results without prescribing live, offline, cached, or ahead-of-playback execution.
- **Deterministic where practical:** exact rules are used for validation, timing, and control behavior; measurable tolerances are used where DSP algorithms may vary.
- **Bounded by engine profiles:** valid documents are finite, and each Piccle engine profile publishes resource limits before allocating render resources.
- **Backward-compatible:** released documents do not change meaning without a new major format version.
- **Small and composable:** new primitives require demonstrated one-shot UI-audio value.

## Documentation model

- [Docs 00 through 11](docs/00-overview.md), [Piccle Engine DSP Runtime](docs/13-implementer-notes.md), [Conformance](docs/14-conformance.md), and the [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md) are normative unless a section says otherwise.
- [Technical Authoring Patterns](docs/12-cookbook.md) is a non-normative collection of synthesis and DSP configurations.
- [Piccle Engine DSP Runtime](docs/13-implementer-notes.md) defines required runtime algorithms, state preparation, and render-loop invariants.
- [schemas/v1.json](schemas/v1.json) is the machine-readable structural contract.
- [test-vectors/](test-vectors/) verifies parsing, schema, and semantic validation.
- [examples/](examples/) demonstrates authoring patterns but is not normative audio output.

Each rule has one canonical documentation home. Other pages link to that rule rather than restating it.

This repository assumes proficiency with digital audio and signal processing. Introductory tutorials, consumer analogies, note-frequency primers, and simplified authoring guidance belong outside the specification repository.

## Proposing a format change

Open an issue describing:

1. The UI-audio problem and concrete assets that cannot be expressed clearly today.
2. The proposed document shape and defaults.
3. Exact units, ranges, timing, boundary behavior, and DSP semantics.
4. Compatibility with every published version.
5. CPU, memory, malicious-input, and determinism implications.
6. At least one realistic example and positive and negative validation cases.

Looping, continuous playback, host-controlled parameters, gesture control, modulation, and theming inputs are intentionally deferred beyond v1 and require a format proposal. Platform support is not a new format feature: Piccle engine profiles adapt rates, numeric modes, channels, and resources without changing document validity.

### Before making changes

1. Read `README.md`.
2. Locate the relevant normative documentation.
3. Inspect the current schema version.
4. Search examples and test vectors for the affected fields.
5. Check `CHANGELOG.md`.
6. Identify whether the requested change is: editorial, a clarification, additive and backward-compatible, behavior-changing, or breaking.

Do not assume that changing only the JSON Schema is sufficient. Do not create a new format concept before checking whether an equivalent concept already exists under another name. Preserve established terminology unless renaming is explicitly part of the task.

## Change categories

### Editorial change

Examples: correcting grammar, improving explanations, fixing broken links, reorganizing non-normative content.

An editorial change must not alter valid documents or rendered behavior. Update only the affected documentation unless the edit reveals inconsistencies elsewhere.

### Clarification

A clarification makes existing intended behavior more explicit without intentionally changing it.

For a clarification:

- Update the normative documentation.
- Add or update a test vector when ambiguity could affect implementations.
- Update schema descriptions when relevant.
- Mention the clarification in the changelog when users or implementers could notice it.

### Additive feature

An additive feature introduces new optional behavior while preserving existing documents.

For an additive feature, normally update:

- Normative documentation.
- JSON Schema.
- At least one focused example.
- Relevant valid and invalid test vectors.
- Changelog.
- Proposal, when the feature is substantial.

### Breaking change

A breaking change includes: removing or renaming a field; changing a field's type or default in a way that alters existing playback; making previously valid documents invalid; changing the interpretation of an existing value; tightening a constraint beyond the range allowed by the current version; or requiring the Piccle engine to produce materially different output for existing assets.

Do not introduce a breaking change casually.

A breaking change requires:

- Explicit user authorization or an accepted proposal.
- A new major format version.
- Migration documentation.
- Updated schemas and test vectors.
- Changelog documentation.
- A clear compatibility analysis.

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

### Synchronized updates matrix

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

This matrix is mandatory for affected artifacts; it does not permit omission of an unlisted dependency.

## Compatibility checklist

Before completing a format change, answer:

- Do existing valid documents remain valid?
- Do they retain the same meaning?
- Could the current Piccle engine reject the new document?
- Can the Piccle engine safely ignore the new field while loading an older format version?
- Is the default behavior explicit?
- Are unknown-field rules sufficient?
- Does this require a new version?
- Is migration guidance required?
- Could an AI generator confuse the new field with an existing field?
- Could this create unbounded CPU or memory use?
- Could `dotpiccle/engine-rs` require an unstated calculation, state transition, or error behavior?

Document material compatibility decisions in the proposal, specification, or pull request.

## Changelog rules

Update `CHANGELOG.md` for user-visible specification changes.

Group entries under categories such as:

- Added
- Changed
- Deprecated
- Removed
- Fixed
- Security

A good changelog entry explains the user-facing or implementer-facing effect.

Bad: > Updated envelope files.

Better: > Clarified that zero-duration envelope stages transition immediately without consuming timeline duration.

Do not add changelog entries for formatting-only edits unless the repository's release process requires them.

Do not claim a version is released unless it has actually been released.

## Definition of done

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

For format additions, the Piccle engine team and implementation agents MUST be able to implement the feature without guessing (see the [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md) for the definition of done).

## Versioning

The document field uses `major.minor`, such as `"piccle": "1.0"`. Repository releases use semantic versions, such as `v1.0.0-rc.1` and `v1.0.0`.

- Major format versions may make breaking document changes.
- Minor format versions may add backward-compatible capabilities implemented by newer Piccle engine releases.
- Patch repository releases may clarify text without changing validation or existing playback meaning.

A published schema URI is immutable. Release preparation must verify that the canonical URI serves the exact tagged schema and record its SHA-256 checksum in the release notes.

## Release process

1. Keep changes under the `Unreleased` changelog section.
2. Run repository validation in a clean checkout.
3. Verify the canonical schema URL.
4. Complete the official engine qualification and listening gates in [Conformance](docs/14-conformance.md).
5. Create an RC tag while any external gate remains open.
6. Move changelog entries to `v1.0.0` only when every stable-release gate is complete.
