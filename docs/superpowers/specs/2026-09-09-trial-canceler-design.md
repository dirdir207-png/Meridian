# Trial & Subscription Canceler — Design

**Date:** 2026-09-09
**Status:** Design for review
**Home:** ORSC Meridian lane (`feat/meridian-implementation`)
**Scope:** Personal use, single user, United States
**Working name:** Meridian Sentinel (`meridian/trials/` + `meridian/cancellation/`)

---

## 1. Problem

Free trials convert silently. The consumer signs up intending to evaluate, the trial
ends on a date nobody recorded, and a charge appears. The tool's job is to make that
outcome structurally impossible or, failing that, to detect it, act on it inside the
deadline, and prove what happened.

### 1.1 Evidence quality — read this before quoting any number

The commonly cited figure — *48% of Americans have forgotten to cancel a free trial
and been charged* — comes from an affiliate comparison site that earns commissions on
streaming and ISP links. Subscription-infrastructure vendors publish the trial-conversion
numbers, and those vendors profit when trials look convertible. **There is no neutral,
government-published U.S. statistic for free-trial conversion or forgetting-to-cancel
rates.** This design therefore does not rely on any such figure for its justification,
and the product must not cite one as established fact.

What *is* documented from primary and enforcement sources:

- The FTC received **>100,000 negative-option complaints over five years** when it opened
  its March 2026 ANPRM.
- Roughly **30 states** now have their own automatic-renewal laws.
- Enforcement shows repeated billing without informed consent even where a "simple
  mechanism" to cancel is already legally required.

The problem is real and well-attested by enforcement record; the popular statistics are
marketing. Both statements go in the design record.

---

## 2. Goals and non-goals

### Goals

1. **Detect** every trial and recurring subscription, ideally at the moment of signup.
2. **Record the deadline** with the trial's real terms, not an estimate.
3. **Prevent** conversion where possible, without needing the merchant's cooperation.
4. **Cancel** within the window across every channel that can work.
5. **Verify** that billing actually stopped — never report success from a UI click.
6. **Escalate** automatically when a merchant ignores a cancellation.
7. **Hand off** cleanly when a human is genuinely required, with a preparation sheet.

### Non-goals

- Farming new trials for their own sake, or any manufactured-benefit scheme.
- Defeating anti-bot protections where a service's terms forbid automation.
- Impersonating the user on a call without disclosure.
- Commercial multi-tenant operation. This is personal-use software.

---

## 3. The legal reality that shapes the design

> These findings were verified against primary sources during design. This is an
> engineering constraint record, not legal advice.

### 3.1 There is no federal click-to-cancel duty today

| Event | Date | Effect |
|---|---|---|
| 2024 FTC Negative Option Rule | — | Would have imposed a federal click-to-cancel duty |
| *Custom Communications, Inc. v. FTC*, 142 F.4th 1060 (8th Cir.) | 2025-07-08 | Rule **vacated** — failure to issue a preliminary regulatory analysis under 15 U.S.C. § 57b-3(b)(1) |
| FTC final rule recodifying 16 C.F.R. pt. 425 | 2026-02-12 | Reverted to the **1973 prenotification text** — covers book/record-club plans, **not** modern auto-renewing subscriptions |
| FTC ANPRM | 2026-03-13 (comments closed 2026-04-13) | No NPRM issued; no new rule in force |

**Consequence:** nothing in federal law obliges a merchant to honor our cancellation.
Leverage comes from ROSCA + FTC Act § 5 + state automatic-renewal laws + card-network
chargebacks. Enforcement capacity under § 5 is real and current (see §3.2).

### 3.2 What actually constrains merchants

- **ROSCA**, 15 U.S.C. § 8403 — requires clear disclosure and a simple mechanism to stop
  recurring charges.
- **FTC Act § 5** — the FTC now pursues the *substance* of the vacated rule as standalone
  deception claims: a **$2.5B Amazon** settlement, **$8.5M Care.com**, **$14M Match Group**,
  **$35M Shutterstock**, and **$150M Adobe** (March 2026) over a cancellation path the DOJ
  described as "unnecessary steps, delays, unsolicited offers, and warnings."
