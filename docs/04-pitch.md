# Pitch

Pitch lives inside a tone source (see [Sources](03-sources.md)). It describes how the pitch of a tone changes over time using a `frequencies` array.

Pitch is always a `frequencies` array -- there are no static shortcuts. A steady tone is a one-entry array; a glide is two entries; a multi-point contour is three or more.

## Structure

```json
"pitch": {
  "frequencies": [
    { "hz": 1046.5 }
  ],
  "offset_cents": 0
}
```

_Target fields inside `pitch`:_

| Field          | Type    | Default | Required | Description                                                                                            |
| -------------- | ------- | ------- | -------- | ------------------------------------------------------------------------------------------------------ |
| `frequencies`  | array   | --      | **Yes**  | One or more entries describing pitch over time. Each entry has the fields below.                       |
| `offset_cents` | integer | 0       | No       | Small pitch offset in cents. -1200 to 1200. 100 cents = 1 semitone. Added to every entry's `hz` value. |

_Fields inside each `frequencies[]` entry:_

| Field              | Type    | Default  | Required | Description                                                                            |
| ------------------ | ------- | -------- | -------- | -------------------------------------------------------------------------------------- |
| `hz`               | number  | --       | **Yes**  | Target pitch at this point. 20-20000 Hz. Higher = higher pitch.                        |
| `hold_ms`          | integer | 0        | No       | How long to hold at this pitch before transitioning to the next. 0 ms or more.         |
| `transition_ms`    | integer | 0        | No       | How long to move from this pitch to the next. 0 ms or more. Ignored on the last entry. |
| `transition_curve` | string  | `linear` | No       | Shape of the transition. See curves below. Ignored on the last entry.                  |

## Static pitch (one entry)

The most common case -- a single steady pitch, like a doorbell ding or notification beep:

```json
"pitch": {
  "frequencies": [
    { "hz": 1046.5 }
  ]
}
```

_A steady tone at 1046.5 Hz (C6) -- a doorbell ding._

## Simple glide (two entries)

A pitch that moves from one frequency to another, like a slide whistle:

```json
"pitch": {
  "frequencies": [
    { "hz": 620, "transition_ms": 50, "transition_curve": "exponential" },
    { "hz": 430 }
  ]
}
```

_A pitch gliding from 620 Hz to 430 Hz over 50 ms with an exponential curve -- like a droplet falling._

The exponential curve is natural for pitch drops. See [Transition Curves](10-curves.md) for the exact formula and behavior.

## Multi-point contour (three or more entries)

For complex pitch shapes, like a droplet that bounces or an error sound that goes up then down:

```json
"pitch": {
  "frequencies": [
    { "hz": 620, "hold_ms": 0, "transition_ms": 50, "transition_curve": "exponential" },
    { "hz": 430, "hold_ms": 0, "transition_ms": 30, "transition_curve": "linear" },
    { "hz": 310 }
  ]
}
```

_A three-point pitch contour: 620 Hz drops to 430 Hz (exponential), then to 310 Hz (linear). The hold and transition fields on the last entry are ignored -- the sound holds at 310 Hz until the layer ends._

## Timing rules for pitch entries

Pitch entries follow the standard contour entry timing rules defined in [Conventions](02-conventions.md). The 20 Hz minimum frequency keeps all exponential inputs valid. An exponential target equal to the start frequency produces no change.

## Offset cents (chorus and detuning)

The `offset_cents` field adds a small pitch shift to every entry in the `frequencies` array. It is measured in **cents**, where 100 cents = 1 semitone (one piano key).

Use `offset_cents` to create chorus or beating effects: two tone layers at the same pitch but with different offsets produce a warm, shimmering sound.

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "left",
      "duration_ms": 800,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 528 }],
          "offset_cents": 0
        }
      }
    },
    {
      "id": "right",
      "duration_ms": 800,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 528 }],
          "offset_cents": 12
        }
      }
    }
  ]
}
```

_Two identical sine tones at 528 Hz, one shifted up by 12 cents -- creates a warm, drifting chorus effect._

The cents-to-frequency formula is: `freq_with_offset = hz * 2^(offset_cents / 1200)`.

## Note-to-Hz quick reference (non-normative)

For convenience, here are common musical notes and their frequencies. Piccle uses Hz everywhere (not note names), but this table helps if you think in notes.

| Note          | Hz      |
| ------------- | ------- |
| C4 (middle C) | 261.63  |
| D4            | 293.66  |
| E4            | 329.63  |
| F4            | 349.23  |
| G4            | 392.00  |
| A4 (tuning A) | 440.00  |
| B4            | 493.88  |
| C5            | 523.25  |
| D5            | 587.33  |
| E5            | 659.25  |
| F5            | 698.46  |
| G5            | 783.99  |
| A5            | 880.00  |
| C6            | 1046.50 |
| E6            | 1318.51 |
| A6            | 1760.00 |
| C7            | 2093.00 |

Each octave up doubles the frequency. To find any note frequency: `freq = 440 * 2^((note_semitones_from_A4) / 12)`.
