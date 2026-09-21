# Medallions and Investigator — DeepSeek implementation handoff

Prepared 2026-09-21. Design deliverables, not a deployed feature.

## Owner scope and basis

Owner selected OS-038's medallion artwork and a user-facing Investigator; explicitly excluded desktop Settings. Owner authorized creating finished artwork here and allowed the full icon pack to be omitted. Owner asked to leave room for cross-references because substantial evidence work was completed yesterday. The five-hour constraint concerns this Codex subscription's usage window, **not a five-hour engineering deadline**.

Source inspected at `1b2bfea` through `331c28f` on `feat/meridian-implementation`; another builder advanced HEAD during preparation. Reconcile fresh source and claims before implementation. Basis: `AGENTS.md`, `docs/project/{HANDOFF,PROJECT_INSTRUCTIONS,MERIDIAN_ROADMAP,MERIDIAN_DECISIONS,MERIDIAN_OS_TASKS,CURRENT_STATUS,AGENT_COORDINATION}.md` (task ledger is `.json`), `artifacts/astra-fidelity-review-2026-09-16/README.md`, `design/observatory-drafts-2026-09-08/BUILD_SPEC.md`, the Accounts concept and 09-18 Review concept. The roadmap/ledger checker passed during preparation. Historical status statements are not new live verification.

Assigned roadmap order, as quoted by HANDOFF: “close Track D's remainder (`OS-038` design gaps, `OS-049` browser baseline), then build **Track I.1** — the envelope *and its permissions* ... then one useful, evidence-backed role (I.2).” The fresh source already implements the envelope, Investigator, run records, and council work. This handoff follows the owner's explicit selection of the remaining artwork and customer-facing surface; it does not restart those delivered backend tasks. OS-038 remains open until integration and visual acceptance. The Investigator surface is recorded as OS-076, linked to OS-073; do not redefine OS-073's CLI acceptance retroactively.

The active builder claims `meridian/ai/**`; coordinate any required evidence-payload change with that lane. This package edits no backend, route, template, stylesheet or live data.

## Deliverables

- `compass-medallion.png`: lilac/brass rim, indigo field, engraved compass rose.
- `wifi-medallion.png`: mint/brass medallion with engraved indigo Wi-Fi mark.
- `assets.json`: original dimensions, hashes and provenance. Both masters are RGBA PNGs with transparent corners.
- `prompts.json`: exact generation prompts and tool provenance.
- `investigator.html`: interactive, synthetic design specimen. Open via a static server. It makes no network/model requests and uses explicitly labeled scripted responses.
- `IMPLEMENTATION.md`: concrete integration boundaries, proposed request contract and acceptance cases.

These are **newly authored concept-inspired raster assets**, made using built-in ImageGen on owner instruction. They are not original concept extractions, exact tracings, a newly supplied SVG pack, or evidence of a particular model called Astra. The compass and Wi-Fi pixels were visually inspected. They are more dimensional than the concept's small painted glyphs; approve their appearance at actual display size before replacing production art.

## Artwork integration

The two images are complete medallions, including rings and center glyphs. Replace the whole decorative medallion in the chosen location; do not stack them over the existing frame or recolor them with a CSS mask. Preserve the existing text label and accessible name; use empty alt text when the adjacent label conveys the meaning. Do not use artwork as an account-type classifier.

Keep the current row layout and connector anchors. Match the **visible disc** size, not the PNG canvas: these masters include transparent padding. Inspect at 56 and 64 CSS-pixel disc sizes in both themes and on the owner phone viewport. Keep the masters; create measured delivery derivatives during integration using the project's normal asset process. Review anti-aliased edges on both parchment and indigo. Do not repeatedly regenerate the art to solve CSS sizing.

The Wi-Fi mark matches the visual concept, but `BUILD_SPEC.md` warns that Wi-Fi does not semantically mean “bill reserve.” Preserve explicit account labels, and only place it where that visual mapping is deliberately accepted. This handoff does not silently change account semantics. The emergency-fund star and full 61-icon pack are outside this small artwork delivery.

## Investigator product design

**Entry:** Activity transaction details → “Investigate”. Keep the existing inspector's desktop rail / mobile sheet rather than opening a second modal. Put the entry near the transaction summary; investigating expands its own section and retains a compact merchant/date/amount anchor.

