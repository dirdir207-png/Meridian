# CFO mandate — open questions

**What this is.** A collector for the constraints that will bound an autonomous CFO (concept 22). You write the
answers as they occur to you, over however long it takes.

**What this is not.** Not a constraint, not a schedule, not a design. Until an answer is written here and recorded
in `MERIDIAN_DECISIONS.md`, the question is **open** — and an open question is **not a default and not
permission**. Absence of an answer must never read as consent. That mirrors the rule the system already follows
for missing data: it is never treated as zero.

**Provenance.** Every question below is architect-posed `[D]`. Every answer is yours alone. Nothing in this file
becomes binding until you write it.

**When this matters.** The CFO is slice C9, behind the correctness spine (C1–C4), the product spine (C0, D1–D5)
and the intelligence spine (I1–I3). Nothing in those depends on this file. It cannot start without your answers —
that is already a stop condition on the slice.

**Why the questions are shaped this way.** Three interfaces will give these constraints their real form, so
answers written before they exist may need revisiting:

| Interface | What it makes answerable |
|---|---|
`C4` per-action receipts | the divergence metric — what it recommended vs what you approved |
`C8` policy evaluator, wired | where standing prohibitions get *enforced* rather than stated |
`I1` evidence envelope | what an autonomous recommendation must carry before you can weigh it |

---

## 1. Scope of the mandate

- **Q1.1** Which categories may it form recommendations about? (bills, bill reserve, funding amounts, pocket
  transfers, subscription cancellations, income changes, account connections…) Which, if any, are excluded outright?
- **Q1.2** May it recommend on accounts or data it has not verified, or only on verified state?
- **Q1.3** May it propose *adding* financial products or connections, or only working within what exists?
- **Q1.4** Does it ever comment on things outside money — employment, housing, relationships — or is the mandate
  strictly financial?

**Your constraint:**

## 2. Bounds

- **Q2.1** Amount caps — per recommendation, per day, per week, per month? Absolute dollars, or relative to balance
  or income?
- **Q2.2** Is a cap a **hard block** (it may not even propose) or a **flag** (propose, clearly marked as over)?
- **Q2.3** Frequency limit — how many proposals per day before it must stop and wait?
- **Q2.4** Is there a bound on *aggregate* exposure across simultaneous pending proposals? Twenty small
  recommendations can sum to a large one, and each individually respects a per-item cap.
- **Q2.5** Does latitude scale with confidence — more freedom when certain, or the opposite?

**Your constraint:**

## 3. Authority and default behaviour

- **Q3.1** Silence is not consent — but what happens to an unreviewed proposal? Expire after N days, or persist
  indefinitely?
- **Q3.2** May it re-propose something you declined? How many times before it must stop permanently?
- **Q3.3** What counts as **ambiguous approval**? A partial approval, an approval with edits, approval of a
  different amount than proposed?
- **Q3.4** When you edit a proposal before approving, does that editing count as a signal it should learn from — and
  must that be visible to you?

**Your constraint:**

## 4. Evidence standard

- **Q4.1** What must accompany every recommendation before you would weigh it? (cited events, confidence, explicit
  assumptions, what would change the answer?)
- **Q4.2** When evidence is missing or partial — must it refuse, or propose with the gap clearly marked?
- **Q4.3** Must it state disagreement when it thinks your decision is wrong, or defer silently once you decide?
- **Q4.4** How stale may its data be before it must say so rather than recommend?

**Your constraint:**

## 5. Standing prohibitions

- **Q5.1** What must it *never* do, even with your approval? (external transfers, new credentials, opening or
  closing accounts, changing security settings, contacting third parties, anything irreversible?)
- **Q5.2** Which prohibitions are permanent and which could be revisited later?
- **Q5.3** Does a prohibitions list belong in the constitution (versioned, revocable) or hard-coded outside its
  reach?

**Your constraint:**

## 6. Oversight, and the gate going slack

- **Q6.1** What approval rate would tell you the gate has gone slack? Above what percentage would you want to be
  *told* it was happening?
- **Q6.2** Do you want a second reviewer at intervals, or only yourself?
- **Q6.3** Does the mandate itself expire? How often must it be actively re-granted?
- **Q6.4** What is the review cadence for what it has recommended over the last period — weekly, monthly, on
  request?

**Your constraint:**

## 7. Failure and uncertainty

- **Q7.1** When it is uncertain or its data is stale — defer, or proceed with disclosure?
- **Q7.2** If it recommended something, you approved, and it was wrong: what record and what rollback do you
  expect? (Note: an uncertain write is never auto-retried — that rule already binds.)
- **Q7.3** What should it do mid-recommendation if a provider fails or an account is unreachable?

**Your constraint:**

## 8. Revocation

- **Q8.1** How do you revoke the mandate mid-flight, and does revocation cancel pending proposals?
- **Q8.2** After revocation, does it stop entirely, or continue monitoring read-only?
- **Q8.3** Can revocation be partial — pull one category of authority while keeping the rest?

**Your constraint:**

## 9. Learning

- **Q9.1** May it learn from your approvals and declines, and change future proposals accordingly?
- **Q9.2** Must that learning be inspectable — can you see *why* it changed its behaviour?
- **Q9.3** May it learn from data outside your explicit interactions (patterns it notices on its own)?

**Your constraint:**

## 10. Phase-in

- **Q10.1** What is the trust ladder? For example: read-only monitoring → recommendations with no execution →
  recommendations in one bounded category → broader. Where does each rung end and what promotes it?
- **Q10.2** What evidence would justify moving up a rung, and who decides — you, or a measured threshold?
- **Q10.3** Is there a rung you would not go beyond without a period of demonstrated correctness first?

**Your constraint:**

---

## Recording answers

When you are ready, answers move to `MERIDIAN_DECISIONS.md` as their own numbered decision (following D-007), and
this file becomes the live list of what is still open. Questions can be added here freely — this is a working
document, not a commitment.
