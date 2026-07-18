# Test vectors — agent instructions

This directory contains machine-verifiable conformance fixtures. Test vectors verify; examples teach.

Test vectors live under these subdirectories:

- `valid/` — documents that must pass schema and semantic validation.
- `invalid/` — documents that must fail validation with a specific stage, code, and JSON path.
- `numeric/` — non-PCM DSP numeric aids for implementers.
- `behavior/` — behavior aids for document-level schedules.
- `invalid-expectations.json` — the machine-readable contract for each invalid fixture.

For the normative definition of each fixture category, expected outcomes, and conformance rules, see `docs/14-conformance.md`. For the validation gate and how to run it, see `README.md`.

## Rules

Every invalid fixture must fail for one primary reason. Do not create a fixture containing many unrelated errors unless it specifically tests multi-error reporting.

A valid fixture should state: what behavior it tests, which schema version applies, expected validation result, and expected semantic result when practical.
