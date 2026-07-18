# Piccle v1 Release Checklist

Use this checklist for `v1.0.0-rc.1` and repeat it before promoting v1 to stable.

## Automated repository gate

- [ ] Run `python3 scripts/validate.py` in a clean checkout.
- [ ] Confirm CI passes on the release commit.
- [ ] Confirm `git diff --check` reports no whitespace errors.
- [ ] Confirm all examples and valid fixtures pass both schema and semantic validation.
- [ ] Confirm every invalid fixture fails at its documented stage.

## Canonical publication

- [ ] `https://dotpiccle.com` resolves over HTTPS.
- [ ] `https://spec.dotpiccle.com/schema/v1.json` resolves over HTTPS.
- [ ] The canonical schema response is byte-for-byte identical to `schemas/v1.json` in the release commit.
- [ ] The schema response has an appropriate JSON media type and long-lived immutable caching for the stable release.
- [ ] Record `shasum -a 256 schemas/v1.json` in the stable GitHub release notes.

## Independent implementation

- [ ] Build a clean-room renderer using only the public normative documentation.
- [ ] Record and resolve every implementation question as a specification issue.
- [ ] Verify canonical 48 kHz timing, PCG32 sequences, oscillator phase, filter equations, equal-power balance, reverb measurements, and output clipping.
- [ ] Confirm invalid, unsupported, and internal-render errors remain distinct in the engine API.

## Listening and performance

- [ ] Render every file in `examples/` at the canonical profile.
- [ ] Listen on neutral headphones.
- [ ] Listen on at least one phone speaker.
- [ ] Check recognizability, onset clicks, ending clicks, clipping, loudness consistency, oscillator aliasing, filter instability, and reverb cutoff.
- [ ] Profile the examples on the lowest supported device and document peak CPU, allocations, and simultaneous voices.

## Stable release

- [ ] All items above are complete.
- [ ] Move the changelog entries from `Unreleased` to `v1.0.0` with the actual date.
- [ ] Restore README status from release candidate to stable.
- [ ] Create the signed `v1.0.0` tag from the validated commit.
- [ ] Verify the published schema checksum again after tagging.

Do not mark v1 stable while any canonical-publication, independent-implementation, or listening item remains incomplete.
