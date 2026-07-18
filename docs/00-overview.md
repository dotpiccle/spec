# Piccle v1 Overview

Piccle is an open, declarative format for describing short, one-shot procedural UI sounds such as feedback, transitions, notifications, confirmations, and errors. This chapter is part of the normative specification for version 1.0.

## Mission

Enable developers, designers, and AI agents to create high-quality, low-latency, lightweight, and expressive micro-audio using structured data.

Piccle aims to become the "Lottie for audio": a portable and expressive format for audio animations and micro-interactions.

A Piccle asset should be:

- Small enough to ship with an application.
- Easy for humans to read and edit.
- Easy for AI systems to generate reliably.
- Deterministic enough for compatible engines to interpret consistently.
- Expressive enough to create polished UI audio without prerecorded WAV or MP3 assets.
- Safe and efficient enough for real-time playback on mobile devices.

## v1 feature summary

| Feature            | Description                                                                                                                  |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| Layers (1 or more) | Each layer is an independent sound generator with its own volume, balance, and filter chain.                                 |
| Tone source        | A pitched hum with a waveform shape (sine, triangle, square, saw) and a pitch contour.                                       |
| Noise source       | A pitchless hiss with a perceptual character (soft, neutral, sharp).                                                         |
| Pitch contour      | An always-array of frequency points with hold time, transition time, and transition curve.                                   |
| Volume contour     | A shorthand number (constant level) or an N-level object with fade-in, fade-out, and per-segment timing.                     |
| Filter chain       | Lowpass, highpass, or bandpass filters in series, each with its own frequency contour and resonance.                         |
| Balance            | Stereo position from -1 (left) to 1 (right).                                                                                 |
| Reverb             | Optional whole-sound reverb with amount, tail length, and damping frequency.                                                 |
| Output shaping     | Whole-sound volume, fade-in, and fade-out.                                                                                   |
| Safety             | Built-in hard clipping, Nyquist-aware frequency handling, validation before allocation, and engine-declared resource limits. |

## v1 scope boundary

Piccle v1 describes finite, one-shot assets. It does not define looping, continuous progress playback, gesture-controlled parameters, runtime theming inputs, modulation, or dynamic interaction with a playing sound. A host application may replay an asset, but seamless looping and host parameters are outside the v1 format contract.

These deferred capabilities require a future format proposal. They are not implied by the `loading` example, which is a one-shot “work started” cue.

## Piccle in one minute

A Piccle sound is a short list of **layers** -- like one instrument per layer in a tiny band. For each layer you say three things:

1. **What it is** (`source`) -- the raw sound this layer makes. It is either a `tone` (a pitched hum -- think a dial tone, doorbell ding, or microwave beep) or `noise` (a pitchless hiss -- think TV static, tape hiss, or a whisper). For a `tone`, the `source` also includes its **pitch** -- a frequency in Hz (like 1046.5 for a C6 bell), or a `frequencies` array that glides from one pitch to another (like a drop of water falling). So the source is a _complete_ description of the raw sound: "a sine tone at 1046.5 Hz" or "soft noise."

2. **Its volume** -- how loud it is, and how that loudness changes over time. For a steady sound, just a number (`"volume": 0.4`). For a sound that changes loudness (a bell that strikes then rings, a click that punches then fades), a small object with a list of levels and transitions: how it fades in, what levels it moves through, and how it fades out.

3. **Optional filters** -- to soften it (keep the lows) or brighten it (keep the highs).

The engine mixes all layers together, optionally adds a little **reverb** for a sense of space, and plays the result. That is the whole format.

## Glossary

| Term             | Meaning                                                                                                                           |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Layer            | One sound generator within a document. Each layer has a source, volume, balance, and optional filters.                            |
| Source           | The raw sound a layer makes -- either a tone (pitched) or noise (pitchless).                                                      |
| Tone             | A pitched sound with a recognizable frequency, like a beep or bell.                                                               |
| Noise            | A pitchless sound, like static or a whisper.                                                                                      |
| Wave             | The shape of a tone's vibration. Piccle supports sine, triangle, square, and saw.                                                 |
| Character        | The spectral quality of noise: soft (muffled), neutral (balanced), or sharp (bright).                                             |
| Frequency (Hz)   | How high or low a pitch sounds. Higher Hz = higher pitch. 440 Hz is the A above middle C.                                         |
| Volume           | How loud a sound is, from 0 (silent) to 1 (full).                                                                                 |
| Balance          | Where a sound sits in stereo: -1 is left, 0 is center, 1 is right.                                                                |
| Contour          | How a value (like volume or pitch) changes over time, described as a sequence of target values with hold and transition timing.   |
| Filter           | A processor that removes or boosts certain frequencies. Lowpass keeps lows, highpass keeps highs, bandpass keeps a focused range. |
| Resonance        | How much a filter rings at its target frequency, like a struck bell.                                                              |
| Reverb           | A sense of space around the sound, like playing in a small room.                                                                  |
| Transition curve | The interpolation shape between contour targets: linear, exponential, easeIn, easeOut, or easeInOut.                              |
| Offset cents     | A tiny pitch shift measured in cents (100 cents = 1 semitone). Two tones at slightly different cents create a warm chorus effect. |
| Attack click     | A brief, harsh click that happens when a sound starts or stops abruptly. Piccle's default fade-out of 5 ms prevents this.         |
