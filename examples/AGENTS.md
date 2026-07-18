# Examples — agent instructions

This directory contains small, polished, valid Piccle documents demonstrating real use cases. Examples are part of the public developer experience — keep them intentional and production-relevant.

For the task-oriented authoring guide, see `docs/12-cookbook.md`. For conformance fixtures (not examples), see `docs/14-conformance.md`. Validate every example with `python3 scripts/validate.py`.

## Examples rules

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

When changing an existing example's audible behavior, explain why.