- **State automatic-renewal laws** (~30 states) — several require that a service allowing
  online signup must permit online cancellation, and some require advance renewal notices.
- **State AG action** — e.g. New York's federal ruling against SiriusXM over
  call/chat-only cancellation, and a $600K Equinox settlement.
- **FTC v. LA Fitness** (Aug 2025) — join online, cancel in person or by mail.

### 3.3 The DoNotPay precedent — the honesty rule

The FTC's action against DoNotPay was **not** about automating consumer tasks. It was
about claiming capabilities that could not be substantiated. Order: **$193,000**, a ban
on unsubstantiated substitution-for-services claims, and notice to past subscribers.

**Transferable rule:** *"We send a cancellation request"* and *"we cancelled it"* are
different claims and must be different words in the UI. Every claim that the product
*executes* an action must be substantiated per-provider and per-flow. This rule drives
the status vocabulary in §9.

### 3.4 Limits that are technical, not legal

- **MFA and passkeys.** Where a merchant requires an OTP per login, unattended automation
  needs the second factor too. Where the user has a passkey, the credential is bound to
  their device and biometric — **a server-side agent cannot use it at all**.
- **Device Bound Session Credentials.** Chrome can bind the session cookie to a hardware
  key, so copied or exported cookies are unusable. Cookie-replay automation breaks outright.
- **Bot defences.** Managed detection (Cloudflare JA3/JA4 TLS fingerprinting, reCAPTCHA v3
  scoring, DataDome, HUMAN, Akamai) fingerprints the transport rather than solving a puzzle.
  Automation fails intermittently and unpredictably.
- **Account risk.** Many terms prohibit automated access; violating them can get the
  *user's* account terminated.

**Design consequence, and the core architectural insight:** any cloud-VM agent
(Pine AI, Meta Muse) is structurally blocked by passkeys and DBSC. An extension running
**inside the user's own authenticated browser** is not, because it inherits a session the
user legitimately established. Local-first, in-browser action is not merely a privacy
preference — it is the only durable way to act on hard merchants.

---

## 4. Architecture

### 4.1 Decision change: local-only for v1

The earlier agreed model was a hybrid — a minimal encrypted cloud ledger holding
subscription metadata, with credentials device-held. Tying the canceler into Meridian
removes the need for that cloud component entirely: Meridian already runs locally
(Flask + SQLite) with its own evidence, contract and scheduling subsystems.

**Proposed for approval:** v1 is **local-only**. No cloud service, no account, no
off-device metadata. The only outbound traffic is to mail providers, optionally Plaid,
and the merchants themselves. Off-device notification (so an alert reaches the user when
the Mac is asleep) is the single feature that would reintroduce a cloud dependency, and
it can be deferred or satisfied by push to a phone via an existing relay.

This strictly improves the privacy posture and removes an entire security surface.

### 4.2 Components

| Component | Role | New or reused |
|---|---|---|
| **Meridian app** (Flask/SQLite) | Domain, ledger, scheduling, evidence, actions, UI | Reused, extended |
| `meridian/trials/` | Trial/subscription records, terms, deadline engine, escalation ladder | **New** |
| `meridian/cancellation/` | Recipe catalog, channel ladder, action→verify→escalate machine, brief generator | **New** |
| `meridian/cancellation/recipes/` | Per-service recipe data (YAML/JSON) | **New** |
| **Browser extension** (MV3) | Checkout-term capture, in-session cancellation, card autofill | **New** |
| Local bridge | Extension ↔ Meridian over `127.0.0.1` with a scoped token | **New** |
| Crew virtual cards | Prevention: scoped card that cannot convert | Reused |
| Gmail/Graph intake | Detection from receipts | Reused |
| Plaid / CSV | Detection from transactions; **verification ground truth** | Reused / new |

