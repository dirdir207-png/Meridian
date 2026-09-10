# Meridian Observatory Dial — new-session handoff (2026-09-09)

This is the continuation handoff for the next anchored-standard session.
It is deliberately scoped to the **Observatory dial concept-fidelity pass**,
because the owner asked for sole focus there until the dial matches or
surpasses the concept art. It is not a claim that the full Meridian project is
complete.

## 1. Session identity and instruction

Resume in:

```text
/Users/stephenwest/Openrouter/simplecrew-latest
branch: feat/meridian-implementation
repo:   dirdir207-png/ORSC
```

Primary instruction from the owner:

> Keep going autonomously, using deployed subagents or subagent swarms where
> it makes sense. Continue until YOU feel confident you matched or surpassed
> the concept; all features should be treated this way.

For this session, keep the dial as the sole focus. Do not drift back into
Plan/Activity/Accounts/Settings unless the owner explicitly changes scope.

Before coding, read:

- `design/observatory-drafts-2026-09-08/BUILD_SPEC.md`
- `docs/project/MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md`
- `docs/project/PROJECT_INSTRUCTIONS.md`
- `docs/project/CURRENT_STATUS.md`
- this handoff
- all seven reference PNGs in `design/observatory-drafts-2026-09-08/`

## 2. Current git state

At handoff time:

- Verify the actual current HEAD with `git log --oneline -1`; this handoff is
  committed and may be one commit behind the live branch tip.
- At handoff time the branch was **45+ commits ahead** of
  `origin/feat/meridian-implementation` and had no tracked dirty files.
- The handoff commit is `928339c`; two follow-up inspector commits are
  `eb1e64f` (observation-record kicker) and `c39daf9` (signed amount/signal colors).
- untracked machine-local/design artifacts:
  - `.env.save` — DO NOT COMMIT
  - `tmp/` — DO NOT COMMIT
  - `artifacts/design-audit/`, `artifacts/observatory-preview/` — local preview artifacts
  - `design/observatory-drafts-2026-09-08/` — reference art, may remain untracked
  - `docs/project/MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md` — consolidated handoff, may remain untracked
  - `output/pdf/Meridian_Consolidated_Handoff_2026-09-08.pdf` — may remain untracked
  - `docs/superpowers/specs/2026-09-09-trial-canceler-design.md` — unrelated untracked design note; leave it

Never commit `.env.save`, `tmp/`, secrets, or credentials.

## 3. Safety boundaries

- No live financial mutation in tests or preview work.
- The dial is read-only. Selection/scrubbing must never POST to a mutation
  endpoint.
- Existing financial write paths remain approval-gated; do not add direct
  Crew mutations while improving visuals.
- Do not expose token material, credential IDs, PAN/CVV, or `.env` contents in
  browser output, logs, docs, or commits.
- Do not write to `/Users/stephenwest/Documents/ChatGPT/Simplecrew Branch`.
  This execution lane is ORSC only.
- Preserve unrelated changes and the current branch. Do not merge to `main`.

## 4. What has already landed (dial-focused)

Key commits from the dial pass:

- `c81d776` — parchment instrument face, engraved rim/rivets, dark sky disk,
  starfield, observatory engraving, golden star-centered pointer, compact
  real-data center, event rail.
- `3804559` — human-readable observation timestamp on the evidence ticket.
- `fcdcea2` — moved the dial into the primary Today view.
- `c1d627f` — compact safe-to-spend strip above the dial.
- `4719099` — stronger parchment surface, engraved ticks, kind-colored orbit
  markers, event-rail icons/date cards, Explore-my-plan CTA.
- `4b83f86` — fixed selection so clicking an event or marker updates the
  center and evidence ticket.
- `3109d2a` — defaults to the first upcoming money moment, so the dial is
  populated on load.
- `b65cd1b` — add orbit leader lines to markers.
- `b8f5c57` — visible kind-colored markers.
- `d04e687` — stronger observatory/lunar engraving.
- `9dadd40` — full-width desktop Today stage so the dial owns the composition.
- `4a2d396` — real "Crew · observed" source stamp above the dial.
- `2b539b5` — Today title + truthful orbit subtitle matching the concept.
- `7d5aae9` — paper/ink texture WEBP assets, applied to parchment/indigo.
- `ce800b4` — browser test for read-only selection and mobile overflow.
- `1c04dba` — day labels seated on the parchment rim.

Important implementation files:

- `static/js/meridian/dial.js`
- `static/css/meridian/dial.css`
- `templates/meridian/partials/today.html`
- `static/css/meridian/today.css`
- `static/css/meridian/observatory.css`
- `static/img/meridian/observatory/` (assets + `ASSET_MANIFEST.md`)
- `tests/meridian/test_dial_js.py`
- `tests/browser/test_observatory_dial.py`

The dial currently has:

- full parchment ring, dark sky disk, starfield, observatory engraving
- real selected-event/available-spend center
- day labels around the ring
- kind-colored event markers with dashed leader lines
- event rail showing all upcoming money moments
- selected evidence ticket with engraved corners and a source observation
- "Days to payday →", "Turn to explore your week", "Explore my plan"
- read-only pointer/scrub/range/keyboard controls
- no non-GET request during selection, verified by browser test

