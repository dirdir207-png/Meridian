# Virgil iOS repository and threat-model reconciliation

**Inspection date:** 2026-09-15

**Meridian revision inspected:** `a3f8370dc6007e7b0fb2facb9003a40f3a4499c9` on
`feat/meridian-implementation`

**Harness:** read-only inspection of `/Users/stephenwest/deepseek-harness`; no configuration, provider, model,
workspace, session, or runtime changes were made.

**Status:** architecture evidence for owner review. This is not a penetration test, implementation approval,
deployment approval, credential enrollment, or finding that every route outside the inspected scope is safe.

## Executive verdict

Virgil iOS is a compatible expansion of Meridian, but it is **not currently an implemented end-to-end
capability**. The strongest reusable core is Meridian's evidence-bound advisor and durable proposal/approval/
execution/readback state machine. The principal missing module is a narrow Virgil orchestration boundary that
owns native-device authentication, durable conversation/task state, capability routing, and the adapters to
Meridian, Harness, and iOS.

The project should use a **hybrid workflow with exclusive ownership**, not two writers in one tree:

- Meridian product/API/action work stays in `simplecrew-latest` under the Meridian Constitutional Builder preset.
- Harness provider, SDK, session-runtime, or adapter work stays in the DeepSeek-Harness workspace under the
  default Constitution Builder preset.
- Codex performs cross-system architecture reconciliation, independent security/code review, verification, and
  narrowly assigned implementation only when its file scope is exclusive.

No new branch or worktree is recommended. Current Meridian authority requires the canonical tree and
`feat/meridian-implementation`; the older consultation's proposed fresh Virgil branch is superseded.

## Repository findings

| Needed capability | Current evidence | Reconciliation |
|---|---|---|
| Authenticated web application | Flask `login_required`, secure/HTTP-only/SameSite session-cookie settings, and `ProxyFix` for the Tailscale Serve topology | Reuse browser authentication for browser UI only. Native Virgil needs a distinct device-scoped credential and enrollment/revocation flow; do not copy cookies into Shortcuts. |
| Evidence-backed Virgil answer | `meridian/ai/advisor.py::ContextualAdvisor` restricts answers to supplied evidence IDs, validates citations, allowlists proposals, and fails unavailable | Reuse behind a Virgil read adapter. Generalize through the Track-I task/result envelope rather than making iOS call the advisor route directly. |
| Existing conversational Virgil UI | `static/js/ui/advisor_fab.js` uses `/api/meridian/advisor` or legacy `/api/advisor/chat` and keeps the last 20 messages in browser `localStorage` | Useful UI proof, not a durable or cross-device conversation service. It also has two advisor paths that should be hidden behind one orchestrator interface. |
| Financial action safety | `crew/actions.py` persists allowlisted requests and state transitions; `crew/executors.py` atomically claims, checks reviewed state, submits once, and requires readback before `verified` | This is the high-value reusable module. Virgil must enter as `ai_interpreted` and may create proposals only. Approval remains a separate authenticated owner act. |
| Local agent proposal seam | `/api/actions/propose/local` uses an `X-Local-Key` and can only create an inert transfer proposal | A useful least-authority pattern for a local Harness adapter, but not suitable as an iPhone token or general Virgil API. Its action surface is intentionally narrow. |
| Deterministic status export | `meridian/status_emitter.py` creates bounded, sanitized, read-only status events and rejects secrets, transcripts, paths, URLs, and financial payloads | Reuse its projection/sanitization principles for task progress. It is one-way status, not a command or conversational bridge. |
| Meridian memory | `meridian/services/memory.py` and the memory API expose evidence-oriented financial workspaces | Do not overload it with raw voice transcripts. Add separate conversation/task records with explicit retention, then reference evidence by opaque ID. |
| Browser notifications | `static/sw.js`, `static/js/features/notifications.js`, and authenticated push-subscription routes support Web Push | Reuse notification policy concepts. A native client still needs APNs device registration, token lifecycle, permission UX, and redacted payload rules. |
| PWA shell | `static/manifest.json` and the service worker provide an installable web surface | Useful fallback and early display surface; it does not supply native App Intents, Share extensions, Keychain, ActivityKit, or reliable background voice. |
| Native iOS client | No Swift, Xcode project/workspace, Swift package, App Intent, WidgetKit, or ActivityKit source was found | New bounded module required. Begin with a small Shortcut adapter; add the native shell only after the client contract is tested. |
| Voice/streaming | No application use of Web Speech, microphone capture, SSE, or WebSocket was found | Start with Shortcuts dictation and ordinary HTTPS. Streaming and interruptible speech are later experience work, not Phase 1 infrastructure. |
| Harness lifecycle and prompts | Harness contains a typed Session Controller/Gateway, durable sessions, an SDK that can run named sessions, prompt idempotency, cancellation, and streaming notifications | There is a real internal seam to build on, but no Meridian-owned, least-privilege Virgil adapter is present. Do not expose the Harness browser/Gateway or a general prompt endpoint to the phone. |
| Meridian-to-Harness bridge | No such adapter was found in the canonical Meridian repository | Treat as missing, not implied by current workspace availability. Define a narrow owned-remote interface and implement each side in its proper lane. |

