# Specification style — agent instructions

This file provides guidance for agents writing or editing the normative specification in this `docs/` directory. It lives here (rather than in the root `AGENTS.md`) because it targets spec-writing agents specifically, not every agent that lands in the repository.

## Single canonical source

Each normative rule, formula, constraint, or field definition MUST live in exactly one doc — its **canonical home**. Other docs that need to mention it MUST give a brief context-specific note plus a `See docs/XX` reference, not a restatement.

Why: restating a rule in two places guarantees they will drift. When the rule changes, one copy is updated and the other is forgotten, creating a silent contradiction.

When to reference vs. restate:

- **Reference**: the rule itself, the formula, the constraint, the default value, the behavior description.
- **Restate (briefly)**: only what the reader needs to understand the current doc's context — e.g., "the safety clipper runs at this signal-flow stage" without restating the full normative requirement.

Field tables are an exception: a table may include a brief one-line description of each field even if the full definition lives elsewhere, provided the table entry links to the canonical doc.

## Documentation style

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
- Avoid words such as "simple," "obvious," "normal," or "reasonable" when they replace a precise rule.
- Use examples after defining behavior, not instead of defining it.
- Include JSON snippets when they materially improve understanding.

## Audio semantic rules

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
