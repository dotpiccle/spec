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
8. [Reverb](07-reverb.md) and [Output](08-output.md)
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

Use the file `test-vectors/invalid-expectations.json` (in the repository root) as the expected validation stage, stable code, and JSON path contract. This file maps each fixture in `test-vectors/invalid/` (54 JSON documents that must fail validation) to its expected outcome: the validation stage that must reject it (malformed, schema-invalid, or semantic), the stable error code, and the JSON path where the error is reported. Your engine's validator must produce the same stage, code, and path for every invalid fixture.

### 2. Resolved document model

Materialize every normative default into an internal immutable render plan. Preserve document layer order. Compute the exact declared layer ends and explicit or computed document duration using checked integer arithmetic before reserving bounded engine state.

Do not change the source document and do not treat schema `default` annotations as a substitute for the normative defaults.

### 3. Boundary schedule

Build one absolute frame-boundary schedule for the selected render profile. Derive layer starts and ends, contour holds and transitions, fades, the document cutoff, and the reverb output end from that schedule.

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
- Apply the whole-document reverb when present.
- Apply root `master_volume_level`.
- Apply the final hard clip exactly once.
- Convert canonical samples to binary32 only after clipping.

Platform sample-rate conversion, hardware channel routing, mono adaptation, and device-volume control remain outside Piccle rendering.

### 8. Reverb

Implement the diffused eight-line FDN runtime specified in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime. At ~194 ops per output sample and ~34 KiB of state at 500 ms tail (state proportional to `tail_ms`), per-frame work is constant independent of `tail_ms`. The engine MUST pass the strict perceptual-equivalence tolerances defined in [Reverb](07-reverb.md) at every declared render profile. A metallic or ringing wet response will fail the echo-density and modal-resonance-floor tolerances.

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

1. **Accept all valid fixtures.** Load every `.json` file in `test-vectors/valid/` (38 documents covering defaults, boundaries, reverb tails, noise determinism, filter sweeps, etc.) and verify your engine classifies each as valid — before applying any engine-specific support limits. The valid fixture inventory is documented at `test-vectors/valid/README.md`.

2. **Reject all invalid fixtures.** Load every `.json` file in `test-vectors/invalid/` (54 documents, each designed to fail for exactly one reason) and verify your engine rejects each at the precise stage (malformed, schema-invalid, or semantic), error code, and JSON path declared in `test-vectors/invalid-expectations.json`. The invalid fixture inventory is documented at `test-vectors/invalid/README.md`.

3. **Match the DSP reference values.** For every entry in `test-vectors/numeric/dsp-values.json` — which contains pre-computed PCG32 noise streams, oscillator Fourier coefficients, biquad filter coefficients at 48 kHz, reverb baseline delay-line lengths, balance stereo gains, frame-boundary schedules at 44.1 kHz, and other non-audio (non-PCM) reference numbers — recompute the same value using your engine's own primitives in canonical mode (binary64, 48 kHz) and assert exact equality against the JSON data. All entries are deterministic across platforms (integers, `sqrt`-derived values, and arithmetic on constants). The single exception is `lowpass_1000_hz_48000_resonance_0`, whose coefficients are derived from `sin`/`cos`; IEEE-754 does not require these to be correctly-rounded, so engines on different platforms may see last-bit differences (typically 1-4 ULP). Do not assert exact equality for this entry — verify your filter implementation via step 4 (spectral purity) instead. These fixtures are non-normative as format definition but normatively referenced by this gate; see [Conformance](14-conformance.md) §Role of repository fixtures. Do the same for every render-case schedule in `test-vectors/behavior/render-cases.json`.

4. **Test oscillator spectral purity.** For each oscillator waveform (sine, square, saw, triangle), measure its spectrum at every canonical measurement frequency (`375`, `1000`, `3000`, `8000`, and `16000` Hz) using a 48000-sample rectangular window starting at oscillator frame zero. Verify the amplitude and phase match the DFT reference values in `test-vectors/numeric/dsp-values.json`.

5. **Test every control surface and filter extreme.** Run your engine against every curve type (linear, exponential, easeIn, easeOut, easeInOut), every filter type (lowpass, highpass, bandpass), balance extremes (hard-left, center, hard-right), reverb amount values (`0`, partial wet, `1`), short reverb tails (`1`, `10`, `20` ms), seeded-noise boundary cases (seed `0` and `4294967295`), simultaneous-boundary layer overlaps, and hard root-truncation. Use the corresponding valid fixtures in `test-vectors/valid/` as test cases.

6. **Verify reverb cross-engine equivalence.** For each declared reverb configuration your engine supports:
     - **For the 5 canonical configurations** (tails 1, 10, 20, 220, and 500 ms at 48 kHz with 4 kHz soften): compare against the published reference IR fixtures in `test-vectors/numeric/reverb-reference-irs/manifest.json`.
      - **For all other configurations** (non-canonical `tail_ms`, `soften_hz`, or `sample_rate` values): generate the reference IR on demand by running the normative FDN (see [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime) at the declared configuration with the normative seed function, following the conformance-harness procedure in [Reverb](07-reverb.md). The reference generator script at [scripts/generate_reverb_reference_irs.py](../scripts/generate_reverb_reference_irs.py) implements this algorithm.
     - To verify your matrix construction independently, compare your `Q` against the test vector in [test-vectors/numeric/reverb-matrix-vector.json](../test-vectors/numeric/reverb-matrix-vector.json) for the configuration `tail_ms=37`, `soften_hz=8000`. The vector includes the seed, PCG32 outputs, source matrix, and resulting Q.

   For each canonical fixture, feed the conformance impulse (one frame at `L=R=sqrt(0.5)` followed by zeroes) through your engine's reverb in canonical mode and:

    - Compute the seven perceptual-equivalence metrics from `docs/07-reverb.md` §Perceptual-equivalence metric algorithms on your FDN's wet output and assert each stays within its tolerance against the reference fixture. Each metric has a normatively pinned algorithm with precise formulas and degenerate-case handling; the published baseline values per canonical fixture are in `manifest.json` under the `metrics` key on each fixture entry. Bit-identical output to the fixture is not required: the reverb configuration constants depend on platform transcendentals, which Piccle does not require to be correctly-rounded across processors.
    - As a non-normative stronger check, engines whose platform `libm` matches the fixture's MAY also assert bit-identical output. This is a convenience test, not a conformance requirement.

    Then, for each additional declared render profile (other sample rates, binary32 production mode, etc.), render the same conformance impulse through your engine's reverb and assert the same seven perceptual-equivalence tolerances.

    This single test replaces the earlier loose "comparable" gate. The full A/B listening review in RELEASE_CHECKLIST.md remains a separate release gate; the metric-based bar catches the common failure modes (metallic ringing, discrete echoes, wrong loudness, wrong stereo decorrelation) algorithmically.

7. **Assert finite output and exact output-frame counts.** Compute the document's expected total frame count from `frame(duration_ms + reverb.tail_ms)` using the engine's own frame formula, then verify the rendered output has exactly that many frames and no non-finite (NaN, infinity) samples.

8. **Render every official example.** Load each of the 14 `.json` files in `examples/` (`button-click.json`, `toggle-on.json`, `toggle-off.json`, `success.json`, `error.json`, `notification.json`, `transition.json`, `sparkle.json`, `droplet.json`, `bloom.json`, `loading.json`, `ready.json`, `whisper.json`, `page.json`) in canonical mode. Complete the listening and platform checks in `RELEASE_CHECKLIST.md`.

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
