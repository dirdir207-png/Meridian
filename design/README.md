# Meridian design

The Observatory direction combines midnight blue, parchment, brass details, and engraved illustrations.

| Record | What it is |
|---|---|
| [Original Observatory concepts](observatory-drafts-2026-09-08/) | The first direction: the selected-direction image and the per-screen drafts (Today, Plan, Activity, Accounts), with the build spec beside them. |
| [Timeline, Review, Settings, and Virgil studies](observatory-extension-2026-09-18/concepts/) | That direction extended to surfaces the first pass did not cover. |
| [Sun study](observatory-sun-2026-09-19/) | A single-asset study, with its prompt and asset metadata. |
| [Investigator medallions](investigator-medallions-2026-09-21/) | The medallion handoff scoped by D-018: implementation notes, verification, the assets and a rendered reference. |
| [Logos](logos/) | The mark set as SVG -- shield, orbit pocket, SC monogram, beacon and wordmark -- with an index. |
| [Settings calibration ornament](settings-calibration-ornament-2026-09-22/) | A single-image asset delivery: the small brass calibration-instrument vignette that sits beside the Settings title, generated 2026-09-22 with built-in ImageGen from the 09-18 Settings concept as reference. Delivered and indexed, NOT integrated. |
| [Plan map marks](plan-map-marks-2026-09-23/) | Four generated brass marks for the Plan allocation map -- the concept's domed rotunda, flagged mountain, star rose and knobbed hub compass -- so the map draws raised metal instead of flat kit silhouettes. Made with Runway `gpt_image_2` per D-021 (80 credits, owner-approved); prompts, raw masters and the alpha derivation recorded. Delivered and integrated 2026-09-23. |
| [Trials sentinel](trials-sentinel-2026-09-23/) | A single generated image: the brass sand-timer that now sits in the Settings Trials & renewals command header. Made with Runway `gpt_image_2` per D-021, with the exact prompt, the raw master and the alpha derivation recorded. Delivered and integrated on the owner's 2026-09-23 approval. |
| [Observatory moon](observatory-moon-2026-09-24/) | Not a new drawing: the derivation record for Today's existing moon engraving, whose SHIPPED asset was opaque on a flat `#101a28` field that does not match the page's `#161c34` navy, so it read as a block of a different blue (owner-reported 2026-09-24). Holds the original opaque master, the colour-distance alpha derivation and the keying tool's own report. The record any future change to this asset must start from. |
| [Reserve Timeline studies](reserve-timeline-2026-09-26/) | Three synthetic ImageGen studies for the Reserve Timeline (Observatory Ledger, Pay-cycle chapters, shortfall lens), with a manifest and the implementation handoff. Design scope only — the surface itself awaits the owner's pass. |

These are design studies, not screenshots of a released product. **The newest explicit governing record takes precedence over historical screenshots and intermediate captures (D-004), so establish which record governs a surface before doing visual work on it.** The table is chronological, not a ranking, and it is checked: every record in this tree must be named here, because an index that omits the newest records answers D-004's question wrongly rather than declining to answer it.

## Which record governs which surface

Named here because the 09-08 folder is **a set of choices, not a specification** — it holds several
mutually exclusive drafts of the same screen, so "the 09-08 concepts" cannot be cited as an
authority without saying WHICH file.

| Surface | Governs | Supersedes, and why |
|---|---|---|
| **Today** | [`06-interactive-observatory-vision.png`](observatory-drafts-2026-09-08/06-interactive-observatory-vision.png) — owner-confirmed 2026-09-25 | `01-today.png` and `00-selected-direction.png`, which draw the Safe-to-Spend figure INSIDE the dial's centre. The owner selected 01 first, then judged 06 vastly superior and changed course: 06 puts the figure **outside** the compass in the header strip and lets the **dial centre state the selected event** (the concept reads `FRI, SEP 11 / Electric / $84 / Reserved`). Only 06 matches the shipped instrument, and OS-098 (`1543c5e`, owner direction 2026-09-24) is the change that made the app match it. |

Recorded after a real mis-read: this session's first pass at OS-079 checked only `00` and `01`,
concluded the app was wrong, and had to be corrected by the owner. A folder of alternatives is not
an authority; the governing FILE is.
