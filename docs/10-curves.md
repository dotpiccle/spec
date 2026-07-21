# Transition Curves

This chapter defines contour scheduling and the five normative interpolation functions.

## Interpolation convention

The interpolation parameter `t` is normalized segment time over `[0, 1)`. `linear`, `easeIn`, `easeOut`, and `easeInOut` apply a normalized progress function to the signed difference `target - start`; their temporal curvature is invariant under transition direction. `exponential` interpolates the endpoint ratio and therefore depends on both endpoint magnitudes.

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

`linear` has constant first derivative `(target - start)` with respect to normalized time and zero second derivative. For pitch contours it produces constant Hz/s, not constant cents/s.

### `exponential`

```text
s = max(start, 1e-10)
e = max(target, 1e-10)
v(t) = s × (e / s)^t
```

The positive floor prevents division by zero for volume transitions. At the segment boundary, the engine uses the exact declared target, including zero. Pitch and filter inputs are already positive.

`exponential` has constant logarithmic rate. Its midpoint is the geometric mean of the floored endpoints. A transition from 100 Hz to 400 Hz therefore reaches 200 Hz at `t = 0.5`, producing constant cents/s for frequency contours.

When either volume endpoint is zero, the formula uses `1e-10` internally and switches to the exact declared zero only at the segment boundary. A transition involving zero therefore remains mathematically positive until that boundary.

### `easeIn`

```text
v(t) = start + (target - start) × t²
```

`easeIn` is quadratic progress. Its first derivative is zero at `t = 0` and maximal immediately before the target boundary; 25% of the value delta is complete at `t = 0.5`.

### `easeOut`

```text
v(t) = start + (target - start) × (1 - (1-t)²)
```

`easeOut` is the time-reversed quadratic progress function. Its first derivative is maximal at `t = 0` and zero at `t = 1`; 75% of the value delta is complete at `t = 0.5`.

### `easeInOut`

```text
v(t) = start + (target - start) × (t² / (t² + (1-t)²))
```

`easeInOut` is a symmetric rational quadratic with zero first derivative at both endpoints and 50% progress at `t = 0.5`. It concentrates control-rate change near the segment midpoint.

## Curve comparison

This non-normative table reports normalized progress checkpoints. The first four rows use a `0` to `1` transition. The exponential row uses `0.1` to `1.0` and expresses its current value as a fraction of that example's absolute delta.

| Curve           | At 25% time | At 50% time | At 75% time | Character                 |
| --------------- | ----------: | ----------: | ----------: | ------------------------- |
| `linear`        |         25% |         50% |         75% | Constant rate             |
| `easeIn`        |       6.25% |         25% |      56.25% | Slow start, fast finish   |
| `easeOut`       |      43.75% |         75% |      93.75% | Fast start, slow finish   |
| `easeInOut`     |         10% |         50% |         90% | Slow at both endpoints    |
| `exponential`\* |       8.65% |      24.03% |      51.37% | Equal ratios through time |

The exponential percentages are endpoint-dependent and apply only to the stated `0.1` to `1.0` interval.

All control calculations use binary64 precision. The Piccle engine MUST produce finite values and MUST begin the next segment from the exact preceding target so rounding error does not accumulate across a contour.

## Fade curves

A fade stage (the `fade_in` or `fade_out` object) is a special case of the same scheduling and interpolation rules. Let `curve(start, target, t)` mean the selected formula in §Curve formulas. For a fade-out of `O > 0` frames, the envelope value at local layer frame `n >= T - O` is:

```text
t = (n - (T - O)) / O
value = curve(held_level, 0, t)
```

At the exclusive layer-end boundary `T`, the value becomes exact zero and no sample is emitted for that layer.

For a fade-in of `I > 0` frames, the envelope value at local layer frame `n < I` is:

```text
t = n / I
value = curve(0, first_level, t)
```

At frame `I`, the first level becomes exact.

For `exponential`, the same positive-floor rule from [Curve Formulas](#curve-formulas) applies to prevent division by zero. During a fade-out, `s` is the held level (positive) and `target` floors to `1e-10` internally; the exact `0` is produced only at frame `T`. During a fade-in from silence, `s` floors to `1e-10` and `target` is the first level. See [Engine Safety](11-engine-safety.md) for the canonical epsilon definition.
