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

## 6. A separate defect found while triaging: bills are not linked to evidence

`evidence_links` holds **15** links in total, and **all 15** target `transaction`:

| target_kind | relation | count |
|---|---|---|
| `transaction` | `documents` | 15 |

**Zero links target a bill** — against **11 bills** in the database — and only **8 distinct evidence
items** of 732 are linked to anything at all. So even with the blobs restored, a bill detail view has
no routine that finds bill-linked evidence: Gmail intake populates
`link_mail_evidence_to_transactions` (`meridian/gmail_intake.py:157`), and there is **no bill
equivalent**. That is a second, independent reason "viewing bills" looks broken, and fixing §3 alone
will not fix it.

---

## 7. What this triage did NOT do

- No provider call, no intake run, no backfill, no calendar fetch.
- No credential, token, message body or content hash value was read out or printed.
- No code, schema, provider or authority change — this document and the ledger row are the only writes.