### Existing strengths to preserve

- Contextual Advisor already demonstrates a deep interface: evidence preparation and proposal validation are
  hidden behind a small question/context call.
- The action state machine records the difference between executed and provider-verified. Virgil must preserve
  that semantic difference in speech, UI, notifications, and task status.
- The local proposer and sanitized status emitter demonstrate least-authority and data-minimization patterns.
- Harness has durable session machinery, prompt request IDs, cancellation, and an SDK surface. The adapter can
  leverage those without coupling Meridian to browser/UI internals.

### Gaps that must not be papered over

- No native authentication/enrollment or per-device revocation contract.
- No server-authoritative Virgil conversation and task store.
- No versioned Virgil client or device-action contract.
- No capability registry or per-capability confirmation class.
- No Meridian-to-Harness owned-remote adapter with constrained evidence/tool scope.
- No APNs, native extension, App Intent, widget, Live Activity, or physical-device acceptance harness.
- CSRF protection was not visible in the inspected Flask application code. That is an audit item, not a claim
  that exploitation is proven. Cookie-authenticated mutation routes must not be reused as the native API, and
  existing browser mutation routes need explicit Origin/CSRF verification before Virgil expands their reach.

## Recommended interfaces

Keep four deep modules with narrow contracts:

1. **Virgil Gateway** — authenticates an enrolled device; enforces payload, rate, nonce, timestamp, scope, and
   idempotency; accepts no provider/model/tool/authority selection from the client.
2. **Virgil Orchestrator** — owns conversation/task state, evidence references, policy decision, adapter routing,
   and one composed response. It receives capabilities, not ambient access.
3. **Harness Task Adapter** — accepts a typed bounded task with role, evidence references, read/tool permissions,
   time/token/cost budget, expiry, and cancellation. It returns sanitized progress and a validated result.
4. **iOS Action Adapter** — accepts only versioned enum cases with schema-validated parameters and confirmation
   class. The phone decides whether the capability exists and whether foreground/user presence is sufficient.

Avoid a shallow “chat endpoint” that accepts arbitrary prompt plus tools. It would expose the complexity and
authority of every downstream system to every trigger and make future providers/actions dangerous to add.

## Threat model

The protected assets are financial evidence and mutation authority, Crew/provider credentials, Harness and
model credentials, private conversation/context, device capabilities, task history, and trustworthy audit state.
Adversaries include a stolen/unlocked phone, malicious shared content, a network client on the tailnet, web-origin
attacks, prompt injection, compromised browser state, an over-capable model/role, and accidental retries.

