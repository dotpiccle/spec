# Sources

The `source` field answers one question: _what kind of sound does this layer make?_ It is the raw starting sound, before volume and filters are applied. Think of it as step one of building a layer: "what raw sound am I starting with?"

A `source` is always one of two structurally-distinct variants -- a `tone` (a pitched hum) or `noise` (a pitchless hiss). The structure itself enforces which fields belong where:

| `source.type` | What it is                                       | Fields inside `source`                    |
| ------------- | ------------------------------------------------ | ----------------------------------------- |
| `tone`        | A pitched hum (doorbell ding, dial tone, beep)   | `wave` (required), `pitch` (required)     |
| `noise`       | A pitchless hiss (TV static, tape hiss, whisper) | `character` (required). No `pitch` field. |

## Tone: a pitched hum

A **tone** is a sound with a recognizable _pitch_ -- a note you could hum or whistle back. It sounds "high" or "low." Real-world examples:

- A **dial tone** on an old phone (that steady hum when you pick up).
- A **doorbell** going _ding_.
- A **tuning fork** after you strike it.
- The **beep** a microwave makes when it is done.
- A single **piano note**.

In Piccle you set a tone's pitch with `hz` (like 1046.5 for C6, where higher numbers = higher-pitched). See [Pitch](04-pitch.md) for a quick-reference table of common notes and their Hz values.

### Wave shapes

The `wave` field selects the shape of the tone's vibration. Each shape sounds different:

```
sine:       ~                Smooth, soft, pure. Like a
           / \               tuning fork or a dial tone.
          /   \
         /     \

triangle:  /\                Warmer than sine, slightly
          /  \               brighter. Like a gentle
         /    \__            flute or vibraphone.

square:   +----+             Buzzy and hollow. Like a
          |    |             video game beep or a
          +----+             cheap alarm clock.

saw:        /|              Bright and buzzy, with
           / |              lots of high frequencies.
          /  |              Like a violin or a
         /   |              synth lead.
```

| Wave       | Sound character                | Use for                                       |
| ---------- | ------------------------------ | --------------------------------------------- |
| `sine`     | Smooth, pure, soft             | Bells, beeps, notifications, dial tones       |
| `triangle` | Warmer, slightly brighter      | Mellow tones, soft bells, gentle cues         |
| `square`   | Buzzy, hollow, video-game-like | Retro sounds, alarms, attention-getting cues  |
| `saw`      | Bright, buzzy, rich            | Rich tones, synth-like sounds, prominent cues |

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

These finite series define target harmonic amplitude, sign, and phase. Their sampled peak need not reach `1`, and truncating a discontinuous waveform's series may produce a peak above `1`. Engines MUST NOT renormalize the retained harmonics independently because doing so would change their published amplitudes.

An engine MAY use additive synthesis, a band-limited wavetable, polyBLEP, oversampling, or another method. For steady canonical-profile tests, each target harmonic at or above −60 dBFS MUST be within ±1 dB of its reference amplitude and within ±1 degree of its reference phase. DC MUST remain below −80 dBFS. Every non-target or aliased spectral component MUST remain below −60 dBFS. Exact sample equality between permitted implementations is not required.

Measure with a rectangular `N = 48000` frame window beginning at oscillator frame zero at each coherent frequency `375`, `1000`, `3000`, `8000`, and `16000` Hz. These frequencies contain an integer number of cycles in one canonical-profile second. Do not apply layer volume, filters, balance, reverb, root volume, or clipping during the measurement.

For measured source samples `x[n]`, define the complex coefficient for bin `k`, where `1 <= k < N/2`, as:

```text
C[k] = (2/N) × Σ(n = 0 .. N-1) x[n] × exp(-i × 2πkn/N)
amplitude[k] = |C[k]|
phase_from_sine[k] = wrap_to_pi(arg(C[k]) + π/2)
DC = abs((1/N) × Σ(n = 0 .. N-1) x[n])
```

Use `20 × log10(amplitude)` for harmonic and unintended-component dBFS values and `20 × log10(DC)` for DC dBFS. A zero value is negative infinity dBFS. A positive sine-series coefficient has reference phase `0`; a negative coefficient has reference phase `π`. Measure phase error as the smallest wrapped angular difference. Evaluate every bin from `1` through `N/2 - 1`; target bins are the harmonic frequencies retained by `H`, and every other bin is unintended.

During pitch motion, engines MUST preserve the phase integral and MUST suppress components at or above Nyquist. The steady-frequency spectral tolerances do not require engines to switch harmonic sets with one particular algorithm.

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

_A steady sine tone at C6 (1046.5 Hz) -- like a doorbell ding._

For pitch glides (like a slide whistle or falling droplet), the `frequencies` array has multiple entries:

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

_A sine tone gliding from 620 Hz down to 430 Hz -- like a drop of water falling._

## Noise: a pitchless hiss

A **noise** is the opposite of a tone: a sound with _no pitch_. It is a hiss or rush you cannot hum along to because there is no note to grab onto. Real-world examples:

- **TV static** (that _shhhhhh_ on an empty channel).
- **Tape hiss** on an old cassette.
- **The ocean** heard through a seashell.
- A **whisper** (the breathy _hhh_ before you form words).
- A burst of **compressed air**.

In Piccle, instead of a pitch, you give noise a **character** and may select a deterministic **seed**:

| Character | Sounds like                       | Use for                                              |
| --------- | --------------------------------- | ---------------------------------------------------- |
| `soft`    | Dull, muffled, rumbly hiss        | Soft clicks, background texture, subtle impacts      |
| `neutral` | Balanced, flat hiss (white noise) | Clicks, ticks, general-purpose noise                 |
| `sharp`   | Bright, crispy, sizzly hiss       | Clicks that cut through, paper sounds, crisp impacts |

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

_A neutral (balanced) hiss -- like TV static used as the base for a button click._

Noise is generated as a deterministic PCG32 stream, normalized to a standard loudness, and treated as mono. Two conforming canonical-profile renders using the same character and seed therefore generate the same source stream. See [Noise and Determinism](09-noise-and-determinism.md) for the exact algorithm.

## Why Piccle has both

Almost every UI sound is a _combination_ of tone and noise layers:

- A **button click** is mostly _noise_ (a short burst of hiss, filtered to sound "clicky") -- no pitch, just a crisp tick.
- A **notification bell** is mostly _tone_ (a clear pitched _ding_ at a specific note) -- but you might add a tiny bit of noise underneath for texture so it does not sound too synthetic.
- A **success sound** is often _tones_ (two or three rising notes, like a little melody).
- A **whoosh transition** is _noise_ that gets brighter over time (a filter sweeps up, making the hiss go from dull to crisp).

**One-sentence mental model:** _`tone` = a pitched hum (a beep or bell); `noise` = a pitchless hiss (static or a whisper). Most UI sounds are a few layers of these mixed together._

## Contrast table

|                       | `tone`                                       | `noise`                                        |
| --------------------- | -------------------------------------------- | ---------------------------------------------- |
| Example               | Doorbell ding, dial tone, microwave beep     | TV static, tape hiss, a whisper                |
| Has a pitch?          | Yes -- sounds high or low                    | No -- just hiss                                |
| Can you hum it?       | Yes                                          | No                                             |
| In Piccle, you set... | `pitch` (a frequency in Hz)                  | `character` (soft / neutral / sharp)           |
| Use it for            | Bells, success chimes, notifications, glides | Clicks, ticks, whooshes, paper flicks, impacts |
