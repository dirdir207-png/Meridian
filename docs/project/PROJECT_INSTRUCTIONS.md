# Enhanced SimpleCrew — Project Instructions

Repository: `dirdir207-png/SimpleCrew`.

Treat the approved design spec and implementation plan as authoritative over informal chat history. Protect `main`: perform all changes on feature branches and merge only through reviewed pull requests. Use the Superpowers workflow, including test-first implementation, verification, and review checkpoints.

For any Virgil, voice, iOS/Shortcuts, native-device action, proactive-notification, or Meridian-to-Harness interface work, read `docs/virgil/VIRGIL_ROADMAP_ADDENDUM.md` before selecting a slice. Follow its links to the north-star contract and repository/threat-model reconciliation, and use `VIRGIL-A0` through `VIRGIL-A5` in `docs/project/MERIDIAN_OS_TASKS.json` as dependency gates. These records route work; they do not grant financial authority, deployment approval, device enrollment, or provider/configuration changes.

Keep all Crew bearer tokens, session tokens, cookies, OTPs, and money-movement credentials server-side or in approved local secure storage. Never expose them to browser code, Base44 frontend code, logs, generated documentation, or source control. Never automatically retry a financial mutation; uncertain transfer outcomes require reconciliation before another attempt.

At the end of each engineering session, update `docs/project/CURRENT_STATUS.md` with the branch, commits, tests, decisions, blockers, and next action. Do not overwrite unrelated files or undocumented user changes.
