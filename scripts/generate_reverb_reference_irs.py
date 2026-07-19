#!/usr/bin/env python3
"""Generate and verify the canonical reverb reference IR fixtures.

Implements the deterministic diffused eight-line FDN from
docs/13-implementer-notes.md and the wet harness from docs/07-reverb.md.
At binary64 48 kHz canonical mode the output is perceptually equivalent across
conforming implementations.

Usage:
    python3 generate_reverb_reference_irs.py          # regenerate all fixtures
    python3 generate_reverb_reference_irs.py --check  # verify SHA-256s only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
FIXTURE_DIR = ROOT / "test-vectors" / "numeric" / "reverb-reference-irs"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SAMPLE_RATE = 48000
SOFTEN_HZ = 4000.0
INV_SQRT2 = 1.0 / math.sqrt(2.0)
INV_SQRT8 = 1.0 / math.sqrt(8.0)


def frame(ms: float) -> int:
    return int(math.floor(ms * SAMPLE_RATE / 1000 + 0.5))


def five_ms_frames() -> int:
    return int(math.floor(5 * SAMPLE_RATE / 1000 + 0.5))


class AllpassDiffuser:
    """Single Schroeder all-pass section with circular delay."""

    def __init__(self, length: int, gain: float):
        self.buffer = [0.0] * length
        self.index = 0
        self.length = length
        self.gain = gain

    def process(self, x: float) -> float:
        delayed = self.buffer[self.index]
        y = delayed - self.gain * x
        self.buffer[self.index] = x + self.gain * y
        self.index = (self.index + 1) % self.length
        return y


class FDN:
    """Diffused eight-line feedback-delay network from docs/13.

    At canonical mode (binary64, 48kHz) the hot path uses only adds, subs,
    muls, sign-flips, and delay-line reads/writes — no transcendentals.
    """

    def __init__(self, tail_ms: int):
        self.sample_rate = SAMPLE_RATE
        self.R = frame(float(tail_ms))  # conformance response length
        self.tail_ms = tail_ms
        self._build_diffusers()
        self._build_late_network()
        self.direct_gain = self._compute_direct_gain()
        self._run_bisection()
        self._reset()

    # --- Diffuser helpers ---

    def _length(self, cap_ms: float, ratio: float, prev: int | None) -> int:
        raw = max(1, min(frame(cap_ms), int(math.floor(self.R * ratio + 0.5))))
        if prev is None:
            return raw
        return min(self.R, max(raw, prev + 1))

    def _make_lengths(self, caps_ms: list[float], ratios: list[float]) -> list[int]:
        lengths: list[int] = []
        for cap, ratio in zip(caps_ms, ratios):
            prev = lengths[-1] if lengths else None
            lengths.append(self._length(cap, ratio, prev))
        return lengths

    def _build_diffusers(self):
        left_cap_ms = [0.17, 0.31, 0.53, 0.89]
        right_cap_ms = [0.23, 0.41, 0.67, 1.07]
        ratios = [0.003, 0.006, 0.012, 0.024]
        left_lengths = self._make_lengths(left_cap_ms, ratios)
        right_lengths = self._make_lengths(right_cap_ms, ratios)
        self.left_diffusers = [
            AllpassDiffuser(length, 0.7) for length in left_lengths
        ]
        self.right_diffusers = [
            AllpassDiffuser(length, -0.7) for length in right_lengths
        ]
        self.diffuser_lengths = {
            "allpass_left": left_lengths,
            "allpass_right": right_lengths,
        }

    def _build_late_network(self):
        cap_ms = [1.49, 1.87, 2.29, 2.83, 3.49, 4.33, 5.39, 6.71]
        ratios = [0.004, 0.006, 0.009, 0.013, 0.019, 0.027, 0.038, 0.053]
        self.fdn_lengths = self._make_lengths(cap_ms, ratios)
        self.num_lines = 8
        self.fdn_buffers = [[0.0] * l for l in self.fdn_lengths]
        self.fdn_indices = [0] * self.num_lines
        self.feedback_gains = [0.0] * self.num_lines

    def _reset(self):
        for diff in self.left_diffusers:
            diff.buffer = [0.0] * diff.length
            diff.index = 0
        for diff in self.right_diffusers:
            diff.buffer = [0.0] * diff.length
            diff.index = 0
        for i in range(self.num_lines):
            self.fdn_buffers[i] = [0.0] * self.fdn_lengths[i]
            self.fdn_indices[i] = 0

    def _set_feedback_gains(self, p: float):
        for i in range(self.num_lines):
            self.feedback_gains[i] = 10.0 ** (-p * self.fdn_lengths[i] / self.R)

    def _compute_direct_gain(self) -> float:
        return min(1.5, max(0.7, 0.7 * math.sqrt(220.0 / self.tail_ms)))

    def _run_bisection(self):
        """16-step bisection over p ∈ [0.5, 6] targeting 1+floor(0.95×R)."""
        target = 1 + int(math.floor(0.95 * self.R))
        lo, hi = 0.5, 6.0
        for _ in range(16):
            p = (lo + hi) / 2.0
            crossing = self._measure_crossing(p)
            if crossing < target:
                hi = p
            else:
                lo = p
        self.p = (lo + hi) / 2.0
        self._set_feedback_gains(self.p)

    def _measure_crossing(self, p: float) -> int:
        self._set_feedback_gains(p)
        return self._impulse_rt60_crossing()

    def _impulse_rt60_crossing(self) -> int:
        self._reset()
        N = self.R
        T = N + 1
        L = [0.0] * T
        R_chan = [0.0] * T

        for n in range(T):
            inp = math.sqrt(0.5) if n == 0 else 0.0
            # Diffusers
            diffL = inp
            for d in self.left_diffusers:
                diffL = d.process(diffL)
            diffR = inp
            for d in self.right_diffusers:
                diffR = d.process(diffR)

            read_z = []
            for i in range(self.num_lines):
                read_z.append(self.fdn_buffers[i][self.fdn_indices[i]])

            mid = (diffL + diffR) * INV_SQRT2
            side = (diffL - diffR) * INV_SQRT2

            mid_sign = [1, 1, -1, 1, -1, -1, 1, -1]
            side_sign = [1, -1, 1, 1, -1, 1, -1, -1]
            u = [0.0] * self.num_lines
            for i in range(self.num_lines):
                u[i] = (mid_sign[i] * mid + side_sign[i] * side) * INV_SQRT8

            q = [self.feedback_gains[i] * read_z[i] for i in range(self.num_lines)]
            self._fwt(q)

            for i in range(self.num_lines):
                write_val = u[i] + q[i] * INV_SQRT8
                self.fdn_buffers[i][self.fdn_indices[i]] = write_val
                self.fdn_indices[i] = (self.fdn_indices[i] + 1) % self.fdn_lengths[i]

            left_sign = [1, 1, 1, -1, 1, -1, -1, -1]
            right_sign_vals = [1, -1, 1, -1, -1, 1, -1, 1]
            coreL = self.direct_gain * diffL
            coreR = self.direct_gain * diffR
            for i in range(self.num_lines):
                coreL += left_sign[i] * read_z[i] * INV_SQRT8
                coreR += right_sign_vals[i] * read_z[i] * INV_SQRT8

            L[n] = coreL
            R_chan[n] = coreR

        a = math.exp(-2.0 * math.pi * SOFTEN_HZ / SAMPLE_RATE)
        yL, yR = 0.0, 0.0
        for n in range(T):
            L[n] = a * yL + (1.0 - a) * L[n]
            yL = L[n]
            R_chan[n] = a * yR + (1.0 - a) * R_chan[n]
            yR = R_chan[n]

        five_ms = five_ms_frames()
        W = max(2, min(five_ms, int(math.ceil(N / 10.0))))
        for n in range(T):
            if n >= T - W:
                gain = (T - 1 - n) / max(W - 1, 1)
                if n >= T:
                    gain = 0.0
                L[n] *= gain
                R_chan[n] *= gain

        energy = sum(L[k] ** 2 + R_chan[k] ** 2 for k in range(T))
        if energy > 0:
            norm = 1.0 / math.sqrt(energy)
            for k in range(T):
                L[k] *= norm
                R_chan[k] *= norm

        E = [L[k] ** 2 + R_chan[k] ** 2 for k in range(T)]
        suffix = [0.0] * T
        s = 0.0
        for k in range(T - 1, -1, -1):
            s += E[k]
            suffix[k] = s
        E0 = suffix[0] if T > 0 else 0.0
        for k in range(T - 1):
            if suffix[k] <= 1e-6 * E0:
                return k
        return T - 1

    def _fwt(self, values: list[float]):
        """In-place normalized fast Walsh-Hadamard transform."""
        n = len(values)
        width = 1
        while width < n:
            for start in range(0, n, 2 * width):
                for j in range(width):
                    a = values[start + j]
                    b = values[start + j + width]
                    values[start + j] = a + b
                    values[start + j + width] = a - b
            width *= 2

    def generate(self, tail_ms: int | None = None) -> tuple[list[float], list[float]]:
        """Generate the reference IR render: L and R lists of length T = N+1.

        The output is the full wet pipeline: core → lowpass → terminal window → normalization.
        """
        N = self.R
        T = N + 1
        L = [0.0] * T
        R_chan = [0.0] * T

        self._reset()

        for n in range(T):
            inp = math.sqrt(0.5) if n == 0 else 0.0

            diffL = inp
            for d in self.left_diffusers:
                diffL = d.process(diffL)
            diffR = inp
            for d in self.right_diffusers:
                diffR = d.process(diffR)

            read_z = []
            for i in range(self.num_lines):
                read_z.append(self.fdn_buffers[i][self.fdn_indices[i]])

            mid = (diffL + diffR) * INV_SQRT2
            side = (diffL - diffR) * INV_SQRT2

            mid_sign = [1, 1, -1, 1, -1, -1, 1, -1]
            side_sign = [1, -1, 1, 1, -1, 1, -1, -1]
            u = [0.0] * self.num_lines
            for i in range(self.num_lines):
                u[i] = (mid_sign[i] * mid + side_sign[i] * side) * INV_SQRT8

            q = [self.feedback_gains[i] * read_z[i] for i in range(self.num_lines)]
            self._fwt(q)

            for i in range(self.num_lines):
                write_val = u[i] + q[i] * INV_SQRT8
                self.fdn_buffers[i][self.fdn_indices[i]] = write_val
                self.fdn_indices[i] = (self.fdn_indices[i] + 1) % self.fdn_lengths[i]

            left_sign = [1, 1, 1, -1, 1, -1, -1, -1]
            right_sign_vals = [1, -1, 1, -1, -1, 1, -1, 1]
            coreL = self.direct_gain * diffL
            coreR = self.direct_gain * diffR
            for i in range(self.num_lines):
                coreL += left_sign[i] * read_z[i] * INV_SQRT8
                coreR += right_sign_vals[i] * read_z[i] * INV_SQRT8

            L[n] = coreL
            R_chan[n] = coreR

        a = math.exp(-2.0 * math.pi * SOFTEN_HZ / SAMPLE_RATE)
        yL, yR = 0.0, 0.0
        for n in range(T):
            L[n] = a * yL + (1.0 - a) * L[n]
            yL = L[n]
            R_chan[n] = a * yR + (1.0 - a) * R_chan[n]
            yR = R_chan[n]

        five_ms = five_ms_frames()
        W = max(2, min(five_ms, int(math.ceil(N / 10.0))))
        for n in range(T):
            if n >= T - W:
                gain = (T - 1 - n) / max(W - 1, 1)
                if n >= T:
                    gain = 0.0
                L[n] *= gain
                R_chan[n] *= gain

        energy = sum(L[k] ** 2 + R_chan[k] ** 2 for k in range(T))
        if energy > 0:
            norm = 1.0 / math.sqrt(energy)
            for k in range(T):
                L[k] *= norm
                R_chan[k] *= norm

        return (L, R_chan)


def pack_stereo_interleaved(L: list[float], R: list[float]) -> bytes:
    buf = bytearray()
    for left, right in zip(L, R):
        buf += struct.pack("<dd", left, right)
    return bytes(buf)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_fixture(tail_ms: int, output_dir: Path) -> dict:
    fdn = FDN(tail_ms)
    L, R = fdn.generate()
    T = len(L)
    N = T - 1
    data = pack_stereo_interleaved(L, R)

    filename = f"tail_{tail_ms:03d}_ms_soften_4000_hz_at_48000.bin"
    filepath = output_dir / filename
    filepath.write_bytes(data)

    return {
        "filename": filename,
        "sample_count": T,
        "channels": 2,
        "sample_rate": SAMPLE_RATE,
        "soften_hz": SOFTEN_HZ,
        "tail_ms": tail_ms,
        "dtype": "binary64le",
        "sha256": sha256(data),
        "generator": "docs/13-implementer-notes.md §Reference reverb runtime",
        "conformance_impulse": {"left": "sqrt(0.5)", "right": "sqrt(0.5)"},
    }


def regenerate_all() -> list[dict]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    tails = [1, 10, 20, 220, 500]
    entries = []
    for tail in tails:
        print(f"  Generating tail {tail} ms...")
        entry = generate_fixture(tail, FIXTURE_DIR)
        entries.append(entry)
        print(f"    → {entry['filename']}  ({entry['sample_count']} frames, SHA-256: {entry['sha256']})")
    entries.sort(key=lambda e: e["tail_ms"])
    manifest = {
        "status": "non-normative",
        "description": "Canonical reference IR render fixtures for the reverb perceptual-equivalence gate. "
                       "Generated from the docs/13 FDN generator algorithm at binary64 48 kHz canonical mode. "
                       "These files record the full wet pipeline: FDN core → wet lowpass → terminal window → normalization.",
        "fixtures": entries,
    }
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(f"  Manifest written to {MANIFEST_PATH}")
    return entries


def check_integrity() -> list[str]:
    errors: list[str] = []

    if not MANIFEST_PATH.exists():
        errors.append(f"manifest not found: {MANIFEST_PATH}")
        return errors

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    for entry in manifest.get("fixtures", []):
        path = FIXTURE_DIR / entry["filename"]
        if not path.exists():
            errors.append(f"fixture missing: {path}")
            continue
        actual_sha = sha256(path.read_bytes())
        if actual_sha != entry["sha256"]:
            errors.append(f"SHA-256 mismatch for {entry['filename']}: expected {entry['sha256']}, got {actual_sha}")
        expected_size = entry["sample_count"] * entry["channels"] * 8
        if path.stat().st_size != expected_size:
            errors.append(f"size mismatch for {entry['filename']}: expected {expected_size}, got {path.stat().st_size}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/verify reverb reference IR fixtures")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify existing fixtures without regenerating",
    )
    args = parser.parse_args()

    if args.check:
        print("Checking reverb reference IR fixtures...")
        errors = check_integrity()
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            return 1
        print("  All fixtures verified OK.")
        return 0

    print("Regenerating reverb reference IR fixtures...")
    entries = regenerate_all()
    print("Regenerated fixtures:")
    for entry in entries:
        size = entry["sample_count"] * entry["channels"] * 8
        print(f"  {entry['filename']}: {entry['sample_count']} frames, {size} bytes")

    errors = check_integrity()
    if errors:
        for e in errors:
            print(f"  POST-GENERATION ERROR: {e}")
        return 1
    print("Post-generation integrity check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
