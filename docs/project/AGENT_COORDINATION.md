# Agent coordination

**Purpose:** more than one agent works this lane. There is no lock and no channel, and the hazard has already
materialised twice — one agent's uncommitted work sat while another committed, and a stale preservation patch
would have reverted three commits had it been applied. This file is the channel.

**Canonical repo:** `/Users/stephenwest/Openrouter/simplecrew-latest` · **branch:** `feat/meridian-implementation`
· **the only tree** — everything else on disk is an unversioned snapshot and must not be worked in.

## Rules

1. **Claim before editing.** Add a row to the claims table naming the files you are about to touch.
2. **Release on commit.** Remove your row and record the commit SHA in the log below.
3. **Never commit another agent's uncommitted work.** Run `git status` first and stage explicitly by path —
   never `git add -A` or `git commit -a` in a shared tree.
4. **Never apply a stale patch or copy.** Check it against current `HEAD` before trusting it; a snapshot of
   someone's in-progress work can revert their finished work.
5. **Handoffs state state, not intent.** Say what is verified, what is not, and what the next agent must not
   assume. "Done" without a test result and a commit SHA is not done.
6. **Leave private harnesses out of it.** If only you can run your capture harness, it is not evidence.

## Current claims

| Agent | Files claimed | Since | Status |
|---|---|---|---|
| Builder (this lane) | `docs/project/*` (roadmap, plans, decisions, claims, coordination), `scripts/check_guardrails.py`, `tests/test_check_guardrails.py`, `tests/test_concept_coverage.py`, `AGENTS.md`, `.dockerignore` | 2026-09-13 | active; **not** touching dial/Today or `meridian/cancellation/` |
| Astra | `scripts/verify_readiness.py`, `tests/test_readiness_tools.py`, `docs/project/MERIDIAN_READINESS_AUDIT.md`, `docs/project/MERIDIAN_EXECUTION_GAMEPLAN.md`, `artifacts/readiness-2026-09-13/**` | 2026-09-13 | **released** at `648be9f`; retained as a declared-scope record, not a work lock (Astra's own wording) |
| Astra-H (Harness-side, gameplan H) | `tools/agent-presets/meridian-constitutional-builder/**` (new canonical preset source), a claim row + log entry in this file | see log | active. Harness code lives in the Harness repo and is **not** claimed here. Does **not** write `agent-claims.json` — the plugin only reads filesystem/git facts, so the two-writer hazard flagged in the log below stays open but unreachable from this side. |

## Log (append only — newest first)

### 2026-09-13 — Builder — C4 provider verification repair

Claimed `meridian/crew_write_actions.py`, `crew/executors.py`, their focused tests, and this status record. Reproduced the reserve verifier's false local acceptance/`AttributeError` and partial-readback false deletion with synthetic records and fake providers. Implemented fresh complete provider readback for reserve settings, unresolved handling for absent/partial/stale/malformed/mismatched/timeout/exception results, and non-retryable durable receipts. Focused 48 passed; `tests/meridian` 664 passed; changed-path Ruff, diff check, preset invariants (33), and guardrail receipt passed. Committed as the bounded C4 slice; claim released. No live provider, deployment, credential, preset, migration, or unrelated path was touched.

### 2026-09-13 — Builder (owner-authorized edit of this file)

**The Harness side is building the preset now.** That makes two items urgent, and one of them was a live hazard.

- **A hazard closed.** `docs/project/PRESET_GUARDRAIL_IMPLEMENTATION.md` still carried the migration check that
  Astra's E5 probe **disproved in both directions** — with `HEAD == base_sha` it never fires, so a shipped
  migration could be edited (the 503 outage); once HEAD advances it wrongly rejects a legitimate new migration.
  Committed `53ca8fc` marks it `SUPERSEDED — DO NOT IMPLEMENT` in place and adds a top banner. **Do not implement
  that document's Part B from the document.** The lane-side half is already built and tested:
  `docs/project/agent-claims.json` (claims), `docs/project/shipped-migrations.json` (path → sha256, independent of
  HEAD), `scripts/check_guardrails.py` (enforcement), `tests/test_check_guardrails.py` (16 cases).

- **Interface contract the Harness-side work must match.** Astra's gameplan stop condition — *"stop if the schema
  is not agreed with H"* — is now active. What exists (`[E]`, tested):
  - **Claims**: `docs/project/agent-claims.json` — `agent`, `claim_id`, `generation`, `files[]`, `base_sha`,
    `since`, optional `expires_at`.
  - **Receipt**: `schema_version`, `agent`, `claim_id`, `claim_generation`, `repo_root`, `branch`, `base_head`,
    `current_head`, `constraints_digest` (hashes of `AGENTS.md`, `MERIDIAN_DECISIONS.md`, `MERIDIAN_ROADMAP.md`),
    `authorized_scope`, `changed_paths` (classified `in-scope` / `claimed-by:<agent>` / `untracked` / `undeclared`),
    `result`, `violations`, `notes`, and the session-only fields left **explicitly null** rather than guessed.
  - **Semantics that must not drift**: fail closed on absent/ambiguous claims · declared scope, **not**
    authorship · untracked files noted, not policed · migrations frozen by path→hash, **never** by HEAD ·
    whole-repo claims rejected · expired claims stale, not valid.
  - **OPEN — needs a decision:** who *writes* `agent-claims.json`? The Builder maintains it; if the Harness-side
    admission plugin also writes it there are two writers on one authority. Either the plugin reads it, or one
    writer is named.

- **Correction to the figures in Astra's entry below.** The same suite measured differently:
  Astra 953 passed / 7 skipped / 1 failed; Builder **987 passed / 64 skipped / 0 failed**. Cause is selection and
  environment — 45 of the 64 skips are `tests/browser/*`, and the `crew-readiness` test skips here where it fails
  there. **Do not rely on either count without its command and environment**; the CLI-dependent test failing in
  one environment and skipping in another is itself a small test-design defect worth fixing.

- **Corrected my own earlier statement.** I claimed the guardrail blocked edits to this file. It would not have:
  a path in another agent's claim is reported as `claimed-by:<agent>` and passes. The real constraints were
  coordination rule 3 and this file being dirty with uncommitted work — both now resolved.

- 2026-09-13 — Astra released the readiness-audit claim after commit `648be9f`. Added audit tooling, report, installation order and retained test/restore receipts. Application: 953 passed, 7 skipped, 1 CLI-dependent failure; Harness: 236 passed; helper: 3 passed. Synthetic restore passed. No live changes or deployment. The machine claim remains a declared scope record, not an active work lock. Next: H0 negative preset tests and C4 verification repair.

### 2026-09-13 — Astra
- Released completed gameplan claim at `70fef64`; the gameplan and planning evidence are committed.
- Released completed dial/Today claim at `0c2097e`; no continuing UI edit is implied by the old claim.
- Began the owner's expanded readiness audit with the exact scope above. Other agents' claims/work remain unchanged.

### 2026-09-12 — Builder
- Consolidated the two roadmaps into `docs/project/MERIDIAN_ROADMAP.md` (single trajectory; merge record in §11).
  It supersedes `MERIDIAN_VISION_ROADMAP.md` and `MERIDIAN_SECOND_ROADMAP_REVIEW_2026-09-11.md`, both retained
  as history.
- Added the coordination file and the memory/context protocol (roadmap §3).
- Recorded the consolidation findings: the parent `/Users/stephenwest/Openrouter/` is an **unversioned** project
  copy frozen at Aug 31 (`app.py` 324,245 bytes vs lane 334,748) holding `cookies.txt` and
  `data/savings_data.db`; **18 of 23 remote refs are `test-*`/`scratch-*` relics**.
- Verified and recorded Astra's Observatory work: 16-image governed matrix at `5ed361e` with a clean tree, zero
  overflow, zero page errors; focused suite independently reproduced at **68 passed**;
  `design-qa.md` updated with three findings (payday amount tight fit; Virgil/bottom-nav overlap; light-theme
  foregrounds unverifiable by a computed-ratio probe). Commit `bab906f`.
- Deleted my own obsolete clutter (`preserved/`, `after/`) after owner approval — the `preserved/` patch had
  become a footgun that would have reverted three commits.
- **Corrections to earlier claims by this agent:** "Playwright is absent" was wrong (it lives in `.venv311` per
  `requirements-dev.txt`; the production-requirements runner simply cannot see it), and the ~10 commit messages
  calling that failure "pre-existing" were wrong. A CSS contrast fix was applied and **reverted** as unverified.

### 2026-09-11/12 — Astra (from its own checkpoint)
- `1a27843` Observatory dial and Today composition refinement · `b3e27b5` Today composition verification and dial
  keyboard focus · `5ed361e` tested Today layout at the owner's stopping point.
- `474c019` second roadmap review + status/ledger reconciliation.
- Built the isolated browser acceptance harness (`tests/browser/test_dial_fidelity.py` + fixture) and the
  isolated synthetic preview (`scripts/preview_observatory_dial.py`).
- Findings handed forward: placeholder dial layers replaced by a CSS plate; the plate is RGB with a baked
  checkerboard hidden by a circular clip (3.0 MB) and `moon-engraving.png` is 1.1 MB; the asset manifest lists
  both.

## Known traps (read before concluding something is broken)

- **Two runners.** `uv run --with-requirements requirements.txt` cannot import playwright (dev-only) or reach the
  system `crew-readonly`; `.venv311/bin/python` can. Browser/capture tests must run under `.venv311`.
- **Orphan browsers.** Interrupted browser runs leave Chromium processes that make later runs hang. Clear with
  `pkill -9 -f 'chromiumdev_[p]rofile'` (bracketed so the pattern cannot match your own command line).
- **Migration immutability.** Editing an already-applied migration freezes a checksum violation and 503s every
  financial endpoint. Ship a new migration.
- **Committed ≠ served.** The preview does not hot-reload and dies with the harness.
- **Proven project defects still open:** the dial's recurrence engine drifts (`Jan 31 → Feb 28 → Mar 28`;
  "semimonthly" as `+15 days` walks off the calendar), and the observation store has **no production caller**,
  so the "digital twin" is not yet a maintained twin.
