# Payday and funding are one mechanism, described twice — findings and proposed correction (OS-104)

**Status: findings verified against the source; the correction is PROPOSED and not implemented.** The parts
that are pure consolidation follow the owner's own instruction ("doesn't need a separate setting or section");
the part that needs his decision is named in §5.

Owner, 2026-09-24, verbatim: *"payday and funding is unnecessarily complex and suggests overlap, payday is the
funding mechanism, so the payday and when it lands is the cadence, this isn't consistent. It still says no
cadence detected in places. Funding the way the app describes separate from payday is per bill and doesn't need
a separate setting or section."* Then, with a screenshot of Crew's own **Edit paycheck** screen (Cancel / Edit
paycheck / Delete — FREQUENCY `Every two weeks`, DAY `Every other Friday`, Identification: *"Deposits matching
these conditions will fund your Autopilot plan"* — CONTAINS `STATE OF NEW HAM PR PAYMENT`, TRANSACTION AMOUNT
`Minimum $1,500.00`, DATE `Within 5 days before or after the expected date`, PAST MATCHING ACTIVITY, Save):
*"Crew has 5 sections. We have all the machinery for bidirectionality."*

Every one of those claims checks out. The record already says the same thing; the screen the owner reads does not.

---

## 1. The app's own precedence rule already agrees with him

`meridian/api.py:515-535`, `_paycheck_config`, verbatim:

> "The Crew funding plan now outranks every leg above it, per the owner's directive that the paycheck **SHOULD be
> a crew record**. The stored plans are read from Meridian's own database -- never fetched here -- so a read path
> stays free of provider calls, and only a plan the sync actually observed can claim to be the income source."

`meridian/providers/base.py:79-92`, `FundingPlanCandidate`, verbatim: *"The plan is the record the owner calls
their 'income source' / 'Funding Cadence' (confirmed 2026-09-19)."*

So the backend's answer to "what is the cadence?" is **Crew's paycheck record, first**, and it has been since
2026-09-19. The Settings screen gives a different answer.

## 2. The four defects, each with its evidence

