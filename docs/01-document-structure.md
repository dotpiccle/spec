# Document Structure

A Piccle document is a single JSON object with the fields below.

## Root fields

| Field                 | Type    | Default  | Required | Description                                                                                                                                                                             |
| --------------------- | ------- | -------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$schema`             | string  | --       | No       | When present, MUST be `https://spec.dotpiccle.com/schema/v1.json`.                                                                                                                      |
| `piccle`              | string  | --       | **Yes**  | The Piccle format version. MUST be `"1.0"` for this specification.                                                                                                                      |
| `name`                | string  | --       | No       | Non-empty human-readable name for this sound.                                                                                                                                           |
| `description`         | string  | --       | No       | Non-empty human-readable description of what this sound is for.                                                                                                                         |
| `duration_ms`         | integer | computed | No       | Total document duration in milliseconds. 1 or more. If absent, duration is computed from the latest-ending layer. A shorter duration trims layers; a longer duration pads with silence. |
| `master_volume_level` | number  | 1        | No       | Final master gain. 0 = silent, 1 = full. A single number; unlike layer `volume`, this field does not accept a contour object. Independent of per-layer volume.                          |
| `spatial_effects`      | array   | --       | No       | Optional whole-document spatial effects applied after the dry mix. Each entry is a `reverb` or `echo`. All effects run in parallel — each receives the same dry mix and adds its wet contribution. An empty array is valid and equivalent to omitting the field. |
| `layers`              | array   | --       | **Yes**  | One or more layers that make up this sound.                                                                                                                                             |

## Layer fields

Each layer is an independent sound generator. The fields below define its behavior:

| Field         | Type             | Default | Required | Description                                                                                                                                       |
| ------------- | ---------------- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`          | string           | --      | **Yes**  | Unique identifier for this layer. Lowercase letters, digits, and hyphens only (pattern: `^[a-z][a-z0-9-]*$`). MUST be unique within the document. |
| `start_ms`    | integer          | 0       | No       | When this layer starts playing, in milliseconds from the document start. Default 0 = start at the same time as all other layers.                  |
| `duration_ms` | integer          | --      | **Yes**  | How long this layer plays, in milliseconds. 1 or more.                                                                                            |
| `source`      | object           | --      | **Yes**  | The raw sound this layer makes: a `tone` or deterministic `noise`. See [Sources](03-sources.md).                                                  |
| `volume`      | number or object | 1       | No       | Loudness contour. A number (0–1) or an object with `fade_in`, `fade_out`, and a `levels` array. See [Layer Volume](05-layer-volume.md).                       |
| `balance`     | number           | 0       | No       | Stereo position. −1 = full left, 0 = center, 1 = full right.                                                                                      |
| `filters`     | array            | []      | No       | Filter chain applied in series. Zero or more filters. See [Filters](06-filters.md).                                                               |

Both tone and noise sources produce a mono signal. Stereo placement is applied exclusively by the `balance` field.

## The layers field

`layers` is the heart of a Piccle document. It is an array of one or more layer objects. The spec does not impose a maximum layer count — engines MAY enforce their own limits. Each layer is an independent sound generator with its own source, volume contour, balance, and optional filter chain.

Here is a minimal document showing the required fields:

```json
{
  "piccle": "1.0",
  "layers": [
    {
      "id": "my-layer",
      "duration_ms": 200,
      "source": {
        "type": "tone",
        "wave": "sine",
        "pitch": {
          "frequencies": [{ "hz": 440 }]
        }
      }
    }
  ]
}
```

## Duration rules

- If `duration_ms` is absent from the document root, the engine computes it from the latest-ending layer (layer `start_ms` + layer `duration_ms`).
- If `duration_ms` is present and shorter than a layer, that layer is hard-truncated. Truncation does not move or create a layer fade and may therefore click.
- If `duration_ms` is present and longer than all layers, the remaining time is silence.
- Every layer has its own required `duration_ms` (1 or more) which is independent of the document duration.
- When spatial effects are present, the output length is `frame(D) + max_i(tail_frames_i)` where each effect's tail length is computed in frames from its own parameters; see [Spatial Effects](07-spatial-effects.md) §Output length.
- Every derived layer end (`start_ms + duration_ms`) and the total output end (`frame(D) + max_i(tail_frames_i)`) MUST be no greater than `9007199254740991`. A document that exceeds either bound is semantically invalid.

## Layer timing

- `start_ms` is the offset, in milliseconds, from the document start to the moment the layer begins playing. It defaults to `0`.
- Every layer that omits `start_ms` (or sets it to `0`) starts at the document start **simultaneously**.
- The order of layers in the `layers` array does **not** affect timing. Array order is for author readability and optional degraded voice-allocation priority; see [Engine Safety](11-engine-safety.md).
- Piccle has **no implicit sequencing**: layers never play "one after the other" by default. To chain a layer after another layer's end, set the later layer's `start_ms` explicitly (for example, layer B's `start_ms` = layer A's `duration_ms`).
- Layers whose intervals `[start_ms, start_ms + duration_ms)` overlap contribute simultaneously during the overlap; see [Output](08-output.md).

The duration-computation rule above uses the declared layer end, which is `start_ms + duration_ms` per layer.

### Layer identifiers

Every layer `id` MUST be unique within the document. Two layers MUST NOT share the same `id`. A validator MUST reject any document in which two or more layers have the same `id`.

## Unknown properties

Every root, layer, source, pitch, volume, filter, frequency-entry, level-entry, and spatial-effect object is closed. A document containing an unknown property is invalid. Future fields require a future schema version.

## Required vs optional visual key

Throughout this specification:

- **Bold "Yes"** under Required means the field must be present.
- "No" under Required means the field is optional. Its Default cell states whether omission applies a value or leaves the field absent.
- **"--"** under Default means the field has no default -- if required, it must be explicitly set; if not required, it is absent when omitted.
