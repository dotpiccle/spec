# Piccle Engine DSP Runtime

This chapter defines the required DSP runtime, state preparation, render-loop boundaries, and validation architecture for [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs). Equations, processing order, initialization, and observable output requirements are normative. A section explicitly labeled as rationale supplies context but does not replace a requirement.

## Required reading order

1. [Document Structure](01-document-structure.md)
2. [Conventions](02-conventions.md)
3. [Sources](03-sources.md) through [Output](08-output.md)
4. [Noise and Determinism](09-noise-and-determinism.md)
5. [Transition Curves](10-curves.md)
6. [Engine Safety](11-engine-safety.md)
7. [Conformance](14-conformance.md)

For the task-ordered implementation and qualification contract, see [Piccle Engine Implementation Contract](15-engine-build-guide.md).

## Reference reverb runtime

The Piccle engine reverb runtime is the diffused eight-line feedback-delay network (FDN) below. The engine MUST implement this topology.

**Runtime cost:** The topology requires approximately 194 operations per output sample with state proportional to `tail_ms` for long tails (approximately 65 bytes per ms at 48 kHz binary64 plus 1.6 KiB of constant diffuser state, 34 KiB at 500 ms, 16 KiB at 220 ms, and 448 bytes at 1 ms). The engine MUST allocate this state during render-plan preparation, not in the audio render loop.

For one `tail_ms` and sample-rate configuration, define the conformance-response length `R` exactly as the reverb harness does:

```text
R = floor(tail_ms × sample_rate / 1000 + 0.5)
```

`R` configures the reverb core. It is distinct from the document's emitted-tail length `N`, which is derived from two absolute boundaries and can differ by one frame at a non-integer-millisecond sample rate.

### Input diffusion

Create four serial Schroeder all-pass stages for each input channel. Each stage has one zero-filled circular delay and processes input `x` as follows:

```text
delayed = buffer[index]
y = delayed - allpass_gain × x
buffer[index] = x + allpass_gain × y
advance index
```

Use `allpass_gain = 0.7` for the left stages and `-0.7` for the right stages. Derive the delay lengths with the helper below, using these caps and ratios:

```text
left_cap_ms  = [0.17, 0.31, 0.53, 0.89]
right_cap_ms = [0.23, 0.41, 0.67, 1.07]
ratio        = [0.003, 0.006, 0.012, 0.024]
```

For either cap array:

```text
raw[i] = max(1, min(frame(cap_ms[i]), floor(R × ratio[i] + 0.5)))
d[0] = raw[0]
d[i] = min(R, max(raw[i], d[i-1] + 1))
```

Here `frame` is the active render profile's boundary conversion. Process the four stages in array order. Call their final outputs `diffL` and `diffR`.

### Eight-line late network

Create eight zero-filled circular delay lines. Derive the delay lengths using the ratios below (no caps — the delay lengths scale proportionally with `R`, bounded by `R`):

```text
ratio = [0.004, 0.006, 0.009, 0.013, 0.019, 0.027, 0.038, 0.053]

raw[i] = max(1, floor(R × ratio[i] + 0.5))
d[0] = raw[0]
d[i] = min(R, max(raw[i], d[i-1] + 1))
```

The FDN delay lengths are uncapped so the total delay `M = Σ d[i]` scales with `tail_ms`, meeting Schroeder's modal-density criterion `M ≥ 0.15 × T₆₀ × Fs` at ~113% of the minimum for all valid tails. The diffuser delay lengths remain capped (see §Input diffusion above) because early reflections (~1 ms) do not scale with tail length.

Every render profile has at least eight frames in the shortest valid tail, so these eight lengths can remain positive and distinct. Start with decay exponent `p = 3` and set each line's feedback gain to:

```text
g[i] = 10 ^ (-p × d[i] / R)
```

For each frame, read the eight delayed samples as `z[0..7]` before writing new values. Map the diffused input into the lines:

```text
mid  = (diffL + diffR) / sqrt(2)
side = (diffL - diffR) / sqrt(2)

mid_sign  = [ 1,  1, -1,  1, -1, -1,  1, -1] / sqrt(8)
side_sign = [ 1, -1,  1,  1, -1,  1, -1, -1] / sqrt(8)
u[i] = mid_sign[i] × mid + side_sign[i] × side
```

Apply the **per-configuration random orthogonal feedback matrix** to `q[i] = g[i] × z[i]`. The matrix `Q` is an 8×8 orthogonal matrix (`Qᵀ Q = I`), generated once at configuration time via modified Gram-Schmidt orthonormalization of a matrix seeded by the normative seed function:

