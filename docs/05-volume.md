# Volume

The `volume` field is the complete loudness description for a layer -- how loud the sound is and how that loudness changes over time. It exists in two forms.

## Form 1: Number shorthand (steady level)

A plain number means the layer plays at a constant level for its entire duration, with a fast anti-click fade-out:

```json
"volume": 0.4
```

_A steady tone at 40% loudness. Equivalent to: `{"fade_in": {"ms": 0}, "fade_out": {"ms": 5}, "levels": [{"level": 0.4}]}`._

This is the 90% case -- steady tones, beeps, and hums that do not change loudness.

## Form 2: Object contour (changing level)

For sounds that change loudness over time -- bells that strike then ring, clicks that punch then fade, pads that swell -- use the object form:

```json
"volume": {
  "fade_in": {"ms": 2},
  "fade_out": {"ms": 200},
  "levels": [
    { "level": 0.4, "hold_ms": 0, "transition_ms": 35, "transition_curve": "exponential" },
    { "level": 0.08 }
  ]
}
```

_A bell-like contour: fades in over 2 ms, strikes at 40%, (exponentially) settles to 8% over 35 ms, holds there, then fades out over 200 ms._

### Object fields

| Field      | Type   | Default                        | Required | Description                                                                                                                                       |
| ---------- | ------ | ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fade_in`  | object | `{"ms": 0, "curve": "linear"}` | No       | Fade-in from silence to the first level. Object with `ms` (duration, 0 or more) and optional `curve`.                                             |
| `fade_out` | object | `{"ms": 5, "curve": "linear"}` | No       | Fade-out from the last level to silence. Object with `ms` (duration, 0 or more) and optional `curve`. The 5 ms default prevents an audible click. |
| `levels`   | array  | --                             | **Yes**  | One or more entries describing the loudness contour. Each entry is described below.                                                               |

### Level entry fields

| Field              | Type    | Default  | Required | Description                                                                                                                                                        |
| ------------------ | ------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `level`            | number  | --       | **Yes**  | Target loudness at this point. 0-1. Always a plain number.                                                                                                         |
| `hold_ms`          | integer | 0        | No       | How long to hold at this level before transitioning to the next. 0 ms or more. Ignored on the last entry (the layer holds at the last level until the layer ends). |
| `transition_ms`    | integer | 0        | No       | How long to move from this level to the next. 0 ms or more. Ignored on the last entry (the fade-out handles the ending).                                           |
| `transition_curve` | string  | `linear` | No       | Shape of the transition to the next level. Ignored on the last entry.                                                                                              |

## One level (steady tone)

A single level entry with no transition fields produces a steady loudness:

```json
"volume": {
  "fade_out": {"ms": 5},
  "levels": [
    { "level": 0.3 }
  ]
}
```

_Equivalent to the shorthand `"volume": 0.3`._

## Two levels (ADSR-style)

Two levels reproduce the classic attack-decay-sustain-release shape found in most UI sounds:

```json
"volume": {
  "fade_in": {"ms": 2},
  "fade_out": {"ms": 200},
  "levels": [
    { "level": 0.5, "hold_ms": 5, "transition_ms": 50, "transition_curve": "exponential" },
    { "level": 0.1 }
  ]
}
```

_A sound that snaps to 50%, holds for 5 ms, exponentially decays to 10% over 50 ms, then fades out over 200 ms._

## Three or more levels (complex contours)

For hit-dip-rise-fall or other complex shapes, use three or more levels:

```json
"volume": {
  "fade_in": {"ms": 1},
  "fade_out": {"ms": 150},
  "levels": [
    { "level": 0.6, "transition_ms": 5, "transition_curve": "linear" },
    { "level": 0.2, "hold_ms": 20, "transition_ms": 50, "transition_curve": "exponential" },
    { "level": 0.4 }
  ]
}
```

_A sharp hit to 60%, immediate dip to 20%, exponential rise to 40%, hold for the remaining time, then fade out._

## Layer-envelope algorithm (normative)

For object-form volume, the layer starts at silence. A non-zero `fade_in.ms` reaches the first level using the curve specified by `fade_in.curve` and the frame convention defined in [Transition Curves](10-curves.md). Contour holds and transitions then run in order. After the final target is reached, the engine holds it until the fade-out begins. The fade-out reaches zero at the declared layer end using the curve specified by `fade_out.curve`.

The effective fade-out is `min(fade_out.ms, layer.duration_ms)`. The complete scheduled contour budget defined in [Conventions](02-conventions.md) MUST fit within the layer duration. This prevents an explicit fade-out from overlapping scheduled contour motion.

For numeric shorthand, the base level is active from layer frame zero and the only envelope stage is a linear `min(5, layer.duration_ms)` fade-out. This rule makes shorthand safe for layers shorter than the normal 5 ms default.

Let the layer start at document time `S`, have declared duration `L`, and end at `E = S + L`. Convert the boundaries with `frame()` from [Engine Safety](11-engine-safety.md):

```text
T = frame(E) - frame(S)
I = frame(S + fade_in.ms) - frame(S)
fade_start_ms = E - min(fade_out.ms, L)
O = frame(E) - frame(fade_start_ms)
```

This absolute-boundary subtraction is mandatory. Engines MUST NOT calculate `I`, `O`, or `T` by rounding each duration independently.

Let `c_in(t)` be the fade-in curve function and `c_out(t)` be the fade-out curve function for `t` in `[0, 1)`, as defined in [Curve Formulas](10-curves.md#curve-formulas). For `linear`, `easeIn`, `easeOut`, and `easeInOut`, `c(0) = 0` and `c(1) = 1`. For `exponential`, the start or target may be near-zero per the epsilon rule in [Engine Safety](11-engine-safety.md).

For local layer frame `n`, where `0 <= n < T`, fade-out gain is:

```text
1                            when O = 0 or n < T-O
c_out((n - (T-O)) / O)      otherwise
```

For `I > 0`, local layer frame `n < I` uses `c_in(n / I)` multiplied by the first level. The first level becomes exact at frame `I`. Fade-in and fade-out cannot overlap in an object-form contour because such a schedule is semantically invalid.

If the document root truncates a layer, the layer envelope is evaluated only through the truncation boundary; see [Output](08-output.md).

## Curved fades

The `curve` property on `fade_in` and `fade_out` reuses the same five-curve enum as `transition_curve`. Any curve available for level-to-level transitions is also available for both fade directions.

For fade-in from silence, `easeOut` and `easeInOut` are usually the most musical choices: they rise naturally and avoid a mechanical constant-rate onset. Avoid `exponential` for fade-in from silence; it spends most of its duration near zero and rises abruptly at the end.

For fade-out to silence, `exponential` is the natural choice for struck, plucked, or percussive sounds because it mirrors physical decay. `easeIn` suits "settle then cut" exits where the sound recedes gradually then falls silent quickly.

The same curve shapes and formulas defined in [Transition Curves](10-curves.md) apply. For very short fade durations (under 5–10 ms), curve choice has minimal audible effect; the anti-click fade-out uses a short window specifically.

### Relationship to the marker-level workaround

Before this feature, authors who needed a curved transition to or from silence used a dedicated `levels` entry with `transition_curve`. That pattern remains valid:

```json
"volume": {
  "fade_out": {"ms": 0},
  "levels": [
    {"level": 0.5, "hold_ms": 100},
    {"level": 0, "transition_ms": 200, "transition_curve": "exponential"}
  ]
}
```

Use the marker-level form when the curve should shape a transition _between two audible levels_ and the final level happens to be zero — for example, an exponential decay from an earlier sustain level. Use `fade_out.curve` for the common case of a simple exit to silence after the final target is reached. The two approaches compose: a marker-level transition shapes the move into zero, and `fade_out` then operates on that zero (silently, producing no audible effect).

## Anti-click note: why fade_out.ms defaults to 5

In digital audio, any sound that is still audible (non-zero amplitude) at the exact moment it stops produces a brief, high-frequency **click** -- a discontinuity in the waveform. This is not a format opinion or an engine choice; it is how digital audio works on every platform.

The default `fade_out.ms: 5` applies a tiny fade that smooths the discontinuity. If the contour reaches a final `level` of `0`, this default has no audible effect because the sound is already silent. To request an abrupt ending, set `fade_out.ms: 0` explicitly.

The engine does NOT add a fade when root `duration_ms` truncates a layer before its declared fade. What you write is what you hear; align the layer end with the document cutoff when a smooth exit is required.

## Exponential curves

When `transition_curve: "exponential"` is set, the transition follows the positive-floor formula in [Transition Curves](10-curves.md). The exact declared target becomes active at the segment boundary. For fade-out, `fade_out.curve: "exponential"` follows the same formula: the engine evaluates `s × (e/s)^t` with a positive floor for the near-zero target, and the exact zero is produced only at the final frame. See [Engine Safety](11-engine-safety.md) for the epsilon rule.
