# Today's moon engraving — opaque master and derivation

The celestial scene beside Today's Safe-to-spend figure: a partially-lit engraved moon, dotted
orbital ellipses, and gold stars.

## Why this directory exists

The shipped `static/img/meridian/observatory/moon-engraving.png` was **opaque**, drawn on a flat
field of `#101a28`. That field was specified deliberately — `OBSERVATORY_REFINEMENT_2026-09-12.md`
records the asset as "uniform `#101a28` background … no text/numerals/UI/transparency" — and the
Today page's own navy is `#161c34`. The two differ by enough to be visible, so the asset rendered as
a **rectangular block of a different blue** behind the moon, and a `border-radius: 50%` circular clip
was added to the element to soften it. The owner reported it on 2026-09-24: *"the moon image needs to
have transparency so it doesn't have a block of different colored blue behind it."*

## How the alpha was derived

`scripts/key_raster_background.py --strategy colour`, with the master as input:

```
.venv311/bin/python scripts/key_raster_background.py \
  design/observatory-moon-2026-09-24/moon-engraving-opaque-master.png \
  static/img/meridian/observatory/moon-engraving.png \
  --strategy colour
```

**Colour, not luminance, and the reason is recorded because it cost a measurement to find.** The
luminance strategy (the tool's original and still its default) keys a subject brighter than its
field. This asset's subject CONTAINS the field's colour: the moon's unlit limb is the same navy, and
its cratered interior sits only ~19 RGB units from it. A luminance key at any floor that removes the
field also removes the moon — measured, the moon's own centre keyed to alpha 0 at floors 30, 40, 50
and 60, i.e. the scene would have shipped as a crescent outline with no moon in it.

Distance from the field colour is the separation that actually works: the flat field is within ~6
units, the moon's interior at ~19.5. With `tolerance=12` (fully clear at ≤12, fully solid at ≥18 on
the `_COLOUR_RAMP = 1.5` ramp) the field clears completely and the moon keeps its limb and craters.

## Result

`key-report.json` holds the tool's report verbatim. Summary:

| Fact | Value |
|---|---|
| Dimensions | 1254×1254, RGBA |
| Fully transparent | **96.67%** of pixels |
| Corners | `(17,28,42,0)`, `(16,29,43,0)`, `(17,29,45,0)`, `(15,27,41,0)` — all zero alpha |
| Reference colour read from the frame's corners | `(17,28,42)` |
| Tolerance / opaque-at | 12 / 18 RGB units |

The moon's dark limb and crater detail survive: a composite of the keyed asset over the page navy
(`#161c34`) shows the full disc reading exactly as the engraving draws it, with the orbits and stars
intact and no rectangular edge.

## Files

| File | What it is |
|---|---|
| `moon-engraving-opaque-master.png` | The original opaque asset, kept so the derivation can be re-run or re-tuned. Bit-identical to what shipped before this change |
| `key-report.json` | The keying tool's own report for this derivation |
