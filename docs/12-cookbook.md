# Technical Authoring Patterns

This non-normative catalog presents compact synthesis and DSP configurations for one-shot UI-audio classes. It assumes familiarity with oscillators, deterministic noise excitation, control contours, biquads, gain envelopes, and spatial processing. Normative document and engine behavior lives in chapters 00 through 11, 13, and 14.

## Broadband transient with highpass shaping

Use deterministic broadband excitation, a short amplitude envelope, and static highpass filtering:

1. Select `character: "neutral"` for a spectrally unshaped PCG32 source.
2. Limit the layer to an 80 ms transient.
3. Apply a 1 ms attack and 50 ms release at 0.5 peak linear gain.
4. Apply a 2 kHz highpass biquad with `resonance: 0`.

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

_An 80 ms broadband transient with low-frequency attenuation._

## Damped sinusoidal notification partial

Use a stationary sinusoidal oscillator, an attack-decay-sustain-release amplitude trajectory, and a low-level reverb contribution:

1. Configure a sine oscillator at 880 Hz.
2. Apply a 2 ms attack to 0.5, a 30 ms exponential decay to 0.08, and a 200 ms exponential release.
3. Add a parallel reverb branch with 0.2 wet gain, 300 ms RT60/tail, and 4 kHz wet-path lowpass.

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

_A damped 880 Hz sinusoidal partial with a diffuse wet tail._

## Staggered ascending tonal sequence

Schedule three independent sinusoidal layers with ascending fundamentals and overlapping decay envelopes:

1. Use fundamentals at 523.25, 659.25, and 783.99 Hz.
2. Set `start_ms` to 0, 60, and 120 ms respectively.
3. Use matched transient/decay envelopes to preserve timbral consistency.
4. Add one shared parallel reverb branch.

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

_Three overlapping ascending sinusoidal layers with a shared reverb contribution._

## Broadband excitation with exponential cutoff sweep

Use deterministic broadband excitation and a time-varying lowpass cutoff:

1. Select neutral noise excitation.
2. Sweep the lowpass cutoff exponentially from 200 Hz to 8 kHz over 150 ms.
3. Apply a 20 ms attack, constant 0.3 base gain, and 30 ms release.

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

_A 200 ms noise event with increasing spectral centroid._

## Descending multi-layer tonal event

Combine a bandpass-shaped noise transient with two delayed triangle-wave layers using descending exponential fundamental-frequency contours:

1. Generate a 1.5 kHz bandpass noise onset.
2. Transition the first triangle oscillator from 500 Hz to 300 Hz.
3. Transition the second from 400 Hz to 200 Hz with a 100 ms onset offset relative to the first.
4. Use exponential pitch and amplitude transitions for constant-ratio decay.

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

_A filtered-noise transient followed by two descending triangle-wave layers._


## Low-feedback short-delay echo

Apply a short low-feedback echo branch to a damped sinusoidal source:

1. Configure a 660 Hz sine layer with 5 ms attack and 100 ms release.
2. Set `delay_ms: 120` and `feedback: 0.25`.
3. Use `wet_gain: 0.18` and a 4 kHz feedback-path lowpass.

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

_A 660 Hz damped sinusoid with low-level, progressively lowpass-filtered repeats._

## Single-repeat short-delay echo

Set `feedback: 0` to produce one delayed repeat through the echo feedback-path lowpass:

1. Generate a 100 ms noise transient.
2. Apply a 1 kHz highpass section.
3. Configure an 80 ms delay, zero feedback, 0.4 wet gain, and 8 kHz damping cutoff.

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

_A highpass-shaped noise transient followed by one 80 ms delayed repeat._

## Parallel echo and reverb branches

Declare both spatial effects to add discrete lowpass-feedback repeats and a diffuse FDN response to the same dry mix. Effects are parallel; neither processes the other's output and array order is non-semantic.

1. Configure a damped 440 Hz sinusoidal layer.
2. Add an echo branch with 100 ms delay and 0.2 feedback.
3. Add a separate reverb branch with 400 ms RT60/tail.

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

_A damped sinusoid feeding independent echo and reverb wet branches._
