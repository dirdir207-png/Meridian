# Investigator implementation contract

This is a proposed implementation contract for the owner-requested surface, not a claim these endpoints or helpers already exist. Read README first. It deliberately allows reuse of newer evidence work. Full icon-pack work and desktop Settings are excluded.

## File map, verified existing anchors

| Existing source | Reuse / proposed change |
|---|---|
| `templates/meridian/partials/transaction-inspector.html` | Add an Investigator section beneath the transaction summary, using current sheet/rail semantics. |
| `static/js/meridian/transaction-inspector.js` | Pass the selected target to the new controller, invalidate on target change/close, preserve focus restoration. |
| `static/css/meridian/inspector.css` | Reuse existing parchment surface, type and spacing. Keep any new styles scoped. |
| `meridian/api.py::transaction_detail` | Existing authenticated target lookup and evidence payload patterns; add a separate bounded POST route. |
| `meridian/api.py::evidence_content` | Existing authenticated evidence viewer and honest missing-blob behavior. |
| `meridian/ai/investigator.py::Investigator` | Run the established role, do not replace it with the contextual advisor's proposal path. |
| `meridian/ai/role.py::EvidenceBoundRole` | Existing evidence binding, context hook, failure states, citation validation; coordinate with current owner of this file. |
| `meridian/ai/run_records.py::RunRecordStore.record` | Persist metadata once for each completed role run; no generated prose or question schema expansion. |
| `scripts/investigate.py::{investigate,render,build_client}` | Reference for role invocation/serialization/provider factory; web code must not shell out to the CLI. |
| `meridian/evidence.py::EvidenceRepository` | Traverse existing local links, preserve source identity/access state. |
| `meridian/documents/extract.py::extract_document` | Existing source-attributed extraction (facts vs candidates); reuse where appropriate, not a new parallel ingestion system. |
| `meridian/gmail_intake.py` | Preserve current receipt match constraints and content-first storage fixes. |

Suggested new modules: `meridian/ai/investigation_service.py` for web orchestration and bounded context assembly, `static/js/meridian/investigator.js` for UI state, `static/css/meridian/investigator.css` for scoped styling. Change these names if the current architecture has a better seam. Keep backend role permissions unchanged.

## Proposed request and response

`POST /api/meridian/transactions/<transaction_id>/investigate`

```json
{
  "question": "Why did the amount change?",
  "owner_context": "I returned the rented equipment.",
  "include_related": true
}
```

Require authenticated access to the selected transaction, JSON object body, nonempty trimmed question (max 2,000 characters), optional string context (max 2,000), and strict boolean scope. Apply the project's current CSRF protection and request limits; do not broaden generic API allowlists. Server loads source IDs and facts; client-supplied evidence IDs or body text must not become trusted evidence. No provider name, key, prompt or arbitrary target kind is accepted from the browser.

Return `status` (`ok`, `unavailable`, `failed`), `claims`, `disagreements`, `assumptions`, `what_would_change`, a safe public `detail`, run metadata and stored run ID. Add `sources` with server-derived ID, title, relation, provenance, observed_at, access/content state and same-origin content URL; add `scope` with actual included/truncated counts. These additions are surface fields, not a change to the audit table. Never return parser text that includes raw model output, secrets or stack traces.

Invalid JSON/types/length → 400 before model invocation; inaccessible/missing target → 404 with no facts exposed; unauthenticated → existing auth behavior. A completed role run with unavailable/failed status remains a typed result. Infrastructure failures before a role run → safe 503. Audit-store failure must be explicit (`run_saved: false`) and never cause a second model call; do not claim the answer was recorded. Honor existing stronger project failure semantics if present.

## Meaningful evidence, bounded cross-references

Start at the selected transaction. Include directly linked accessible evidence. With related scope on, follow existing verified graph relations to linked commitment/document/event/observation facts relevant to the question. A default ceiling of one relationship hop, 12 evidence items, 24,000 total characters and 2,000 characters per item is a proposed starting bound, not a claim about current role-budget enforcement. Use the lower existing role/provider limit; expose a partial scope when capped. Use deterministic source ordering (direct, then verified related; timestamp and ID tie-break), cycle protection and deduplication. Never silently search all mail or fetch new provider data.

Send structured facts or minimal relevant excerpts with source IDs; source text is untrusted data, never instructions. Reuse the existing sanitized extraction and storage access paths. Only permit citations to included accessible sources. Validate expiry at read time, not only when a sweeper runs. Missing blobs can support only metadata statements, not claims about unread content. Owner context travels separately under an explicitly unverified label and cannot supply an invented evidence citation.