## 5. Remaining dial gaps before confidence

These are the next concrete targets, in priority order:

1. **Fix the date-sensitive dial service test.**
   - `tests/meridian/services/test_dial.py::test_build_dial_returns_empty_horizon_when_no_records`
     expects `freshness == "fresh"`, but the fixture timestamp
     `2026-09-08T09:00:00Z` is now older than the 24-hour freshness threshold
     relative to the actual machine date (2026-09-09).
   - Preferred fix: make the test clock-safe by passing an explicit `now`/as-of
     to `build_dial`/`data_freshness` rather than weakening freshness logic.
   - Do not change production freshness rules just to satisfy a stale fixture.

2. **Event orbit composition.**
   - The concept has outside event labels with dashed, connected orbital
     leaders; currently the event rail is adjacent and the markers have short
   leaders. Push closer with either connected labels or a stronger rail
   relationship, while keeping the accessible HTML event list as the source
   of truth.

3. **Center spacing.**
   - The selected event/amount block can still visually crowd the dark disk on
     some desktop widths. Tighten without shrinking essential text below
     readable sizes.

4. **Mobile flow.**
   - The mobile dial + event rail + ticket + CTA stack is close but long.
     Improve the first viewport relationship while preserving 390px no-overflow.

5. **Asset polish.**
   - The current engravings/textures are in-repo placeholders derived from the
     direction. Only replace with approved/licensed art or the owner's chosen
     generated art. Keep decorative assets separate from financial geometry.

6. **Visual comparison.**
   - Compare current desktop/mobile screenshots against
     `01-today.png` and `06-interactive-observatory-vision.png` at supported
     widths. Inspect the actual screenshots, not merely file existence.

## 6. Verification commands

The system `pytest` at `/usr/local/bin/pytest` is broken (old Homebrew
Python). Use one of these:

```bash
cd /Users/stephenwest/Openrouter/simplecrew-latest

# Current local 3.11 venv:
.venv311/bin/pytest tests/meridian -q --disable-warnings --maxfail=1

# If the venv is unavailable, uv route (per project memory):
~/.local/bin/uv run --python 3.11 \
  --with-requirements requirements.txt \
  --with pytest python -m pytest tests/meridian -q --disable-warnings
```

Known result at handoff time:

- `tests/meridian`: recollect and run the full file set in this session before
  relying on a count; at handoff time the known blocker is the date-sensitive
  `test_build_dial_returns_empty_horizon_when_no_records` test described above.
- `tests/browser/test_observatory_dial.py`: **2 passed** with
  `APP_URL=http://127.0.0.1:8081`
- `ruff check app.py crew meridian tests`: clean
- Full non-browser baseline: 651 passed, 1 skipped, 1 pre-existing isolated
  failure in `tests/test_app_evidence_integration.py::test_evidence_content_resolves`
  (unrelated to Observatory)

Dial browser command:

```bash
APP_URL=http://127.0.0.1:8081 .venv311/bin/pytest \
  tests/browser/test_observatory_dial.py -q --disable-warnings --maxfail=1
```

## 7. Preview server

The owner views the preview from an iPhone over Tailscale, not Wi-Fi.

Preview URL:

```text
https://stephens-macbook-air.tail690234.ts.net/login
```

Local:

```text
http://127.0.0.1:8081/login
```

Start/restart the preview **with `.env` sourced** so Virgil/DeepSeek remains
connected:

```bash
cd /Users/stephenwest/Openrouter/simplecrew-latest
pkill -f 'run_preview.py' 2>/dev/null || true
set -a; . ./.env; set +a
DB_FILE=/Users/stephenwest/Openrouter/simplecrew-latest/savings_data.db \
  nohup .venv311/bin/python run_preview.py \
  > /tmp/meridian-preview.log 2>&1 &
```

Notes:

- The preview server was previously restarted without sourcing `.env`, which
  disconnected Virgil/DeepSeek. That was an environment mistake, not a code
  revert.
- Flask is running with `debug=False` and no reloader. **Template changes
  require a server restart.** Static JS/CSS changes are served from disk and
  usually appear on reload.
- Preview screenshots are saved under `artifacts/observatory-preview/`.
- The owner likes screenshot updates. Generate them with Playwright after
  meaningful visual changes.

## 8. Next-session opening checklist

1. Confirm `git status --short --branch`; preserve untracked secrets/artifacts.
2. Read the dial files and the two relevant reference PNGs.
3. Fix the date-sensitive test safely.
4. Pick the next dial visual/functional gap from §5 and implement one small
   testable slice.
5. Run targeted tests and the browser dial test.
6. Regenerate desktop/mobile screenshots and report the path.
7. Commit with a clear `feat:`/`fix:` message; do not amend unrelated commits.
8. Update `docs/project/CURRENT_STATUS.md` at the end of the session.

Do not declare the dial or project complete until the owner confirms the
concept fidelity and the remaining workspace features have had the same
treatment.
