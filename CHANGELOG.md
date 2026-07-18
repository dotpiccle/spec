# Changelog

All notable changes to the Piccle specification are documented here. Piccle v1 has not yet reached a stable release.

## Unreleased — targeting v1.0.0-rc.1

### Added

- Canonical 48 kHz stereo render profile with binary64 control calculations, binary32 output samples, half-open timelines, and exact millisecond-to-frame conversion.
- Deterministic PCG32 noise generation and optional unsigned 32-bit `source.seed`, defaulting to `0`.
- Normative oscillator phase, waveform, anti-aliasing, signal-flow, equal-power balance, filter-coefficient, fade, clipping, and reverb-normalization rules.
- Dedicated conformance chapter distinguishing malformed, schema-invalid, semantically invalid, and valid-but-unsupported documents.
- Reproducible repository validator and CI for schema, semantic rules, duplicate JSON members, fixtures, links, formatting, and contract invariants.
- Public contribution, compatibility, and release process.
- Canonical engine conformance and additional render profiles covering browser, desktop, mobile, console, vehicle, kiosk, and embedded implementations.
- Render-profile frequency adaptation down to declared 8 kHz engine profiles.
- Measurable oscillator harmonic, phase, DC, and alias tolerances using coherent canonical-profile windows.
- Normative reverb wet lowpass, energy-decay measurement, and automatic terminal window.
- Exact absolute-boundary scheduling for layers, contours, fades, document cutoffs, and reverb tails at every render rate.
- Agent-oriented engine build guide with subsystem order, target-platform decisions, required evidence, and definition of done.
- Deterministic generated-convolution baseline for a first conforming reverb implementation.
- Stable semantic errors for derived layer-end and output-end safe-integer overflow.
- Parser fixtures and stable errors for non-JSON numeric tokens and decimal values outside finite binary64 range.
- Non-PCM document render cases for computed duration, hard truncation, simultaneous boundaries, fades, and non-additive reverb-tail frame counts.

### Removed

- Removed root `fade_in_ms` and `fade_out_ms`. Fades now belong exclusively to layer volume envelopes; reverb termination is automatic.

### Changed

- Narrowed v1's public scope to finite one-shot UI sounds. Looping, continuous playback, host-controlled parameters, gesture control, theming inputs, and modulation are deferred.
- Replaced fixed noise buffers with duration-independent deterministic streams.
- Defined `soft` as a 400 Hz first-order lowpass and `sharp` as a realizable 2 kHz first-order highpass.
- Defined `tail_ms` consistently as reverb RT60 and emitted-tail duration; removed the contradictory `2 × tail_ms` lifetime rule.
- Replaced broad sample-exactness claims with component-specific determinism and tolerance requirements.
- Replaced the impossible sampled-oscillator peak requirement with band-limited Fourier targets and coherent spectral measurements.
- Defined explicit root duration as a hard cutoff that does not relocate a layer's declared fade.
- Generalized engine behavior from mobile-oriented assumptions to all interactive platforms and declared render rates of 8 kHz or higher.
- Made live, offline, cached, and ahead-of-playback rendering engine choices rather than separate conformance classes.
- Defined pitch processing as contour interpolation, cents offset, render-profile clamp, then phase integration.
- Defined canonical layer accumulation order and the oscillator DFT amplitude and phase measurement convention.
- Clarified that mathematically integral JSON numbers such as `1.0` satisfy integer fields.
- Clarified that engine resource limits affect support, never format validity.
- Reorganized public documentation into normative reference, authoring cookbook, non-normative implementation guidance, and conformance material.

### Fixed

- Fixed broken cross-document links and malformed README navigation.
- Corrected the documented layer `volume` type from “number or array” to “number or object.”
- Synchronized schema defaults, closed-object behavior, metadata constraints, noise semantics, examples, and validation fixtures.
- Defined previously ambiguous filter state, bandpass gain, coefficient update, panning, fade-overlap, truncation, and reverb wet-gain behavior.
- Replaced ambiguous reverb damping and tail-cutoff behavior with an exact wet lowpass, Schroeder energy-decay rule, and zero-valued final wet frame.

### Release gates

- The canonical website and schema URI must resolve and serve the frozen schema.
- A clean-room engine must be implementable from the normative text without unresolved questions.
- Every official example and primitive-coverage asset must pass cross-platform rendering, headphone, full-range, small-speaker, and low-bandwidth listening review.
- Stable `v1.0.0` release notes must record the tagged schema's SHA-256 checksum.
