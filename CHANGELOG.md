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

### Changed

- Narrowed v1's public scope to finite one-shot UI sounds. Looping, continuous playback, runtime parameters, gesture control, theming inputs, and modulation are deferred.
- Replaced fixed noise buffers with duration-independent deterministic streams.
- Defined `soft` as a 400 Hz first-order lowpass and `sharp` as a realizable 2 kHz first-order highpass.
- Defined `tail_ms` consistently as reverb RT60 and emitted-tail duration; removed the contradictory `2 × tail_ms` lifetime rule.
- Replaced broad sample-exactness claims with component-specific determinism and tolerance requirements.
- Clarified that engine resource limits affect support, never format validity.
- Reorganized public documentation into normative reference, authoring cookbook, non-normative implementation guidance, and conformance material.

### Fixed

- Fixed broken cross-document links and malformed README navigation.
- Corrected the documented layer `volume` type from “number or array” to “number or object.”
- Synchronized schema defaults, closed-object behavior, metadata constraints, noise semantics, examples, and validation fixtures.
- Defined previously ambiguous filter state, bandpass gain, coefficient update, panning, fade-overlap, truncation, and reverb wet-gain behavior.

### Release gates

- The canonical website and schema URI must resolve and serve the frozen schema.
- A clean-room renderer must be implementable from the normative text without unresolved questions.
- Every official example must pass headphone and phone-speaker listening review.
- Stable `v1.0.0` release notes must record the tagged schema's SHA-256 checksum.
