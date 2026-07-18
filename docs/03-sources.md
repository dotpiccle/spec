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
phase[n + 1] = (phase[n] + 2π × frequency_hz[n] / sample_rate) mod 2π
```

The ideal, peak-normalized waveforms are:

```text
sine(phase)     = sin(phase)
square(phase)   =  1 when 0 <= phase < π, otherwise -1
saw(phase)      = phase / π, for -π < phase <= π
triangle(phase) = (2 / π) × asin(sin(phase))
```

The phase is interpreted in `(-π, π]` for the `saw` formula. All waveforms have a fundamental phase that crosses zero with positive slope at the layer start, except that the discontinuous square waveform takes the value `1` at phase zero.

An engine MUST prevent harmonics at or above the Nyquist frequency from folding into the audible band. It MAY use a band-limited wavetable, additive synthesis, polyBLEP, oversampling, or another anti-aliasing technique. For a steady pitch measured over at least ten complete cycles, the mono source peak MUST be between `0.99` and `1`, its mean MUST be within `0.001` of zero, and aliased components MUST remain below −60 dBFS in the canonical profile. The fundamental frequency and phase MUST follow the equations above. Exact sample equality between different anti-aliasing implementations is not required.

Pitch and phase calculations use the canonical precision and frame timing defined in [Engine Safety and the Canonical Render Profile](11-engine-safety.md).

> **Non-normative origin:** The ideal waveform phase conventions are aligned with the [W3C Web Audio oscillator model](https://www.w3.org/TR/webaudio-1.1/). The equations and tolerances in this chapter remain the complete Piccle requirement.

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
