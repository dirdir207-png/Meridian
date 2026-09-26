# Crew reserve projection shape capture

Captured read-only from the owner's already-authenticated Crew app on 2026-09-26.

The capture proxy recorded only the GraphQL operation text and a structural response
shape. It did not save authorization headers, cookies, variables, raw response values,
HAR/flow files, account identifiers, bill identifiers, or balances.

Observed operation: `AutopilotReserveProjectionScreen`.

Observed response: HTTP 200, zero GraphQL errors, 451 projection rows, 132 rows with
multiple events, nondecreasing row dates, row amounts equal to the sum of event amounts,
running balances reconciling to `openingBalance`, `firstNegative` matching its first
negative row, and `lowPoint` matching the minimum row balance.

The historical OS-130 record cited 452 rows. That difference remains an explicit
capture-to-capture discrepancy; it is not silently normalized. The captured shape
establishes field names and nesting, but not the provider's numeric unit scale.

Files: `AutopilotReserveProjectionScreen.graphql` and `capture-shape.json`.

No provider mutation, reserve top-up, bill edit, deployment, or application-code change
was performed for this capture.