```text
soften_mhz = floor(soften_hz × 1000 + 0.5)
seed = (tail_ms × 2654435769 + soften_mhz) mod 2^32
```

where `2654435769 = 0x9E3779B9` is the 32-bit golden ratio constant (2^32 / φ). The multiplication is unsigned 32-bit wrapping (`mod 2^32`). The seed initializes PCG32 (see [Noise and Determinism](09-noise-and-determinism.md)), which generates the random entries for the matrix before orthonormalization. The matrix is cached per reverb configuration and reused for every frame.

### Random orthogonal feedback matrix construction

The construction is deterministic: the same `(tail_ms, soften_hz)` always produces the same `Q`.

**Step 1 — Compute the configuration seed** (as above).

**Step 2 — Initialize PCG32** per [Noise and Determinism](09-noise-and-determinism.md) with the configuration seed:

```text
state = 0
pcg32_next()                    // discard
state = state + seed
pcg32_next()                    // discard
```

The first non-discarded `pcg32_next()` output is the first source entry.

**Step 3 — Fill the 8×8 source matrix `A` in row-major order.** Each `u32` output `u` is converted to binary64 via the same formula as the noise source:

```text
x = 2 × (u / 4294967296) - 1
```

Generate 64 outputs and fill `A` row by row:

```text
for i = 0 to 7:
    for j = 0 to 7:
        A[i][j] = 2 × (pcg32_next() / 4294967296) - 1
```

**Step 4 — Column-oriented modified Gram-Schmidt orthonormalization.** The columns of `Q` are orthonormal (`Qᵀ Q = I`):

```text
for j = 0 to 7:
    // Extract column j of A
    v[i] = A[i][j]  for i = 0..7

    // Subtract projections onto previously computed Q columns
    for k = 0 to j-1:
        dot = Σ(i=0..7) Q[i][k] × v[i]
        for i = 0..7:
            v[i] = v[i] - dot × Q[i][k]

    // Normalize; handle degeneracy
    norm = sqrt(Σ(i=0..7) v[i]²)
    if norm < 1e-15:
        v[j] = 1.0
        norm = sqrt(Σ(i=0..7) v[i]²)
    for i = 0..7:
        Q[i][j] = v[i] / norm
```

Every `Σ(i=0..7)` above MUST be accumulated left-to-right in ascending `i` order, starting from
binary64 positive zero and rounding to binary64 after each addition. Implementations MUST NOT use a
compensated, pairwise, or runtime-version-dependent summation algorithm for these two reductions.
This explicit order is part of the canonical matrix construction.

The degeneracy fallback (`v[j] = 1.0`) replaces the near-zero residual with a standard basis vector, ensuring linear independence from previous columns. The matrix is cached per configuration and reused for every frame.

A language-neutral test vector verifying this construction is published at [test-vectors/numeric/reverb-matrix-vector.json](../test-vectors/numeric/reverb-matrix-vector.json) for the configuration `tail_ms = 37`, `soften_hz = 8000`. It includes the seed, PCG32 outputs, source matrix `A`, and resulting matrix `Q`.

The matrix is applied as:

```text
v = Q × q     (8×8 dense matrix-vector multiply: 64 mults + 56 adds)
write[i] = u[i] + v[i]
```

The random orthogonal matrix has eigenvalues spread as `e^{±jθ}` around the unit circle, distributing mode energy more uniformly than the Walsh-Hadamard transform (whose eigenvalues are all `±1`, clustering modes at two frequencies). This reduces the modal crest factor and the modal resonance floor for all tail lengths, with the largest improvement at long tails. Reference: Dal Santo et al. 2024, *Efficient Optimization of Feedback Delay Networks for Smooth Reverberation* (arXiv:2402.11216); JOS *Physical Audio Signal Processing*, §Choice of Lossless Feedback Matrix.

Write and advance all eight circular delay lines. The orthogonal matrix is lossless (`Qᵀ Q = I`) and every `g[i]` is below `1`, so the late network is stable.

### Wet output and decay preparation

Use these orthogonal sign vectors for the FDN output:

```text
left_sign  = [ 1,  1,  1, -1,  1, -1, -1, -1] / sqrt(8)
right_sign = [ 1, -1,  1, -1, -1,  1, -1,  1] / sqrt(8)
```

Set the diffused direct contribution to:

```text
direct_gain = min(1.5, max(0.7, 0.7 × sqrt(220 / tail_ms)))
```

Then produce:

```text
coreL = direct_gain × diffL + Σ(i = 0 .. 7) left_sign[i]  × z[i]
coreR = direct_gain × diffR + Σ(i = 0 .. 7) right_sign[i] × z[i]
```

