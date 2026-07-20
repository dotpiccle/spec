# Cookbook

This non-normative how-to guide contains recipes for common one-shot UI sounds: clicks, notifications, chimes, whooshes, errors, reverb, and echo. Normative field behavior lives in chapters 00 through 11 and 14.

## Make a button click

Start with **noise**. A button click is a short burst of hiss -- there is no pitch, just a crisp tick.

1. Create a noise layer with `character: "neutral"`.
2. Give it a short `duration_ms` (about 60-100 ms).
3. Shape the volume so it punches quickly and fades out: a short `fade_in` (1 ms), a peak level (0.5), and a `fade_out` (around 40-60 ms).
4. Add a `highpass` filter to brighten it and remove low-end rumble.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "click",
      "duration_ms": 80,
      "source": {
        "type": "noise",
        "character": "neutral",
        "seed": 7
      },
      "volume": {
        "fade_in": { "ms": 1 },
        "fade_out": { "ms": 50 },
        "levels": [{ "level": 0.5 }]
      },
      "filters": [
        {
          "type": "highpass",
          "frequencies": [{ "hz": 2000 }],
          "resonance": 0
        }
      ]
    }
  ]
}
```

_A short noise burst, brightened with a highpass filter -- the everyday button click._

## Make a notification bell

Start with a **tone**. A notification bell is a pitched sound, like a doorbell ding.

1. Create a tone layer with `wave: "sine"`.
2. Set the pitch to something pleasant, like A5 (880 Hz).
3. Shape the volume like a bell: a quick rise to a peak, then an exponential decay to a lower sustain level, then a fade-out.
4. Add reverb for warmth using a spatial_effect.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "bell",
      "duration_ms": 400,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 880 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 2 },
        "fade_out": { "ms": 200, "curve": "exponential" },
        "levels": [
          {
            "level": 0.5,
            "transition_ms": 30,
            "transition_curve": "exponential"
          },
          { "level": 0.08 }
        ]
      }
    }
  ],
  "spatial_effects": [
    { "type": "reverb", "amount": 0.2, "tail_ms": 300, "soften_hz": 4000 }
  ]
}
```

_A single soft bell at A5 (880 Hz) with gentle reverb._

## Make a success chime

Use multiple **tone** layers offset in time. A success sound is often three rising notes, like a little melody.

1. Create three sine tone layers, each at a different pitch.
2. Offset their start times so they play one after another (e.g., 0 ms, 60 ms, 120 ms).
3. Give each a bell-like volume shape.
4. Add reverb for a polished finish using a spatial_effect.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "note-1",
      "start_ms": 0,
      "duration_ms": 350,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 523.25 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 2 },
        "fade_out": { "ms": 250 },
        "levels": [
          {
            "level": 0.4,
            "transition_ms": 40,
            "transition_curve": "exponential"
          },
          { "level": 0.05 }
        ]
      }
    },
    {
      "id": "note-2",
      "start_ms": 60,
      "duration_ms": 350,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 659.25 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 2 },
        "fade_out": { "ms": 250 },
        "levels": [
          {
            "level": 0.4,
            "transition_ms": 40,
            "transition_curve": "exponential"
          },
          { "level": 0.05 }
        ]
      }
    },
    {
      "id": "note-3",
      "start_ms": 120,
      "duration_ms": 350,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 783.99 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 2 },
        "fade_out": { "ms": 250 },
        "levels": [
          {
            "level": 0.4,
            "transition_ms": 40,
            "transition_curve": "exponential"
          },
          { "level": 0.05 }
        ]
      }
    }
  ],
  "spatial_effects": [
    { "type": "reverb", "amount": 0.2, "tail_ms": 300, "soften_hz": 5000 }
  ]
}
```

_Three rising sine tones with a short reverb -- the classic "done!" confirmation._

## Make a whoosh

Use **noise** with a **filter sweep**. A whoosh is noise that opens up from dull to crisp.

1. Create a noise layer with `character: "neutral"`.
2. Add a `lowpass` filter that sweeps from a low cutoff to a high cutoff.
3. Use `transition_curve: "exponential"` so the sweep sounds natural.
4. Shape the volume with a slow fade-in and fade-out.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "whoosh",
      "duration_ms": 200,
      "source": {
        "type": "noise",
        "character": "neutral"
      },
      "volume": {
        "fade_in": { "ms": 20 },
        "fade_out": { "ms": 30 },
        "levels": [{ "level": 0.3 }]
      },
      "filters": [
        {
          "type": "lowpass",
          "frequencies": [
            {
              "hz": 200,
              "transition_ms": 150,
              "transition_curve": "exponential"
            },
            { "hz": 8000 }
          ],
          "resonance": 0
        }
      ]
    }
  ]
}
```

_A brightening whoosh -- noise that opens up from dull to crisp._

## Make an error sound

Use **descending tones**. An error sound signals something went wrong -- it often falls in pitch.

