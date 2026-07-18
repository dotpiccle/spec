# Engine Safety and Render Profiles

This chapter defines Piccle's platform-independent conformance profile, additional engine render profiles, frequency safety, and resource behavior.

## Canonical conformance profile

Every conforming engine MUST provide a canonical test mode with:

| Property                     | Canonical value                 |
| ---------------------------- | ------------------------------- |
| Render sample rate           | 48000 Hz                        |
| Output channels              | 2: left, right                  |
| Control and DSP calculations | IEEE-754 binary64               |
| Output sample storage        | IEEE-754 binary32               |
| Time origin                  | Frame `0`, document time `0 ms` |

Canonical mode may be exposed through diagnostics, tests, command-line tooling, or another engine-defined interface. It does not need to be the engine's normal production profile.

Convert a non-negative absolute millisecond boundary `m` to a frame at sample rate `r` with:

```text
frame(m) = floor(m × r / 1000 + 0.5)
```

At 48 kHz, every integer millisecond is exactly 48 frames. Engines MUST calculate segment lengths by subtracting converted absolute boundaries. Timelines are half-open: `[start_frame, end_frame)`.

Canonical mode processes source values, filter state, reverb state, coefficients, and controls in binary64. After the final hard clip, convert each left and right sample to binary32 using round-to-nearest, ties-to-even.

## Additional engine render profiles

An engine MAY provide other render profiles for particular platforms, products, or resource classes. Each such profile:

- MUST declare an integer render sample rate of at least 8000 Hz;
- MAY use binary32, fixed-point, SIMD, WebAssembly, JavaScript numbers, DSP hardware, or another documented numeric mode;
- MUST implement every v1 primitive for documents within its published resource limits;
- MUST use the absolute-boundary frame rule at its declared rate;
- MUST keep every declared timing boundary within one frame at its declared rate;
- MUST produce finite, stable output and suppress energy at and above Nyquist; and
- MUST apply every specified default, contour, gain, state, and signal-flow rule.

Cross-rate and cross-numeric-mode sample equality is not required. Whether an engine renders live, ahead of playback, offline, into a cache, or through another execution strategy is an engine concern and does not change Piccle document semantics or conformance.

## Render-profile frequency safety

For an active render profile, define:

```text
render_frequency_max = min(20000, 0.49 × sample_rate)
```

Canonical mode therefore uses `20000` Hz. The engine clamps instantaneous pitch and author filter frequencies to:

```text
[20, render_frequency_max]
```

It also clamps the fixed `soft` and `sharp` noise-character corners and `reverb.soften_hz` to `render_frequency_max` before calculating their coefficients. Declared document values remain unchanged and valid; the clamp adapts rendering to the profile's available bandwidth.

An engine MAY instead report a valid document as unsupported when an output-bandwidth policy cannot represent the document adequately. Output-bandwidth limits affect support, never format validity.

## Conformance

A conforming engine passes every normative 48 kHz canonical-profile requirement. It MAY expose any number of additional render profiles.

Conformance does not prescribe whether rendering happens during playback, before playback, on the target device, on another processor, or as part of an asset-build pipeline. It describes the engine's accepted documents and rendered output, not its deployment architecture.

## Determinism classes

| Component                                                                      | Canonical requirement                                                              |
| ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Version, validation, defaults, timing, curves, gain, balance, mixing, clipping | Exact semantics                                                                    |
| Seeded PCG32 raw noise                                                         | Exact unsigned sequence and source values                                          |
| Tone oscillators                                                               | Exact phase semantics and the harmonic tolerances in [Sources](03-sources.md)      |
| Filters                                                                        | Published coefficients, zero state, and per-frame updates                          |
| Reverb                                                                         | Published lowpass, terminal window, measured response, normalization, and lifetime |

“Exact semantics” does not require bit-identical transcendentals across processors. Canonical implementations MUST use binary64 calculations.

## Finite output and clipping

Every DSP stage MUST produce finite samples. If an internal calculation produces `NaN` or infinity, the engine MUST stop rendering that document and report an implementation error; it MUST NOT forward the value to an output system.

The final hard clipper defined in [Output](08-output.md) is mandatory and is the last normative DSP stage.

## Denormal protection

Engines MUST prevent subnormal values from causing unbounded DSP cost. Flush-to-zero modes, explicit state floors, or equivalent methods are permitted. Denormal handling MUST NOT produce output above `-180 dBFS` and MUST NOT change a declared timeline boundary.

## Engine-defined resource limits

Piccle does not impose maximum document duration, layer count, filter count, contour point count, reverb tail, simultaneous voice count, memory, or CPU cost. Engines MAY publish finite limits for these resources.

A document that passes format validation but exceeds a published engine limit is valid but unsupported by that engine. Resource and output-bandwidth limits MUST be checked before allocating render resources and MUST NOT be presented as schema or semantic-validation failures.

Each tone or noise layer active at a frame counts as one voice. If an engine chooses partial playback after exceeding a voice limit, it SHOULD retain earlier array entries first, but partial playback is degraded behavior and MUST be reported to the host.

## Untrusted input

Engines MUST treat documents as untrusted input. Before rendering, they MUST:

1. Enforce parser size and nesting limits. If input exceeds them before validity can be established, report a resource-limit rejection.
2. Reject invalid UTF-8, malformed JSON, and duplicate member names.
3. Validate against the declared schema version.
4. Run Piccle semantic validation.
5. Compare the valid document with engine resource and output-bandwidth limits.
6. Allocate only bounded, checked buffers and state.

The distinction between invalid and unsupported is defined in [Conformance](14-conformance.md).
