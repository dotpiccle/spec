# Engine Build Guide

This guide is non-normative. It turns the normative Piccle v1 chapters into an implementation sequence for engine authors and coding agents. When this guide and a normative chapter disagree, the normative chapter wins.

## Intended handoff

An engine task may begin with:

> Here is the Piccle specification. Implement a conforming Piccle v1 engine for `<target platform>` using `<language and integration constraints>`.

The implementation agent should receive this repository in full, not isolated excerpts. The target-platform request supplies deployment constraints; the Piccle repository supplies document validity and audio semantics.

The agent MUST NOT invent a Piccle field, default, DSP stage, timing rule, or validation category. If a normative question cannot be answered from this repository, report it as a specification defect before assigning behavior.

## Read before coding

Read the normative chapters in this order:

1. [Document Structure](01-document-structure.md)
2. [Conventions](02-conventions.md)
3. [Engine Safety and Render Profiles](11-engine-safety.md)
4. [Transition Curves](10-curves.md)
5. [Sources](03-sources.md) and [Pitch](04-pitch.md)
6. [Noise and Determinism](09-noise-and-determinism.md)
7. [Filters](06-filters.md) and [Volume](05-volume.md)
8. [Reverb](07-reverb.md) and [Output](08-output.md)
9. [Conformance](14-conformance.md)

Then read [Implementer Notes](13-implementer-notes.md), including the lightweight baseline reverb recipe and render-loop guidance.

## Required engine subsystems

Implement these boundaries separately so each can be tested before complete audio rendering:

### 1. Input and validation

- Decode UTF-8 JSON without losing duplicate member names.
- Bundle `schemas/v1.json`; validation MUST NOT require network access.
- Reject malformed JSON and duplicate members separately.
- Validate the self-contained Draft 2019-09 schema.
- Run semantic validation for layer IDs, contour budgets, and derived-time bounds.
- Report malformed, schema-invalid, semantically invalid, unsupported, and internal failures as distinct outcomes.

Use `test-vectors/invalid-expectations.json` as the expected validation stage, stable code, and JSON path contract.

### 2. Resolved document model

Materialize every normative default into an internal immutable render plan. Preserve document layer order. Compute the exact declared layer ends and explicit or computed document duration using checked integer arithmetic before reserving bounded engine state.

Do not change the source document and do not treat schema `default` annotations as a substitute for the normative defaults.

### 3. Boundary schedule

Build one absolute frame-boundary schedule for the selected render profile. Derive layer starts and ends, contour holds and transitions, fades, the document cutoff, and the reverb output end from that schedule.

Do not round individual durations independently. Verify the non-additive 44.1 kHz cases in `test-vectors/numeric/dsp-values.json` before implementing DSP.

### 4. Control evaluators

Implement the five curve functions once and reuse them for pitch, filter frequency, and volume targets. Test first values, zero-frame jumps, exact target boundaries, last-entry remainder, and root truncation.

For pitch, preserve the specified order: contour interpolation, cents offset, render-profile clamp, then phase integration.

### 5. Mono layer sources

- Implement zero-phase, phase-continuous, band-limited tone oscillators.
- Implement exact PCG32 streaming noise and the three character responses.
- Keep source generation mono through the filter and layer-volume stages.
- Use a band-limited wavetable, polyBLEP, or an equivalent bounded-cost oscillator in the production render path. Do not evaluate the full reference harmonic series for every output sample.

Use the numeric aids for PCG32 and harmonic coefficients, then implement the complete oscillator DFT measurement from [Sources](03-sources.md).

### 6. Layer processing

- Apply serial zero-state biquads using the active per-frame cutoff.
- Apply the layer volume envelope and its declared-end fades.
- Convert mono to stereo with equal-power balance.
- Discard layer state at its declared end or an earlier document cutoff.

### 7. Mix and document processing

- Sum layers in the canonical array order without intermediate clipping.
- Apply the whole-document reverb when present.
- Apply root volume.
- Apply the final hard clip exactly once.
- Convert canonical samples to binary32 only after clipping.

Platform sample-rate conversion, hardware channel routing, mono adaptation, and device-volume control remain outside Piccle rendering.

### 8. Reverb

Use the diffused eight-line FDN baseline in [Implementer Notes](13-implementer-notes.md) for a first implementation. It targets the dense onset and smooth decay of the convolution baseline while performing constant work per output frame with bounded circular-delay storage. A different topology is acceptable only after its final softened, windowed, and normalized wet response passes every measurement in [Reverb](07-reverb.md) and receives the same perceptual qualification.

Test `amount` values `0`, partial wet, and `1`, plus `tail_ms` values `1`, `10`, `20`, `220`, and `500`. Verify the final emitted wet frame is exactly zero. A/B the baseline at `20`, `220`, and `500` ms as described in Implementer Notes; matching RT60 alone is insufficient.

### 9. Production render path

Keep document preparation separate from audio production. Before rendering begins:

- parse, validate, resolve defaults, and enforce resource limits;
- compile contours into segments with forward-only cursors;
- determine peak voices and reserve a fixed state pool;
- construct or select oscillator tables;
- compute static filter coefficients; and
- prepare and cache reverb normalization for the selected configuration.

During rendering, do not parse JSON, walk the schema, sort events, search contour arrays from the beginning, allocate memory, construct oscillator tables, or measure a reverb impulse response. Rendering may be streamed in bounded blocks; an engine does not need to retain the complete output in memory.

For a lightweight engine, steady render cost should scale with active voices and their declared filters. Reverb should add constant work per frame rather than work proportional to `tail_ms`.

## Target-platform decisions

The engine may choose these integration details without changing Piccle semantics:

- programming language and public API;
- live, offline, cached, or ahead-of-playback rendering;
- threading and scheduling model;
- buffer and callback sizes;
- supported resource limits;
- additional render profiles and numeric modes;
- hardware output API and downstream channel adaptation.

The engine must still expose or make testable the canonical 48 kHz stereo binary64 mode. Platform constraints never change whether a Piccle document is valid.

## Required verification

Before calling the implementation conforming:

1. Run `python3 scripts/validate.py` in this repository.
2. Classify every valid fixture as valid before applying engine support limits, and render every official example in canonical mode.
3. Reject every invalid fixture at its declared stage, code, and path.
4. Recompute every value in `test-vectors/numeric/dsp-values.json` and every schedule in `test-vectors/behavior/render-cases.json` independently in the engine test suite.
5. Test every oscillator at every canonical measurement frequency.
6. Test every curve, filter type, balance extreme, reverb amount, short tail, seeded-noise boundary, simultaneous boundary, and hard truncation case.
7. Assert finite output and exact output-frame counts.
8. Render every official example and complete the listening and platform checks in `RELEASE_CHECKLIST.md`.
9. Profile the production render path with the engine's maximum supported voices, filters, and reverb tail. Verify that steady rendering performs no memory allocation and has no cost spike when a contour boundary is crossed.

Repository fixture success proves document handling and individual calculations. It does not replace DSP measurements or listening review.

## Definition of done for an agent-built engine

The implementation is complete only when it provides:

- a parser and validator with distinct failure categories;
- a canonical render entry point;
- all Piccle v1 primitives and defaults;
- deterministic seeded noise;
- the normative signal flow and timelines;
- published engine resource limits;
- automated document, numeric, DSP, and boundary tests;
- rendered official examples; and
- a short conformance report listing the tested commit of this specification.

Compiling successfully or producing audible output is not sufficient. Every unchecked normative requirement remains unfinished work.
