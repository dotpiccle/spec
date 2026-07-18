# Specification docs — agent instructions

## What this file is

This is `docs/AGENTS.md`. It tells AI agents how to write and edit the normative specification documents in this `docs/` directory.

If you are an agent editing a `.md` file in `docs/`, you must follow the rules in this file **in addition to** the rules in the root `AGENTS.md` at the repository root (`piccle-spec/AGENTS.md`). The root file has broader rules that apply to every file in this repository (repository layout, design principles, agent behavior). This file has rules that only apply to `docs/`.

If you are working in `schemas/` instead, read `schemas/AGENTS.md`. If you are working in `test-vectors/`, read `test-vectors/AGENTS.md`.

---

## What "normative" means

- **Normative** = required. A conforming engine MUST follow this rule. A valid document MUST adhere to this constraint.
- **Non-normative** = explanatory. Guidance, examples, notes, and design rationale that help implementers and authors but do not define requirements.

Normative sections must be precise and testable. They include: valid types, required behavior, defaults, units, bounds, error conditions, compatibility behavior.

Non-normative sections (labeled with "Note:" or inside a "Non-normative" subheading) explain intent, common patterns, and design guidance.

Bad (non-normative rule framed as vague requirement):

> Filters should make the sound better.

Good (normative rule):

> A lowpass filter with no `frequencies` contour must pass the input signal unchanged (resonance = 0, cutoff at render_frequency_max).

---

## Single canonical source

Each normative rule, formula, constraint, or field definition MUST live in exactly one `docs/` file — its **canonical home**. Other docs that need to mention it MUST give a brief context-specific note plus a `See docs/XX` reference, not a restatement.

**Why:** Restating a rule in two places guarantees they will drift. When the rule changes, one copy is updated and the other is forgotten, creating a silent contradiction.

**When to reference vs. restate:**

| Scenario                                          | Action                                                         | Example                                                                                         |
| ------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------- |
| You need the full rule                            | Reference: `docs/07-reverb.md` defines the tail-length formula | _"The emitted tail length N is given by the formula in docs/07-reverb.md."_                     |
| Your reader needs context to follow a description | Restate briefly with a link                                    | _"The safety clipper runs after the root master gain (see docs/08-output.md for signal flow)."_ |
| You're writing a field table                      | Include a one-line description and link                        | \*"`tail_ms`                                                                                    | integer | Reverb decay time in milliseconds (see docs/07-reverb.md)."\* |

---

## Documentation style

### Three audiences

Every doc in `docs/` serves three readers:

1. **Engine implementers** — building a Piccle playback engine from scratch. Need precise formulas, default values, signal flow order, error handling rules.
2. **Application developers and sound designers** — authoring Piccle documents. Need field semantics, ranges, defaults, and design guidance.
3. **AI agents generating Piccle documents** — need field structures, valid values, unit conventions, and constraints.

A good doc serves all three without sacrificing precision.

### Writing guidelines

- Use concise sentences. Prefer active voice.
- Define a term before using it.
- Use one term consistently throughout — never switch between "sample rate" and "sampling frequency" or "gain" and "level" for the same concept.
- Avoid marketing language inside normative sections.
- Avoid weasel words: "simple", "obvious", "normal", "reasonable". Replace them with precise rules.
- Use examples after defining behavior, not instead of defining it.
- Include JSON snippets when they materially improve understanding — but keep them correct and verified.
- When referencing any file or directory in this repository, use a Markdown link — never backticks. The reader must be able to click through directly. This applies to spec docs, schemas, test vectors, examples, scripts, and README files alike.

| Do                                                                                                                          | Don't                                                             |
| --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| _"The layer volume envelope applies after serial biquad filters (see [docs/06-filters.md](06-filters.md))."_                | _"See \`docs/06-filters.md\` for details."_                       |
| _"The invalid fixture contract is at [test-vectors/invalid-expectations.json](../test-vectors/invalid-expectations.json)."_ | _"Use `test-vectors/invalid-expectations.json` as the contract."_ |
| _"Clamp instantaneous pitch to [20, render_frequency_max] after cents offset."_                                             | _"Make sure the pitch doesn't go too high."_                      |
| _"At 48 kHz, every integer millisecond is exactly 48 frames."_                                                              | _"48 kHz makes the math nice."_                                   |

