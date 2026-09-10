# Meridian Operating System Architecture

## Status

Draft foundation for owner review. This document does not grant financial authority or approve production deployment.

## Direction

Meridian evolves in layers: financial mirror → interpreter → simulator → adviser → constrained operator → constitutional guardian → personal economic operating system. Intelligence and authority remain separate.

## Recommended architecture

Prefer a modular extension of the existing Meridian repository first. Introduce immutable observations and typed domain services inside the current Flask/SQLite application before extracting an event or agent service. Extract only when operational or security boundaries justify it.

Core boundaries:

- **Providers:** read and normalize external data; preserve source provenance.
- **Observation store:** immutable provider observations with observed-at, source-updated-at, freshness, confidence, and assumptions.
- **Financial read model:** current derived views; never overwrite historical observations.
- **Simulation:** isolated, reproducible scenario projections; cannot write real financial state.
- **Policy:** evaluates constitution and action plans; does not execute mutations.
- **Agents:** observe/reason/propose through structured outputs; no direct mutation authority.
- **Executor:** sole constrained mutation path using proposal → approval → execution → provider readback verification.
- **UI:** exposes actual, stale, inferred, simulated, and proposed states distinctly.
- **Audit:** records evidence, assumptions, decisions, approvals, executions, verification, and failures.

## Sequence

1. Reconcile governing documents and current code.
2. Add the read-only observation/digital-twin substrate.
3. Add scenario simulation with explicit assumptions and confidence.
4. Add constitution and policy evaluation.
5. Add proactive event grouping and financial weather.
6. Add evidence-backed explanations and investigations.
7. Add specialized agents behind structured interfaces.
8. Improve controlled operations and consolidated approvals.
9. Add sandboxed Builder proposals; installation and deployment remain owner-gated.

## Non-goals for the initial slice

No autonomous external transfers, automatic subscription cancellation, self-deploying code, live connector repair, agent council, household integrations, or authority-policy activation.
