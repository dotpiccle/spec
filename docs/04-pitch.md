# Pitch

Pitch is the fundamental-frequency control object of a tone source (see [Sources](03-sources.md)). It defines a piecewise time-varying frequency trajectory through the `frequencies` array.

Pitch is always a `frequencies` array -- there are no static shortcuts. A steady tone is a one-entry array; a glide is two entries; a multi-point contour is three or more.

## Structure

```json
"pitch": {
  "frequencies": [
    { "hz": 1046.5 }
  ],
  "offset_cents": 0
}
```

_Target fields inside `pitch`:_

| Field          | Type    | Default | Required | Description                                                                                            |
| -------------- | ------- | ------- | -------- | ------------------------------------------------------------------------------------------------------ |
| `frequencies`  | array   | --      | **Yes**  | One or more entries describing pitch over time. Each entry has the fields below.                       |
| `offset_cents` | integer | 0       | No       | Small pitch offset in cents. -1200 to 1200. 100 cents = 1 semitone. Added to every entry's `hz` value. |

_Fields inside each `frequencies[]` entry:_

| Field              | Type    | Default  | Required | Description                                                                            |
| ------------------ | ------- | -------- | -------- | -------------------------------------------------------------------------------------- |
| `hz`               | number  | --       | **Yes**  | Target pitch at this point. 20-20000 Hz. Higher = higher pitch.                        |
| `hold_ms`          | integer | 0        | No       | How long to hold at this pitch before transitioning to the next. 0 ms or more.         |
| `transition_ms`    | integer | 0        | No       | How long to move from this pitch to the next. 0 ms or more. Ignored on the last entry. |
| `transition_curve` | string  | `linear` | No       | Shape of the transition. See curves below. Ignored on the last entry.                  |

## Stationary fundamental (one entry)

A single entry produces a stationary fundamental frequency:

```json
"pitch": {
  "frequencies": [
    { "hz": 1046.5 }
  ]
}
```

_A stationary fundamental at 1046.5 Hz._

## Two-point frequency transition

A two-entry contour transitions from the first fundamental-frequency target to the second:

```json
"pitch": {
  "frequencies": [
    { "hz": 620, "transition_ms": 50, "transition_curve": "exponential" },
    { "hz": 430 }
  ]
}
```

_An exponential fundamental-frequency transition from 620 Hz to 430 Hz over 50 ms._

Exponential interpolation produces constant frequency ratios over equal time intervals. See [Transition Curves](10-curves.md) for the exact formula.

## Multi-point contour (three or more entries)

Three or more entries define a multi-segment fundamental-frequency trajectory:

```json
"pitch": {
  "frequencies": [
    { "hz": 620, "hold_ms": 0, "transition_ms": 50, "transition_curve": "exponential" },
    { "hz": 430, "hold_ms": 0, "transition_ms": 30, "transition_curve": "linear" },
    { "hz": 310 }
  ]
}
```

_A three-point pitch contour: 620 Hz drops to 430 Hz (exponential), then to 310 Hz (linear). The hold and transition fields on the last entry are ignored -- the sound holds at 310 Hz until the layer ends._

## Timing rules for pitch entries

Pitch entries follow the standard contour entry timing rules defined in [Conventions](02-conventions.md). The 20 Hz minimum frequency keeps all exponential inputs valid. An exponential target equal to the start frequency produces no change.

## Cents offset and detuning

The `offset_cents` field applies an equal-tempered frequency ratio to the interpolated contour. One hundred cents equals one semitone and 1200 cents equals one octave.

Parallel tone layers with small non-zero relative offsets produce deterministic beating at the difference frequency. Larger offsets produce explicit interval transposition.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "left",
      "duration_ms": 800,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 528 }],
          "offset_cents": 0
        }
      }
    },
    {
      "id": "right",
      "duration_ms": 800,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 528 }],
          "offset_cents": 12
        }
      }
    }
  ]
}
```

_Two 528 Hz sinusoidal layers with a relative detuning of 12 cents._

For every sample frame, the Piccle engine MUST apply pitch operations in this order:

1. Evaluate the `frequencies` contour to obtain `contour_hz`.
2. Apply the cents offset:

   ```text
   offset_hz = contour_hz × 2^(offset_cents / 1200)
   ```

3. Clamp `offset_hz` to `[20, render_frequency_max]` for the active render profile.
4. Use the clamped result for oscillator phase integration.

Do not clamp each declared target before interpolation, and do not apply `offset_cents` after the render-profile clamp. This order is observable near the format and Nyquist boundaries.
