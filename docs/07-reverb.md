# Reverb

Reverb is an optional whole-document effect applied after the dry stereo layer mix. It gives a one-shot sound a short sense of space.

## Fields

When `reverb` is present, all fields are required.

| Field       | Type    | Range         | Meaning                                       |
| ----------- | ------- | ------------- | --------------------------------------------- |
| `amount`    | number  | `0`–`1`       | Linear dry/wet crossfade.                     |
| `tail_ms`   | integer | `1` or more   | RT60 target and emitted wet-tail duration.    |
| `soften_hz` | number  | `200`–`12000` | Wet-path first-order lowpass corner in Hertz. |

```json
"reverb": {
  "amount": 0.18,
  "tail_ms": 220,
  "soften_hz": 4000
}
```

## Timeline

Let `D` be the explicit or computed document duration. Define:

```text
dry_end_frame = frame(D)
output_end_frame = frame(D + tail_ms)
N = output_end_frame - dry_end_frame
```

When reverb is present, the output timeline is `[0, output_end_frame)`. The reverb consumes the dry mix before `dry_end_frame` and zero input afterward. Engines MUST derive `N` by subtracting these absolute boundaries; they MUST NOT round `tail_ms` independently.

The dry branch ends at `D`. The wet branch emits exactly `N` tail frames after `D`, including its automatic terminal window, and is zero outside the output timeline. All reverb core and lowpass state starts at zero and is discarded after the final output frame.

## Wet processor

The reverb core MUST be causal, bounded-input bounded-output stable, deterministic, linear, time-invariant, stereo, and free of dry-path leakage. It MUST begin from zero state for each document. Its conformance impulse response MUST have finite, positive energy before normalization. The topology is implementation-defined.

After the reverb core, apply this first-order lowpass independently to the wet left and right channels:

```text
f = min(soften_hz, render_frequency_max)
a = exp(-2π × f / sample_rate)
y[n] = a × y[n-1] + (1-a) × x[n]
y[-1] = 0
```

`render_frequency_max` is defined in [Engine Safety](11-engine-safety.md). In the canonical profile, every valid `soften_hz` is below that maximum and is used unchanged.

## Automatic terminal window

The wet tail always terminates smoothly. This behavior is mandatory and has no document field.

Let `T = output_end_frame`, let the tail contain `N` frames, and define the rounded five-millisecond span for the active sample rate:

```text
five_ms_frames = floor(5 × sample_rate / 1000 + 0.5)
W = max(2, min(five_ms_frames, ceil(N / 10)))
```

All engine render profiles use rates of at least 8 kHz, so a valid one-millisecond tail contains enough frames for `W >= 2`. For frame `n`:

```text
terminal_gain(n) = 1                              when n < T-W
                   (T - 1 - n) / (W - 1)          when T-W <= n < T
                   0                              otherwise
```

The gain is `1` on the first terminal-window frame and exactly `0` on the final emitted frame.

## Wet-path normalization and RT60

This measurement uses a DSP conformance harness, not a schema-valid Piccle document. Reset the reverb to zero state. Feed one frame whose left and right inputs are both `sqrt(0.5)`, followed by zeroes. For the harness only, define:

```text
N = floor(tail_ms × sample_rate / 1000 + 0.5)
T = N + 1
```

Capture frames `0` through `N`: frame `0` contains the input impulse and frames `1` through `N` are the tail. Apply the same lowpass and terminal-window equations with exclusive end `T`.

For captured wet samples `L[n]` and `R[n]`, apply one constant gain so that:

```text
Σ(n = 0 .. T-1) (L[n]² + R[n]²) = 1
```

Normalization occurs after softening and terminal windowing. An implementation MAY calculate and cache the gain for a reverb configuration.

Define the backward-integrated energy-decay curve:

```text
E[n] = Σ(k = n .. T-1) (L[k]² + R[k]²)
EDC_dB[n] = 10 × log10(E[n] / E[0])
```

The first frame whose energy is at most `10^-6` of `E[0]` is the −60 dB crossing. If its index is `c`, it MUST satisfy:

```text
c >= 1 + floor(0.9 × N)
c <= N
```

The final emitted wet frame `N` is exactly zero because of the terminal window. Compute the threshold comparison from the linear energy ratio; do not take `log10(0)` on the final frame.

## Dry/wet crossfade

After the reverb core, wet lowpass, terminal window, and normalization, apply:

