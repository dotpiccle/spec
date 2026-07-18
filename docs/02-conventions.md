# Conventions

This chapter defines Piccle's JSON, naming, unit, timing, and contour conventions. These rules are normative unless marked otherwise.

## JSON representation

A Piccle document MUST be UTF-8 encoded JSON as defined by [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html). The Piccle requirements below are authoritative where they are stricter than the base JSON specification.

- The root value MUST be an object.
- Object member names MUST be unique. A parser MUST reject duplicate member names rather than keeping the first or last value.
- Unknown properties are invalid at every object level. The schema expresses this with `additionalProperties: false`.
- Implementations MUST support every integer in the interoperable binary64 range `[-(2^53)+1, (2^53)-1]` while parsing JSON. Individual Piccle fields impose much smaller ranges where required.
- Implementations MUST parse decimal numbers with at least IEEE-754 binary64 precision for control calculations. Audio sample storage may use binary32 as defined by the canonical render profile.
- When a decimal is converted to binary64, use round-to-nearest, ties-to-even. A parser that retains greater precision MUST produce the same binary64 value before canonical control evaluation.
- `NaN`, `Infinity`, and `-Infinity` tokens are not JSON and MUST fail JSON parsing with code `json.non_finite_number`.
- A syntactically valid decimal token whose mathematical value cannot be represented as finite IEEE-754 binary64, such as `1e400`, MUST fail JSON parsing with code `json.number_out_of_range`. An engine MUST NOT silently convert it to infinity before validation.
- JSON Schema's `integer` type is mathematical, not lexical. A JSON number such as `1`, `1.0`, or `1e0` satisfies an integer field because its value has no fractional part. Engines MUST accept all three forms when the value meets the field's range.
- Object member order has no semantic meaning. Array order has meaning only where this specification explicitly defines it.

The optional root `$schema` member, when present, MUST equal `https://spec.dotpiccle.com/schema/v1.json`.

## Unit conventions

### Time: milliseconds (`*_ms`)

All document time values are integer milliseconds no greater than `9007199254740991` (`2^53-1`) and use an `_ms` suffix. Durations and reverb tails are at least `1`; offsets, fades, holds, and transitions are at least `0`.

- `duration_ms` — total sound or layer length.
- `fade_in.ms` — layer fade-in duration.
- `fade_out.ms` — layer fade-out duration.
- `start_ms` — layer start offset.
- `hold_ms` — hold time at a contour value.
- `transition_ms` — time to move to the next contour value.
- `tail_ms` — reverb RT60 and emitted-tail duration.

The exact conversion of document and layer boundaries to sample frames is defined in [Engine Safety and Render Profiles](11-engine-safety.md).

### Frequency: Hertz (`*_hz`)

Frequency values use Hertz. A field name uses `_hz`, except for `frequencies[].hz`, where the array supplies the context.

- `soften_hz` — reverb wet-path lowpass frequency.
- `frequencies[].hz` — pitch or filter frequency.

### Pitch offset: cents

`offset_cents` is an integer pitch offset. One hundred cents equals one equal-tempered semitone.

## Naming conventions

Field names use `snake_case`. Enumerated values use the spelling and case published by the schema; values are case-sensitive.

Defaults generally represent an identity or safe baseline:

- `start_ms: 0` — start at the document origin.
- `balance: 0` — centered.
- `resonance: 0` — Q = 0.707.
- Layer `fade_in.ms: 0` — no fade-in.
- `hold_ms: 0` — no hold.
- `transition_ms: 0` — instantaneous transition.
- `transition_curve: "linear"` — linear interpolation.
- `offset_cents: 0` — no detuning.
- `seed: 0` — the default deterministic noise stream.
- Root and layer `volume: 1` — unity gain.

Fields that choose a sound characteristic, such as source `type`, `wave`, `character`, and reverb fields, have no implicit default unless their field table states one.

## Volume and balance scales

Volume values are linear amplitude gains from `0` through `1`. They do not control the device's operating-system volume.

`balance` ranges from `-1` through `1`. Piccle uses equal-power mono-to-stereo panning; the exact equations are defined in [Output](08-output.md).

## Contour model

Pitch, volume, and filter contours use ordered target arrays. For an array with `n` entries:

1. Entry `0` is the value at contour time zero.
2. For each entry `i` from `0` through `n-2`, the engine holds entry `i` for `hold_ms[i]`, then transitions from entry `i` to entry `i+1` for `transition_ms[i]`.
3. The `hold_ms`, `transition_ms`, and `transition_curve` members on the last entry are ignored.
4. After the last target is reached, its value is held until the layer ends.

For pitch and filter contours, contour time zero is the layer start. Their scheduled duration is:

```text
Σ(i = 0 .. n-2) (hold_ms[i] + transition_ms[i])
```

For an object-form layer-volume contour, transitions begin after `fade_in.ms`. Its scheduled duration is:

```text
fade_in.ms
+ Σ(i = 0 .. n-2) (hold_ms[i] + transition_ms[i])
+ effective_fade_out_ms
```

where:

```text
effective_fade_out_ms = min(fade_out.ms, layer.duration_ms)
```

The applicable scheduled duration MUST NOT exceed the declared layer `duration_ms`; otherwise the document is semantically invalid. The shorthand numeric volume has no contour transitions and uses `min(5, layer.duration_ms)` as its effective default fade-out. A shorter explicit document duration hard-truncates this declared schedule without relocating the fade.

All sums used to derive layer ends and output ends are exact integer calculations. A layer end or output end greater than `9007199254740991` makes the document semantically invalid even when every individual field is within its schema range.

The precise sample-frame algorithm, including zero-duration transitions and boundaries, is defined in [Transition Curves](10-curves.md).

## Volume polymorphism

Layer `volume` is the only polymorphic field in v1:

1. A number is a constant base level with a default anti-click fade-out.
2. An object supplies fade stages and one or more `levels` targets.

These forms share the same output-envelope semantics defined in [Volume](05-volume.md).

## Forward compatibility

Unknown properties are invalid in v1. A future optional field therefore requires a new Piccle schema version. A newer engine may support both the old and new schema versions, but a v1.0 validator MUST NOT silently accept fields it does not recognize.