The first term is part of the wet diffuser response, not an unprocessed dry bypass. Do not add another dry tap to the wet branch.

Apply the normative wet lowpass and terminal window after this core. During configuration preparation, run the normative impulse once, calculate `normalization_gain = 1 / sqrt(wet_energy)`, and cache that scalar by render profile, `tail_ms`, and `soften_hz`. Apply the cached scalar to rendered wet samples. During document rendering, use the document's actual `N` for the terminal window and output boundary. Do not generate an impulse response, measure energy, tune decay, or allocate delay lines in the audio callback.

Measure the final softened, windowed response for the active render profile during configuration preparation. If its RT60 crossing is outside the permitted window, calibrate `p`. Use 16 bisection steps over `[0.5, 6]` to target crossing frame `1 + floor(0.95 × R)`: lower `p` when the crossing is too early and raise `p` when it is too late. Cache the resulting exponent with the normalization gain. A crossing anywhere in the normative final-10% interval is sufficient; do not add calibration work to the render loop.

### Perceptual qualification

The Piccle engine MUST pass the strict perceptual-equivalence tolerances in [Spatial Effects](07-spatial-effects.md) §Perceptual-equivalence metric algorithms. Each of the seven metrics has a normatively pinned measurement algorithm, and the baseline values per canonical fixture are published in [manifest.json](../test-vectors/numeric/reverb-reference-irs/manifest.json). Apply those tolerances across the finite canonical, qualification, and additional-profile matrices in [the implementation contract](15-engine-build-guide.md) step 6.

The release listening gate MUST confirm:

- immediate wet onset rather than audible predelay;
- dense, noise-like reflections without discrete echoes;
- no pitched or metallic ringing;
- similar early-to-late energy balance and decay shape;
- low left/right correlation without unstable image movement; and
- spectral centroid within the tolerance defined for the post-lowpass wet response.

