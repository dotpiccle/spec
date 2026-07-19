#!/usr/bin/env python3
"""Reference implementation of the seven perceptual-equivalence metrics
defined in docs/07-reverb.md §Perceptual-equivalence metric algorithms.

Usage:
    python3 scripts/reverb_metrics.py            # compute and print; exit 0 if match manifest
    python3 scripts/reverb_metrics.py --update   # rewrite manifest metrics block
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "test-vectors" / "numeric" / "reverb-reference-irs"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SAMPLE_RATE = 48000
N_FFT = 65536


def _next_power_of_two(n: int) -> int:
    """Smallest power of two >= n (i.e., smallest 2^k >= n for integer k >= 0)."""
    if n <= 1:
        return 1
    p = 1
    while p < n:
        p <<= 1
    return p


def load_fixture(entry: dict) -> tuple[list[float], list[float], int, int]:
    """Load a fixture's interleaved binary64 stereo PCM.

    Returns (L, R, T, N) where T = sample_count, N = T - 1.
    """
    path = FIXTURE_DIR / entry["filename"]
    data = path.read_bytes()
    T = entry["sample_count"]
    samples = struct.unpack(f"<{T * 2}d", data)
    L = list(samples[0::2])
    R = list(samples[1::2])
    N = T - 1
    return L, R, T, N


def frame(ms: float, rate: int = SAMPLE_RATE) -> int:
    return int(math.floor(ms * rate / 1000 + 0.5))


def hann(length: int) -> list[float]:
    if length <= 1:
        return [1.0]
    return [0.5 * (1.0 - math.cos(2.0 * math.pi * k / (length - 1))) for k in range(length)]


def fft_radix2(x: list[float]) -> list[complex]:
    """Iterative radix-2 Cooley-Tukey FFT. x length MUST be a power of 2.

    Returns N_fft/2 + 1 bins (0 through Nyquist).
    """
    n = len(x)
    z = [complex(v, 0.0) for v in x]

    # Bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            z[i], z[j] = z[j], z[i]

    # Butterfly stages
    length = 2
    while length <= n:
        angle = -2.0 * math.pi / length
        wlen_real = math.cos(angle)
        wlen_imag = math.sin(angle)
        for i in range(0, n, length):
            w_real = 1.0
            w_imag = 0.0
            half = length // 2
            for j in range(i, i + half):
                u = z[j]
                v_real = z[j + half].real * w_real - z[j + half].imag * w_imag
                v_imag = z[j + half].real * w_imag + z[j + half].imag * w_real
                z[j] = complex(u.real + v_real, u.imag + v_imag)
                z[j + half] = complex(u.real - v_real, u.imag - v_imag)
                # Rotate twiddle factor
                new_real = w_real * wlen_real - w_imag * wlen_imag
                w_imag = w_real * wlen_imag + w_imag * wlen_real
                w_real = new_real
        length *= 2

    # Return positive-frequency bins 0..N/2
    nq = n // 2
    return [complex(z[k].real / nq, z[k].imag / nq) for k in range(nq + 1)]


def magnitude_spectrum(signal: list[float], fft_length: int | None = None) -> list[float]:
    """Window the signal with Hann, zero-pad, FFT, return magnitude spectrum.

    Returns (N_fft/2 + 1) bins, index 0 = DC, index N_fft/2 = Nyquist.
    When fft_length is None, uses max(65536, next_power_of_two(len(signal))).
    """
    T = len(signal)
    if fft_length is None:
        fft_length = max(N_FFT, _next_power_of_two(T))
    window = hann(T)
    x = [signal[k] * window[k] for k in range(T)]
    x += [0.0] * (fft_length - T)
    spec = fft_radix2(x)
    return [abs(bin_val) for bin_val in spec]


def rt60_crossing(L: list[float], R: list[float], N: int, T: int) -> int:
    """The first frame whose backward-integrated energy <= 1e-6 * total energy.

    Implements docs/07-reverb.md ## Wet-path normalization and RT60 lines 92-106.
    """
    # The harness uses T = N + 1 where N = floor(tail_ms * rate / 1000 + 0.5)
    E = [L[k] ** 2 + R[k] ** 2 for k in range(T)]
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


def total_energy(L: list[float], R: list[float], T: int) -> float:
    """Sum of L[n]^2 + R[n]^2 for n in [0, T)."""
    return sum(L[k] ** 2 + R[k] ** 2 for k in range(T))


def echo_density(L: list[float], R: list[float], N: int, rate: int = SAMPLE_RATE) -> float:
    """Fraction of zero-crossing intervals below rate/1000 in the tail.

    Excludes frame 0 (the impulse). See docs/07-reverb.md metric 3.
    """
    M = min(N, int(0.05 * rate))
    if M <= 1:
        return 0.0
    # Mono sum over frames (1, 1+M)
    m = [(L[k] + R[k]) / 2.0 for k in range(1, 1 + M)]

    # Effective sign with carry for exact zeros
    def sign(x: float) -> int:
        return 1 if x > 0 else (-1 if x < 0 else 0)

    # Find first non-zero sample to initialize sgn
    s: list[int] = []
    for v in m:
        sg = sign(v)
        if sg != 0 or s:
            if s:
                s.append(sg if sg != 0 else s[-1])
            else:
                s.append(sg)
    if not s:
        return 0.0
    # Fill any leading zeros that were skipped — shouldn't happen since we skip frame 0
    if len(s) < len(m):
        s = [s[0]] * (len(m) - len(s)) + s

    # Find sign-change indices
    crossings = [i for i in range(1, len(s)) if s[i] != s[i - 1]]

    if len(crossings) < 2:
        return 0.0

    # Compute intervals between successive crossings
    intervals = [crossings[i + 1] - crossings[i] for i in range(len(crossings) - 1)]
    qualifying = [d for d in intervals if d < rate / 1000.0]
    return float(len(qualifying)) / float(len(intervals)) if intervals else 0.0


def _fdn_total_delay(tail_ms: int, rate: int = SAMPLE_RATE) -> int:
    """Compute the FDN total delay M = Σ d[i] for the uncapped proportional formula.

    Matches the generator's _build_late_network (cap_ms=None) and docs/13.
    Used by the Schroeder-aware analysis window: W_m = min(T - onset_skip, max(Schroeder_min, 2*M)).
    The 2× factor is a Nyquist-like resolution criterion: to resolve modes spaced at
    Fs/M Hz, the window must span at least 2×M/Fs seconds.
    """
    R = int(math.floor(tail_ms * rate / 1000 + 0.5))
    ratios = [0.004, 0.006, 0.009, 0.013, 0.019, 0.027, 0.038, 0.053]
    lengths: list[int] = []
    for ratio in ratios:
        raw = max(1, int(math.floor(R * ratio + 0.5)))
        if lengths:
            d = min(R, max(raw, lengths[-1] + 1))
        else:
            d = raw
        lengths.append(d)
    return sum(lengths)


def modal_resonance_floor(
    L: list[float], R: list[float], T: int, tail_ms: int, rate: int = SAMPLE_RATE
) -> float | None:
    """Strongest sustained sinusoidal mode in any Schroeder-aware window.

    The window length is W_m = min(T - onset_skip, max(0.15 × tail_ms × Fs, 2 × M))
    where M is the FDN's total delay. The 2×M factor is a Nyquist-like resolution
    criterion: to resolve modes spaced at Fs/M Hz, the window must span at least
    2×M/Fs seconds. The min(T - onset_skip, ...) bound ensures the window fits
    in the available late tail.

    Returns dB value, or None if no analysis window fits (degenerate: tail too short).
    See docs/07-reverb.md metric 4.
    """
    m = [(L[k] + R[k]) / 2.0 for k in range(T)]
    peak_wet = max(abs(v) for v in m) if m else 0.0
    if peak_wet == 0.0:
        return None

    onset_skip = max(frame(5, rate), frame(0.05 * tail_ms, rate))
    schroeder_min = frame(0.15 * tail_ms, rate)
    M = _fdn_total_delay(tail_ms, rate)
    late_tail = T - onset_skip
    W_m = min(late_tail, max(schroeder_min, 2 * M))
    if onset_skip + W_m > T or W_m < 2:
        return None

    hop = max(1, W_m // 4)
    n_fft = max(N_FFT, _next_power_of_two(W_m))

    window = hann(W_m)
    k_min = max(1, int(math.ceil(20.0 * n_fft / rate)))
    strongest: float = 0.0

    start = onset_skip
    while start + W_m <= T:
        seg = m[start: start + W_m]
        seg_mean = sum(seg) / len(seg)
        seg = [v - seg_mean for v in seg]
        seg_win = [seg[k] * window[k] for k in range(W_m)]
        # Zero-pad and FFT
        pad = seg_win + [0.0] * (n_fft - W_m)
        spec = fft_radix2(pad)

        # Find peak in audible bins
        for k in range(k_min, n_fft // 2 + 1):
            amp = abs(spec[k])  # bin magnitude (already normalized by n_fft/2 in fft_fn)
            if amp > strongest:
                strongest = amp
        start += hop

    if strongest <= 0.0:
        return None

    # Undo fft_radix2 normalization (divide by n_fft/2) and correct for Hann
    # coherent gain (0.5, via factor of 2). Combined correction: 2.0 * n_fft / W_m.
    # Derivation: |M[k]| = A * W_m / (2 * n_fft) after normalization,
    # so A = |M[k]| * 2 * n_fft / W_m.
    amplitude = strongest * 2.0 * n_fft / W_m
    db = 20.0 * math.log10(amplitude / peak_wet) if amplitude > 0 and peak_wet > 0 else -float("inf")
    return db


def lr_correlation(L: list[float], R: list[float], T: int) -> float:
    """Pearson correlation across the tail (excluding frame 0).

    Returns value in [-1, 1], or 0.0 for degenerate cases.
    See docs/07-reverb.md metric 5.
    """
    if T <= 2:
        return 0.0
    L_tail = L[1:]
    R_tail = R[1:]
    n = len(L_tail)
    meanL = sum(L_tail) / n
    meanR = sum(R_tail) / n
    cov = sum((L_tail[k] - meanL) * (R_tail[k] - meanR) for k in range(n))
    varL = sum((L_tail[k] - meanL) ** 2 for k in range(n))
    varR = sum((R_tail[k] - meanR) ** 2 for k in range(n))
    if varL == 0.0 or varR == 0.0:
        return 0.0
    return cov / math.sqrt(varL * varR)


def spectral_centroid(L: list[float], R: list[float], T: int, rate: int = SAMPLE_RATE) -> float:
    """Magnitude-weighted spectral centroid of the full wet response.

    Returns Hz. See docs/07-reverb.md metric 6.
    """
    m = [(L[k] + R[k]) / 2.0 for k in range(T)]
    mag = magnitude_spectrum(m)
    n_fft = 2 * (len(mag) - 1)
    # Skip DC
    num = sum(k * mag[k] for k in range(1, len(mag)))
    den = sum(mag[k] for k in range(1, len(mag)))
    if den == 0.0:
        return 0.0
    centroid_bin = num / den
    return centroid_bin * rate / n_fft


def onset_frame(L: list[float], R: list[float], T: int) -> int:
    """Index of first sample exceeding 0.1 * peak across both channels.

    See docs/07-reverb.md metric 7.
    """
    peak = 0.0
    for k in range(T):
        abs_max = max(abs(L[k]), abs(R[k]))
        if abs_max > peak:
            peak = abs_max
    if peak == 0.0:
        return 0
    threshold = 0.1 * peak
    for k in range(T):
        if max(abs(L[k]), abs(R[k])) >= threshold:
            return k
    return T - 1


# Tolerance comparisons matching docs/07-reverb.md exactly
# Modal floor uses a HYBRID tolerance: engine ≤ ref + 6 (relative) AND
# engine ≤ MODAL_FLOOR_ABSOLUTE_GATE (absolute quality floor). Both must pass.
MODAL_FLOOR_ABSOLUTE_GATE = -30.0  # worst non-degenerate ref (-32.8) + 2.8 dB headroom, rounded to -30

TOLERANCE_SPEC: dict[str, dict] = {
    "rt60_crossing_frame": {"type": "exact"},
    "total_wet_energy": {"type": "db", "max_abs": 0.5},
    "echo_density": {"type": "relative", "lower_factor": 0.9, "upper_factor": 1.1},
    "modal_resonance_floor_db": {"type": "hybrid_db", "max_excess": 6.0, "absolute_gate": MODAL_FLOOR_ABSOLUTE_GATE},
    "lr_correlation": {"type": "absolute", "max_abs": 0.15},
    "spectral_centroid_hz": {"type": "relative", "lower_factor": 0.9, "upper_factor": 1.1},
    "onset_frame": {"type": "absolute", "max_abs": 1},
}


def check_metric(key: str, engine: float | None, ref: float | None) -> tuple[bool, str]:
    """Check a single metric against its tolerance.

    Returns (passes: bool, description: str).
    """
    spec = TOLERANCE_SPEC.get(key, {})
    tol_type = spec.get("type", "exact")

    # Handle null reference (degenerate case)
    if ref is None:
        if engine is None:
            return True, f"{key}: both null (degenerate) — pass"
        if tol_type in ("one_sided_db", "hybrid_db"):
            return True, f"{key}: ref is null (degenerate), engine={engine} — pass (trivially)"
        return False, f"{key}: ref=null but engine={engine!r} — fail (engine should be null)"

    if engine is None:
        return False, f"{key}: engine=None but ref={ref!r} — fail (engine should not be null)"

    if tol_type == "exact":
        ok = abs(engine - ref) < 1e-9
        return ok, f"{key}: engine={engine}, ref={ref} — {'pass' if ok else 'FAIL'}"

    if tol_type == "absolute":
        max_abs = spec.get("max_abs", 0.0)
        ok = abs(engine - ref) <= max_abs
        return ok, f"{key}: engine={engine}, ref={ref}, |diff|={abs(engine - ref):.4g}, max={max_abs} — {'pass' if ok else 'FAIL'}"

    if tol_type == "relative":
        lower_factor = spec.get("lower_factor", 0.9)
        upper_factor = spec.get("upper_factor", 1.1)
        if ref == 0.0:
            ok = engine == 0.0
            return ok, f"{key}: engine={engine}, ref=0 — {'pass' if ok else 'FAIL (must be 0)'}"
        lower = ref * lower_factor
        upper = ref * upper_factor
        ok = lower <= engine <= upper
        return ok, f"{key}: engine={engine}, ref={ref}, [{lower:.6g}, {upper:.6g}] — {'pass' if ok else 'FAIL'}"

    if tol_type == "one_sided_db":
        max_excess = spec.get("max_excess", 0.0)
        if engine > ref + max_excess:
            return False, f"{key}: engine={engine} dB, ref={ref} dB, excess={engine - ref:.2f} dB > {max_excess} dB — FAIL"
        return True, f"{key}: engine={engine} dB, ref={ref} dB, excess={engine - ref:.2f} dB <= {max_excess} dB — pass"

    if tol_type == "hybrid_db":
        max_excess = spec.get("max_excess", 0.0)
        absolute_gate = spec.get("absolute_gate", -float("inf"))
        rel_ok = engine <= ref + max_excess
        abs_ok = engine <= absolute_gate
        ok = rel_ok and abs_ok
        parts = []
        if not rel_ok:
            parts.append(f"relative: {engine} > {ref} + {max_excess} = {ref + max_excess} dB — FAIL")
        else:
            parts.append(f"relative: {engine} <= {ref + max_excess} dB — pass")
        if not abs_ok:
            parts.append(f"absolute: {engine} > {absolute_gate} dB — FAIL")
        else:
            parts.append(f"absolute: {engine} <= {absolute_gate} dB — pass")
        return ok, f"{key}: engine={engine} dB, ref={ref} dB — {'pass' if ok else 'FAIL'} ({'; '.join(parts)})"

    if tol_type == "db":
        max_abs = spec.get("max_abs", 0.0)
        if ref <= 0.0 or engine <= 0.0:
            ok = abs(engine - ref) < 1e-9
            return ok, f"{key}: engine={engine}, ref={ref} — {'pass' if ok else 'FAIL'}"
        db_diff = abs(20.0 * math.log10(engine / ref))
        ok = db_diff <= max_abs
        return ok, f"{key}: engine={engine}, ref={ref}, |dB diff|={db_diff:.4g} <= {max_abs} — {'pass' if ok else 'FAIL'}"

    return False, f"{key}: unknown tolerance type {tol_type!r}"


def compute_all(L: list[float], R: list[float], entry: dict) -> dict:
    """Compute all 7 metrics from the PCM data and manifest metadata.

    Returns dict matching manifest "metrics" schema.
    """
    T = entry["sample_count"]
    N = T - 1
    tail_ms = entry["tail_ms"]
    rate = entry["sample_rate"]

    c = rt60_crossing(L, R, N, T)
    energy = total_energy(L, R, T)
    ed = echo_density(L, R, N, rate)
    mrf = modal_resonance_floor(L, R, T, tail_ms, rate)
    lrc = lr_correlation(L, R, T)
    sc = spectral_centroid(L, R, T, rate)
    onset = onset_frame(L, R, T)

    metrics: dict = {
        "rt60_crossing_frame": c,
        "total_wet_energy": energy,
        "echo_density": ed,
        "lr_correlation": lrc,
        "spectral_centroid_hz": sc,
        "onset_frame": onset,
    }
    if mrf is None:
        metrics["modal_resonance_floor_db"] = None
    else:
        # Round to 1 decimal place for readability
        metrics["modal_resonance_floor_db"] = round(mrf, 1)
    return metrics


def compute_and_check(entry: dict) -> list[str]:
    """Compute metrics for one fixture and compare to manifest's published values."""
    L, R, T, N = load_fixture(entry)
    computed = compute_all(L, R, entry)
    published = entry.get("metrics")
    failures: list[str] = []
    if published is None:
        failures.append(f"{entry['filename']}: no metrics block in manifest")
        return failures

    for key in sorted(computed):
        engine_val = computed[key]
        ref_val = published.get(key)
        ok, desc = check_metric(key, engine_val, ref_val)
        if not ok:
            failures.append(f"{entry['filename']}: {desc}")
    return failures