### Normative section checklist

When writing a normative section, include:

- Valid types (e.g., "integer in range [0, 9007199254740991]").
- Required behavior ("MUST", "MAY", "MUST NOT").
- Defaults ("When omitted, defaults to X").
- Units ("milliseconds", "Hz", "linear gain").
- Bounds ("MUST be at least 1").
- Error conditions ("An engine MUST reject a document where...").
- Compatibility behavior ("Engines SHOULD accept v1.0 documents").

### Non-normative sections

Use "Note:" or a clearly labeled paragraph for non-normative content:

> **Note:** The exponential curve's rate parameter matches the industry convention for audio fade curves. Applications that render at very low sample rates may observe stair-stepping at the contour midpoint; this is a sample-rate artifact, not a spec defect.

---

## Audio semantic rules

When introducing or changing an audio primitive (oscillator, filter, reverb, envelope, noise source, etc.), define enough behavior for independent engines to produce perceptually equivalent results.

Depending on the feature, document:

- Input and output range.
- Initial state (e.g., "oscillator phase starts at 0").
- Time evolution (e.g., "phase advances by 2π × frequency / sample_rate per frame").
- Curve or interpolation behavior (e.g., "linear, exponential with rate parameter").
- Combination behavior with other nodes or events (e.g., "filters are serial on one layer").
- Clamping or normalization (e.g., "clamp to [20, 20000] after cents offset").
- Channel behavior (e.g., "source is mono through filter and volume, then panned").
- Randomness and seeding (e.g., "PCG32 with the document's seed value").
- Behavior at document boundaries (e.g., "layers end at their declared duration or root cutoff, whichever comes first").
- Whether the feature is required or optional for conforming engines.
- Allowed implementation tolerance (e.g., "±1 sample at 48 kHz" or "match exactly in canonical mode").

Do not require one specific platform API, synthesis library, or DSP implementation. Specify **observable behavior**, not internal architecture.

Bad (requires specific implementation):

> Implement the filter as a direct-form I biquad using the Cookbook formulae.

Good (specifies observable behavior):

> Apply a second-order lowpass filter with the given cutoff and resonance. At canonical mode, the coefficients and response must match the values in `test-vectors/numeric/dsp-values.json`.

---

## How docs/ relates to other directories

When you change a `docs/` file, you may also need to update:

| If you change                   | Also update                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------- |
| A field definition              | `schemas/v1.json` (schema must match docs)                                    |
| A field definition              | Any example in `examples/` that uses the field                                |
| A numerical formula or default  | The corresponding entry in `test-vectors/numeric/dsp-values.json`             |
| A validation rule or constraint | The fixture in `test-vectors/valid/` or `test-vectors/invalid/` that tests it |
| A document-structure rule       | `test-vectors/invalid-expectations.json` if a new error category is added     |
| A field name or unit convention | `docs/02-conventions.md` (the canonical home for conventions)                 |

The repository's `scripts/validate.py` (`piccle-spec/scripts/validate.py`) runs a gate that checks many of these invariants automatically. After editing, run `python3 scripts/validate.py` from the repository root to check for regressions.

---

## Common mistakes to avoid

- **Adding a field to the schema without documenting it in `docs/`.** The schema is not self-documenting; every field needs a normative definition.
- **Adding a default to `docs/` without updating the schema.** The schema's `default` annotation must match the normative default.
- **Restating a formula from another doc.** It will drift. Reference the canonical home instead.
- **Adding implementation-specific requirements.** Piccle is platform-neutral. Do not require a specific audio framework, OS API, or language.
- **Using vague normative language.** "Make it sound good" is not a rule. "The filter must attenuate frequencies above cutoff by at least 12 dB/octave" is a rule.
- **Adding a feature just because another audio format has it.** Every feature must have a demonstrated need in UI micro-audio. See the design principles in the root `AGENTS.md`.
- **Creating speculative abstractions.** Do not refactor the spec's structure to be "more elegant." Only restructure when there is an immediate format need.
