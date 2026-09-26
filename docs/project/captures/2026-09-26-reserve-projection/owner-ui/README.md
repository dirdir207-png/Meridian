# Owner-UI evidence — Crew's "Plan reserve" screen, 2026-09-26

**Why this exists.** The 2026-09-26 projection capture established field names and nesting but recorded its own limit:
*"units: Unresolved by shape alone; must corroborate with provider UI or schema."* These five screenshots are that
corroboration, supplied by the owner. Provider-UI arithmetic is the instrument; nothing here is inferred from a name.

**These are screenshots of the owner's live Crew app and they contain live amounts.** They are internal evidence. They
are **not** part of the Harness handoff, whose do-not-provide list excludes raw financial captures.

| file | sha256 (supplied) | what it shows |
|---|---|---|
| `IMG_1757.jpg` | `03b0eca64ea391c1…` | the list head: badge "Off track", captions "Runs short · Today" and "Current reserve balance", then Sep 26 → Oct 30 |
| `IMG_1758.jpg` | `8996f13d70c0fc79…` | the Oct 16 group sheet: Rent −$1,442.00, Safe to Spend −$552.00, Verizon Payment Arrangement −$75.20 |
| `IMG_1759.jpg` | `bdc79b32599f574c…` | the Oct 30 group sheet: Safe to Spend −$552.00, Eversource −$210.00, Xfinity −$93.00 |
| `IMG_1760.jpg` | `279ec911ca53e1d8…` | the list continued: Oct 30 → Dec 11 |
| `IMG_1761.jpg` | `7d9206ef10819a42…` | the list continued: Nov 30 → Jan 8, 2027 |

**Two instruments, then arithmetic.** The figures were transcribed manually and re-read by an independent image-reading
pass; the two readings agree row for row. Then the arithmetic was checked, because it is self-verifying: **balance =
previous balance + that row's delta holds on 23 of 23 transitions**, and both group totals equal the sum of their
itemised rows exactly (1,442.00 + 552.00 + 75.20 = 2,069.20; 552.00 + 210.00 + 93.00 = 855.00).

## 1. Units — settled, and the settlement is a cross-check rather than an opinion

* The provider API returns **cents** (integer minor units): the 2026-09-19 record stored `totalReservedAmount`
  `109710` = $1,097.10, and OS-058's experiment recorded `48077` = $480.77.
* Our ingest converts, deliberately and in one place: `meridian/providers/crewwork.py:285`
  `total_reserved_amount=_cents_to_dollars_or_none(total)`, with `currency="USD"`.
* The provider's own UI displays **dollars with cents**.
* **The decisive check:** the UI's first row is `Sep 26 … −$183.77` with a delta of `−$176.77`, so the balance before
  today's events is **−$7.00**. Our stored `crew_bill_reserves.total_reserved_amount` reads **−7.0**, and our column is
  dollars. Two independent instruments, one number. The unit convention is therefore bound for this field, and the
  projection's rows are read on the same scale as the sibling field.

**What this does and does not settle.** It settles the convention and proves our ingest matches the provider's display.
It does not by itself prove that the projection's `rows[].amount` is in the same minor unit as every other amount field —
that one still deserves a single value-level comparison at contract lock, because this repository has mixed cents and
dollars across surfaces before.

## 2. Two fields share a name and do not mean the same thing

| level | field | value now | what it is |
|---|---|---|---|
| reserve | `estimated_next_funding_amount` | **1435.97** | the provider's own PAYCHECK event amount in the projection (UI: `+$1,435.97` on eight consecutive pay dates) |
| per bill | `estimated_next_funding_amount` | VPA 34.59, Verizon 46.72, Xfinity 42.78, Eversource 96.60, Rent 663.27 | each bill's prorated forward need; **they sum to exactly 883.96** |

