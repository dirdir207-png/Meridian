# What Crew actually computes (reverse-engineered 2026-09-19)

Owner request: *"see if you can discern the actual calculations used by Crew based on reserve amount and funding rules."*

Source of truth: one read-only snapshot from the sanctioned connector (`crew-readonly snapshot`, `mode: read-only`, `complete: true`, captured `2026-09-19T22:27:32Z`), read against the live `:8081` database. Credentials are handled inside the connector and never surfaced; account/subaccount/reserve identifiers are redacted below to short prefixes. No provider mutation, no write of any kind.

This document records what Crew's own payload says. It is evidence, not a design: the design consequences are in D-015 and OS-056.

## The fields Crew exposes (bill reserve)

Reserve level:

| field | value observed | meaning |
|---|---|---|
| `totalReservedAmount` | `109710` cents = **$1,097.10** | money currently held for this reserve |
| `estimatedNextFundingAmount` | `143597` cents = **$1,435.97** | amount Crew expects to add at the next funding event (**not yet explained** — see below) |
| `nextFundingDate` | `2026-10-02` | the next funding event, derived from the plan (anchor `2026-09-04` + 2 x 14d) |
| `settings.funding.subaccount` | a Checking subaccount | the account the reserve funds from |
| `bills` | 5 | the reserve's bills |
| `fundingPlans` | 1 | `Veterans Home`, amount `166300` ($1,663.00), `anchorDate 2026-09-04`, `frequency WEEKLY`, `frequencyInterval 2` (**this is biweekly**; `crewwork.py:46` maps `("WEEKLY", 2) -> "biweekly"`) |

Per bill (all five, complete field list — bills carry **no** nested objects):

`amount`, `anchorDate`, `autoAdjustAmount`, `dayOfMonth`, `daysOverdue`, `estimatedNextFundingAmount`, `frequency`, `frequencyInterval`, `id`, `name`, `paused`, `reservedAmount`, `reservedBy`, `status`.

The two fields that matter most and that Meridian was discarding:

- **`reservedBy`** — the deadline the reservation is for. Observed values are exactly each bill's next due date: `2026-09-22` (Verizon, day 22), `2026-09-30` (Eversource, Xfinity, day 30), `2026-10-16` (Rent, Verizon Payment Arrangement, day 16 — their `2026-09-16` occurrence is 3 days past, `daysOverdue: 3`). This is Crew's own statement of *"funded by this date"*.
- **`estimatedNextFundingAmount`** — Crew's per-bill, per-funding-event contribution.

## The formula: proven

```
bill.estimatedNextFundingAmount = ceil( bill.amount * 14 / 30.4375 )
```

where `14` is the funding interval in days (`frequencyInterval 2` x `WEEKLY 7`) and `30.4375` is the average month (`365.25 / 12`).

Verified against all five bills, in cents:

| bill | `amount` | Crew `estimatedNextFundingAmount` | `amount * 14 / 30.4375` | ceil | match |
|---|---|---|---|---|---|
| Rent | 144200 | 66327 | 66326.1 | 66327 | yes |
| Verizon Payment Arrangement | 7520 | 3459 | 3458.9 | 3459 | yes |
| Verizon | 10157 | 4672 | 4671.8 | 4672 | yes |
| Eversource | 21000 | 9660 | 9659.1 | 9660 | yes |
| Xfinity | 9300 | 4278 | 4277.6 | 4278 | yes |

The residual is positive on every bill (+0.1 to +0.9 cents), which is why it is a **ceiling**, not a round: rounding to nearest would give Eversource 9659 and Rent 66326. This is a **daily-rate proration of the monthly obligation across the funding interval** — not a division of the reserve balance across bills, and not a per-cycle fixed amount.

Two consequences worth stating plainly:

1. **Crew funds each bill gradually from every funding event.** That is the Simple/Beacon *"fund it by its due date"* mechanic, computed from the bill's own amount and the plan's cadence. The owner's stated intent is what Crew already does.
2. **The rate depends only on `amount`, the interval, and the month length.** It does not depend on how many bills share the reserve or on the reserve balance — so a bill's contribution does not change when another bill is added, which is what an even split of a bucket would do.

## What is *not* explained, stated rather than guessed

- **`totalReservedAmount` ($1,097.10).** It coincides exactly with Rent's `reservedAmount`, and the other four bills read `0`. `109710 / 0.46 = 238500` is exactly `$2,385.00`, but that clean ratio does **not** survive the proven formula (`ceil(238500 * 14 / 30.4375)` = `109694`, sixteen cents short), so it is a coincidence and not the calculation. Possible readings remain open: it is the reserve's *balance* (money actually moved in, which Crew does not break down), or it is an accrual Crew computes from a figure Meridian cannot see.
- **How Crew chooses which bill the balance is earmarked to.** Rent (due `2026-10-16`) holds everything while Eversource and Xfinity (due `2026-09-30`, sooner) hold nothing, so a nearest-due-first waterfall is **refuted**, as is an even split (`109710 / 5 = 21942` cents, not observed) and a proportional split. Rent is first in Crew's `bills` array and is one of the two overdue bills; both facts are candidates, neither is proven.
- **The reserve-level `estimatedNextFundingAmount` ($1,435.97).** Not the sum of the per-bill estimates (`88396` cents = `$883.96`), not the plan amount, and not `10-16`'s bills scaled by the proven formula. It is plausibly "what must arrive at `nextFundingDate` to stay on schedule", which would make it directly useful — but that is a hypothesis.

## The decisive next observation (free, no new tooling)

`nextFundingDate` is **`2026-10-02`**. When that event passes, three of the open questions become measurable from data Meridian already persists every 15 seconds:

1. watch `crew_bill_reserves.total_reserved_amount` before/after the event — the delta tests the `$1,435.97` hypothesis directly;
2. watch whether the four `0` bills move off zero, which tests the earmarking rule;
3. watch `commitments.funded_amount` per bill, which tests whether contributions accrue per event as the proven formula implies.

No code change is needed to run this; `crew_bill_reserves` and `commitments` are already updated on every refresh. Until `2026-10-02` there is a single observation point, and one point cannot separate the surviving hypotheses.

## Method note

The connector's own CLI hung once when invoked while the app's 15-second refresh was also calling it (a foreground call exceeded the shell limit). Running it detached, with output to a file, returned in seconds. Reproduce with:

```
/Users/stephenwest/Applications/CrewWorkAssistantOTP/.venv/bin/crew-readonly snapshot > /tmp/crew-snapshot.out
```

and read only the fields you need — the payload is the owner's real financial data and must not be pasted around wholesale.