**Question:** a labeled multiline “What would you like to understand?” field. Example suggestions populate the field without submitting: “What explains this charge?”, “Why did the amount change?”, “Does this match a bill?” A separate collapsed “Add what you know” field allows clarification. It is explicitly owner-provided context, not independently verified evidence.

**Scope:** “Include related evidence” is initially on, meaning existing verified relationships around this record. Display the sources considered, why each was included, observation time, and any missing content. Turning it off narrows to directly linked evidence. This is a local read scope; it does not launch new ingestion, cross-account searches, a browser agent or a bank operation.

**Result order:** (1) concise answer, (2) unresolved conflicts if present, (3) evidence-backed findings with source links, (4) assumptions and the owner's clarification, (5) “What would change this answer?”, (6) expandable run details. Use “Not enough evidence” and a concrete missing fact when support is absent. Avoid a numeric confidence badge in the main reading path: model confidence is not a measured probability. If shown in run details, label it as the model's assessment.

**Iterate:** retain the submitted question and context, let the owner edit either, and run explicitly again. Keep an older answer visibly labeled “Previous answer — question changed” until replaced, or collapse it. Never relabel an old result as the answer to the new question. Switching transaction or closing the panel invalidates pending UI results. Request cancellation cannot promise cancellation of an already-started model call.

**Input changes the answer** means question, owner clarification and scope actually enter the request and evidence selection; not that a model must invent a different answer for every rewording. Source-supported uncertainty is a valid changed outcome. Clarification may change the interpretation while remaining an unverified owner statement.

## Existing evidence work to preserve

Read OS-067/OS-068 and CURRENT_STATUS's evidence-recovery section before implementing. Existing work includes content-first encrypted blob persistence, readable missing-content pages, and amount-plus-corroborating-date receipt matching in `meridian/gmail_intake.py`. The owner declined a broad missing-blob backfill; this surface must not repeat it. Do not reuse an older amount-only reconciliation path as though it proves a match.

Cross-reference through `EvidenceRepository.list_links_for_target()` and `list_links()`, verified transaction/commitment relationships, and already available observation/calendar read models where relevant. Reuse a newer evidence service if the active builder has supplied one. Preserve relation and provenance, deduplicate, bound traversal, and show truncation. A suggested/fuzzy link is a candidate, not corroboration. A same-amount or same-merchant record alone is not a match. Missing/revoked/expired/deleted content cannot become an invented fact. Calendar presence and relevance do not prove a charge occurred.

**Important discovered gap:** at the inspected source, `EvidenceBoundRole._prompt_payload()` sends evidence ID, provenance, observed time and freshness, but no document facts. Merely wiring the UI to that implementation cannot explain a bill. This is an integration prerequisite, not a reason to discard yesterday's evidence work. Have the builder expose a small, source-attributed, read-only fact bundle from the existing evidence pipeline and pass it through the Investigator's existing context hook. Keep full raw documents and credentials out of model payloads. Tests must prove useful source facts reached the model, not only that an ID was cited. Citation validation proves membership, not that a claim is supported by its cited content.

## Visual direction and limits

Use existing Observatory typefaces, parchment/indigo surfaces, lilac section accents, brass separators and orange primary action. The specimen illustrates hierarchy and interaction, not a new site-wide token system. No new mascot, navigation tab, Settings redesign, autonomous council, financial action buttons, provider setup flow or chat transcript store.

The UI specimen's synthetic internet bill ($60 current, $48 prior, $12 equipment line) is invented test data. Nothing in this package describes the owner's account. The prototype does not demonstrate a live model, evidence retrieval, authentication or production integration.

## Harness launch instruction

Read this file and `IMPLEMENTATION.md`, reconcile the current claims and governing sources, then implement one bounded vertical slice at a time. Reuse current evidence services and source provenance. Treat prototype layout details as guidance; adjust integration details where fresh source justifies it and record material differences. Preserve the owner's two selected deliverables, editable-input behavior and cross-reference capability. Do not fabricate a completed integration, live acceptance, artwork provenance or missing evidence.

Finish with explicit implemented / tested / deployed / verified status, commit and exact commands. Update the task ledger evidence, CURRENT_STATUS and coordination log; run the roadmap checker and regenerate HANDOFF. Production deployment and live acceptance remain separately gated. Backend changes require a preview restart; say so in the delivery.
