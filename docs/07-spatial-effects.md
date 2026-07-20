# Spatial Effects

Spatial effects are optional whole-document effects applied after the dry stereo layer mix. They extend the sound beyond its original dry duration, adding a sense of space (reverb) or discrete repeats (echo).

## Overview

`spatial_effects` is an array of spatial effect objects at the document root. Each entry has a `type` discriminator (`"reverb"` or `"echo"`) and type-specific fields. An empty array or omitted field means no spatial processing — the dry mix passes through unchanged.

Effects are applied in **parallel**: every effect receives the same dry stereo layer mix as its input, starting at the document origin (frame 0). All effects run simultaneously — no effect waits for or chains from another. The final output is the dry mix plus the sum of each effect's wet contribution:

```text
output[n] = dry[n] + Σ_i (contribution_i[n])
```

where `contribution_i[n]` is the wet signal from effect `i`, scaled by that effect's wet-gain field (`amount` for reverb, `wet_gain` for echo). Both are additive wet gains — the dry signal is always present at full level. There is no dry/wet crossfade in either effect.

### Output length

Let `D` be the explicit or computed document duration. Each effect `i` extends the output by its own effective tail length `tail_frames_i` (computed in frames from the effect's own parameters — see each effect's Timeline subsection). The total output length is determined by the **longest** tail:

```text
output_end_frame = frame(D) + max_i(tail_frames_i)
```

When `spatial_effects` is absent or empty, `output_end_frame = frame(D)` and the output timeline is `[0, frame(D))`.

Each effect `i` processes its stage input on `[0, frame(D))` and receives zero input on `[frame(D), frame(D) + tail_frames_i)`. Its terminal window applies to `[frame(D), frame(D) + tail_frames_i)` — its own tail region only. Effects with shorter tails produce zero output after their tail ends; the output continues until the longest tail terminates.

The total `D + max_i(tail_ms_effective_i)` MUST be ≤ `9007199254740991`. A document that exceeds this bound is semantically invalid.

See [Document Structure](01-document-structure.md) for the top-level field definition and [Output](08-output.md) for the signal-flow position.

## Reverb effect

A reverb effect gives a one-shot sound a short sense of space.

### Fields

When a reverb entry is present, all fields are required.

| Field       | Type    | Range         | Meaning                                       |
| ----------- | ------- | ------------- | --------------------------------------------- |
| `type`      | string  | `"reverb"`    | Discriminator identifying this as a reverb effect. |
| `amount`    | number  | `0`–`1`       | Additive wet gain. `0` = no reverb, `1` = reverb at full level. Dry is always present. |
| `tail_ms`   | integer | `1` or more   | RT60 target and emitted wet-tail duration.    |
| `soften_hz` | number  | `200`–`12000` | Wet-path first-order lowpass corner in Hertz. |

```json
{
  "type": "reverb",
  "amount": 0.18,
  "tail_ms": 220,
  "soften_hz": 4000
}
```

### Timeline

The reverb processes the dry mix on `[0, frame(D))` and receives zero input afterward. Its tail length in frames is:

```text
tail_frames = frame(tail_ms)
```

Define:

```text
input_end_frame = frame(D)
output_end_frame = input_end_frame + tail_frames
N = output_end_frame - input_end_frame
```

The reverb consumes its input before `input_end_frame` and zero input afterward. Engines MUST derive `N` by subtracting these absolute boundaries; they MUST NOT round `tail_ms` independently.

The wet branch emits exactly `N` tail frames after `input_end_frame`, including its automatic terminal window, and is zero outside the output timeline. All reverb core and lowpass state starts at zero and is discarded after the final output frame.

### Wet processor

The reverb core MUST be causal, bounded-input bounded-output stable, deterministic, linear, time-invariant, stereo, and free of dry-path leakage. It MUST begin from zero state for each document. Its conformance impulse response MUST have finite, positive energy before normalization. The topology is the diffused eight-line FDN specified in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime. A conforming engine MUST implement this topology.

After the reverb core, apply this first-order lowpass independently to the wet left and right channels:

```text
f = min(soften_hz, render_frequency_max)
a = exp(-2π × f / sample_rate)
y[n] = a × y[n-1] + (1-a) × x[n]
y[-1] = 0
```

