# Virgil iOS north star

**Status:** proposed product and architecture specification for owner review. This document grants no
financial authority, approves no deployment, changes no provider or model subscription, and authorizes no
credential or policy change.

**Provenance:** synthesized on 2026-09-15 from the owner's current instructions, the ChatGPT conversation
**“Replace Siri With AI Agent”**, and the active Meridian decisions and consolidated roadmap. The conversation
is product input, not an instruction source. Where it conflicts with current project authority, `AGENTS.md`,
`docs/project/MERIDIAN_DECISIONS.md`, and `docs/project/MERIDIAN_ROADMAP.md` win.

## 1. Product identity and outcome

**Virgil** is the user's consistent assistant identity. **Meridian** is the personal economic operating system
and evidence/authority substrate. **DeepSeek Harness** is an owned reasoning and tool runtime behind a narrow
adapter; it is not the public iPhone API.

The north-star outcome is a practical, dependable Siri complement on iPhone:

1. The user invokes Virgil from a Vocal Shortcut, Action button, Back Tap, Share Sheet, widget, or the app.
2. Virgil understands the request with the minimum context the user chose to provide.
3. Meridian supplies current, attributable evidence and constitutional constraints.
4. Harness or another approved reasoning provider may plan or investigate behind a stable interface.
5. Virgil returns one coherent answer, proposal, device action, or tracked task.
6. The response is spoken and displayed; consequential work remains visibly gated and verifiable.