**(a) The Cadence card uses the weaker source, so it can say "Not recognized" while the same payload carries the
authoritative cadence.** `meridian/services/payday.py:87` builds `pattern` from `recognize_payday(transactions…)`
— the *learned income pattern* — while `funding_plans` (Crew's records, lines 63-83) is built separately and
handed over in the same payload. `static/js/meridian/payday.js:54-64` then renders the summary from `pattern`
alone: `"Not recognized"`, `"Add or confirm your payday timing"`, `"Income unavailable"`, `"No run projected"`.
The Crew plans are rendered by a different function further down the same page, each printing its own
`Crew cadence: …` (payday.js:209-212). **Two cadences, one screen, and the summary is the one that does not
consult Crew.** That is the owner's "this isn't consistent / it still says no cadence detected in places".

**(b) The instruction is unactionable — there is no write path for a payday at all.** `payday.js:60` tells the
owner to *"Add or confirm your payday timing"*. `/settings/payday` is GET-only (`api.py:1200`) and the only POST
in the pane sets the *learning floor* (`api.py:1220`). A repository-wide search for a payday/pattern write
(`set_payday`, `confirm_payday`, `payday_pattern`, `income_pattern`) returns **nothing**, and the pane contains
no payday input — its two editors write a funding rule and a learning floor. The screen asks for an action the
product cannot perform.

**(c) One object, two editors, and the Settings one is the subset.** Plan already ships the per-commitment
funding-rule editor with **four** modes — fixed per paycheck, percent of paycheck, calendar cadence, even by due
date — proposing through `/api/meridian/funding-rules/propose`
(`templates/meridian/partials/plan.html:345-369`, `static/js/meridian/plan.js:1199`). Settings ships a second
editor for the same record with **two** modes and a commitment picker
(`templates/meridian/partials/payday-funding.html:38-55`, `payday.js:116-135`, same endpoint). Backed by one
repository (`meridian/funding_repo.py`). So "Funding" is a settings section that duplicates a Plan capability
and offers less of it — exactly the owner's "per bill and doesn't need a separate setting or section".

**(d) Funding is named twice in the hub.** `meridian/settings_hub.py:142` ("Funding schedules", detail "Manage in
Plan", a pointer) and `:171` ("Payday & funding", detail "Your payday rhythm and what Meridian funds", the pane).
Both rows are deliberate and documented; together they present funding as two subjects.

## 3. "We have all the machinery for bidirectionality" — verified, and here is its exact extent

`meridian/crew_write_actions.py:674-684` already registers, with readback verifiers:

| action | executor | verification |
|---|---|---|
| `create_crew_paycheck_funding_plan` | `create_paycheck_funding_plan` | `_verify_crew_funding_plan(expect_created=True)` |
| `update_crew_paycheck_funding_plan` | `update_paycheck_funding_plan` | `_verify_crew_funding_plan(...)` |
| `delete_crew_paycheck_funding_plan` | `delete_paycheck_funding_plan` | `_verify_crew_funding_plan(expect_absent=True)` |

So Meridian can already **create, change and delete Crew's funding plan with a readback gate** — the owner is
right. What it does *not* cover is the rest of the paycheck his screenshot shows: **FREQUENCY**, **DAY**,
**IDENTIFICATION** (matching conditions) and the **DATE** window. Today Meridian ingests only part of that
record (`FundingPlanCandidate`: `external_id`, `name`, `amount`, `bill_reserve_id`, `cadence`,
`estimated_next_funding_amount`, `reserved_by`), and `cadence` is documented as `None` whenever Crew's
frequency/interval "cannot be expressed exactly" — never coerced.

## 4. The proposed correction (bounded, and the part that follows directly from his instruction)

Presentation and derivation only. **No change to which mechanism funds anything, no change to the action
pipeline, no change to any provider call, no new write capability.**

1. **One cadence, one card, with its source named.** The summary's Cadence card resolves in the *backend's own
   precedence*: Crew's paycheck record first (naming it: "Crew paycheck · Every two weeks"), then the observed
   pattern ("Learned · 12 deposits"), then nothing — and it never says "Not recognized" while a Crew cadence is
   present in the same payload. The plan rows stop printing a second `Crew cadence:` line.
2. **The per-bill funding editor leaves Settings.** Plan keeps the four-mode editor it already has; the
   Settings pane keeps the payday summary, Crew's paycheck records, and the learning floor. "Funding" stops
   being a settings section, per his instruction.
3. **One unavailable phrase per fact.** "Not recognized" / "Income unavailable" / "No run projected" /
   "not reported" / "no payday cadence to set" are five phrasings of two facts; they become two, each used once.
4. **The dead-end instruction is replaced by one that is true**: it names where the paycheck actually lives
   (Crew) and what Meridian does with it, instead of asking for a control that does not exist.

## 5. What needs the owner's decision

The one thing the correction above cannot decide by itself: **where FREQUENCY, DAY and IDENTIFICATION are
edited.**

- **(A) Crew owns them; Meridian reads.** Meridian's Cadence card states the Crew cadence and points at Crew for
  changing it. No new authority, no new commands, ships immediately — and matches Crew's screen, which already
  has all five sections.
- **(B) Meridian grows the write commands** for frequency/day/identification, on the same pattern as the
  funding-plan actions (deterministic owner-stated values, proposal or direct per the write model, readback
  verification, never auto-retried). This is a *new capability*, so it needs his explicit authorisation and its
  own bounded slice with its own safety analysis; "all the machinery" makes it plumbing rather than invention,
  but the authority boundary still moves and must move deliberately.
- **(C) Both**: read now, write later.

## 6. Non-goals

Nothing here removes a mechanism, changes a proposal, retires the local funding rule's effect, alters
`FundingRule`/`funding_repo`/the propose route, touches migration state, or changes what any action does when
executed. The per-bill rule keeps working exactly as it does today; it simply stops being presented as a second
settings subject.
