# Meridian Visual Capture Specification

**Status:** Governing capture contract for visual-fidelity work.

## Capture matrix

| Class | CSS viewport | DPR | Themes |
|---|---:|---:|---|
| Desktop | 1440×900 | 1 | light, dark |
| Tablet | 1024×768 | 1 | light, dark |
| Mobile | 430×932 | 3 | light, dark |
| Mobile-small | 390×844 | 3 | light, dark |

## Determinism contract

- Explicitly set the theme; never rely on OS defaults.
- Disable animations, transitions, and reduced-motion effects.
- Wait for `document.fonts.ready`.
- Wait for network idle and all Meridian API/data requests to settle.
- Use deterministic synthetic seed records, never live bank data.
- Freeze the clock to a fixed test date/time.
- Disable polling, timers, and auto-refresh during capture.
- Lock workspace, selected record, proposal state, connection state, and scroll position.
- Use the same viewport and `fullPage` setting for a given comparison.
- Capture both the initial viewport and any explicitly defined full-page artifact.

## Responsive acceptance

At minimum, verify 390×844, 430×932, and 1440×900 in both light and dark themes. The 1024×768 tablet capture is required for the full matrix.

## Artifact metadata

Every capture set must record concept path, current path, viewport, DPR, theme, fixture/seed identifier, frozen clock, UI state, `fullPage`, commit, and capture date. Generate side-by-side and overlay/difference artifacts where tooling permits. Compare only matching dimensions and state. Live-data validation is a separate track from concept-fidelity validation.

## Completion rule

Visual parity is not complete until the capture harness enforces this contract and the required matrix has fresh evidence. Existing screenshots are historical unless regenerated under this specification.

## Harness implementation

The pure contract validator lives in `tests/browser/capture_contract.py`. It encodes the four viewport/DPR pairs, light/dark themes, and required deterministic metadata fields. `tests/test_capture_contract.py` protects the matrix and rejects incomplete or mismatched capture records.
