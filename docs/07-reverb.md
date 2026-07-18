# Reverb

Reverb is an optional whole-document effect applied after the dry stereo layer mix. It gives a one-shot sound a short sense of space.

## Fields

When `reverb` is present, all fields are required.

| Field       | Type    | Range         | Meaning                                    |
| ----------- | ------- | ------------- | ------------------------------------------ |
| `amount`    | number  | `0`–`1`       | Linear dry/wet crossfade.                  |
| `tail_ms`   | integer | `1` or more   | RT60 decay time and emitted tail duration. |
| `soften_hz` | number  | `200`–`12000` | Damping corner applied to the wet decay.   |

```json
"reverb": {
  "amount": 0.18,
  "tail_ms": 220,
  "soften_hz": 4000
}
```

## Timeline

Let `D` be the explicit or computed document duration. When reverb is present, the output timeline is `[0, D + tail_ms)`. The reverb consumes the dry mix during `[0, D)` and zero input afterward. Its state is discarded at `D + tail_ms`.

`tail_ms` is the time for the wet decay to fall by 60 dB (RT60), measured from the peak response to an impulse. The emitted tail also ends at `tail_ms`. The root `fade_out_ms` reaches zero at the end of the complete output timeline, preventing a discontinuity when the reverb state is discarded.

## Wet-path normalization

The wet processor MUST have unity impulse-response energy before the `amount` crossfade. For a centered unit impulse, sum the squared wet samples over both output channels through `tail_ms`:

```text
energy = Σ(wet_left[n]² + wet_right[n]²)
```

The processor applies one constant normalization gain so that `energy = 1`. An implementation MAY calculate this gain when its reverb configuration is created and cache it. This requirement gives `amount` a comparable loudness meaning across algorithms and prevents an arbitrary wet gain from driving the safety clipper.

## Required response

A conforming reverb MUST satisfy all of the following:

1. Its energy-decay curve reaches −60 dB at `tail_ms`, with a tolerance of ±10% of `tail_ms`.
2. Frequencies above `soften_hz` decay faster than frequencies below it. The wet tail's one-third-octave spectrum MUST roll off by at least 3 dB per octave above `soften_hz`, excluding bands that reach Nyquist.
3. It produces finite samples and MUST NOT sustain feedback after its declared tail.
4. It uses the crossfade:

   ```text
   output = (1 - amount) × dry + amount × wet
   ```

   `amount: 0` is fully dry. `amount: 1` is fully wet.

Measure RT60 and damping with a centered, full-scale, one-frame stereo impulse at the canonical 48 kHz sample rate. Apply wet-path normalization before measuring. Do not include the root output envelope or safety clipper in these measurements.

## Implementation freedom

Piccle does not mandate a reverb topology. Schroeder, feedback-delay-network, and generated-convolution implementations are permitted when they meet the response, normalization, and lifetime requirements above. Exact cross-engine reverb samples are not required.

The suggested implementation in [Implementer Notes](13-implementer-notes.md) is non-normative.
