# Output

This chapter defines channel layout, signal-flow order, stereo balance, document duration, master gain, platform adaptation, and clipping.

## Signal flow

The normative order is:

```text
tone/noise source
  → serial layer filters
  → layer volume envelope and fades
  → equal-power balance (mono to stereo)
  → sum all active layers into the dry mix
  → spatial effects processing, when present (see [Spatial Effects](07-spatial-effects.md))
  → root master_volume_level
  → safety hard clipper
  → canonical stereo output
  → platform output adaptation
```

Changing the normative stages' order changes the sound and is not conforming. Each layer's filters and envelope state begin at its declared start and are discarded at its declared end or an earlier explicit document cutoff. The mix is an unnormalized sum; root master_volume_level and the safety clipper control the final range.

Sample-rate conversion, stereo-to-mono downmixing, hardware channel routing, and device-volume control are platform adaptation. They occur after the normative hard clipper and do not change Piccle asset semantics.

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

## Canonical mixing order

In canonical mode, initialize the dry left and right accumulators to binary64 positive zero for every frame. Visit active layers in document array order and perform one binary64 addition per channel for each layer. Do not clip, normalize, or reorder partial sums. This rule fixes rounding behavior without giving layer order any timing meaning.

Additional engine render profiles MAY use an equivalent parallel or vectorized reduction. Their output need not be sample-identical to canonical mode.

## Document and output timelines

Let `D` be the explicit root `duration_ms`, or the latest declared layer end when it is omitted. Let `F(m) = frame(m)` from [Engine Safety](11-engine-safety.md). Without spatial effects, output frames are `[0, F(D))`. With spatial effects, output frames are `[0, Eₙ)` where `Eₙ` is the accumulated per-stage frame boundary defined in [Spatial Effects](07-spatial-effects.md) §Stage boundaries. Engines MUST accumulate per-stage frame counts; they MUST NOT round the millisecond sum independently.

For a layer starting at `S` and ending at `E = S + layer.duration_ms`, its untruncated global-frame interval is `[F(S), F(E))`. An explicit `duration_ms` changes the active interval to `[F(S), min(F(E), F(D)))`; the interval is empty when its end is not greater than its start. Truncation does not move or create a layer fade. A non-zero sample may therefore be followed by zero at the boundary. Authors who need a smooth explicit cutoff must align each affected layer's declared duration and fade with `D`.

If `duration_ms` is longer than every layer, the dry mix is silent after the latest layer end. Reverb still receives zero input through `D` and its declared tail begins after `D`.

## Root volume

The optional root `master_volume_level` is a linear master gain from `0` through `1`, defaulting to `1`. It is applied to the dry/wet result immediately before clipping. Unlike layer `volume`, this field accepts only a single number — not a contour object. Piccle v1 has no root fade fields; fades belong exclusively to layer volume envelopes.

## Safety clipper

For each final left and right sample `s`, engines MUST apply:

```text
clip(s) = -1 when s < -1
           1 when s > 1
           s otherwise
```

The hard clipper is the last normative DSP stage. It has no attack, release, lookahead, makeup gain, or behavior below full scale.

## Mono and device output

The canonical output is always stereo. A host with mono hardware MAY downmix after clipping. The recommended non-normative equal-power-preserving downmix is:

```text
mono = (left + right) / sqrt(2)
```

The host is responsible for preventing overflow introduced by downstream mixing or device processing.