### 4.3 Existing Meridian seams (verified in this branch)

| Capability | Location |
|---|---|
| Virtual-card create command | `meridian/crew_commands.py:137`, payload builder `:235` |
| Card executor registered | `meridian/crew_write_actions.py:109` |
| Direct-vs-propose routing gate | `meridian/write_routing.py:64` (`classify_action`), `:137` (`route_mutation`) |
| Evidence ledger (hashes, typed links) | `meridian/evidence.py:43` |
| Contracts, obligations, advisory boundary | `meridian/contracts.py:62` |
| Deadline math, merchant matching | `meridian/billers.py:61` (`_next_due`) |
| Gmail + iCloud ingestion | `meridian/gmail_intake.py:27`, `:205` |
| Action store / executors | `meridian/crew_write_actions.py`, `meridian/crew_write.py` |
| Route registration + allowlist | `app.py:1015-1017` |

Before writing new plumbing, prefer extending these. The canceler is mostly a **new domain
composed from existing subsystems**, plus one genuinely new component (the extension).

---

## 5. Domain model

```
Service (canonical merchant, e.g. "Adobe")
  └─ Subscription          one enrollment; status: trial | active | canceled | unknown
       ├─ Terms            trial_days, price_after, cadence, cancel_notice_period,
       │                   source_of_truth: checkout_capture | receipt | inferred
       ├─ Deadline[]       trial_end | promo_end | price_increase | contract_end
       │                     each: due_at, confidence, derived_from
       ├─ ConsentPolicy    autonomy tier, allowlist state, spend cap
       ├─ Action[]         attempt: channel, started_at, outcome, artifacts
       ├─ Verification[]   billing_stopped_evidence, checked_at, method
       └─ Dispute[]        refund request, chargeback, regulator complaint
```

**Deadline engine.** Each subscription may carry several distinct deadlines. The engine
computes `cancel_by = deadline − buffer`, in the owner's timezone, and schedules an
escalation ladder at T−7, T−3, T−1 and morning-of. Buffers are per-service (some require
notice periods; some are business-hours-only). A single missed notification must never be
the difference between a cancellation and a charge.

**Terms provenance is explicit.** A term captured from the checkout page outranks a term
inferred from a receipt, which outranks a default assumption. Confidence propagates into
the routing decision in §8, because an inferred 7-day trial is exactly the situation where
we must ask rather than act.

---

## 6. Detection

### 6.1 Ranked sources

1. **Checkout-page capture (extension)** — authoritative. Trial length, price after,
   renewal cadence and the consent checkbox captured at the moment of signup. This is the
   only source that knows the terms with certainty and the only one that works for trials
   that send no email at all.
2. **Email receipts** — trial-start confirmations, renewal receipts, price-increase
   notices. Meridian already ingests Gmail and iCloud.
3. **Transaction feeds** — Plaid or CSV/OFX import. Catches zombie subscriptions and
   price creep, and is the **verification ground truth** in §9.
4. **Manual add** — always available; never the only option.

### 6.2 Mail integration — verified constraints

- **Gmail:** `gmail.readonly` is a **Restricted** scope; full verification requires an
  annual CASA security assessment (assessor-priced, no published Google price list,
  ~6-week review). Critically, an OAuth app left in **Testing** status gets **7-day
  refresh tokens** — an unattended monitor would die weekly — plus a lifetime
  **100-test-user cap that cannot be reset**.
  **Recommended primary path: Gmail IMAP (`imap.gmail.com:993`) with a 16-character app
  password.** It requires 2SV on the account and is revoked on password change, but it
  bypasses OAuth verification, CASA and the 7-day token expiry entirely. If OAuth is
  preferred, publish **In production unverified**: Google's own policy exempts personal-use
  apps under 100 users, which also avoids CASA.
- **Microsoft Graph:** `Mail.Read` and `Mail.Send` are available for **personal** Microsoft
  accounts with **no admin consent and no review gate** at all. Throttling per mailbox:
  10,000 requests/10 min, 4 concurrent. Outlook.com IMAP now uses Modern Auth, so use
  Graph `/messages/delta` rather than IMAP.
