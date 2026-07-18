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

## Reverb starting point

A compact Schroeder-style reverb can satisfy short UI-sound use cases:

1. Use several parallel comb filters with mutually non-harmonic delay lengths.
2. Follow them with two or three short allpass stages.
3. Put a lowpass in each feedback path for `soften_hz` damping.
4. Choose feedback gains for an RT60 of `tail_ms`.
5. Measure and normalize the combined stereo impulse-response energy before applying `amount`.

For a delay of `delay_samples`, a common RT60 feedback starting point is:

```text
gain = 10 ^ (-3 × delay_samples / (tail_ms × sample_rate / 1000))
```

The result still needs to pass the normative RT60, damping, energy, and lifetime measurements in [Reverb](07-reverb.md).

## Noise implementation

Implement PCG32 with explicit-width unsigned integers. Languages without native wrapping integers should mask the state and result after each operation. Convert the result to binary64 before division by `2^32`.

The `soft` and `sharp` character gains are analytic stationary-RMS gains. They avoid pre-rendering, duration-dependent normalization, and unbounded buffers. Unit tests for an engine should compare the first several generator integers with a separately implemented PCG32 routine before testing the character filters.

## Oscillators

A band-limited wavetable or polyBLEP oscillator is usually more efficient than evaluating a harmonic series per frame. Preserve the normative zero phase and phase integral when selecting or interpolating tables. Frequency-dependent tables help prevent high-frequency square and saw layers from aliasing on phone speakers.

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

Before claiming renderer conformance, render every official example at the canonical profile and the engine's native device rate. Listen on headphones and a phone speaker, then inspect for non-finite samples, clipping frequency, high-frequency aliasing, envelope discontinuities, reverb cutoff, and unexpected CPU spikes.
