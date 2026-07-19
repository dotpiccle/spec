#!/usr/bin/env python3
"""Regression test: reverb_metrics.check_metric tolerance bounds.

Guards against the bug where the relative-tolerance lower bound was
computed as ref / 1.1 ≈ 0.909 × ref instead of the normative 0.9 × ref.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reverb_metrics import check_metric


def assert_pass(key, engine, ref):
    ok, desc = check_metric(key, engine, ref)
    assert ok, f"expected pass: {desc}"


def assert_fail(key, engine, ref):
    ok, desc = check_metric(key, engine, ref)
    assert not ok, f"expected fail: {desc}"


def test_echo_density_bounds():
    key = "echo_density"
    # Exact lower bound (inclusive)
    assert_pass(key, 0.9, 1.0)
    # Just above lower bound
    assert_pass(key, 0.9001, 1.0)
    # Just below lower bound
    assert_fail(key, 0.8999, 1.0)
    # Exact upper bound (inclusive)
    assert_pass(key, 1.1, 1.0)
    # Just below upper bound
    assert_pass(key, 1.0999, 1.0)
    # Just above upper bound
    assert_fail(key, 1.1001, 1.0)
    # Mid-range passes
    assert_pass(key, 1.0, 1.0)
    assert_pass(key, 0.95, 1.0)
    assert_pass(key, 1.05, 1.0)


def test_spectral_centroid_bounds():
    key = "spectral_centroid_hz"
    ref = 9000.0
    # Exact lower bound (inclusive)
    assert_pass(key, 8100.0, ref)
    # Just below lower bound
    assert_fail(key, 8099.0, ref)
    # Exact upper bound (inclusive)
    assert_pass(key, 9900.0, ref)
    # Just above upper bound
    assert_fail(key, 9901.0, ref)
    # Mid-range passes
    assert_pass(key, 9000.0, ref)
    assert_pass(key, 8500.0, ref)
    assert_pass(key, 9500.0, ref)


def test_degenerate_cases():
    for key in ("echo_density", "spectral_centroid_hz"):
        # Both zero passes
        assert_pass(key, 0.0, 0.0)
        # Engine non-zero when ref is zero fails
        assert_fail(key, 0.5, 0.0)
    # Null reference (degenerate fixture) passes for relative metrics
    assert_pass("echo_density", None, None)
    assert_pass("spectral_centroid_hz", None, None)


def test_nonrelative_types():
    # exact: must match exactly
    assert_pass("rt60_crossing_frame", 1000, 1000)
    assert_fail("rt60_crossing_frame", 1001, 1000)

    # db: |20 * log10(engine / ref)| <= 0.5 dB
    assert_pass("total_wet_energy", 1.0, 1.0)
    # 0.6 dB exceeds 0.5 dB max, so engine = ref * 10^(0.6/20) should fail
    assert_fail("total_wet_energy", 1.0 * 10 ** (0.6 / 20), 1.0)

    # absolute: |engine - ref| <= 0.15
    assert_pass("lr_correlation", 0.5, 0.5)
    assert_pass("lr_correlation", 0.36, 0.5)
    assert_fail("lr_correlation", 0.2, 0.5)


def test_modal_floor_conditional_absolute_gate():
    key = "modal_resonance_floor_db"
    # A reference that meets the quality floor keeps both clauses mandatory.
    assert_pass(key, -30.0, -32.0)
    assert_fail(key, -29.9, -32.0)
    # A same-configuration reference above the floor cannot fail against itself.
    assert_pass(key, -19.8, -19.8)
    assert_pass(key, -14.0, -19.8)
    assert_fail(key, -13.7, -19.8)


if __name__ == "__main__":
    test_echo_density_bounds()
    test_spectral_centroid_bounds()
    test_degenerate_cases()
    test_nonrelative_types()
    test_modal_floor_conditional_absolute_gate()
    print("All tolerance boundary tests passed.")
