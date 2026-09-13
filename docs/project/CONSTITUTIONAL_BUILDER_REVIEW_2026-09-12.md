# Meridian Constitutional Builder: installed-preset review

Status: review and proposed changes only. The installed preset, model routes, memory system, permissions and running Harness were not modified. No model calls or subagents were used in this review.

## Scope and verdict

Inspected the actual installation at `/Users/stephenwest/.dsh/.agent-presets/meridian-constitutional-builder/`, the generic sibling preset, selected settings fields, and the local Harness implementations of persona, system-prompt assembly, plan mode and Ralph. Six keyless assertions exercised the installed custom hooks and seed builder with synthetic sessions.

Keep the Meridian mission, one-slice discipline, financial-authority separation, on-demand discovery and durable context approach. Change the context/permission plumbing before relying on this as an enforced build loop. Today it is primarily a strong persona plus experimental prefab controls; the named DISCOVER → COMMIT stages are instructions, not a validated state machine.

The generic `constitutional-builder` is the configured default for new sessions. This does **not** mean the special mode was unused: the supplied archived session records explicit selections of `meridian-constitutional-builder`. Bind/check the Meridian preset for the Meridian workspace; do not change the global default to a lane-specific preset for unrelated projects.

## Changes I recommend, in order

### 1. Preserve governing instructions and active mode constraints

`instruction-hint.mjs:239–242` tells the model that AGENTS/CLAUDE files are “not task instructions” and that the task “never depends on them.” That directly contradicts the Meridian persona and the repository's instruction model.

`agent.cordis.yml:123–124` sets `complete: true` and `includeRuntimeContext: false`. The Harness system-prompt assembler restores a complete section as the sole system section and removes suppressed contexts after its waterfall. This can suppress the normal `plan:policy` system section and runtime policy snapshots. Host/tool enforcement is a separate layer; this finding is about what the model sees, not proof that every permission check is bypassed.

**Proposal:** preserve a concise, always-visible authority/mode capsule; treat accepted project instructions as requirements under the governing precedence rules. Remove blanket complete-prompt/context suppression, or replace it with an explicitly tested allowlist that preserves required sections. Keep optional catalogs lazy.

### 2. Make re-entry a read/verify boundary, not merely a reminder

The context gate removes newly appended instruction messages and runtime contexts immediately after `compaction/end`. The tool bootstrap simultaneously exposes `bash`, `str_replace_editor` and configured read/write/edit tools. The instruction hint is once per session, not once per compaction epoch or instruction version.

**Tested:** after synthetic compaction, fresh instruction context was removed while `write` remained in the catalog; after a prior durable hint and a later compaction/promotion, no fresh instruction hint appeared.

**Proposal:** before the first mutation after startup, resume, compaction, model/preset change or HEAD movement, validate a small re-entry packet: repository/branch, task, approved scope, current constraints version, file claims, last verified commit, unresolved outcomes and next action. Do not allow a first tool call to count as proof that those checks happened.

Important qualification: startup is not necessarily instruction-free. The seed loader does read the current global/workspace AGENTS files and substitutes them into one seeded tool result. The defect is inconsistent context provenance and refresh, especially after compaction.

### 3. Remove foreign instruction/catalog material from the seed

The approximately 80 KB `template.jsonl` contains two warm-up turns. `buildSeedPlan` replaces an instruction tool result and selected skill-search results, but retains separate user-role reminders from the roll environment.

**Tested:** a seed rendered for a synthetic current workspace still contains the original Windows instruction reminder and an old `available_skills` block. The Windows rules are conditional; this is not a claim that Windows commands were executed on the Mac. It is evidence that stale, foreign context survives hydration.

**Proposal:** retain only explicitly labeled, environment-neutral examples. Rebuild instruction and skill context from the current registry. Treat example history as examples, never as current-session verification. Prefer a concise re-entry packet if the prefab cannot demonstrate a task-quality benefit across the actual model rotation. Seeding makes no LLM call, but replayed text can still occupy subsequent model input.

### 4. Give every write-capable tool the same boundary

`agent.cordis.yml:242–256` isolates `str_replace_editor` behind `dsh-fs-local`, while the normal file tools use the host filesystem provider. Its cwd comes from `DSH_CWD`/`process.cwd()`; the Meridian lane restriction is persona text rather than an explicit preset startup/path check.

**Proposal:** route the editor through the same applicable filesystem/permission boundary, validate the workspace/branch at entry, and check claimed paths before mutation/commit. Tests should cover wrong cwd, path escapes, stale HEAD and another writer's claim. No out-of-scope write was attempted in this review.

