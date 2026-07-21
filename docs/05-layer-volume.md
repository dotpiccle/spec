# Layer Volume and Amplitude Envelope

The layer `volume` field defines a linear-amplitude control signal applied after the serial filter chain and before equal-power panning. It accepts either a scalar shorthand or an object-form piecewise envelope.

> **Note:** The document root has a separate `master_volume_level` field (a single 0–1 number representing final post-mix gain). Unlike layer `volume`, it does **not** accept a contour object. See [Output](08-output.md#root-volume) for the root field's definition. This chapter covers only the layer `volume` field.

## Scalar shorthand

A number defines a constant base gain with the normative terminal linear fade:

```json
"volume": 0.4
```

_A linear-amplitude gain of 0.4, equivalent to `{"fade_in": {"ms": 0}, "fade_out": {"ms": 5}, "levels": [{"level": 0.4}]}`._

Use the shorthand when no intermediate amplitude targets or non-linear terminal curve are required.

## Object-form envelope

The object form defines fade-in, ordered level segments, and fade-out explicitly:

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

_A 2 ms attack to 0.4, 35 ms exponential decay to 0.08, sustain at 0.08, and 200 ms exponential release._

### Object fields

| Field      | Type   | Default                        | Required | Description                                                                                                                                       |
| ---------- | ------ | ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fade_in`  | object | `{"ms": 0, "curve": "linear"}` | No       | Fade-in from silence to the first level. Object with `ms` (duration, 0 or more) and optional `curve`.                                             |
| `fade_out` | object | `{"ms": 5, "curve": "linear"}` | No       | Fade-out from the last level to silence. Object with `ms` (duration, 0 or more) and optional `curve`. The 5 ms default prevents an audible click. |
| `levels`   | array  | --                             | **Yes**  | One or more ordered linear-amplitude targets. Each entry is described below.                                                                       |

### Level entry fields

| Field              | Type    | Default  | Required | Description                                                                                                                                                        |
| ------------------ | ------- | -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `level`            | number  | --       | **Yes**  | Target linear-amplitude gain in [0, 1]. Always a scalar number.                                                                                                    |
| `hold_ms`          | integer | 0        | No       | How long to hold at this level before transitioning to the next. 0 ms or more. Ignored on the last entry (the layer holds at the last level until the layer ends). |
| `transition_ms`    | integer | 0        | No       | How long to move from this level to the next. 0 ms or more. Ignored on the last entry (the fade-out handles the ending).                                           |
| `transition_curve` | string  | `linear` | No       | Shape of the transition to the next level. Ignored on the last entry.                                                                                              |

## Single-level envelope

A single level entry with no transition fields produces stationary gain:

```json
"volume": {
  "fade_out": {"ms": 5},
  "levels": [
    { "level": 0.3 }
  ]
}
```

_Equivalent to the shorthand `"volume": 0.3`._

## Two-level attack-decay-sustain-release envelope

Two levels define attack, peak hold, decay, sustain, and terminal release segments:

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

_A 2 ms attack to 0.5, 5 ms peak hold, 50 ms exponential decay to a 0.1 sustain level, and 200 ms release._

## Multi-segment envelope

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

_A three-target amplitude trajectory followed by the declared terminal fade._

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

This absolute-boundary subtraction is mandatory. The Piccle engine MUST NOT calculate `I`, `O`, or `T` by rounding each duration independently.

Let `curve(start, target, t)` denote the selected interpolation formula from [Curve Formulas](10-curves.md#curve-formulas), evaluated for `t` in `[0, 1)`. For local layer frame `n`, where `0 <= n < T`, the object-form envelope value during fade-out is:

```text
held_level                                                     when O = 0 or n < T-O
curve(held_level, 0, (n - (T-O)) / O)                         otherwise
```

For `I > 0`, local layer frame `n < I` uses `curve(0, first_level, n / I)`. The first level becomes exact at frame `I`. Fade-in and fade-out cannot overlap in an object-form contour because such a schedule is semantically invalid. For numeric shorthand, use the same rule with `held_level` equal to the shorthand number and `curve` equal to `linear`.

If the document root truncates a layer, the layer envelope is evaluated only through the truncation boundary; see [Output](08-output.md).

## Curved fades

The `curve` property on `fade_in` and `fade_out` reuses the same five-curve enum as `transition_curve`. Any curve available for level-to-level transitions is also available for both fade directions.

For fade-in from zero, `easeOut` concentrates gain change near onset while `easeInOut` reduces the derivative at both boundaries. An exponential fade-in remains near the positive floor for most of the interval and concentrates gain change near the terminal boundary.

For fade-out to zero, `exponential` produces a constant-ratio decay toward the positive floor. `easeIn` retains more energy early in the release and concentrates attenuation near the layer boundary.

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

Use the marker-level form when zero is an explicit contour target rather than the endpoint of the terminal fade stage. The two mechanisms compose: a level transition may reach zero before `fade_out` begins, after which the terminal fade multiplies an already zero-valued envelope.

## Default terminal de-click fade

A hard transition from a non-zero sample to zero introduces a broadband discontinuity. The default `fade_out.ms: 5` applies a short linear terminal window to reduce this boundary transient.

If the contour already reaches `level: 0`, the default terminal fade has zero output. Set `fade_out.ms: 0` to retain an abrupt declared layer boundary.

The engine does NOT add a fade when root `duration_ms` truncates a layer before its declared fade. What you write is what you hear; align the layer end with the document cutoff when a smooth exit is required.

## Exponential curves

When `transition_curve: "exponential"` is set, the transition follows the positive-floor formula in [Transition Curves](10-curves.md). The exact declared target becomes active at the segment boundary. For fade-out, `fade_out.curve: "exponential"` follows the same formula: the engine evaluates `s × (e/s)^t` with a positive floor for the near-zero target, and the exact zero is produced only at the final frame. See [Engine Safety](11-engine-safety.md) for the epsilon rule.
