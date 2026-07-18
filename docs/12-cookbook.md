# Cookbook

This non-normative how-to guide contains recipes for common one-shot UI sounds. Normative field behavior lives in chapters 00 through 11 and 14.

## Make a button click

Start with **noise**. A button click is a short burst of hiss -- there is no pitch, just a crisp tick.

1. Create a noise layer with `character: "neutral"`.
2. Give it a short `duration_ms` (about 60-100 ms).
3. Shape the volume so it punches quickly and fades out: a short `fade_in_ms` (1 ms), a peak level (0.5), and a `fade_out_ms` (around 40-60 ms).
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
        "fade_in_ms": 1,
        "fade_out_ms": 50,
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
  ],
  "fade_out_ms": 5
}
```

_A short noise burst, brightened with a highpass filter -- the everyday button click._

## Make a notification bell

Start with a **tone**. A notification bell is a pitched sound, like a doorbell ding.

1. Create a tone layer with `wave: "sine"`.
2. Set the pitch to something pleasant, like A5 (880 Hz).
3. Shape the volume like a bell: a quick rise to a peak, then an exponential decay to a lower sustain level, then a fade-out.
4. Add reverb for warmth.

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
        "fade_in_ms": 2,
        "fade_out_ms": 200,
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
  "reverb": {
    "amount": 0.25,
    "tail_ms": 350,
    "soften_hz": 6000
  }
}
```

_A single soft bell at A5 (880 Hz) with gentle reverb._

## Make a success chime

Use multiple **tone** layers offset in time. A success sound is often three rising notes, like a little melody.

1. Create three sine tone layers, each at a different pitch.
2. Offset their start times so they play one after another (e.g., 0 ms, 60 ms, 120 ms).
3. Give each a bell-like volume shape.
4. Add reverb for a polished finish.

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
        "fade_in_ms": 2,
        "fade_out_ms": 250,
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
        "fade_in_ms": 2,
        "fade_out_ms": 250,
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
        "fade_in_ms": 2,
        "fade_out_ms": 250,
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
  "reverb": {
    "amount": 0.2,
    "tail_ms": 300,
    "soften_hz": 5000
  }
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
        "fade_in_ms": 20,
        "fade_out_ms": 30,
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
        "fade_in_ms": 1,
        "fade_out_ms": 50,
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
        "fade_in_ms": 3,
        "fade_out_ms": 100,
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
        "fade_in_ms": 3,
        "fade_out_ms": 150,
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
