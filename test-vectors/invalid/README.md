# Invalid test vectors

Each invalid fixture fails for exactly one primary reason, matching the rule listed below.

| Test vector                                | Rule violated                                     |
| ------------------------------------------ | ------------------------------------------------- |
| `missing-piccle.json`                      | Document root: `piccle` required.                 |
| `unsupported-version.json`                 | Document root: `piccle` must be `"1.0"`.          |
| `zero-layers.json`                         | Document root: `layers` requires at least 1.      |
| `duplicate-layer-id.json`                  | Semantic: layer IDs must be unique.               |
| `duplicate-member.json`                    | JSON parsing: object member names must be unique. |
| `empty-description.json`                   | Root: optional `description` cannot be empty.     |
| `empty-name.json`                          | Root: optional `name` cannot be empty.            |
| `layer-missing-duration.json`              | Layer: `duration_ms` required.                    |
| `layer-duration-zero.json`                 | Layer: `duration_ms` must be at least 1.          |
| `noise-source-with-pitch-field.json`       | Source: noise variant cannot have `pitch`.        |
| `tone-without-pitch.json`                  | Source: tone variant requires `pitch`.            |
| `time-above-safe-integer.json`             | Time values cannot exceed `2^53-1` milliseconds.  |
| `pitch-frequencies-entry-missing-hz.json`  | Pitch: each `frequencies[]` entry requires `hz`.  |
| `pitch-timing-exceeds-duration.json`       | Semantic: pitch contour timing must not exceed `duration_ms`. |
| `frequency-out-of-range.json`              | Pitch: `hz` must be 20–20000.                     |
| `negative-fade.json`                       | Layer volume: fade time cannot be negative.       |
| `root-fade-in-removed.json`                | Root: `fade_in_ms` is not a Piccle v1 field.       |
| `root-fade-out-removed.json`               | Root: `fade_out_ms` is not a Piccle v1 field.      |
| `negative-hold.json`                       | Contour: `hold_ms` cannot be negative.            |
| `negative-transition.json`                 | Contour: `transition_ms` cannot be negative.      |
| `offset-cents-out-of-range.json`           | Pitch: `offset_cents` must be −1200–1200.         |
| `volume-level-missing-level.json`          | Volume: each `levels[]` entry requires `level`.   |
| `volume-level-negative.json`               | Volume: level must be 0–1.                        |
| `volume-above-1.json`                      | Volume: level must be 0–1.                        |
| `volume-timing-exceeds-duration.json`      | Semantic: volume contour timing must not exceed `duration_ms`. |
| `balance-out-of-range.json`                | Layer: balance must be −1 to 1.                   |
| `unknown-property.json`                    | Root: no unknown properties allowed.              |
| `unknown-enum.json`                        | Various: enum value not in allowed set.           |
| `missing-wave.json`                        | Source: tone variant requires `wave`.             |
| `missing-character.json`                   | Source: noise variant requires `character`.       |
| `reverb-missing-field.json`                | Reverb: all three fields required when present.   |
| `reverb-amount-out-of-range.json`          | Reverb: `amount` must be 0–1.                     |
| `reverb-soften-out-of-range.json`          | Reverb: `soften_hz` must be 200–12000.            |
| `reverb-tail-zero.json`                    | Reverb: `tail_ms` must be at least 1.             |
| `resonance-out-of-range.json`              | Filter: `resonance` must be 0–1.                  |
| `root-duration-zero.json`                  | Root: `duration_ms` must be at least 1.           |
| `filter-missing-frequencies.json`          | Filter: `frequencies` array required.             |
| `filter-frequencies-entry-missing-hz.json` | Filter: each `frequencies[]` entry requires `hz`. |
| `filter-timing-exceeds-duration.json`      | Semantic: filter contour exceeds layer duration.  |
| `negative-start.json`                      | Layer: `start_ms` cannot be negative.              |
| `nested-unknown-property.json`             | Nested objects reject unknown properties.         |
| `seed-above-uint32.json`                   | Noise: `seed` exceeds the unsigned 32-bit range.   |
| `seed-negative.json`                       | Noise: `seed` cannot be negative.                  |
| `volume-fade-exceeds-duration.json`        | Semantic: volume fade budget exceeds duration.    |
| `wrong-schema-uri.json`                    | Root: `$schema` must identify the v1 schema.       |
