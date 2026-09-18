# Connector readback fields — patch for the owner to apply

**Status:** verified patch, **not applied**. Prepared 2026-09-14 in the ORSC lane.
**Target repository:** `/Users/stephenwest/Applications/CrewWorkAssistantOTP` (different repository, out of this lane).
**Read-only:** both changes are GraphQL *field selections inside existing queries*. Neither adds a mutation, an operation file, or an allowlist entry.

## Why this document exists instead of a commit

The owner authorized this connector edit on 2026-09-14. This lane cannot make it: the preset's `agent-admission` guard refuses mutations outside `/Users/stephenwest/Openrouter/simplecrew-latest` with

```
agent-admission: edit is denied because file_path resolves outside this lane (path-escape).
Mutate inside the lane, or state the change and let the owner make it.
```

That guard is a deliberate boundary, so it was **not** worked around with a sandbox escalation. The guard's own second route — state the change and let the owner make it — is what this document does.

## What it unblocks

Six of the seven remaining unverified Crew write action types. Each blocker is the same shape: the live evidence exists (Astra's `CREW_DISCOVERY_HANDOFF.md`, 2026-09-14), but the connector's queries do not request the fields, so ORSC cannot read them.

| Action type | Needs | Field already live-verified |
|---|---|---|
| `create_crew_paycheck_funding_plan` | `fundingPlans` | yes |
| `update_crew_paycheck_funding_plan` | `fundingPlans` | yes |
| `delete_crew_paycheck_funding_plan` | `fundingPlans` | yes |
| `top_up_crew_reserve` | `billReserve.id` | yes |
| `create_crew_pocket_reassignment_rule` | `reassignmentRules` | yes (query accepted; response observed empty) |
| `delete_crew_pocket_reassignment_rule` | `reassignmentRules` | yes (same) |

Not addressed here: `crew_initiate_transfer` needs the transfer id returned by the write, which is a mutation-result shape and is not yet captured.

## The patch

Applies from the repository root with `git apply`. `git apply --check` has already been run against the live working tree and passes for both files.

```diff
--- a/operations/expenses.graphql
+++ b/operations/expenses.graphql
@@ -2,10 +2,15 @@
   currentUser {
     accounts {
       billReserve {
+        id
         nextFundingDate
         totalReservedAmount
         estimatedNextFundingAmount
         settings { funding { subaccount { id displayName } } }
+        fundingPlans {
+          id name amount frequency frequencyInterval anchorDate
+          reassignmentRule { id match minAmount maxAmount }
+        }
         bills {
           amount anchorDate autoAdjustAmount dayOfMonth daysOverdue
           estimatedNextFundingAmount frequency frequencyInterval id name
--- a/operations/family.graphql
+++ b/operations/family.graphql
@@ -12,6 +12,10 @@
         scheduledAllowance { id totalAmount }
       }
       parents { id isApplying cardColor imageUrl displayedFirstName }
+      reassignmentRules {
+        id match minAmount maxAmount
+        assignmentSubaccount { id displayName }
+      }
     }
   }
 }
```

### Resulting `operations/expenses.graphql`

```graphql
query CurrentUser {
  currentUser {
    accounts {
      billReserve {
        id
        nextFundingDate
        totalReservedAmount
        estimatedNextFundingAmount
        settings { funding { subaccount { id displayName } } }
        fundingPlans {
          id name amount frequency frequencyInterval anchorDate
          reassignmentRule { id match minAmount maxAmount }
        }
        bills {
          amount anchorDate autoAdjustAmount dayOfMonth daysOverdue
          estimatedNextFundingAmount frequency frequencyInterval id name
          paused reservedAmount reservedBy status
        }
      }
    }
  }
}
```

### Resulting `operations/family.graphql`

```graphql
query FamilyScreen {
  currentUser {
    id
    family {
      id
      children {
        id dob cardColor imageUrl displayedFirstName
        spendAccount {
          id overallBalance
          subaccounts { id displayName clearedBalance }
        }
        scheduledAllowance { id totalAmount }
      }
      parents { id isApplying cardColor imageUrl displayedFirstName }
      reassignmentRules {
        id match minAmount maxAmount
        assignmentSubaccount { id displayName }
      }
    }
  }
}
```

## Verification already performed (in-lane, read-only)

Performed against the proposed documents before handing them over:

- **The connector's own gate.** Both documents were passed through that repository's `crew_work_assistant.safety.assert_read_only`, which rejects any document containing `mutation` and requires a query document. Both pass.
- **No placeholder.** `operations.PLACEHOLDER_MARKER` (`CAPTURE_FROM_CREW_WEB_APP`) is absent from both, so `load_operation` will not raise.
- **Braces balanced** in both.
- **`git apply --check`** against the live working tree: clean for both files.
- **Field names are live-verified**, not authored: every added field appears in an accepted live query in `CREW_DISCOVERY_HANDOFF.md` Appendix A — `fundingPlans { id name amount frequency frequencyInterval anchorDate reassignmentRule { id match minAmount maxAmount } }` and `billReserve { id … }` in `FundingPlanReadback`/`ReserveSettingsVerified`, and `reassignmentRules { id match minAmount maxAmount assignmentSubaccount { id displayName } }` in `ReassignmentRead`.

**Not verified, and cannot be from this lane:** that the live server accepts the *composed* documents. Each field is individually accepted; the combinations have not been sent. This is the residual risk, and it is small but real.

## Steps to apply

```bash
cd /Users/stephenwest/Applications/CrewWorkAssistantOTP
git apply /path/to/patch.diff           # or paste the two files above
.venv/bin/python -m pytest tests/ -q    # that repo's own suite
git add operations/expenses.graphql operations/family.graphql
git commit -m "Select billReserve.id, fundingPlans and family reassignmentRules"
```

**Preserve unrelated work.** That repository currently has ` M src/crew_work_assistant/auth.py` (uncommitted) and an untracked `uv.lock`, is on `main`, and has **no remote**. Stage only the two `operations/` files, as above — never `git add -A`. Astra's handoff also says not to stash or discard the `auth.py` change.

## What happens after it lands

Nothing changes in ORSC until the adapter is extended to read the new fields, which is the next slice and is in-lane:

1. `meridian/providers/crewwork.py` — accessors for `billReserve.fundingPlans` (from the `expenses` facet) and `family.reassignmentRules`.
2. `meridian/crew_write_actions.py` — verifiers for the six action types. Absence confirms a deletion, never a creation; an unobserved facet stays unresolved, never "empty".
3. `docs/project/write-coverage.json` — move the six types from `verification: none` to `readback` with their check names.

Discipline the handoff requires for `top_up_crew_reserve`: **a changed reserve amount is not proof of a particular top-up.** Attribution must key on `billReserve.id`, not on a delta — which is precisely why the one-field `id` addition is in this patch rather than a total-only comparison.
