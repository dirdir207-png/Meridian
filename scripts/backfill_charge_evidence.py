"""Backfill charge evidence from a Gmail receipt sample (OS-067).

WHY THIS EXISTS. Meridian can only read iCloud over IMAP; the Gmail API tokens are dead
(Testing-status 7-day refresh expiry). Composio can read Gmail in full, but only the agent
can call it — the running app cannot. So historical receipts are unreachable BY THE APP
unless they are fetched once and replayed into the canonical intake.

HOW IT WORKS, and why it is safe. It does NOT write evidence rows itself. It supplies the
fetched messages through a transport that satisfies the same interface as the iCloud one and
hands them to the SAME `ingest_icloud_recent` the poller uses. So every row goes through the
canonical path: quarantine, dedupe, content-before-row, blob store, amount/date linking.
Nothing here can produce a row the normal pipeline would not.

Dedupe is load-bearing and free: `evidence_items` is unique on
(source_kind, source_id, content_hash) and `source_id` is the provider message id, so
replaying a message that already arrived by forwarded mail is a no-op that only fills in a
missing blob.

DEFAULTS TO A DRY RUN. `--apply` is required to write to the live database, and the dry run
reports the honest numbers first — including how many receipts matched a real charge.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/stephenwest/Openrouter/simplecrew-latest")
sys.path.insert(0, str(ROOT))
import os

for _line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if _line.strip() and not _line.startswith("#") and "=" in _line:
        _k, _v = _line.split("=", 1)
        if _k.strip() and _v.strip() and _k.strip() not in os.environ:
            os.environ[_k.strip()] = _v.strip()


class ReplayTransport:
    """Serves staged Gmail receipts through the iCloud transport interface.

    Read-only by construction: it holds a list and slices it. It cannot reach the network.
    """

    def __init__(self, records: list[dict]):
        self._records = records

    def fetch_recent(self, *, max_results=20, since=None, mailbox="INBOX"):
        from meridian.connectors.icloud_mail import IcloudMailMessage

        selected = self._records[:max_results]
        return [
            IcloudMailMessage(
                message_id=r["message_id"],
                subject=r.get("subject") or "",
                sender=r.get("sender") or "",
                received_at=r.get("received_at") or "",
                body_text=r.get("body_text") or "",
                thread_id=r.get("thread_id"),
            )
            for r in selected
        ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", default="tmp/receipts_backfill.json")
    parser.add_argument("--db", default="/tmp/gate-preview/gate.db")
    parser.add_argument("--apply", action="store_true", help="write to the live database")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    records_path = ROOT / args.records
    records = json.loads(records_path.read_text(encoding="utf-8"))
    print(f"staged receipts: {len(records)}  (source: {args.records})")

    live_db = args.db
    if args.apply:
        target = live_db
        print(f"MODE: APPLY -> writing to {live_db}")
    else:
        sandbox = Path(tempfile.mkdtemp(prefix="meridian-backfill-dryrun-"))
        target = str(sandbox / "gate.db")
        blob_root = Path(live_db).parent / "evidence"
        try:
            shutil.copy(live_db, target)
        except Exception as exc:  # noqa: BLE001
            print(f"could not copy the live DB ({exc}); running against an empty store")
        print(f"MODE: DRY RUN -> writing to a throwaway copy at {target}")
        if blob_root.exists():
            print("       (blobs are read from the live store; the dry run writes new ones "
                  "beside it under the sandbox, not into it)")

    from meridian.evidence import EvidenceRepository
    from meridian.gmail_intake import ingest_icloud_recent
    from meridian.repository import FinancialRepository

    graph = FinancialRepository(target)
    repo = EvidenceRepository(graph.db_path)

    transactions: list = []
    cursor = None
    for _ in range(20):
        page, cursor = graph.list_transactions(limit=200, cursor=cursor)
        transactions.extend(page)
        if not cursor:
            break
    print(f"transactions available for matching: {len(transactions)}")

    # The app's OWN factory, so key derivation matches production exactly. DB_FILE must be
    # set BEFORE the import, because the factory derives the evidence root from it — setting
    # it afterwards would read the live blobs while writing to the sandbox, and a dry run
    # that writes to one place and reads from another reports numbers that mean nothing.
    os.environ["DB_FILE"] = target
    os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
    import app as app_module

    blob_store = app_module.app.config["MERIDIAN_EVIDENCE_BLOB_STORE_FACTORY"]()
    print(f"blob store root: {getattr(blob_store, '_root', 'n/a')}")

    before_items = len(repo.list_items(source_kind="mail", limit=100000))
    summary = ingest_icloud_recent(
        transport=ReplayTransport(records),
        evidence_repo=repo,
        transactions=transactions,
        max_messages=args.limit,
        since_days=120,
        mailbox="INBOX",
        blob_store=blob_store,
    )

    print("\n=== canonical intake summary ===")
    for key, value in summary.items():
        if key != "items":
            print(f"  {key}: {value}")

    after_items = len(repo.list_items(source_kind="mail", limit=100000))
    print(f"\nmail evidence rows: {before_items} -> {after_items} (+{after_items - before_items})")

    # Filled blobs: rows that existed but whose content was missing.
    filled = 0
    for item in repo.list_items(source_kind="mail", limit=100000):
        try:
            blob_store.read(item.content_hash)
            filled += 1
        except Exception:
            pass
    print(f"blobs now readable: {filled}")

    links = summary.get("linked", 0)
    print(f"charge links created: {links}")

    from meridian.charge_match import find_charge_matches, summarize

    class WithBody:
        __slots__ = ("id", "title", "sender", "body")

        def __init__(self, item, body):
            self.id, self.title, self.sender, self.body = item.id, item.title, item.sender, body

    enriched = []
    for item in repo.list_items(source_kind="mail", limit=100000):
        try:
            body = blob_store.read(item.content_hash).decode("utf-8", errors="replace")
        except Exception:
            body = ""
        enriched.append(WithBody(item, body))
    outcome = summarize(find_charge_matches(evidence_items=enriched, transactions=transactions))
    print("\n=== charge-match accounting over the store ===")
    for key, value in outcome.items():
        print(f"  {key}: {value}")

    # Show the links themselves. Precision is the whole point of the date requirement, so a
    # count is not enough — the actual receipt-to-charge pairs must be inspectable before
    # anything is written to the live store.
    by_id = {t.id: t for t in transactions}
    print("\n=== links this batch WOULD create (receipt -> charge) ===")
    shown = 0
    for item in repo.list_items(source_kind="mail", limit=100000):
        for link in repo.list_links(item.id):
            if link.target_kind != "transaction":
                continue
            tx = by_id.get(link.target_id) or by_id.get(int(link.target_id) if str(link.target_id).isdigit() else -1)
            amount = f"${abs(float(tx.amount)):.2f}" if tx else "(charge not in range)"
            when = (tx.occurred_at or "")[:10] if tx else ""
            shown += 1
            print(
                f"  {amount:>9}  {when}  {(item.title or '')[:44]}\n"
                f"             -> charge {link.target_id}  [{link.provenance}]"
            )
    print(f"  total transaction links in the store: {shown}")

    if not args.apply:
        print(f"\nDRY RUN complete; nothing written to {live_db}.")
        print("Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
