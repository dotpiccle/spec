# Schemas — agent instructions

This directory contains JSON Schema files for each published Piccle format version. Currently: `v1.json` (self-contained Draft 2019-09, with `$defs` inline).

This file provides schema-authoring guidance for agents editing these files. For contribution workflow (new fields, defaults, constraints), see `CONTRIBUTING.md`. For naming/unit conventions, see `docs/02-conventions.md`.

## Schema rules

All JSON Schemas must be valid for the repository's selected JSON Schema dialect.

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

Descriptions must speak to the person creating audio. That person must not need to know anything about the engine or how it works. The description should tell them what the field does and how to use it.

Engine implementation details (topology, determinism, arithmetic, tolerances, normalization, windowing) belong in `docs/` — never in the schema description.

Bad (engine-focused):

> The wet-path first-order lowpass corner frequency. An engine clamps it to render_frequency_max before coefficient calculation.

Bad (merely restates type):

> A number representing frequency.

Better (author-focused):

> How much to soften the reverb tail. Higher values (up to 12000 Hz) make the space sound warmer; lower values (down to 200 Hz) make it brighter and clearer.
