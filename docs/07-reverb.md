# Reverb

Reverb is an optional whole-document effect applied after the dry stereo layer mix. It gives a one-shot sound a short sense of space.

## Fields

When `reverb` is present, all fields are required.

| Field       | Type    | Range         | Meaning                                       |
| ----------- | ------- | ------------- | --------------------------------------------- |
| `amount`    | number  | `0`–`1`       | Linear dry/wet crossfade.                     |
| `tail_ms`   | integer | `1` or more   | RT60 target and emitted wet-tail duration.    |
| `soften_hz` | number  | `200`–`12000` | Wet-path first-order lowpass corner in Hertz. |

```json
"reverb": {
  "amount": 0.18,
  "tail_ms": 220,
  "soften_hz": 4000
}
```

## Timeline

Let `D` be the explicit or computed document duration. Define:

```text
dry_end_frame = frame(D)
output_end_frame = frame(D + tail_ms)
N = output_end_frame - dry_end_frame
```

When reverb is present, the output timeline is `[0, output_end_frame)`. The reverb consumes the dry mix before `dry_end_frame` and zero input afterward. Engines MUST derive `N` by subtracting these absolute boundaries; they MUST NOT round `tail_ms` independently.

The dry branch ends at `D`. The wet branch emits exactly `N` tail frames after `D`, including its automatic terminal window, and is zero outside the output timeline. All reverb core and lowpass state starts at zero and is discarded after the final output frame.

## Wet processor

The reverb core MUST be causal, bounded-input bounded-output stable, deterministic, linear, time-invariant, stereo, and free of dry-path leakage. It MUST begin from zero state for each document. Its conformance impulse response MUST have finite, positive energy before normalization. The topology is implementation-defined.

After the reverb core, apply this first-order lowpass independently to the wet left and right channels:

```text
f = min(soften_hz, render_frequency_max)
a = exp(-2π × f / sample_rate)
y[n] = a × y[n-1] + (1-a) × x[n]
y[-1] = 0
```

`render_frequency_max` is defined in [Engine Safety](11-engine-safety.md). In the canonical profile, every valid `soften_hz` is below that maximum and is used unchanged.

## Automatic terminal window

The wet tail always terminates smoothly. This behavior is mandatory and has no document field.

Let `T = output_end_frame`, let the tail contain `N` frames, and define the rounded five-millisecond span for the active sample rate:

```text
five_ms_frames = floor(5 × sample_rate / 1000 + 0.5)
W = max(2, min(five_ms_frames, ceil(N / 10)))
```

All engine render profiles use rates of at least 8 kHz, so a valid one-millisecond tail contains enough frames for `W >= 2`. For frame `n`:

```text
terminal_gain(n) = 1                              when n < T-W
                   (T - 1 - n) / (W - 1)          when T-W <= n < T
                   0                              otherwise
```

The gain is `1` on the first terminal-window frame and exactly `0` on the final emitted frame.

## Wet-path normalization and RT60

This measurement uses a DSP conformance harness, not a schema-valid Piccle document. Reset the reverb to zero state. Feed one frame whose left and right inputs are both `sqrt(0.5)`, followed by zeroes. For the harness only, define:

```text
N = floor(tail_ms × sample_rate / 1000 + 0.5)
T = N + 1
```

Capture frames `0` through `N`: frame `0` contains the input impulse and frames `1` through `N` are the tail. Apply the same lowpass and terminal-window equations with exclusive end `T`.

For captured wet samples `L[n]` and `R[n]`, apply one constant gain so that:

```text
Σ(n = 0 .. T-1) (L[n]² + R[n]²) = 1
```

Normalization occurs after softening and terminal windowing. An implementation MAY calculate and cache the gain for a reverb configuration.

Define the backward-integrated energy-decay curve:

```text
E[n] = Σ(k = n .. T-1) (L[k]² + R[k]²)
EDC_dB[n] = 10 × log10(E[n] / E[0])
```