- **Plaid:** personal use is explicitly supported — the free **Trial plan** provides live
  data for **10 Items** and is described as appropriate for hobbyist use (Limited
  Production is deprecated). One Item per institution means multiple banks can be linked
  within the cap. `POST /transactions/recurring/get` returns `outflow_streams[]` with
  merchant, frequency, average amount and `predicted_next_date`. Recurring detection must
  be enabled **at Link time** (180+ days of history recommended).
- **Apple, Google Play, PayPal, Stripe, Braintree are detection dead ends.** No third party
  can enumerate a consumer's own subscriptions on any of them: StoreKit 2 and the App Store
  Server API are scoped to *your own* app, Play `subscriptionsv2` needs the merchant's own
  service account, and every payment provider's API is merchant-scoped. These surfaces can
  only be **linked out to**, never read.
  macOS gotcha: `AppStore.showManageSubscriptions(in:)` is **unsupported on macOS**, and
  Apple documents no `itms-apps://` subscription URL — treat deep links as best-effort.

---

## 7. Prevention — the strongest lane

Prevention outranks cancellation: a card that cannot be charged needs no merchant
cooperation, no click path, and no legal leverage.

### 7.1 Cancel-on-signup (default ON, with allowlist)

Most trials permit cancelling immediately and retain access for the full trial period.
Where that holds, cancelling at signup reduces the trial to a state that **cannot convert**.
This is the single highest-reliability play in the product.

Default policy, approved: **on for every trial matching the owner's rules, with an
allowlist of services the owner intends to keep.** The allowlist is checked before any
automatic cancel. Cancel-on-signup is *never* applied to allowlisted services, and the
extension confirms on the checkout page at first encounter with any new service.

### 7.2 Scoped virtual cards (Crew)

Meridian can already issue virtual cards; the payload builder at `crew_commands.py:235`
includes `monthlyLimit` and `cancelAfter`, and `GenerateViewSadToken{debitCardId}` — the
primitive needed to reveal card details for autofill — is present in the verified catalog.

Intended flow: at checkout, mint a card scoped to that merchant with a spend limit that
permits the trial's $0–$1 authorization but not the post-trial price, and `cancelAfter`
set before the conversion date; autofill it into the checkout form.

### 7.3 The card-updater trap — read carefully

**Visa Account Updater and Mastercard Automatic Billing Updater exist precisely to keep
card-on-file credentials current.** Replacing a card, letting it expire, or virtualising it
often does **not** stop the subscription: the issuer pushes the new number to the merchant
and billing continues. Merchant-locked and spend-capped cards therefore buy **a decline,
not a cancellation**.

The distinction that matters, and the reason this lane is still worth building:

| Scenario | Updater behaviour | Outcome |
|---|---|---|
| Card replaced / reissued after loss | New number pushed to merchant | **Billing continues** |
| Card merely expired | Merchant enrolled in ABU receives updated expiry | **Billing continues** |
| Card **closed with no successor**, unsolicited by the merchant | No successor number exists to push | **Charge declines** |

A scheduled self-close with no successor is the good primitive. **Open verification item
(§14, V1):** whether Crew's `cancelAfter` self-closes the card with no successor — or
silently reissues. If it reissues, this lane is downgraded to a *deterrent* and the
cancellation lane carries the load. The prevention lane is therefore built behind a
**contract adapter** so the verified contract and its semantics can slot in as a
one-file change.

### 7.4 Fallbacks that remain useful

- **Downgrade to a free tier** instead of cancelling.
- **Scheduled card freeze** where the issuer supports it.
- **Cancellation Brief + deadline alarm** — the human path, always available (§10).

---

## 8. Consent, autonomy and routing

Meridian already implements the right gate. `write_routing.py` splits actions by
**provenance and determinism**, with `_under_specified`, `_flags_low_confidence` and
`_flags_multi_op` feeding a `RoutingDecision`. The canceler extends that model rather than
inventing a parallel one.