Also inspect each metric from the [normative algorithm specification](07-spatial-effects.md#perceptual-equivalence-metric-algorithms). No single metric substitutes for listening. An engine that only matches RT60 does not conform.

At 48 kHz, the FDN's total delay `M = Σ d[i] ≈ 0.169 × tail_ms × sample_rate / 1000` samples (e.g., M ≈ 1,784 at 220 ms, M ≈ 4,056 at 500 ms), meeting Schroeder's modal-density criterion at ~113% of the minimum. The diffuser delays add approximately 205 samples of constant state, giving a total of ~1,989 samples at 220 ms and ~4,261 samples at 500 ms. The eight-line dense matrix multiply, eight feedback gains, eight all-pass stages, and stereo input/output matrices require ~194 operations per output sample, constant work independent of `tail_ms`.

## Reference echo runtime

The Piccle engine echo runtime is the two per-channel delay lines (one per L/R channel) with feedback-path lowpass (lossy-bilinear comb filter) below. The engine MUST implement this topology.

The echo uses two per-channel delay lines (one per L/R channel) with independent lowpass state, mirroring the reverb's per-channel wet lowpass. The delay length `delay_length = max(1, frame(delay_ms))` is the same for both channels; only the lowpass state and delay buffer contents differ. This preserves the author's `balance` placement — a panned dry sound produces a panned echo in the same position.

The echo topology is purely deterministic in canonical mode; the only transcendental is the lowpass coefficient `a = exp(-2π × f / sample_rate)`, which benefits from the same platform tolerance as the reverb wet-lowpass coefficient.

### Topology

For each frame `n` in `[0, output_end_frame)`, for each channel `c` in `{L, R}`:

1. `d_c[n] = delay_buffer_c[read_index_c]` (zero-filled buffer; zero until first write)
2. `d_lp_c[n] = a × d_lp_c[n-1] + (1-a) × d_c[n]` (first-order one-pole IIR lowpass at `damp_hz`, per-channel state)
3. `fb_c[n] = feedback × d_lp_c[n]`
4. Write `delay_buffer_c[write_index_c] = stage_input_c[n] + fb_c[n]`
5. Apply the terminal window (see [Spatial Effects](07-spatial-effects.md) §Echo effect) to `d_lp_c[n]` → `d_win_c[n]`
6. `w_c[n] = d_win_c[n]`
7. `contribution_c[n] = wet_gain × w_c[n]`
8. Advance `read_index_c` and `write_index_c` (mod `delay_length`)

Where:

```text
delay_length = max(1, frame(delay_ms))
a = exp(-2π × min(damp_hz, render_frequency_max) / sample_rate)
```

The document output for an isolated echo is `stage_input_c[n] + contribution_c[n]`. In a `spatial_effects` array with multiple entries, add only `contribution_c[n]` from this echo to the shared dry mix; do not add another copy of `stage_input_c[n]`.

**Runtime cost:** The echo requires two delay lines of `delay_length` frames each (one per L/R channel), one state variable per channel for the IIR lowpass, and constant work per frame. State is proportional to `delay_ms` (approximately 75 KiB per 100 ms at 48 kHz binary64 for both channels). The engine MUST allocate this state during render-plan preparation.

### Denormal handling

Apply the same denormal-protection strategy as the reverb feedback paths (see §Denormal handling). Apply the strategy consistently to filters, reverb feedback paths, and echo feedback paths.

### Terminal window

The echo wet tail MUST terminate smoothly using the automatic terminal window defined in [Spatial Effects](07-spatial-effects.md) §Echo effect.

## Noise implementation

Implement PCG32 with explicit-width unsigned integers. On targets without native wrapping integers, the engine MUST mask the state and result after each operation. Convert the result to binary64 before division by `2^32`.

The `soft` and `sharp` character gains are analytic stationary-RMS gains. They avoid pre-rendering, duration-dependent normalization, and unbounded buffers. Engine tests MUST compare the published PCG32 prefix and character-filter values in [the numeric DSP aid](../test-vectors/numeric/dsp-values.json) before exercising complete noise renders.

## Oscillators

The published finite harmonic series defines the output target, not the private Rust oscillator representation. The production oscillator MUST have bounded per-frame cost, MUST prepare any tables outside the render loop, and MUST preserve zero phase, the phase integral, harmonic amplitudes, harmonic phases, DC limit, and alias limits in [Sources](03-sources.md). A wavetable, polyBLEP, or another internal realization is permitted only when it satisfies those requirements.

## Dynamic biquads

Canonical mode MUST recompute coefficients for every frame. Production profiles MUST compute static-cutoff coefficients during render-plan preparation. For moving cutoffs, a production profile MAY use per-frame calculation, bounded control blocks with stable coefficient interpolation, or a topology-preserving transform, but it MUST preserve declared boundary timing, stability, and the filter response requirements. Qualification MUST include fast exponential sweeps at maximum `resonance`; an optimization that produces non-finite or unstable output is invalid.

The normative coefficient equations and zero initial state are in [Filters](06-filters.md).

## Denormal handling

On x86 targets, the Piccle engine MUST enable Flush-to-Zero and Denormals-Are-Zero for the render thread when the target exposes those modes. On targets without equivalent modes, it MUST explicitly clear sufficiently small state values. The selected strategy MUST be applied consistently to filters, reverb feedback paths, and echo feedback paths and MUST satisfy the `-180 dBFS` bound in [Engine Safety](11-engine-safety.md) §Denormal protection.

## Voice allocation

The engine MUST preflight layer intervals, compute peak simultaneous voices, and reserve a bounded voice pool before rendering. The interval algorithm is implementation-defined because it cannot affect output. The audio callback MUST NOT allocate a new voice or grow a collection. If the host explicitly enables degraded partial playback, the engine MUST retain earlier layer-array entries first and MUST report degradation.

## Render-loop discipline

The engine MUST compile a validated document into an immutable render plan before producing audio. The plan MUST contain resolved defaults, absolute frame boundaries, contour segments, precomputed static gains, oscillator realization selections, filter configuration, and bounded state sizes.

The production render loop MUST:

- accept and emit fixed-size blocks or individual frames without requiring a whole-document PCM buffer;
- advance contour cursors instead of searching contour arrays each frame;
- reuse preallocated voice, filter, mix, and reverb state;
- reuse cached oscillator tables and reverb normalization values; and
- perform work proportional to active voices and filters, with constant reverb work per frame.

JSON decoding, schema validation, semantic validation, sorting, table construction, impulse measurement, resource-limit checks, and memory allocation MUST complete before rendering begins. Canonical test mode MAY use a slower internal realization, but production entry points MUST preserve the preparation/render separation above.

## Validation architecture

The Piccle engine public API MUST keep these failures separate:

- malformed JSON;
- schema-invalid document;
- semantically invalid document;
- valid but unsupported document;
- internal render failure.

This separation makes authoring tools useful and prevents device capacity from being mistaken for a format defect.

## Release qualification

Before releasing the Piccle engine, render every official example in canonical mode and in each production render profile. Qualify every supported native desktop, browser, mobile, constrained-device, low-rate, stereo, and mono-host integration. Complete the listening and measurement gates in [the Release Checklist](../RELEASE_CHECKLIST.md), including non-finite samples, clipping frequency, high-frequency aliasing, envelope discontinuities, spatial-effect termination, state memory, and render-time CPU spikes.
