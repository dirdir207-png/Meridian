# Evidence pipeline triage — Gmail / calendar intake and the evidence viewer (2026-09-20)

**Owner report:** *"I don't think new evidence is being pulled from Gmail or calendar, and viewing
bills/evidence may be broken."*

**Verdict: BOTH ARE CONFIRMED, they have DIFFERENT causes, and the viewer failure has a specific,
reproducible root cause.** This is read-only triage against a copy of the live database. **No provider
call was made and no intake was run.**

Method: read-only `sqlite3` queries and `find` against a copy of the live DB (`/tmp/gate-preview/gate.db`)
and its evidence root. No credentials, tokens or message bodies were selected or printed — only counts,
flags and dates.

---

## 1. Gmail — CONFIRMED: nothing is pulling it

**Gmail intake is manual-only and nothing calls it.**

- The route is `POST /api/meridian/gmail/intake` (`meridian/api.py:685`), a **backfill** endpoint.
- **No frontend code calls it.** `grep -rn "gmail/intake" static/js/ templates/` returns **nothing**.
- The only automatic refresh is Crew: `meridian/refresh.py` → `MeridianRefreshService` pulls the
  CrewWorkAssistant snapshot. The live log shows it doing exactly that, repeatedly:
  `provider=crew status=complete accounts=6 transactions=100 errors=0`.

**Measured state of the evidence store (732 items):**

| source_kind | count | oldest | newest |
|---|---|---|---|
| `mail` | **730** | 2026-09-06 | **2026-09-06** |
| `manual` | 2 | 2026-09-04 | 2026-09-04 |
| `calendar` | **0** | — | — |

Every one of the 730 mail rows carries the **same** date, which is the signature of a **single
one-off backfill** rather than a running pipeline. Nothing has refreshed since.

Credentials are **not** the blocker: `connection_authorizations` shows `gmail|connected` (1) and
`calendar|connected` (1), and `oauth_tokens` holds **5 Gmail + 1 calendar** rows, **all with a
refresh token**.

## 2. Calendar — CONFIRMED, and it is worse than "not pulled": it is WIRED TO NOTHING

There is a real connector — `meridian/connectors/calendar.py`, docstring *"Bounded, minimum-field,
read-only calendar ingestion"* — but **nothing ingests with it**:

```
grep -rn "connectors.calendar" --include=*.py meridian/ scripts/ app.py
  meridian/api.py:1054  from meridian.connectors.calendar import READ_ONLY_CALENDAR_SCOPE
  app.py:129            from meridian.connectors.calendar import READ_ONLY_CALENDAR_SCOPE
```

Both hits import the **OAuth scope constant** only. There is no `calendar_intake` route (the intake
routes are `POST /gmail/intake` and `POST /icloud/intake`), and no caller of the ingestion function.

**And the calendar OAuth token exists** (`oauth_tokens`: 1 `calendar` row, with a refresh token,
created 2026-09-06). So the authorization was granted and then **never used** — consistent with the
owner's memory that calendar was set up. A connected, consented, refresh-capable calendar integration
with zero evidence rows and no code path that could ever produce one.

## 3. Evidence viewer — CONFIRMED, with a precise root cause: THE BLOB STORE IS EMPTY

This is the actionable one, and it explains "viewing evidence may be broken" exactly.

**The live log shows a real 404 from an evidence view:**

```
100.113.221.23 - - [19/Sep/2026 03:53:48] "GET /api/meridian/evidence/616/content HTTP/1.1" 404 -
```

**Why it 404s.** `meridian/api.py:1370` reads the blob and, if that read fails, returns:

> *"evidence_content_missing — This document's content is not stored yet. It was created before content
> was persisted; re-run the mail intake to backfill it."*

**Measured cause:**

| Check | Result |
|---|---|
| `evidence_items` rows | **732** |
| …carrying a non-empty `content_hash` | **732** |
| …carrying `size_bytes > 0` | **732** |
| **files in the blob store** (`/tmp/gate-preview/evidence`) | **0** |
| rows with `content_deleted_at` set | 0 |
| rows with `revoked_at` set | 0 |

So **every single evidence record has metadata claiming content, and not one blob exists on disk.**
Nothing was deleted, revoked or swept — the content was **never written**.

**This is a past defect, already partially fixed.** `meridian/ingest.py:79-86` now contains the repair
path for exactly this situation:

```python
existing = evidence_repo.get_by_content_hash(record.content_hash) ...
if existing is not None:
    # Still persist the blob on a duplicate (a prior run may have created the
    # metadata row before blob storage was wired, leaving the content missing).
    if blob_store is not None:
        try:
            blob_store.put(record.blob, mime_type=record.mime_type)
        except Exception:   # noqa: BLE001 - best-effort
            pass
        return IntakeResult(..., duplicate=True)
```

Both current routes **do** pass a blob store (`gmail_intake` at `meridian/api.py:707`,
`icloud_intake` at `:678`), and `EncryptedBlobStore.put` is **content-addressed by sha256**, so a
re-run is **idempotent** — it writes only what is missing and cannot duplicate.

