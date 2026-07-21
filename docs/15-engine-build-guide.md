# Piccle Engine Implementation Contract

This chapter is the mandatory implementation and qualification contract for [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs). It orders the normative Piccle requirements into executable engineering work. When this chapter and the defining algorithm chapter disagree, stop implementation and resolve the specification inconsistency; do not choose one silently.

## AI and maintainer handoff

An implementation task begins with both repositories in context:

> Implement Piccle v1 in `dotpiccle/engine-rs` for `<target integration>`. Use this repository as the authority for parsing, validation, default resolution, frame scheduling, DSP calculations, state initialization, signal flow, error classification, and qualification.

The implementation agent MUST receive this repository in full, not isolated excerpts. The target request supplies deployment constraints; this repository supplies document validity and engine behavior. The engine repository supplies Rust architecture and platform integration context.

The agent MUST NOT invent a Piccle field, default, DSP stage, timing rule, or validation category. If a normative question cannot be answered from this repository, report it as a specification defect before assigning behavior.

Treat this repository as authoritative. Consume the normative chapters, the bundled [V1 schema](../schemas/v1.json), and the [test vectors](../test-vectors/) as ground truth. Do not use README summaries as substitutes for the linked calculation sections.

## Read before coding

Read the normative chapters in this order:

1. [Document Structure](01-document-structure.md)
2. [Conventions](02-conventions.md)
3. [Engine Safety and Render Profiles](11-engine-safety.md)
4. [Transition Curves](10-curves.md)
5. [Sources](03-sources.md) and [Pitch](04-pitch.md)
6. [Noise and Determinism](09-noise-and-determinism.md)
7. [Filters](06-filters.md) and [Volume](05-layer-volume.md)
8. [Spatial Effects](07-spatial-effects.md) and [Output](08-output.md)
9. [Conformance](14-conformance.md)

Then read [Piccle Engine DSP Runtime](13-implementer-notes.md), which defines the required spatial-effect runtimes, state preparation, and render-loop invariants.

## Calculation ownership index

Use this index before searching prose. Each row points to the single authoritative calculation or behavioral contract.

| Engine concern | Authoritative section |
| --- | --- |
| JSON shape, required fields, defaults, and closed objects | [Document Structure](01-document-structure.md) and [V1 schema](../schemas/v1.json) |
| Validation order and stable failure classes | [Conformance](14-conformance.md) §Validation stages |
| Milliseconds-to-frame conversion and absolute boundaries | [Engine Safety](11-engine-safety.md) §Canonical conformance profile |
| Contour scheduling and interpolation | [Conventions](02-conventions.md) §Contour timing and [Transition Curves](10-curves.md) |
| Oscillator phase and harmonic targets | [Sources](03-sources.md) §Tone generation |
| Pitch evaluation and cents conversion | [Pitch](04-pitch.md) §Processing order |
| Layer gain, fades, and envelope overlap | [Layer Volume](05-layer-volume.md) §Normative timing and overlap behavior |
| Biquad coefficients, state, and update order | [Filters](06-filters.md) §Coefficient equations and state |
| PCG32, noise-character filters, and RMS gains | [Noise and Determinism](09-noise-and-determinism.md) |
| Layer reduction, equal-power balance, master gain, and clipping | [Output](08-output.md) |
| Reverb/echo lifetime, wet contribution, and qualification metrics | [Spatial Effects](07-spatial-effects.md) |
| Reverb/echo delay state and per-frame runtime | [Piccle Engine DSP Runtime](13-implementer-notes.md) |
| Resource preflight, finite-output behavior, and render profiles | [Engine Safety](11-engine-safety.md) |
| Mandatory engine release evidence | [Piccle engine qualification](#piccle-engine-qualification) and [Release Checklist](../RELEASE_CHECKLIST.md) |

## Required engine subsystems

Implement these boundaries separately so each can be tested before complete audio rendering:

### 1. Input and validation

- Decode UTF-8 JSON without losing duplicate member names.
- Bundle the [V1 schema](../schemas/v1.json); validation MUST NOT require network access.
- Reject malformed JSON and duplicate members separately.
- Validate the self-contained Draft 2019-09 schema.
- Run semantic validation for layer IDs, contour budgets, and derived-time bounds.
- Report malformed, schema-invalid, semantically invalid, unsupported, and internal failures as distinct outcomes.

Use [invalid-expectations.json](../test-vectors/invalid-expectations.json) as the validation-stage, stable-code, and JSON-path contract. It maps every fixture in [test-vectors/invalid/](../test-vectors/invalid/) to the stage that MUST reject it, the stable error code, and the JSON path. The Piccle engine validator MUST produce the same stage, code, and path for every invalid fixture.

### 2. Resolved document model

Materialize every normative default into an internal immutable render plan. Preserve document layer order. Compute the exact declared layer ends and explicit or computed document duration using checked integer arithmetic before reserving bounded engine state.

Do not change the source document and do not treat schema `default` annotations as a substitute for the normative defaults.

### 3. Boundary schedule

Build one absolute frame-boundary schedule for the selected render profile. Derive layer starts and ends, contour holds and transitions, fades, the document cutoff, and the spatial-effects output end from that schedule.

Do not round individual durations independently. Use the non-additive 44.1 kHz boundary cases in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json) as ground truth when checking the engine's boundary schedule. This file contains timing values computed from the normative formulas; the Piccle engine frame schedule at 44.1 kHz MUST match them exactly.