1. Create triangle wave tones (warmer, less harsh than sine for errors).
2. Use a `lowpass` filter to soften the sound.
3. Have the pitch fall from higher to lower.
4. Offset two layers so the second tone descends after the first.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "thud",
      "start_ms": 0,
      "duration_ms": 100,
      "source": {
        "type": "noise",
        "character": "neutral"
      },
      "volume": {
        "fade_in": { "ms": 1 },
        "fade_out": { "ms": 50 },
        "levels": [{ "level": 0.3 }]
      },
      "filters": [
        {
          "type": "bandpass",
          "frequencies": [{ "hz": 1500 }],
          "resonance": 0.1
        }
      ]
    },
    {
      "id": "tone-1",
      "start_ms": 80,
      "duration_ms": 200,
      "source": {
        "type": "tone",
        "wave": "triangle",
        "pitch": {
          "frequencies": [
            {
              "hz": 500,
              "transition_ms": 100,
              "transition_curve": "exponential"
            },
            { "hz": 300 }
          ]
        }
      },
      "volume": {
        "fade_in": { "ms": 3 },
        "fade_out": { "ms": 100 },
        "levels": [
          {
            "level": 0.3,
            "transition_ms": 20,
            "transition_curve": "exponential"
          },
          { "level": 0.08 }
        ]
      }
    },
    {
      "id": "tone-2",
      "start_ms": 180,
      "duration_ms": 250,
      "source": {
        "type": "tone",
        "wave": "triangle",
        "pitch": {
          "frequencies": [
            {
              "hz": 400,
              "transition_ms": 120,
              "transition_curve": "exponential"
            },
            { "hz": 200 }
          ]
        }
      },
      "volume": {
        "fade_in": { "ms": 3 },
        "fade_out": { "ms": 150 },
        "levels": [
          {
            "level": 0.25,
            "transition_ms": 20,
            "transition_curve": "exponential"
          },
          { "level": 0.05 }
        ]
      }
    }
  ]
}
```

_A muted tick followed by two falling tones -- a calm, recoverable error._


## Make a soft echo (cuelume-style shimmer)

Use a single **echo** tap. A soft echo adds space without calling attention to itself — think of the shimmer after a gentle UI cue.

1. Create a tone layer with a pleasant mid-range pitch.
2. Set a short `fade_in` and a moderate `fade_out`.
3. Add a single `echo` spatial effect with a short delay, low feedback, and damping.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "shimmer",
      "duration_ms": 200,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 660 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 5 },
        "fade_out": { "ms": 100 },
        "levels": [{ "level": 0.4 }]
      }
    }
  ],
  "spatial_effects": [
    {
      "type": "echo",
      "delay_ms": 120,
      "feedback": 0.25,
      "wet_gain": 0.18,
      "damp_hz": 4000
    }
  ]
}
```

_A soft, shimmering echo behind a single tone — a common cuelume preset._

## Make a slap-back echo

A slap-back echo is a single distinct repeat. Use zero feedback to prevent further repeats.

1. Create a noise layer with a short burst (or a tone).
2. Brighten it with a highpass filter.
3. Apply a slap-back echo: a very short delay with zero feedback.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "slap",
      "duration_ms": 100,
      "source": {
        "type": "noise",
        "character": "neutral",
        "seed": 42
      },
      "volume": {
        "fade_in": { "ms": 1 },
        "fade_out": { "ms": 30 },
        "levels": [{ "level": 0.4 }]
      },
      "filters": [
        {
          "type": "highpass",
          "frequencies": [{ "hz": 1000 }],
          "resonance": 0
        }
      ]
    }
  ],
  "spatial_effects": [
    {
      "type": "echo",
      "delay_ms": 80,
      "feedback": 0,
      "wet_gain": 0.4,
      "damp_hz": 8000
    }
  ]
}
```

_A short noise burst followed by a single slap-back repeat._

## Stack reverb onto an echo

Combine both spatial effects for a richer sound. The echo adds rhythmic repeats while the reverb fills in the space between them.

1. Create a tone layer with a bell-like volume shape.
2. Add an echo with moderate feedback.
3. Add a reverb after the echo for a smooth tail.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "stacked",
      "duration_ms": 300,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 440 }]
        }
      },
      "volume": {
        "fade_in": { "ms": 2 },
        "fade_out": { "ms": 150 },
        "levels": [
          {
            "level": 0.5,
            "transition_ms": 30,
            "transition_curve": "exponential"
          },
          { "level": 0.08 }
        ]
      }
    }
  ],
  "spatial_effects": [
    {
      "type": "echo",
      "delay_ms": 100,
      "feedback": 0.2,
      "wet_gain": 0.2,
      "damp_hz": 5000
    },
    {
      "type": "reverb",
      "amount": 0.15,
      "tail_ms": 400,
      "soften_hz": 6000
    }
  ]
}
```

_A layered tone with echo and reverb working together — echo provides the rhythm, reverb provides the space._