**Verified independently:** the blob store itself is **functional**. An encrypted put/read round-trip
on a scratch root returns the original bytes, so the store is not the broken part.

---

## 4. The three real risks in the obvious fix

The obvious fix — re-run `POST /api/meridian/gmail/intake` — is right, but it is **not** risk-free and
must not be run blindly.

**(a) A 14-day window of mail may be permanently unrecoverable.** `since_days=30` and
`max_messages_per_account=50` are **hardcoded** in the route; neither is a request parameter.

| run | window |
|---|---|
| original (2026-09-06) | 2026-08-07 → 2026-09-06 |
| a re-run today (2026-09-20) | 2026-08-21 → 2026-09-20 |

The two windows overlap only from 2026-08-21. **Mail dated 2026-08-07 → 2026-08-20 is outside the new
window**, so those blobs can no longer be fetched from the provider and would stay permanently
unreadable even after a successful backfill. Widening `since_days` (or making it a parameter) **before**
re-running is the difference between recovering most of the archive and recovering half of it.
The same arithmetic applies to `max_messages_per_account=50` with 5 Gmail accounts in play.

**(b) The failure is SILENT.** The blob write on the duplicate path is wrapped in
`except Exception: pass` (`ingest.py:85-86`). If the write fails, intake still reports
`state: ingested` with `duplicate: true`, the API tells the owner it worked, and the blob count stays
zero. **The only trustworthy check is the blob count on disk, not the route's response.**

**(c) The encryption key is derived from `app.secret_key`.** `app.py:116-120` builds the store as
`EncryptedBlobStore(evidence_root, DerivedKeyProvider(app.secret_key.encode()))`. If `app.secret_key`
has changed since a blob was written, that blob becomes undecryptable, and `read()` raising is caught
and reported as the same "not stored yet" 404 — indistinguishable to the owner from the current
condition. Worth checking deliberately rather than discovering later.

## 5. Recommended order (all require the owner's go-ahead)

1. **Widen the intake window first** (`since_days`, and review the per-account cap), so the re-run
   recovers as much of the 2026-08-07 → 2026-09-06 range as the provider still holds. Doing the
   backfill before this loses that 14 days permanently.
2. **Re-run Gmail intake**, then **verify by counting blobs on disk** — not by reading the response.
   A successful backfill moves the count from 0 to (approximately) the number of recoverable rows.
3. **Make the silent failure visible.** Surface a blob-write failure rather than swallowing it, so
   "ingested" can never again mean "metadata written, content missing".
4. **Calendar needs a decision, not a fix.** The connector and a live token both exist and nothing
   calls it. Wiring it is a new capability with its own scope question (which events become
   evidence, and under what linking rule), so it belongs in a task, not a patch.
5. **Then the bills/evidence linking gap** — see §6.

## 6. CORRECTION — bills DO have evidence; my first claim here was wrong

**I originally wrote that "bills are not linked to evidence" and that bill evidence would not
appear even after restoring the blobs. That was WRONG and the owner corrected it. The mechanism
exists and works through a path I did not check.**

Bill invoices are rendered on the Plan page from `commitment.invoice_evidence`:

- `static/js/meridian/plan.js:583-594` builds a clickable link per invoice —
  `Invoice · {title}` — opening `invoice.content_url` (the evidence-content endpoint).
- `meridian/services/plan.py:182` `_bill_invoice_evidence(...)` resolves it, exposed at
  `plan.py:418-419` as `"invoice_evidence"`.

The mistake was mine and worth naming precisely: I queried the `evidence_links` **table** for
`target_kind='bill'`, found none, and concluded the capability was missing. In fact bill evidence is
resolved **at read time by name/domain matching** over the mail store, not through a stored link row:

```
meridian/services/plan.py:182   def _bill_invoice_evidence(evidence_repository, bill_name, limit=4)
  … items = evidence_repository.list_items(source_kind="mail", limit=400)
  … matches sender domain first, then biller-name tokens in the subject
```

`evidence_links` is used for the **transaction** linkage only
(`gmail_intake.py:157` `link_mail_evidence_to_transactions`). Both are legitimate; they are just
different mechanisms, and "no link row" is not "no evidence".

**What survives, and is now the single reason invoices do not open:** §3 — the blob store holds
**0 files against 732 metadata rows**, so every `content_url` the Plan page produces returns the
`evidence_content_missing` 404. One root cause, not two.

**One real caveat found while correcting this:** `_bill_invoice_evidence` calls
`list_items(source_kind="mail", limit=400)` while the store holds **730** mail items. That cap is a
silent truncation — evidence beyond the 400 most recent mail items per bill lookup is invisible to
the matcher. Worth reviewing, since a fresh backfill will push the count further past it.

## 7. THE BACKFILL WAS ATTEMPTED AND IS BLOCKED — ALL GOOGLE TOKENS ARE DEAD

The owner approved the backfill ("go ahead approved, and I'll restart"). It was run and it
**failed at authentication, before any fetch**. This is a blocking finding, not a code defect.

