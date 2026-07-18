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

Let `D` be the explicit or computed document duration and let `N` be the frame count obtained by converting `tail_ms` with the absolute-boundary rule in [Engine Safety](11-engine-safety.md). When reverb is present, the output timeline is `[0, D + tail_ms)`. The reverb consumes the dry mix during `[0, D)` and zero input afterward.

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

Let `T` be the exclusive output end frame and let the tail contain `N` frames. Define:

```text
W = max(2, min(frame_count(5 ms), ceil(N / 10)))
```

All engine render profiles use rates of at least 8 kHz, so a valid one-millisecond tail contains enough frames for `W >= 2`. For frame `n`:

```text
terminal_gain(n) = 1                              when n < T-W
                   (T - 1 - n) / (W - 1)          when T-W <= n < T
                   0                              otherwise
```

The gain is `1` on the first terminal-window frame and exactly `0` on the final emitted frame.

## Wet-path normalization and RT60

Measure an engine with a one-frame dry input whose left and right samples are both `sqrt(0.5)`. The document duration for this measurement is one frame. If the tail contains `N` frames, the captured response has `T = N + 1` frames indexed `0` through `N`; frame `0` is the one-frame document interval and frames `1` through `N` are the emitted tail interval. Capture the complete softened and terminal-windowed wet response.

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

The first frame whose energy is at most `10^-6` of `E[0]` is the −60 dB crossing. It MUST occur at a frame in the final 10% of tail frames `1` through `N`. The final emitted wet frame `N` is exactly zero because of the terminal window.

## Dry/wet crossfade

After normalization, terminal windowing, and softening, apply:

```text
output = (1 - amount) × dry + amount × wet
```

`amount: 0` is fully dry and `amount: 1` is fully wet. Reverb presence still defines the complete output timeline even when the amount is zero.

## Implementation freedom

Schroeder, feedback-delay-network, generated-convolution, and other linear time-invariant implementations are permitted when they meet the response, normalization, and lifetime requirements above. Exact cross-engine reverb samples are not required.

The suggested implementation in [Implementer Notes](13-implementer-notes.md) is non-normative.
