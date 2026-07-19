# Changelog

All notable changes to the Piccle specification are documented here. Piccle v1 has not yet reached a stable release.

## Unreleased — targeting v1.0.0-rc.1

### Added

- Canonical reference IR render fixtures for the reverb perceptual-equivalence gate (five binary64 stereo PCM files at 48 kHz with 4 kHz soften, 1, 10, 20, 220, and 500 ms tails, SHA-256 manifest) at `test-vectors/numeric/reverb-reference-irs/`.
- Strict normative perceptual-equivalence tolerances for reverb across non-canonical render profiles: RT60 crossing window, total wet energy ±0.5 dB, echo density ±10% of reference, modal resonance floor hybrid (engine ≤ ref + 6 AND engine ≤ −30 dB), L/R correlation ±0.15, spectral centroid ±10%, onset within ±1 sample.
- Perceptually equivalent wet reverb output at canonical (binary64, 48 kHz) mode across conforming engines, verified by seven strict numeric tolerances against the canonical reference IR fixtures. The FDN hot path contains no transcendentals, but configuration-preparation constants (feedback gains, wet lowpass) use `pow` and `exp`, which IEEE-754 does not require to be correctly-rounded across processors.
- Author-facing note in `docs/07-reverb.md` clarifying that the equivalence tolerances constrain engine conformance, not author intent.
- Canonical 48 kHz stereo render profile with binary64 control calculations, binary32 output samples, half-open timelines, and exact millisecond-to-frame conversion.
- Deterministic PCG32 noise generation and optional unsigned 32-bit `source.seed`, defaulting to `0`.
- Normative oscillator phase, waveform, anti-aliasing, signal-flow, equal-power balance, filter-coefficient, fade, clipping, and reverb-normalization rules.
- Dedicated conformance chapter distinguishing malformed, schema-invalid, semantically invalid, and valid-but-unsupported documents.
- Reproducible repository validator and CI for schema, semantic rules, duplicate JSON members, fixtures, links, formatting, and contract invariants.
- Public contribution, compatibility, and release process.
- Per-fixture published baseline values for the seven reverb perceptual-equivalence metrics in `test-vectors/numeric/reverb-reference-irs/manifest.json` under `metrics`.
- Reference implementation of all seven metrics in `scripts/reverb_metrics.py`.
- Validator gate comparing each fixture's published baseline metrics to a fresh computation in `scripts/validate.py::reverb_reference_ir_metrics_errors()`.
- Per-configuration random orthogonal feedback matrix for the reference FDN, generated via modified Gram-Schmidt orthonormalization of a PCG32-seeded matrix. The random orthogonal matrix spreads eigenvalues as `e^{±jθ}` around the unit circle (vs the Walsh-Hadamard transform's `±1`), distributing mode energy more uniformly and reducing the modal resonance floor. Reference: Dal Santo et al. 2024 (arXiv:2402.11216); JOS PASP §Choice of Lossless Feedback Matrix.
- Canonical engine conformance and additional render profiles covering browser, desktop, mobile, console, vehicle, kiosk, and embedded implementations.
- Render-profile frequency adaptation down to declared 8 kHz engine profiles.
- Measurable oscillator harmonic, phase, DC, and alias tolerances using coherent canonical-profile windows.
- Normative reverb wet lowpass, energy-decay measurement, and automatic terminal window.
- Exact absolute-boundary scheduling for layers, contours, fades, document cutoffs, and reverb tails at every render rate.
- Agent-oriented engine build guide with subsystem order, target-platform decisions, required evidence, and definition of done.
- Deterministic diffused eight-line feedback-delay-network baseline with constant per-frame work, bounded delay memory, and perceptual qualification against the earlier generated-convolution response.
- Stable semantic errors for derived layer-end and output-end safe-integer overflow.
- Parser fixtures and stable errors for non-JSON numeric tokens and decimal values outside finite binary64 range.
- Non-PCM document render cases for computed duration, hard truncation, simultaneous boundaries, fades, and non-additive reverb-tail frame counts.
- Curved fade-in and fade-out. The `transition_curve` enum (`linear`, `exponential`, `easeIn`, `easeOut`, `easeInOut`) is now reusable on `fade_in.curve` and `fade_out.curve` in object-form layer volume.

### Removed

- Removed root `fade_in_ms` and `fade_out_ms`. Fades now belong exclusively to layer volume envelopes; reverb termination is automatic.

### Changed

- **FDN delay caps removed for long tails.** The eight-line late-network delay lengths in `docs/13-implementer-notes.md` are no longer capped by fixed `cap_ms` values; the proportional part `R × ratio[i]` scales with `tail_ms`, meeting Schroeder's modal-density criterion `M ≥ 0.15 × T₆₀ × Fs` at ~113% of the minimum for all valid tails. The diffuser caps are unchanged (early reflections don't scale with tail_ms). State memory is now proportional to `tail_ms` (~70 bytes/ms at 48 kHz, ~34 KiB at 500 ms); per-frame work remains constant at ~194 ops. All 5 canonical fixtures regenerated.
- **FDN feedback matrix changed from Walsh-Hadamard transform to per-configuration random orthogonal matrix.** The random orthogonal matrix (generated via modified Gram-Schmidt from a PCG32-seeded matrix, cached per reverb configuration) spreads eigenvalues as `e^{±jθ}` around the unit circle, distributing mode energy more uniformly than the WHT's `±1` eigenvalues. This reduces the modal resonance floor for all tail lengths, with the largest improvement at long tails (220 ms: −28.1 → −30.7 dB; 500 ms: −34.8 → −35.9 dB). Per-frame work increases from ~94 to ~194 ops (dense 8×8 matrix multiply vs fast Walsh-Hadamard transform). Reference: Dal Santo et al. 2024 (arXiv:2402.11216).
- **Modal resonance floor tolerance tightened from one-sided to hybrid.** The previous one-sided `engine ≤ ref + 6 dB` is supplemented with an absolute floor `engine ≤ −25 dB` (derived from the worst non-degenerate reference fixture, `−27.7 dB` for `tail_ms = 20`, plus 2.7 dB headroom, rounded to `−25 dB`). Both clauses must be satisfied. The hybrid is strictly tighter than the one-sided tolerance for all non-degenerate fixtures. The "transitional" framing in the `docs/07-reverb.md` Note has been removed — this is now the final bar.
- **Modal resonance floor analysis window changed from `0.15 × tail_ms` (Schroeder minimum) to `max(0.15 × tail_ms × Fs, M)` (Schroeder-aware).** The window now accounts for the FDN's actual total delay `M`, which may exceed the Schroeder minimum for short tails where the proportional delays and the `prev + 1` distinctness constraint produce `M > 0.15 × T₆₀ × Fs`.
- **Modal resonance floor analysis window changed to Nyquist-resolution formula** (issue #7). The previous `W_m = max(schroeder_min, M)` was insufficient: for the 20 ms fixture, the 162-frame window (3.4 ms) had exactly 296 Hz Rayleigh resolution — equal to the mode spacing — causing unresolved modes to smear together and inflating the measured modal floor to −27.7 dB. The new formula `W_m = min(late_tail, max(schroeder_min, 2 × M))` applies a Nyquist-like 2× factor, giving a 324-frame (6.75 ms) window for the 20 ms fixture. This resolved the artifact and revealed the true modal floor of −32.8 dB. **The absolute gate tightened from `engine ≤ −25 dB` to `engine ≤ −30 dB`** (2.8 dB headroom below the new worst non-degenerate fixture, rounded to `−30 dB`). No fixtures were regenerated; the FDN output is identical. All 5 modal-floor baselines improved: 10 ms −42.8 → −46.6 dB; 20 ms −27.7 → −32.8 dB; 220 ms −30.7 → −37.8 dB; 500 ms −35.9 → −40.8 dB.
- **Reverb determinism-class row promoted** from "Published lowpass, terminal window, measured response, normalization, and lifetime" to "Bit-identical wet response at canonical mode; published reference IR generator, lowpass, terminal window, measured response, normalization, lifetime, and strict perceptual-equivalence tolerances at additional render profiles."
- **Reverb topology changed from implementation-defined to normative.** The diffused eight-line FDN in `docs/13-implementer-notes.md` §Reference reverb runtime is now the only conforming reverb topology. A conforming engine MUST implement it. The previous "recommended default" and "engines may replace with another LTI realization (e.g. convolution)" language has been removed from `docs/13`, `docs/07`, and `docs/15`. This resolves issue #10: the modal-resonance metric's `M` parameter is now the same for all engines (same FDN, same `tail_ms`, same sample rate → same `M`), making cross-engine comparison reproducible. No fixtures regenerated, no baselines changed, no SHA-256s changed — the reference IRs were already generated from this FDN.
- **FDN recipe elevated from "first-implementation suggestion" to "recommended default runtime topology"** in `docs/13-implementer-notes.md`; convolution against the published reference IR is permitted but not the recommended default.
- **Soft "comparable" wording in RELEASE_CHECKLIST.md replaced** with the strict perceptual-equivalence tolerances against the published reference IR render. A/B listening remains a release gate but is no longer the sole cross-engine equivalence gate.
- **AGENTS.md refactored to agent-orientation-only file.** Removed duplicated process, normative, and schema-authoring content that had other canonical homes. Moved contribution/process sections to `CONTRIBUTING.md` (change categories, compatibility checklist, synchronized updates matrix, changelog rules, definition of done). Created `schemas/AGENTS.md`, `examples/AGENTS.md`, `test-vectors/AGENTS.md`, and `docs/AGENTS.md` as dedicated sub-instruction files. Added normative-language glossary to `docs/02-conventions.md`. No format, validation, schema, or playback behavior changed.
- **Narrative:** Reframed the repository as the specification for the Piccle product (which ships an open-source reference engine), rather than as an open standard primarily for third-party engine implementers. Building an independent engine remains a fully supported path via the Engine Build Guide and conformance gates. No format, validation, schema, or playback behavior changed.
- **Root `volume` renamed to `master_volume_level` (breaking, pre-rc.1).** The root `volume` field is a single 0–1 master gain and never accepted a contour object, unlike the layer `volume` field which accepts a number shorthand or a `{ fade_in, fade_out, levels }` object. The shared name invited authors and generators to assume root `volume` could take a contour. Renamed to `master_volume_level` to make the contract self-evident — `master` signals whole-document post-mix gain, `level` signals a single amplitude value (consistent with the per-entry `level` field in the layer contour). Mechanical migration: `"volume": X` → `"master_volume_level": X`. Layer `volume` is unchanged.
- **Fade fields migrated to object form (breaking, pre-rc.1).** Layer-volume `fade_in_ms` (integer) and `fade_out_ms` (integer) replaced by `fade_in` and `fade_out` objects, each `{ "ms": integer, "curve": enum }`. The `curve` defaults to `"linear"`, so existing audio output is byte-equivalent when migrating via the mechanical form `"fade_in_ms": X` → `"fade_in": {"ms": X}`. The marker-level workaround (zero-level entry with `transition_curve`) remains valid for transitions between audible levels.
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
- Separated document compilation from audio production and documented allocation-free, block-streamable engine guidance.
- **Normatively pinned the measurement algorithm for each of the seven reverb perceptual-equivalence metrics** (echo density, modal resonance floor, L/R Pearson correlation, spectral centroid, onset frame, RT60 crossing, total wet energy) in `docs/07-reverb.md` §Perceptual-equivalence metric algorithms. Previously only RT60 crossing and total wet energy were precisely specified; the other five left outcome-changing choices unspecified. Tolerance interpretation is now relative for echo density, total wet energy, and spectral centroid (`engine ∈ [0.9 × ref, 1.1 × ref]`, with `engine == 0` required when `ref == 0`); absolute for L/R correlation (`|engine − ref| ≤ 0.15`); integer-exact for the RT60 crossing frame and onset frame; and one-sided relative for the modal resonance floor.
- **Modal resonance floor tolerance changed from the previous absolute `≤ −40 dB` gate to a one-sided relative tolerance `engine ≤ ref + 6 dB` against the reference fixture's measured value.** The previous absolute gate was unattainable: the canonical reference fixtures themselves measure in the −60 to −104 dB range under any reasonable STFT-based algorithm, because the reference FDN is modal-deficient by design at long tails (its total delay `M ≈ 1,570` samples is below Schroeder's modal-density minimum `M ≥ 0.15 × T₆₀ × Fs` for `tail_ms ≥ 220`). The −40 dB figure was not derived from any standard reverb-quality metric. The one-sided relative tolerance allows elite engines that exceed the reference's modal density to pass while catching single-mode resonator failures (a resonator near 0 dB fails by ~60 dB). This is a transitional bar; a tracked follow-up issue will fix the reference FDN's modal density and tighten the tolerance to an absolute gate.
- **Modal resonance floor analysis window changed from `0.1 × tail_ms` to `0.15 × tail_ms`** (the Schroeder minimum, per Schroeder & Logan 1961 and JOS *Physical Audio Signal Processing*). The previous window was 2/3 of the modal-resolution minimum and could not resolve individual modes.
- **Modal resonance floor now excludes the onset** (`onset_skip = max(frame(5), frame(0.05 × tail_ms))` frames) before placing analysis windows. The previous algorithm's "max over all windows" picked the onset window, measuring onset spectral coloration rather than a sustained ringing mode.
- No fixtures were regenerated; no SHA-256s changed. The metrics are computed from the unchanged fixtures with the new algorithms.