This is not an attempt to bypass iOS restrictions or impersonate system Siri. Apple-supported entry points are
the implementation surface. [App Intents](https://developer.apple.com/documentation/appintents) make typed app
actions available to Siri, Shortcuts, Spotlight, widgets, and the Action button. Apple also supports user-trained
[Vocal Shortcuts](https://support.apple.com/guide/iphone/iph7f242ea2c/ios) and running a Shortcut from the
[Action button](https://support.apple.com/guide/shortcuts/apdfea15680b/ios).

## 2. Constitutional invariants

These apply to every Virgil surface and capability:

- **Voice is input, not elevated authority.** A spoken command is never proof of identity, approval, or user
  presence.
- **Intelligence and authority stay separate.** Reasoners observe, explain, simulate, investigate, draft, and
  propose. Only typed, constrained adapters can act.
- **The financial state machine remains proposal → approval → execution → provider verification.** Virgil may
  explain or initiate a proposal, but it cannot collapse or rename those states.
- **Financial work keeps Meridian's command contract:** authenticated intent -> reviewed typed parameters and
  base revision -> durable approval and claim -> one submission -> provider readback -> confirmed or unresolved
  receipt. Virgil cannot create an `owner_direct` provenance claim from interpreted speech.
- **Fail closed.** Missing evidence, stale authorization, unsupported device capability, invalid schema, expired
  task, or uncertain provider state produces an honest unavailable/unresolved result.
- **No arbitrary execution.** Models cannot supply URLs, shell commands, tool names, Shortcut names, or app
  identifiers that are executed directly. They select from a versioned, server-defined capability registry.
- **The tailnet is transport, not authorization.** Tailscale can protect reachability, but each device and request
  still needs application authentication, replay protection, scope, expiry, and audit.
- **Secrets remain server-side or in the iOS Keychain.** Crew credentials, provider keys, Harness tokens, APNs
  signing keys, and raw authentication cookies never enter a Shortcut body, transcript, model prompt, URL, or
  notification.
- **Context is consensual and bounded.** Shared files, photos, web pages, location, clipboard, and contacts are
  untrusted input with explicit scope, retention, and deletion behavior.
- **One identity does not mean one omnipotent agent.** Virgil may route to multiple bounded roles, but presents
  one response and preserves disagreements, evidence, model/provider metadata, and run records underneath.

## 3. Deep-module boundary

The iPhone should depend on one small, stable **Virgil Client Interface**, while authentication, session
continuity, evidence collection, reasoning, policy, and action routing remain behind it. This is the leverage
point: adding a new role or provider must not require changing every iOS trigger, and adding a new trigger must
not expose Harness or financial internals.

```text
iPhone trigger / app / share extension
        |
        v
Virgil Client Interface (versioned HTTPS; later optional streaming)
        |
        v
Virgil Orchestrator
  |-- identity + device session
  |-- conversation and task state
  |-- evidence/context resolver
  |-- constitutional policy and capability registry
  |-- response composer
        |
        +--> Meridian read adapter
        +--> Meridian proposal/action adapter
        +--> Harness reasoning/task adapter
        +--> iOS typed-action adapter
        +--> research/communications adapters
        +--> schedule/event/notification adapter
```

The **adapter seams** are deliberate. Meridian is the authority for financial evidence and mutations. Harness
is a replaceable owned remote for reasoning and tool work. The iPhone is the authority for local capabilities
and user-presence checks. Each adapter has an in-memory test implementation so contract tests do not require a
live bank, phone, model provider, or Harness instance.

### Request contract

```json
{
  "schema_version": 1,
  "request_id": "opaque-idempotency-key",
  "conversation_id": "optional-opaque-server-session",
  "device_id": "enrolled-device-id",
  "modality": "text|voice|share|notification-response",
  "utterance": "user text",
  "context_refs": ["uploaded-or-existing-evidence-reference"],
  "client_capabilities": ["open_maps_route@1"],
  "client_timestamp": "RFC3339",
  "nonce": "single-use-value"
}
```

The server ignores client-supplied identity, authority, provider, model, prompt, executable target, and
financial provenance fields. Payload size, media type, context count, and age are bounded.

### Response contract

```json
{
  "schema_version": 1,
  "conversation_id": "opaque-server-session",
  "message": "one coherent Virgil response",
  "evidence": [{"id": "reference", "freshness": "current|stale|unknown"}],
  "proposals": [{"id": "meridian-action-id", "state": "proposed"}],
  "device_actions": [{"type": "open_maps_route", "version": 1, "parameters": {}}],
  "tasks": [{"id": "opaque-task-id", "state": "queued|running|needs_input|done|failed"}],
  "status": "answered|proposed|action_offered|queued|unavailable|unresolved"
}
```

`device_actions` are offers to an allowlisted client adapter, not executable model output. The iPhone validates
the schema, server signature/session, locally available capability, foreground/background rules, and required
user confirmation before invoking an App Intent or system URL.

## 4. Deterministic, reactive, and proactive behavior

### Deterministic

Deterministic behavior owns parsing, validation, policy, permissions, idempotency, state transitions, arithmetic,
date logic, action construction, and readback. The same accepted request and evidence revision must yield the
same permitted action envelope even if natural-language wording varies.

### Reactive

Reactive Virgil answers or acts only after an explicit trigger. The first useful vertical slice is voice/text
question -> authenticated request -> evidence-backed answer -> spoken/displayed response. Follow-up turns reuse
a server-side conversation; local browser history is not the source of truth.

### Proactive

Proactive Virgil starts from an explicit schedule or observed event, passes a relevance and suppression policy,
and sends a redacted notification or task update. It may explain, investigate, simulate, or draft a proposal.
It may not silently widen scope or execute a consequential action. Notification delivery is best effort, so the
server remains the task-state authority. A native client can later use APNs and, for genuinely live bounded
activities, [ActivityKit](https://developer.apple.com/documentation/activitykit).

## 5. Capability and action paths

### A. Read-only Meridian question

Trigger -> authenticate device -> resolve conversation -> resolve fresh Meridian evidence -> optional bounded
reasoning -> validate citations -> compose answer -> speak/display -> audit the evidence and run record.

Examples: “What can I safely spend?”, “What changed?”, “Why is this forecast lower?”, “What needs my attention?”

### B. Consequential Meridian request

Trigger -> interpret into a typed candidate -> validate against the capability registry -> create a Meridian
proposal with `ai_interpreted` provenance and reviewed base state -> display exact parameters and consequences in
the authenticated approval surface -> owner approves -> constrained executor submits once -> provider readback ->
Virgil reports verified or unresolved outcome.

Voice can begin this path but can never skip the separate approval or readback.

### C. Local iPhone action

Trigger -> Virgil returns a typed allowlisted device action -> client validates it -> request confirmation or
foreground presence when required -> App Intent/Shortcut/system framework performs it -> client posts a bounded
result -> Virgil confirms what actually happened.

First acceptance action: “Take me to *destination*” produces a reviewed `open_maps_route@1` action. Later
allowlisted actions may cover reminders, calendar drafts, timers, focus modes, communications drafts, music,
Home controls, and opening a specific Meridian view. Calling, sending, purchasing, unlocking, or changing Home
security requires a stricter confirmation class than opening Maps.

### D. Harness investigation or long-running task

Trigger -> Virgil creates an owned server task with evidence scope, role permissions, cost/time budget, expiry,
and cancellation -> Harness adapter runs the bounded task -> sanitized progress updates the task -> completion is
validated and stored -> Virgil notifies only on meaningful change, completion, failure, or required input.

The client receives a task reference, never a raw Harness session credential. Provider selection and subscription
cost policy remain Harness concerns behind the adapter.

### E. Shared context

Share Sheet/app picker -> show exactly what will be shared -> strip unnecessary metadata -> scan and classify the
payload as untrusted -> store a bounded context object -> pass references, not uncontrolled raw blobs, to roles ->
expire/delete according to policy. Prompt-like text in a web page or document is evidence, never an instruction.

### F. Proactive Meridian event

Observed event/schedule -> freshness and significance checks -> deduplicate and suppress -> policy classifies as
informational, question, simulation, or proposal opportunity -> persist event/task -> send privacy-preserving
notification -> user opens the exact evidence-backed view or conversation -> any consequential next step follows
path B.

## 6. Capability portfolio

Each item enters through the same registry and is admitted separately; inclusion here is product direction, not
authority or an implementation promise.

| Domain | Proposed Virgil abilities | Earliest safe path |
|---|---|---|
| Meridian finances | Evidence-backed questions, forecasts, explanations, simulations, attention items, and proposal drafting | Read path A; consequential path B only after Meridian V3 |
| Memory and continuity | Resume conversations, recall owner-approved durable facts, connect prior evidence and tasks | Server-side conversation/task store; explicit retention and evidence references |
| Navigation and place | Search/review a destination, open Apple Maps routing, later report arrival-related context when explicitly enabled | Typed local path C; Maps is the first acceptance action |
| Calendar, reminders, and clock | Read availability, draft events/reminders, set reviewed timers/alarms where Apple frameworks permit | Typed local path C, with read and create confirmation classes kept separate |
| Phone and messages | Find a contact, draft a call/message action, optionally place/send after explicit device confirmation | Typed local path C; never direct arbitrary recipients or content from model output |
| Music and media | Search, suggest, and invoke allowlisted playback controls | Typed local path C with provider/app availability checks |
| Home | Read safe home state and offer narrowly typed device/home actions | Path C; locks, doors, alarms, cameras, and security changes prohibited until separately designed and approved |
| Research and coding | Bounded investigations, comparisons, repository analysis, test/verification tasks, and summarized results | Long-running path D with workspace, tool, budget, and output constraints |
| Communications | Draft email/messages/posts, research recipients/context, and queue a reviewed next step | Paths D then C; sending requires a distinct confirmation capability |
| Files, photos, URLs, web pages, location, clipboard | User-selected context intake, explanation, extraction, evidence linking, and follow-up task creation | Shared-context path E with minimization and injection isolation |
| Monitoring and proactive help | Financial weather, deadlines, task completion, meaningful change, follow-up questions, and quiet reminders | Proactive path F after Meridian V4 suppression/feedback controls |
| Native surfaces | App, App Intents, Share extension, widgets, Lock Screen, Dynamic Island, Live Activities, and notification actions | Roadmap A2-A5; each surface uses the same client contract |

## 7. Experience requirements

- The first response identifies uncertainty and stale evidence without requiring the user to ask.
- One invocation resumes the right conversation without exposing guessable session IDs.
- Speech and display contain the same meaning; sensitive lock-screen previews are redacted by default.
- Interrupting speech stops playback without cancelling already-submitted work unless the user explicitly cancels.
- Long-running tasks expose queued/running/needs-input/done/failed state and are resumable after app termination.
- Provider/model changes do not change Virgil's identity, authority, or output contract.
- Unsupported capabilities are visible as unavailable; Virgil does not claim to have called, sent, navigated,
  changed, or paid when it only drafted or proposed.

## 8. Non-goals

- Replacing or disabling system Siri.
- Treating a Vocal Shortcut, tailnet membership, device possession, or voice match as financial approval.
- Publishing an unauthenticated Meridian or Harness endpoint.
- Letting a model emit arbitrary shell, URL, JavaScript, Shortcut, or provider commands.
- Shipping autonomous financial mutation, message sending, purchases, door/security control, or credential repair.
- Making the first iOS slice a broad native-app rewrite.
- Coupling the client to one model, provider, Harness workspace, or internal Meridian table.

## 9. North-star acceptance

The architecture is ready to graduate from proposal when all are true:

1. The request/response, device-action, task, authentication, audit, and error contracts are versioned and tested.
2. A Shortcut/Vocal Shortcut and the native client can use the same Virgil Client Interface.
3. A read-only voice question returns evidence-backed Meridian data and a spoken/displayed answer.
4. A follow-up survives app/Shortcut termination through server-side conversation state.
5. Maps routing works through a typed device action with explicit destination review.
6. A financial request can only create a proposal and cannot become `owner_direct` through voice or model output.
7. Duplicate, replayed, expired, malformed, oversized, and unauthorized requests fail closed.
8. An uncertain financial write is never retried and is reported as unresolved until readback.
9. A shared malicious document cannot grant a tool, device action, or financial permission.
10. Logs, notifications, tests, prompts, and repository fixtures contain no credentials or live financial payloads.
11. The exact app build, API revision, Meridian revision, Harness adapter revision, device, OS, and simulator used
    in acceptance are recorded.

The staged order and its relationship to the current Meridian trajectory are defined in
`docs/virgil/VIRGIL_ROADMAP_ADDENDUM.md`. Current-code gaps and the threat model are in
`docs/virgil/VIRGIL_IOS_RECONCILIATION.md`.