| ID | Threat and impact | Required control / acceptance evidence |
|---|---|---|
| **VTH-01** | Credential or transcript leakage through Shortcut bodies, URLs, prompts, logs, fixtures, or notifications | Device-scoped Keychain secret; server-side provider/Crew/Harness secrets; structured redaction and retention tests; no secrets in query strings or push bodies |
| **VTH-02** | Voice spoofing or replay treated as owner authorization | Voice is never approval; short-lived authenticated request, nonce/timestamp, server replay cache, request ID, device binding; replay/expired tests |
| **VTH-03** | Model output becomes a confused deputy for iOS actions | Versioned action enum and schemas; server and client allowlists; parameter canonicalization; confirmation class; no arbitrary URL/Shortcut/tool names; malicious-output tests |
| **VTH-04** | Virgil bypasses Meridian financial gates | Force Virgil/agent provenance to `ai_interpreted`; separate approval surface; base-revision/precondition check; one execution; readback; negative tests for `owner_direct` injection |
| **VTH-05** | Prompt injection in a shared URL, file, image text, email, or research result grants tools or authority | Mark imported content untrusted; isolate content from instructions; fixed role/tool scope; capability firewall; injection corpus proving no permission/action elevation |
| **VTH-06** | CSRF or stolen browser cookie triggers state-changing web routes | Verify/add CSRF and Origin controls for cookie routes; use separate scoped bearer/device authentication for native API; never export browser cookies to Shortcuts |
| **VTH-07** | Tailnet membership is mistaken for application trust | Authenticate and authorize every request; bind token to user/device/scope; rate-limit and audit; test an unauthenticated tailnet client |
| **VTH-08** | Guessable/stolen conversation ID exposes cross-device context | High-entropy opaque IDs; server ownership check on every access; rotation/revocation; no IDs as bearer credentials; cross-user/device tests |
| **VTH-09** | Arbitrary URL scheme, deep link, Shortcut, or app target runs on device | Typed actions with per-case destination validation and allowed schemes; display destination before Maps navigation; reject `javascript:`, file, custom, and malformed schemes |
| **VTH-10** | Lock-screen notification reveals sensitive finances or private context | Redacted default content, per-category preview settings, generic task identifier, fetch detail after unlock; notification snapshot/privacy tests |
| **VTH-11** | Retry or duplicate submission causes double financial/device action | End-to-end idempotency across gateway, orchestrator, proposal, task, and device receipt; never retry uncertain financial writes; duplicate/disconnect tests |
| **VTH-12** | Long-running task outlives its evidence, budget, or permission set | Capture immutable permission/evidence version, budget, expiry, cancellation, and revocation at task creation; require reauthorization to widen scope |
| **VTH-13** | Harness or local bridge becomes a general remote-control endpoint | Bind only the protected adapter; mutual/app auth; strict schemas, size/rate limits, timeouts, and tool/evidence allowlists; keep raw Gateway/SDK unavailable to phone |
| **VTH-14** | Provider/model failure silently changes identity, quality, cost, or authority | Provider/model/run metadata, explicit unavailable/fallback policy, hard budgets, invariant output validation; fallback never widens capability or authority |
| **VTH-15** | App extension/background execution behaves differently from foreground | Per-capability execution-mode policy; require foreground/user presence where needed; simulator plus physical-device tests for termination, cancellation, and background limits |
| **VTH-16** | Proactive system creates alert storms or autonomous scope growth | Event deduplication, cooldown/suppression, relevance threshold, preference controls, quiet unchanged state, measurable usefulness; proactive output cannot mutate consequential state |

## Security and architecture decisions for A0

Before endpoint implementation, decide and record:

1. Minimum iPhone/iOS target and whether Phase A1 supports Shortcuts only or also a thin native shell.
2. Enrollment: how an authenticated Meridian owner enrolls, names, rotates, and revokes a device credential.
3. Request signing/replay contract, token scopes, expiry, and rate/payload limits.
4. Conversation/task schema and retention; raw audio should not be retained by default.
5. Capability registry and confirmation classes: read, open/display, draft, local reversible, send/communicate,
   financial/consequential, and prohibited.
6. Owned-remote Harness adapter interface, workspace/preset selection, role/tool scope, budget, cancellation, and
   sanitized progress contract.
7. APNs enrollment and notification privacy policy, deferred until A4 if A1 uses synchronous Shortcuts.
8. CSRF/Origin evidence for existing browser state-changing routes before any shared gateway is introduced.

## Verification plan

### Contract and adversarial

- Valid request/response and every error state; unknown versions and fields fail closed where security-sensitive.
- Missing/expired/revoked device, reused nonce/request ID, clock skew, wrong device/session, oversized request,
  too many context references, malformed Unicode/URL/destination, and rate exhaustion.
- Tool/prompt/action injection from user text and imported content; model attempts to select authority/provider/tool.
- Duplicate/delayed/out-of-order Harness notifications, cancellation, provider timeout, fallback, and budget expiry.
- Duplicate financial proposal, approval expiry, changed base state, verifier exception, and uncertain write.

### iOS

- Xcode build/test and Swift concurrency checks on the selected toolchain.
- Simulator tests for networking, auth errors, conversation state, action schema, deep links, and UI privacy.
- Physical-device tests for Vocal Shortcuts, Action button/Back Tap where available, Share extension, microphone,
  speech output, Keychain persistence/revocation, lock-screen privacy, background termination, and APNs.
