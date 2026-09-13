# Meridian forward execution gameplan

**Status:** proposed execution plan, not approval to install a preset, restart Harness, deploy, conduct live acceptance, change credentials or activate authority. Prepared September 13, 2026. This is the execution companion to `docs/project/MERIDIAN_ROADMAP.md`, not a replacement trajectory or entry point.

**Readiness supplement (September 13):** [MERIDIAN_READINESS_AUDIT.md](MERIDIAN_READINESS_AUDIT.md) now records the wiring audit, tested prerequisite order, 953 passing isolated application tests (one CLI-dependent failure, seven skips), 236 passing Harness tests and successful synthetic restore rehearsal. Read it before executing this plan. R0 has since been implemented in the repository; E4/E5 below retain historical baseline meaning, not current defect status. Use the new concept coverage and implementation plan for depth instead of creating a competing roadmap. No preset activation or production release is implied.

**Goal:** make the build process preserve authority and verified context, then deliver the existing Meridian vision through bounded, useful capabilities.

**Baselines:** application `9d8107ff50e61c3edd9340edb4acb9aedcecd64b` (the assignment's `713d7b2` design plus its assignment commit); Harness `a834868c143f4a896840b8d08a7777df1b899f13`. The installed preset is external to both Git histories and must be inventoried separately before implementation.

**Evidence notation:** `[E]` directly read/observed; `[S]` source-inspected; `[T]` tested this pass; `[D]` proposed design or sequencing judgment; `[U]` unresolved. A tagged paragraph/table introduction applies to its entries. Historical test claims remain historical; they are not re-certified here.

**Owners:** **H — Astra, Harness-side lead/integrator**, the role assigned by the owner, independent of which model occupies it; **R — existing repo-maintainer agent, application integrator**; **O — Stephen, owner**; **Q — separate reviewer designated by O**, currently unassigned. No delegation or additional sessions were launched for this assignment. H owns Harness code and preset design; R owns application integration. H claims exact application-repo paths before writing there. Q cannot be relabeled independent when the implementer performs self-review.

**Evidence register:** paths below are relative to the canonical application repository.

| Evidence | Artifact and command outcome | Source identity / meaning |
|---|---|---|
| E1 | `artifacts/gameplan-2026-09-13/inventory.json`; inventory command exit 0 | Records both baseline SHAs, document blob IDs, exact local/remote refs, named parent items and lint findings |
| E2 | `git ls-remote --heads origin`, exit 0, recorded in E1 | Two actual server branches; no server `test-*`/`scratch-*` branches at inspection |
| E3 | `git for-each-ref refs/remotes` and individual ancestry checks, recorded in E1 | 23 local tracking entries including symbolic `origin/HEAD`; 17 absent-server tips are not ancestors of application baseline |
| E4 | `.venv311/bin/python -m ruff check . --output-format=json`, exit 1, recorded in E1 | Eleven current findings, including untracked artifact scripts; this is not a clean lint baseline |
| E5 | `artifacts/gameplan-2026-09-13/guardrail-probes.json`; disposable-fixture driver exit 0 | Executed the Python example from design blob `bf82f26984cc72142c13d7a0606494b79433a635`; bad old-migration edit returns 0, legitimate new migration returns 1 |
| E6 | `docs/project/CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md`, blob `37622d532b16eb607ced74e6af33d082debb84d4` | Existing installed-preset review and six historical keyless probes; consult rather than re-derive |
| E7 | `docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md` and `tests/browser/capture_contract.py` at application baseline | Five governed viewports, ten viewport/theme combinations; prior twenty-image claims require checking their linked manifests, not recounting them as this pass's tests |

No credential content, live database content, installed-preset change, deployment or live acceptance was involved in E1–E5. Parent candidates were inspected by name/type/size only. Evidence artifacts contain metadata and synthetic results.

## D1 — Consolidation, executable with rollback

### D1.1 Preserve first; do not mistake old for redundant

[D] Execute the following order. R integrates repository changes; H supplies Harness/preset information; O authorizes every destructive/relocation step. Discovery and proposed manifests can proceed now. No consolidation deletion or move is authorized by this plan.

1. Recheck both HEADs, dirty paths, current claims and active process working directories. Refuse a move that intersects `simplecrew-latest`, a separate Chime project, an active runtime, or another writer's claim. Claim only the exact paths in the selected consolidation slice.
2. Produce a reviewed item manifest containing source path, classification, owner, destination, dependency checks, backup receipt and rollback action. Missing classification means **retain**, not “probably duplicate.”
3. For source-only material approved as non-sensitive, make an item-specific backup, hash the included files, list the archive, restore into an isolated directory, and compare hashes. The backup receipt records the exact manifest and restore-test exit code. No recursive parent-directory archive.
4. For `data/`, `backups/` and potentially credential-bearing history, O or an explicitly designated backup operator performs the protected backup and verification. This agent must not copy credentials. Require a non-secret receipt identifying the snapshot, integrity result and restored-copy verification before any retirement. A file existing or a successful `cp` is not proof.
5. Only after the exact manifest and backup are approved, retire one named item. Verify remaining launchers/tests no longer depend on it. Roll back that item from its verified backup on any failure. Never overwrite a destination that already exists.
6. End the slice with an inventory delta, restored-path instructions, exact SHA and remaining retained items. Do not combine source archival, database relocation and ref cleanup into one transaction.

[E/D] The following named parent items exist (E1). These are **candidates**, not proven dispensable duplicates:

| Exact item under `/Users/stephenwest/Openrouter/` | Retirement decision and prerequisite | Backup / rollback |
|---|---|---|
| `app.py` | Compare against canonical app source and runtime references; archive only after unique behavior is reconciled | Approved source-only item backup; restore this file to its original path |
| `assistant.py` | Compare advisor/bootstrap imports; preserve unique behavior | Same item-specific backup/restore |
| `crew/` | Compare module inventory and connector imports; no wholesale transplantation | Reviewed non-sensitive member allowlist; owner handles any sensitive members; restore exact members |
| `crew_broker.py` | Confirm no launcher/client imports this copy | Item backup plus launcher-reference report; restore original path |
| `run_preview.py` | Check launchd/shell/process references before retirement | Item backup and previous launch command receipt; restore file/reference pair |
| `data/` | Hold: uniqueness, credential-bearing contents and runtime use unresolved | Owner-operated protected database backup; integrity and restored-state proof; matched runtime/data rollback |
| `backups/` | Hold until every backup is identified and at least one usable restore path remains | Owner-operated protected inventory/restore proof; preserve all unknown generations |
| `cookies.txt` | Credential quarantine decision only; **do not open, print, copy, commit or automatically move it** | O selects secure handling or revocation/destruction after dependency review; absent that decision leave untouched |
| `simplecrew-latest/` | Canonical working tree: **never archive as part of parent cleanup** | Existing project recovery policy; no move planned |

[D] These source candidates may go into a reviewed archive beneath the canonical project's designated private artifact storage, or another O-approved destination. Do not invent a new unversioned working copy. The destination must be chosen and checked before running the item-specific backup; lack of a destination does not block code or guardrail planning.

### D1.2 Branches: correct the actual target of cleanup

[T] E2 shows only these server branches. **Retain both; no remote branch deletion is proposed:**

| Server branch | Observed tip |
|---|---|
| `feat/meridian-implementation` | `448ceed94b0c6c437390c1f4f7769dfd4afbf984` |
| `main` | `41102887a3245c137745ae21c3793bf8b5d903d3` |

[E/D] The clutter is local remote-tracking refs. The complete exact-name/OID/ancestry list is E1. Preserve `origin/HEAD`, `origin/main` and `origin/feat/meridian-implementation`. Do not run a blanket `fetch --prune` or `remote prune` before preserving the unique tips.

| Local tracking ref (server absent) | Recorded tip | Decision / why |
|---|---|---|
| `origin/docs/enhanced-simplecrew-project-control` | `2ecf80480ce02a06382860d4c24af3bcb675a7b4` | Prune candidate after O-approved backup: tip is retained in canonical HEAD history. |
| `origin/fix/review-blockers` | `1db3e031b81c080a317e58e758502d40e8a9da7e` | Prune candidate after O-approved backup: tip is retained in canonical HEAD history. |
| `origin/ref-only-test` | `41102887a3245c137745ae21c3793bf8b5d903d3` | Prune candidate after O-approved backup: tip is retained in canonical HEAD history. |
| `origin/scratch-a` | `41888c1f6d2d658cec62dc3a2ff6ccf2aea954aa` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/scratch-b` | `86c29e1b70b85b2a4b8d6c8870f3415198990e7a` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-a30-atlas` | `b82ce033245d584f0707ba70f435b152f7825531` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-a30-current` | `852daabf435be6c2930373a6e704a59895b620c6` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-a30-iterations` | `24caf3619ec4c84e013a1a64eb38bb4b0192dc51` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-app` | `0a08cd81da9a695f9b38b85ae3130609bbdbd57a` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-audit-0831` | `57ee4448d39944d40b8b8d5523eec2e4893c4de4` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-chunk-folder` | `01fafccf8f0bcfd6b4b8f428b31c6d009a75ba46` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-chunk-output` | `34f1abf95411f9474d86fc086333ca4687aa6014` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-chunk-zip` | `cbc686be34f31cd2f5a003dd0fe0021139107af1` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-control-meridian` | `7b525f7dd7084e6faf94ac2431be45d800e9d930` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-crew` | `449aaa769222b30ab3bc732448c65123a272af97` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-docs` | `df8a6a64f8ec0733c0d72e946d467ee98914f74d` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-dummy30` | `475625e8ee388a37e4bfa6e1185d68cf1175e74a` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-meridian` | `0b2d10680faf7bedb18232fcb916890136179202` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-misc` | `eb762809b1fd4b89819f3503b56475fb7bb67546` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |
| `origin/test-retest-atlas` | `bd9d7afa99dc58f04cbe8219cdc460403712c9e3` | Retain now: not an ancestor of canonical HEAD; review unique work and verify approved history backup before any prune. |

[D] For each absent-server ref approved for pruning:

- Refresh the server listing and compare its exact OID with E1. Any server reappearance or local OID change stops that ref's cleanup.
- Preserve a ref-name/OID manifest and an O-approved, verified Git-history backup. If the history may contain credentials, O handles the protected backup; this agent does not copy it. Verify the archive can resolve the recorded commit in an isolated repository. Unknown backup/exposure status means keep the ref.
- For non-ancestor tips, inspect the unique history/diff before deciding discard versus selective integration. An archived bundle alone does not prove the work is unwanted.
- Remove **only the approved local tracking ref**, with compare-and-swap semantics: `git update-ref -d refs/remotes/origin/NAME EXPECTED_OID`, substituting the exact reviewed row. Never execute this as a prefix loop or delete server branches based on these stale names.
- Rollback: restore the recorded ref to its OID after verifying the object exists; otherwise restore objects from the verified approved backup first. No working-tree reset is involved.

### D1.3 One preview and one capture entry point

[S] Keep `scripts/preview_observatory_dial.py` as the **isolated synthetic preview** and `scripts/capture_meridian_matrix.py` as the **canonical capture command**. `run_preview.py` is the daily runtime launcher, not a duplicate fixture harness. `scripts/crew_mitm_capture.py` captures provider contracts, not UI screenshots; it is outside this retirement.

[S] The two UI capture approaches cannot simply be renamed into one: the canonical capture command currently assumes login and multiple workspaces; the isolated preview deliberately has no login/bank connection and runs a narrow controller set. R must merge the missing fixture/no-auth, density, engine and workspace-selection support before retiring the local capture script.

[D] Consolidation slice C0:

1. Extend the canonical command with explicit `--workspace`, `--fixture`, `--engine`, and isolated-preview handshake support; keep the existing authenticated capture mode for later separately authorized acceptance. A loopback URL alone is **not** proof of synthetic data.
2. Require a preview identity response declaring synthetic mode, fixture hash and source identity. Captures must refuse the daily preview's missing/incorrect identity, without reading bank data.
3. Import the useful behavior from `artifacts/dial-refinement-2026-09-12/capture.py`: density fixtures, current template/style rendering, errors/overflow checks, fixed clock and explicit theme. Retain full metadata and inspected comparisons.
4. Demonstrate ten viewport/theme combinations × viewport/full-page = **20 files per selected workspace/engine/fixture**. More workspaces or engines multiply this count; twenty is not whole-product acceptance.
5. Once parity passes, retire `artifacts/dial-refinement-2026-09-12/serve.py` and `capture.py` only after O approval and their verified source backup. Keep their historical captures with a manifest; do not delete evidence to make the directory look clean.

[E/D] Existing artifact directories are `artifacts/design-audit/`, `artifacts/observatory-preview/`, `artifacts/dial-refinement-2026-09-12/`, `artifacts/product-audit-2026-09-08/`, `artifacts/design-audit-2026-08-30/`, and `artifacts/design-audit-2026-08-31/`. Index them first. New canonical UI runs use `artifacts/visual/<run-id>/`; old runs stay at their cited paths until approved archival with a link/manifest migration. `artifacts/gameplan-2026-09-13/` is this planning evidence, not another harness. Quarantine historical/unclassified captures from new tests; do not bulk inspect or publish potentially live captures.

### D1.4 One document entry point

[D] `docs/project/README.md` remains the sole start-here index. Add this plan as an execution reference; retain the roadmap as trajectory and owner decisions as authority. R cleans duplicated roadmap paragraphs and the malformed viewport prose without changing requirements. Reconcile the five-viewport table with the root AGENTS four-viewport wording. Superseded narratives can remain in place; moving them is optional and requires link repair and O approval. Track every original concept/finding as delivered, planned, gated or deferred in the existing task ledger rather than creating another ledger.

## D2 — Work ahead: owners, contracts, dependencies and exits

[D] Every slice follows: claim → acceptance case → red test where behavior changes → bounded implementation → focused checks → review → owned-path commit → evidence/handoff. A timebox is a checkpoint limit, not a completion estimate. After two failed evidence-based fixes, stop and re-plan; on owner stop/quota exhaustion checkpoint immediately. Never advance a slice with failed required checks or unsupported verification claims.

### Ownership of shared interfaces

| Contract | Sole interface owner | Integrator | Consumers / controlled change rule |
|---|---|---|---|
| Harness admission, mode and authority capsule | H | H | Preset, file/shell tools, subagents; version before consumers change |
| Claims, re-entry and evidence receipt schema | R, with H as required reviewer | R | Harness admission, Git checker, task ledger; H implements against an agreed schema fixture |
| Dated occurrence and cash allocation contract | R | R | Today, dial, Plan, Beacon, Forecaster; one golden fixture set owns semantics |
| Observation/evidence identity and publication | R | R | Read models, simulations, Investigator; commits publish one coherent revision |
| Advisory task/result envelope | R | R | Runtime roles; H reviews tool/budget isolation; no model supplies authorization |
| Command approval/claim/readback lifecycle | R | R | UI and deterministic executor; Q review required before live integration |
| Visual fixture/capture manifest | R | R | All design sessions; H consumes receipts rather than maintaining another harness |
| Installed preset manifest and activation | H | H; O activates | Versioned source in application repo; no live overwrite |

### Application work packages

[D] Existing module paths below are grounded in the substrate inventory/source; paths explicitly marked **new** are proposed files, not claims they already exist. R assigns sequential short sessions to these packages. “Stop” includes the global rule above.

| ID / owner | One user-visible outcome | Dependencies and reversal failure | Files touched | Acceptance evidence / exit / stop |
|---|---|---|---|---|
| R0 / R | Builds start from a trustworthy declared scope and usable verifier | None; feeds safe shared execution | **new** `scripts/check_guardrails.py`, `tests/test_check_guardrails.py`, `docs/project/agent-claims.json`, generated re-entry receipt; existing coordination/ledger | Corrected D6 checks pass positive/negative fixtures; targeted lint clean. Stop if another claim overlaps or schema not agreed with H |
| C0 / R | One reproducible command shows the actual fixture-backed interface | R0; retiring old captures first would lose coverage | Preview/capture scripts, `tests/browser/capture_contract.py`, `tests/test_capture_contract.py`, dev requirements, visual spec/index | Synthetic handshake, five-view matrix, error/overflow and WebKit Air cases; same fixture can be replayed by H. Stop on missing identity or browser failures |
| D1 / R | Today layout matches the endorsed composition on the owner's device | C0; without it visual acceptance is not reproducible | Today/dial CSS/JS/partial, `tests/browser/test_dial_fidelity.py`, `design-qa.md` | Fresh sparse/dense/long-title/unknown-value states in both themes; no overlap, keyboard parity, concept comparison. O's later visual acceptance separate; stop at any unresolved material gap |
| C1 / R | Upcoming bill dates stop drifting | Acceptance semantics agreed; pure tests need not wait for C0/Harness installation | **new** `meridian/occurrences.py`, `tests/meridian/test_occurrences.py`; `services/dial.py`, `funding.py`, `paycheck.py`, `beacon.py`, `services/plan.py` | Fixed-anchor Jan31→Feb28→Mar31; leap year; explicit two monthly anchors versus every15days; DST civil dates; same occurrence IDs/dates across consumers. Stop on ambiguous provider cadence; preserve unknown instead of inventing anchors |
| C2 / R | Selecting a current amount opens reproducible source evidence | R0; input/identity contract before I2 or simulations prevents stale/unreplayable claims | `observations.py`, `live.py`, `sync.py`, `repository.py`, `api.py`; **new additive migration only if required**, observation integration tests | Ordinary synthetic sync publishes immutable history plus coherent current revision; empty/partial/out-of-order cases, failure rollback and restart replay. Stop on partial publication or missing scope/completeness proof |
| I1 / R, H reviews | Virgil can return one structured, cited answer within a hard read-only boundary | Agreed evidence schema; synthetic work can run alongside C1/C2 | **new** `meridian/ai/contracts.py`, `meridian/ai/role_runner.py`, `tests/meridian/ai/test_role_runner.py`; advisor integration | Typed envelope, scope/budget, unknown evidence, malformed output and forbidden write-tool rejection tests. Exit is one synthetic answer rendered with citations; not live intelligence acceptance |
| C3 / R | A saved paycheck plan allocates one cash pool correctly | C1; before calendar correctness contributions/due windows are wrong | `funding.py`, `funding_repo.py`, `paycheck.py`, `commitments.py`, `services/plan.py`, Plan/payday UI/tests | Field-complete save/read/restart; caps, zero/null, distributed strategy, exact shortfalls, reserve applied once per occurrence. Stop until carry-forward policy is explicit where needed |
| I2 / R | One Forecaster explains a trustworthy projection and its assumptions | I1+C1+C2+C3; before these it can narrate inconsistent facts | Advisor/role runner, forecast/scenario adapter, **new** `tests/meridian/ai/test_forecaster_acceptance.py` | Hand-calculated fixtures, valid evidence IDs, stale/contradictory inputs, unavailable model; display disagreement/uncertainty. Approved real-model pilot only after keyless gates |
| D2 / R | Plan is both editable and visually faithful | C0+C3 interface stable; skinning before save contract stabilizes duplicates work | Plan/payday controllers/partials/CSS, Plan browser tests | Named schedule/bill edit→reread→restart plus governed captures; stop on dropped fields or outcome ambiguity |
| C4 / R + Q | Each supported intervention has an honest durable receipt | C2 and typed command contract; no dependency on full council | `app.py` action routes, `write_routing.py`, `crew_commands.py`, `crew_write_actions.py`, `crew/actions.py`, `crew/executors.py`, mutation/history UI/tests | One operation at a time: tampered authority, stale base, double claim, timeout, empty result, uncertain readback and restart. Stop unresolved writes; never resend. Live acceptance requires O |
| D3 / R | Activity supports clear review, correction and evidence | C0; classification/evidence interface locked | Activity/review/inspector controllers/partials/CSS and browser tests | Correct→refresh→same correction; filter/navigation and dense/empty/error captures; stop on lost correction or inaccessible inspector |
| D4 / R | Accounts explains source, freshness and missing records | C0+C2 read contract | Accounts/connections service/UI/tests | Current/absent/partial/stale cases match data; captures and account→Activity navigation; stop on false-current claims |
| C5 / R | What-if scenarios show changed outcomes without touching actual state | C1+C2+C3; write-path completeness not a prerequisite | `scenarios.py`, `beacon.py`, `services/plan.py`, scenario UI/tests | 7/30 then 90/365-day event replay with explicit horizon assumptions; denied access to actual-state writers; actual state unchanged. Stop on copied stale aggregate fields or unbounded assumptions |
| C6 / R | One useful change alert can be resolved or dismissed without repeats | C1/C2; notification delivery independent of bank execution | `proactive.py`, deposit/biller helpers, durable event state via additive migration if needed, Today/advisor/tests | One late-deposit or bill-change lifecycle, duplicate/restart/reconnect/snooze tests. Stop before external delivery without required channel approval |
| C7 / R | One document/refund/subscription issue can be traced to closure | C2 plus only the selected connector | Evidence/storage/intake/documents/context/contracts/cancellation modules and chosen UI/tests | Intake→reviewed match→explanation→correction/closure; ambiguous match, prompt injection, revocation and retention cases. Stop at new credentials/scopes/retention or external cancellation gates |
| I3 / R, H reviews | Forecaster, Skeptic and Guardian expose useful disagreement on one question | I2 evaluation passes and policy evidence contract exists | Role runner, **new** `meridian/ai/council.py`, `tests/meridian/ai/test_council.py`, advisor presentation | One bounded sequential deliberation; no majority vote; citations checked; final typed proposal never authorizes execution. Stop if extra roles add cost without accepted value |
| D5 / R | Settings, login and inline Virgil match the design while preserving connections | C0 and stable auth/connection contracts | Settings/connections/login/advisor templates/CSS/controllers/tests | Five-view/theme captures, keyboard/reduced-motion, configuration/revocation states; O handles real auth acceptance. Stop on scope/credential change |
| C8 / R + O | Constitution choices are inspectable, versioned and revocable | C4+I1; evaluator tests can precede activation | `policy.py`, policy repository/UI and additive policy version migration/tests | Overrides/expiry/missing evidence fail closed; every applicable command links evaluation. Activation, limits and grants require O |
| C9 / R + O | One optional economic-OS experiment addresses a demonstrated unmet job | Only its real prerequisites: crisis rehearsal C5; household C2+C5+consent; Builder H-boundary+reviewed permissions | Crisis: **new** `meridian/crisis.py`; household or temporary-tool modules only after selected experiment's small spec | One keep/change/drop trial with explicit data/authority boundary. Stop without separate approval for household data, installation or authority; eight-process council remains excluded |
| V8 / R, H for Harness releases, O authorizes | A released capability is the one tested and can be restored | Runs for every candidate release; never waits for C9 | CI/release launcher, migration/backup runbook, dev requirements and acceptance records | Exact source/dependency/preset identity, executed gates, matched image/DB restore and runtime checks; stop before production/live acceptance until O approves |

[D] Overall order: R0 → C0 → D1, while C1 and I1's synthetic contract work progress in separately claimed scopes after interfaces are agreed. C2 can follow the evidence contract; C3 follows C1; I2 consumes C1–C3 and I1. D2–D5 proceed in their stated workspace order, interleaved with capabilities. C4 is an early independent correctness lane, not postponed behind I3. H's safety work below can run concurrently with R's pure domain tests because they share no writer, but shared schemas are frozen before consumer changes. Serialize migrations, `app.py` integration, preset activation and commits in each shared checkout. A claims table alone does not provide exclusion.

### Vision coverage and specification boundary

[D] This gameplan routes all 22 concepts, but routing is not a finished product specification. C7/C9 deliberately require a bounded use-case specification before implementation; role usefulness, long-horizon accuracy and causal explanations need evaluation, not just interfaces. Proper execution can deliver the first daily-driver and intelligence milestones; it does not guarantee that every optional economic-OS idea is useful or authorized.

| Vision concept | Work package | Additional product definition / acceptance needed |
|---|---|---|
| Financial digital twin | C2 | Replay scope across accounts, commitments, schedules and observations |
| 7/30/90/365 projections | C1/C3/C5 | Horizon assumptions and independently checked forecast examples |
| Confidence/uncertainty/provenance | C2/I1, all UI | Distinguish measured confidence from model self-confidence |
| Living constitution | C8 | Owner-selected policies, overrides, expiry and review interval |
| Policy evaluator | C8/C4 | Fail-closed evaluation and command linkage, separate from authority |
| Specialized agents | I1/I2/I3 | Per-role usefulness cases; not all named roles required on day one |
| Single constrained executor | C4 | Per-operation typed contract and owner-observed provider acceptance |
| Proactive weather/alerts | C6 | Relevance, suppression, resolution and notification channel boundaries |
| Balance forensics/anomaly investigation | C7 | Reconciled deltas, alternatives and explicit unexplained remainder |
| Continuously repaired budgets | C3/C6/C4 | Explainable proposed repair, owner acceptance and undo semantics |
| Paycheck landing | C3/C6/C4 | Expected/observed matching, partial/late deposit and reviewed funding |
| Scenario/counterfactual learning | C5/C7 | Compare past prediction with actual evidence without claiming causality |
| Refund/subscription lifecycle | C7 | Capture through verified charge/refund/closure; external acts gated |
| Bureaucracy/negotiation preparation | C7 | Sourced draft brief, missing evidence, no implied sending or agreement |
| Household planning | C9 | Participants, consent, privacy/isolation and ownership rules |
| Crisis-command mode | C9 after C5 | Essentials-first rehearsal and reviewed options under reduced income |
| Causal financial memory | C2/C7 | Versioned explanations; observations versus causal hypotheses |
| Temporary personalized tools | C9/H2 | Concrete unmet job, sandbox, lifetime and permission diff |
| Connector self-diagnosis | C2/V8 | Stage-level failures and safe recovery guidance, no autonomous repair |
| Sandboxed skill generation | C9/H6 | Artifact evaluation, permission diff and explicit installation approval |
| Proposed UI evolution | D1–D5 | Concept/layout fidelity plus usable real journeys and adverse data states |
| Bounded autonomous CFO behavior | C8/C9 | Separate authority design; standing prohibitions still bind |

[D] Before calling the whole vision fulfilled, O must accept a product-level outcome set and the selected concept contracts must pass their real journeys. Future discovery may add, split or reject concepts. The plan should be strengthened by a targeted vision/specification pass and per-slice implementation plans, not continually replaced by another high-level roadmap.

## D3 — Preset adjustments: code, configuration, tests and installation

[D] Adopt **1a+1b+2 together → 4 → 5 → 3 → 6** as implementation increments, with two corrections: **7a source/version/backup design is the prelude**, and **7b installation is the final owner gate**. Do not install any intermediate increment. Boundary 4 is part of the acceptance of the combined safety bundle: hiding tool names is not enforcement while shell or another mutation path remains usable. Seed contamination must be fixed before live adoption; it is not inherently harmless merely because it is “context.”

| Increment / owner | Configuration versus code | Exact source locations / proposed files | Proof before exit |
|---|---|---|---|
| H0 — 7a + red safety specification / H | No installed changes. Establish source inventory and failure tests | Installed preset read-only; **new canonical source directory** `tools/agent-presets/meridian-constitutional-builder/` after exact claim; Harness **new** `packages/guard/agent-admission/tests/reentry.spec.ts` and package scaffold under Harness conventions | Hash manifest excludes credentials; keyless pre-/post-compaction, active-plan and denied mutation cases reproduce missing protection. Exit at reproducible failures plus interface contract; do not “fix” by weakening tests |
| H1 — 1a+1b+2 / H | Config: preserve required sections/context. Code: epoch/version-aware capsule and admission state | Versioned preset `agent.cordis.yml`, `context-gate.mjs`, `instruction-hint.mjs`, `tool-bootstrap.mjs`; **new** Harness `packages/guard/agent-admission/src/index.ts`; consume existing system-prompt and agent hooks | Required persona/active `plan:policy`/runtime policy/capsule remain in assembled text. First mutation after startup/resume/compaction/model/preset/HEAD change is rejected until fresh machine-validated admission. Injected notice cannot be stripped after validation |
| H2 — 4 / H | Config: remove private raw-filesystem bypass. Code: common mutation authority at execution boundary | Versioned preset bootstrap-filesystem rows; Harness `packages/core/tools/src/index.ts` extension seam, `packages/interaction/permission-presets/src/index.ts`, existing file/shell provider seams; prefer plugin hooks to loop rewrites | Deny wrong cwd/branch, `../`, symlink escape, absolute out-of-lane path, stale HEAD/lease, shell-mediated file write and conflicting claim. Read-only inspection still works. Test actual effects in synthetic sandbox, not just missing tool schemas |
| H3 — 5 / H with R schema review | Code: receipts, budgets, completion admission. Config: per-slice limits | Admission plugin; Harness `packages/workflow/tool-ralph/src/index.ts`, goal/runtime seams where necessary; proposed typed receipt schema shared with R0 | Fake evidence path, wrong SHA/hash, nonzero exit, skipped required tests and confident prose all fail completion. Owner stop/quota/timeout produces durable checkpoint, no new child/model call; unresolved financial outcomes cannot schedule retries |
| H4 — 3 / H | Code: filter/rebuild seed context. Data: reviewed seed manifest | Versioned `prefab-session-seed.mjs`, `template.jsonl`, metadata and tests | No foreign instruction reminders/catalog; current instruction hashes and current skill registry only. Examples labeled and cannot create a false verification receipt; duplicate message IDs and seed failures handled explicitly |
| H5 — 6 / H | Config/docs: exact versioned operating packet and role entry points | Versioned persona/README; consume repo README, decisions, task packet, claims and visual manifest | Every mandatory path resolves at declared revision; conflicting/newer version invalidates admission; sparse/dense/unknown/large-number/Air/WebKit cases resolve from current capture contract |
| H6 — 7b / H, O activates | Packaging code/config, then separately approved installation | **new** `tools/agent-presets/install-reviewed.mjs`, reviewed manifest/diff/rollback receipt; existing Harness preset selection in `packages/preset/agent-presets/src/session.ts`/discovery as required | Dry-run reports exact changes and installed/source fingerprints. Refuse active sessions, source drift, missing backup or failed restore rehearsal. After approval, version marker matches loaded composition; rollback restores previous full preset/version and session readability |

[D] H0's first keyless acceptance sketch, to translate against the actual Harness test utilities before implementation:

```text
Given: synthetic Meridian workspace, exact base HEAD and constraints digest,
       active plan mode, and a compaction boundary.
When: assemble the next request and attempt a file mutation through each real tool path.
Then: required policy/capsule are present; every attempted effect is denied;
      merely calling a read tool or emitting assistant text does not admit writes.
When: the trusted gate validates the packet and the owner-authorized scope permits writing.
Then: an in-scope synthetic write succeeds; a wrong path/HEAD/claim still fails.
```

[D] Version/installation procedure:

1. Inventory only the named preset's source files and hashes; do not copy `.credentials.yaml`, `.env`, session histories or unrelated settings. Review the seed for embedded sensitive material before adding it to source control. If uncertain, record only its hash and retain the live copy untouched.
2. H claims the canonical preset-source directory; R accepts the location/interface, H commits source with its tests. Harness-generic plugin implementation stays in Harness, on a verified approved Harness development branch; no new Meridian branch/worktree is created.
3. Produce a complete source→installed diff with file hashes and minimum Harness/package compatibility, excluding secrets. Run all negative tests against a disposable preset copy and stub host.
4. O reviews D3/D4 and the concrete install diff. Confirm all affected live sessions are idle using Harness's active-session API, not journal silence. Owner decides whether to defer running sessions; never interrupt them to make installation convenient.
5. Before activation, an approved backup of the exact installed preset is restored into a disposable directory and hash-compared. Preserve installed profile/model/credential configuration; credential changes are outside this install.
6. Install atomically or fail back to the old version; record loaded version/capsule hash and session compatibility. No restart until separately approved. On failure, restore the exact prior preset and verify discovery plus session read/re-entry; do not rewrite session history.

## D4 — First prompt for the Harness agent

[D] Ready to paste **after O approves D3/D4 for source development**. This prompt does not authorize live installation, restart or deployment.

```text
You are Astra, the Harness-side implementer for Meridian. Complete only H0:
establish versioned preset provenance and keyless failing tests for the combined
authority-capsule/re-entry gate. Do not implement the entire gameplan in this session.

Harness root: /Users/stephenwest/deepseek-harness
Reviewed Harness baseline: a834868c143f4a896840b8d08a7777df1b899f13
Application root: /Users/stephenwest/Openrouter/simplecrew-latest
Application branch: feat/meridian-implementation
Reviewed application baseline: 9d8107ff50e61c3edd9340edb4acb9aedcecd64b
Installed preset (READ ONLY):
/Users/stephenwest/.dsh/.agent-presets/meridian-constitutional-builder/

Load the current Harness AGENTS.md and docs/architecture.md before package work.
In the application repo, load the following exact documents as reviewed at
9d8107ff50e61c3edd9340edb4acb9aedcecd64b, then compare their current versions:
AGENTS.md
docs/project/README.md
docs/project/MERIDIAN_ROADMAP.md
docs/project/MERIDIAN_DECISIONS.md
docs/project/CONSTITUTIONAL_BUILDER_REVIEW_2026-09-12.md
docs/project/PRESET_GUARDRAIL_IMPLEMENTATION.md
docs/project/AGENT_COORDINATION.md
docs/project/MERIDIAN_OS_TASKS.json
docs/project/CURRENT_STATUS.md
docs/project/MERIDIAN_VISUAL_CAPTURE_SPEC.md
design-qa.md

Use git show BASE:path to retrieve reviewed versions, not a guessed bare filename.
Read current claims/status as current state, not as frozen permission. If HEAD,
instructions or claims changed, reconcile before editing; never revert to the baseline.

Before any application-repo write, claim exact paths in
docs/project/AGENT_COORDINATION.md. Proposed application write scope for H0 is
tools/agent-presets/meridian-constitutional-builder/ source/manifest only, plus
your explicit coordination/ledger evidence entries. Do not take docs/project/*.
The repo maintainer owns application source. Stage only your named files.

Inspect the real preset assembly and mutation execution seams. Start by writing
keyless tests for: required instruction/plan-policy text survives startup and
compaction; a stale or absent re-entry admission cannot mutate through file,
editor or shell paths; a tool call alone does not grant admission; newer
constraints invalidate the old admission. Use a synthetic workspace and stub
providers, with no model calls, credentials or live financial data.

Create only the minimal versioned-source inventory and test scaffolding needed
to reproduce those failures. New Harness test location:
packages/guard/agent-admission/tests/reentry.spec.ts, following Harness package
and fixture conventions. Verify the supported test command from that checkout;
record its exact invocation, exit and failure assertions. Do not claim the
proposed plugin already exists.

STOP when those failures are reproducible and the admission interface is
specified, or after two failed attempts to establish a trustworthy reproducer.
This is a red-test/specification slice: an expected red result is not a verified
implementation and must not enter a release gate as green.

Return: current branch/HEADs; changed paths and hashes; preset inventory hash;
test artifact paths, exact commands and exit codes; the failing contracts;
proposed admission schema; unresolved questions; and exactly one next action.
Save red results as reproduction evidence, not as passing implementation. Do not
merge known-failing registered tests into the active suite: keep their specification
and reproducible failure artifact in the H0 checkpoint, then register the regression
with H1 when its implementation passes. Commit only owned checkpoint/scaffold
changes, release your claim and leave a bounded handoff.

Never open/print/copy cookies.txt or credentials. Never mutate bank state,
auto-retry a financial mutation, change a shipped migration, prune refs, archive
the parent directory, install a preset, restart Harness, activate policy, deploy
or perform live acceptance. Source development is authorized; those actions are not.
Do not spawn subagents or additional sessions without a separate owner instruction.
```

## D5 — Session architecture, compaction and stopping

[D] Use **four reusable session roles**, not four perpetual processes: H development, R implementation, Q review, and O-controlled activation/acceptance. At most H and R implement concurrently, only under disjoint mutually exclusive claims and frozen shared interfaces. Q receives an immutable artifact/diff after its relevant writer stops; O's activation session runs with both writers idle. If Q is unavailable, mark review pending and continue only work that does not require its approval.

[D] Make each session one slice (H0, H1, C1, D1, etc.). A new short session receives a small handoff, not the previous conversation. Cross-session payload: task ID/outcome, role/claim, repo+branch+base/current SHA, constraints/preset version, interface versions, exact files/hashes, acceptance receipts, unresolved results, stop reason, remaining authorized budget and exactly one next action. Never send secrets, cookies, raw bank payloads or unrelated source trees.

[D] **Compaction trigger:** retain the existing ratio setting as a starting configuration, then enforce a per-task absolute context allowance in addition. The effective trigger is the earlier supported bound, with enough measured headroom for checkpoint and summary. Select/record the allowance before the first paid task using its route's real context limit and packet size; no universal token threshold is asserted. Compact at a slice boundary where possible; force re-entry after compaction, resume, preset/model change, instruction version change or HEAD movement. A hard context-overflow/quota event stops new work and uses the last durable checkpoint; it must not recursively launch agents to rescue memory.

[D] Required re-entry packet fields: `task_id`, `session_id`, `repo_root`, `branch`, `base_head`, `current_head`, `constraints_digest`, `preset_digest`, `mode`, `authorized_scope`, `claim_id`, `claim_generation`, `lease_expires_at`, `interface_versions`, `last_verified_source`, `evidence_receipts`, `unresolved_outcomes`, `budget_remaining_or_unknown`, `next_action`, `stop_reason`. Store state per task/session in the claims/evidence store; `docs/project/REENTRY.md` is a generated human view, not one shared mutable authority file that sessions overwrite.

[D] Before its first mutation, the session must prove through the trusted gate: correct repo/branch; current constraints/preset versions; authorized non-plan mode; exclusive unexpired claim; unchanged baseline relevant files; allowed operation/target; and remaining budget. A model-authored JSON packet or assertion “I read it” is not proof. The gate computes/verifies digests and issues an admission generation, and checks it again at the effect boundary to close the check/use race. Reads stay available for repair.

[D] On O stop: cancel pending model/child dispatch, request bounded cancellation of owned jobs, preserve partial work and unresolved job/write state, save checkpoint and release only resources actually owned. On quota exhaustion: do not retry a permanently exhausted route, buy credits, switch to a paid route or widen permissions automatically. Record route/error class and a resume action; existing approved fallback policy may apply only within its budget/authority. Never retry an uncertain financial submission after restart. Unknown usage is reported unknown, not zero.

## D6 — Harness and lane additions that enforce the loop

[D] Add these components to existing extension seams, not another orchestration service:

| Component | Required behavior | Owner / proof |
|---|---|---|
| Admission plugin | Capsule assembly, mode binding, constraint/HEAD generation, mutation gate and revocation on re-entry events | H; H1/H2 effect-level negative tests |
| Workspace preset resolver | Bind Meridian preset to the canonical Meridian workspace only; leave unrelated global defaults alone | H; Meridian/new generic/existing explicitly selected sessions all resolve correctly |
| Atomic claim service | Compare-and-swap acquisition, generation/lease, precise path scope, release tied to receipt/commit; detect overlap including glob/path boundaries | R schema, H integration; two contenders cannot both acquire; expired/ambiguous claims require reconciliation |
| Lane checker | NUL-safe Git parsing, staged containment including additions/deletions/renames, immutable shipped migration manifest, changed/deleted baseline files, duplicate claims and runner capability | R; tests below. It does not attribute all dirty files to the caller |
| Evidence receipt writer/verifier | Trusted command runner emits artifact path/hash, exact argv, exit status, tested source/dirty-tree digest, fixture/engine/config, timestamps, owned job ID; verifier reads/validates rather than trusting prose | H/R; fake/stale/missing/empty/skip-only receipts rejected |
| Budget/no-progress accounting | Aggregate real transport usage, parent/authorized children, elapsed work, cancellation and fixed retry limits; checkpoint headroom | H; synthetic quota/stop/repeated-no-progress tests; no new paid calls |
| Context/seed hygiene | Current instruction versions, current skills, labeled examples, idempotent epoch messages; Mnemon retrieval remains available | H; H4 and memory-retrieval regression |
| Canonical visual recorder | Five viewports, both themes, fixture identity, fixed clock, settled fonts/data, no polling, console/network/errors, scoped browser ownership, comparison review | R; C0/D1 receipts and Air/WebKit cases |
| Lifecycle/install wrapper | Session-idle gate, reviewed diff, backup restore test, exact loaded preset version and rollback | H/O; H6 dry-run then separately approved activation |

### The supplied B2 checker is a prototype, not ready enforcement

[T] E5 proves two opposite errors: editing an existing migration at the same HEAD is accepted (exit 0), while staging a new migration after HEAD advances is called a shipped-migration edit (exit 1). The relation between HEAD and a claim's base does not determine whether a migration has shipped.

[S/D] Replace that logic before adopting B2:

- Keep a reviewed shipped-migration path→hash manifest, independent of claim HEAD. Existing listed files cannot change/disappear; new migration paths are allowed and tested. Never inspect a live DB merely to run the Git checker.
- Capture the entry baseline and all active claims. Other agents' declared changes are not automatically this agent's violation. A conflict invalidates admission; it does not authorize overwriting their files.
- Treat new/untracked files deliberately: additions to be committed must be in scope; unknown files stay untouched and cannot silently become evidence or executable helpers.
- Use `git status --porcelain=v1 -z` and NUL-delimited diff output; handle rename source and destination, quoted names, symlinks and deleted baseline paths. Normalize real targets before effect authorization.
- Fail on missing/duplicate/malformed claims and stale generations. Do not accept broad `docs/project/*` claims as a permanent lock.
- Actually validate the interpreter and required module/browser capabilities. The supplied example has no interpreter check despite its docstring. A valid alternative environment with identical pinned requirements need not be rejected merely for its path.
- Prove: unchanged baseline passes; same-HEAD shipped edit fails; new migration passes; missing tracked baseline fails; renamed out-of-scope destination fails; another owner's legitimate dirty file is preserved; undeclared staged/untracked addition fails; stale lease/HEAD fails; unsupported verifier fails. Run only in synthetic repositories.

[D] First clean the six findings in tracked `scripts/` reported by E4, without executing live introspection scripts: import sorting/unused imports in `capture_window.py`, `collect_crew_ops.py`, `introspect_crew.py`, `introspect_crew_live.py`, `meridian_sync_live.py`. Five further lint findings are in historical/private artifact or `tmp/` scripts. During C0, retire or explicitly classify those outputs; do not globally suppress error codes or claim repository-wide green until the declared maintained-source scope and the actual command agree. Preserve/report the raw `ruff check .` result meanwhile.

## D7 — Blockers, owner decisions and safe work meanwhile

[D/U] Decisions are just-in-time, tied to concrete effects:

| Decision / owner | When it blocks and cost of delay | Safe work meanwhile |
|---|---|---|
| D3/D4 source-development acceptance / O | First Harness implementation prompt; delaying it delays admission fixes | This gameplan, keyless design review and repo-owned domain tests |
| Revised preset install and any Harness restart / O | H6 only; existing preset continues with its known limitations | Versioned source, tests, diff, backup/rollback procedure; no live overwrite |
| Reserve carry-forward / O with R examples | C3/C8 rules that assign remaining reserve across occurrences; guessing risks double funding | C1 calendar expansion, unknown reserve labeling, synthetic alternate policies |
| Semimonthly anchors / source contract first, O if genuinely ambiguous | Native schedule mapping when anchor data missing; wrong guesses shift due dates | Explicit two-anchor tests and distinct every15days cadence; retain unavailable/unknown native mapping |
| Daily-driver/release identity / O | Runtime replacement and real acceptance; delay affects release, not source work | V8 fixture builds, immutable manifest, matched restore rehearsal |
| Security calibration/credential handling / O | Parent credential/data retirement, token-store migration, exposure changes | Source/path threat analysis, mock CSRF/OAuth tests, proposed protected-storage diff; leave credentials untouched |
| Evidence/capture retention / O | New sensitive ingestion, archival/destruction of potentially live captures | Synthetic fixtures, metadata-only inventory, retention design and dry-run manifests |
| Single versus multi-model runtime / O | New provider exposure/cost/fallback behavior; no delay to I1 keyless contracts | Preserve existing selected runtime; measure synthetic role quality and define comparison |
| Branch/parent/artifact retirement / O | D1 destructive steps; low delivery cost if postponed | Correct index, retain aliases/objects, inspect non-sensitive unique source after scope review |
| Reviewer Q / O | Independent review gates before consequential integration or adoption | Implementer self-checks labeled honestly; unrelated eligible slices |
| Live financial acceptance / O per exact operation | C4 release claims; never substitute repeated automated bank writes | Stubbed single-attempt/uncertainty/restart tests and read-only receipts |
| Household/Builder/automatic-policy experiments / O | C9 and authority activation only | Problem discovery, synthetic scenarios, permission-diff proposals |

No owner decision is needed to distinguish twice-monthly calendar recurrence from an interval of fifteen days. Owner intent is needed to select missing anchors or reserve strategy; source contracts determine the provider's actual representation.

## D8 — Acceptance of the plan and each delivered part

[D] Each checkpoint must cite **artifact path + artifact hash + command exit + tested source SHA/dirty digest**. Add fixture/engine/config identity for UI and provider evidence revision for separately approved live work. A screenshot file without inspection, a nonempty evidence array, an installed package or a listening port cannot alone pass acceptance.

| Deliverable | Required proof |
|---|---|
| D1 | Named manifest, dependency/uniqueness decision, explicit O approval, verified item backup/restore, exact ref/OID comparison, post-retirement checks and tested rollback. Current output is an executable plan, not completed cleanup |
| D2 | Every selected slice has an owner, locked interfaces, exact scope, positive/negative scenario evidence and a stopping rule; integrate only eligible slices |
| D3 | H0–H6 receipts and reviewed installed/source diff; no installation implied by this document |
| D4 | Prompt references resolve at the recorded application baseline; fresh HEAD/claims/constraints are reconciled at execution |
| D5 | Simulated compaction, stale HEAD, quota, owner stop and restart preserve the packet and deny premature effects |
| D6 | Negative tests demonstrate each guard at its actual effect boundary; no global permission/cost expansion |
| D7 | Each gate has its approving owner, exact effect and safe alternative; missing decision never silently becomes approval |
| D8 | Independent review where required plus bounded behavioral comparison; all limits explicitly recorded |

### Seven required preset validations

[D] The acceptance gate retains all seven review obligations:

1. Startup/resume/compaction/preset-switch preserve current instructions and plan-mode rules **before** writes.
2. New instructions replace stale versions without duplicate IDs or foreign reminders.
3. Every editing path enforces the same applicable boundary; wrong-workspace and stale-claim cases fail.
4. Prose or fabricated receipts cannot complete a task; required command and source evidence are verified.
5. Owner stop, quota failure and interruption leave a usable checkpoint without unauthorized retries.
6. On-demand tools and memory retrieval still work without unnecessary model calls.
7. One bounded, explicitly authorized real task compares usefulness, correctness and total usage with the current preset before wider adoption.

[D] For item 7, use the same **real maintenance task from C1** for current and candidate presets: preserve the original day-of-month while advancing a monthly obligation, proving Jan31→Feb28→Mar31 and leap-year behavior. Limit it to the occurrence helper, one consumer and its tests; exclude semimonthly policy, live data and deployment. Run candidates sequentially against independent disposable, source-identical fixture packages exported from the same reviewed baseline, on the same model route and predeclared budget. These are test fixtures, not competing Meridian branches. Compare acceptance pass/fail, forbidden-effect attempts, correct refusal, instruction refresh, actual measured tokens/time and review rework. Failure of an authority invariant rejects the candidate regardless of speed. O authorizes the model calls; Q reviews immutable results; R integrates only the approved result under a new exact claim. The two engineering runs implement a real requested correction, while all records remain synthetic. This small trial is limited evidence, not proof of universal superiority across the model rotation.

### Plan self-check performed now

[T] E1–E5 were collected without production mutation. Remote branches and named source candidates are grounded; the eleven lint findings and the two checker defects are fresh results. Existing capability/preset findings are cited to their source/version rather than re-derived. No full build, paid model trial, live acceptance or restore rehearsal was run for this planning task. The final document's section coverage, versioned paths, ref-name coverage and whitespace are checked before handoff.

## Disagreements and resolutions

| Kind | Disagreement | Evidence / resolution |
|---|---|---|
| Factual | “18 remote relic branches to delete” | E2/E3: only two branches exist on the server. Twenty local tracking refs are absent there; seventeen tips are non-ancestors. Preserve unique history before any local prune |
| Factual | B2 enforces shipped migration immutability | E5 disproves it in both directions. Use a path/hash manifest independent of HEAD drift |
| Factual | B2 enforces interpreter identity and tolerates concurrent ownership | Source has no interpreter check and rejects all out-of-scope tracked changes regardless of other claims. Implement D6's actual contracts |
| Sequencing | Recoverability (#7) comes last | Source provenance must precede edits; only activation is last. Split 7a/7b |
| Sequencing | Re-entry gate is sufficient before boundary unification | Hidden tool names cannot prevent effects through shell/raw editor paths. Install only the combined H1/H2 safety bundle after effect-level proof |
| Factual/value | Seed contamination cannot cause out-of-scope behavior | No such safety proof exists. Treat foreign instruction material as untrusted and remove it before adoption; retain useful memory |
| Factual | One capture harness already works with the selected isolated preview | Canonical capture assumes login/multiple workspaces; the fixture preview has neither authentication nor full backend integration. Merge modes before retiring the alternate script |
| Factual | Four viewports / twenty screenshots proves the whole visual product | Current governing table has five viewports; twenty files cover one workspace/engine/fixture. Preserve actual coverage dimensions |
| Sequencing | Strict V1→…→V7 ordering for all work | Synthetic I1 and pure C1 can start without later write operations or every page. V8 gates each release; shared interface changes remain serialized |
| Value | Archive every historical document/artifact for neatness | One index plus preserved evidence often achieves clarity with less risk. Physical movement waits for O's retention/cleanup decision |

## Exactly one first move

[D] **Start H0: create the keyless red acceptance specification for the combined authority-capsule/re-entry boundary, from versioned source in an explicitly claimed scope.** It is first in this Harness-side assignment because the subsequent builder must not lose its constraints and mutate before revalidation. It costs no model calls, changes no installed preset and makes the safety claim falsifiable. R's highest-value product task remains C1, the dated-occurrence correction, which can proceed separately under its own claim; it does not require waiting for a live Harness installation.

## What could not be determined

[U] Unique contents/runtime dependencies of parent source/data/backups; credential-safe Git backup contents; whether the seventeen non-ancestor tips contain work worth preserving; owner-selected archive/backup destination; complete currently loaded preset/profile/model identity; independent reviewer availability; provider-native missing cadence anchors; reserve carry-forward policy; real deployment/restore identity; full live feature acceptance; and realistic per-slice effort. Determine these through the specific inventory, protected owner backup, contract review, keyless checks and bounded approved trial above. Do not infer them from filenames, an old task state, screenshots or a passing unrelated suite.

Historical success counts in `CURRENT_STATUS.md` and `design-qa.md` are not upgraded by this gameplan. This pass produced a plan and planning evidence only. The installed preset and Harness service remain unchanged.