### 5. Add bounded progress and completion evidence

The named build stages are not mechanically coupled to evidence. The preset offers delegation/workflow tools and a Ralph ceiling of 64 rounds. Ralph is an explicitly requested optional tool, not an automatically running 64-round loop; its structured completion report requires nonempty evidence but does not itself prove a test passed.

**Proposal:** one slice per cycle, a declared aggregate time/token budget, a bounded retry policy and a no-progress stop. Record actual transport usage, including children when authorized. Advancement to verified/complete requires observed command exit codes, tested source identity and the relevant browser/provider evidence. A task should checkpoint cleanly when the owner says stop, quota is exhausted or evidence cannot be obtained.

Preserve current owner authorization: ordinary authorized fixes should not acquire a new confirmation at every stage. Native plan mode and genuinely gated actions still follow their explicit approval contracts.

### 6. Update the Meridian-specific operating packet

The persona predates the consolidated roadmap and coordination file. Its resume references use bare status/ledger filenames rather than their `docs/project/` locations. Add the current accepted roadmap entry, decisions, active task packet, coordination claim and visual capture contract by exact path/version; avoid loading every historical narrative.

For UI work, include data-density and target-device cases, not only the attractive three-event fixture: long titles, large/unknown amounts, many same-day events, long lists, stale/unavailable states, Safari/WebKit and the owner's iPhone Air viewport. Capture production templates with isolated data; verify the actual served template/assets separately.

Keep Mnemon and durable memory. Use one compact working checkpoint with references to versioned evidence; do not replace it with repeated full-history injection or automatically add paid memory-agent fan-out.

### 7. Make the preset recoverable and identifiable

The Meridian README still describes installing/selecting “Prefab Anchored Standard” and includes Windows/generic installation instructions. Correct the name, scope, entry documents and update procedure. Version the intended preset source in the canonical project and use a reviewed diff/backup for installation; do not silently overwrite a live preset during an active session.

Evaluate the loop on accepted task outcomes, regressions, grounding, authorization, stop/resume and total usage. The seed metadata's style checks and counts of phrases such as “let me” are not evidence of engineering quality.

## Proposed operational loop

1. Load/validate current context and active authorization.
2. Claim the bounded scope and check HEAD/file ownership.
3. Define one user-visible outcome and its acceptance evidence.
4. Reproduce the defect or establish a synthetic acceptance case.
5. Plan the narrow change; obtain only the approval the actual action requires.
6. Implement within the claim.
7. Run the relevant checks and inspect the actual rendered/returned behavior.
8. Review the diff, evidence, authority boundary and unrelated changes.
9. Commit only owned files; release the claim with its SHA.
10. If deployment is authorized, verify the served version and relevant configuration.
11. Checkpoint facts, unresolved issues, usage and exactly one next action.
12. Continue within the authorized scope/budget, or stop cleanly.

This is a proposed contract for the existing loop, not a request to create another orchestration service.

## Validation before installing a revision

- Startup/resume/compaction/preset-switch preserve current instructions and plan-mode rules before writes.
- Newer instructions replace stale versions without duplicate message IDs or foreign reminders.
- All editing paths enforce the same applicable boundary; wrong-workspace and stale-claim cases fail.
- Passing-looking prose without actual verification cannot complete a task.
- Owner stop, provider quota failure and process interruption preserve a usable checkpoint.
- On-demand tools and memory retrieval still work; no unnecessary model calls are added.
- One bounded, authorized real task compares usefulness, correctness and total usage against the current preset before wider adoption.

## Evidence anchors

Installed preset: `agent.cordis.yml` context-gate/tool-bootstrap/persona/bootstrap-filesystem/compaction/delegation sections; `instruction-hint.mjs:171–257`; `context-gate.mjs:156–211`; `tool-bootstrap.mjs:236–278`; `prefab-session-seed.mjs:297–315,385–400` and `template.jsonl`.

Harness source: `packages/preset/persona/src/index.ts:65–79`; `packages/core/system-prompt/src/index.ts:590–626`; `packages/plan/plan-mode/src/index.ts:211–219`; `packages/workflow/tool-ralph/src/index.ts:125–174`.

Six keyless assertions passed: post-compaction instruction filtering, context suppression, write-tool exposure during that phase, foreign instruction reminder retained in the seed, old skill catalog retained, and absence of an epoch-refreshed instruction hint. These were controlled module probes, not a full mounted-host integration test. No preset changes or paid behavioral evaluation were performed.
