# Conformance

This chapter defines validation and engine-conformance terms used by Piccle.

## Validation stages

A Piccle processor evaluates input in this order:

1. **Input-resource preflight** — enforce published byte-size and nesting limits needed to parse safely.
2. **JSON parsing** — decode UTF-8 RFC 8259 JSON and reject duplicate member names.
3. **Schema validation** — validate the parsed value against the schema named by `piccle` and `$schema`.
4. **Semantic validation** — enforce rules that JSON Schema cannot express directly:
   - layer IDs are unique;
   - pitch and filter contour schedules do not exceed their declared layer duration;
   - object-form layer-volume schedules, including fades, do not exceed their declared layer duration;
   - every `start_ms + duration_ms` layer end remains within the safe-integer bound; and
   - the document duration plus the longest spatial effect's effective tail length remains within the safe-integer bound.
5. **Engine support check** — compare the valid document with the engine's published resource and output-bandwidth limits.

Failure at stage 1 is a resource-rejected input whose format validity was not established. Failure at stages 2 through 4 produces an invalid document. Failure only at stage 5 produces an unsupported document.

## Document terms

### Schema-valid document

A parsed JSON value that validates against `schemas/v1.json`. Schema validity alone does not establish Piccle validity because layer-ID uniqueness and contour timing require semantic validation.

### Valid document

A document that passes JSON parsing, schema validation, and semantic validation.

### Invalid document

A document that violates a normative syntax, schema, or semantic requirement. Engines MUST reject invalid documents and MUST NOT attempt partial rendering.

### Unsupported document

A valid document that exceeds an engine's published duration, layers, filters, contour points, voices, memory, CPU, output bandwidth, or another render limit. An engine MUST distinguish this result from invalid input.

### Resource-rejected input

Input whose byte size or nesting exceeds a processor's published safe parsing limits before document validity can be established. The processor MUST NOT label it invalid or valid; it reports that validation was not completed because of a resource limit.

## Engine conformance

A conforming v1 engine:

- performs JSON parsing, schema validation, and semantic validation;
- classifies every fixture in `test-vectors/valid/` as valid through semantic validation, before the engine support check;
- rejects every fixture in `test-vectors/invalid/` for its documented primary stage, code, and location;
- does not use engine limits to change format validity;
- provides the canonical 48 kHz stereo binary64 test mode;
- renders every document in `examples/` in canonical mode rather than reporting it unsupported;
- implements every v1 source, contour, filter, balance, reverb, echo, output, and safety rule; and
- meets each canonical determinism or tolerance requirement, including the reverb perceptual-equivalence tolerances in [Spatial Effects](07-spatial-effects.md) measured against the canonical reference IR fixtures in [test-vectors/numeric/reverb-reference-irs/](../test-vectors/numeric/reverb-reference-irs/);

The machine-readable expected stage, stable code, and JSON path for each invalid fixture are declared in `test-vectors/invalid-expectations.json`.

An engine MAY expose additional render profiles with different sample rates, numeric modes, output bandwidth, and resource limits as defined in [Engine Safety](11-engine-safety.md).

A valid fixture may be reported unsupported after it has been classified as valid when it intentionally exceeds published render limits. The `engine-limit-independent`, long-duration, and many-layer fixtures exercise this distinction. Parser byte-size and nesting limits used for conformance testing MUST be sufficient to parse every checked-in fixture.

Whether the engine renders live, offline, ahead of playback, into a cache, or through another architecture is outside the Piccle format contract. These strategies do not create separate conformance classes.

## Platform adaptation

Piccle rendering ends with clipped stereo samples. Sample-rate conversion, stereo-to-mono downmixing, hardware routing, operating-system volume, and device processing occur afterward and are not part of asset semantics. No operating-system API, threading model, filesystem, network access, or hardware architecture is normative.

## Role of repository fixtures

Checked-in document fixtures prove parsing, schema, and semantic-validation behavior. Non-PCM numeric aids help implementers check individual formulas, and behavior aids check document-level schedules. None of these categories proves audible rendering conformance.

Piccle intentionally publishes normative text and formulas rather than normative PCM files or an embedded engine. Piccle's reference engine and any independent engine must be tested against the formulas, measurements, cross-platform qualification matrix, and listening gates in this repository.

The numeric and behavior aids ([DSP values](../test-vectors/numeric/dsp-values.json), [render cases](../test-vectors/behavior/render-cases.json), [reverb reference IR fixtures](../test-vectors/numeric/reverb-reference-irs/), [the reverb matrix test vector](../test-vectors/numeric/reverb-matrix-vector.json), and the echo impulse-response test vector) are **non-normative as format definition**: they are derivable from the formulas in this specification and can be regenerated from them. However, they are **normatively referenced** by the conformance gates in [Engine Build Guide](15-engine-build-guide.md). A conforming engine MUST reproduce deterministic canonical-mode values exactly and MUST use the explicitly published tolerance for fields subject to permitted transcendental variance (see [Engine Safety](11-engine-safety.md)). If an aid disagrees with the formulas in [the normative documents](./), the formulas are authoritative; the aid is corrected in place; and engines must then match the corrected aid. The repository validator recomputes every numeric aid with the same exact-or-tolerant classification, so drift is caught mechanically.
