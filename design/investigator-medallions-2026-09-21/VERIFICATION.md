# Design-deliverable verification — 2026-09-21

## What was checked

- Generated medallions inspected visually against the Accounts reference. Both are 1254×1254 RGBA PNGs. Pillow read-only inspection confirmed alpha range 0–255 and corner alpha 0; hashes and byte sizes are in assets.json. No image postprocessing was performed.
- Specimen served locally on loopback port 8766 and exercised in the Codex in-app browser. It calls no model or API.
- Initial amount-change question rendered the equipment-line comparison. “Explain the charge” changed the question and rendered the two-line-item answer.
- “I returned the equipment.” rendered an unresolved fee question, explicitly labeling owner context as unverified.
- Turning related evidence off reduced “Sources considered” from 2 to 1 and labeled the result direct-only.
- Missing evidence, unavailable model, rejected citation and conflicting sources each rendered their corresponding state.
- Inspected phone-width dark layout (420×912) and desktop light layout (1440×900). DOM width checks: 405 ≤ 420 and 1425 ≤ 1440, no horizontal overflow in those observed states. Desktop image checks showed all four image elements loaded at natural width 1254. Exactly one Investigator panel existed. Browser error log was empty.
- Full-page phone capture had stitching duplication; it is not accepted as a fidelity artifact. This is not the repository's complete governed capture matrix. A later source-link/responsive sweep hit a browser input timeout and was stopped; do not claim that sweep passed. The viewport override was reset and the specimen reloaded for owner review.
- Extracted inline script checked with `node --check /tmp/meridian-investigator-specimen.js` (exit 0). Run again after any specimen change.
- `python3 scripts/roadmap_handoff_check.py` passed before writing the design; rerun during final handoff reconciliation.

## What this does not prove

No application code was implemented or tested, no provider was called, no account data was read, no live model behavior was verified, no production deployment occurred. The specimen's answers are deliberately scripted synthetic data. API/security/financial safety requirements in IMPLEMENTATION.md are acceptance work for Harness, not guarantees established by the specimen.

The two PNGs are full-disc raster masters, not separate vector glyphs. Their exact generation prompts are in prompts.json. The full icon pack is omitted. Visible-disc sizing, delivery optimization, both-theme compositing and actual app visual acceptance remain integration work. The generated art is newly authored and concept-inspired, not exact extracted original artwork.

## Run the specimen again

From the canonical repository, serve static files locally:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/design/investigator-medallions-2026-09-21/investigator.html`. Keep the service loopback-only. If port 8766 is already serving this specimen, reuse it. It is separate from the Meridian application preview and requires no preview restart.

Final documentation checks: `node --check /tmp/meridian-investigator-specimen.js`, `python3 scripts/roadmap_handoff_check.py`, `python3 scripts/generate_handoff.py`, and `git diff --check` all exited 0. OS-076 is an owner-requested follow-on recorded in the ledger; the checker identifies it as outside the existing roadmap text. It is not silently promoted into the roadmap's global critical path.
