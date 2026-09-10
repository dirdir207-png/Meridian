"""Pure validation for the governing Meridian visual capture contract."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

CAPTURE_MATRIX = {
    "desktop": {"width": 1440, "height": 900, "dpr": 1},
    "tablet": {"width": 1024, "height": 768, "dpr": 1},
    "mobile": {"width": 430, "height": 932, "dpr": 3},
    "mobile-small": {"width": 390, "height": 844, "dpr": 3},
}
THEMES = ("light", "dark")


@dataclass(frozen=True)
class CaptureMetadata:
    concept_path: str
    current_path: str
    viewport: str
    theme: str
    fixture: str
    frozen_clock: str
    ui_state: str
    full_page: bool
    commit: str
    captured_at: str
    dpr: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_metadata(metadata: Mapping[str, Any]) -> None:
    required = {field for field in CaptureMetadata.__dataclass_fields__}
    missing = required - metadata.keys()
    if missing:
        raise ValueError(f"capture metadata missing: {', '.join(sorted(missing))}")
    viewport = metadata["viewport"]
    if viewport not in CAPTURE_MATRIX:
        raise ValueError(f"unsupported viewport: {viewport}")
    if metadata["theme"] not in THEMES:
        raise ValueError(f"unsupported theme: {metadata['theme']}")
    if metadata["dpr"] != CAPTURE_MATRIX[viewport]["dpr"]:
        raise ValueError("capture DPR does not match the governing viewport matrix")
    if not isinstance(metadata["full_page"], bool):
        raise ValueError("full_page must be boolean")
    for field in ("concept_path", "current_path", "fixture", "frozen_clock", "ui_state", "commit", "captured_at"):
        if not isinstance(metadata[field], str) or not metadata[field].strip():
            raise ValueError(f"capture metadata field must be non-empty: {field}")


def required_matrix() -> tuple[tuple[str, str], ...]:
    return tuple((viewport, theme) for viewport in CAPTURE_MATRIX for theme in THEMES)
