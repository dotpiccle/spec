# Engine Build Guide

This guide is non-normative. It turns the normative Piccle chapters into an implementation sequence for anyone building a Piccle engine — whether Piccle's own reference engine team or an independent implementer. When this guide and a normative chapter disagree, the normative chapter wins.

## Intended handoff

If you are building a Piccle engine — for a new target platform, language, or integration — a typical task begins with:

> Implement a conforming Piccle engine for `<target platform>` using `<language and integration constraints>`.

The implementation agent should receive this repository in full, not isolated excerpts. The target-platform request supplies deployment constraints; the Piccle repository supplies document validity and audio semantics.

The agent MUST NOT invent a Piccle field, default, DSP stage, timing rule, or validation category. If a normative question cannot be answered from this repository, report it as a specification defect before assigning behavior.

Treat this repository as authoritative. Consume the normative chapters, `schemas/v1.json`, and `test-vectors/*.json` as ground truth.

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

Then read [Implementer Notes](13-implementer-notes.md), including the normative reverb runtime and render-loop guidance.

## Required engine subsystems

Implement these boundaries separately so each can be tested before complete audio rendering:

### 1. Input and validation

- Decode UTF-8 JSON without losing duplicate member names.
- Bundle `schemas/v1.json`; validation MUST NOT require network access.
- Reject malformed JSON and duplicate members separately.
- Validate the self-contained Draft 2019-09 schema.
- Run semantic validation for layer IDs, contour budgets, and derived-time bounds.
- Report malformed, schema-invalid, semantically invalid, unsupported, and internal failures as distinct outcomes.

Use the file `test-vectors/invalid-expectations.json` (in the repository root) as the expected validation stage, stable code, and JSON path contract. This file maps each fixture in `test-vectors/invalid/` (63 JSON documents that must fail validation) to its expected outcome: the validation stage that must reject it (malformed, schema-invalid, or semantic), the stable error code, and the JSON path where the error is reported. Your engine's validator must produce the same stage, code, and path for every invalid fixture.

### 2. Resolved document model

Materialize every normative default into an internal immutable render plan. Preserve document layer order. Compute the exact declared layer ends and explicit or computed document duration using checked integer arithmetic before reserving bounded engine state.

Do not change the source document and do not treat schema `default` annotations as a substitute for the normative defaults.

### 3. Boundary schedule

Build one absolute frame-boundary schedule for the selected render profile. Derive layer starts and ends, contour holds and transitions, fades, the document cutoff, and the spatial-effects output end from that schedule.

Do not round individual durations independently. Use the non-additive 44.1 kHz boundary cases in `test-vectors/numeric/dsp-values.json` (at `piccle-spec/test-vectors/numeric/dsp-values.json` in this repository) as ground truth when checking the engine's own boundary schedule. This file contains reference timing values computed from the spec's formulas; your engine's frame schedule at 44.1 kHz must match them exactly.

### 4. Control evaluators

Implement the five curve functions once and reuse them for pitch, filter frequency, and volume targets. Test first values, zero-frame jumps, exact target boundaries, last-entry remainder, and root truncation.

For pitch, preserve the specified order: contour interpolation, cents offset, render-profile clamp, then phase integration.

### 5. Mono layer sources

- Implement zero-phase, phase-continuous, band-limited tone oscillators.
- Implement exact PCG32 streaming noise and the three character responses.
- Keep source generation mono through the filter and layer-volume stages.
- Use a band-limited wavetable, polyBLEP, or an equivalent bounded-cost oscillator in the production render path. Do not evaluate the full reference harmonic series for every output sample.

Use the PCG32 stream values and harmonic oscillator coefficients in `test-vectors/numeric/dsp-values.json` (at `piccle-spec/test-vectors/numeric/dsp-values.json` in this repository) as ground truth for your noise and oscillator implementations. After those match, implement the complete oscillator DFT measurement described in [Sources](03-sources.md) to verify spectral purity.

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

Implement the diffused eight-line FDN runtime specified in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime. At ~194 ops per output sample and ~34 KiB of state at 500 ms tail (state proportional to `tail_ms`), per-frame work is constant independent of `tail_ms`. The engine MUST pass the strict perceptual-equivalence tolerances defined in [Spatial Effects](07-spatial-effects.md) across the mandatory profile matrix in conformance step 6. A metallic or ringing wet response will fail the echo-density and modal-resonance-floor tolerances.