| Tier | Trigger | Behaviour |
|---|---|---|
| **Direct** | Allowlisted rule, known recipe, deterministic, unambiguous | Execute, record, notify |
| **Propose → approve** | New merchant, unclear terms, low detection confidence, multiple interacting actions, novel recipe | Present a proposal with the evidence; act only on approval |
| **Autonomous (opt-in)** | Owner pre-authorizes a class of action | Execute within allowlist, spend cap, and dry-run; kill switch always live |

Hard guardrails, regardless of tier:

- **Never auto-cancel essentials** — utilities, insurance, medical, loan servicing,
  government payments — without per-service confirmation.
- **Never auto-cancel an allowlisted service.**
- **High-risk channels always re-prompt**, even in autonomous mode.
- **Every action is evidenced** before it is considered complete.
- **A global kill switch** stops all scheduled activity immediately.

---

## 9. Action → Verify → Escalate

Attempting a cancellation is not confirming one. Two documented traps make this mandatory:

1. **Retention flows.** The first "Cancel" click often yields a pause, a downgrade or a
   discount. An agent that clicks once and reports success is wrong. Apple has formally
   supported retention offers at cancellation since July 2025.
2. **Silent continuation.** Merchants continue billing after receiving cancellations.
   Email has no reliable proof of receipt.

### State machine

```
Planned → Attempted → AwaitingAck → Verified  (billing demonstrably stopped)
                      ↘ Unverified → Escalated (next channel / dispute)
```

### Verification signals, weakest to strongest

1. Merchant account page reflects "cancelled / no active subscription" (extension re-read).
2. A cancellation confirmation with a reference ID is captured.
3. **No charge appears on the card or bank feed past the renewal date** — Meridian's own
   reconciliation is the ground truth, and it is the only signal that generalizes to
   every merchant.
4. For the prevention lane: the scoped card declines and the card is confirmed closed
   with no successor.

**Status vocabulary is deliberate, following §3.3:** *Requested*, *Acknowledged*,
*Billing stopped*, *Unverified*, *Failed — needs you*. The UI must never print "Cancelled"
on the strength of a click.

---

## 10. The Cancellation Brief (human hand-off)

One of the original requirements: when the machine cannot finish, hand the owner a sheet
rather than a failure. Generated per subscription and per deadline:

- Service, account identifier used, and plan/trial name.
- The exact deadline, with buffer and timezone, and days remaining.
- **Channel ladder** with the recommended route first.
- **Credential sheet** — which credential is needed, from which of the three lanes (§11),
  never printed into logs or evidence.
- **Call script** for phone-only providers: what to say, what to refuse (pause/downgrade),
  the disclosure line if a voice agent is used, and the recording-consent note for
  all-party-consent states.
- **Evidence checklist** — the confirmation number, screenshot or email to capture.
- A **done** control that files the artifact into the evidence ledger.

Output as an on-screen task, an exportable PDF, and a phone-readable summary.

---

## 11. Credentials and secrets

Extension-first removes most credential handling, which is the point.

| Lane | When used | Storage |
|---|---|---|
| **1. Live browser session** | Default. The extension acts inside the user's authenticated session. | Nothing stored |
| **2. Device-held vault / Keychain** | Unattended runs needing a login; 1Password/Bitwarden CLI or macOS Keychain. | Device only |
| **3. Short-lived delegated token** | Rare; scoped to one service, one action, one window. | Revocable, expiring |

Never: server-side plaintext, escrowed master keys, credentials in logs, credentials in
evidence artifacts, or credentials in the brief's export path.

**Passkey-only services** are explicitly unsupported for unattended automation (§3.4) and
must route to a live-session or human path. The product must say so plainly rather than
failing mysteriously.

---

## 12. Cancellation channels

Each channel carries a verdict. Recipes live in `meridian/cancellation/recipes/` with a
`last_verified` date; an unverified recipe degrades to the human path rather than guessing.

