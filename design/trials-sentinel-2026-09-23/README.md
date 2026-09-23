# Trials sentinel — 2026-09-23

A single generated image: an antique brass sand-timer, engraved in line on black, placed as the decorative ornament in the Settings **Trials & renewals** pane header beside the title `Free trials, kept visible.`

## Why this surface

The pane's subject is the time left before a trial converts or a renewal charges, so an instrument that measures time belongs here rather than on a surface with no such subject. The pane is routed and reachable (`/meridian/settings?section=trials`), and it carried no artwork while the Settings hub corner already carries a hand-drawn engraving. The ornament is additive: no existing element was replaced, so `templates/meridian/partials/observatory-engraving.html` keeps the `currentColor` behaviour that lets a vector follow the theme.

The owner approved both the generation and the integration on 2026-09-23, which D-021 §4 requires because delivery and integration are separate decisions.

## Generation

One Runway task through the existing Composio connection, per D-021.

| Field | Value |
|---|---|
| Model | `gpt_image_2` |
| Ratio / quality / outputs | `1920:1280` / `high` / 1 |
| Task id | `46eb3dc5-c9ce-4413-8150-722bf5e5e36f` |
| Cost | 20 credits (balance was 500; D-021's decision-time figure of 500 was not the per-image cost) |
| Reference images | none |

The exact prompt is `prompt.txt`. The raw 1920×1280 RGB master is kept here as `master-gpt-image-2.png` so the delivery survives the generation URL's expiry. The prompt asks for no text, no numerals and no measurement graduations, because `ASSET_MANIFEST.md` states that decorative assets never carry financial meaning.

## Derivation

The service returns an opaque master. `scripts/key_raster_background.py` derives alpha from luminance and crops to the visible ink plus 12px:

```sh
python scripts/key_raster_background.py \
  design/trials-sentinel-2026-09-23/master-gpt-image-2.png \
  static/img/meridian/observatory/trials-sentinel-hourglass.png \
  --floor 16 --crop-pad 12
```

Re-running that command on the master with those values reproduces the delivered asset byte for byte. `assets.json` carries the dimensions, mode, alpha extrema, visible bounds and the sha256 of both the master and the delivered asset.

## Integration

- `static/img/meridian/observatory/trials-sentinel-hourglass.png` — 607×1222 RGBA, 76.0% of pixels fully transparent, all four corners transparent.
- `templates/meridian/partials/trials.html` — an `aria-hidden` ornament slot in the pane's existing `.m-settings-command` header.
- `static/css/meridian/settings.css` — `.m-trials-sentinel` renders the PNG as a CSS `mask`, the same pattern the Settings row glyphs use, so the engraving takes `--obs-brass` and follows the theme instead of freezing the generated colour. The light theme overrides the colour to a darker bronze, because measured brass on the light canvas `#f4ecdf` is too low-contrast to read.

This is decoration and nothing else. It is not a control, not a status indicator, and not an account icon; it shows no deadline, count, or progress, and it carries no data of any kind.

## Capture evidence

`artifacts/trials-sentinel-2026-09-23/` holds the governed capture of `/meridian/settings?section=trials` across the five viewport/DPR pairs and both themes, produced by `scripts/capture_settings_surfaces.py` against the isolated synthetic preview (`http://127.0.0.1:8093`, `--fixture synthetic-settings`). Those files are captures rather than shipped code, so `tests/meridian/test_static_assets_tracked.py` excludes them from the tracked trees by design.