### Fixed

- Fixed broken cross-document links and malformed README navigation.
- Corrected the documented layer `volume` type from “number or array” to “number or object.”
- Synchronized schema defaults, closed-object behavior, metadata constraints, noise semantics, examples, and validation fixtures.
- Defined previously ambiguous filter state, bandpass gain, coefficient update, panning, fade-overlap, truncation, and reverb wet-gain behavior.
- Replaced ambiguous reverb damping and tail-cutoff behavior with an exact wet lowpass, Schroeder energy-decay rule, and zero-valued final wet frame.
- Fixed stale `reverb_baseline_at_48000` FDN delay lengths in `test-vectors/numeric/dsp-values.json` for `tail_220_ms` and `tail_500_ms`. Commit `e8cc4fc` (issue #6) removed the FDN delay caps from `docs/13` and the reference IR generator but missed `dsp-values.json` and the validator's `baseline_lengths` helper, which still passed the old caps. The validator now passes `None` (uncapped) for the FDN, matching the generator and `reverb_metrics.py`.
- Fixed reverb perceptual-equivalence metrics (modal resonance floor and spectral centroid) being undefined when the captured response `T` or modal analysis window `W_m` exceeds `N_fft = 65536`. The FFT length is now `N_fft = max(65536, next_power_of_two(signal_length))` per metric, covering the full valid tail range. The 65536 minimum preserves all published baselines (the 5 canonical fixtures all have `T` and `W_m` below 65536). Added `--test` regression mode to `reverb_metrics.py` verifying metrics at boundary lengths (65535, 65536, 65537, 65538, 100K, 200K frames).

### Release gates

- The canonical website and schema URI must resolve and serve the frozen schema.
- A clean-room engine must be implementable from the normative text without unresolved questions.
- Every official example and primitive-coverage asset must pass cross-platform rendering, headphone, full-range, small-speaker, and low-bandwidth listening review.
- Stable `v1.0.0` release notes must record the tagged schema's SHA-256 checksum.
