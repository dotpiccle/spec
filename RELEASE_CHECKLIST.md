# Piccle v1 Release Checklist

This checklist records the stable `v1.0.0` specification release. Website publication is optional; the repository tag and frozen schema are authoritative.

## Automated repository gate

- [x] Run `python3 scripts/validate.py` against the release tree.
- [x] Confirm `git diff --check` reports no whitespace errors.
- [x] Confirm all examples and valid fixtures pass both schema and semantic validation before engine support limits are considered.
- [x] Confirm every invalid fixture fails at its documented stage.
- [ ] Confirm hosted CI passes on the release commit after push.

## Release artifact

- [x] Freeze [schemas/v1.json](schemas/v1.json) in the `v1.0.0` release commit.
- [x] Record schema SHA-256 `58bbd0946fa5c8e7175866f7a48b4afcd5ef00b1f3c9b29ee8197b396f55ceb4` in [CHANGELOG.md](CHANGELOG.md).
- [ ] Push the release commit and `v1.0.0` tag to the canonical Git remote.

Website or DNS publication MAY mirror the tagged schema later. It does not block or redefine the stable specification.

## Official Piccle engine qualification

- [ ] Update [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs) against the tagged specification commit using the [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md).
- [ ] Confirm an implementation agent can locate every parsing, validation, scheduling, DSP, state, and output rule through the implementation contract's calculation ownership index without inventing behavior.
- [ ] Give an implementation agent only this repository, a target platform, and the prompt in README; confirm it can finish without an unanswered format-level question.
- [ ] Record and resolve every implementation question as a specification issue.
- [ ] Verify canonical 48 kHz timing, PCG32 sequences, oscillator phase, filter equations, equal-power balance, reverb measurements, and output clipping.
- [ ] Confirm invalid, unsupported, and internal-render errors remain distinct in the engine API.

## Cross-platform engine qualification

- [ ] Qualify a native desktop x86-64 engine integration.
- [ ] Qualify a native desktop ARM64 engine integration.
- [ ] Qualify a browser engine integration using JavaScript, WebAssembly, or WebAudio.
- [ ] Qualify a native mobile ARM engine integration.
- [ ] Qualify a constrained no-FPU engine profile using binary32 or fixed-point DSP.
- [ ] Exercise every supported rate in the reverb qualification matrix's representative set: 8,
      16, 22.05, 24, 32, 44.1, 48, 96, and 192 kHz. Profiles with a smaller finite rate set test
      every declared rate.
- [ ] Exercise stereo hosts and mono hosts that downmix only after Piccle clipping.
- [ ] Verify finite output, timing within one render-profile frame, seeded-noise determinism, resource rejection, frequency clamping, alias suppression, filter stability, and exact reverb termination in every applicable class.
- [ ] Publish each engine profile's CPU, memory, voice, duration, and output-bandwidth limits without changing format validity.
- [ ] Document whether each tested Piccle engine profile renders live, offline, ahead of playback, or through another implementation-defined strategy.

## Listening and performance

- [ ] Render every file in `examples/` at the canonical profile.
- [ ] Listen on neutral headphones.
- [ ] Listen on full-range speakers and at least one small-device speaker.
- [ ] Listen through the lowest-bandwidth supported output path.
- [ ] Check recognizability, onset clicks, ending clicks, clipping, loudness consistency, oscillator aliasing, filter instability, and reverb cutoff.
- [ ] Pass the reverb perceptual-equivalence tolerances in [Spatial Effects](docs/07-spatial-effects.md) across the finite canonical, qualification, and additional-profile matrices in the [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md) step 6. Use the published canonical fixtures at 48 kHz and generate same-configuration references on demand elsewhere.
- [ ] A/B confirm wet onset, echo density, early-to-late energy, stereo decorrelation, brightness, and decay without metallic ringing or discrete echoes; RT60 and tolerance agreement alone is insufficient without listening review.
- [ ] Profile the examples and the engine's published maximum supported document on the lowest supported device; document render throughput, peak CPU, state memory, and simultaneous voices.
- [ ] Confirm the production render path performs no JSON work, schema traversal, sorting, table construction, impulse measurement, or memory allocation.
- [ ] Confirm output can be streamed in bounded blocks without retaining whole-document PCM.
- [ ] Confirm oscillator cost is bounded per voice and does not evaluate the full reference harmonic series per sample.
- [ ] Confirm reverb work per frame does not grow with `tail_ms`; record its fixed state-memory cost at the maximum supported tail.
- [ ] Confirm contour boundaries and voice starts do not cause unexpected render-cost spikes.

## Stable specification release

- [x] Move the changelog entries to `v1.0.0` with the release date.
- [x] Set README status to stable.
- [x] Create the `v1.0.0` tag from the validated commit.
- [x] Verify the tagged schema checksum.

Official engine, cross-platform, listening, and performance sections above are the downstream `dotpiccle/engine-rs` release contract. They do not alter the frozen Piccle v1 document specification.