| # | Channel | Automation | Main risk |
|---|---|---|---|
| 1 | Official API / account settings in live session | Full | Recipe drift |
| 2 | Browser automation, human-confirm before submit | Full with approval | Bot defences; ToS |
| 3 | Email cancellation notice + ack tracking | Partial | Delivery ≠ cancellation |
| 4 | Certified mail (Lob/PostGrid) | Semi | Cost; slow; still no guarantee |
| 5 | Support chat | Assisted | Anti-bot; retention loops |
| 6 | Voice agent / call script | Assisted | Recording-consent law; disclosure |
| 7 | Payment hub (Apple/Google/PayPal/Roku/carrier) | Guided only | Cannot be read or driven (§6.2) |
| 8 | Pause / downgrade | Full | Reduces harm without ending billing |
| 9 | Card/ACH block | Emergency only | Does not cancel; updater may defeat it |
| 10 | Refund → chargeback → regulator | Escalation | Time limits; evidence quality |

Channel mechanics and pricing are detailed in the accompanying research notes
(`docs/research/`), which carry their own citations and dates.

---

## 13. Evidence, dispute and escalation

The evidence ledger already exists (`evidence.py`): content hashes and typed links. Every
action writes: what was attempted, when, through which channel, with what artifact, and
what the merchant said.

Escalation ladder when verification fails:

1. Second notice, citing the operative **state automatic-renewal statute** for the owner's
   state and restating the revocation.
2. Certified mail with proof of delivery.
3. **Dispute packet** — assembled automatically from the ledger: cancellation record,
   acknowledgement (or documented absence), charge record, statutory citation. Supports a
   card chargeback and, for bank debits, an **EFTA / Regulation E** revocation of
   authorization to the bank.
4. Regulator complaint (state AG / FTC / CFPB) as a generated draft.

Note the boundary: the product **prepares** disputes and complaints. It does not act as a
lawyer, does not promise outcomes, and does not claim to sue on anyone's behalf — the
exact line the DoNotPay order drew.

This is also why prevention matters more than ever: with no federal duty to honor our
cancellation, the escalation ladder is the only backstop, and a card that cannot be
charged skips the entire fight.

---

## 14. Phases

| Phase | Content | Exit criterion |
|---|---|---|
| **0** | Slot in the captured `CreateVirtualDebitCard` contract behind the adapter; verify `cancelAfter`/`monthlyLimit`/single-use semantics | Contract verified against live traffic; semantics documented |
| **1** | Extension checkout capture; trial ledger; deadline engine; escalation notifications; Cancellation Brief; `docs/research/` decisions implemented for mail intake | A trial signed up in the browser appears in Meridian with the correct deadline and alerts before conversion |
| **2** | Cancel-on-signup for allowlist-exempt services; live-session cancellation via recipes; action→verify→escalate; evidence capture | A real trial is cancelled at signup and verified by the absence of a charge |
| **3** | Email/certified mail; chat assistance; voice script; payment-hub guidance; Plaid/CSV detection and verification | A non-recipe merchant is handled end-to-end with evidence |
| **4** | Scoped virtual cards in the prevention lane; pre-authorized autonomy; retention-offer capture; dispute packet generation | A trial converts to a decline with zero merchant cooperation |

Phase 0 is unblocked as soon as the mutation is captured — expected imminently, which is
why the prevention lane is no longer deferred to the end.

### Open verification items

| ID | Item | Blocks |
|---|---|---|
| **V1** | Does `cancelAfter` self-close with no successor, or reissue the card? | Phase 4 viability |
| **V2** | Does `CreateVirtualDebitCard` accept `monthlyLimit`, `cancelAfter`, and a single-use type? | Phase 0 / 4 |
| **V3** | Does `GenerateViewSadToken` return a full PAN/CVV suitable for autofill? | Checkout autofill |
| **V4** | Which mail path: Gmail IMAP + app password, or OAuth published-unverified? | Phase 1 |
| **V5** | Is Plaid's recurring stream available within the free Trial plan's 10-Item cap? | Phase 3 |

