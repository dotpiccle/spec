# Volume

The `volume` field is the complete loudness description for a layer -- how loud the sound is and how that loudness changes over time. It exists in two forms.

## Form 1: Number shorthand (steady level)

A plain number means the layer plays at a constant level for its entire duration, with a fast anti-click fade-out:

```json
"volume": 0.4
```

_A steady tone at 40% loudness. Equivalent to: `{"fade_in_ms": 0, "fade_out_ms": 5, "levels": [{"level": 0.4}]}`._

This is the 90% case -- steady tones, beeps, and hums that do not change loudness.

## Form 2: Object contour (changing level)

For sounds that change loudness over time -- bells that strike then ring, clicks that punch then fade, pads that swell -- use the object form:

```json
"volume": {
  "fade_in_ms": 2,
  "fade_out_ms": 200,
  "levels": [
    { "level": 0.4, "hold_ms": 0, "transition_ms": 35, "transition_curve": "exponential" },
    { "level": 0.08 }
  ]
}
```

_A bell-like contour: fades in over 2 ms, strikes at 40%, (exponentially) settles to 8% over 35 ms, holds there, then fades out over 200 ms._

### Object fields

| Field         | Type    | Default | Required | Description                                                                                            |
| ------------- | ------- | ------- | -------- | ------------------------------------------------------------------------------------------------------ |
| `fade_in_ms`  | integer | 0       | No       | Time to rise from silence to the first level's target. 0 ms or more.                                   |
| `fade_out_ms` | integer | 5       | No       | Time to fade from the last level to silence. 0 ms or more. The 5 ms default prevents an audible click. |
| `levels`      | array   | --      | **Yes**  | One or more entries describing the loudness contour. Each entry is described below.                    |

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
  "fade_out_ms": 5,
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
  "fade_in_ms": 2,
  "fade_out_ms": 200,
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
  "fade_in_ms": 1,
  "fade_out_ms": 150,
  "levels": [
    { "level": 0.6, "transition_ms": 5, "transition_curve": "linear" },
    { "level": 0.2, "hold_ms": 20, "transition_ms": 50, "transition_curve": "exponential" },
    { "level": 0.4 }
  ]
}
```

_A sharp hit to 60%, immediate dip to 20%, exponential rise to 40%, hold for the remaining time, then fade out._

## Layer-envelope algorithm (normative)

For object-form volume, the layer starts at silence. A non-zero `fade_in_ms` linearly reaches the first level using the same frame convention as [Transition Curves](10-curves.md). Contour holds and transitions then run in order. After the final target is reached, the engine holds it until the fade-out begins. The linear fade-out reaches zero at the declared layer end.

The effective fade-out is `min(fade_out_ms, layer.duration_ms)`. The complete scheduled contour budget defined in [Conventions](02-conventions.md) MUST fit within the layer duration. This prevents an explicit fade-out from overlapping scheduled contour motion.

For numeric shorthand, the base level is active from layer frame zero and the only envelope stage is a linear `min(5, layer.duration_ms)` fade-out. This rule makes shorthand safe for layers shorter than the normal 5 ms default.

For a layer containing `T` frames and an effective fade-out of `O` frames, fade-out frame gain is:

```text
1                 when O = 0 or n < T-O
(T - n) / O       otherwise
```

For a fade-in containing `I > 0` frames, layer frame `n < I` uses `n/I` times the first level. The first level becomes exact at frame `I`. Fade-in and fade-out cannot overlap in an object-form contour because such a schedule is semantically invalid.

If the document root truncates a layer, the layer envelope is evaluated only through the truncation boundary; see [Output](08-output.md).

## Anti-click note: why fade_out_ms defaults to 5

In digital audio, any sound that is still audible (non-zero amplitude) at the exact moment it stops produces a brief, high-frequency **click** -- a discontinuity in the waveform. This is not a format opinion or an engine choice; it is how digital audio works on every platform.

The default `fade_out_ms: 5` applies a tiny fade that smooths the discontinuity. If the contour reaches a final `level` of `0`, this default has no audible effect because the sound is already silent. To request an abrupt ending, set `fade_out_ms: 0` explicitly.

The engine does NOT add a fade when root `duration_ms` truncates a layer before its declared fade. What you write is what you hear; align the layer end with the document cutoff when a smooth exit is required.

## Exponential curves

When `transition_curve: "exponential"` is set, the transition follows the positive-floor formula in [Transition Curves](10-curves.md). The exact declared target becomes active at the segment boundary. The `fade_out_ms` stage always approaches true zero linearly.