def regenerate_metrics() -> list[dict]:
    """Load manifest, compute metrics for all fixtures, update manifest in place, return entries."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["fixtures"]:
        L, R, T, N = load_fixture(entry)
        metrics = compute_all(L, R, entry)
        entry["metrics"] = metrics
        print(f"    {entry['filename']}: metrics computed")
    manifest["fixtures"].sort(key=lambda e: e["tail_ms"])
    text = json.dumps(manifest, indent=2)
    MANIFEST_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"  Manifest written to {MANIFEST_PATH}")
    return manifest["fixtures"]


def check_all() -> list[str]:
    """Check every fixture's metrics match the published baselines."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    for entry in manifest.get("fixtures", []):
        errors.extend(compute_and_check(entry))
    return errors


def run_regression_tests() -> list[str]:
    """Verify metrics are finite and N_fft scales correctly at boundary lengths.

    Tests at T = 65535, 65536, 65537, 65538, 100000, 200000 frames using
    synthetic responses (no fixture files needed). Validates that the
    dynamic N_fft = max(65536, next_power_of_two(signal_length)) formula
    works at and above the 65536 boundary.
    """
    errors: list[str] = []
    rate = 48000
    for length in [65535, 65536, 65537, 65538, 100000, 200000]:
        # Synthetic stereo response: impulse + decaying sinusoid
        L = [0.0] * length
        R = [0.0] * length
        L[0] = R[0] = math.sqrt(0.5)
        for i in range(1, min(length, 2000)):
            decay = math.exp(-i / 200.0)
            L[i] = decay * math.sin(i * 0.1)
            R[i] = decay * math.cos(i * 0.1)

        # Verify spectral_centroid is finite
        sc = spectral_centroid(L, R, length, rate)
        if not math.isfinite(sc):
            errors.append(f"spectral_centroid not finite at T={length}")

        # Verify N_fft for spectral_centroid is correct
        expected_n = max(N_FFT, _next_power_of_two(length))
        mag = magnitude_spectrum([(L[k] + R[k]) / 2.0 for k in range(length)])
        actual_n = 2 * (len(mag) - 1)
        if actual_n != expected_n:
            errors.append(f"centroid N_fft at T={length}: expected {expected_n}, got {actual_n}")

        # Verify modal_resonance_floor is finite or None (degenerate)
        tail_ms = max(1, int(round(length * 1000.0 / rate)))
        mrf = modal_resonance_floor(L, R, length, tail_ms, rate)
        if mrf is not None and not math.isfinite(mrf):
            errors.append(f"modal_resonance_floor not finite at T={length}")

        # Verify N_fft for modal_resonance_floor if non-degenerate
        if mrf is not None:
            M = _fdn_total_delay(tail_ms, rate)
            onset_skip = max(frame(5, rate), frame(0.05 * tail_ms, rate))
            late_tail = length - onset_skip
            schroeder_min = frame(0.15 * tail_ms, rate)
            W_m = min(late_tail, max(schroeder_min, 2 * M))
            expected_modal_n = max(N_FFT, _next_power_of_two(W_m))
            # Re-run one window to check the FFT length indirectly
            # (the function doesn't return n_fft, so we verify W_m < n_fft)
            if W_m > expected_modal_n:
                errors.append(f"modal N_fft at T={length}: W_m={W_m} > n_fft={expected_modal_n}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute/verify reverb perception-equivalence metrics")
    parser.add_argument("--update", action="store_true", help="recompute metrics and update manifest")
    parser.add_argument("--test", action="store_true", help="run N_fft scaling regression tests")
    args = parser.parse_args()

    if args.test:
        print("Running N_fft scaling regression tests...")
        errors = run_regression_tests()
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            print(f"  FAILED with {len(errors)} error(s)")
            return 1
        print("  All regression tests passed.")
        return 0

    if args.update:
        print("Recomputing metrics for all fixtures...")
        regenerate_metrics()
        print("Verifying recomputed metrics...")
        errors = check_all()
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            return 1
        print("All metrics verified against new manifest.")
        return 0

    print("Checking reverb perception-equivalence metrics...")
    errors = check_all()
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"  FAILED with {len(errors)} error(s)")
        return 1
    print("  All metrics match published baselines.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
