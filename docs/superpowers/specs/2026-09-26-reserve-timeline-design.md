# Meridian Reserve Timeline design

Date: 2026-09-26 · OS-116 / Track D surfaces · **Proposed, not selected or approved**
Basis: canonical `feat/meridian-implementation`, inspected at `18737b0`.

## Intent and recovered request

The owner asked to finish the failed Superpowers design-and-planning request in
“Identify Allocated Spend Pocket” (task `01a0d99e-5ed2-7c93-b4ad-347f0a3dddbd`).
The request is to reproduce Crew's useful Plan Reserve journey with Meridian's
visual language, and consider parallel DeepSeek Harness execution where possible.
The authentication error interrupted that request; repairing authentication is not
this assignment. The screenshot is evidence, not authority for unrelated actions.

Success: the owner can see when reserve cash is expected to arrive and leave,
expand a grouped obligation, understand the running balance and first shortfall,
and separately inspect Crew's dated current allocation. No new financial authority.
The explicit current request authorizes preparation of both design and draft plan;
it does not select a visual option, approve implementation, or launch agents.

This advances concepts 2 (projections), 3 (provenance/uncertainty), and 21 (proposed
UI evolution). It does not implement a new forecasting engine or an autonomous CFO.
OS-116 is already in the ledger and roadmap addendum. The owner's current planning
request addresses it without replacing the roadmap's remaining Track D, Track I,
and funding-measurement priorities with an implementation assignment.

## Authority and evidence

- `AGENTS.md`, `PROJECT_INSTRUCTIONS.md`, `MERIDIAN_ROADMAP.md`,
  `MERIDIAN_DECISIONS.md`, `MERIDIAN_CONCEPTS.md`, and `MERIDIAN_OS_TASKS.json`
  under `docs/project/` where applicable. Handoff source hashes matched on inspection.
- September 18 Observatory extension governs Timeline vocabulary; September 8
  governs Plan composition and shared language where the extension is silent.
- The recovered session establishes ordered cashflow, repeated dates, expandable
  groups and the distinction from `reservedAmount`. Its financial values are not
  copied into fixtures or design examples.
- **Newer ledger evidence:** OS-130 documents capture and replay of
  `AutopilotReserveProjectionScreen`, including ordered rows/events, opening and
  running balances, low point, first negative and provider horizon. This is stronger
  than OS-116's older “no projection source” assessment. It is recorded evidence,
  not a new provider verification in this planning turn.
- OS-130 remains blocked on OS-059 connector work. A captured query is not an
  installed feed. No local forecast may stand in for a missing Crew projection.
- `meridian/bill_allocation.py` already stores dated allocations; its current read
  helpers require explicit connection/reserve/mode scoping before UI reuse.
- Later current-status records say the injected reserve was unwound; probe bills
  remained. This is historical project evidence, not a fresh live-state check.

## Three visual directions

Images in `design/reserve-timeline-2026-09-26/` are synthetic design studies.
They inherit the inspected September 18 reference, not a newly invented brand.

| Display order | Direction | Strength | Tradeoff |
|---|---|---|---|
| 1 | Observatory Ledger — recommended | Chart followed by the full ordered ledger makes duplicate dates and grouped events legible | More scrolling |
| 2 | Pay-cycle Chapters | Funding-cycle sections make paycheck-to-paycheck planning approachable | Chapter boundaries can obscure cross-cycle obligations; must never infer a cycle from an unverified schedule |
| 3 | Shortfall Lens | First shortfall and selected-event inspector answer “what causes the gap?” quickly | Less neutral when no shortfall exists; needs an equally good no-shortfall state |

The draft implementation plan recommends direction 1, but shares its data contract
with all three. Selection remains the owner's. No study is a screenshot of running
software. Generated text/chart inaccuracies do not override this specification.

### Required corrections to the studies

Use the title **Reserve Timeline**, not a design-direction name. Scope to one
verified reserve and currency; remove the generated “All accounts” control. Keep
all same-day events on their original dates. Plot actual provider row coordinates:
no smoothed line, invented dates, or even spacing that implies elapsed time. Render
zero and negative balances accurately. Internal transfers remain neutral rather
than income-green; decorative moon/sun symbols must not imply day/night. Shrink
oversized header artwork before shrinking body text. All text and chart geometry
are real accessible UI when implemented, never a raster screenshot background.

## Proposed experience

Entry: existing Plan, a Reserve Timeline view; retain the four workspaces and
existing Plan journeys. Two local tabs: **Forecast** and **Current allocation**.

Forecast opens with reserve identity, “Crew estimate”, source age and as-of date.
Then a compact step chart, first-shortfall/low-point summary, and ordered ledger.
Initial display is 30 days; 90/365-day ranges are enabled only within the provider's
reported horizon. Full provider data is retained without client recurrence expansion.
Date range changes never reset the balance: use the preceding provider row as the
range opening point. Label the visible range and full-horizon summary separately.

Each row shows date, event meaning, signed change, projected balance and expansion
control. Repeated dates are legitimate. A multi-event provider row expands into
its original children; mixed bill/transfer rows retain each child's semantic type.
Do not add children and parent amounts twice. Keep provider array order. A group
name identifies contents, not which bill owns the reserve.