```text
output = (1 - amount) × dry + amount × wet
```

`amount: 0` is fully dry and `amount: 1` is fully wet. Reverb presence still defines the complete output timeline even when the amount is zero.

## Reference IR and cross-engine equivalence

Piccle publishes canonical reference IR render fixtures for the reverb perceptual-equivalence gate at [test-vectors/numeric/reverb-reference-irs/](../test-vectors/numeric/reverb-reference-irs/). These fixtures are generated from the deterministic FDN algorithm in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime, running at canonical mode (binary64, 48 kHz) and following the conformance-harness procedure in this chapter. They record the full wet pipeline — reverb core, wet lowpass, terminal window, and normalization — as binary64 stereo PCM. The fixtures are the canonical reference IR render used as the measurement baseline for the perceptual-equivalence tolerances in this chapter; the `manifest.json` wrapper is a non-normative metadata file recording checksums and per-file metadata. Conforming engines need not produce byte-identical output to the fixtures.

At canonical mode and at every additional render profile, a conforming engine's wet output MUST meet the strict perceptual-equivalence tolerances in the table below, measured against the canonical reference IR fixture for the same reverb configuration. Bit-identical output is not required across platforms: the reverb configuration constants (feedback gains via `pow`, the wet lowpass coefficient via `exp`) depend on platform transcendental implementations, and Piccle does not require correctly-rounded transcendentals across processors (see [Engine Safety](11-engine-safety.md)). Two engines on the same platform using the same system `libm` typically produce bit-identical output, but this is not a conformance requirement.

