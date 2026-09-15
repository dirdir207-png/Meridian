# Virgil roadmap addendum

**Status:** proposed addendum to `docs/project/MERIDIAN_ROADMAP.md`. It does not supersede or reorder the
consolidated roadmap, grant authority, approve deployment, or create a separate branch, tree, or Harness.

## Placement in the current order of operations

Virgil is a **cross-track interface lane**, not a new fourth product trajectory. Its work attaches to the
existing capability spine at the points where Meridian can support it honestly:

```text
Track C:   V1 trustworthy read model -> V2 planning -> V3 controlled intervention -> V4 proactive loop
Track I:        I.1 envelope/permissions -> I.2 one useful role -> I.3 council
Virgil:   A0 contracts/threat model -> A1 read-only voice -> A2 device actions -> A3 proposals -> A4 proactive
```

The first buildable Virgil slice is **A1 after C-V1 and I.1 are adequate**, and it should begin before broad
C-V3 expansion. In plain terms: first make Meridian's answers trustworthy and its agent envelope enforceable;
then give Virgil an authenticated read-only voice path; then add bounded iPhone actions; only after the existing
executor path is release-ready should Virgil initiate consequential proposals.

This ordering avoids two traps: a polished voice surface that confidently reads unreliable data, and a general
assistant endpoint that acquires authority before its permissions are enforceable.

## Slices

| Virgil slice | Depends on | Outcome | Explicit boundary |
|---|---|---|---|
| **A0 — Contract and threat-model foundation** | Current decisions and inspected code | Versioned client, session, device-action, task, audit, and error contracts; enrollment/auth design; attack tests specified | Documentation and test harnesses only; no public endpoint or credential change |
| **A1 — Read-only voice vertical slice** | C-V1 trustworthy evidence; I.1 envelope/permissions | Vocal Shortcut/Shortcut -> authenticated Virgil interface -> one evidence-backed Meridian answer -> spoken/displayed result; server-side follow-up conversation | Read-only; no financial proposal, mutation, arbitrary tool, streaming, or background autonomy |
| **A2 — Deterministic device actions** | A1; typed client-action registry | Native shell/App Intent plus `open_maps_route@1`; Action button/Back Tap/Share Sheet use the same interface | Client validates allowlist and user presence; no arbitrary URLs, Shortcut names, calls, sends, or purchases |
| **A3 — Meridian proposal bridge** | C-V3 command contract and verified executor; A2 auth/audit | Voice may create an `ai_interpreted` financial proposal, open exact review UI, and report execution/readback state | Voice never approves; no `owner_direct`; no automatic retry; no mutation without separate owner approval |
| **A4 — Proactive and long-running work** | C-V4 closed feedback loop; I.2 useful role; task/suppression policy | Event/schedule-driven insights, bounded Harness investigations, meaningful APNs updates, resumable tasks | No alert storms; no silent scope growth; notification delivery is not completion; consequential output remains a proposal |
| **A5 — Rich conversational client** | A1-A4 measured and stable | Streaming, interruptible speech, richer native surfaces, widgets/Live Activities, context-sharing refinements, more device actions | Expansion remains capability-by-capability; native polish does not widen authority |

## Immediate sequence

1. **Now — A0:** accept or amend the north star and reconciliation; decide enrollment/authentication and the
   minimum supported iPhone/OS; install a compatible Xcode and simulator; define contract and adversarial tests.
2. **After C-V1 + I.1 gates — A1:** implement one text request first, then wire the same endpoint to a small
   Shortcut/Vocal Shortcut. Measure network, reasoning, and speech latency separately.
3. **Then — A2:** add the minimal native shell and one typed Maps action. Keep Shortcuts as an entry adapter,
   not the intelligence layer.
4. **At C-V3 readiness — A3:** connect Virgil to the existing proposal state machine and approval UI. Prove by
   negative tests that speech/model output cannot select direct mutation provenance.
5. **At C-V4 + I.2 readiness — A4:** add one high-value, low-noise proactive Meridian event and one bounded
   read-only Harness investigation. Measure usefulness and suppression before adding event types.
6. **Only after evidence — A5:** add persistent voice, streaming, broader local actions, widgets, Live
   Activities, communications, research, files/photos/URLs, and optional role routing one capability at a time.

## Release gates per slice

Every Virgil slice inherits roadmap V8 and adds:

- contract tests against in-memory adapters and the owned remote adapter;
- negative authorization, replay, injection, duplicate, timeout, cancellation, and privacy tests;
- exact running-identity capture for app/API/Meridian/Harness revisions;
- physical-device acceptance in addition to simulator acceptance for microphone, Shortcuts, notifications, and
  background behavior;
- explicit owner approval for production deployment, credentials, device enrollment, APNs setup, and any
  authority/policy activation.

## Integration rule

When accepted, the consolidated roadmap should gain a short link to this addendum rather than absorbing its full
detail. Task-ledger entries should be created only as each slice is accepted for implementation. All code remains
in the canonical `simplecrew-latest` tree on `feat/meridian-implementation`; Harness-side adapter work remains in
the DeepSeek-Harness workspace under its default Constitution Builder preset, while Meridian work uses the
Meridian Constitutional Builder preset.