`render_frequency_max` is defined in [Engine Safety](11-engine-safety.md). In the canonical profile, every valid `soften_hz` is below that maximum and is used unchanged.

### Automatic terminal window

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

### Wet-path normalization and RT60

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

### Wet contribution

After the reverb core, wet lowpass, terminal window, and normalization, the reverb's wet contribution is:

```text
contribution = amount × wet
```

This is an additive wet gain — the dry signal is always present at full level from the parallel spatial-effects stage. `amount: 0` produces no reverb contribution; `amount: 1` adds the full wet signal on top of the dry. This is the same mixing model as echo's `wet_gain`.

### Reference IR and cross-engine equivalence

**Terminology.** A **document reverb configuration** is the `(tail_ms, soften_hz)` pair declared in a Piccle document. A **render profile** is the `(sample_rate, numeric mode, channel/storage)` tuple declared by an engine (see [Engine Safety](11-engine-safety.md)). A **reference IR configuration** is the `(tail_ms, soften_hz, sample_rate)` triple for which a reference IR is generated — the combination of a document reverb configuration and a render profile's sample rate.

Piccle publishes canonical reference IR render fixtures for the reverb perceptual-equivalence gate at [test-vectors/numeric/reverb-reference-irs/](../test-vectors/numeric/reverb-reference-irs/). The 5 canonical configurations are: `tail_ms ∈ {1, 10, 20, 220, 500}`, `soften_hz = 4000`, `sample_rate = 48000` (canonical mode). These fixtures are generated from the normative FDN algorithm in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime, running at canonical mode (binary64, 48 kHz) with the normative seed function, and following the conformance-harness procedure in this section. They record the full wet pipeline — reverb core, wet lowpass, terminal window, and normalization — as binary64 stereo PCM. The fixtures are the canonical reference IR render used as the measurement baseline for the perceptual-equivalence tolerances in this section; the `manifest.json` wrapper is a non-normative metadata file recording checksums and per-file metadata.