```
BEFORE  mail_items=730  blobs=0
RUNNING since_days=45  max_per_account=50
Google token refresh failed (HTTP 400)
```

**Every stored token fails, not just one** (`tmp/diagnose_tokens.py`, outcome only — no tokens,
addresses or bodies printed):

```
kind=gmail    accounts=4   account[0..3] has_refresh=True refresh=FAILED HTTP 400
kind=calendar accounts=1   account[0]    has_refresh=True refresh=FAILED HTTP 400
```

**The store was not damaged.** After the failure: 732 items, 0 blobs — identical to before,
because the refusal happens in `list_message_ids` before any write. That is the fail-safe
working: a run that cannot authenticate changes nothing.

### The likely cause, and it is a configuration issue rather than a bug

| | |
|---|---|
| all 5 tokens created | **2026-09-06** |
| today | **2026-09-20** |
| age | **exactly 14 days** |

Google expires refresh tokens after **7 days** while the OAuth consent screen is in
**"Testing"** publishing status. `HTTP 400` on refresh with a present `refresh_token` is that
signature — the token is not malformed, it has been invalidated. It also fits the whole picture:
the store froze on exactly the day the tokens were minted and nothing has refreshed since.

**This must be confirmed against the Google Cloud console rather than assumed** — the same 400
is also what a revoked or rotated token produces, and an expired *client secret* looks similar.
The console check is: OAuth consent screen publishing status, and whether the refresh tokens are
still listed for the app.

### What this means for the fix I just shipped

The polling service is correct and will work **once there is a live token** — but **it cannot
fix this on its own.** With a dead refresh token it will log a failure every 30 minutes forever.
Two consequences worth stating plainly:

1. **The owner must re-authorize Gmail (and calendar) once**, from the Meridian settings UI,
   because consent is the one step Meridian cannot self-serve.
2. **Publishing the OAuth app to "In production" is what prevents this recurring.** In Testing
   status the same 7-day expiry will kill the tokens again, and the symptom will look identical
   to the bug just fixed. Publishing is a Google Cloud console action only the owner can take.

A partial mitigation now exists in the code: because polling reports a **verified blob delta**,
a cycle that authenticates but writes no content is visible in the log. A cycle that cannot
authenticate still only logs a line, so the failure is quieter than it should be.

### Current status of the four defects in this triage

| # | Defect | Status |
|---|---|---|
| 1 | Gmail not polled (manual-only) | **FIXED** — polling service shipped; blocked from *delivering* by the dead token |
| 2 | Calendar wired to nothing | **OPEN** — connector exists, token was also dead; needs a scope decision |
| 3 | Blob store empty → every view 404s | **ROOT-CAUSED** — needs one successful authenticated run; blocked by the dead token |
| 4 | Bills DO have evidence | **NOT A DEFECT** — my §6 correction |

## 8. IMPLEMENTED — semi-regular polling (the owner's direction)

> *"it should semi-regularly poll though, I shouldnt have to request a back fill through the harness any
> time I want evidence information, defeats the purpose."*

`meridian/evidence_refresh.py` now runs the read-only intake on an interval, wired into `app.py`
beside the existing Crew refresh (started from `ensure_meridian_refresh`, never on import).

| knob | default | why |
|---|---|---|
| `MERIDIAN_EVIDENCE_INTERVAL` | 1800s | floor **300s** — this makes authenticated calls to Google, so it is deliberately *far* slower than the 15s graph reconcile |
| `MERIDIAN_EVIDENCE_SINCE_DAYS` | 45 | widened from the old hardcoded 30, so a backfill reaches at least as far back as the run it repairs |
| `MERIDIAN_EVIDENCE_MAX_MESSAGES` | 50 | per account |

Three properties are load-bearing, and each is pinned by a test:

1. **It reports what it OBSERVED, not what it ATTEMPTED.** Because `ingest_record` swallows
   blob-write failures, the service counts the blob store before and after every cycle and reports
   `blobs_written`. "Ingested" can therefore never again silently mean "metadata only" — the exact
   failure that produced 732 rows and 0 blobs.
2. **Single-flight.** A concurrent cycle is **refused, not queued**, so a tick that overruns cannot
   stack provider calls.
3. **Read-only at the provider.** Fetches only — no send, label, archive or delete. No financial
   write path, no approval authority.

The manual route now also honours `MERIDIAN_EVIDENCE_SINCE_DAYS` (default 45) instead of a hardcoded
30, so a deliberate backfill is not stuck with the window that caused the problem.

**Falsified three ways**, each failing exactly one test: removing the single-flight refusal,
replacing the verified blob delta with the intake's own `total_stored` claim, and dropping the
provider-poll floor.

**Still open, and deliberately not done:** the backfill itself has **not** been run (it makes real
provider calls and needs the owner's go-ahead), calendar remains wired to nothing, and the 14-day
window is *mitigated* by the wider default but only actually recovered by running the backfill.

## 9. What this triage did NOT do

- No provider call, no intake run, no backfill, no calendar fetch.
- No credential, token, message body or content hash value was read out or printed.
- No code, schema, provider or authority change — this document and the ledger row are the only writes.
