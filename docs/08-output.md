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
  → reverb dry/wet crossfade, when present
  → root volume
  → safety hard clipper
  → canonical stereo output
  → platform output adaptation
```

Changing the normative stages' order changes the sound and is not conforming. Each layer's filters and envelope state begin at its `start_ms` and are discarded at its effective end. The mix is an unnormalized sum; root volume and the safety clipper control the final range.

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

## Document and output timelines

Let `D` be the explicit root `duration_ms`, or the latest declared layer end when it is omitted. Without reverb, output is defined on `[0, D)`. With reverb, output is defined on `[0, D + tail_ms)` as specified in [Reverb](07-reverb.md).

An explicit `duration_ms` hard-truncates every active layer at `D`. Truncation does not move or create a layer fade. A non-zero sample may therefore be followed by zero at the boundary. Authors who need a smooth explicit cutoff must align each affected layer's declared duration and fade with `D`.

If `duration_ms` is longer than every layer, the dry mix is silent after the latest layer end. Reverb still receives zero input through `D` and its declared tail begins after `D`.

## Root volume

The optional root `volume` is a linear master gain from `0` through `1`, defaulting to `1`. It is applied to the dry/wet result immediately before clipping. Piccle v1 has no root fade fields; fades belong exclusively to layer volume envelopes.

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
