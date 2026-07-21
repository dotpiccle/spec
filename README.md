<p align="center">
  <img alt="piccle" src="assets/banner.png" width="600">
</p>

<p align="center"><strong>Declarative synthesis and DSP semantics for UI micro-audio.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/spec-v1.0.1-brightgreen?style=flat-square" alt="version 1.0.1">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="license"></a>
  <a href="./CHANGELOG.md"><img src="https://img.shields.io/badge/status-stable-brightgreen?style=flat-square" alt="stable status"></a>
</p>

<p align="center">
  <a href="#what-is-piccle">What is Piccle?</a> ·
  <a href="#minimal-document">Minimal document</a> ·
  <a href="docs/00-overview.md">Specification</a> ·
  <a href="examples/">Examples</a> ·
  <a href="schemas/v1.json">JSON Schema</a> ·
  <a href="docs/14-conformance.md">Conformance</a>
</p>

---

## What is Piccle?

Piccle is a declarative format for finite procedural UI-audio signals across browsers, desktop and mobile systems, consoles, vehicles, kiosks, and embedded targets. This repository is the normative technical specification for the format.

A Piccle asset contains structured synthesis instructions rather than recorded audio:

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "click",
      "duration_ms": 80,
      "source": { "type": "noise", "character": "sharp", "seed": 7 },
      "volume": 0.6,
      "filters": [{ "type": "highpass", "frequencies": [{ "hz": 3000 }] }]
    }
  ]
}
```

This repository contains the normative DSP specification, JSON Schema, technical authoring examples, qualification fixtures, numeric aids, and the execution contract for the official [Piccle Rust engine](https://github.com/dotpiccle/engine-rs). It targets audio engineers, engine maintainers, validation/tooling authors, and AI infrastructure. Introductory and consumer-facing documentation belongs on a separate documentation surface.

Piccle v1.0 is stable. The authoritative release artifact is the latest `v1.0.x` repository tag; website publication is optional and is not part of format validity.

## V1 scope

Piccle v1 is designed for finite, one-shot UI sounds:

- taps, toggles, confirmations, warnings, and errors;
- notification and navigation cues;
- short impacts, clicks, chimes, textures, and whooshes;
- layered tone and deterministic noise synthesis.

The format is platform-neutral. The Piccle engine provides a canonical 48 kHz test mode and may expose additional production render profiles for desktop, browser, mobile, console, vehicle, kiosk, and embedded integrations. Every profile uses the same document semantics. Execution placement—live, ahead of playback, offline, or cached—is internal to the engine and cannot change validation or rendered intent.

V1 does not define looping, continuous progress playback, host-controlled parameters, gesture control, theming inputs, modulation, speech, recorded samples, or long-form music. Hosts may replay an asset, but seamless looping is outside the format contract.

## Format at a glance

```text
document
├── piccle          "1.0"
├── duration_ms     optional explicit cutoff
├── master_volume_level  final master gain
├── spatial_effects[]  parallel reverb and/or echo entries
└── layers[]
    ├── id, start_ms, duration_ms
    ├── source
    │   ├── tone    { wave, pitch }
    │   └── noise   { character, seed }
    ├── filters[]   serial lowpass/highpass/bandpass
    ├── volume      number or contour object
    └── balance     equal-power stereo position
```

The normative signal flow is:

```text
source → filters → layer volume → balance → dry mix → parallel spatial effects → root master_volume_level → hard clip → platform adaptation
```

## Minimal document

The shortest valid tone document is:

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "beep",
      "duration_ms": 200,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": { "frequencies": [{ "hz": 440 }] }
      }
    }
  ]
}
```

Optional fields use documented defaults. Schema `default` annotations do not modify JSON; the Piccle engine applies the defaults defined by the normative chapters.

## Documentation paths

| Technical goal                                             | Start here                                                                                    |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Review the format scope and signal model                   | [Overview](docs/00-overview.md)                                                               |
| Implement parsing and the resolved document model          | [Document Structure](docs/01-document-structure.md) and [Conventions](docs/02-conventions.md) |
| Implement source, control, filter, mix, and output DSP      | [Sources](docs/03-sources.md), then chapters 04–11                                            |
| Inspect non-normative synthesis and sound-design patterns  | [Technical Authoring Patterns](docs/12-cookbook.md)                                           |
| Implement required runtime algorithms and state            | [Piccle Engine DSP Runtime](docs/13-implementer-notes.md)                                     |
| Implement validation results and qualification reporting   | [Conformance](docs/14-conformance.md)                                                         |
| Implement and qualify `dotpiccle/engine-rs`                | [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md)                        |
| Propose a format change                                    | [Contributing](CONTRIBUTING.md)                                                               |
| Prepare an RC or stable release                            | [Release Checklist](RELEASE_CHECKLIST.md)                                                     |

