# Valid test vectors

Each valid fixture tests acceptance, a default behavior, or a boundary condition.

| Test vector                     | What it exercises                                                         |
| ------------------------------- | ------------------------------------------------------------------------- |
| `defaults.json`                 | All optional fields omitted — engine must apply defaults.                 |
| `engine-limit-independent.json` | Validity remains independent of engine duration limits.                   |
| `fade-defaults-equivalence.json`| Explicit linear defaults match the implicit rule.                         |
| `fade-in-exponential.json`      | Fade-in with exponential curve from silence.                              |
| `fade-out-ease-in.json`         | Fade-out with easeIn curve (settle-then-cut exit).                        |
| `fade-out-exponential.json`     | Fade-out with exponential curve to silence (natural decay tail).          |
| `all-curves.json`               | All five transition-curve values in one valid contour.                    |
| `filter-frequencies.json`       | Static bandpass filter with resonance.                                    |
| `filter-frequencies-sweep.json` | Filter frequency sweep (two entries, exponential curve).                  |
| `frequency-boundary.json`       | Pitch `hz` at 20 and 20000 (range boundaries).                            |
| `integer-number-forms.json`     | Integer fields accept mathematically integral JSON numbers such as `1.0`. |
| `layers-start-together.json`    | Two layers both omit `start_ms` — default to 0, no implicit sequencing.   |
| `long-duration.json`            | 5000 ms duration with square wave.                                        |
| `many-layers.json`              | 32 layers (valid under the no-spec-maximum rule).                         |
| `minimal.json`                  | Shortest valid document with only required fields.                        |
| `multi-filter.json`             | Two filters in series on one layer.                                       |
| `numeric-maximums.json`         | Inclusive upper bounds for bounded numeric fields.                        |
| `numeric-minimums.json`         | Inclusive lower bounds for bounded numeric fields.                        |
| `long-seeded-noise.json`        | Deterministic noise streams without buffering or looping.                 |
| `noise-determinism.json`        | Explicit seeded soft noise with a bandpass filter.                        |
| `nonadditive-tail-boundary.json`| Absolute 44.1 kHz boundaries where rounded spans are not additive.        |
| `offset-cents.json`             | Two layers with different `offset_cents` values (0 and 12).               |
| `pitch-frequencies.json`        | Two-entry pitch glide with exponential curve.                             |
| `pitch-frequencies-multi.json`  | Three-entry multi-point pitch contour.                                    |
| `pitch-frequencies-static.json` | Single-entry static pitch (saw wave).                                     |
| `reverb-minimal.json`           | Reverb with all three required fields present.                            |
| `reverb-tail-10ms.json`         | A short 10 ms wet tail and automatic terminal window.                     |
| `reverb-tail-20ms.json`         | A short 20 ms wet tail and automatic terminal window.                     |
| `reverb-tail-500ms.json`        | A 500 ms wet tail and automatic terminal window.                          |
| `reverb-timeline.json`          | Explicit document duration plus emitted RT60 tail.                        |
| `root-truncation.json`          | Hard root cutoff truncates a layer before its declared fade.              |
| `render-frequency-clamp.json`   | Valid frequencies that low-rate engine profiles clamp to bandwidth.       |
| `seed-boundaries.json`          | Noise seed at unsigned 32-bit minimum and maximum.                        |
| `short-default-fade.json`       | Default layer fade clamps for a layer shorter than 5 ms.                  |
| `simultaneous-boundary.json`    | Half-open layer intervals meeting at one boundary.                        |
| `spatial-effects-echo-then-reverb.json` | Stacked spatial effects: echo first, then reverb (serial order). |
| `spatial-effects-empty-array.json` | Valid document with an empty `spatial_effects` array.                  |
| `spatial-effects-reverb-then-echo.json` | Stacked spatial effects: reverb first, then echo (serial order). |
| `volume-last-entry-hold.json`   | Last-entry timing fields are ignored by semantic validation.              |
| `volume-level-curve.json`       | Volume contour with two levels and exponential decay.                     |
