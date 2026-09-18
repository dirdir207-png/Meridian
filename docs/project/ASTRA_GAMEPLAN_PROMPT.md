# Assignment for Astra — the total gameplan

**Paste this into the Harness session. It is self-contained; do not assume shared context with any prior session.**

---

## Your standing in this task

You own the **Harness-side** lane: the DeepSeek Harness source and the installed agent presets
(`/Users/stephenwest/.dsh/.agent-presets/`). You are the authority there.

The **repo lane** is `/Users/stephenwest/Openrouter/simplecrew-latest` (branch
`feat/meridian-implementation`). A different agent maintains it. You may read it freely. Before you **write**
anything there, follow `docs/project/AGENT_COORDINATION.md`: add a claim naming the files, stage by path, never
`git add -A`, and release the claim with a commit SHA when done. Another agent's uncommitted work has already
been caught by that rule once; do not break it.

Owner-gated, permanently, for both of us: production deployment, live acceptance, credential changes,
authority-policy activation, and self-modifying installation (including installing a revised preset).

## Ground truth — load these before planning

Repo `HEAD` at the time of writing: **`713d7b2`**.

| Path | What it is |
|---|---|
`docs/project/README.md` | **Start here.** The entry point: governing authorities, living documents, reference, superseded |
`docs/project/MERIDIAN_ROADMAP.md` | The single trajectory: Track D (design fidelity), Track I (agent council), Track C (capability spine V1–V8), merge record, hazards |
`docs/project/CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md` | **Your own review** of the installed preset |
`docs/project/PRESET_GUARDRAIL_IMPLEMENTATION.md` | The design that implements your review: Harness-side anchors + proofs, and the lane-side half |
`docs/project/AGENT_COORDINATION.md` | Claims table and append-only log; known traps |
`docs/project/MERIDIAN_SUBSTRATE_INVENTORY.md` | What actually exists in the code: modules, schema, stubs, wiring |
`docs/project/MERIDIAN_OS_TASKS.json` | Task ledger |
`design-qa.md` | Visual acceptance state and known gaps |
`AGENTS.md`, `MERIDIAN_DECISIONS.md`, `MERIDIAN_VISUAL_CAPTURE_SPEC.md` | Binding rules |

## Current state — facts, not narrative

- **Verified tonight:** the owner's iPhone Air viewport (420×912 @ DPR 3) is now a **governed** capture viewport
  (`8193f7f`); the governed harness produces 20 captures with zero overflow and zero errors. The dial/callout
  alignment fix is `0c2097e`, confirmed by Chromium and WebKit geometry assertions.
- **Open and proven:** the dial's own recurrence engine drifts — `Jan 31 → Feb 28 → Mar 28` permanently, and
  "semimonthly" is `+15 days`, walking off the calendar (`meridian/services/dial.py`). The dial is **already on
  live data**, so the defects reach the rendered surface. This is the highest-value correctness item.
- **Open:** the observation store has **no production caller** (`append_snapshot` is never invoked by the app), so
  the "digital twin" is not a maintained twin.
- **Open:** `ruff check .` reports **11 pre-existing errors**; the repo has no clean-lint baseline, so a lint gate
  added today fails immediately.
- **Consolidation facts:** `/Users/stephenwest/Openrouter/` is an **unversioned** project copy with no `.git`
  (frozen Aug 31) that **contains** the canonical repo — so it must never be archived wholesale. It holds an
  unversioned `cookies.txt` (a credential — never open or print it) and `data/savings_data.db`.
  **18 of 23 remote refs** are `test-*`/`scratch-*`/`ref-only-*` relics. Three artifact dirs and two private
  capture harnesses exist because each agent built its own.
- **Environment traps:** playwright and Chromium live in `.venv311` (per `requirements-dev.txt`) and are absent
  from the uv-isolated runner built on `requirements.txt`; interrupted browser runs leave orphan Chromium
  processes that make later runs hang; an edited shipped migration 503s every financial endpoint; committed is
  not served.

## Your assignment

Produce **the total gameplan** for Meridian's forward execution. Not a status update, not a restatement — an
executable plan with owners, order, dependencies, evidence and stop conditions.

## Required deliverables

**D1 — Consolidation, executed or executable.** Ordered steps with rollback. Must include: what duplicate material
to archive (by name — never a parent-directory move), what verified backup precedes each destructive step, how
`cookies.txt` is handled, which remote refs to prune and why each is safe, how the three artifact dirs and two
harnesses collapse to one preview plus one capture harness, and how the doc set stays at one entry point. State
explicitly which steps need owner approval.

