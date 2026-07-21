# Reverb reference IR fixtures

These files are derived numeric aids containing canonical IR renders for the reverb perceptual-equivalence gate defined in [Spatial Effects](../../../docs/07-spatial-effects.md) §Reference IR and engine qualification.

Each fixture is raw little-endian binary64 IEEE-754 interleaved stereo PCM, generated from the deterministic FDN algorithm in [Piccle Engine DSP Runtime](../../../docs/13-implementer-notes.md) §Reference reverb runtime at canonical mode (binary64, 48 kHz). The generator runs the qualification harness from [Spatial Effects](../../../docs/07-spatial-effects.md) — one impulse frame at `L=R=sqrt(0.5)`, then zeroes — and records the full wet pipeline (FDN core, wet lowpass, automatic terminal window, and normalization).

## Schema

`manifest.json` contains per-file metadata:

| Field                 | Type   | Meaning                                                                                             |
| --------------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `filename`            | string | Name of the `.bin` file                                                                             |
| `sample_count`        | int    | Total frames (impulse + tail); equals `N + 1` where `N = floor(tail_ms × 48 + 0.5)` for the harness |
| `channels`            | int    | Always 2 (stereo, interleaved L,R)                                                                  |
| `sample_rate`         | int    | Always 48000                                                                                        |
| `soften_hz`           | number | Wet lowpass corner frequency in Hz (always 4000)                                                    |
| `tail_ms`             | int    | The `tail_ms` value used by the generator                                                           |
| `dtype`               | string | Always `binary64le`                                                                                 |
| `sha256`              | string | SHA-256 hex digest of the raw `.bin` file                                                           |
| `generator`           | string | Pointer to the normative algorithm document                                                         |
| `conformance_impulse` | object | The input impulse used (one frame: `{"left": "sqrt(0.5)", "right": "sqrt(0.5)"}`)                   |
| `metrics`             | object | Published baseline values for the seven perceptual-equivalence metrics (see [Spatial Effects](../../../docs/07-spatial-effects.md) §Perceptual-equivalence metric algorithms) |

Each `metrics` object contains the following keys:

| Key | Type | Meaning |
|---|---|---|
| `rt60_crossing_frame` | int | The first frame whose backward-integrated energy is ≤ −60 dB from the total |
| `total_wet_energy` | float | `Σ(L² + R²)` after harness normalization (always `1.0` by construction) |
| `echo_density` | float | Fraction of zero-crossing intervals below `sample_rate / 1000` in the first 50 ms of the tail |
| `modal_resonance_floor_db` | float or `null` | Strongest sustained sinusoidal mode in any Schroeder-aware `min(late_tail, max(0.15 × tail_ms, 2 × M))` window (excluding onset), relative to the wet peak (dB). `null` when the tail is too short for analysis |
| `lr_correlation` | float | Pearson correlation across the tail (excluding the impulse frame) |
| `spectral_centroid_hz` | float | Magnitude-weighted spectral centroid (Hz) of the full wet response |
| `onset_frame` | int | Index of first sample exceeding `0.1 × peak` across both channels |

The measurement algorithms are normative and defined in [Spatial Effects](../../../docs/07-spatial-effects.md). The published values are reference baselines for engine conformance comparison; the manifest itself is non-normative metadata.

## Usage

To load a fixture in Python:

```python
import struct, hashlib, json
from pathlib import Path

manifest = json.loads(Path("manifest.json").read_text())
entry = next(e for e in manifest["fixtures"] if e["tail_ms"] == 220)
data = Path(entry["filename"]).read_bytes()

# Verify integrity
assert hashlib.sha256(data).hexdigest() == entry["sha256"]

# Parse interleaved binary64 stereo PCM
T = entry["sample_count"]
samples = struct.unpack(f"<{T * 2}d", data)  # [L0, R0, L1, R1, ..., L_{T-1}, R_{T-1}]
L = list(samples[0::2])
R = list(samples[1::2])
```

To regenerate the fixtures, run [scripts/generate_reverb_reference_irs.py](../../../scripts/generate_reverb_reference_irs.py) from the repository root.