### 4. Control evaluators

Implement the five curve functions once and reuse them for pitch, filter frequency, and volume targets. Test first values, zero-frame jumps, exact target boundaries, last-entry remainder, directional fade-in and fade-out values from [the numeric DSP aid](../test-vectors/numeric/dsp-values.json), and root truncation.

For pitch, preserve the specified order: contour interpolation, cents offset, render-profile clamp, then phase integration.

### 5. Mono layer sources

- Implement zero-phase, phase-continuous, band-limited tone oscillators.
- Implement exact PCG32 streaming noise and the three character responses.
- Keep source generation mono through the filter and layer-volume stages.
- Use a bounded-cost production oscillator that satisfies the harmonic, phase, DC, and alias limits in [Sources](03-sources.md). Prepare any oscillator tables before rendering; do not evaluate an unbounded harmonic series in the render loop.

Use the PCG32 stream values and harmonic oscillator coefficients in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json) as ground truth for your noise and oscillator implementations. After those match, implement the complete oscillator DFT measurement described in [Sources](03-sources.md) to verify spectral purity.

### 6. Layer processing

- Apply serial zero-state biquads using the active per-frame cutoff.
- Apply the layer volume envelope and its declared-end fades.
- Convert mono to stereo with equal-power balance.
- Discard layer state at its declared end or an earlier document cutoff.

### 7. Mix and document processing

- Sum layers in the canonical array order without intermediate clipping.
- Apply the whole-document `spatial_effects` array when present.
- Apply root `master_volume_level`.
- Apply the final hard clip exactly once.
- Convert canonical samples to binary32 only after clipping.

Platform sample-rate conversion, hardware channel routing, mono adaptation, and device-volume control remain outside Piccle rendering.

### 8. Reverb effect (inside `spatial_effects`)

Implement the diffused eight-line FDN runtime specified in [Piccle Engine DSP Runtime](13-implementer-notes.md) §Reference reverb runtime. At ~194 ops per output sample and ~34 KiB of state at 500 ms tail (state proportional to `tail_ms`), per-frame work is constant independent of `tail_ms`. The engine MUST pass the strict perceptual-equivalence tolerances defined in [Spatial Effects](07-spatial-effects.md) across the mandatory profile matrix in qualification step 6. A metallic or ringing wet response will fail the echo-density and modal-resonance-floor tolerances.

Test `amount` values `0`, partial wet, and `1`, plus `tail_ms` values `1`, `10`, `20`, `220`, and `500`. Verify the final emitted wet frame is exactly zero. For each canonical tail, render the conformance impulse and assert each tolerance against the published fixture. Matching RT60 alone is insufficient.

### 9. Echo effect (inside `spatial_effects`)

Implement the two-channel lowpass-feedback comb runtime specified in [Piccle Engine DSP Runtime](13-implementer-notes.md) §Reference echo runtime. Derive the repeat count and output length with the bounded iterative binary64 procedure in [Spatial Effects](07-spatial-effects.md) §Echo effect, and apply its automatic terminal window only to the post-document tail.

Test `feedback: 0` as a single filtered repeat, values approaching `1` against the iteration cap and engine resource limits, both balance extremes, and multiple parallel spatial effects without duplicating the dry mix. Match the [canonical echo impulse-response aid](../test-vectors/numeric/echo-impulse-response.json) within its published tolerance.

### 10. Production render path

Keep document preparation separate from audio production. Before rendering begins:

- parse, validate, resolve defaults, and enforce resource limits;
- compile contours into segments with forward-only cursors;
- determine peak voices and reserve a fixed state pool;
- construct or select oscillator tables;
- compute static filter coefficients; and
- prepare and cache reverb normalization for the selected configuration.

