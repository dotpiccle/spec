# Engine Safety and the Canonical Render Profile

This chapter defines the required reference environment and resource-safety behavior for Piccle engines.

## Canonical render profile

The canonical profile is used to interpret all normative frame-level algorithms:

| Property                             | Canonical value                 |
| ------------------------------------ | ------------------------------- |
| Render sample rate                   | 48000 Hz                        |
| Output channels                      | 2: left, right                  |
| Control and coefficient calculations | IEEE-754 binary64               |
| Output sample storage                | IEEE-754 binary32               |
| Time origin                          | Frame `0`, document time `0 ms` |

Convert a non-negative absolute millisecond boundary `m` to a frame at sample rate `r` with:

```text
frame(m) = floor(m × r / 1000 + 0.5)
```

At 48 kHz, every integer millisecond is exactly 48 frames. Engines MUST calculate segment lengths by subtracting converted absolute boundaries. Timelines are half-open: `[start_frame, end_frame)`.

The canonical profile processes signal values, filter state, reverb state, coefficients, and control values in binary64. After the final hard clip, convert each left and right sample to binary32 using round-to-nearest, ties-to-even. Native real-time engines MAY use binary32 DSP internally when they still meet the published semantic and measured tolerances.

A native renderer MAY operate at another rate of at least 44100 Hz. It MUST use the same absolute-boundary rule at that rate. Cross-rate sample equality is not required. An engine whose hardware rate is lower MUST render internally at a supported rate and resample, or report the document as unsupported.

## Determinism classes

| Component                                                                      | Requirement                                                                                         |
| ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| Version, validation, defaults, timing, curves, gain, balance, mixing, clipping | Exact semantics                                                                                     |
| Seeded PCG32 raw noise at the same sample rate                                 | Exact unsigned sequence and source values                                                           |
| Tone oscillators                                                               | Exact frequency and phase semantics; anti-aliasing implementation may vary within the stated bounds |
| Filters in the canonical profile                                               | Published coefficients, zero state, and per-frame updates                                           |
| Reverb                                                                         | Measured response and normalization; exact samples are not required                                 |

“Exact semantics” does not require bit-identical transcendentals across processors. Implementations MUST use binary64 control calculations and MUST keep timing within one frame of the canonical boundary.

## Frequency safety

Declared pitch and filter values are schema-valid only in `[20, 20000]` Hz. After pitch offset and during interpolation, engines MUST clamp the instantaneous frequency to:

```text
[20, min(20000, sample_rate / 2)]
```

The canonical 48 kHz profile therefore uses `[20, 20000]`. Engines MUST suppress oscillator energy at and above Nyquist and MUST prevent invalid or unstable filter coefficients.

## Finite output and clipping

Every DSP stage MUST produce finite samples. If an internal calculation produces `NaN` or infinity, the engine MUST stop rendering that document and report an implementation error; it MUST NOT forward the value to audio hardware.

The final hard clipper defined in [Output](08-output.md) is mandatory and is the last DSP stage.

## Denormal protection

Engines MUST prevent subnormal floating-point values from causing unbounded DSP cost. Flush-to-zero CPU modes, explicit state floors, or equivalent methods are permitted. Denormal handling MUST NOT produce output above `-180 dBFS` and MUST NOT change any declared timeline boundary.

## Engine-defined resource limits

Piccle deliberately does not impose maximum document duration, layer count, filter count, contour point count, reverb tail, or simultaneous voice count. Engines MAY publish finite limits for these resources.

A document that passes format validation but exceeds a published engine limit is **valid but unsupported** by that engine. Resource limits MUST be checked before allocating render resources. They MUST NOT be presented as schema or semantic-validation failures.

Each tone or noise layer active at a frame counts as one voice. If an engine chooses partial playback after exceeding a real-time voice limit, it SHOULD retain earlier array entries first, but partial playback is degraded behavior and MUST be reported to the host.

## Untrusted input

Engines MUST treat documents as untrusted input. Before rendering, they MUST:

1. Enforce parser size and nesting limits. If an input exceeds them before validity can be established, report a resource-limit rejection, not an invalid Piccle document.
2. Reject invalid UTF-8, malformed JSON, and duplicate member names.
3. Validate against the declared schema version.
4. Run Piccle semantic validation.
5. Compare the valid document with engine render-resource limits.
6. Allocate only bounded, checked buffer sizes.

The distinction between invalid and unsupported is defined in [Conformance](14-conformance.md).
