# Sources

The `source` object instantiates the mono excitation stage at the head of each layer signal path. It is a closed discriminated union with two variants:

| `source.type` | Signal class | Required variant fields |
| --- | --- | --- |
| `tone` | Deterministic band-limited periodic oscillator | `wave`, `pitch` |
| `noise` | Deterministic RMS-normalized stochastic excitation | `character`; optional `seed` |

Source output is generated at the active render-profile sample rate, then processed by the layer's serial filter chain and amplitude envelope. Source state initializes at the layer's first active frame and is discarded at its declared or truncated end.

## Tone oscillator

The tone variant generates a phase-continuous periodic signal. `pitch.frequencies` defines the time-varying fundamental frequency; `pitch.offset_cents` applies a multiplicative equal-tempered frequency ratio before render-profile clamping.

### Waveform classes

| `wave` | Ideal continuous form | Retained partials in the band-limited target | Spectral slope |
| --- | --- | --- | --- |
| `sine` | Sinusoid | Fundamental only | Not applicable |
| `triangle` | Triangle wave | Odd harmonics with alternating sign | `1/k²` |
| `square` | Bipolar square wave | Odd harmonics | `1/k` |
| `saw` | Bipolar sawtooth | All integer harmonics with alternating sign | `1/k` |

The finite harmonic series below, rather than the discontinuous ideal waveform, defines canonical spectral amplitude and phase.

### Tone generation (normative)

A tone source produces one mono channel. Its oscillator starts with phase `0` at the layer's `start_ms`. At sample frame `n`, the phase advances using the current pitch after `offset_cents`:

```text
phase[0] = 0
source[n] = band_limited_wave(phase[n])
phase[n + 1] = (phase[n] + 2π × frequency_hz[n] / sample_rate) mod 2π
```

Emit `source[n]` from `phase[n]` before advancing to `phase[n+1]`. The first tone sample therefore uses phase zero. `frequency_hz[n]` is the result of the complete pitch operation order in [Pitch](04-pitch.md).

The ideal continuous waveforms are peak-normalized to `[-1, 1]`:

```text
sine(phase)     = sin(phase)
square(phase)   =  1 when 0 <= phase < π, otherwise -1
saw(phase)      = phase / π, for -π < phase <= π
triangle(phase) = (2 / π) × asin(sin(phase))
```

The phase is interpreted in `(-π, π]` for the `saw` formula. The ideal square value at its discontinuity is `1`. A rendered band-limited square instead uses the midpoint value implied by its finite harmonic series; this distinction prevents the discontinuity convention from requiring an aliased sample.

#### Band-limited harmonic target

Let `f` be the current oscillator frequency, `r` the render sample rate, and:

```text
H = { k ∈ positive integers | k × f < r / 2 }
```

Only harmonics in `H` are present in the target. The band-limited reference series are:

```text
sine(φ) = sin(φ)

square(φ) = (4/π) × Σ(k ∈ H, k odd) sin(kφ) / k

saw(φ) = (2/π) × Σ(k ∈ H) (-1)^(k+1) × sin(kφ) / k

triangle(φ) = (8/π²) × Σ(k ∈ H, k odd)
              (-1)^((k-1)/2) × sin(kφ) / k²
```

These finite series define target harmonic amplitude, sign, and phase. Their sampled peak need not reach `1`, and truncating a discontinuous waveform's series may produce a peak above `1`. The Piccle engine MUST NOT renormalize the retained harmonics independently because doing so would change their published amplitudes.

The Piccle engine oscillator realization is implementation-defined and MAY use additive synthesis, a band-limited wavetable, polyBLEP, oversampling, or another bounded method. For steady canonical-profile tests, each target harmonic at or above −60 dBFS MUST be within ±1 dB of its reference amplitude and within ±1 degree of its reference phase. DC MUST remain below −80 dBFS. Every non-target or aliased spectral component MUST remain below −60 dBFS. The realization choice does not relax these output requirements.

Measure with a rectangular `N = 48000` frame window beginning at oscillator frame zero at each coherent frequency `375`, `1000`, `3000`, `8000`, and `16000` Hz. These frequencies contain an integer number of cycles in one canonical-profile second. Do not apply layer volume, filters, balance, spatial effects, root `master_volume_level`, or clipping during the measurement.

