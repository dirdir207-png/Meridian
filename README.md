# Meridian

Meridian is a mobile-first personal financial command center over Crew. It brings current cash, planned obligations, activity, accounts, evidence, and a carefully bounded assistant into one calm Observatory interface.

The repository was previously named SimpleCrew/ORSC. The product direction is now Meridian; the GitHub repository is being renamed to match.

![Meridian Beacon mark](static/images/meridian-avatar.png)

## Product overview

Meridian is built around four financial workspaces and a Settings utility:

- **Today** explains current Safe to Spend, upcoming money moments, forecast freshness, runway, commitments, and Virgil's evidence-linked brief.
- **Plan** models named funding schedules, pay events, bills, goals, reserves, contribution limits, shortfalls, and dated forecasts without double-counting reserved money.
- **Activity** separates Timeline (what happened), Review (what needs a bookkeeping decision), and Patterns (observed trends with evidence). Categories are deterministic when the merchant identity is clear, while mixed or uncertain transactions remain reviewable.
- **Accounts** shows cash, pockets, liabilities, provenance, freshness, net position, and connection health.
- **Settings** is the utility surface for connections, preferences, approval boundaries, memory and privacy, notifications, security, backups, and action history.
- **Virgil** is the consistent evidence-led assistant identity. It can explain, investigate, plan, and draft proposals; voice, iPhone actions, and consequential financial work remain capability-gated and owner-approved.

## Current functionality

The current codebase includes Flask/Jinja and vanilla JavaScript surfaces, a responsive PWA shell, Crew-oriented read models, synthetic Observatory previews, local schedule and bill persistence, funding previews, proposal and approval boundaries, transaction classification and correction history, account/activity reads, connection metadata, read-only evidence connectors, and passkey/session foundations.

The current surface map is:

| Area | Current capability |
|---|---|
| Today | Safe to Spend read model, observed freshness, upcoming money moments, dated runway/forecast views, Beacon briefing, plan links, evidence links, honest unavailable and synthetic-preview states |
| Plan | Named schedules, expected income, recurrence anchors, funding accounts, bill allocations, caps/minima, buffers, due dates, funding coverage, shortfall explanations, local save/read-back, and proposal-only funding changes |
| Activity | Date-grouped Timeline, Review queue, Patterns entry point, account/category filters, transaction detail, source/account labels, confidence and evidence text, correction editor, batch review, protected correction history, and semantic category glyphs |
| Accounts | Cash and pocket grouping, balances and available balances, active/archived account state, provider freshness, connection metadata, reimbursements, liabilities/read-model hooks, and account detail navigation |
| Settings | Reachable utility route, connection and Payday design contracts, appearance/security/retention/action-history concepts, and read-only connection metadata foundations; the complete Observatory Settings composition remains in integration |
| Classification | Deterministic merchant identity rules, owner assignment rules, transfer/refund/reimbursement precedence, recurrence fallback, AI fallback for unresolved rows, confidence thresholding, explanation/provenance, and correction persistence |
| Connections | Provider connection records, freshness and job state, separate Gmail/Calendar read-only connector contracts, OAuth state/callback foundations, scope verification, revocation/read models, and source identity boundaries |
| Safety | Proposal → approval → execution → provider readback vocabulary, constrained executors, uncertain-write handling, no automatic financial retry, synthetic test fixtures, and credential/log redaction rules |
| Virgil | Contextual advisor entry point, evidence-linked briefing language, proposal vocabulary, read-only assistant direction, and a staged client contract; voice and device actions are still gated roadmap work |

Some modules are intentionally substrate-only or wired without a complete user-facing journey. The status labels below are the measured project state, not a claim that every listed capability is release-accepted.

Deterministic classification currently covers 29 categories and 51 curated merchant rules with conservative identity matching. Owner corrections survive provider refreshes. Explicitly unclassified transactions stay in Review and cannot be approved as “Uncategorized.” Category and action icons are semantic SVG assets rather than one reused clock or compass glyph.

Financial authority follows this state machine:

```text
observe → explain/simulate → propose → owner approval → execute once → provider readback
```

No design asset or model response bypasses that boundary.

## Planned functionality

The roadmap continues toward:

- trustworthy 7-, 30-, 90-, and 365-day projections with explicit evidence, age, assumptions, and uncertainty;
- continuously repaired budgets, paycheck landing, scenario simulation, counterfactual learning, and proactive financial weather;
- balance forensics, anomaly investigation, refunds and subscription lifecycle support, reimbursement tracking, and connected biller monitoring;
- multiple independent email and calendar identities with scoped read-only permissions, cursors, revocation, and retention;
- Virgil's staged iPhone path: contracts and threat model, read-only voice, typed device actions, proposal bridge, proactive tasks, then richer native surfaces;
- household/resource planning and bounded autonomous tools only where the owner-approved permission set, lifetime, evidence, and approval boundary are explicit.

Planned means designed or routed in the roadmap. It does not mean deployed or provider-accepted.

## The 22 planned concepts

The roadmap tracks these 22 concepts explicitly so future work cannot disappear into a file listing or be mistaken for a shipped user journey. `built-wired` means code paths are reachable; `built-visible` means a design-system surface exists; `substrate-only` means supporting modules exist without a complete consumer; `built-unwired` means a module exists but no running path currently invokes it; `gated` means the concept is permitted to be designed but still requires an owner-approved permission or authority design; `not-started` means no implementation substrate exists.

| # | Planned concept | What it means in Meridian | Measured state |
|---:|---|---|---|
| 1 | Financial digital twin | A continuously attributable observation graph for accounts, transactions, classifications, commitments, evidence, freshness, and reconciliation. | Built-unwired: observation storage exists, but the complete append/publication path is not continuously consumed. |
| 2 | 7-, 30-, 90-, and 365-day projections | Dated cash and obligation projections with horizon-specific assumptions, coverage, freshness, and confidence. | Built-wired: projection services are reachable; full horizon parity remains unverified. |
| 3 | Explicit confidence, uncertainty, assumptions, and provenance | Every material answer or recommendation carries source, age, confidence, assumptions, and uncertainty instead of presenting inference as fact. | Substrate-only: evidence storage exists; the complete AI role envelope is not yet in place. |
| 4 | Living financial constitution | Versioned owner policies that define priorities, boundaries, safety rules, and acceptable proposals. | Built-unwired: policy substrate exists, but no running product path consults the evaluator. |
| 5 | Policy evaluator | A deterministic gate that checks proposed work against the living constitution before execution or escalation. | Built-unwired: evaluator exists without an active importer in the application or write router. |
| 6 | Specialized financial agents | Separate bounded roles for classification, planning, investigation, reconciliation, and explanation with scoped evidence and permissions. | Substrate-only: classifier/advisor modules exist; role runner and council are not complete. |
| 7 | Single constrained executor | One narrow execution boundary that validates, submits once, records uncertainty, and requires provider readback. | Built-wired: action/executor paths are reachable; completeness across all mutation types remains unproven. |
| 8 | Proactive financial weather and alerts | Quiet, deduplicated warnings about cash pressure, stale connections, upcoming obligations, and meaningful changes. | Built-wired: proactive service exists; lifecycle, dedupe, and delivery channels remain to verify. |
| 9 | Balance forensics and anomaly investigation | Evidence-led investigation of unexpected balances, duplicate activity, missing records, and reconciliation anomalies. | Substrate-only: evidence and reconciliation foundations exist without a complete read-only forensics surface. |
| 10 | Continuously repaired budgets | Budgets that reconcile observed cash, reservations, schedules, commitments, and corrections over time. | Built-wired: funding and commitment paths exist; proposal integration and reserve policy remain open. |
| 11 | Paycheck landing workflows | Recognize or manually define income cadence, show the next landing, allocate capacity across upcoming bills, and explain shortfalls. | Built-wired: payday services and routes exist; the dedicated funding page still needs a complete interactive journey. |
| 12 | Scenario simulation and counterfactual learning | Try changed income, timing, contributions, or obligations in an isolated simulation and compare outcomes without mutating actual state. | Built-wired: scenario API is reachable; actual/simulated isolation still needs full acceptance. |
| 13 | Refunds and subscription lifecycle management | Track refunds, renewals, cancellations, recurring charges, retention evidence, and follow-up tasks. | Built-wired: cancellation service and tests exist; visible UI remains partial. |
| 14 | Bureaucracy and negotiation preparation | Assemble evidence, timelines, briefs, escalation plans, and negotiation-ready summaries for household and financial administration. | Built-wired: brief/escalation services are reachable; no complete user-facing surface exists yet. |
| 15 | Household resource planning | Extend the model to shared household resources, responsibilities, consent, and non-financial planning. | Not started: requires a consent and privacy design. |
| 16 | Crisis-command mode | A focused mode for urgent financial situations that compresses evidence, deadlines, cash, obligations, and safe next actions. | Not started: would build on scenario and evidence primitives plus owner policy. |
| 17 | Causal financial memory | Preserve why a decision, correction, assumption, or proposal happened and use that history to explain future recommendations. | Substrate-only: memory action/storage services exist; contextual read integration is incomplete. |
| 18 | Temporary personalized tools | Owner-approved, time-limited tools generated for a specific planning or investigation need with a visible permission diff. | Gated: requires sandboxing, explicit permission set, lifetime, review point, and revocation. |
| 19 | Connector self-diagnosis | Explain stale, revoked, limited, failed, partial, and healthy connections and suggest a safe recovery path. | Built-wired: connection and job services are reachable; failure-mode classification needs full verification. |
| 20 | Sandboxed skill generation | Generate narrowly scoped helper skills that cannot expand authority or escape their approved workspace and lifetime. | Gated: runtime enforcement belongs at the Harness boundary and needs an approved permission model. |
| 21 | Proposed UI evolution | Let Meridian surface evidence-backed interface improvements and experiments without silently changing navigation, permissions, or financial meaning. | Built-visible: concept and partial UI surfaces exist; owner visual acceptance and remaining fidelity gaps are open. |
| 22 | Bounded autonomous CFO behavior | A proactive planning role that can monitor, explain, simulate, recommend, and prepare proposals while every value-moving action remains owner-gated. | Gated: requires an owner-approved authority mandate, permission set, evidence contract, lifetime, and action review design. |

