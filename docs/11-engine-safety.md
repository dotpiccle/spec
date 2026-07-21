# Engine Safety and Render Profiles

This chapter defines the Piccle engine's canonical test profile, production render-profile contract, frequency safety, finite-output behavior, and resource preflight.

## Canonical conformance profile

The Piccle engine MUST provide a canonical test mode with:

| Property                     | Canonical value                 |
| ---------------------------- | ------------------------------- |
| Render sample rate           | 48000 Hz                        |
| Output channels              | 2: left, right                  |
| Control and DSP calculations | IEEE-754 binary64               |
| Output sample storage        | IEEE-754 binary32               |
| Time origin                  | Frame `0`, document time `0 ms` |

Canonical mode MUST be reachable by the engine qualification suite. The Rust API surface used to reach it is implementation-defined; canonical mode does not need to be the normal production profile.

Convert any non-negative document-time boundary `m` in milliseconds to a frame at sample rate `r` with:

```text
frame(m) = floor(m × r / 1000 + 0.5)
```

`m` may be a derived rational boundary, such as the 90% point of a reverb tail. Evaluate the formula in binary64 in canonical mode. At 48 kHz, every integer millisecond is exactly 48 frames.

The Piccle engine MUST construct one absolute boundary schedule before rendering. For a layer whose declared start is `S`, every local boundary at offset `c` maps to `frame(S + c)`. A segment from offsets `a` through `b` contains:

```text
frame(S + b) - frame(S + a)
```

Do not round `a`, `b`, or a segment duration independently. The document cutoff is `frame(D)`. Spatial-effect tails are computed in frames from each effect's parameters and added to that cutoff as defined in [Spatial Effects](07-spatial-effects.md) §Output length. Timelines are half-open: `[start_frame, end_frame)`.

Canonical mode processes source values, filter state, reverb state, coefficients, and controls in binary64. After the final hard clip, convert each left and right sample to binary32 using round-to-nearest, ties-to-even.

## Additional engine render profiles

The Piccle engine MAY provide production render profiles for particular platforms, products, or resource classes. Every exposed profile:

- MUST declare an integer render sample rate of at least 8000 Hz;
- MAY use binary32, fixed-point, SIMD, WebAssembly, JavaScript numbers, DSP hardware, or another documented numeric mode;
- MUST implement every v1 primitive for documents within its published resource limits;
- MUST use the absolute-boundary frame rule at its declared rate;
- MUST keep every declared timing boundary within one frame at its declared rate;
- MUST produce finite, stable output and suppress energy at and above Nyquist; and
- MUST apply every specified default, contour, gain, state, and signal-flow rule.

Cross-rate and cross-numeric-mode sample equality is not required. Whether the Piccle engine renders live, ahead of playback, offline, into a cache, or through another execution strategy is implementation-defined and MUST NOT change Piccle document semantics or qualification.

## Render-profile frequency safety

For an active render profile, define:

```text
render_frequency_max = min(20000, 0.49 × sample_rate)
```

Canonical mode therefore uses `20000` Hz. The engine clamps instantaneous pitch and author filter frequencies to:

```text
[20, render_frequency_max]
```

It also clamps the fixed `soft` and `sharp` noise-character corners and the `soften_hz` or `damp_hz` field of each applicable `spatial_effects` entry to `render_frequency_max` before calculating coefficients. Declared document values remain unchanged and valid; the clamp adapts rendering to the profile's available bandwidth.

If an active profile's published output-bandwidth policy cannot represent a document adequately, the engine MUST report the valid document as unsupported. It MUST NOT change format validity.

## Conformance

The Piccle engine MUST pass every normative 48 kHz canonical-profile requirement and MUST qualify every additional render profile it exposes.

The specification does not prescribe whether rendering happens during playback, before playback, on the target device, on another processor, or in an asset-build pipeline. That deployment choice is implementation-defined; accepted documents and rendered output remain governed by this specification.

## Determinism classes

| Component                                                                      | Canonical requirement                                                              |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Version, validation, defaults, timing, curves, gain, balance, mixing, clipping | Exact semantics                                                                    |
| Seeded PCG32 raw noise                                                         | Exact unsigned sequence and source values                                          |
| Tone oscillators                                                               | Exact phase semantics and the harmonic tolerances in [Sources](03-sources.md)      |
| Filters                                                                        | Published coefficients, zero state, and per-frame updates                          |
| Reverb effect                                                                  | Perceptually equivalent wet response at canonical and additional render profiles, measured against the canonical reference IR fixtures using the tolerances in [Spatial Effects](07-spatial-effects.md); published reference IR generator, lowpass, terminal window, measured response, normalization, and lifetime |
| Echo effect                                                                    | Canonical-mode bit-equivalence with transcendental tolerance for the lowpass coefficient; deterministic output-length formula |

“Exact semantics” does not require bit-identical transcendentals across processors. Canonical implementations MUST use binary64 calculations.

## Finite output and clipping

Every DSP stage MUST produce finite samples. If an internal calculation produces `NaN` or infinity, the engine MUST stop rendering that document and report an implementation error; it MUST NOT forward the value to an output system.

The final hard clipper defined in [Output](08-output.md) is mandatory and is the last normative DSP stage.

## Denormal protection

The Piccle engine MUST prevent subnormal values from causing unbounded DSP cost. Flush-to-zero modes, explicit state floors, or equivalent methods are permitted. Denormal handling MUST NOT produce output above `-180 dBFS` and MUST NOT change a declared timeline boundary.

## Engine-defined resource limits

Piccle does not impose maximum document duration, layer count, filter count, contour point count, reverb tail, simultaneous voice count, memory, or CPU cost. Each production profile MUST publish finite limits for every resource it bounds.

A document that passes format validation but exceeds a published engine limit is valid but unsupported by that engine. Resource and output-bandwidth limits MUST be checked before allocating render resources and MUST NOT be presented as schema or semantic-validation failures.

Each tone or noise layer active at a frame counts as one voice. If the host explicitly enables partial playback after a voice-limit failure, the engine MUST retain earlier layer-array entries first and MUST report degraded output to the host. Otherwise it MUST return unsupported without rendering.

## Untrusted input

The Piccle engine MUST treat documents as untrusted input. Before rendering, it MUST:

1. Enforce parser size and nesting limits. If input exceeds them before validity can be established, report a resource-limit rejection.
2. Reject invalid UTF-8, malformed JSON, and duplicate member names.
3. Validate against the declared schema version.
4. Run Piccle semantic validation.
5. Compare the valid document with engine resource and output-bandwidth limits.
6. Allocate only bounded, checked buffers and state.

The distinction between invalid and unsupported is defined in [Conformance](14-conformance.md).
