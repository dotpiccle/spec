<p align="center">
  <img alt="piccle" src="assets/banner.png" width="600">
</p>

<p align="center"><strong>Building micro-audio made easy.</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/spec-v1.0.0--rc.1-orange?style=flat-square" alt="version candidate">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="license"></a>
  <a href="./CHANGELOG.md"><img src="https://img.shields.io/badge/status-release%20candidate-orange?style=flat-square" alt="release candidate status"></a>
</p>

<p align="center">
  <a href="#what-is-piccle">What is Piccle?</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/00-overview.md">Specification</a> ·
  <a href="examples/">Examples</a> ·
  <a href="schemas/v1.json">JSON Schema</a> ·
  <a href="docs/14-conformance.md">Conformance</a>
</p>

---

## What is Piccle?

Piccle is a product that makes building micro-audio for user interfaces across platforms easy — from browsers and desktop applications to mobile devices, consoles, vehicles, kiosks, and embedded appliances. This repository is the specification for the Piccle format.

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

This repository is the specification for the Piccle product. It contains the normative specification, JSON Schema, authoring examples, and validation fixtures. It does not contain a playback engine — Piccle's reference engine lives in a separate repository. Anyone may implement their own engine using this specification.

> [!IMPORTANT]
> Piccle v1 is a release candidate. Do not describe the format as stable until the canonical schema URL, clean-room implementation, and listening gates in [Conformance](docs/14-conformance.md) are complete.

## V1 scope

Piccle v1 is designed for finite, one-shot UI sounds:

- taps, toggles, confirmations, warnings, and errors;
- notification and navigation cues;
- short impacts, clicks, chimes, textures, and whooshes;
- layered tone and deterministic noise synthesis.

The format is platform-neutral. Piccle's reference engine includes a canonical 48 kHz test mode, and any conforming engine does the same. Desktop, browser, mobile, console, vehicle, kiosk, and embedded engines use the same documents and may publish different render profiles and resource limits. Whether an engine renders live, ahead of playback, offline, or into a cache is an implementation choice.

V1 does not define looping, continuous progress playback, host-controlled parameters, gesture control, theming inputs, modulation, speech, recorded samples, or long-form music. Hosts may replay an asset, but seamless looping is outside the format contract.

## Format at a glance

```text
document
├── piccle          "1.0"
├── duration_ms     optional explicit cutoff
├── volume          final master gain
├── reverb          { amount, tail_ms, soften_hz }
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
source → filters → layer volume → balance → mix → reverb → root volume → hard clip → platform adaptation
```

## Quick start

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

Optional fields use documented defaults. Schema `default` annotations do not modify JSON; engines apply the defaults defined by the normative chapters.

## Documentation paths

| Audience and goal                               | Start here                                                                                    |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Learn the format model                          | [Overview](docs/00-overview.md)                                                               |
| Implement parsing and the document model        | [Document Structure](docs/01-document-structure.md) and [Conventions](docs/02-conventions.md) |
| Implement DSP behavior                          | [Sources](docs/03-sources.md), then chapters 04–11                                            |
| Author common UI sounds                         | [Cookbook](docs/12-cookbook.md)                                                               |
| Review non-normative DSP guidance               | [Implementer Notes](docs/13-implementer-notes.md)                                             |
| Implement validation and conformance reporting  | [Conformance](docs/14-conformance.md)                                                         |
| Build an engine from the complete specification | [Engine Build Guide](docs/15-engine-build-guide.md)                                           |
| Propose a format change                         | [Contributing](CONTRIBUTING.md)                                                               |
| Prepare an RC or stable release                 | [Release Checklist](RELEASE_CHECKLIST.md)                                                     |

When artifacts disagree, authority is: normative `docs/` chapters, schema, test vectors, examples, then README.

## Examples

The official examples are small authoring demonstrations, not normative audio renders.

| Example                                                                                     | Intent                                    |
| ------------------------------------------------------------------------------------------- | ----------------------------------------- |
| [`button-click.json`](examples/button-click.json)                                           | Seeded sharp noise and highpass filtering |
| [`toggle-on.json`](examples/toggle-on.json) / [`toggle-off.json`](examples/toggle-off.json) | Rising and falling toggle feedback        |
| [`success.json`](examples/success.json)                                                     | Staggered rising confirmation tones       |
| [`error.json`](examples/error.json)                                                         | Muted impact and descending tones         |
| [`notification.json`](examples/notification.json)                                           | Detuned bell layers and reverb            |
| [`transition.json`](examples/transition.json)                                               | Noise and a moving lowpass filter         |
| [`sparkle.json`](examples/sparkle.json)                                                     | Four staggered tones                      |
| [`droplet.json`](examples/droplet.json)                                                     | Multi-point pitch motion                  |
| [`bloom.json`](examples/bloom.json)                                                         | Slow detuned swell                        |
| [`loading.json`](examples/loading.json)                                                     | One-shot “work started” cue, not a loop   |
| [`ready.json`](examples/ready.json)                                                         | Tick and two harmonic tones               |
| [`whisper.json`](examples/whisper.json)                                                     | Single soft-noise swell                   |
| [`page.json`](examples/page.json)                                                           | Layered paper texture and glass tick      |

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

## Building an engine

Most users will use Piccle's reference engine. If you want to build your own engine — for a new platform, language, or use case — give an implementation agent this complete repository and a target such as:

> Implement a conforming Piccle engine for `<platform>` using `<language and integration constraints>`. Follow the Engine Build Guide, implement canonical mode and every v1 primitive, and provide the required conformance evidence.

The [Engine Build Guide](docs/15-engine-build-guide.md) provides the task order and definition of done. Normative behavior remains in chapters 00–11 and 14. Live, offline, cached, and ahead-of-playback execution are engine choices.

An implementation question that requires inventing Piccle behavior is a specification defect. Resolve it here rather than silently choosing behavior in one engine.

## Conformance and engine limits

Piccle's reference engine and any independent engine follow the same processing model, which has five distinct outcomes:

1. resource-rejected before parsing completes;
2. malformed JSON;
3. schema-invalid;
4. semantically invalid;
5. valid but unsupported by a particular engine's published render limits.

Piccle v1 leaves capacity limits to engines. That means format validity is portable, but the ability to render an unusually large valid document is capacity-dependent. Engines must report unsupported documents separately from invalid documents.

The repository document fixtures verify validation behavior, non-PCM numeric aids check individual formulas, and behavior aids check document-level frame schedules. They do not, by themselves, prove audible rendering conformance; see [Conformance](docs/14-conformance.md).

## Versioning

| Document version | Repository status | Schema                               |
| ---------------- | ----------------- | ------------------------------------ |
| `1.0`            | Release candidate | [`schemas/v1.json`](schemas/v1.json) |

Documents use a `major.minor` `piccle` value. Repository tags use semantic versions. The first stable tag will be `v1.0.0`; until then, release candidates use tags such as `v1.0.0-rc.1`.

Published stable schemas are immutable. See [Contributing](CONTRIBUTING.md) for compatibility and release policy.

## License

Piccle is available under the [MIT License](LICENSE).
