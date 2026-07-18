# Non-normative render cases

`render-cases.json` connects valid Piccle documents to expected frame schedules. It verifies document duration, layer intervals, declared fade locations, hard truncation, reverb tail length, and terminal-window length without prescribing PCM output.

The normative timing rules remain in `docs/05-layer-volume.md`, `docs/07-reverb.md`, `docs/08-output.md`, and `docs/11-engine-safety.md`. Engines should reproduce these cases in their own scheduler tests.