That sum is a verified prediction, not a coincidence: OS-058's measurement doc states *"one event's five allocations
would sum to 883.96"*, and the live store now produces exactly that. **Correction owed to OS-058's BEFORE table**, whose
annotation called the reserve-level field *"account-total, lagged — NOT a reserve figure"*: the provider's projection
shows it carrying the next PAYCHECK amount, so the annotation was wrong in both directions — it is a reserve figure, and
it is an event amount rather than an account total. It is also **not** the plan's stored amount ($1,649.10 biweekly),
which is a discrepancy to keep open rather than explain away.

## 3. The projection is a forecast that goes negative — and that is not `totalReservedAmount`

The header says **"Off track"** and **"Runs short · Today"**; the chart falls below its zero line repeatedly; the current
reserve balance is **−$183.77**. Meanwhile our `totalReservedAmount` was 0.00 for most of the series and is now −7.00
(the pre-event balance). These are different quantities:

* `totalReservedAmount` is money the provider says is *set aside right now*.
* The projection's running balance is a *forecast* of the reserve's cash flow, which the provider itself allows to go
  negative and labels as running short.

The two must never be presented as one figure (D-015, D-017). The timeline's headline may quote the projection; it may
not restate it as money held.

## 4. What the three event types look like in the UI

The structural capture recorded `event types: ALLOCATION, BILL, PAYCHECK`. The UI shows all three in one list:

* **PAYCHECK** — `State Of New Hampshire +$1,435.97`, every **14 days**: Oct 2 → Oct 16 → Oct 30 → Nov 13 → Nov 27 →
  Dec 11 → Dec 25 → Jan 8, 2027. Eight consecutive paychecks, each the same amount, which also corroborates the
  biweekly anchor our store holds (2026-09-18 + 14n reaches 2026-10-02 ✔).
* **BILL** — Rent 1,442.00 · Verizon 101.57 · Eversource 210.00 · Xfinity 93.00 · Verizon Payment Arrangement 75.20.
  Every amount matches our `commitments.amount` for the same bill, to the cent.
* **ALLOCATION** — a recurring `−$552.00` labelled `Safe to Spend`, appearing on the same dates as paychecks. Reading it
  as an ALLOCATION event is **an inference from the recorded event types plus its name, not a proven mapping**; what is
  observed is that a −$552.00 entry named "Safe to Spend" recurs every 14 days and is grouped with bills on shared dates.

**Grouping rule the UI follows, and the timeline must reproduce:** rows are grouped by date; the group label is the first
event's name plus "+N more"; the group's delta is the sum of its items; the running balance carries across groups.

## 5. Two observations about the live data, recorded rather than resolved

* **The series recorded its first real non-zero allocation at 2026-09-26T18:05:18Z**: VPA 150.40, Verizon 203.14,
  Xfinity 186.00, Eversource 420.00, Rent 1,043.48 (`data_mode = actual`, one capture, zero in the captures either
  side). The first four are **exactly twice** those bills' amounts; Rent's is not twice its amount, so no rule is
  established from it. It is unexplained by anything in this repository and the owner should say what he ran at
  ~14:05 local. What it *does* prove: the dated record path works end-to-end on a live non-zero state, which was
  OS-114 item 2's outstanding requirement.
* **The fixtures changed.** The six `Allocation Probe*` bills are gone (0 live rows) and **12 `Journey Test Bill` rows at
  exactly $100.00 each** now exist, all with no `reserved_by`, none appearing in the projection or in the per-bill
  observation series. That name is the one created by `tests/browser/test_recovery_journeys.py`, and
  `tests/browser/conftest.py` targets `APP_URL` from the environment — so the most likely explanation is a journey run
  against the live app rather than an owner-made fixture. **Not concluded: asked.** If it is a test artifact it is the
  same isolation class as OS-131; either way the handling is archive, never delete (D-039).

## Provenance

Owner-supplied, 2026-09-26, from the native Crew app (`2:54–2:55` local) while the reserve was off track. Reading: manual
transcription plus an independent image-reading pass, then arithmetic verification. No credential, cookie, token or
account identifier appears in any of the five files; the amounts are the owner's own and are already recorded in this
repository's ledger.