The canonical measured matrix is maintained in [`docs/project/CONCEPT_COVERAGE.md`](docs/project/CONCEPT_COVERAGE.md). The concepts describe the product trajectory; they do not grant financial authority, approve deployment, or imply that an unverified provider capability is available.

## Concept gallery

These are visual concepts and handoff references. They are not screenshots of shipped production behavior. The first seven are the current Observatory composition set; the four dated September 18 concepts extend Activity, Settings, and Virgil.

### Current Observatory concepts

| Surface | Concept |
|---|---|
| Selected direction | ![Selected Observatory direction](design/observatory-drafts-2026-09-08/00-selected-direction.png) |
| Today | ![Today concept](design/observatory-drafts-2026-09-08/01-today.png) |
| Plan | ![Plan concept](design/observatory-drafts-2026-09-08/02-plan.png) |
| Activity | ![Activity concept](design/observatory-drafts-2026-09-08/03-activity.png) |
| Accounts | ![Accounts concept](design/observatory-drafts-2026-09-08/04-accounts.png) |
| Settings | ![Settings concept](design/observatory-drafts-2026-09-08/05-settings.png) |
| Interactive observatory | ![Interactive observatory concept](design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png) |

### September 18 extension concepts

| Surface | Concept |
|---|---|
| Timeline | ![Timeline concept](design/observatory-extension-2026-09-18/concepts/timeline.png) |
| Review | ![Review concept](design/observatory-extension-2026-09-18/concepts/review.png) |
| Settings refresh | ![Settings refresh concept](design/observatory-extension-2026-09-18/concepts/settings.png) |
| Virgil refresh | ![Virgil concept](design/observatory-extension-2026-09-18/concepts/virgil.png) |

The complete implementation handoff, icon map, prompt set, deep-orange token proposal, and licensed SVG specimen are in [`design/observatory-extension-2026-09-18/`](design/observatory-extension-2026-09-18/).

## Development

This repository contains the active Meridian implementation, project decisions, measured status, and design records.

Use the pinned Python 3.11 environment for verification:

```bash
.venv311/bin/python -m pytest -q
.venv311/bin/python -m ruff check .
```

The isolated Observatory preview uses synthetic data only:

```bash
.venv311/bin/python scripts/preview_observatory_dial.py
```

Verification uses synthetic fixtures and does not require live financial mutations or provider credentials.

## Status

The concept and deterministic-classification handoff is complete. Production integration, deployment, provider acceptance, and owner-observed mobile acceptance remain separate project stages.

## License

MIT. See [`LICENSE`](LICENSE).
