# Plan panes — Rules and Crew: design proposal for approval (OS-102)

**Status: PROPOSAL. Nothing here is implemented, and no code has been written for it.**
Owner instruction, 2026-09-24: *"the rules and crew tab of the plan page have almost no styling. I do not
believe there is a previous concept, so it is one you will have to design."*
Ledger scope, verbatim: *"Owner-stated absence of a concept is a claim to VERIFY against design/ before
designing anything."* This document is that verification, and then the design it asks for.

---

## 1. The verification: the premise is half right, and the half that is wrong changes the job

**No DRAWN concept exists for these two panes.** Checked all nine `design/*/` directories, their READMEs and
handoffs, and the asset/icon manifests:

- `design/observatory-drafts-2026-09-08/02-plan.png` draws the Plan tab (the foldout map, the allocation
  summary, the bills table). It does not draw a Rules pane or a Crew pane.
- `design/observatory-extension-2026-09-18/concepts/` holds exactly four concepts — `review`, `settings`,
  `timeline`, `virgil` — and its `BUILD_HANDOFF.md` names the same four surfaces. No Plan pane.
- `design/plan-map-marks-2026-09-23/` supplies map marks for the Plan *map*, not these panes.
- Nothing else under `design/` mentions either pane.

**A governing PROSE specification does exist, and it is binding.** `design/observatory-drafts-2026-09-08/BUILD_SPEC.md`
§8 "Plan suite" states both panes' requirements verbatim:

> **Rules tab:** grouped existing rules with readable trigger → condition → effect summaries. Show schedule and
> paused state. Edit opens a form prefilled with every supported current field; omissions must not clear
> unrelated Crew configuration.
>
> **Crew tab:** operation controls organized by purpose (bills, pockets, cards), not raw GraphQL names. Hide
> unsupported controls or explain unavailable capability honestly. No 'deferred' item next to a working
> duplicate control.

`AGENTS.md` settles precedence: the 09-18 set governs what it covers, and *"anything it does not cover is
governed by `design/observatory-drafts-2026-09-08/`"* — which names `plan` explicitly, `BUILD_SPEC.md` included.

**Conclusion, and the reason this document is shorter than "design two panes":** the CONTENT requirements, the
honesty rules and one interaction are already specified by a governing record. What is missing is the
**composition and styling**. That is a derivation job with a binding checklist, not an invention — so the
invention risk, and the scope, both fall.

---

## 2. What is there today (measured, not read)

Measured in the isolated synthetic preview at 420x912 DPR 3, both themes, by clicking the app's own segmented
control. Captures: `artifacts/plan-panes-discovery-2026-09-24/{rules,crew}-{dark,light}.png` (untracked).

### Rules pane — `[data-plan-view-pane="rules"]`

One section, `[data-plan-rules]`, whose only pane-level styling anywhere is `plan.css: .m-plan-rules`. Its
renderer is `renderRules()` (`static/js/meridian/plan.js:1606`).

| BUILD_SPEC §8 requires | today |
|---|---|
| grouped existing rules | a flat list; no grouping |
| readable **trigger → condition → effect** | **nothing.** The card renders a name, an optional `Paused` badge and a `Delete` button |
| schedule | **nothing** |
| paused state | yes — a `Paused` badge (`m-bill-badge--due_soon`) |
| edit, prefilled with every field | **absent** — and the pane's own deferred list admits "Edit autopilot rule" |

**Defect 1 (observed, empty case):** `[data-rules-empty]` is a CHILD of `[data-rules-list]`, and `renderRules`
calls `list.replaceChildren()`. With zero rules the note is made visible and detached in the same pass.
Measured: `noteInDom: false`, `childElementCount: 0`, pane height **0px**. The owner sees a blank pane and
cannot tell "no rules" from "broken".

**Defect 2 (reasoned from the source, NOT observed):** with the note detached, a second `renderRules` pass would
evaluate `empty.hidden` on `null`. It does not run twice in one page life in the preview, so this is a risk
statement rather than a measurement; it would be pinned by a test either way.

### Crew pane — `[data-plan-view-pane="crew"]`

Three sections, and they are not peers:

| section | class | styling today | note |
|---|---|---|---|
| Crew capabilities (deferred) | `.m-plan-parity` | **none at all** — neither `.m-plan-parity` nor `.m-parity-list` appears in ANY stylesheet | 4 entries, kept honest by `tests/browser/test_capability_parity.py` (OS-066) |
| Crew actions | `.m-plan-actions` | container rule in plan.css; `.m-action-form` also has an observatory.css rule | **7 forms in one flat sequence** |
| Crew mutation coverage | `.m-surface.m-plan-capture-status` | the only real card (`rgb(20,27,50)`, 1px border, radius 16) | read-only |

