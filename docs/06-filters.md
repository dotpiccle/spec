# Filters

Filters shape a sound by removing or boosting certain frequency regions. A layer can have zero or more filters applied **in series** -- filter 1's output feeds filter 2, and so on. The spec does not impose a maximum filter count per layer — engines MAY enforce their own limit.

Each filter has a **fixed type** for the whole layer, a `frequencies` array describing how the cutoff moves over time, and a `resonance` value.

## Filter types

| Type       | What it does                                                         | Use for                                                   |
| ---------- | -------------------------------------------------------------------- | --------------------------------------------------------- |
| `lowpass`  | Keeps low frequencies, softens highs. Like a blanket over the sound. | Warm/soft sounds, muffled effects, whooshes that open up. |
| `highpass` | Keeps high frequencies, removes lows. Makes sound thin/crisp.        | Clicks, ticks, paper sounds, bright effects.              |
| `bandpass` | Keeps a focused frequency band, removes everything above and below.  | Pops, resonant impacts, telephone-like sounds.            |

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

## Static filter (one entry)

The most common case -- a single fixed cutoff, like a button click or a notification bell:

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

_A bandpass filter centered at 2000 Hz with slight resonance -- produces a focused, clicky sound. "A short noise burst, brightened with a bandpass filter -- the everyday button click."_

## Filter sweep (two entries)

A filter whose cutoff moves over time, like a whoosh that opens from dull to crisp:

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

_A lowpass filter sweeping from 200 Hz to 8000 Hz over 110 ms -- the cutoff opens up, making the sound go from muffled to bright. "A brightening whoosh -- noise that opens up from dull to crisp."_

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

_The lowpass opens from 3000 Hz to 9000 Hz while the highpass stays fixed at 500 Hz. The filter chain removes deep rumble while the lowpass gradually brightens the sound._

## Resonance

Resonance controls how much the filter rings at its cutoff frequency. Think of it like a small bell tuned to the cutoff frequency:

- **At `resonance: 0`** there is no bell -- the filter just quietly passes sound through.
- **At higher values**, the filter starts to ring at its cutoff frequency after the input stops, like a struck bell singing its note.
- **A notification bell** typically uses `resonance: 0.4-0.6` on a bandpass filter at the bell's pitch.

This is not the same as reverb. Reverb makes the _whole sound_ bounce back like an echo in a room. Resonance makes a filter sustain _one frequency_ like a struck bell. A sound can use both.

The exact Q mapping and coefficients are defined below.

## Timing rules

Filter `frequencies` entries follow the standard contour entry timing rules defined in [Conventions](02-conventions.md). A static filter is a single entry containing only `hz`.

## Biquad definition (normative)

Each filter is a second-order digital biquad. Its state is all zeroes at the layer start. Filters run in array order and discard their remaining state at the effective layer end.

Map `resonance` to Q:

```text
Q = 0.707 + resonance × 11.293
```

For the current per-frame frequency `f` and render sample rate `sample_rate`, calculate:

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

In the canonical render profile, a moving cutoff is evaluated and the coefficients are recomputed for every sample frame. Other engine render profiles use their clamped render frequency and MAY use a numerically stable optimization when they preserve the declared contour timing and finite, stable output. Guidance for avoiding zipper noise is non-normative; see [Implementer Notes](13-implementer-notes.md).

Frequency clamping and numeric requirements are defined in [Engine Safety and the Canonical Render Profile](11-engine-safety.md).
