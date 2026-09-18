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

## Where Meridian is heading

The broader vision extends beyond a dashboard. These are planned directions, with some supporting work already present; they are not a list of released features.

| Direction | Intended experience |
|---|---|
| **A connected financial picture** | Bring accounts, activity, commitments, supporting documents, and decision history together, with clear sources and uncertainty. |
| **Longer-range planning** | Explore 7-, 30-, 90-, and 365-day projections, changed income or bill timing, and alternative scenarios. |
| **Budgets and payday planning** | Reconcile plans with observed cash, allocate incoming pay across obligations, and explain gaps before they become urgent. |
| **Personal priorities** | Remember the person's financial preferences and boundaries when preparing recommendations. |
| **Early warnings and investigation** | Flag cash pressure, stale connections, unexpected balances, duplicate activity, and other changes worth reviewing. |
| **Household administration** | Follow refunds, subscriptions, renewals, and reimbursements; assemble useful records for negotiations or disputes. |
| **Independent connections** | Support multiple email and calendar accounts with clear permissions, retention choices, and disconnection controls. |
| **Voice and iPhone access** | Make explanations and approved workflows easier to reach through Virgil, beginning with read-only access. |
| **Shared and urgent planning** | Explore household coordination and a focused view of deadlines, resources, and next steps during financial difficulty. |
| **Personalized assistance** | Offer specialized planning and investigation, temporary helpers, and suggested interface improvements with visible controls and review. |

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