At every render profile (canonical and additional), the wet output MUST meet these strict perceptual-equivalence tolerances against the published reference IR render, measured using the conformance harness (one frame of `L=R=sqrt(0.5)` followed by zeroes, through the engine's full wet pipeline):

| Metric | Tolerance | Captures |
|---|---|---|
| RT60 crossing frame `c` (`EDC_dB[c] <= -60 dB`) | `1 + floor(0.9 × N) <= c <= N` (existing, preserved) | Bulk decay timing |
| Total wet energy `Σ(L² + R²)` after normalization | Within `±0.5 dB` of the reference fixture's value | Overall loudness |
| Echo density — fraction of zero-crossing intervals below `sample_rate / 1000` in the first `min(N, 0.05 × sample_rate)` frames | Within `±10%` of the reference fixture's density | No metallic ringing or discrete echoes |
| Modal resonance floor — strongest sustained sinusoidal mode in any Schroeder-aware `min(late_tail, max(0.15 × T₆₀ × Fs, 2 × M))` window (excluding onset), relative to the wet peak | `engine ≤ ref + 6` AND `engine ≤ −30` dB (hybrid) | Single ringing frequency mode |
| L/R correlation across the tail (Pearson) | Within `±0.15` of the reference fixture's measured correlation | Stereo decorrelation |
| Spectral centroid of the post-softened wet response | Within `±10%` of the reference fixture's centroid | Brightness and damping beyond the normative lowpass corner |
| Onset frame — index of first wet sample exceeding `0.1 × peak_wet_sample` | Within `±1 sample` at canonical mode; within `±1 frame` at the active sample rate for additional profiles | No spurious predelay or different early-reflection patterns |

**Note.** These tolerances constrain engine conformance, not author intent. They require that a conforming engine's wet response matches the reference IR render for the *same* reverb configuration the author declared. They do not restrict what reverb configurations an author may select — an engine must reproduce whatever character the author's chosen `amount`, `tail_ms`, and `soften_hz` produce in the reference render, including the metallic or resonant character of a very short tail at high `soften_hz`.

## Perceptual-equivalence metric algorithms

This section defines the exact measurement procedure for each of the seven metrics in the tolerance table above. The engine's implementation MUST follow these algorithms; the published baseline values in `manifest.json` for each canonical fixture are the reference implementation's computed values using the same or equivalent procedures.

Every measurement operates on the conformance-harness output defined in §Wet-path normalization and RT60: one impulse frame at `L = R = sqrt(0.5)` followed by zeroes, normalized so `Σ(L² + R²) = 1`, through the engine's full wet pipeline (reverb core, wet lowpass, terminal window, normalization). Let the captured response have `T` frames total (impulse + tail), with `N = T - 1` tail frames. The sample rate is the active render profile's rate.

### Metric 1: RT60 crossing frame `c`

Compute `c` using the backward-integrated energy-decay curve in §Wet-path normalization and RT60. The tolerance is the range `1 + floor(0.9 × N) ≤ c ≤ N`.

**Published baseline:** the measured `c` per fixture.

### Metric 2: Total wet energy after normalization

Compute `E = Σ(n = 0 .. T − 1) (L[n]² + R[n]²)`. The harness normalizes this to `1.0` by construction. The engine's measured `E` must satisfy `|20 × log10(E / 1.0)| ≤ 0.5` dB, i.e. `E ∈ [10^(-0.5/20), 10^(0.5/20)] ≈ [0.944, 1.059]`.

**Published baseline:** `1.0` for every fixture.

### Metric 3: Echo density

Form the mono sum `m[n] = (L[n] + R[n]) / 2` over the first `M = min(N, floor(0.05 × sample_rate + 0.5))` tail frames, i.e. indices `n ∈ [1, 1 + M)` of the captured response. Frame 0 (the impulse) is excluded to avoid biasing the count.

Define the sign function:

```text
sgn(x) =  1   if x > 0
         -1   if x < 0
          0   if x == 0
```

Build an effective sign sequence `s[n]` for the analysis window. Initialize `s` from the first non-zero sample. For each subsequent sample, assign `s[n] = sgn(m[n])` when `m[n] != 0`, otherwise `s[n] = s[n - 1]` (carry-forward for exact zeros).

A zero-crossing interval is the number of samples between two consecutive sign changes (indices where `s[n] != s[n-1]`). An interval qualifies when its length is strictly less than `sample_rate / 1000` samples. Compute:

```text
echo_density = (number of qualifying intervals) / (number of intervals)
```

If fewer than two sign changes occur (zero or one intervals), `echo_density = 0`.

**Tolerance:** relative. `0.9 × ref ≤ engine ≤ 1.1 × ref`. If the reference value is `0`, the engine's value MUST also be `0`.

**Published baseline:** the measured `echo_density` (a float in `[0, 1]`) per fixture.

### Metric 4: Modal resonance floor

Form the mono sum `m[n] = (L[n] + R[n]) / 2` over the full captured response `[0, T)`. Compute the reference amplitude:

```text
peak_wet = max(|m[n]|)  over n ∈ [0, T)
```

Exclude the onset from analysis. The onset (direct path plus diffuser output) is not a sustained ringing mode:

```text
onset_skip = max(frame(5), frame(0.05 × tail_ms))
```

Define the analysis window length as the Schroeder-aware Nyquist-resolution maximum of the Schroeder minimum modal-density criterion and twice the FDN's total delay `M = Σ d[i]`, bounded by the available late tail:

```text
schroeder_min = floor(0.15 × tail_ms × sample_rate / 1000 + 0.5)
M = Σ d[i]  (the FDN's total delay; see [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime)
late_tail = T − onset_skip
W_m = min(late_tail, max(schroeder_min, 2 × M))
```

The Schroeder minimum (`0.15 × T₆₀ × Fs`) is the minimum window length to resolve modes at the Schroeder modal-density criterion. The `2 × M` factor is a Nyquist-like resolution criterion: to resolve modes spaced at `Fs / M` Hz, the window must span at least `2 × M / Fs` seconds. Using `max(schroeder_min, 2 × M)` ensures the window can resolve modes at the FDN's actual modal density, not just the theoretical minimum; the `min(late_tail, ...)` bound ensures the window fits in the available late tail after onset exclusion.

Use hop size `hop = max(1, floor(W_m / 4))`. For every window start position `start = onset_skip, onset_skip + hop, onset_skip + 2·hop, ...` where `start + W_m ≤ T`:

1. Extract the segment `seg = m[start : start + W_m]`.
2. Subtract its mean: `seg[k] -= mean(seg)`.
3. Apply a Hann window: `w[k] = 0.5 × (1 − cos(2π × k / (W_m − 1)))` for `k ∈ [0, W_m)` (if `W_m = 1`, `w[0] = 1`).
4. Zero-pad to `N_fft = max(65536, next_power_of_two(W_m))` and compute the DFT. Here `next_power_of_two(n)` is the smallest `2^k ≥ n` for integer `k ≥ 0`. (The zero-padding provides bin interpolation; the Rayleigh frequency resolution is `sample_rate / W_m`, not `sample_rate / N_fft`.)
5. Compute the magnitude spectrum `|M[k]|` for `k ∈ [k_min, N_fft / 2]` where `k_min = ceil(20 × N_fft / sample_rate)` (the bin for 20 Hz, the audible lower bound).
6. Recover the amplitude of the strongest bin in this window:

   ```text
   window_peak = max(4 × |M[k]| / W_m)
   ```

   The factor `4` divides by the Hann window's DC gain `|W(0)| / 2 = W_m / 4`, which accounts for both the cosine-to-exponential half-gain and the window's coherent gain. For a sinusoid of amplitude A at a bin center frequency, the standard (unnormalized) DFT magnitude at that bin is `|X[k]| = A × W_m / 4`. Worst-case scalloping loss for a non-bin-centered sinusoid is approximately 1.5 dB, well within the tolerance.

The **strongest sustained mode** is the maximum `window_peak` across all window positions. The **modal resonance floor** in dB is:

```text
modal_floor = 20 × log10(strongest / peak_wet)
```

**Degenerate cases:**
- If `peak_wet == 0`, the modal floor is undefined (the generator MUST NOT produce this).
- If `onset_skip + W_m > T` (no analysis window fits), the modal floor is `−∞ dB` (the tail is too short to sustain a modal resonance). The published baseline for very short tails is `null`.

**Tolerance:** hybrid. The engine's modal floor MUST satisfy BOTH clauses:

1. `engine ≤ ref + 6` dB (character match — no more than 6 dB worse than the reference)
2. `engine ≤ −30` dB (absolute quality floor — no single sustained mode louder than −30 dB relative to the wet peak)

Both clauses must be satisfied. The absolute floor of `−30 dB` is derived from the worst non-degenerate reference fixture's modal floor (`−32.8 dB` for `tail_ms = 20` with the `2 × M` Nyquist-resolution window) plus 2.8 dB headroom, rounded to `−30 dB` for a clean gate value. An engine that produces a single sustained resonator above `−30 dB` fails the absolute clause regardless of the reference; an engine that exceeds the reference by more than 6 dB fails the relative clause.

**Note on the tolerance history.** The original specification used an absolute `≤ −40 dB` gate. That gate was not achievable by any reasonable FDN under this algorithm (the `−40 dB` figure had no literature basis). Issue #5 replaced the absolute gate with a one-sided `engine ≤ ref + 6 dB` transitional tolerance. Issue #6 supplemented the one-sided tolerance with an absolute `−25 dB` quality floor and improved the reference FDN (delay caps removed so `M` scales with `tail_ms`, random orthogonal feedback matrix replacing the Walsh-Hadamard transform) to meet Schroeder's modal-density criterion at ~113% for all valid tails. Issue #7 identified that the 20 ms fixture's previous modal floor (`−27.7 dB`) was a Rayleigh resolution artifact: the previous `W_m = max(schroeder_min, M)` window (162 frames, 3.4 ms) could not resolve modes spaced at 296 Hz. The window length was changed to `W_m = min(late_tail, max(schroeder_min, 2 × M))`, giving a 324-frame (6.75 ms) window for the 20 ms fixture. This resolved the artifact and revealed the true modal floor of `−32.8 dB`, allowing the absolute gate to tighten from `−25 dB` to `−30 dB` without any FDN change. No fixtures were regenerated; the FDN output is identical.

The analysis window is Schroeder-aware with Nyquist resolution: `W_m = min(late_tail, max(0.15 × T₆₀ × Fs, 2 × M))`, per Schroeder & Logan, 1961, and JOS *Physical Audio Signal Processing*, §Mode Density Requirement. The onset exclusion prevents measuring onset spectral coloration rather than sustained ringing.

**Published baseline:** the measured `modal_floor` in dB per fixture. For the 1 ms fixture at 48 kHz, the published value is `null` (degenerate — onset_skip exceeds the response length).

### Metric 5: L/R Pearson correlation

Compute over the tail frames only, indices `n ∈ [1, T)`. Frame 0 (the impulse) is excluded — it carries no stereo decorrelation information.

```text
meanL = (1/(T−1)) × Σ L[n]
meanR = (1/(T−1)) × Σ R[n]
cov   = Σ (L[n] − meanL) × (R[n] − meanR)
varL  = Σ (L[n] − meanL)²
varR  = Σ (R[n] − meanR)²
r = cov / sqrt(varL × varR)
```

**Degenerate cases:** if `T ≤ 2` (tail has 0 or 1 samples) or `varL == 0` or `varR == 0`, then `r = 0`.

**Tolerance:** absolute. `|engine − ref| ≤ 0.15`.

**Published baseline:** the measured Pearson `r` per fixture, in `[-1, 1]`.

### Metric 6: Spectral centroid

Form the mono sum `m[n] = (L[n] + R[n]) / 2` over the full captured response `[0, T)`. Apply a Hann window:

```text
w[k] = 0.5 × (1 − cos(2π × k / (T − 1)))  for k ∈ [0, T)
```

Zero-pad the windowed signal to `N_fft = max(65536, next_power_of_two(T))` and compute the magnitude spectrum `|M[k]|`. The spectral centroid uses **magnitude weighting** (not power weighting):

```text
centroid_bin  = (Σ k × |M[k]|) / (Σ |M[k]|)             over k ∈ [1, N_fft/2]
centroid_hz   = centroid_bin × sample_rate / N_fft
```

The summation excludes the DC bin (k = 0). If `Σ |M[k]| = 0`, `centroid_hz = 0`.

**Tolerance:** relative. `0.9 × ref ≤ centroid_hz ≤ 1.1 × ref`. If the reference value is `0`, the engine's value MUST also be `0`.

**Published baseline:** the measured centroid in Hz per fixture.

**Note on `N_fft` scaling.** Metrics 4 and 6 both use `N_fft = max(65536, next_power_of_two(signal_length))`, where `signal_length` is `W_m` (Metric 4) or `T` (Metric 6). The 65536 minimum ensures stable bin interpolation for short responses and preserves all published baselines (the 5 canonical fixtures all have `T` and `W_m` below 65536). For responses or windows longer than 65536 frames, `N_fft` is the next power of two above the input length, preserving the zero-padding interpolation behavior. At 48 kHz, the 65536 minimum covers tails up to ~1365 ms; the next-power-of-two rule covers the full valid tail range up to the engine's published ceiling. The amplitude recovery formula (`4 × |M[k]| / W_m`) and the centroid formula (`centroid_bin × sample_rate / N_fft`) are both correct for any `N_fft` because the unnormalized DFT magnitude is independent of zero-padding length and the bin-to-Hz conversion scales with `1 / N_fft`.

### Metric 7: Onset frame

Compute the peak sample across both channels over the full response:

```text
peak = max(max(|L[n]|), max(|R[n]|))  over n ∈ [0, T)
```

The onset frame is the smallest `n ≥ 0` where `max(|L[n]|, |R[n]|) ≥ 0.1 × peak`.

**Degenerate case:** if `peak == 0`, the onset is undefined (the generator MUST NOT produce this).

**Tolerance:** `|engine − ref| ≤ 1` sample at canonical mode; `|engine − ref| ≤ 1` frame at the active sample rate for additional profiles.

**Published baseline:** the onset frame index per fixture.

### Tolerance interpretation summary

| Metric | Tolerance type | Formula |
|---|---|---|
| RT60 crossing frame `c` | Range | `1 + floor(0.9 × N) ≤ c ≤ N` |
| Total wet energy | Relative dB | `\|20 × log10(E / ref)\| ≤ 0.5` dB (ref is `1.0`) |
| Echo density | Relative | `0.9 × ref ≤ engine ≤ 1.1 × ref` (`engine == 0` when `ref == 0`) |
| Modal resonance floor | Hybrid dB | `engine ≤ ref + 6` AND `engine ≤ −30` dB (`null` ref is degenerate — trivially passes) |
| L/R Pearson correlation | Absolute | `\|engine − ref\| ≤ 0.15` |
| Spectral centroid | Relative | `0.9 × ref ≤ engine ≤ 1.1 × ref` (`engine == 0` when `ref == 0`) |
| Onset frame | Absolute | `\|engine − ref\| ≤ 1` frame |

The published baseline values for each canonical fixture are recorded in `test-vectors/numeric/reverb-reference-irs/manifest.json` under the `metrics` key on each fixture entry. The manifest is non-normative metadata; the algorithms in this section are the normative authority for metric computation.

## Implementation freedom

Schroeder, feedback-delay-network, generated-convolution, and other linear time-invariant implementations are permitted when they meet the response, normalization, equivalence tolerances, and lifetime requirements above.

The implementation in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime is the recommended default.
