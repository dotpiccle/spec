# Transition Curves

This chapter defines contour scheduling and the five normative interpolation functions.

## How to read the curve illustrations

The illustrations in this chapter are non-normative. They show rising transitions from left to right: time advances along the horizontal axis, and the interpolated value rises along the vertical axis. A denser rise near the left means that more of the change happens early; a denser rise near the right means that more happens late.

```text
value
  ^                         target
  |                       /
  |                     /
  |                   /
  |                 /
  | start         /
  +----------------------------> time
    t = 0                    t = 1
```

For `linear`, `easeIn`, `easeOut`, and `easeInOut`, the same progress shape applies whether the target is above or below the start. A falling transition therefore moves slowly or quickly at the same part of its duration as the corresponding rising illustration.

`exponential` is different: it interpolates ratios rather than equal differences. Its exact shape depends on the ratio between `start` and `target`, so its illustration uses a concrete `0.1` to `1.0` example.

The `transition_curve` on one contour entry shapes the movement from that entry's value to the next entry's value. It changes only the intermediate values: it does not change the hold duration, transition duration, start value, or exact target at the segment boundary.

Fade stages (`fade_in.curve` and `fade_out.curve` on a layer volume object) reuse the same five curves and the same `t = j / N` frame convention. The difference is that fades always interpolate between zero and the first/last level, rather than between consecutive contour entries. See [Layer Volume](05-layer-volume.md#curved-fades) for fade-specific guidance.

## Frame scheduling

Let `S` be the layer's document-time start. Build cumulative contour offsets in milliseconds, beginning at `0`. Convert offset `c` to global frame `frame(S + c)` using [the render-profile timing rule](11-engine-safety.md). Derive every hold and transition length by subtracting consecutive global boundary frames; do not round a hold, transition, or cumulative offset independently.

Pitch and filter contour offsets begin at `0`. Object-form volume contour offsets begin after `fade_in.ms`; the fade-in boundary is therefore `frame(S + fade_in.ms)`. The declared target at any boundary becomes active on that boundary's frame.

At layer frame zero, a contour has entry `0`'s value. For each entry except the last:

1. Emit the current value throughout its `hold_ms` interval.
2. Emit the transition throughout its `transition_ms` interval.
3. At the first frame after the transition, the next entry becomes the exact current value.

For a transition containing `N > 0` frames, transition frame `j`, where `0 <= j < N`, uses:

```text
t = j / N
```

The exact target begins at the following frame. A transition with zero frames is an instantaneous jump to the target at its boundary, independent of `transition_curve`.

When multiple zero-frame holds or transitions share one boundary, process entries in array order before emitting that boundary frame. The last target reached by zero-frame jumps becomes current. If a positive-length transition also begins there, its first frame uses `j = 0` and therefore emits that current start target.

The last entry's timing members are ignored, and its value remains active through the rest of the declared layer timeline or an earlier document cutoff.

## Curve formulas

Let `start` and `target` be the surrounding entry values and let `t` be in `[0, 1)`.

### `linear`

```text
v(t) = start + (target - start) × t
```

`linear` changes by the same absolute amount during every equal interval of time. It has no acceleration or deceleration: at 25% of the transition time, it has completed 25% of the value change.

```text
target |                         *
       |                    *
       |               *
       |          *
start  |     *
       +---------------------------> time
             steady rate
```

Use it when a parameter should move at a constant rate, or when a very short transition does not benefit from additional shaping. For pitch, a linear curve changes by equal numbers of hertz per unit of time, not by equal musical intervals.

### `exponential`

```text
s = max(start, 1e-10)
e = max(target, 1e-10)
v(t) = s × (e / s)^t
```

The positive floor prevents division by zero for volume transitions. At the segment boundary, the engine uses the exact declared target, including zero. Pitch and filter inputs are already positive.

`exponential` changes by the same ratio during every equal interval of time. The midpoint is the geometric mean of the floored endpoints, not their arithmetic average. For example, a transition from `100 Hz` to `400 Hz` reaches `200 Hz` halfway through because both halves multiply frequency by two.

The following rising illustration uses `start = 0.1` and `target = 1.0`:

```text
1.0    |                         *
       |                        /
       |                      /
       |                  ***
0.1    |     *************
       +---------------------------> time
             slow, then fast
```

For a rising transition, smaller values occupy more of the timeline before the curve climbs rapidly toward the target. For a falling transition, the value drops rapidly at first and then spends more time near the smaller target. This behavior is often perceptually natural for pitch and filter-frequency sweeps because frequency ratios correspond more closely to musical intervals than equal differences in hertz do.

When either volume endpoint is zero, the formula uses `1e-10` internally and switches to the exact declared zero only at the segment boundary. Authors should expect a transition involving zero to remain mathematically positive until that boundary.

### `easeIn`

```text
v(t) = start + (target - start) × t²
```

`easeIn` begins with almost no movement and continuously accelerates. At 50% of the transition time, it has completed only 25% of the value change; the remaining 75% happens during the second half.

```text
target |                         *
       |                       **
       |                    ***
       |              ******
start  |     *********
       +---------------------------> time
             slow, then fast
```

Use it when the transition should feel restrained at its start and decisive near its end, such as a sweep that gathers energy. The curve does not ease into the target: its rate is greatest immediately before the boundary.

### `easeOut`

```text
v(t) = start + (target - start) × (1 - (1-t)²)
```

`easeOut` changes rapidly at the start and continuously decelerates toward the target. At 50% of the transition time, it has already completed 75% of the value change.

```text
target |                  ********
       |              ****
       |          ****
       |       ***
start  |     **
       +---------------------------> time
             fast, then slow
```

Use it when the response should be immediate but settle gently, such as a parameter change that should do most of its work early. The curve leaves the start at its maximum rate and then slows continuously; it does not ease away from the starting value.

### `easeInOut`

```text
v(t) = start + (target - start) × (t² / (t² + (1-t)²))
```

`easeInOut` begins slowly, accelerates through the middle, and decelerates toward the target. It is symmetric around the midpoint and completes exactly 50% of the value change at 50% of the transition time.

```text
target |                       ***
       |                    ***
       |             *******
       |          ***
start  |     *****
       +---------------------------> time
          slow, fast, then slow
```

Use it for a smooth departure and arrival when neither endpoint should feel abrupt. Compared with `easeIn` and `easeOut`, it concentrates more of the change around the middle of the transition.

## Curve comparison

This non-normative table compares how much of a rising value change has occurred at selected times. The first four rows use a normalized `0` to `1` transition. The exponential row uses `0.1` to `1.0`, then expresses its current value as a percentage of that example's total absolute change.

| Curve           | At 25% time | At 50% time | At 75% time | Character                 |
| --------------- | ----------: | ----------: | ----------: | ------------------------- |
| `linear`        |         25% |         50% |         75% | Constant rate             |
| `easeIn`        |       6.25% |         25% |      56.25% | Slow start, fast finish   |
| `easeOut`       |      43.75% |         75% |      93.75% | Fast start, slow finish   |
| `easeInOut`     |         10% |         50% |         90% | Slow at both endpoints    |
| `exponential`\* |       8.65% |      24.03% |      51.37% | Equal ratios through time |

The percentages describe the illustrated rising examples only. In particular, exponential interpolation should be chosen for its ratio-based behavior, not as a generic substitute for `easeIn`.

All control calculations use binary64 precision. Engines MUST produce finite values and MUST begin the next segment from the exact preceding target so rounding error does not accumulate across a contour.

## Fade curves

A fade stage (the `fade_in` or `fade_out` object) is a special case of the same scheduling and interpolation rules. For a fade-out of `O > 0` frames, the fade gain at local layer frame `n >= T - O` is:

```text
t = (n - (T - O)) / O
gain = c(t)
```

where `c(t)` is the curve function for `fade_out.curve`. The gain multiplies the held final level. At frame `T`, the gain reaches zero.

For a fade-in of `I > 0` frames, the fade gain at local layer frame `n < I` is:

```text
t = n / I
gain = c(t)
```

The gain multiplies the first level. At frame `I`, the gain reaches `1` and the first level becomes exact.

For `exponential`, the same positive-floor rule from [Curve Formulas](#curve-formulas) applies to prevent division by zero. During a fade-out, `s` is the held level (positive) and `target` floors to `1e-10` internally; the exact `0` is produced only at frame `T`. During a fade-in from silence, `s` floors to `1e-10` and `target` is the first level. See [Engine Safety](11-engine-safety.md) for the canonical epsilon definition.