During rendering, do not parse JSON, walk the schema, sort events, search contour arrays from the beginning, allocate memory, construct oscillator tables, or measure a reverb impulse response. Rendering may be streamed in bounded blocks; an engine does not need to retain the complete output in memory.

Production steady-state render cost MUST scale with active voices and declared filters. Reverb work per frame MUST remain constant with respect to `tail_ms`; only allocated delay state scales with the tail.

## Implementation-defined integration details

The following details are owned by `dotpiccle/engine-rs` and its platform adapters. They are implementation-defined because they MUST NOT change Piccle semantics or qualification results:

- programming language and public API;
- live, offline, cached, or ahead-of-playback rendering;
- threading and scheduling model;
- buffer and callback sizes;
- supported resource limits;
- additional render profiles and numeric modes;
- hardware output API and downstream channel adaptation.

The engine MUST expose or make testable the canonical 48 kHz stereo binary64 mode. Platform constraints never change whether a Piccle document is valid.

## Piccle engine qualification

The engine release gate MUST execute every step below:

1. **Accept all valid fixtures.** Load every JSON file in [test-vectors/valid/](../test-vectors/valid/) and verify the Piccle engine classifies each as valid before applying profile support limits. Use the directory's [fixture inventory](../test-vectors/valid/README.md); do not hard-code an expected count outside that inventory.

2. **Reject all invalid fixtures.** Load every JSON file in [test-vectors/invalid/](../test-vectors/invalid/) and verify the Piccle engine rejects each at the precise stage, error code, and JSON path declared in [invalid-expectations.json](../test-vectors/invalid-expectations.json). Use the directory's [fixture inventory](../test-vectors/invalid/README.md); do not hard-code an expected count outside that inventory.

3. **Match the DSP reference values.** Recompute every entry in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json) using the engine's own canonical-mode primitives (binary64, 48 kHz). Integer and deterministic arithmetic entries MUST match exactly. The `balance` and `lowpass_1000_hz_48000_resonance_0` fields use `sin`/`cos`, and `fade_values_at_half.fade_in.exponential` and `fade_values_at_half.fade_out.exponential` use `pow`; IEEE-754 does not require these operations to be correctly rounded. Compare each of those fields with `abs(engine − reference) ≤ 8 × ε × max(1, abs(reference))`, where binary64 machine epsilon `ε = 2⁻⁵²`. All other numeric-aid fields MUST match exactly. This bound covers documented cross-libm last-bit variance without weakening the observable DSP contract. The aid is non-normative as format definition but normatively referenced by this gate; see [Conformance](14-conformance.md) §Role of repository fixtures. Apply exact equality to every schedule in [the behavior aid](../test-vectors/behavior/render-cases.json).

4. **Test oscillator spectral purity.** For each oscillator waveform (sine, square, saw, triangle), measure its spectrum at every canonical measurement frequency (`375`, `1000`, `3000`, `8000`, and `16000` Hz) using a 48000-sample rectangular window starting at oscillator frame zero. Verify the amplitude and phase match the DFT reference values in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json).

5. **Test every control surface and filter extreme.** Run the Piccle engine against every curve type (linear, exponential, easeIn, easeOut, easeInOut), every filter type (lowpass, highpass, bandpass), balance extreme (hard-left, center, hard-right), reverb amount value (`0`, partial wet, `1`), short reverb tail (`1`, `10`, `20` ms), seeded-noise boundary case (seed `0` and `4294967295`), simultaneous-boundary layer overlap, and hard root truncation. Use the corresponding fixtures in [test-vectors/valid/](../test-vectors/valid/) as test cases.