---

## 15. Testing

- **Unit:** deadline engine (timezones, buffers, business-hours rules, DST boundaries),
  recipe matching, routing tier selection, verification-signal precedence.
- **Contract:** the virtual-card adapter against a recorded fixture, so the unverified
  contract cannot silently drift once captured.
- **Integration:** extension ↔ local bridge against a running Meridian instance; mail
  ingestion against recorded fixtures rather than live mailboxes.
- **End-to-end replay:** recorded checkout → capture → deadline → cancel → verify, with the
  merchant stubbed, asserting the state machine never reports *Billing stopped* without a
  positive verification signal.

**Environment note (real constraint in this repo):** `python3` resolves to the 3.9 Command
Line Tools interpreter, which cannot run this codebase. Tests and lint run through:

```
~/.local/bin/uv run --python 3.11 --with-requirements requirements.txt --with pytest \
  python -m pytest ...
~/.local/bin/uv run --python 3.11 --with-requirements requirements.txt ruff check ...
```

`tests/meridian/test_live.py` fails under the uv isolate because it cannot see the system
`crew-readonly` binary — environmental, not a code defect.

---

## 16. Risks

| Risk | Mitigation |
|---|---|
| Recipe drift breaks a cancellation silently | `last_verified` dates; degrade to human path; verification catches failure |
| Merchant ignores cancellation | Evidence ledger + escalation ladder (§13) |
| Retention flow fakes success | Verification requires billing evidence, never UI state (§9) |
| Card updater defeats the prevention lane | Verify V1; adapter isolates the contract; cancellation lane carries load |
| Passkey/MFA merchant | Route to live-session or human path; state the limit plainly |
| ToS violation terminates a user account | Per-service automation policy; respect explicit prohibitions; prefer live-session actions the user could take themselves |
| Overclaiming in the UI | The §3.3 vocabulary rule, enforced in review |
| Credential exposure | Three-lane model (§11); the server never holds secrets; local-only v1 |

### What this product must never promise

- "We cancel any subscription automatically."
- "Give us your bank and merchant passwords."
- "Cancel your card and the charges stop."
- "We'll email them and it's handled."
- "Guaranteed savings of $X."
- "Set it and forget it — 100% unattended."

The honest claim: **we detect what you signed up for, act on what can be acted on, tell you
exactly what still needs you, and verify the charge actually stopped.**

---

## 17. Appendix — capture checklist for the missing mutation

For the `CreateVirtualDebitCard` capture, the design needs these answered:

1. **Exact input shape.** Field names and types; whether `cancelAfter` and `monthlyLimit`
   are accepted, and their formats (ISO date? epoch? cents?).
2. **Single-use support.** Is there a `type` or flag distinguishing single-use from
   reusable virtual cards? (`crew_commands.py` currently sends `type: "DEBIT"`.)
3. **`cancelAfter` semantics.** Does the card self-close at that time, and **is a successor
   number issued?** This is V1 and it decides whether the prevention lane works at all.
4. **Result fields.** What the mutation returns — the card id needed for a subsequent
   `GenerateViewSadToken`.
5. **Reveal path.** Whether `GenerateViewSadToken{debitCardId}` yields a full PAN/CVV for
   autofill, and whether it is single-use/short-lived.
6. **Limits.** Whether a card may be created with a $0 or $1 authorization ceiling.
7. **Deletion.** Whether a virtual card can be closed or deleted directly, and by what
   mutation.

Capturing these seven answers closes Phase 0 outright.

---

## 18. Sources

Design-time research notes, with per-claim citations and date stamps
(compiled 2026-09-09; every claim verified against first-party documentation):

- `docs/research/legal-landscape.md`
- `docs/research/discovery-integrations.md`
- `docs/research/cancellation-channels.md`
- `docs/research/competitive-and-failure-modes.md`