The first frame whose energy is at most `10^-6` of `E[0]` is the −60 dB crossing. If its index is `c`, it MUST satisfy:

```text
c >= 1 + floor(0.9 × N)
c <= N
```

The final emitted wet frame `N` is exactly zero because of the terminal window. Compute the threshold comparison from the linear energy ratio; do not take `log10(0)` on the final frame.

## Dry/wet crossfade

After the reverb core, wet lowpass, terminal window, and normalization, apply:

```text
output = (1 - amount) × dry + amount × wet
```

`amount: 0` is fully dry and `amount: 1` is fully wet. Reverb presence still defines the complete output timeline even when the amount is zero.

## Reference IR and cross-engine equivalence

Piccle publishes canonical reference IR render fixtures for the reverb perceptual-equivalence gate at [test-vectors/numeric/reverb-reference-irs/](../test-vectors/numeric/reverb-reference-irs/). These fixtures are generated from the deterministic FDN algorithm in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime, running at canonical mode (binary64, 48 kHz) and following the conformance-harness procedure in this chapter. They record the full wet pipeline — reverb core, wet lowpass, terminal window, and normalization — as binary64 stereo PCM. The fixtures are the normative canonical reference IR render referenced by this chapter, [Engine Safety](11-engine-safety.md), and [Conformance](14-conformance.md); the `manifest.json` wrapper is a non-normative metadata file recording checksums and per-file metadata.

At canonical mode, a conforming engine implementing the diffused eight-line FDN generator at the published arithmetic ordering produces bit-identical wet output to every other conforming engine — the same guarantee Piccle gives for seeded noise via PCG32. This is the strongest cross-engine reverb equivalence Piccle can provide: two engines fed the same dry input produce the same wet samples, not merely comparable ones.

At additional render profiles (other sample rates, numeric modes, or runtime topologies), the wet output MUST meet these strict perceptual-equivalence tolerances against the published reference IR render, measured using the conformance harness (one frame of `L=R=sqrt(0.5)` followed by zeroes, through the engine's full wet pipeline):

| Metric | Tolerance | Captures |
|---|---|---|
| RT60 crossing frame `c` (`EDC_dB[c] <= -60 dB`) | `1 + floor(0.9 × N) <= c <= N` (existing, preserved) | Bulk decay timing |
| Total wet energy `Σ(L² + R²)` after normalization | Within `±0.5 dB` of the reference fixture's value | Overall loudness |
| Echo density — fraction of zero-crossing intervals below `sample_rate / 1000` in the first `min(N, 0.05 × sample_rate)` frames | Within `±10%` of the reference fixture's density | No metallic ringing or discrete echoes |
| Modal resonance floor — strongest sustained sinusoidal mode in any contiguous `0.1 × tail_ms` window, relative to the wet peak | `≤ −40 dB` | Single ringing frequency mode |
| L/R correlation across the tail (Pearson) | Within `±0.15` of the reference fixture's measured correlation | Stereo decorrelation |
| Spectral centroid of the post-softened wet response | Within `±10%` of the reference fixture's centroid | Brightness and damping beyond the normative lowpass corner |
| Onset frame — index of first wet sample exceeding `0.1 × peak_wet_sample` | Within `±1 sample` at canonical mode; within `±1 frame` at the active sample rate for additional profiles | No spurious predelay or different early-reflection patterns |

**Note.** These tolerances constrain engine conformance, not author intent. They require that a conforming engine's wet response matches the reference IR render for the *same* reverb configuration the author declared. They do not restrict what reverb configurations an author may select — an engine must reproduce whatever character the author's chosen `amount`, `tail_ms`, and `soften_hz` produce in the reference render, including the metallic or resonant character of a very short tail at high `soften_hz`.

## Implementation freedom

Schroeder, feedback-delay-network, generated-convolution, and other linear time-invariant implementations are permitted when they meet the response, normalization, equivalence tolerances, and lifetime requirements above.

The implementation in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime is the recommended default.