**D2 — Work-ahead plan.** Sequence Tracks D (design/layout fidelity to the concept), I (higher intelligence /
agent council) and C (capability spine V1–V8) into bounded slices, each with: one user-visible outcome, its
acceptance evidence, dependencies, files touched, and exit criteria. State what can genuinely run in parallel and
what cannot — remembering that shared contracts mean "different files" is not a safety property. Name the
integrator and the interface owner for each shared contract.

**D3 — Preset adjustment plan.** Your 7 findings, ordered, each with the **test that proves it** (a change without
a test is another prose instruction). Distinguish Harness **code** changes from **configuration** changes. Include
the migration path: how the preset source is versioned in the canonical project, how an install is reviewed as a
diff, how a backup is taken, and how you avoid overwriting a live preset during an active session. Adopt or
challenge the revised ordering in `PRESET_GUARDRAIL_IMPLEMENTATION.md`: `1a+1b+2 together → 4 → 5 → 3 → 6 → 7`.

**D4 — The first prompt for the Harness agent.** Draft it in full, ready to paste: role, lane boundary, which
documents to load by exact path, the claims requirement, the one slice to start on, and the evidence it must
return. It must reference documents by **exact `docs/project/` paths at versions** — the current persona names
bare filenames, which is finding 6.

**D5 — Session architecture.** How many sessions, what each owns, and what crosses between them. Address the
compaction problem directly (finding 2: fresh instruction context is removed after `compaction/end` while write
tools remain). Specify: when to compact, what the re-entry packet contains, what a session must prove before its
first mutation, and how to stop cleanly on quota exhaustion or owner stop. Prefer several short, bounded sessions
with explicit handoffs over one long drifting session — this session is the evidence for why.

**D6 — Harness additions.** Everything you would add so the workflow *happens* rather than being described:
hooks, config, plugins, budget accounting, evidence capture, plan-mode binding, preset-selection binding (Meridian
preset bound to the Meridian workspace — **and not** made the global default for unrelated projects), seed
hygiene, tool-boundary unification, and anything you judge necessary that is not on this list.

**D7 — Blockers and owner decisions.** Everything that needs the owner, with the cost of delay and the safe work
that can proceed meanwhile. Include the deferred decisions carried in the roadmap: dated-event semantics
(reserve carry-forward; semimonthly anchors), daily-driver deployment identity, security calibration
(unversioned `cookies.txt`, plaintext stores, absent CSRF), evidence retention, and agent runtime (single vs
multi-model).

**D8 — Acceptance.** How each part is proven, including your own 7-item validation checklist, one bounded real
task compared against the current preset, and what remains unverifiable.

## Constraints that bind you

- **Evidence over assertion.** Tag claims `[E]` (read/ran it), `[S]` (source-inspected), `[T]` (tested this pass),
  `[D]` (judgment), `[U]` (unknown). A checkpoint must **cite the artifact** — path, exit code, SHA — for each
  claim. "Nonempty evidence" is not enough: tonight's failures happened *with* evidence available and mis-stated.
- **Do not guess.** A viewport, DPR, path or contract you have not verified is `[U]`, not a plan.
- **One bounded slice at a time**, test-first, and no completion claim because a schema, endpoint, button, prompt
  or placeholder exists.
- **Intelligence never mutates financial state.** Only the constrained executor does, via
  proposal → approval → execution → provider verification. No role ever receives a bank write tool.
- **Never auto-retry a financial mutation.** Never present stale as current, forecast as fact, simulation as
  balance, or recommendation as permission. Missing data is never zero.

## What not to do

- Do not move or archive `/Users/stephenwest/Openrouter/` wholesale — the canonical repo lives inside it.
- Do not open, print, copy or commit `cookies.txt` or any credential.
- Do not restate the roadmap as your gameplan, and do not re-derive what is already committed.
- Do not widen the Meridian preset into the global default.
- Do not design an agent council of eight processes; the envelope and permissions come first.
- Do not attempt a release, deployment or live acceptance.

## What makes your gameplan good

It is **executable** (someone could start tomorrow), **ordered by dependency truth** (for each claimed dependency,
say what concretely breaks if it is reversed), **bounded** (every slice has a stop condition), **evidence-bound**
(each stage says what proves it), **safe** (no authority expansion, owner gates respected), **honest about
unknowns**, and **consolidating** (it reduces the number of trees, branches, harnesses and entry points rather
than adding to them).

## Report format

Return the gameplan as one document, sections D1–D8, followed by:
1. **Disagreements** with the committed roadmap or with `PRESET_GUARDRAIL_IMPLEMENTATION.md`, classified as
   *factual* (evidence settles it), *sequencing* (a dependency test settles it) or *value* (owner decides), each
   with its evidence.
2. **Exactly one first move**, and why it is first.
3. **What you could not determine**, and how it would be determined.

Do not change the installed preset or restart the Harness until the owner approves D3 and D4.
