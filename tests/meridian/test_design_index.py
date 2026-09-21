"""Every design record must be NAMED in design/README.md, or the index cannot answer D-004.

D-004 requires visual work to begin by establishing which record governs: *"The newest explicit
governing visual design takes precedence over historical screenshots and intermediate captures.
Confirm current authority before visual work."* `design/README.md` is where that is answered.

**Why this exists.** On 2026-09-21 that README listed TWO of the FIVE records in the tree. The three
it omitted were the LOGO set and the two NEWEST records -- the 09-19 sun study and the 09-21
medallion handoff that D-018 scopes, which is itself Phase 3 work (OS-082). So the index pointed at
the oldest material and said nothing about the newest, while five docs elsewhere already cited the
unlisted records. An index that omits the newest records is worse than no index: it answers "confirm
current authority" WRONGLY rather than declining to answer it, and a reader following it would do
visual work against a superseded direction.

The check is deliberately structural -- every directory in `design/` must be named somewhere in the
README -- so it cannot be satisfied by editing a description while a record goes unlisted.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "design"
README = DESIGN / "README.md"


def test_every_design_record_is_named_in_the_index():
    records = sorted(path.name for path in DESIGN.iterdir() if path.is_dir())
    assert records, "the design tree contains no records, which cannot be right"
    readme = README.read_text(encoding="utf-8")
    missing = [name for name in records if name not in readme]
    assert not missing, (
        f"{len(missing)} design record(s) exist but are not named in design/README.md, so it cannot "
        f"answer which record governs a surface: {missing}"
    )


def test_the_index_check_is_reading_a_real_index():
    """Guards the guard: a README that had been emptied or renamed would make the check vacuous."""
    readme = README.read_text(encoding="utf-8")
    assert "D-004" in readme, "the index no longer states the precedence rule it exists to serve"
    assert "observatory-drafts-2026-09-08" in readme, "the index lost its oldest record"
