<p align="center">
  <img src="static/img/meridian/observatory/kit-2026-09-16/observatory-landscape.png" alt="Meridian Observatory — a brass-toned engraved observatory on a wooded hill" width="280">
</p>

<h1 align="center">Meridian</h1>
<p align="center"><strong>A clearer view of your money, and what comes next.</strong></p>

Meridian is a mobile-first personal finance project built around Crew Banking. It brings cash, bills, spending, savings, and financial planning into one place, with enough context to understand both today's position and the choices ahead.

Originally developed from SimpleCrew, Meridian now has its own Observatory design: midnight blue, warm parchment, brass details, engraved illustrations, and instrument-inspired views of time and money.

**Status: active development.** The repository contains working features alongside unfinished integrations and planned experiences. The images below are design concepts, not evidence of a finished or publicly released product.

## Explore Meridian

| Workspace | What it helps you understand |
|---|---|
| **Today** | What is available to spend, which obligations are coming up, and how recent the supporting information is. |
| **Plan** | How expected income, bills, savings goals, and reserves fit together over time—and where a shortfall may occur. |
| **Activity** | What happened in the Timeline, what needs a decision in Review, and what spending Patterns may reveal. |
| **Accounts** | How cash, pockets, and liabilities contribute to the overall picture, with account details and connection health. |
| **Settings** | Connections, appearance, privacy, security, and preferences. The complete Observatory settings experience is still being integrated. |

Virgil is Meridian's planned companion for explaining financial information, exploring scenarios, and preparing suggestions. Contextual assistance has foundations in the current project; the fuller voice and iPhone experience remains on the roadmap.

## An interactive view of what comes next

The Observatory dial is a way to explore time, not just a balance display. Its current controls let you:

- **Tap or drag around the dial** to select a day within the displayed planning horizon.
- **Step backward or forward a day**, or use the date slider for another way to navigate.
- **Select an upcoming event** to bring its date, amount, and funding status into focus.
- **Return to today** to restore the current view.

The pointer, selected date, and event details connect the visual timeline to upcoming bills and income. Exploring the dial changes the view; it does not move money. The intended experience is a natural way to ask, “What comes next, and is it covered?”

These interactions are implemented, but mobile behavior and visual refinements are still being verified. The concept images illustrate the intended experience, including details that may differ from the current build.

## What is in the project today?

The implementation includes a responsive web interface, Crew account and activity views, local bill and funding-schedule storage, funding previews, transaction categorization, and a review workflow for correcting classifications. It also includes connection-status information and foundations for sign-in, passkeys, and read-only email and calendar connections.

These features are at different stages of integration. A module in the repository does not necessarily represent a complete, tested experience in the running application. End-to-end connection setup, the full Settings experience, mobile polish, and verification against provider behavior remain ongoing work.

A few principles shape the experience:

- **Show the source and its age.** An old balance or incomplete connection should be recognizable as such.
- **Keep forecasts distinct from cash.** Projections depend on assumptions; they are not current balances.
- **Make corrections durable.** Reviewing a transaction should improve the record without losing the person's decision on the next refresh.
- **Keep financial decisions with the person.** Proposed money movements require explicit approval, with their outcome checked afterward.

## Roadmap: future features

These 22 concepts describe Meridian's intended future feature set. **They are future features, not claims of current availability.** Some have early supporting code, but the complete experiences remain ahead. Each concept is listed individually so the full ambition of the project stays visible.

