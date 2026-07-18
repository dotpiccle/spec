# Implementer Notes

This appendix is non-normative. It offers implementation guidance after an engine author has read the normative chapters.

## Recommended reading order

1. [Document Structure](01-document-structure.md)
2. [Conventions](02-conventions.md)
3. [Sources](03-sources.md) through [Output](08-output.md)
4. [Noise and Determinism](09-noise-and-determinism.md)
5. [Transition Curves](10-curves.md)
6. [Engine Safety](11-engine-safety.md)
7. [Conformance](14-conformance.md)

For a task-ordered implementation checklist, see [Engine Build Guide](15-engine-build-guide.md).

## Baseline reverb implementation

An agent or first engine implementation should use the deterministic generated-convolution baseline below unless the platform already has another implementation that passes the normative measurements. This recipe is non-normative: engines may replace it without changing Piccle documents.

For one `tail_ms`, `soften_hz`, and sample-rate configuration:

1. Set `N = floor(tail_ms × sample_rate / 1000 + 0.5)` and allocate a 2-by-2 FIR matrix `hLL`, `hLR`, `hRL`, and `hRR`, each indexed `0..N`.
2. Initialize four Piccle PCG32 streams for those arrays with seeds `0x50494343`, `0x4C455256`, `0x52455652`, and `0x53544552` respectively. Generate and retain one sign per coefficient. Reuse these same sign arrays for every calibration candidate; do not continue advancing the generators during bisection.
3. For a provisional decay value `p`, generate every matrix coefficient from its retained sign:

   ```text
   envelope[n] = 10 ^ (-p × n / N)
   signXY = -1 when pcgXY_next() < 2^31, otherwise 1
   hXY[n] = signXY × envelope[n] / 2
   ```

4. Treat these coefficients as a stereo FIR reverb core:

   ```text
   wetL = convolve(dryL, hLL) + convolve(dryR, hLR)
   wetR = convolve(dryL, hRL) + convolve(dryR, hRR)
   ```

   Do not add a separate dry tap to the wet branch.
5. Run the normative conformance impulse through the FIR, wet lowpass, and terminal window. Measure its first −60 dB energy crossing.
6. Starting with the interval `p = [0.5, 6]`, use 32 bisection steps to target crossing frame `1 + floor(0.95 × N)`. If the crossing is earlier than the target, lower `p`; if it is later, raise `p`. A crossing anywhere in the normative final-10% interval is sufficient; exact convergence on the target is not required.
7. Apply the normative constant wet-energy normalization to the calibrated response. Cache the coefficients and gain by render profile, `tail_ms`, and `soften_hz` when useful.

The FIR is causal, stable, deterministic, linear, time-invariant, dense even for short tails, and finite by construction. Independent signs give stereo decorrelation without introducing an author-facing random parameter. Direct convolution is adequate for short UI tails; partitioned convolution or another mathematically equivalent implementation can reduce cost for long supported tails.

A Schroeder or feedback-delay-network reverb is also permitted, but its delay layout, feedback tuning, stereo mapping, and response calibration become engine responsibilities. It still needs to pass every normative measurement in [Reverb](07-reverb.md).

## Noise implementation

Implement PCG32 with explicit-width unsigned integers. Languages without native wrapping integers should mask the state and result after each operation. Convert the result to binary64 before division by `2^32`.

The `soft` and `sharp` character gains are analytic stationary-RMS gains. They avoid pre-rendering, duration-dependent normalization, and unbounded buffers. Unit tests for an engine should compare the first several generator integers with a separately implemented PCG32 routine before testing the character filters.

## Oscillators

A band-limited wavetable or polyBLEP oscillator is usually more efficient than evaluating a harmonic series per frame. Preserve the normative zero phase, phase integral, and harmonic targets when selecting or interpolating tables. Frequency-dependent tables help prevent high-frequency square and saw layers from aliasing across output systems.

## Dynamic biquads

The canonical profile recomputes coefficients per frame. A real-time engine may reduce coefficient work when a cutoff is static. For moving cutoffs, common stable approaches include per-frame coefficient calculation, short control blocks with coefficient interpolation, or a topology-preserving transform. Validate fast exponential sweeps at high Q; direct coefficient interpolation can become unstable.

The normative coefficient equations and zero initial state are in [Filters](06-filters.md).

## Denormal handling

On x86, Flush-to-Zero and Denormals-Are-Zero flags are usually the cheapest protection. On other platforms, explicitly clear sufficiently small state values. Apply the strategy consistently to filters and reverb feedback paths.

## Voice allocation

Preflight the layer intervals before playback so the engine can determine peak simultaneous voices without allocating each voice. A sweep-line over sorted start and end boundaries is sufficient. When a host chooses degraded partial playback, earlier layer-array entries have the recommended priority.

## Validation architecture

Keep these failures separate in the public API:

- malformed JSON;
- schema-invalid document;
- semantically invalid document;
- valid but unsupported document;
- internal render failure.

This separation makes authoring tools useful and prevents device capacity from being mistaken for a format defect.

## Release qualification

Before claiming engine conformance, render every official example in canonical mode and in each additional declared render profile. Qualify native desktop, browser, mobile, constrained-device, low-rate, stereo, and mono-host integrations that the engine supports. Listen on headphones, full-range speakers, a small-device speaker, and the lowest-bandwidth supported output, then inspect for non-finite samples, clipping frequency, high-frequency aliasing, envelope discontinuities, reverb cutoff, and unexpected CPU spikes.
