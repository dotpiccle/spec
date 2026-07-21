# Examples — agent instructions

This directory contains small, valid Piccle documents demonstrating production-relevant synthesis and DSP configurations. Examples are technical reference assets, not introductory tutorials.

For non-normative technical synthesis configurations, see `docs/12-cookbook.md`. For conformance fixtures (not examples), see `docs/14-conformance.md`. Validate every example with `python3 scripts/validate.py`.

## Examples rules

Every example must:

- Validate against its declared schema version.
- Demonstrate one primary concept or use case.
- Use realistic UI-sound durations and parameter values.
- Isolate one primary synthesis, contour, filter, spatial-effect, or scheduling configuration without unrelated complexity.
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

When adding a public feature, provide the smallest example that exposes its technical behavior and intended UI-audio application.

When changing an existing example's audible behavior, explain why.