The 7 forms run: Create pocket, Create bill, Top up reserve, Manage autopilot rule, Set active spend pocket,
Delete pocket, Create virtual card. **BUILD_SPEC §8's "organized by purpose (bills, pockets, cards)" is not
met** — the pocket controls sit at positions 1, 5 and 6, the card control last, the rule control between them.

**Not a finding:** the preview answers 501 to any POST and does not serve `/api/meridian/crew/mutations-status`,
so the coverage card renders empty here. Both are the isolated preview's own limits, not application defects.

### The datum that makes the Rules pane cheap to fix

`meridian/services/plan.py` already sends each rule's **`formula`** (`"formula": item.get("formula")`, line ~119),
and `renderRules` drops it on the floor. That formula is the real Crew AutopilotRule payload — `triggers`,
`actions` (sixteen-supported action types), optional `IdMatch`/`Or`/`And` conditions, and often a `description`
(`meridian/crew_commands.py:257-330`). It is exactly the trigger → condition → effect material §8 asks to render.
**The pane can meet §8's central requirement from data it already receives: no backend change, no new query.**

---

## 3. The proposal

**Principle.** These panes adopt the Plan surface's existing Observatory vocabulary rather than inventing a new
one: the same section label and one-line note the other Plan sections use; the dotted-brass rule already
governed on Accounts for separations; the app's existing badges, buttons and forms. One new visual element is
proposed for the Rules pane — an engraved mark per rule group — and it is the ONLY new artwork the design needs.

### 3.1 Rules pane — a rule reads as a STATEMENT

```
[engraved mark]  Round Up Savings                             [Paused]
                 When   a debit card transaction settles
                 If     the merchant matches "Coffee"          ← omitted when the rule has none
                 Then   round up to the nearest $1.00 into Checking · Pocket
                 ────────────────────────────────────────────────────────────
                 Crew · observed 2h ago                        [Edit]  [Delete]
```

- **Trigger / condition / effect come from `formula`**, humanised for the action types Meridian can name, with
  the account or pocket named rather than its id.
- **Honesty, per §8's "explain unavailable capability honestly":** when a formula's shape is not one Meridian can
  humanise, the card shows the raw formula instead of inventing a sentence. It never shows a sentence it cannot
  support.
- **Grouping** is by what the rule acts on — Bills · Pockets · Cards · Notifications — falling back to a single
  "Rules" group. Never by raw action-type union names (§8: "not raw GraphQL names").
- **Provenance on every card:** source (`Crew`) and observation time, which OS-102's acceptance requires.
- **Schedule** is shown when the formula carries one, and the card says so plainly when it does not — never a
  blank where a fact should be.
- **Empty state:** the note survives (defect 1 fixed) and says what a rule would do for you.
- **Edit is a NON-GOAL of this slice.** §8 asks for a prefilled edit form, but that is a new WRITE control, so it
  goes through the action pipeline as its own bounded slice with its own authority review. Until then the card
  reserves its place and the pane states plainly that editing is not yet available here.

### 3.2 Crew pane — controls organized by PURPOSE

```
Bills      Create bill
Pockets    Create pocket · Top up reserve · Set active spend pocket · Delete pocket
Cards      Create virtual card
Rules      Manage autopilot rule
```

- Each purpose becomes a labelled group with its own heading; every existing control keeps its exact behaviour,
  label and validation — this is re-grouping existing forms, not new capability.
- **The deferred list moves INSIDE its purpose group** ("Update virtual card" with Cards, "Create pocket
  reassignment rule" with Pockets). That satisfies §8's "no 'deferred' item next to a working duplicate control"
  more strictly than today's separate block, and it retires the wholly unstyled top section the owner is seeing.
- Destructive actions stay separated from ordinary editing (§8 states that rule for bill/goal detail; applying it
  here is consistency, and `Delete pocket` already carries the danger treatment and a confirm).
- The read-only coverage card keeps its card treatment and sits last, under a heading that says it is
  read-only.

### 3.3 Non-goals (unchanged from the ledger, restated because they are the safety case)

No new navigation. No financial behaviour. No authority change. No mutation. No invented data. Every word and
figure stays real HTML; decoration stays `pointer-events: none`; money is never cropped; nothing here grants a
capability that does not already exist — and the grouping must not make a capability *look* newer or safer
than it is.

---

## 4. What the owner is being asked for

1. **Approve the direction** — Rules as statements built from `formula`, Crew grouped by purpose — or name what
   should change.
2. **The deferred list's home.** (a) inside each purpose group *(recommended: it improves honesty and satisfies
   §8 more strictly)*, (b) kept as its own block but styled, or (c) retired once each deferred item has a live
   control — which is a capability question, not a styling one.
3. **Whether Edit-a-rule is scoped now** as its own bounded write slice, or stays parked with the pane saying so.

On approval, the implementation is one bounded slice per pane, each with its own guards, both themes, and the
governed viewports; the ledger entry is updated with the measurement before and after, as OS-103 was.