Test `amount` values `0`, partial wet, and `1`, plus `tail_ms` values `1`, `10`, `20`, `220`, and `500`. Verify the final emitted wet frame is exactly zero. For each canonical tail, render the conformance impulse and assert each tolerance against the published fixture. Matching RT60 alone is insufficient.

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

## Engine conformance verification

These steps verify the engine against this specification. Before calling the implementation conforming:

1. **Accept all valid fixtures.** Load every `.json` file in `test-vectors/valid/` (38 documents covering defaults, boundaries, reverb tails, noise determinism, filter sweeps, spatial effects, etc.) and verify your engine classifies each as valid — before applying any engine-specific support limits. The valid fixture inventory is documented at `test-vectors/valid/README.md`.

2. **Reject all invalid fixtures.** Load every `.json` file in `test-vectors/invalid/` (64 documents, each designed to fail for exactly one reason) and verify your engine rejects each at the precise stage (malformed, schema-invalid, or semantic), error code, and JSON path declared in `test-vectors/invalid-expectations.json`. The invalid fixture inventory is documented at `test-vectors/invalid/README.md`.

3. **Match the DSP reference values.** Recompute every entry in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json) using the engine's own canonical-mode primitives (binary64, 48 kHz). Integer and deterministic arithmetic entries MUST match exactly. The `balance` and `lowpass_1000_hz_48000_resonance_0` fields use `sin`/`cos`, which IEEE-754 does not require to be correctly rounded; compare each of those fields with `abs(engine − reference) ≤ 8 × ε × max(1, abs(reference))`, where binary64 machine epsilon `ε = 2⁻⁵²`. This bound covers documented cross-libm last-bit variance without weakening the observable DSP contract. The aid is non-normative as format definition but normatively referenced by this gate; see [Conformance](14-conformance.md) §Role of repository fixtures. Apply exact equality to every schedule in [the behavior aid](../test-vectors/behavior/render-cases.json).

4. **Test oscillator spectral purity.** For each oscillator waveform (sine, square, saw, triangle), measure its spectrum at every canonical measurement frequency (`375`, `1000`, `3000`, `8000`, and `16000` Hz) using a 48000-sample rectangular window starting at oscillator frame zero. Verify the amplitude and phase match the DFT reference values in `test-vectors/numeric/dsp-values.json`.

5. **Test every control surface and filter extreme.** Run your engine against every curve type (linear, exponential, easeIn, easeOut, easeInOut), every filter type (lowpass, highpass, bandpass), balance extremes (hard-left, center, hard-right), reverb amount values (`0`, partial wet, `1`), short reverb tails (`1`, `10`, `20` ms), seeded-noise boundary cases (seed `0` and `4294967295`), simultaneous-boundary layer overlaps, and hard root-truncation. Use the corresponding valid fixtures in `test-vectors/valid/` as test cases.