| # | Future feature | What it would offer |
|---:|---|---|
| 1 | **Financial digital twin** | An evolving model of your financial life, connecting accounts, transactions, bills, plans, and supporting records. |
| 2 | **7-, 30-, 90-, and 365-day projections** | Views of where cash and obligations may stand across different time horizons, with the assumptions behind each forecast. |
| 3 | **Explicit confidence, uncertainty, assumptions, and provenance** | Clear explanations of what is known, what is estimated, how certain a conclusion is, and where its evidence came from. |
| 4 | **Living financial constitution** | A personal, revisable set of financial priorities, preferences, and boundaries that guides recommendations. |
| 5 | **Policy evaluator** | Checks that proposed actions fit those priorities and boundaries, with understandable reasons when something does not. |
| 6 | **Specialized financial agents** | Focused assistants for planning, classification, investigation, reconciliation, and explanation, each with a defined role and limited permissions. |
| 7 | **A single constrained executor** | One controlled path for carrying out approved financial actions, recording the result and checking it with the provider. |
| 8 | **Proactive financial weather and alerts** | Timely warnings about cash pressure, upcoming obligations, stale information, and meaningful changes without constant noise. |
| 9 | **Balance forensics and anomaly investigation** | Help tracing unexpected balances, duplicate activity, missing records, and discrepancies back to their causes. |
| 10 | **Continuously repaired budgets** | Budgets that reconcile with actual cash, reservations, commitments, and corrections, making needed adjustments visible for review. |
| 11 | **Paycheck landing workflows** | A clear plan for incoming pay: what needs funding, what can go toward goals, and where a shortfall remains. |
| 12 | **Scenario simulation and counterfactual learning** | Explore “what if” changes without affecting real accounts, then learn from how earlier choices and assumptions played out. |
| 13 | **Refunds and subscription lifecycle management** | Track expected refunds, recurring charges, renewals, cancellations, and the follow-up needed to resolve them. |
| 14 | **Bureaucracy and negotiation preparation** | Organize evidence, timelines, correspondence, and preparation for disputes, negotiations, and financial administration. |
| 15 | **Household resource planning** | Coordinate shared resources, responsibilities, and plans with explicit consent and privacy boundaries. |
| 16 | **Crisis-command mode** | A focused view of urgent deadlines, available resources, essential obligations, and practical next steps during financial difficulty. |
| 17 | **Causal financial memory** | Remember why a decision or correction was made, so later explanations and recommendations retain that context. |
| 18 | **Temporary personalized tools** | Purpose-built helpers for a particular planning or investigation need, with visible permissions, an expiry, and a way to revoke access. |
| 19 | **Connector self-diagnosis** | Explain why a connection is stale, incomplete, limited, or failing, and identify a useful recovery path. |
| 20 | **Sandboxed skill generation** | Create reusable helpers for recurring tasks inside an isolated environment, with reviewed permissions and controlled access. |
| 21 | **Proposed UI evolution** | Suggest interface improvements based on how the product is used, with changes available for review rather than silently imposed. |
| 22 | **Bounded autonomous CFO behavior** | A proactive financial planning partner that monitors, investigates, simulates, and prepares recommendations within agreed limits; money-moving actions remain subject to explicit approval. |

The wider roadmap also includes multiple independent email and calendar connections, plus Virgil's staged voice and iPhone experience. These are future directions too, not released capabilities or promised delivery dates.

## The Observatory design

The visual direction combines the clarity of a financial workspace with the character of an old observatory: measured, tactile, and calm. The gallery contains illustrative concept data, not live account records.

### Today

<img src="design/observatory-drafts-2026-09-08/01-today.png" alt="Today Observatory design concept" width="420">

<details>
<summary><strong>Explore Plan, Activity, Accounts, and Settings concepts</strong></summary>

### Plan

<img src="design/observatory-drafts-2026-09-08/02-plan.png" alt="Plan Observatory design concept" width="420">

### Activity

<img src="design/observatory-drafts-2026-09-08/03-activity.png" alt="Activity Observatory design concept" width="420">

### Accounts

<img src="design/observatory-drafts-2026-09-08/04-accounts.png" alt="Accounts Observatory design concept" width="420">

### Settings

<img src="design/observatory-drafts-2026-09-08/05-settings.png" alt="Settings Observatory design concept" width="420">

### Interactive Observatory

<img src="design/observatory-drafts-2026-09-08/06-interactive-observatory-vision.png" alt="Interactive Observatory design concept" width="420">

</details>

<details>
<summary><strong>Explore the September 18 design studies</strong></summary>

These later studies explore the Timeline, Review, Settings, and Virgil experiences. They show intended visual direction rather than completed functionality.

### Timeline

<img src="design/observatory-extension-2026-09-18/concepts/timeline.png" alt="Timeline design study" width="420">

### Review

<img src="design/observatory-extension-2026-09-18/concepts/review.png" alt="Review design study" width="420">

### Settings

<img src="design/observatory-extension-2026-09-18/concepts/settings.png" alt="Settings design study" width="420">

### Virgil

<img src="design/observatory-extension-2026-09-18/concepts/virgil.png" alt="Virgil design study" width="420">

</details>

## About the codebase

Meridian uses Python and Flask, server-rendered Jinja templates, vanilla JavaScript, CSS, and SQLite. The repository includes application code, tests using synthetic data, design studies, and development records.

Meridian is an independent project built for use with Crew Banking, not an official Crew product.

## License

Meridian is available under the [MIT License](LICENSE).