When artifacts disagree, authority is: normative `docs/` chapters, schema, test vectors, examples, then README.

## Examples

The official examples are compact synthesis and signal-processing configurations, not normative PCM renders.

| Example                                                                                     | Intent                                    |
| ------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [`button-click.json`](examples/button-click.json)                                           | Seeded noise excitation through a static highpass biquad |
| [`toggle-on.json`](examples/toggle-on.json) / [`toggle-off.json`](examples/toggle-off.json) | Opposed pitch-contour trajectories                     |
| [`success.json`](examples/success.json)                                                     | Staggered pitched partials with reverb                 |
| [`error.json`](examples/error.json)                                                         | Band-limited transient plus descending tone layers     |
| [`notification.json`](examples/notification.json)                                           | Detuned tonal layers with parallel reverb              |
| [`transition.json`](examples/transition.json)                                               | Noise excitation with a time-varying lowpass cutoff    |
| [`sparkle.json`](examples/sparkle.json)                                                     | Four asynchronously scheduled tonal layers             |
| [`droplet.json`](examples/droplet.json)                                                     | Multi-segment pitch contour                             |
| [`bloom.json`](examples/bloom.json)                                                         | Detuned tonal onset and long envelope                   |
| [`loading.json`](examples/loading.json)                                                     | Finite broadband onset with tonal sustain |
| [`ready.json`](examples/ready.json)                                                         | Transient plus two harmonic partials      |
| [`whisper.json`](examples/whisper.json)                                                     | Lowpass-shaped deterministic noise envelope            |
| [`page.json`](examples/page.json)                                                           | Layered filtered-noise and tonal transients             |
| [`echo.json`](examples/echo.json)                                                           | Lowpass-feedback comb response                         |

## Validation

Install the pinned validation dependency and run the complete repository gate:

```bash
python3 -m pip install jsonschema==4.25.1
python3 scripts/validate.py
```

The command:

- meta-validates the Draft 2019-09 schema;
- accepts every example and valid fixture;
- rejects every invalid fixture with its declared stable error code and JSON path;
- checks duplicate JSON members and Piccle semantic rules;
- recomputes the non-PCM DSP numeric aids;
- verifies fixture inventories, local links and Markdown anchors, schema/docs invariants, and canonical JSON formatting.

CI runs the same command.

## Implementing the Piccle engine

The official implementation is [`dotpiccle/engine-rs`](https://github.com/dotpiccle/engine-rs). Give an implementation agent both repositories and the target-platform constraints:

> Implement Piccle v1 in `dotpiccle/engine-rs` for `<target integration>`. Treat the Piccle specification as authoritative for parsing, validation, default resolution, frame scheduling, DSP calculations, state initialization, signal flow, error classification, and qualification. Do not invent behavior that is absent from the specification.

The [Piccle Engine Implementation Contract](docs/15-engine-build-guide.md) gives the mandatory work sequence and definition of done. Required behavior lives in chapters 00–11 and 14; chapter 13 defines runtime algorithms, state, preparation, and render-loop invariants. Private Rust structure and platform I/O remain owned by the engine repository.

An implementation question that requires inventing observable Piccle behavior is a specification defect. Resolve it here before encoding behavior in `engine-rs`.

## Conformance and engine limits

The Piccle engine follows one processing model with five distinct outcomes:

1. resource-rejected before parsing completes;
2. malformed JSON;
3. schema-invalid;
4. semantically invalid;
5. valid but unsupported by the active Piccle engine profile's published limits.

Piccle v1 separates format validity from profile capacity. The Piccle engine MUST report a valid document that exceeds an active profile limit as unsupported, never invalid.

The repository document fixtures verify validation behavior, non-PCM numeric aids check individual formulas, and behavior aids check document-level frame schedules. They do not, by themselves, prove complete engine qualification; see [Conformance](docs/14-conformance.md).

## Versioning

| Document version | Repository status | Schema                               |
| ---------------- | ----------------- | ------------------------------------ |
| `1.0`            | Stable (`v1.0.1`) | [`schemas/v1.json`](schemas/v1.json) |

Documents use a `major.minor` `piccle` value. Repository tags use semantic versions. The latest stable Piccle v1 specification is tagged `v1.0.1`.

Published stable schemas are immutable. See [Contributing](CONTRIBUTING.md) for compatibility and release policy.

## License

Piccle is available under the [MIT License](LICENSE).
