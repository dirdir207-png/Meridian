"""The coverage matrix must not be able to lie by omission.

The whole point of the matrix is that a concept cannot be quietly dropped. That only
holds if something checks it, so these tests assert:

1. the matrix covers exactly the concepts in the builder prompt's product vision -
   anchored to the SOURCE list, not to the matrix's own idea of what the list is. A
   concept the roadmap forgot stays forgotten otherwise, and the check returns green.
2. every state comes from the fixed vocabulary, so "done" cannot be typed loosely.
3. every row that claims built/accepted state cites evidence.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "docs/project/MERIDIAN_INITIAL_BUILDER_PROMPT.md"
MATRIX = ROOT / "docs/project/CONCEPT_COVERAGE.md"

STATES = {
    "not-started",
    "substrate-only",
    "built-unwired",
    "built-wired",
    "built-visible",
    "accepted",
    "gated",
}
CLAIMING_STATES = {"built-unwired", "built-wired", "built-visible", "accepted"}


def source_concepts() -> list[str]:
    """The 22 concepts, read from the governing prompt rather than retyped here."""
    text = PROMPT.read_text()
    start = text.index("Evaluate—not automatically implement—the following possible capabilities:")
    end = text.index("Classify each concept as:")
    concepts = []
    for line in text[start:end].splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        name = line[2:].strip().rstrip(";.").strip()
        if name.startswith("and "):
            name = name[4:]
        concepts.append(name)
    return concepts


def matrix_rows() -> list[tuple[int, str, str, str]]:
    """(number, concept, state, evidence) for every data row."""
    rows = []
    for line in MATRIX.read_text().splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        number, concept, _slice, state, evidence = cells[0], cells[1], cells[2], cells[3], cells[4]
        rows.append((int(number), concept, state.strip("`"), evidence))
    return rows


def test_source_has_twenty_two_concepts() -> None:
    assert len(source_concepts()) == 22, source_concepts()


def test_matrix_covers_exactly_the_source_concepts() -> None:
    """Anchored to the prompt: a dropped or renamed concept fails here."""
    expected = set(source_concepts())
    actual = {concept for _, concept, _, _ in matrix_rows()}
    assert actual == expected, {
        "missing from matrix": sorted(expected - actual),
        "not in source list": sorted(actual - expected),
    }


def test_matrix_is_numbered_one_to_twentytwo_without_gaps() -> None:
    numbers = [n for n, _, _, _ in matrix_rows()]
    assert numbers == list(range(1, 23)), numbers


@pytest.mark.parametrize("row", matrix_rows(), ids=lambda r: f"{r[0]:02d}")
def test_every_state_is_from_the_fixed_vocabulary(row: tuple[int, str, str, str]) -> None:
    _, concept, state, _ = row
    assert state in STATES, f"concept {concept!r} has unknown state {state!r}"


@pytest.mark.parametrize("row", matrix_rows(), ids=lambda r: f"{r[0]:02d}")
def test_claimed_state_cites_evidence(row: tuple[int, str, str, str]) -> None:
    """A row asserting real existence must name what proves it."""
    _, concept, state, evidence = row
    if state in CLAIMING_STATES:
        assert len(evidence) > 12 and evidence not in {"-", "—"}, (
            f"concept {concept!r} claims {state!r} without citing evidence"
        )


def test_every_concept_has_an_owning_slice() -> None:
    """No concept may be orphaned: each names the slice that carries it."""
    for line in MATRIX.read_text().splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        assert len(cells) >= 6, line
        assert cells[2], f"concept {cells[1]!r} has no owning slice"
