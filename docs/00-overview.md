# Piccle v1 Overview

Piccle is a declarative control format for finite procedural UI-audio signals. A document defines source excitation, control contours, per-layer filtering and gain, stereo placement, summation, optional parallel spatial processing, master gain, and output limiting. This chapter is normative.

## Audience and documentation boundary

This specification targets audio engineers, DSP engineers, maintainers of [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs), validation-tool authors, and automated systems that require the complete format and execution contract. It assumes familiarity with discrete-time signals, sample frames, oscillators, spectra, envelopes, digital filters, gain staging, stereo processing, impulse responses, and numerical precision.

Throughout the normative chapters, **the engine** means the official Piccle implementation in `dotpiccle/engine-rs`. Normative engine statements define its externally observable parsing, validation, scheduling, DSP, and output behavior. Private Rust types, module boundaries, threading, and platform I/O remain implementation details unless they affect that behavior.

Introductory sound-design tutorials and simplified user documentation are outside this repository. They may reference this specification but do not define Piccle behavior.

## Format objectives

A Piccle document is intended to be:

- compact enough for application distribution and asset pipelines;
- structurally explicit enough for deterministic parsing and automated generation;
- portable across render architectures and platform audio APIs;
- deterministic where exact equivalence is practical and tolerance-bounded elsewhere;
- expressive enough for short layered synthetic UI cues; and
- bounded for validation and preflight resource analysis.

## V1 signal model

| Component | Technical role |
| --- | --- |
| Layers | One or more independently scheduled mono signal generators with per-layer control and processing state. |
| Tone source | Band-limited periodic oscillator using sine, triangle, square, or saw harmonic targets and a time-varying fundamental-frequency contour. |
| Noise source | Deterministic PCG32 excitation with `neutral`, lowpass-shaped `soft`, or highpass-shaped `sharp` spectral character. |
| Pitch contour | Ordered frequency targets with hold duration, transition duration, interpolation curve, and optional cents offset. |
| Volume contour | Scalar-gain shorthand or a multi-segment amplitude envelope with independently curved fade-in and fade-out stages. |
| Filter chain | Serial second-order lowpass, highpass, or constant-peak-gain bandpass biquads with time-varying cutoff and resonance-to-Q mapping. |
| Balance | Equal-power mono-to-stereo panning over `[-1, 1]`. |
| Spatial effects | Parallel document-level reverb and echo wet branches receiving the same dry stereo mix. |
| Output stage | Post-effect `master_volume_level`, hard clipping to `[-1, 1]`, canonical stereo emission, then non-normative platform adaptation. |

The normative signal path is defined in [Output](08-output.md). Source and filter state are scoped to layer lifetime; spatial-effect state is scoped to the document output timeline.

## V1 scope boundary

Piccle v1 describes finite, one-shot assets. It does not define looping, continuous progress playback, gesture-controlled parameters, host-supplied theming inputs, modulation, runtime parameter automation, speech synthesis, or recorded-sample playback. A host may retrigger an asset, but seamless looping and host-driven control are outside the v1 contract.

These capabilities require a future format proposal. The `loading` example is a one-shot onset cue and does not imply a loop primitive.

## Terminology

| Term | Definition |
| --- | --- |
| Layer | Independently scheduled mono source plus its filter chain, amplitude envelope, and stereo balance. |
| Source | Deterministic tone oscillator or noise excitation generator. |
| Fundamental frequency | Instantaneous oscillator frequency after contour evaluation, cents offset, and render-profile clamping. |
| Partial | Sinusoidal component of a band-limited periodic waveform at an integer multiple of the fundamental. |
| Contour | Piecewise control trajectory composed of target values, holds, transitions, and interpolation curves. |
| Envelope | Time-varying linear-amplitude gain applied after the layer filter chain. |
| Biquad | Second-order IIR section implementing one Piccle filter entry. |
| Resonance | Normalized control mapped to filter quality factor `Q`. |
| Dry mix | Canonical stereo sum of all active post-balance layers before spatial processing. |
| Wet contribution | Output of one spatial-effect branch after its effect-specific gain, excluding the shared dry signal. |
| RT60 | Time required for backward-integrated response energy to decay by 60 dB. |
| FDN | Feedback delay network used by the normative reverb runtime. |
| Render profile | Declared sample rate, numeric mode, channel/storage mode, output bandwidth, and resource limits. |
| Boundary | Document-time instant mapped to an absolute sample frame by the active render profile. |