- Network-loss tests at request admission, Harness dispatch, action offer, device execution, and result receipt.

### System evidence

- Exact app/API/Meridian/Harness revisions and configuration identity, without secret values.
- End-to-end A1: invocation -> authenticated read -> cited response -> spoken/displayed output -> durable follow-up.
- End-to-end A2: reviewed Maps destination -> typed action -> local result receipt.
- Negative A3: voice/model cannot approve or directly execute; positive proposal -> separate approval -> one submit ->
  provider-verified/unresolved result.

## Xcode preflight result

**Verified 2026-09-15:** the storage/install blocker is resolved. The owner authorized pruning Docker build
cache and unused images; containers and volumes were preserved, and free space rose from about 27 GB to about
50 GB before installation. The signed Apple-silicon Xcode archive passed `codesign --verify --deep --strict`
and Gatekeeper assessment before installation at `/Applications/Xcode.app`.

The selected toolchain now reports:

| Check | Verified result |
|---|---|
| macOS | 26.4.1 (25E253) |
| Full Xcode | 26.6 (17F113) |
| Selected developer directory | `/Applications/Xcode.app/Contents/Developer` |
| iPhoneOS SDK | 26.5 |
| iPhoneSimulator SDK | 26.5 |
| Simulator runtime | iOS 26.5 (23F77) |
| Available phone profiles | iPhone 17 Pro/Pro Max/17e/17, and iPhone Air |
| `simctl` | `/Applications/Xcode.app/Contents/Developer/usr/bin/simctl` |
| First-launch components | `xcodebuild -checkFirstLaunchStatus` exit 0 |
| Code signing | verified state is **0 valid signing identities** |

Apple's [Xcode system requirements](https://developer.apple.com/xcode/system-requirements) list Xcode 26.6 as
compatible with macOS 26.2-26.x; Xcode 27 requires macOS 26.6 or later, so 26.6 is the newest compatible choice
for this Mac's current OS. The iPhone Air simulator booted and reported runtime 26.5, and `simctl io` captured a
real 1260 x 2736 display image. Its first `bootstatus -b` remained in Apple's one-time LaunchServices data
migration when the monitor was stopped after more than five minutes; the booted runtime and display are usable,
but a later acceptance run should still record a clean terminal boot after migration completes.

The verification commands were:

```bash
xcodebuild -version
xcode-select -p
xcrun --sdk iphoneos --show-sdk-version
xcrun --sdk iphonesimulator --show-sdk-version
xcrun --find simctl
xcrun simctl list runtimes
xcrun simctl list devices available
xcrun simctl boot 'iPhone Air'
xcrun simctl getenv booted SIMULATOR_RUNTIME_VERSION
xcrun simctl io booted screenshot <temporary-path>/iphone-air.png
xcodebuild -checkFirstLaunchStatus
security find-identity -v -p codesigning
```

Signing is inspected but not configured: the Apple developer account/team is not enrolled in Xcode and no
usable identity exists. Creating a certificate, profile, App ID, or device enrollment remains owner-gated.

## Recommended first implementation packet

When the owner accepts A0, the Meridian Builder should receive the entire north star for context but implement
only this packet:

1. Versioned Python request/response/device-action/task value objects and validation.
2. In-memory adapters for Meridian reads, Harness tasks, and iOS actions.
3. Device-auth/replay policy interfaces with fake test implementations; no production credential issuance.
4. Orchestrator tests proving read-only Q&A, unavailable evidence, injection isolation, idempotency, and that all
   financial output is proposal-only.
5. No endpoint, Swift app, live Harness call, APNs, deployment, or provider/model change in this packet.

That packet produces a deep, testable module before either system exposes another network surface. The next
packet can add the authenticated HTTP adapter and Shortcut client without changing the core contracts.

## Open owner decisions

- Minimum supported iPhone model/iOS and whether Action button acceptance is mandatory or optional.
- Device enrollment and revocation experience.
- Whether A1 begins as Shortcut-only or includes a thin native app immediately.
- Conversation retention and whether transcripts may sync across devices.
- Which single proactive event earns A4 first.
- Which device actions beyond Maps are useful enough to justify their confirmation and privacy surface.

The roadmap placement and slice gates are in `docs/virgil/VIRGIL_ROADMAP_ADDENDUM.md`; the complete product
contract is in `docs/virgil/VIRGIL_IOS_NORTH_STAR.md`.
