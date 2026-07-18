# Conformance

This chapter defines the validation and implementation terms used by Piccle.

## Validation stages

A Piccle processor evaluates input in this order:

1. **Input-resource preflight** — enforce published byte-size and nesting limits needed to parse safely.
2. **JSON parsing** — decode UTF-8 RFC 8259 JSON and reject duplicate member names.
3. **Schema validation** — validate the parsed value against the schema named by `piccle` and `$schema`.
4. **Semantic validation** — enforce rules that JSON Schema cannot express directly:
   - layer IDs are unique;
   - pitch and filter contour schedules do not exceed their layer duration;
   - object-form volume schedules, including fades, do not exceed their layer duration.
5. **Render support check** — compare the valid document with the engine's published render-resource limits.

Failure at stage 1 is a **resource-rejected input** whose format validity was not established. Failure at stages 2 through 4 produces an **invalid document**. Failure only at stage 5 produces an **unsupported document**.

## Terms

### Schema-valid document

A parsed JSON value that validates against `schemas/v1.json`. Schema validity alone does not establish Piccle validity because layer-ID uniqueness and contour timing require semantic validation.

### Valid document

A document that passes JSON parsing, schema validation, and semantic validation.

### Invalid document

A document that violates a normative syntax, schema, or semantic requirement. Engines MUST reject invalid documents and MUST NOT attempt partial playback.

### Unsupported document

A valid document that uses more duration, layers, filters, contour points, voices, memory, or another declared resource than a particular engine supports. An engine MUST distinguish this result from invalid input.

### Resource-rejected input

Input whose byte size or nesting exceeds a processor's published safe parsing limits before document validity can be established. The processor MUST NOT label it invalid or valid; it reports that validation was not completed because of a resource limit.

### Conforming validator

A conforming v1 validator:

- implements all three validation stages;
- accepts every fixture in `test-vectors/valid/`;
- rejects every fixture in `test-vectors/invalid/` for its documented primary reason; and
- does not use engine resource limits to change format validity.

### Conforming renderer

A conforming v1 renderer:

- includes a conforming validator;
- implements every v1 source, contour, filter, balance, reverb, output, and safety rule;
- renders valid documents that fall within its published limits;
- reports valid documents beyond those limits as unsupported; and
- meets the determinism class for each component in [Engine Safety and the Canonical Render Profile](11-engine-safety.md).

An engine cannot claim support for only a subset of v1 primitives while describing itself as a conforming v1 renderer. Capacity may vary; feature semantics may not.

## Role of repository fixtures

The checked-in fixtures prove parsing, schema, and semantic-validation behavior. They do not prove audible rendering conformance. Piccle intentionally publishes normative text and formulas rather than normative PCM files or a reference renderer.

Engine authors are responsible for testing their DSP implementation against the formulas and measured tolerances in the normative chapters. The cookbook and official examples are authoring guidance, not audio reference output.