Chart selection and ledger selection synchronize. Keyboard users can navigate the
ledger without operating the chart. Provide an equivalent text/table description.
Expanded details show provenance, source time, bill link if its provider identity
resolves, and amount interpretation. Unknown IDs/types remain visible with neutral
labels, never dropped or guessed from English names.

Current allocation is a different read model: one coherent dated capture, scoped
to provider, connection, reserve and actual mode. Show observed bucket total,
per-bill reported reserve, and a separately labelled **Crew next-funding estimate**.
Unknown stays “Not reported”; reported zero is $0.00. Incomplete or mismatched
capture evidence must not claim reconciliation. Historical allocation changes do
not prove a payment, release cause, or universal amount-based priority rule.

### Layout and accessibility

Dark: #172334 canvas, #202b40 surfaces, #eee4cf text, #b7b8cb secondary,
#c1a9e2 lilac, #c6aa71 brass, #e99a48 selected action. Light: warm ivory with dark
ink, independently checked. Reuse bundled Libre Baskerville and Source Sans 3.
16px body, 14px secondary minimum; 44px targets. Quiet dividers, limited nested cards.
Mobile: one column, full-height detail sheet, bottom-dock/safe-area clearance.
Desktop: existing rail, fluid chart/ledger, 320–360px inspector. No fifth workspace.
Disclosure buttons expose aria-expanded/aria-controls; focus returns on close.
Color never carries event type, provenance or shortfall status alone.

## Data architecture and semantics

Read-only connector → snapshot facet → immutable credential-free projection
observation → Reserve Timeline service/API → UI. Reuse the observation store;
add no separate financial ledger or allocation algorithm.

Projection capture carries provider/connection/reserve identity, currency,
snapshot ID, observed time, provider as-of date, mode and payload hash. Preserve
`asOfDate`, `maximumBalance`, `openingBalance`, nullable `lowPoint` and
`firstNegative`, `rows[].{amount,balance,date,events[]}`, and each event's
`amount,name,sourceId,type`. Related next-funding/NSF metadata retain their exact
source location; do not pretend they are children of the projection if they are
siblings in the captured document. Permission metadata never creates a write control.

Known captured types: PAYCHECK, BILL, ALLOCATION. Display as funding, bill and
allocation; say “Pocket transfer” only where captured semantics/identity establish
that meaning. ALLOCATION alone is not proof of a transfer destination.

Use exact decimal-to-minor-unit conversion with verified currency scale; the USD
slice uses integer cents. Null stays null. Reject ambiguous units and unsupported
currencies rather than applying an assumed cents conversion. Arithmetic validates
the provider; it never silently corrects or replaces provider balances:

1. Sum child event amounts = provider row amount.
2. Opening balance + cumulative row amounts = each row balance.
3. Provider low-point/first-negative markers must be consistent with their stated
   scope; opening-negative and null-marker behavior need captured-contract evidence.
4. Preserve nondecreasing row dates and exact same-day order.

Event identity is snapshot ID + row index + event index, since a source bill can
recur. Source IDs are links, not unique occurrence IDs. Fetch/store a complete
observation atomically; never combine the latest row from different captures.

Provenance has separate axes: actual vs simulated input, and observed fact vs
provider estimate vs Meridian projection. An actual capture of a forecast is still
a **Crew estimate**. Current allocations are **Crew reported**. Future local
counterfactuals are **Meridian projection** or **Simulated**, in their own mode;
these controls are not enabled in this first slice.

## Failure, stale and contaminated states

Loading, empty-known, unavailable, partial, stale, invalid, and available are distinct.
Use the existing freshness policy; show source age and last successful observation.
A failed refresh cannot replace a valid older snapshot with zero or “all clear”.
Missing facet is unavailable; an explicitly empty valid feed is empty-known.
Reconciliation failure suppresses reassurance and identifies the discrepancy while
retaining raw provider values for inspection. Conflicting NSF/first-negative fields
are shown as a disagreement, never collapsed into an invented date.

Fixtures live only in synthetic previews/tests. Live probe bills require explicit
provider-ID provenance from a reviewed experiment manifest; never infer by prefix
or silently delete/hide them. A contaminated provider projection is labelled
“Contains test activity — not a clean planning forecast”; do not show coverage
reassurance. A filtered counterfactual, if later requested, must be simulated and
recomputed separately. Do not filter a row out while retaining Crew's old balances.
No bank cleanup or observation-history retention change is part of OS-116.

## Acceptance and scope

Exact-cent synthetic golden case: opening 40000; same-day +100000, -60000
(children -45000 and -15000), -10000; later -90000. Provider balances 140000,
80000, 70000, -20000. First shortfall at the final event. These are invented values.
Tests cover duplicate dates/source IDs, repeated sync, unknown event types, nulls,
negative opening, broken sums, connection isolation, simulated isolation, stale
refresh, range carry-forward, HTML-like names and mismatched allocation captures.

No mutation route, automatic financial recommendation, API-key repair, new billing
experiment, bank cleanup, deployment or background automation. OS-059/OS-130
acceptance must precede production projection availability. The plan's self-review
is not independent financial review; independent review and owner visual selection
remain required before integration/release.