For measured source samples `x[n]`, define the complex coefficient for bin `k`, where `1 <= k < N/2`, as:

```text
C[k] = (2/N) × Σ(n = 0 .. N-1) x[n] × exp(-i × 2πkn/N)
amplitude[k] = |C[k]|
phase_from_sine[k] = wrap_to_pi(arg(C[k]) + π/2)
DC = abs((1/N) × Σ(n = 0 .. N-1) x[n])
```

Use `20 × log10(amplitude)` for harmonic and unintended-component dBFS values and `20 × log10(DC)` for DC dBFS. A zero value is negative infinity dBFS. A positive sine-series coefficient has reference phase `0`; a negative coefficient has reference phase `π`. Measure phase error as the smallest wrapped angular difference. Evaluate every bin from `1` through `N/2 - 1`; target bins are the harmonic frequencies retained by `H`, and every other bin is unintended.

During pitch motion, the Piccle engine MUST preserve the phase integral and MUST suppress components at or above Nyquist. Harmonic-set switching is implementation-defined but MUST satisfy the steady-frequency spectral tolerances.

Pitch and phase calculations use the canonical precision and frame timing defined in [Engine Safety and the Canonical Render Profile](11-engine-safety.md).

> **Non-normative origin:** The ideal waveform phase conventions are aligned with the [W3C Web Audio oscillator model](https://www.w3.org/TR/webaudio-1.1/). The equations, harmonic targets, and tolerances in this chapter remain the complete Piccle requirement.

### Tone example

```json
"source": {
  "type": "tone",
  "wave": "sine",
  "pitch": {
    "frequencies": [
      { "hz": 1046.5 }
    ]
  }
}
```

_A stationary 1046.5 Hz sinusoidal oscillator._

For frequency modulation represented as a piecewise contour, `frequencies` contains multiple entries:

```json
"source": {
  "type": "tone",
  "wave": "sine",
  "pitch": {
    "frequencies": [
      { "hz": 620, "hold_ms": 0, "transition_ms": 50, "transition_curve": "exponential" },
      { "hz": 430 }
    ]
  }
}
```

_A sinusoidal oscillator with a 50 ms exponential fundamental-frequency transition from 620 Hz to 430 Hz._

## Noise excitation

The noise variant generates a deterministic PCG32 sequence and applies the selected character response and stationary-RMS normalization defined in [Noise and Determinism](09-noise-and-determinism.md).

| `character` | Transfer characteristic | Typical spectral application |
| --- | --- | --- |
| `soft` | First-order 400 Hz lowpass | Low-frequency-weighted transients and diffuse texture |
| `neutral` | Identity response | Broadband excitation for subsequent filter shaping |
| `sharp` | First-order 2 kHz highpass | High-frequency-weighted transients and friction-like texture |

| Field       | Type    | Default | Required | Description                                                                                 |
| ----------- | ------- | ------- | -------- | ------------------------------------------------------------------------------------------- |
| `type`      | string  | —       | **Yes**  | MUST be `noise`.                                                                            |
| `character` | string  | —       | **Yes**  | `soft`, `neutral`, or `sharp`.                                                              |
| `seed`      | integer | `0`     | No       | Selects the deterministic stream; see [Noise and Determinism](09-noise-and-determinism.md). |

### Noise example

```json
"source": {
  "type": "noise",
  "character": "neutral",
  "seed": 0
}
```

_Deterministic broadband excitation using PCG32 seed 0._

Noise is generated as a deterministic PCG32 stream, normalized to the specified RMS target, and treated as mono. Repeated canonical-profile renders using the same character and seed therefore generate the same source stream. See [Noise and Determinism](09-noise-and-determinism.md) for the exact algorithm.

## Layering implications

Tone and noise sources are orthogonal excitation primitives. A document may combine them in separate layers to construct pitched partial structures, deterministic broadband transients, filtered noise bands, or composite tonal/noise events. Cross-layer phase, timing, gain, and balance relationships are explicit; Piccle does not infer orchestration or source coupling.