6. **Verify reverb and echo cross-engine equivalence.** A conforming engine MUST pass all of the following:

   a. **Reverb canonical fixtures** (5 configurations): For each of the 5 canonical reference IR configurations — `(tail_ms, soften_hz, sample_rate)` ∈ `{(1, 4000, 48000), (10, 4000, 48000), (20, 4000, 48000), (220, 4000, 48000), (500, 4000, 48000)}` — feed the conformance impulse through your engine's reverb entry inside `spatial_effects` in canonical mode, compute the seven perceptual-equivalence metrics from [Spatial Effects](07-spatial-effects.md) §Perceptual-equivalence metric algorithms, and assert each stays within its tolerance against the published fixture in [test-vectors/numeric/reverb-reference-irs/manifest.json](../test-vectors/numeric/reverb-reference-irs/manifest.json). Bit-identical output is not required (platform transcendental variance; see [Engine Safety](11-engine-safety.md)).

   b. **Echo canonical fixtures** (1 configuration): Feed the conformance impulse through your engine's echo entry inside `spatial_effects` at `delay_ms=200`, `feedback=0.6`, `wet_gain=0.3`, `damp_hz=4000` in canonical mode, and verify the output matches the reference fixture in the echo impulse-response test vector within the numerical tolerance defined in [Spatial Effects](07-spatial-effects.md) §Echo effect §Conformance bar (`|y_engine[n] − y_ref[n]| ≤ 1e-10 × max(1, |y_ref[n]|)` for each checkpoint frame).

   c. **Parallel-effects fixtures** (2 configurations): Render `test-vectors/valid/spatial-effects-reverb-then-echo.json` and `test-vectors/valid/spatial-effects-echo-then-reverb.json` in canonical mode. Verify that both orders produce identical output (effects run in parallel, not serial — array order does not affect the result), that each effect receives the same dry mix, and that the output terminates at `frame(D) + max_i(tail_frames_i)`.

   d. **Qualification matrix** (10 configurations): For each entry in [test-vectors/numeric/reverb-qualification-matrix.json](../test-vectors/numeric/reverb-qualification-matrix.json), generate the reference IR on demand by running the normative FDN at the declared `(tail_ms, soften_hz, sample_rate)`, render the conformance impulse through your engine's reverb, compute the seven metrics, and assert each stays within its tolerance. The matrix covers non-canonical configurations including minimum/maximum parameter values, Nyquist clamping, rounding boundaries, and long FFT sizing.

   e. **Matrix construction vector** (1 configuration): Compare your `Q` against the test vector in [test-vectors/numeric/reverb-matrix-vector.json](../test-vectors/numeric/reverb-matrix-vector.json) for `tail_ms=37`, `soften_hz=8000`. PCG32 and the source matrix `A` match exactly. Because Gram-Schmidt normalization uses `sqrt`, compare every `Q[i][j]` with `abs(engine − reference) ≤ 8 × ε × max(1, abs(reference))`, using binary64 `ε = 2⁻⁵²`.

   f. **Additional render profiles**: Treat sample rate separately from discrete numeric-mode and channel/storage choices. For every discrete numeric-mode and channel/storage combination the engine declares, render the 5 canonical document reverb configurations (`tail_ms ∈ {1, 10, 20, 220, 500}`, `soften_hz = 4000`) at each supported rate in `additional_profile_sample_rates` from [the reverb qualification matrix](../test-vectors/numeric/reverb-qualification-matrix.json), generate the reference IR on demand, and assert the seven tolerances. The canonical binary64/stereo combination at 48 kHz is already covered by part (a) and need not be duplicated. Engines with a continuous or large sample-rate range MUST use this representative matrix rather than exhaustively enumerating every accepted integer rate. Engines with a finite declared rate set smaller than the matrix test every declared rate.

   g. **Property-based differential testing (SHOULD)**: Using PCG32 with an engine-chosen seed, sample at least 100 random `(tail_ms, soften_hz, sample_rate)` tuples within the valid ranges (see the `property_test` section of the qualification matrix file), generate the reference IR for each, render through your engine's reverb, and assert the seven tolerances. The seed and count SHOULD be documented in the engine's release notes. These results are informative and do not affect conformance.

   This finite mandatory set (a–f) plus the recommended property-based pass (g) replaces exhaustive enumeration of document configurations and continuous sample-rate APIs. An engine that passes (a–f) can honestly claim reverb and echo qualification for its declared render profiles.

7. **Assert finite output and exact output-frame counts.** Compute the document's expected total frame count from `frame(D) + max_i(tail_frames_i)` (where each effect's `tail_frames` is computed in frames from its own parameters — see [Spatial Effects](07-spatial-effects.md) §Output length), then verify the rendered output has exactly that many frames and no non-finite (NaN, infinity) samples.

8. **Render every official example.** Load each of the 15 `.json` files in `examples/` (`button-click.json`, `toggle-on.json`, `toggle-off.json`, `success.json`, `error.json`, `notification.json`, `transition.json`, `sparkle.json`, `droplet.json`, `bloom.json`, `loading.json`, `ready.json`, `whisper.json`, `page.json`, `echo.json`) in canonical mode. Complete the listening and platform checks in `RELEASE_CHECKLIST.md`.

9. **Profile the production render path.** Run the engine with its maximum supported voices, filters, and reverb tail. Verify that steady rendering performs no memory allocation and has no cost spike when a contour boundary is crossed.

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
