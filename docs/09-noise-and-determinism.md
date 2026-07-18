# Noise and Determinism

This chapter defines the normative noise generator. Noise is streamed; Piccle does not use reusable or looping noise buffers.

## Source fields

| Field       | Type    | Default | Required | Meaning                                                            |
| ----------- | ------- | ------- | -------- | ------------------------------------------------------------------ |
| `type`      | string  | —       | **Yes**  | MUST be `noise`.                                                   |
| `character` | string  | —       | **Yes**  | `soft`, `neutral`, or `sharp`.                                     |
| `seed`      | integer | `0`     | No       | Unsigned 32-bit deterministic seed, from `0` through `4294967295`. |

The generator and all character filters start from their initial state at the layer's `start_ms`. Replaying a layer with the same `character` and `seed` MUST reproduce the same canonical-profile source samples. Two layers with the same character and seed intentionally produce identical source streams; authors SHOULD use different seeds when they want decorrelated texture.

## PCG32 stream

Piccle uses the PCG-XSH-RR 64/32 generator. All unsigned arithmetic wraps modulo `2^64` or `2^32` according to the destination width.

The algorithm originates from the [official PCG32 reference](https://www.pcg-random.org/download.html), but the initialization and equations below are the self-contained normative Piccle definition.

Initialize the generator as follows:

```text
state = 0
increment = 1442695040888963407
pcg32_next()                         // discard
state = state + seed
pcg32_next()                         // discard
```

Each `pcg32_next()` performs:

```text
old_state = state
state = old_state × 6364136223846793005 + increment
xorshifted = uint32(((old_state >> 18) xor old_state) >> 27)
rotation = uint32(old_state >> 59)
u = (xorshifted >> rotation)
    or (xorshifted << ((-rotation) and 31))
```

Convert each unsigned result `u` to one binary64 raw sample:

```text
x = 2 × (u / 4294967296) - 1
```

The resulting discrete uniform values lie in `[-1, 1)`. The first non-discarded result supplies sample frame zero. Engines MUST NOT substitute a platform random-number generator.

## Character filters

All filters below use binary64 control calculations, a zero initial state, and the canonical or engine render sample rate `sample_rate`.

### `neutral`

`neutral` uses the raw PCG32 sample `x[n]` without spectral filtering.

### `soft`

`soft` is a first-order lowpass with a 400 Hz corner. It is approximately flat below the corner and approaches a −6 dB/octave slope above it:

```text
a = exp(-2π × 400 / sample_rate)
y[n] = a × y[n-1] + (1-a) × x[n]
y[-1] = 0
```

### `sharp`

`sharp` is a first-order highpass with a 2 kHz corner. It approaches a +6 dB/octave slope below the corner and is approximately flat above it:

```text
a = exp(-2π × 2000 / sample_rate)
y[n] = a × (y[n-1] + x[n] - x[n-1])
y[-1] = 0
x[-1] = 0
```

This replaces the earlier unrealizable requirement that the spectrum continue rising above 2 kHz.

## RMS normalization

The stationary expected RMS after character shaping is `0.25`. Apply a constant character gain; do not scan or pre-render the layer.

The raw uniform stream has variance `1/3`. Let `variance` be:

```text
neutral: 1/3
soft:    (1/3) × (1-a) / (1+a)
sharp:   (1/3) × 2a² / (1+a)
```

Then emit:

```text
source_sample = y × (0.25 / sqrt(variance))
```

For `neutral`, use `y = x`. Short layers may differ from the stationary target because the character filter starts from zero. That deterministic transient is part of the source semantics.

## Channel behavior

Noise produces one mono channel. The layer's equal-power `balance` stage converts it to stereo after filtering and volume shaping; see [Output](08-output.md).

## Native-rate equivalence

Canonical 48 kHz renders are deterministic for a given character and seed. A native-rate engine uses the same PCG32 sequence and recomputes character coefficients at its render sample rate. Cross-rate sample equality is not required.

For implementation quality checks, a noise layer long enough to reach stationary behavior SHOULD measure within 10% of RMS `0.25`. Its spectrum SHOULD follow the stated first-order response within 3 dB per one-third-octave band, excluding bands whose upper edge reaches Nyquist.
