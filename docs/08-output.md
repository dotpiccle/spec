# Output

This chapter defines channel layout, signal-flow order, stereo balance, whole-document output shaping, and clipping.

## Signal flow

The normative order is:

```text
tone/noise source
  → serial layer filters
  → layer volume envelope
  → equal-power balance (mono to stereo)
  → sum all active layers
  → reverb dry/wet crossfade, when present
  → root volume and root fade envelope
  → safety hard clipper
  → stereo output
```

Changing this order changes the sound and is not conforming. Each layer's filters and envelope state begin at its `start_ms` and are discarded at its effective end. The mix is an unnormalized sum; the root volume and safety clipper control the final range.

## Equal-power balance

Tone and noise sources are mono. For a layer `balance` value `b`, calculate:

```text
x = (b + 1) / 2
left_gain  = cos(x × π/2)
right_gain = sin(x × π/2)
left  = mono × left_gain
right = mono × right_gain
```

This gives full left at `-1`, equal-power center at `0`, and full right at `1`. Balance is static for the layer in v1.

## Output timeline

Without reverb, total output duration is the explicit or computed document duration. With reverb, add `reverb.tail_ms`. All timelines are half-open: a duration of `T` frames contains frames `0` through `T-1`.

The root fade-in starts at frame zero. The root fade-out ends at the first frame after the output timeline. A fade longer than the output is clamped to the total output duration.

For total frame count `T`, effective fade frame counts `I` and `O`, and frame `n`:

```text
fade_in_gain(n) = 1                         when I = 0
                  min(1, n / I)             otherwise

fade_out_gain(n) = 1                        when O = 0 or n < T-O
                   (T - n) / O              otherwise

root_gain(n) = volume × fade_in_gain(n) × fade_out_gain(n)
```

When fades overlap, their gains multiply. Output is exactly zero outside `[0, T)`.

## Root fields

| Field         | Type    | Default | Range       | Meaning                                        |
| ------------- | ------- | ------- | ----------- | ---------------------------------------------- |
| `volume`      | number  | `1`     | `0`–`1`     | Linear gain applied to the post-reverb signal. |
| `fade_in_ms`  | integer | `0`     | `0` or more | Linear fade from silence at output start.      |
| `fade_out_ms` | integer | `5`     | `0` or more | Linear fade to silence at output end.          |

These members live at the document root. Layer volume fields affect only their owning layer.

## Truncation

An explicit document `duration_ms` may end before a layer's declared end. The layer is truncated at the document boundary before reverb. Its remaining oscillator, filter, and envelope state is discarded. The root fade still operates at the end of the complete output timeline.

## Safety clipper

For each final left and right sample `s`, engines MUST apply:

```text
clip(s) = -1 when s < -1
           1 when s > 1
           s otherwise
```

The hard clipper is the last DSP stage. It has no attack, release, lookahead, makeup gain, or behavior below full scale.
