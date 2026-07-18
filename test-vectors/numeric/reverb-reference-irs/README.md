# Reverb reference IR fixtures

These files are non-normative numeric aids. They contain canonical reference IR renders for the reverb perceptual-equivalence gate defined in `docs/07-reverb.md` §Reference IR and cross-engine equivalence.

Each fixture is raw little-endian binary64 IEEE-754 interleaved stereo PCM, generated from the deterministic FDN algorithm in `docs/13-implementer-notes.md` §Reference reverb runtime at canonical mode (binary64, 48 kHz). The generator runs the conformance harness from `docs/07-reverb.md` — one impulse frame at `L=R=sqrt(0.5)`, then zeroes — and records the full wet pipeline (FDN core, wet lowpass, automatic terminal window, and normalization).

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

To regenerate the fixtures, run `scripts/generate_reverb_reference_irs.py` from the repository root.
