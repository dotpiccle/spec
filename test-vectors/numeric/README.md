# Non-normative numeric aids

These values help engine authors catch transcription and boundary mistakes without embedding a reference engine or PCM output. The normative formulas remain in `docs/`; these aids alone do not prove audible conformance.

`dsp-values.json` covers PCG32 initialization, transition-curve checkpoints, oscillator Fourier coefficients and DFT convention, a canonical biquad coefficient set, equal-power balance and mono adaptation, absolute timing boundaries, pitch transformation order, canonical mixing order, render-profile frequency clamping, and reverb tail boundaries, terminal windows, and baseline generator configuration. `reverb-reference-irs/` contains the canonical reference IR render fixtures for the reverb perceptual-equivalence gate.