6. **Verify spatial-effect output.** The Piccle engine MUST pass all of the following:

   a. **Reverb canonical fixtures** (5 configurations): For each of the 5 canonical reference IR configurations — `(tail_ms, soften_hz, sample_rate)` ∈ `{(1, 4000, 48000), (10, 4000, 48000), (20, 4000, 48000), (220, 4000, 48000), (500, 4000, 48000)}` — feed the qualification impulse through the Piccle engine's reverb entry inside `spatial_effects` in canonical mode, compute the seven perceptual-equivalence metrics from [Spatial Effects](07-spatial-effects.md) §Perceptual-equivalence metric algorithms, and assert each stays within its tolerance against the published fixture in [test-vectors/numeric/reverb-reference-irs/manifest.json](../test-vectors/numeric/reverb-reference-irs/manifest.json). Bit-identical output is not required because platform transcendental variance is explicitly bounded; see [Engine Safety](11-engine-safety.md).

   b. **Echo canonical fixture** (1 configuration): Feed the qualification impulse through the Piccle engine's echo entry inside `spatial_effects` at `delay_ms=200`, `feedback=0.6`, `wet_gain=0.3`, `damp_hz=4000` in canonical mode, and verify the output matches the echo impulse-response vector within `|y_engine[n] − y_ref[n]| ≤ 1e-10 × max(1, |y_ref[n]|)` at every checkpoint frame defined by [Spatial Effects](07-spatial-effects.md) §Echo effect §Conformance bar.

   c. **Parallel-effects fixtures** (2 configurations): Render [reverb then echo](../test-vectors/valid/spatial-effects-reverb-then-echo.json) and [echo then reverb](../test-vectors/valid/spatial-effects-echo-then-reverb.json) in canonical mode. Verify that both orders produce identical output (effects run in parallel, not serial — array order does not affect the result), that each effect receives the same dry mix, and that the output terminates at `frame(D) + max_i(tail_frames_i)`.

   d. **Qualification matrix** (10 configurations): For each entry in [test-vectors/numeric/reverb-qualification-matrix.json](../test-vectors/numeric/reverb-qualification-matrix.json), generate the reference IR on demand by running the normative FDN at the declared `(tail_ms, soften_hz, sample_rate)`, render the qualification impulse through the Piccle engine reverb, compute the seven metrics, and assert each stays within its tolerance. The matrix covers non-canonical configurations including minimum/maximum parameter values, Nyquist clamping, rounding boundaries, and long FFT sizing.

   e. **Matrix construction vector** (1 configuration): Compare your `Q` against the test vector in [test-vectors/numeric/reverb-matrix-vector.json](../test-vectors/numeric/reverb-matrix-vector.json) for `tail_ms=37`, `soften_hz=8000`. PCG32 and the source matrix `A` match exactly. Because Gram-Schmidt normalization uses `sqrt`, compare every `Q[i][j]` with `abs(engine − reference) ≤ 8 × ε × max(1, abs(reference))`, using binary64 `ε = 2⁻⁵²`.

   f. **Additional render profiles**: Treat sample rate separately from discrete numeric-mode and channel/storage choices. For every discrete numeric-mode and channel/storage combination the engine declares, render the 5 canonical document reverb configurations (`tail_ms ∈ {1, 10, 20, 220, 500}`, `soften_hz = 4000`) at each supported rate in `additional_profile_sample_rates` from [the reverb qualification matrix](../test-vectors/numeric/reverb-qualification-matrix.json), generate the reference IR on demand, and assert the seven tolerances. The canonical binary64/stereo combination at 48 kHz is already covered by part (a) and need not be duplicated. Engines with a continuous or large sample-rate range MUST use this representative matrix rather than exhaustively enumerating every accepted integer rate. Engines with a finite declared rate set smaller than the matrix test every declared rate.

   g. **Property-based differential testing**: Using PCG32 with `seed = 0`, sample at least 100 random `(tail_ms, soften_hz, sample_rate)` tuples within the valid ranges defined by the `property_test` section of the qualification matrix. Generate the reference IR for each tuple, render the Piccle engine reverb, and assert all seven tolerances. Record the seed and count in the engine qualification report.

   The complete mandatory set is (a–g). It replaces exhaustive enumeration of document configurations and continuous sample-rate APIs.

7. **Assert finite output and exact output-frame counts.** Compute the document's expected total frame count from `frame(D) + max_i(tail_frames_i)` (where each effect's `tail_frames` is computed in frames from its own parameters — see [Spatial Effects](07-spatial-effects.md) §Output length), then verify the rendered output has exactly that many frames and no non-finite (NaN, infinity) samples.

8. **Render every official example.** Load every JSON file in [examples/](../examples/) in canonical mode. Use the README's [example inventory](../README.md#examples), then complete the listening and platform checks in the [Release Checklist](../RELEASE_CHECKLIST.md). Do not duplicate a fixed example count here.

9. **Profile the production render path.** Run the engine with its maximum supported voices, filters, and reverb tail. Verify that steady rendering performs no memory allocation and has no cost spike when a contour boundary is crossed.

Repository fixture success proves document handling and individual calculations. It does not replace DSP measurements or listening review.

## Definition of done for `dotpiccle/engine-rs`

The implementation is complete only when it provides:

- a parser and validator with distinct failure categories;
- a canonical render entry point;
- all Piccle v1 primitives and defaults;
- deterministic seeded noise;
- the normative signal flow and timelines;
- published engine resource limits;
- automated document, numeric, DSP, and boundary tests;
- rendered official examples; and
- a qualification report listing the tested commit of this specification.

Compiling successfully or producing audible output is not sufficient. Every unchecked normative requirement remains unfinished work.
