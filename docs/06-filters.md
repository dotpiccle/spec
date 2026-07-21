# Filters

The `filters` array defines zero or more serial second-order IIR sections on a layer. Each section receives the preceding section's output. The specification imposes no filter-count maximum; each Piccle engine profile MUST publish any filter-count support limit it enforces.

Each filter has a **fixed type** for the whole layer, a `frequencies` array describing how the cutoff moves over time, and a `resonance` value.

## Filter types

| Type | Transfer-function class | Piccle coefficient form |
| --- | --- | --- |
| `lowpass` | Second-order lowpass | RBJ-style lowpass numerator with resonance-derived `Q` |
| `highpass` | Second-order highpass | RBJ-style highpass numerator with resonance-derived `Q` |
| `bandpass` | Constant 0 dB peak-gain bandpass | `b0 = α`, `b1 = 0`, `b2 = -α` before `a0` normalization |

## Filter structure

```json
"filters": [
  {
    "type": "lowpass",
    "frequencies": [
      { "hz": 2000 }
    ],
    "resonance": 0
  }
]
```

### Filter fields

| Field         | Type   | Default | Required | Description                                                                                     |
| ------------- | ------ | ------- | -------- | ----------------------------------------------------------------------------------------------- |
| `type`        | string | --      | **Yes**  | Filter type: `lowpass`, `highpass`, or `bandpass`. Fixed for the whole layer.                   |
| `frequencies` | array  | --      | **Yes**  | One or more entries describing the cutoff frequency over time. Each entry has the fields below. |
| `resonance`   | number | 0       | No       | How much the filter rings at its cutoff frequency. 0-1. 0 = flat, 1 = strong ringing.           |

### Frequency entry fields

| Field              | Type    | Default  | Required | Description                                                                         |
| ------------------ | ------- | -------- | -------- | ----------------------------------------------------------------------------------- |
| `hz`               | number  | --       | **Yes**  | Cutoff frequency at this point. 20-20000 Hz.                                        |
| `hold_ms`          | integer | 0        | No       | How long to hold at this cutoff before transitioning. 0 ms or more.                 |
| `transition_ms`    | integer | 0        | No       | How long to move from this cutoff to the next. 0 ms or more. Ignored on last entry. |
| `transition_curve` | string  | `linear` | No       | Shape of the transition. Ignored on last entry.                                     |

## Static cutoff

A one-entry frequency contour holds a constant cutoff or center frequency for the layer lifetime:

```json
"filters": [
  {
    "type": "bandpass",
    "frequencies": [
      { "hz": 2000 }
    ],
    "resonance": 0.2
  }
]
```

_A 2 kHz constant-peak-gain bandpass section with `resonance: 0.2`._

## Two-point cutoff trajectory

A two-entry contour produces a time-varying cutoff:

```json
"filters": [
  {
    "type": "lowpass",
    "frequencies": [
      { "hz": 200, "transition_ms": 110, "transition_curve": "exponential" },
      { "hz": 8000 }
    ],
    "resonance": 0
  }
]
```

_A lowpass cutoff transitioning exponentially from 200 Hz to 8 kHz over 110 ms._

## Multi-point filter contour (three-plus entries)

For complex filter motion, use three or more entries:

```json
"filters": [
  {
    "type": "highpass",
    "frequencies": [
      { "hz": 300, "hold_ms": 10, "transition_ms": 60, "transition_curve": "linear" },
      { "hz": 2000, "hold_ms": 0, "transition_ms": 40, "transition_curve": "exponential" },
      { "hz": 5000 }
    ],
    "resonance": 0.1
  }
]
```

## Two-filter chain

Use multiple filters in the `filters` array when you need different types operating simultaneously. The filters run in series:

```json
"filters": [
  {
    "type": "lowpass",
    "frequencies": [
      { "hz": 3000, "transition_ms": 80, "transition_curve": "linear" },
      { "hz": 9000 }
    ],
    "resonance": 0
  },
  {
    "type": "highpass",
    "frequencies": [
      { "hz": 500 }
    ],
    "resonance": 0
  }
]
```

_The lowpass corner sweeps from 3000 Hz to 9000 Hz while the highpass corner remains fixed at 500 Hz, progressively increasing retained upper-band energy while maintaining low-frequency attenuation._

## Resonance and Q

`resonance` is a normalized control mapped linearly to quality factor `Q` over `[0.707, 12]`. Increasing `Q` narrows the transition bandwidth and increases the pole-pair decay time and response magnitude near cutoff for lowpass/highpass sections. For the constant-peak-gain bandpass form, increasing `Q` narrows bandwidth while retaining 0 dB peak gain. The exact mapping and coefficients are defined below.

## Timing rules

Filter `frequencies` entries follow the standard contour entry timing rules defined in [Conventions](02-conventions.md). A static filter is a single entry containing only `hz`.

## Biquad definition (normative)

Each filter is a second-order digital biquad. Its state is all zeroes at the layer start. Filters run in array order and discard their remaining state at the declared layer end or an earlier explicit document cutoff.

Map `resonance` to Q:

```text
Q = 0.707 + resonance × 11.293
```

At each layer frame, first evaluate the filter-frequency contour, then clamp that result to `[20, render_frequency_max]`, then use the clamped value as `f`. For `f` and render sample rate `sample_rate`, calculate:

```text
ω = 2π × f / sample_rate
c = cos(ω)
α = sin(ω) / (2Q)
```

The unnormalized coefficients are:

| Type       |      `b0` |     `b1` |      `b2` |  `a0` |  `a1` |  `a2` |
| ---------- | --------: | -------: | --------: | ----: | ----: | ----: |
| `lowpass`  | `(1-c)/2` |    `1-c` | `(1-c)/2` | `1+α` | `-2c` | `1-α` |
| `highpass` | `(1+c)/2` | `-(1+c)` | `(1+c)/2` | `1+α` | `-2c` | `1-α` |
| `bandpass` |       `α` |      `0` |      `-α` | `1+α` | `-2c` | `1-α` |

The `bandpass` form has constant 0 dB peak gain; Q controls its bandwidth. Normalize `b0`, `b1`, `b2`, `a1`, and `a2` by `a0`, then evaluate:

```text
y[n] = b0×x[n] + b1×x[n-1] + b2×x[n-2]
       - a1×y[n-1] - a2×y[n-2]
```

In the canonical render profile, evaluate the control for frame `n`, compute that frame's coefficients, and then process input sample `x[n]`. A moving cutoff is recomputed for every sample frame. Production render profiles use their clamped render frequency and MAY optimize coefficient evaluation only when they preserve declared contour timing and finite, stable output. The required production-profile constraints are in [Piccle Engine DSP Runtime](13-implementer-notes.md) §Dynamic biquads.

Frequency clamping and numeric requirements are defined in [Engine Safety and the Canonical Render Profile](11-engine-safety.md).