The current envelope only knows document references. If normalized transaction/observation facts need their own citation namespace, explicitly extend the contract and tests with the backend lane; do not pass an invented `transaction:*` ID through a document-only validator. If the active evidence pipeline already supports this, reuse it. Do not call the general advisor as a shortcut: its proposal sink is outside this surface's read-only scope.

The web client must use an injected server-side model client. Inspect the configured failover chain rather than assuming the role's one `complete()` call means one external request. Add no UI retry loop, provider-chain change or new credential flow. No evidence that can answer → an honest unavailable state; metadata alone must not be embellished into a financial explanation.

## Browser behavior

- Submit only by explicit button or an intentional keyboard shortcut. Suggestion chips populate, never auto-run. Show busy text and disable duplicate submission while pending.
- Use request generation IDs and target IDs to reject late results. Clearing/changing the target invalidates pending results even if network cancellation fails.
- Keep draft question/context in memory for the current target. Do not put them in URLs, analytics, localStorage or a transcript database. On target change clear them for the first slice.
- Render model text via textContent / DOM nodes, never raw HTML. Construct evidence links from validated server source entries, not generated URLs.
- Announce loading and result availability with a small polite live region; do not re-announce every source. Preserve a visible focus indicator and keyboard order. Keep current focus on submit; offer a result heading link if necessary rather than abruptly moving it.
- Mobile uses the existing full-screen inspector, no nested sheet. Controls have at least 44px touch targets; long citations and question text wrap. The close button remains reachable.
- Edits mark the existing answer as previous. Changing scope can change available findings; display which scope produced the result.

## Acceptance cases (synthetic only)

1. Same selected transaction, question A “What makes up $60?” vs B “Why did it increase?”: fake client records the actual different prompts and returns different evidence-bound findings; browser renders the corresponding response. Assert the request includes facts, not merely IDs.
2. Add owner context “equipment returned”: it reaches the role as unverified context, changes the interpretation to an unresolved fee question, never asserts a refund or edits the bill.
3. Related scope off omits prior-statement facts; on includes the verified relation, cites it and explains inclusion. A same-amount unrelated record remains excluded. Cycles and duplicate paths yield one source each.
4. No usable evidence → unavailable and zero model calls; revoked/deleted/expired items excluded; missing blob has no invented document facts. Preserve owner decision against broad backfill.
5. Hallucinated citation → whole result fails, zero displayed claims. Contradictions show both supported readings. Unparseable model response and unavailable model render safe states, no raw reply, no automatic retry.
6. Invalid target, malformed JSON/list body, whitespace question, oversize text, nonboolean scope, unauthenticated request and attempted evidence-ID injection fail before model access.
7. Double-click submits once. Target A reply arriving after opening B is discarded. Editing while pending never labels the pending answer as a response to the edited text. Closing never opens the inspector again on late completion.
8. Prompt-injection text in a document remains quoted evidence; hostile HTML in generated text is inert. Unsupported money/action claims are not presented as executed operations. No path to proposal sink or financial executor.
9. Audit row stores role/provider/model/evidence IDs/timing/outcome only. Storage failure is visible without a repeated model call. Do not claim a known provider/model when transport cannot attest it.
10. Existing transaction inspector deep links, Activity filters, focus restoration, missing-content viewer and contextual advisor continue working. Run current affected tests plus new service/API/UI tests.

Suggested existing regression suites: `tests/meridian/test_ai_investigator.py`, `tests/meridian/test_ai_envelope.py`, `tests/meridian/test_ai_run_records.py`, `tests/test_investigate_script.py`, `tests/meridian/test_evidence.py`, `tests/meridian/test_gmail_intake.py`, `tests/browser/test_transaction_inspector.py`, `tests/browser/test_evidence_memory.py`. Fresh source may add shared-role tests; include those. Add new targeted tests for the ten cases rather than weakening old assertions.

Use the repository's `.venv311` and synthetic preview setup. Follow `MERIDIAN_VISUAL_CAPTURE_SPEC.md` at 1440×900, 1024×768, 430×932, 390×844 and 420×912, explicit themes and specified DPR. Observe actual browser input → submit → answer → source opening. Final required checks include lint, JS syntax, `git diff --check`, relevant tests, roadmap reconciliation and regenerated handoff. A screenshot of the design specimen is not runtime acceptance.
