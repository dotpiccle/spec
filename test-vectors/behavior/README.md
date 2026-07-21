# Non-normative render cases

`render-cases.json` connects valid Piccle documents to expected frame schedules. It verifies document duration, layer intervals, declared fade locations, hard truncation, reverb tail length, and terminal-window length without prescribing PCM output.

The normative timing rules remain in [Layer Volume](../../docs/05-layer-volume.md), [Spatial Effects](../../docs/07-spatial-effects.md), [Output](../../docs/08-output.md), and [Engine Safety](../../docs/11-engine-safety.md). The Piccle engine qualification suite MUST reproduce every case in its scheduler tests.
