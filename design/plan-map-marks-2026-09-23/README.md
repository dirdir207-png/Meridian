# Plan map marks -- 2026-09-23

Four generated brass marks for the Plan workspace's allocation map, so the map's icons are the
marks the governing concept draws rather than the flat single-colour kit silhouettes it was
using.

## Why generation, and why these four

`design/observatory-drafts-2026-09-08/02-plan.png` draws the map's marks as RAISED brass: a domed
rotunda for the Bills station, a mountain summit with a flag for Goals, one eight-point star rose
for Available, and -- as a full-resolution read later confirmed -- a LARGER compass for the hub
with its own medium-thick solid bezel carrying rivet knobs at north and south.

Three zero-spend routes were checked and rejected on evidence before spending anything:

* the kit's 63 Bootstrap glyphs contain **no domed building and no mountain** in either kit, so the
  motifs cannot be matched from what is tracked;
* `accounts-ticket-building.png` (the owner's own domed building) is painterly full-colour art with
  scrolls and an open book, and compositing it on navy at 34/54/96px showed it reads as an
  unreadable blob at medallion size;
* narrowing the map to reuse an existing mark changed nothing about the icons themselves.

The owner approved four marks at 20 credits each. **80 credits were spent** through the existing
Runway connection under D-021, from a balance of 500 read read-only immediately before the first
generation.

## Generation

One `RUNWAY_GENERATE_IMAGE` task per mark: `gpt_image_2`, `1920:1920`, quality `high`, one output,
opaque background, no reference images. Each master is kept here so the delivery survives the
generation URL's expiry; the task ids and per-asset credit cost are in `assets.json`.

The prompts (`prompts/*.txt`) describe each object from a 4x crop of the concept rather than from
memory, and every one of them forbids text, numerals, discs, rings and frames -- except the hub,
whose bezel IS the subject and whose prompt instead requires the interior to stay the same flat
black as the background so the alpha key leaves it transparent over the disc.

## Derivation

`scripts/key_raster_background.py` derives alpha from luminance and crops to the visible ink plus
12px, exactly as the trials sand-timer does. The delivered copies in
`static/img/meridian/observatory/` are additionally resized to a 256px maximum edge: the marks are
drawn at 23-40 CSS px (69-120 device px at DPR 3), so 256px keeps roughly 3x headroom without
putting megabytes into the repository for a glyph.

## Integration, and one correction

`allocationMark()` in `static/js/meridian/plan.js` maps a segment to a mark, and the mark is applied
as a background IMAGE rather than a mask: masking it to a single brass token would flatten exactly
the raised highlight and shadow the owner asked for. A segment the concept never draws keeps its kit
glyph.

The first delivery used ONE star for both the hub and Available, on the reading that the concept
draws the same motif at two sizes. The owner compared it with the concept and reported that "the
top star is different than the bottom one"; a full-resolution read confirmed a thick solid bezel
with rivet knobs on the hub against a thinner rim and shorter points on Available. The hub compass
was therefore generated as the fourth mark, and what had been the shared star is now Available's
alone.