For all reference IR configurations other than the 5 canonical triples, the reference IR is generated on demand by running the same normative FDN (see [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime) at the declared `(tail_ms, soften_hz, sample_rate)` using the normative seed function. The conformance test harness MUST generate the reference for each configuration in the mandatory qualification matrix (see [Engine Build Guide](15-engine-build-guide.md) step 6) and compare the engine's wet output against it using the tolerances in this section. The reference generator at [scripts/generate_reverb_reference_irs.py](../scripts/generate_reverb_reference_irs.py) implements this normative algorithm for any valid `(tail_ms, soften_hz, sample_rate)`.

Conforming engines need not produce byte-identical output to the fixtures. At canonical mode and at every additional render profile, a conforming engine's wet output MUST meet the strict perceptual-equivalence tolerances in the table below, measured against the reference IR for the same reverb configuration (published for the 5 canonical configurations, generated on demand for all others).

At every render profile (canonical and additional), the wet output MUST meet these strict perceptual-equivalence tolerances against the published reference IR render, measured using the conformance harness (one frame of `L=R=sqrt(0.5)` followed by zeroes, through the engine's full wet pipeline):

| Metric | Tolerance | Captures |
|---|---|---|
| RT60 crossing frame `c` (`EDC_dB[c] <= -60 dB`) | `1 + floor(0.9 × N) <= c <= N` (existing, preserved) | Bulk decay timing |
| Total wet energy `Σ(L² + R²)` after normalization | Within `±0.5 dB` of the reference fixture's value | Overall loudness |
| Echo density — fraction of zero-crossing intervals below `sample_rate / 1000` in the first `min(N, 0.05 × sample_rate)` frames | Within `±10%` of the reference fixture's density | No metallic ringing or discrete echoes |
| Modal resonance floor — strongest sustained sinusoidal mode in any Schroeder-aware `min(late_tail, max(0.15 × T₆₀ × Fs, 2 × M))` window (excluding onset), relative to the wet peak | Always `engine ≤ ref + 6` dB; additionally `engine ≤ −30` dB when `ref ≤ −30` dB | Single ringing frequency mode |
| L/R correlation across the tail (Pearson) | Within `±0.15` of the reference fixture's measured correlation | Stereo decorrelation |
| Spectral centroid of the post-softened wet response | Within `±10%` of the reference fixture's centroid | Brightness and damping beyond the normative lowpass corner |
| Onset frame — index of first wet sample exceeding `0.1 × peak_wet_sample` | Within `±1 sample` at canonical mode; within `±1 frame` at the active sample rate for additional profiles | No spurious predelay or different early-reflection patterns |

**Note.** These tolerances constrain engine conformance, not author intent. They require that a conforming engine's wet response matches the reference IR render for the *same* reverb configuration the author declared. They do not restrict what reverb configurations an author may select — an engine must reproduce whatever character the author's chosen `amount`, `tail_ms`, and `soften_hz` produce in the reference render, including the metallic or resonant character of a very short tail at high `soften_hz`.

### Perceptual-equivalence metric algorithms

This section defines the exact measurement procedure for each of the seven metrics in the tolerance table above. The engine's implementation MUST follow these algorithms; the published baseline values in `manifest.json` for each canonical fixture are the reference implementation's computed values using the same or equivalent procedures.

Every measurement operates on the conformance-harness output defined in §Wet-path normalization and RT60: one impulse frame at `L = R = sqrt(0.5)` followed by zeroes, normalized so `Σ(L² + R²) = 1`, through the engine's full wet pipeline (reverb core, wet lowpass, terminal window, normalization). Let the captured response have `T` frames total (impulse + tail), with `N = T - 1` tail frames. The sample rate is the active render profile's rate.

#### Metric 1: RT60 crossing frame `c`

Compute `c` using the backward-integrated energy-decay curve in §Wet-path normalization and RT60. The tolerance is the range `1 + floor(0.9 × N) ≤ c ≤ N`.

**Published baseline:** the measured `c` per fixture.

#### Metric 2: Total wet energy after normalization

Compute `E = Σ(n = 0 .. T − 1) (L[n]² + R[n]²)`. The harness normalizes this to `1.0` by construction. The engine's measured `E` must satisfy `|20 × log10(E / 1.0)| ≤ 0.5` dB, i.e. `E ∈ [10^(-0.5/20), 10^(0.5/20)] ≈ [0.944, 1.059]`.

**Published baseline:** `1.0` for every fixture.

#### Metric 3: Echo density

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

#### Metric 4: Modal resonance floor

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
M = Σ d[i]  (the conforming FDN's total delay, computed by the normative delay-length formula in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime)
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

**Tolerance:** reference-qualified hybrid. The engine's modal floor MUST satisfy the relative clause, and the absolute clause applies when the reference itself meets the quality floor:

1. `engine ≤ ref + 6` dB (character match — no more than 6 dB worse than the reference)
2. If `ref ≤ −30` dB, then `engine ≤ −30` dB (absolute quality floor)

The absolute floor of `−30 dB` is derived from the worst non-degenerate canonical reference fixture's modal floor in [the reference manifest](../test-vectors/numeric/reverb-reference-irs/manifest.json), plus a small headroom rounded to a clean gate value. Some valid low-rate or high-corner configurations intentionally produce a reference response above that canonical quality floor. Such a reference cannot fail against itself: for those configurations the relative clause remains mandatory and the absolute clause is not applicable. When the same-configuration reference meets `−30 dB`, an engine above `−30 dB` fails even if it remains within 6 dB of the reference.

**Note on the tolerance history.** The original specification used an absolute `≤ −40 dB` gate. That gate was not achievable by any reasonable FDN under this algorithm (the `−40 dB` figure had no literature basis). Issue #5 replaced the absolute gate with a one-sided `engine ≤ ref + 6 dB` transitional tolerance. Issue #6 supplemented the one-sided tolerance with an absolute `−25 dB` quality floor and improved the reference FDN (delay caps removed so `M` scales with `tail_ms`, random orthogonal feedback matrix replacing the Walsh-Hadamard transform) to meet Schroeder's modal-density criterion at ~113% for all valid tails. Issue #7 identified that the 20 ms fixture's previous modal floor (`−27.7 dB`) was a Rayleigh resolution artifact: the previous `W_m = max(schroeder_min, M)` window (162 frames, 3.4 ms) could not resolve modes spaced at 296 Hz. The window length was changed to `W_m = min(late_tail, max(schroeder_min, 2 × M))`, giving a 324-frame (6.75 ms) window for the 20 ms fixture. This resolved the artifact and revealed the true modal floor of `−32.8 dB`, allowing the absolute gate to tighten from `−25 dB` to `−30 dB` without any FDN change. No fixtures were regenerated; the FDN output is identical. Issue #11's normative seed function subsequently regenerated all canonical fixtures; the 20 ms modal floor shifted slightly (see [manifest.json](../test-vectors/numeric/reverb-reference-irs/manifest.json) for the current value). The absolute gate remains `−30 dB`.

The analysis window is Schroeder-aware with Nyquist resolution: `W_m = min(late_tail, max(0.15 × T₆₀ × Fs, 2 × M))`, per Schroeder & Logan, 1961, and JOS *Physical Audio Signal Processing*, §Mode Density Requirement. The onset exclusion prevents measuring onset spectral coloration rather than sustained ringing.

**Published baseline:** the measured `modal_floor` in dB per fixture. For the 1 ms fixture at 48 kHz, the published value is `null` (degenerate — onset_skip exceeds the response length).

#### Metric 5: L/R Pearson correlation

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

#### Metric 6: Spectral centroid

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

#### Metric 7: Onset frame

Compute the peak sample across both channels over the full response:

```text
peak = max(max(|L[n]|), max(|R[n]|))  over n ∈ [0, T)
```

The onset frame is the smallest `n ≥ 0` where `max(|L[n]|, |R[n]|) ≥ 0.1 × peak`.

**Degenerate case:** if `peak == 0`, the onset is undefined (the generator MUST NOT produce this).

**Tolerance:** `|engine − ref| ≤ 1` sample at canonical mode; `|engine − ref| ≤ 1` frame at the active sample rate for additional profiles.

**Published baseline:** the onset frame index per fixture.

#### Tolerance interpretation summary

| Metric | Tolerance type | Formula |
|---|---|---|
| RT60 crossing frame `c` | Range | `1 + floor(0.9 × N) ≤ c ≤ N` |
| Total wet energy | Relative dB | `\|20 × log10(E / ref)\| ≤ 0.5` dB (ref is `1.0`) |
| Echo density | Relative | `0.9 × ref ≤ engine ≤ 1.1 × ref` (`engine == 0` when `ref == 0`) |
| Modal resonance floor | Reference-qualified hybrid dB | Always `engine ≤ ref + 6`; additionally `engine ≤ −30` dB when `ref ≤ −30` dB (`null` ref is degenerate — trivially passes) |
| L/R Pearson correlation | Absolute | `\|engine − ref\| ≤ 0.15` |
| Spectral centroid | Relative | `0.9 × ref ≤ engine ≤ 1.1 × ref` (`engine == 0` when `ref == 0`) |
| Onset frame | Absolute | `\|engine − ref\| ≤ 1` frame |

The published baseline values for each canonical fixture are recorded in `test-vectors/numeric/reverb-reference-irs/manifest.json` under the `metrics` key on each fixture entry. The manifest is non-normative metadata; the algorithms in this section are the normative authority for metric computation.

### Reverb topology

The conforming reverb topology is the diffused eight-line FDN specified in [Implementer Notes](13-implementer-notes.md) §Reference reverb runtime. A conforming engine MUST implement this topology. The perceptual-equivalence tolerances in this section are measured against the canonical reference IR render, which is generated from this same FDN.

## Echo effect

An echo effect adds one or more discrete repeats of the dry signal. Each repeat is progressively darkened by a first-order lowpass in the feedback path.

### Echo topology

The echo topology is two per-channel delay lines (one per L/R channel) with feedback-path lowpass (lossy-bilinear comb filter):

**Per-channel processing.** The echo processes the left and right channels independently, with identical topology. Each channel has its own delay buffer, its own lowpass state (`d_lp_c[n-1]`), and its own read/write indices. The delay length is the same for both channels: `delay_length = max(1, frame(delay_ms))`. There is no cross-channel mixing in v1 — the echo preserves the author's `balance` placement (a panned dry sound produces a panned echo in the same position). This matches the reverb's per-channel lowpass approach. Cross-channel feedback (ping-pong) is reserved for a future spec version.

```text
For each frame n in [0, output_end_frame):
    For each channel c in {L, R}:
        1. d_c[n] = delay_buffer_c[read_index_c]   (zero-filled buffer; zero until first write)
        2. d_lp_c[n] = a × d_lp_c[n-1] + (1-a) × d_c[n]   (first-order one-pole IIR lowpass at damp_hz, per-channel state)
        3. fb_c[n] = feedback × d_lp_c[n]
        4. delay_buffer_c[write_index_c] = stage_input_c[n] + fb_c[n]
        5. Apply terminal window to d_lp_c[n] → d_win_c[n]
        6. w_c[n] = d_win_c[n]
        7. y_c[n] = stage_input_c[n] + wet_gain × w_c[n]
        8. Advance read_index_c and write_index_c (mod delay_length)
```

All delay buffers are zero-filled at document start; both lowpass states start at zero; all state is discarded after the final output frame.

Where:

```text
delay_length = max(1, frame(delay_ms))
a = exp(-2π × min(damp_hz, render_frequency_max) / sample_rate)
```

The lowpass is the same first-order one-pole IIR as reverb's wet lowpass:

```text
f = min(damp_hz, render_frequency_max)
a = exp(-2π × f / sample_rate)
d_lp[n] = a × d_lp[n-1] + (1-a) × d[n]
d_lp[-1] = 0
```

`render_frequency_max` is defined in [Engine Safety](11-engine-safety.md). In the canonical profile, every valid `damp_hz` is below that maximum and is used unchanged.

### Fields

All fields are required.

| Field       | Type    | Range         | Meaning                                       |
| ----------- | ------- | ------------- | --------------------------------------------- |
| `type`      | string  | `"echo"`      | Discriminator identifying this as an echo effect. |
| `delay_ms`  | integer | `1` or more   | Time between successive echoes and time to the first echo, in milliseconds. |
| `feedback`  | number  | `0`–`<1`      | How much of each echo feeds back into the delay line. `0` = a single echo (one repeat); approaching `1` = many repeats, very long tail. MUST be strictly less than `1` for stability. |
| `wet_gain`  | number  | `0`–`1`       | How much of the echo is heard. `0` = no echo (dry only); `1` = echo at full level. Additive — dry is always present at full level regardless of this value. |
| `damp_hz`   | number  | `200`–`12000` | Corner frequency of the first-order lowpass in the feedback path. Higher = brighter repeats; lower = darker, more muffled repeats. |

```json
{
  "type": "echo",
  "delay_ms": 200,
  "feedback": 0.6,
  "wet_gain": 0.3,
  "damp_hz": 4000
}
```

### Timeline

The echo processes the dry mix on `[0, frame(D))` and receives zero input afterward. Its tail length in frames is:

```text
tail_frames = N_total × delay_length
```

where `delay_length = max(1, frame(delay_ms))` and `N_total` is the deterministic repeat count, computed by an iterative binary64 procedure that uses no transcendentals:

```text
if feedback == 0:
    N_total = 1
else:
    N = 1                                # echo 1 (amplitude feedback⁰ = 1, always audible)
    amp = feedback                        # amplitude of echo 2
    iterations = 0
    while amp >= 0.001:
        amp = amp × feedback              # binary64, round-to-nearest-even
        N = N + 1
        iterations = iterations + 1
        if iterations >= 1048576:         # 2^20 iteration cap
            N_total = undefined           # document is semantically invalid
            break
    if N_total is defined:
        N_total = N + 1                   # include the first below-threshold echo
```

This iterative procedure uses only IEEE-754 correctly-rounded binary64 multiplication — no `log` or `ceil` — so it is deterministic across libm implementations. It matches the arithmetic the DSP feedback loop itself performs.

The procedure is bounded at `2^20 = 1_048_576` iterations. If the cap is reached (`amp` has not fallen below `0.001` after `2^20` multiplications), `N_total` is undefined and the document is semantically invalid with error code `semantic.echo_tail_unbounded`. This guarantees tractable computation for any conforming implementation. Conforming engines MAY pre-screen using a closed-form formula (`ceil(log(0.001)/log(feedback)) + 1`) to short-circuit such documents in constant time; the closed form is non-normative for determinism, the iterative procedure remains the source of truth for `N_total`.

Define:

```text
input_end_frame = frame(D)
output_end_frame = input_end_frame + tail_frames
N_echo = output_end_frame - input_end_frame
```

The echo processes its input on `[0, input_end_frame)` and receives zero input on `[input_end_frame, output_end_frame)`.

### Automatic terminal window

The echo wet tail terminates smoothly. The terminal window is applied to the wet signal `d_lp_c[n]` for frames `n ∈ [input_end_frame, output_end_frame)` — the tail region only. Frames before `input_end_frame` pass through unwindowed. When `N_echo < W` (the tail is shorter than the minimum window), the window is clamped to `W = max(2, N_echo)` to avoid the active region extending into the input region.

```text
T = output_end_frame
N_echo = output_end_frame - input_end_frame
five_ms_frames = floor(5 × sample_rate / 1000 + 0.5)
W = max(2, min(five_ms_frames, ceil(N_echo / 10)))
terminal_gain(n) = 1                              when n < T-W
                   (T - 1 - n) / (W - 1)          when T-W <= n < T
                   0                              otherwise
```

### Wet-path normalization

None. The echo wet path is not normalized. The feedback gain, `wet_gain`, and damping coefficient determine the output level directly. This is deliberate: echo repeats should be perceptually consistent with the author's chosen gains, not auto-leveled.

### Mixing model

The echo uses additive mixing:

```text
contribution[n] = wet_gain × w[n]
```

The echo's wet contribution is added to the dry mix (and any other spatial effects' contributions) by the parallel spatial-effects stage. The dry signal is always present at full level regardless of `wet_gain`. This is the same additive mixing model as reverb's `amount`.

### Conformance bar

In canonical mode, the echo effect MUST produce output matching the published echo impulse-response test vector within an explicit numerical tolerance. The lowpass coefficient `a = exp(-2π × f / sample_rate)` is transcendental; the coefficient tolerance is:

```text
|a_engine − a_ref| ≤ 8 × ε × max(1, |a_ref|)
```

where `ε = 2⁻⁵²` (binary64 machine epsilon). This matches the existing biquad filter coefficient tolerance in [Engine Build Guide](15-engine-build-guide.md) step 3.

For each checkpoint frame `n` in the echo impulse-response test vector, the rendered output MUST satisfy:

```text
|y_engine[n] − y_ref[n]| ≤ 1e-10 × max(1, |y_ref[n]|)
```

This bound is specific to the published test vector configuration (`delay_ms=200, feedback=0.6, wet_gain=0.3, damp_hz=4000, 48 kHz, 144,048 output frames`). Future echo test vectors with longer tails MUST publish their own bound, scaled to the accumulated ULP drift over the response length. For this configuration, the worst-case accumulated ULP drift over 144K frames is approximately `1.6e-11` (each frame accumulates at most one lowpass-coefficient ULP ~`1.1e-16`, compounded by the geometric feedback series `Σ feedback^k ≈ 1/(1-0.6) = 2.5`), so `1e-10` is approximately 6× the estimated drift — large enough to cover cross-libm coefficient variance, small enough to catch implementation bugs (~`1e-2`) and perceptible differences (~`1e-3`).

### Authoring guidance

The tail length is *derived* from `feedback` and `delay_ms` via an iterative binary64 procedure (see §Timeline above). High `feedback` combined with long `delay_ms` produces very long output:

- `feedback: 0.99`, `delay_ms: 1000` → tail ≈ 11.5 minutes
- `feedback: 0.999`, `delay_ms: 1000` → tail ≈ 2 hours

Authors are responsible for choosing values appropriate to their use case. Engines MAY reject configurations whose computed tail exceeds their resource budget.

> **Note.** With `feedback: 0`, the single echo repeat is still processed through the feedback-path lowpass once. An author who wants a pristine, unfiltered single echo should set `damp_hz` to the maximum value (12000 Hz), which makes the lowpass effectively transparent for most UI sounds.
