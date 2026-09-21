# Meridian Substrate Inventory

## Executive summary
- **Scope:** read-only inventory of `feat/meridian-implementation`; no app, migration, or database was run/read.
- **Architecture:** Flask `app.py` remains a large legacy monolith beside layered Meridian APIs/services/repositories.
- **Read path:** Crew preview sync uses `meridian.live` and the configured `crew-readonly` CLI.
- **Write path:** proposals/actions use Crew action storage and constrained executors; verification varies by operation.
- **Schema:** migrations 001–021 cover normalized finance, commitments/funding, classification, evidence/context/assets, connections, trials/cancellation, observations, and absence reconciliation.
- **Providers:** Crew/CrewWork are wired; SimpleFin, LunchFlow, and Splitwise adapters are implemented/tested but no active Meridian registration was found.
- **UI:** Meridian shell, Today, Plan, Activity, Accounts, Settings, dial, memory, trials, and review surfaces exist beside legacy pages.
- **Tests:** broad unit coverage exists; browser tests are commonly skip-gated by `APP_URL`.
- **Largest substrate gap:** evidence/document/context capabilities have modules and migrations, but active ingestion and end-to-end reachability are uneven.
- **Authority note:** consolidated handoff says Observatory designs are proposed/not shipped, while CURRENT_STATUS claims slices complete; source reachability is decisive.

Confidence: **HIGH** = directly source-confirmed; **MEDIUM** = static import/search inference; **LOW** = unresolved.

## A. Module inventory

| Path | Purpose | Main public entry points | Wired into running app? | State | Confidence |
|---|---|---|---|---|---|
| `meridian/__init__.py` | Meridian's provider-neutral financial data layer. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/ai/__init__.py` | Provider-agnostic AI services for Meridian. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/ai/advisor.py` | Evidence-bound contextual advisor for Meridian workspaces. | UnsupportedAdvisorClaim, AdvisorContext, MeridianContextBuilder, ContextualAdvisor | yes (direct/imported path) | partial/stub candidates | HIGH |
| `meridian/ai/classifier.py` | Structured AI fallback for transactions unresolved by deterministic rules. | AIClassifier, classify_with_ai_fallback | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/api.py` | Stable, authenticated HTTP read models for Meridian. | _repository, _evidence_repository, _evidence_blob_store, _connection_repository, _evidence_payload, _plan_repositories, _error, _safe_read, _account_payload, _account_labels, _transaction_payload, _transaction_payload_with_suggestion, _positive_int, observations | yes (direct/imported path) | implemented | HIGH |
| `meridian/assets.py` | Evidence-backed asset and warranty memory with proposal-only corrections. | _now, Asset, Warranty, MemoryEvent, CorrectionProposal, AssetRepository, asset_events | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/beacon.py` | Explainable deterministic cash runway forecasts for Meridian. | ForecastFactor, ForecastShortfall, Forecast, _commitment_amount, _date, forecast | yes (direct/imported path) | implemented | HIGH |
| `meridian/billers.py` | Read-only Biller Monitor (R33). | MonitorBill, _date_of, _next_due, _advance, _merchant_match, _last_paid, _funded_status, _days_until, build_biller_monitor, bill_status_for | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/__init__.py` | Conservative cancellation workflow primitives. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/adapters.py` | Explicitly inert adapter implementations for integration and dry-run tests. | DryRunAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/approval.py` | Explicit approval gate for cancellation submissions. | ApprovalDecision, evaluate_submission | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/brief.py` | Deterministic human hand-off brief for trials that need owner action. | build_cancellation_brief | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/capture.py` | Strict checkout/receipt capture adapter for creating trial records. | capture_trial | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/deadlines.py` | Read-only deadline projection for UI and future notification schedulers. | upcoming_deadlines | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/escalation.py` | Deterministic escalation planning; this module never sends or disputes. | EscalationStep, build_escalation_plan | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/executor.py` | Provider adapter boundary; no provider call is made by the default implementation. | CancellationAdapter, ExecutionResult, execute_approved | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/notification_payload.py` | Safe notification payloads for an owning delivery channel. | TrialReminderPayload, build_trial_reminder_payload | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/notifications.py` | Durable, idempotent reminder materialization for trial deadlines. | TrialNotification, TrialNotificationRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/recipes/__init__.py` | Provider cancellation recipes. Unverified recipes are never executable. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/recipes/catalog.py` | unknown | Recipe, _normalize, load_catalog, match_recipe | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/reconcile.py` | Post-deadline billing verification using Meridian's transaction read model. | verify_post_deadline_billing | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/replay.py` | Deterministic end-to-end cancellation workflow replay against a stub adapter. | ReplayResult, replay_stubbed_cancellation | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/repository.py` | Durable cancellation attempts; provider adapters remain outside this store. | CancellationAction, CancellationRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/cancellation/scheduler.py` | Small scheduler seam for trial reminders. | run_reminder_cycle | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/cancellation/workflow.py` | Action -> verify -> escalate state machine for subscription cancellation. | CancellationState, VerificationSignal, RoutingResult, advance, verification_status, route_cancellation, status_for_transition | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/classify.py` | Pure deterministic transaction classification with explicit precedence. | ClassificationInput, AssignmentRule, Classification, _matches, _date, _is_monthly, classify_deterministic | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/commitments.py` | Unified Commitment domain: typed financial intentions over Crew pockets. | CommitmentType, CommitmentStatus, Commitment, _now, _as_money, _require_positive, CommitmentRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/connection_jobs.py` | R26: resumable per-account mail/calendar ingestion cursors + revocation. | _now, IngestionCursorStore, ResumableIncremental | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/connections.py` | Sanitized metadata for user-controlled external connections. | ConnectionState, ConnectionRecord, public_connection_id, _now, ConnectionRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/connectors/__init__.py` | Read-only external evidence connectors. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/connectors/calendar.py` | Bounded, minimum-field, read-only calendar ingestion. | CalendarTransport, CalendarEvent, CalendarBatch, ReadOnlyCalendarConnector | yes (direct/imported path) | implemented | HIGH |
| `meridian/connectors/email.py` | Minimum-scope, cursor-based read-only mail ingestion. | MailTransport, MailAttachment, MailMessage, MailBatch, ReadOnlyMailConnector | yes (direct/imported path) | implemented | HIGH |
| `meridian/connectors/gmail_read.py` | Real read-only Gmail transport for evidence intake (R28/29). | GmailReadError, GmailEvidence, _decode_body, _headers, GmailTransport | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/connectors/google_auth.py` | Google OAuth 2.0 transport for read-only Gmail/Calendar (R25). | CredentialError, _now, GoogleOAuthConfigError, GoogleOAuthConfig, GoogleOAuth2Client, OAuthTokenStore, _quote, callback_redirect_uri, email_from_id_token | yes (direct/imported path) | implemented | HIGH |
| `meridian/connectors/icloud_mail.py` | Read-only iCloud Mail transport for evidence intake. | IcloudMailReadError, IcloudMailMessage, _decode_header_value, _decode_body, _imap_date, IcloudMailTransport | no/unknown (no direct app reference found) | partial/stub candidates | MEDIUM |
| `meridian/context.py` | Opt-in contextual signals and explicitly bounded scenario assumptions. | _now, ContextSignal, Assumption, ContextRepository, scenario_assumptions | yes (direct/imported path) | implemented | HIGH |
| `meridian/contracts.py` | Evidence-backed contract facts without professional determinations. | _now, Contract, Obligation, ContractEvent, AdvisoryBoundary, ContractRepository, contract_events, advisory_boundary | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/crew_commands.py` | Validated, provider-specific command payloads for Meridian proposals. | CommandSpec, command_spec, _cents, build_command_payload, _build_roundup_formula, _build_formula_from_payload | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/crew_write.py` | Crew write-back executor (personal-use). | CrewWriteBlocked, CrewWriteUncertain, execute_crew_write | yes (direct/imported path) | implemented | HIGH |
| `meridian/crew_write_actions.py` | Crew write-back executors for the proposal→approval→execute pipeline. | _crew_write_executor, _verify_stored, _verify_crew_bill_readback, crew_write_executors, _bill_record, _reviewed_values, capture_base_state, _bill_precondition, crew_write_preconditions | yes (direct/imported path) | implemented | HIGH |
| `meridian/db.py` | Versioned SQLite migrations for Meridian. | _canonicalize_transaction_timestamps, _migration_files, _statements, _checksum, _validate_migration_history, run_migrations | yes (direct/imported path) | implemented | HIGH |
| `meridian/deposit_discovery.py` | R24: deposit discovery over the canonical transaction graph. | DepositCandidate, DepositDiscovery, _confidence_from_description, discover_deposits, _parse_date | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/documents/__init__.py` | Safe deterministic financial-document processing. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/documents/extract.py` | Deterministic text-first extraction with line-level provenance. | Provenance, ExtractedValue, ExtractedDocument, _text_from_blob, _document_type, extract_document | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/documents/reconcile.py` | Deterministic document reconciliation against normalized transactions. | DocumentMatch, DocumentDiscrepancy, DocumentProposal, DocumentReconciliation, _document_amount, _merchant_score, reconcile_document | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/documents/safety.py` | Attachment validation performed before storage or parsing. | MalwareScanner, ValidationResult, _sanitize_filename, _detected_mime, validate_attachment | yes (direct/imported path) | implemented | HIGH |
| `meridian/evidence.py` | Auditable metadata and provenance links for encrypted financial evidence. | _now, EvidenceItem, EvidenceLink, EvidenceRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/funding.py` | Pure funding-rule projections. | FundingRule, FundingEvent, FundingProjection, _money, _monthly_dates, _cadence_dates, _commitment_target, _commitment_deadline, _clamp_to_caps, project_funding, _cash_balance_lookup, _even_by_date_dates | yes (direct/imported path) | implemented | HIGH |
| `meridian/funding_proposals.py` | Turn due funding events into idempotent, approval-only proposals. | _dedup_key, _rationale, propose_due_funding | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/funding_repo.py` | Persistence for funding rules (local planning metadata; never Crew state). | _now, _money, FundingRuleRepository | yes (direct/imported path) | implemented | HIGH |
| `meridian/gmail_intake.py` | Gmail -> evidence intake runner (R28/29 pilot). | _date_days_ago, ingest_gmail_recent, ingest_all_gmail_accounts, link_mail_evidence_to_transactions, ingest_icloud_recent | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/ingest.py` | R28/R29: document intake pipeline — mail/manual blob → extraction → evidence. | _now, QuarantineError, IntakeResult, IntakeRecord, ingest_record | no/unknown (no direct app reference found) | partial/stub candidates | MEDIUM |
| `meridian/live.py` | Live Crew snapshot collector for automatic refresh. | capture_crew_snapshot, sync_live_crew, build_sync_once | yes (direct/imported path) | implemented | HIGH |
| `meridian/memory_actions.py` | Pipeline executors and verifiers for asset/contract management. | _asset_from_params, _merge_asset, _contract_from_params, _merge_contract, _warranties_from_params, _obligations_from_params, _persist_warranties, _persist_obligations, _link_evidence, asset_executors, contract_executors | yes (direct/imported path) | implemented | HIGH |
| `meridian/migrate_legacy.py` | Non-destructive migration of legacy pocket records into Commitments. | MigrationPreview, MigrationReport, _now, _debt_linked_pocket_ids, _decide_account, preview_legacy_migration, _persist_preview, _load_preview, apply_legacy_migration, resolve_review | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/models.py` | Immutable, JSON-safe records returned by the Meridian repository. | AccountRecord, ArchivedAccountRecord, TransactionRecord | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/mutations.py` | Write-through reconciliation helpers for confirmed Crew mutations. | reconcile_crew_mutation | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/observations.py` | Append-only, credential-free provider observations for the Meridian digital twin. | ObservationObject, ObservationRecord, ActualSnapshot, SimulationInput, build_simulation_input, _now, _canonical, _digest, _account_payload, _transaction_payload, ObservationRepository, record_provider_snapshot | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/paycheck.py` | Configurable paycheck (funding source) for per-bill funding projections. | PaycheckConfig, _now, PaycheckRepository, _next_after, future_paycheck_events, build_cash_events | yes (direct/imported path) | implemented | HIGH |
| `meridian/paycheck_learning.py` | Self-learning paycheck detection over real income transactions. | _parse_date, _is_income, _cadence_guess, learn_paycheck, _period_delta | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/payday.py` | Conservative, deterministic recognition of recurring payday evidence. | PaydayPattern, _transaction_date, _next_monthly, _next_semimonthly, recognize_payday | yes (direct/imported path) | implemented | HIGH |
| `meridian/policy.py` | Read-only constitution evaluation; this module never executes actions. | Constitution, ActionPlan, PolicyDecision, evaluate_constitution | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/proactive.py` | Read-only proactive layer: grouped meaningful events and financial weather. | MeaningfulEvent, EventGroup, FinancialWeather, _parse_date, _is_amount, _available_minor, _meaningful_event, _event_explanation, _format_amount, _group, _total_label, build_financial_weather | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/providers/__init__.py` | Read-only provider adapters for Meridian's financial graph. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/providers/base.py` | Provider-neutral, credential-free snapshots used by Meridian syncs. | NormalizedAccount, NormalizedTransaction, ExpectedInflow, CommitmentCandidate, ProviderSnapshot, ProviderAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/providers/crew.py` | Read-only Crew adapter that emits credential-free normalized records. | CrewReadAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/providers/crewwork.py` | Read-only Meridian provider adapter for a CrewWorkAssistant snapshot. | _status, _clean_merchant, _cents_to_dollars, _cents_to_dollars_or_none, _as_dict, _as_list, CrewWorkSnapshotAdapter | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/providers/lunchflow.py` | Read-only LunchFlow normalization for Meridian. | LunchFlowAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/providers/simplefin.py` | Read-only SimpleFin normalization for Meridian. | _milliunits, SimpleFinAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/providers/splitwise.py` | Read-only Splitwise balance and shared-expense normalization. | SplitwiseAdapter | yes (direct/imported path) | implemented | HIGH |
| `meridian/reconcile.py` | Deterministic, idempotent transaction relation discovery. | ReconciliationReport, _timestamp, reconcile | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/refresh.py` | Automatic live-data refresh: periodically pull a CrewWorkAssistant snapshot | MeridianRefreshService | yes (direct/imported path) | implemented | HIGH |
| `meridian/repository.py` | Provider-neutral writes and stable reads for Meridian financial records. | SyncRun, ProviderConnectionFreshness, ProviderFreshnessScope, TransactionRelationRecord, StoredAssignmentRule, ReimbursementRecord, _available_transaction_columns, _available_account_columns, _reconciles_absence, _now, _encode_cursor, _decode_cursor, FinancialRepository, _keyword_category_guess | yes (direct/imported path) | implemented | HIGH |
| `meridian/scenarios.py` | Pure comparisons over an existing deterministic Meridian forecast. | ScenarioResult, run_scenario | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/services/__init__.py` | Read-model calculations for Meridian workspaces. | none | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/accounts.py` | Provider-neutral Accounts workspace read model. | _role, _account_view, build_accounts | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/activity.py` | Read-only Activity access backed exclusively by FinancialRepository. | get_activity, get_transaction, get_review_queue, get_patterns | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/connections.py` | Presentation-safe read models for Meridian connection settings. | FinancialConnectionSource, _authorization_payload, _financial_payload, get_connection_detail, build_connections | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/dial.py` | Read-only Observatory dial view model. | _minor, _date_of, _advance, _next_occurrence, _spend_source_account, _available_to_spend, _horizon, _commitment_events, _paycheck_events, build_dial | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/services/memory.py` | unknown | _now_iso, _evidence_entries, _source_kind_label, _urgency, _why_it_matters, _base_item, _compose_today, _compose_plan, _compose_activity, _compose_accounts, build_memory | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/payday.py` | Read-only Payday & Funding settings composed from existing Meridian data. | _rule_payload, build_payday_settings | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/plan.py` | One canonical Plan view model: summary, timeline, allocation, commitments. | _crew_ids, _money, _biller_status, _sender_host, _bill_invoice_evidence, _project_commitment, build_plan, _next_paycheck_event, _coverage_explanation, _commitment_target, _date_of, _next_occurrence, _cash_events_from_graph, _graph_freshness | yes (direct/imported path) | implemented | HIGH |
| `meridian/services/today.py` | Calculations for Meridian's read-only Today workspace. | _parse_timestamp, _last_trustworthy_update, data_freshness, _currency_total, _spend_source_account, _unfunded_bill_total, _next_paycheck_inflow, _learned_paycheck_range, _build_beacon_signal, _iso_short, _build_virgil_brief, build_today, _commitment_breakdown, _setup_summary | yes (direct/imported path) | partial/stub candidates | HIGH |
| `meridian/storage.py` | Encrypted, content-addressed storage for financial evidence blobs. | KeyProvider, BlobDecryptionError, StoredBlob, EncryptedBlobStore, DerivedKeyProvider | yes (direct/imported path) | partial/stub candidates | HIGH |
| `meridian/sync.py` | Idempotent synchronization of provider snapshots into Meridian. | SyncReport, sync_provider, sync_providers, _relation_type_for_hint, _reclassify_relations | yes (direct/imported path) | implemented | HIGH |
| `meridian/sync_gate.py` | Cadence gate for safe, read-only provider-to-Meridian synchronization. | MeridianSyncGate | yes (direct/imported path) | implemented | HIGH |
| `meridian/timestamps.py` | Canonical timestamp handling shared by writes, cursors, and migrations. | canonical_occurred_at | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `meridian/trials.py` | Local trial ledger and conservative deadline calculations. | _parse, _iso, Trial, TrialRepository, deadline_events | yes (direct/imported path) | implemented | HIGH |
| `meridian/write_routing.py` | Route a requested Meridian mutation to DIRECT execution or a PROPOSAL. | Provenance, RoutingDecision, classify_action, route_mutation, route_many, _coerce_provenance, _under_specified, _flags_low_confidence, _flags_multi_op, reroute_direct_if_owner, all_provenances | yes (direct/imported path) | implemented | HIGH |
| `crew/__init__.py` | unknown | none | yes (direct/imported path) | implemented | HIGH |
| `crew/actions.py` | Durable action-proposal pipeline: propose → approve → execute → verify. | UnknownActionTypeError, IllegalTransitionError, ActionState, _now, ActionStore | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/advisor.py` | AI advisor: conversational copilot that can only PROPOSE actions. | AdvisorUnavailable, MeridianAdvisorBridge, llm_configured, llm_model, OpenAICompatClient, FailoverLLMClient, build_llm_chain, build_system_prompt, FinancialContextBuilder, AdvisorService | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/assistant.py` | Local assistant: plain-English transfer intents -> loopback proposals. | IntentParseError, parse_transfer_intent, propose_intent | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/beacon.py` | Beacon: forward-looking budget projection from balance history. | build_forecast, project_reserve | yes (direct/imported path) | implemented | HIGH |
| `crew/broker.py` | unknown | BrokerConfig, create_broker_app | yes (direct/imported path) | implemented | HIGH |
| `crew/browser_capture.py` | Local browser-based Crew credential capture for guided renewal. | _is_crew_api_url, _filter_crew_cookies, PlaywrightSessionCapturer, PlaywrightAuthorizationCapturer, create_mac_capturer | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/client.py` | unknown | CrewError, CrewAuthenticationError, CrewTransportError, CrewAPIError, CrewUncertainWriteError, _looks_like_auth_error, CrewClient | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/credentials.py` | unknown | CredentialProvider, _normalize_token, StoredBearerTokenProvider, MacCredentialProvider | yes (direct/imported path) | implemented | HIGH |
| `crew/executors.py` | Executor registry for approved actions. | ExecutorSpec, _precondition_payload, _precondition_refusal, _failure, execute_approved_action, expire_stale_approvals | yes (direct/imported path) | implemented | HIGH |
| `crew/health.py` | unknown | BrokerUnavailableError, CredentialLockedError, CrewHealthState, CrewHealth, CredentialHealthService | yes (direct/imported path) | implemented | HIGH |
| `crew/mac_secrets.py` | unknown | SecretStoreError, MacKeychainKeyProvider, load_or_create_capability | no/unknown (no direct app reference found) | partial/stub candidates | MEDIUM |
| `crew/operations.py` | Exact Crew GraphQL documents shared by command adapters and broker. | none | no/unknown (no direct app reference found) | implemented | MEDIUM |
| `crew/proposals.py` | Proposal builders for local AI/command proposers. | ProposalError, TransferResolver, _resolve, build_transfer_proposal | yes (direct/imported path) | partial/stub candidates | HIGH |
| `crew/propose_key.py` | Shared local capability key for the loopback proposal endpoint. | get_or_create_local_key, load_local_key | yes (direct/imported path) | implemented | HIGH |
| `crew/renewal.py` | Guided Crew credential renewal lifecycle. | CapturerUnavailable, RenewalStatus, _Session, _sanitize_health, sanitize_status_payload, GuidedRenewalService | yes (direct/imported path) | implemented | HIGH |
| `crew/session_credentials.py` | unknown | KeyProvider, CredentialDecryptionError, SessionCredential, EncryptedCredential, SessionCipher, SessionCredentialStore | no/unknown (no direct app reference found) | partial/stub candidates | MEDIUM |
| `crew/transports.py` | unknown | BrokerCrewTransport, SessionCookieTransport | yes (direct/imported path) | implemented | HIGH |
| `assistant.py` | CLI assistant and intent proposal entry point | `propose_intent`, `main` | yes (CLI/imported by tests) | implemented | HIGH |
| `app.py` | Flask application, legacy routes, Meridian routes, sync/action services | Flask `app`, route handlers, sync/action helpers | yes (WSGI entry point) | partial (legacy monolith plus Meridian surfaces) | HIGH |

### `app.py` section inventory (HIGH; exact anchors)

| Lines/section | Contents | Wiring |
|---|---|---|
| 1–180 | imports, Flask setup, security/no-store, evidence store, user/session setup | module startup |
| 181–348 | User loader, SimpleFin cadence/cache, cleanup helpers | app helpers |
| 349–812 | `init_db`, legacy schema setup, credential/session persistence, WebAuthn helpers | import/startup DB initialization |
| 840–918 | `sync_crew_snapshot`, `MeridianSyncGate`, `MeridianRefreshService` | active Crew refresh/sync |
| 927–1119 | funding/commitment action apply+verify, memory sink, Crew target resolution, action registration | proposal/action pipeline |
| 1132–1295 | financial snapshot, proposal sink, beacon/advisor/provider config APIs | legacy/API support |
| 1343–2950 | notifications, Crew sync bridge, legacy accounts/transactions/expenses/goals/family/cards/money movement/pockets/bills | legacy helpers and mutation paths |
| 2977–3610 | Meridian/legacy page routes, auth/register/passkeys, redirects/debug/health | active routing |
| 3636–4140+ | onboarding, Crew token/health, account/settings and remaining APIs | active/partial; exact handlers vary |

## B. Schema map

Parsed from `meridian/migrations/*.sql`; legacy tables made by `app.py:init_db` are separate. **HIGH.**

| Table | Columns/types and key constraints | Indexes/owner |
|---|---|---|
| `provider_connections` | id INTEGER PRIMARY KEY AUTOINCREMENT; provider TEXT NOT NULL; external_id TEXT NOT NULL; display_name TEXT NOT NULL; status TEXT NOT NULL DEFAULT 'unknown'; last_attempted_at TEXT; last_successful_at TEXT; created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP; updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP; UNIQUE (provider, external_id) | idx_financial_accounts_connection, idx_financial_transactions_account_order, idx_financial_transactions_order, idx_transaction_relations_source, idx_transaction_relations_related; owner `meridian/connections.py` |
| `financial_accounts` | id INTEGER PRIMARY KEY AUTOINCREMENT; connection_id INTEGER; provider TEXT NOT NULL; external_id TEXT NOT NULL; name TEXT NOT NULL; account_type TEXT NOT NULL; balance REAL NOT NULL; available_balance REAL; currency TEXT NOT NULL; is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)); source_updated_at TEXT; synced_at TEXT NOT NULL; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; FOREIGN KEY (connection_id) REFERENCES provider_connections(id); UNIQUE (provider, external_id) | idx_financial_accounts_connection, idx_financial_transactions_account_order, idx_financial_transactions_order, idx_transaction_relations_source, idx_transaction_relations_related; owner `meridian/repository.py` |
| `financial_transactions` | id INTEGER PRIMARY KEY AUTOINCREMENT; account_id INTEGER NOT NULL; provider TEXT NOT NULL; external_id TEXT NOT NULL; amount REAL NOT NULL; currency TEXT NOT NULL; occurred_at TEXT NOT NULL; posted_at TEXT; description TEXT NOT NULL; merchant TEXT; status TEXT NOT NULL; raw_description TEXT; source_updated_at TEXT; synced_at TEXT NOT NULL; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; FOREIGN KEY (account_id) REFERENCES financial_accounts(id); UNIQUE (provider, external_id) | idx_financial_accounts_connection, idx_financial_transactions_account_order, idx_financial_transactions_order, idx_transaction_relations_source, idx_transaction_relations_related; owner `meridian/repository.py` |
| `transaction_relations` | id INTEGER PRIMARY KEY AUTOINCREMENT; provider TEXT NOT NULL; external_id TEXT NOT NULL; source_transaction_id INTEGER NOT NULL; related_transaction_id INTEGER NOT NULL; relation_type TEXT NOT NULL; confidence REAL; created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP; updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP; FOREIGN KEY (source_transaction_id) REFERENCES financial_transactions(id); FOREIGN KEY (related_transaction_id) REFERENCES financial_transactions(id); CHECK (source_transaction_id <> related_transaction_id); UNIQUE (provider, external_id) | idx_financial_accounts_connection, idx_financial_transactions_account_order, idx_financial_transactions_order, idx_transaction_relations_source, idx_transaction_relations_related; owner migration consumers; exact owner unknown |
| `transaction_relations (altered in 002_financial_integrity.sql)` | source_updated_at TEXT | migration alteration; base-table owner |
| `transaction_relations (altered in 002_financial_integrity.sql)` | synced_at TEXT | migration alteration; base-table owner |
| `provider_sync_runs` | id INTEGER PRIMARY KEY AUTOINCREMENT; connection_id INTEGER NOT NULL; provider TEXT NOT NULL; status TEXT NOT NULL CHECK (status IN ('running', 'complete', 'partial', 'failed')); started_at TEXT NOT NULL; completed_at TEXT; accounts_synced INTEGER NOT NULL DEFAULT 0; transactions_synced INTEGER NOT NULL DEFAULT 0; errors INTEGER NOT NULL DEFAULT 0; FOREIGN KEY (connection_id) REFERENCES provider_connections(id) | idx_provider_sync_runs_connection_started; owner migration consumers; exact owner unknown |
| `commitments` | id INTEGER PRIMARY KEY AUTOINCREMENT; type TEXT NOT NULL CHECK (type IN ('bill', 'goal', 'reserve', 'buffer', 'debt')); name TEXT NOT NULL; status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')); priority INTEGER NOT NULL DEFAULT 3 CHECK (priority >= 1); currency TEXT NOT NULL DEFAULT 'USD'; target_amount REAL; target_date TEXT; funded_amount REAL NOT NULL DEFAULT 0 CHECK (funded_amount >= 0); amount REAL; due_date TEXT; recurrence TEXT; cadence TEXT; minimum_payment REAL; buffer_minimum REAL; payoff_strategy TEXT; backing_account_id INTEGER REFERENCES financial_accounts(id); legacy_source TEXT; legacy_id TEXT; migration_version TEXT; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; CHECK ( target_amount IS NULL OR target_amount >= 0 ); CHECK ( amount IS NULL OR amount >= 0 ); CHECK ( minimum_payment IS NULL OR minimum_payment >= 0 ); CHECK ( buffer_minimum IS NULL OR buffer_minimum >= 0 ) | idx_commitments_legacy_identity; owner `meridian/commitments.py` |
| `migration_previews` | id INTEGER PRIMARY KEY AUTOINCREMENT; preview_id TEXT NOT NULL UNIQUE; created_at TEXT NOT NULL; payload TEXT NOT NULL | idx_commitments_legacy_identity; owner migration consumers; exact owner unknown |
| `migration_review_queue` | id INTEGER PRIMARY KEY AUTOINCREMENT; preview_id TEXT NOT NULL; source_type TEXT NOT NULL; legacy_source TEXT NOT NULL; legacy_id TEXT NOT NULL; suggested_type TEXT NOT NULL; name TEXT NOT NULL; reason TEXT NOT NULL; payload TEXT NOT NULL; created_at TEXT NOT NULL; resolution TEXT; resolved_at TEXT | idx_commitments_legacy_identity; owner migration consumers; exact owner unknown |
| `funding_rules` | id INTEGER PRIMARY KEY AUTOINCREMENT; commitment_id INTEGER NOT NULL REFERENCES commitments(id); kind TEXT NOT NULL CHECK (kind IN ( 'fixed_per_paycheck', 'percent_of_paycheck', 'calendar'; 'even_by_due_date', 'priority_waterfall' )); amount REAL; percent REAL; cadence TEXT; day_of_month INTEGER; start_date TEXT NOT NULL; horizon_end TEXT; min_contribution REAL; max_contribution REAL; paused INTEGER NOT NULL DEFAULT 0 CHECK (paused IN (0, 1)); skip_dates TEXT NOT NULL DEFAULT '[]'; one_time_override REAL; priority INTEGER NOT NULL DEFAULT 3 CHECK (priority >= 1); created_at TEXT NOT NULL; updated_at TEXT NOT NULL; CHECK (amount IS NULL OR amount >= 0); CHECK (percent IS NULL OR (percent > 0 AND percent <= 100)); CHECK (min_contribution IS NULL OR min_contribution >= 0); CHECK (max_contribution IS NULL OR max_contribution >= 0); CHECK (one_time_override IS NULL OR one_time_override >= 0) | idx_funding_rules_commitment; owner `meridian/funding_repo.py`/`funding.py` |
| `transaction_classification_history` | id INTEGER PRIMARY KEY AUTOINCREMENT; transaction_id INTEGER NOT NULL REFERENCES financial_transactions(id); category TEXT NOT NULL; kind TEXT NOT NULL; confidence REAL NOT NULL; rule_id TEXT NOT NULL; evidence TEXT NOT NULL; method TEXT NOT NULL; version INTEGER NOT NULL; replaced_at TEXT NOT NULL | idx_transaction_classification_history_transaction; owner migration consumers; exact owner unknown |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_category TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_kind TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_confidence REAL | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_rule_id TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_evidence TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_method TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 007_transaction_classification.sql)` | classification_version INTEGER NOT NULL DEFAULT 0 | migration alteration; base-table owner |
| `financial_transactions (altered in 008_ai_classification_audit.sql)` | classification_provider TEXT | migration alteration; base-table owner |
| `financial_transactions (altered in 008_ai_classification_audit.sql)` | classification_model TEXT | migration alteration; base-table owner |
| `transaction_classification_history (altered in 008_ai_classification_audit.sql)` | provider TEXT | migration alteration; base-table owner |
| `transaction_classification_history (altered in 008_ai_classification_audit.sql)` | model TEXT | migration alteration; base-table owner |
| `assignment_rules` | id INTEGER PRIMARY KEY AUTOINCREMENT; category TEXT NOT NULL; kind TEXT NOT NULL; merchant_pattern TEXT; description_pattern TEXT; created_at TEXT NOT NULL; updated_at TEXT NOT NULL | none declared; owner migration consumers; exact owner unknown |
| `classification_corrections` | id INTEGER PRIMARY KEY AUTOINCREMENT; transaction_id INTEGER NOT NULL REFERENCES financial_transactions(id); category TEXT NOT NULL; kind TEXT NOT NULL; assignment_rule_id INTEGER REFERENCES assignment_rules(id); created_at TEXT NOT NULL | none declared; owner migration consumers; exact owner unknown |
| `provider_reimbursements` | id INTEGER PRIMARY KEY AUTOINCREMENT; provider TEXT NOT NULL; external_id TEXT NOT NULL; name TEXT NOT NULL; amount REAL NOT NULL CHECK (amount >= 0); currency TEXT NOT NULL; source_updated_at TEXT; synced_at TEXT NOT NULL; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; UNIQUE (provider, external_id) | idx_provider_reimbursements_provider; owner migration consumers; exact owner unknown |
| `evidence_items` | id INTEGER PRIMARY KEY AUTOINCREMENT; source_kind TEXT NOT NULL; source_id TEXT NOT NULL; content_hash TEXT NOT NULL CHECK(length(content_hash) = 64); mime_type TEXT NOT NULL; size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0); title TEXT; expires_at TEXT; revoked_at TEXT; content_deleted_at TEXT; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; UNIQUE(source_kind, source_id, content_hash) | idx_evidence_items_source, idx_evidence_items_retention, idx_evidence_links_target; owner `meridian/evidence.py` |
| `evidence_links` | id INTEGER PRIMARY KEY AUTOINCREMENT; evidence_id INTEGER NOT NULL REFERENCES evidence_items(id) ON DELETE RESTRICT; target_kind TEXT NOT NULL; target_id TEXT NOT NULL; relation TEXT NOT NULL; provenance TEXT NOT NULL; created_at TEXT NOT NULL; UNIQUE(evidence_id, target_kind, target_id, relation, provenance) | idx_evidence_items_source, idx_evidence_items_retention, idx_evidence_links_target; owner migration consumers; exact owner unknown |
| `context_signals` | id INTEGER PRIMARY KEY AUTOINCREMENT; source_kind TEXT NOT NULL; source_id TEXT NOT NULL; kind TEXT NOT NULL; occurred_on TEXT NOT NULL; range_min REAL; range_max REAL; confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1); confirmed INTEGER NOT NULL CHECK(confirmed IN (0, 1)); revoked_at TEXT; created_at TEXT NOT NULL; updated_at TEXT NOT NULL; UNIQUE(source_kind, source_id, kind) | idx_context_signals_source, idx_context_signals_date; owner `meridian/context.py` |
| `assets` | id INTEGER PRIMARY KEY AUTOINCREMENT; name TEXT NOT NULL; category TEXT NOT NULL; purchased_on TEXT; purchase_price REAL; return_until TEXT; maintenance_interval_days INTEGER; replacement_reserve REAL; evidence_id INTEGER; evidence_span TEXT NOT NULL; confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | none declared; owner `meridian/assets.py` |
| `warranties` | id INTEGER PRIMARY KEY AUTOINCREMENT; asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE; provider TEXT NOT NULL; expires_on TEXT; deductible REAL; evidence_id INTEGER; evidence_span TEXT NOT NULL; confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | none declared; owner migration consumers; exact owner unknown |
| `contracts` | id INTEGER PRIMARY KEY AUTOINCREMENT; kind TEXT NOT NULL; name TEXT NOT NULL; starts_on TEXT; ends_on TEXT; renews_on TEXT; cancel_by TEXT; escalation_percent REAL; deductible REAL; evidence_id INTEGER; evidence_span TEXT NOT NULL; confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | none declared; owner `meridian/contracts.py` |
| `obligations` | id INTEGER PRIMARY KEY AUTOINCREMENT; contract_id INTEGER NOT NULL REFERENCES contracts(id) ON DELETE CASCADE; name TEXT NOT NULL; amount REAL NOT NULL; due_on TEXT; recurrence TEXT; commitment_id INTEGER; evidence_id INTEGER; evidence_span TEXT NOT NULL; confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | none declared; owner migration consumers; exact owner unknown |
| `asset_correction_proposals` | id INTEGER PRIMARY KEY AUTOINCREMENT; asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE; field TEXT NOT NULL; proposed_value TEXT NOT NULL; evidence_id INTEGER; status TEXT NOT NULL CHECK(status IN ('proposed', 'approved', 'rejected')); created_at TEXT NOT NULL | none declared; owner migration consumers; exact owner unknown |
| `connection_authorizations` | id INTEGER PRIMARY KEY AUTOINCREMENT; public_id TEXT NOT NULL UNIQUE; kind TEXT NOT NULL; display_name TEXT NOT NULL; state TEXT NOT NULL CHECK ( state IN ('connected', 'pending', 'limited', 'failed', 'revoked') ); granted_scopes TEXT NOT NULL DEFAULT '[]'; last_successful_at TEXT; retention_days INTEGER CHECK (retention_days IS NULL OR retention_days >= 0); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | idx_connection_authorizations_kind_state; owner migration consumers; exact owner unknown |
| `evidence_items (altered in 015_evidence_sender.sql)` | sender TEXT | migration alteration; base-table owner |
| `trials` | id INTEGER PRIMARY KEY AUTOINCREMENT; service TEXT NOT NULL; account_identifier TEXT; plan_name TEXT; status TEXT NOT NULL DEFAULT 'trial' CHECK(status IN ('trial','active','canceled','unknown')); trial_started_at TEXT NOT NULL; trial_ends_at TEXT NOT NULL; cancel_by TEXT NOT NULL; buffer_days INTEGER NOT NULL DEFAULT 1 CHECK(buffer_days >= 0 AND buffer_days <= 90); price_after REAL; cadence TEXT; timezone TEXT NOT NULL DEFAULT 'UTC'; source_of_truth TEXT NOT NULL DEFAULT 'manual' CHECK(source_of_truth IN ('checkout_capture','receipt','transaction','manual','inferred')); confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0 AND confidence <= 1); allowlisted INTEGER NOT NULL DEFAULT 0 CHECK(allowlisted IN (0,1)); essential INTEGER NOT NULL DEFAULT 0 CHECK(essential IN (0,1)); autonomy_tier TEXT NOT NULL DEFAULT 'propose' CHECK(autonomy_tier IN ('direct','propose','autonomous')); created_at TEXT NOT NULL; updated_at TEXT NOT NULL | trials_cancel_by_idx, trials_status_idx; owner `meridian/trials.py` |
| `cancellation_actions` | id INTEGER PRIMARY KEY AUTOINCREMENT; trial_id INTEGER NOT NULL REFERENCES trials(id) ON DELETE CASCADE; channel TEXT NOT NULL; state TEXT NOT NULL CHECK(state IN ('planned','attempted','awaiting_ack','verified','unverified','escalated','failed')); status_label TEXT NOT NULL DEFAULT 'Unverified'; confirmation_reference TEXT; started_at TEXT; completed_at TEXT; artifact_ids TEXT NOT NULL DEFAULT '[]'; notes TEXT; created_at TEXT NOT NULL; updated_at TEXT NOT NULL | cancellation_actions_trial_idx; owner `meridian/cancellation/repository.py` |
| `trial_notifications` | id INTEGER PRIMARY KEY AUTOINCREMENT; trial_id INTEGER NOT NULL REFERENCES trials(id) ON DELETE CASCADE; kind TEXT NOT NULL CHECK(kind IN ('7_days','3_days','1_day','deadline')); due_at TEXT NOT NULL; status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','dismissed')); created_at TEXT NOT NULL; sent_at TEXT; UNIQUE(trial_id, kind) | trial_notifications_due_idx; owner `meridian/cancellation/notifications.py` |
| `financial_observations` | id INTEGER PRIMARY KEY AUTOINCREMENT; snapshot_id TEXT NOT NULL; provider TEXT NOT NULL; connection_external_id TEXT NOT NULL; object_kind TEXT NOT NULL CHECK (object_kind IN ('account', 'transaction')); external_id TEXT NOT NULL; observed_at TEXT NOT NULL; source_updated_at TEXT; freshness TEXT NOT NULL CHECK (freshness IN ('fresh', 'stale', 'partial', 'unavailable')); confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)); assumptions_json TEXT NOT NULL DEFAULT '[]'; payload_json TEXT NOT NULL; payload_hash TEXT NOT NULL; data_mode TEXT NOT NULL DEFAULT 'actual' CHECK (data_mode IN ('actual', 'simulated')); created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP; UNIQUE (snapshot_id, object_kind, external_id) | idx_financial_observations_snapshot, idx_financial_observations_external; owner migration consumers; exact owner unknown |
| `financial_accounts (altered in 020_account_absence_reconciliation.sql)` | absent_since TEXT | migration alteration; base-table owner |
| `commitments (altered in 021_commitment_absence_reconciliation.sql)` | absent_since TEXT | migration alteration; base-table owner |

## C. Domain model inventory

| Record/enum | Fields/values | Defined in | Confidence |
|---|---|---|---|
| `NormalizedAccount`, `NormalizedTransaction`, `ExpectedInflow`, `CommitmentCandidate`, `ProviderSnapshot` | normalized provider fields; snapshot includes connection identity, accounts, transactions, inflows/candidates/errors | `meridian/providers/base.py:8-70` | HIGH |
| `CommitmentType`, `Commitment` | commitment type and planning/legacy identity, amount/date/funding/status fields | `meridian/commitments.py` | HIGH |
| `FundingRule`, `FundingEvent`, `FundingProjection` | rule kinds include fixed, percent, calendar, even-by-date, waterfall, weekly, biweekly; projection events/shortfall | `meridian/funding.py` | HIGH |
| `AccountRecord`, `TransactionRecord` | normalized persisted read records | `meridian/models.py` | HIGH |
| `SyncReport`, `ProviderConnectionFreshness` | sync status/counts/errors and freshness state | `meridian/sync.py`, `meridian/repository.py` | MEDIUM |
| action states/records and policy results | proposal/approval/executing/terminal lifecycle and authorization decisions | `crew/actions.py`, `crew/policy`-equivalent executors, `meridian/policy.py` | MEDIUM |
| cancellation/trial records | trial, cancellation action, notification states | `meridian/trials.py`, `meridian/cancellation/*` | HIGH |

## D. Stub and dead-code audit

- `crew/proposals.py:17` raises `NotImplementedError`; this is an abstract proposal hook, not executable capability.
- Pass-only classes in `meridian/ai/advisor.py:8`, `crew/client.py`, `crew/actions.py`, `crew/assistant.py`, `crew/advisor.py`, `crew/mac_secrets.py`, `crew/session_credentials.py`, and `crew/proposals.py` are mostly marker/abstract types; concrete implementations exist, so classify as interfaces/partial rather than dead.
- Exception-swallowing `pass` occurs at `meridian/services/today.py:203,266`, `meridian/ingest.py:86,112`, and `meridian/connectors/icloud_mail.py:168,172`; failures may be hidden and deserve observability review.
- Numerous `None`/empty returns in `meridian/proactive.py`, `payday.py`, `paycheck_learning.py`, `services/*`, and provider adapters represent missing/optional data paths; individual stub status is unknown without runtime inputs.
- No TODO/FIXME/HACK marker was found in `meridian/`, `crew/`, `app.py`, or `assistant.py` by grep. **HIGH.**
- `templates/index.html.backup` is not referenced by source search and is likely unserved. **MEDIUM.** Static imports cannot prove other modules dead because API/app use dynamic imports; adapters with tests are unwired, not dead.

## E. Provider/data-source truth table

| Adapter | Reads | Connection identity | Local tables/populates | Active in preview? | Confidence |
|---|---|---|---|---|---|
| `CrewReadAdapter` | CrewClient current-user accounts/transactions/transfers | `current-user` / Crew | normalized accounts, transactions, relations through sync | no direct app path found; app uses CrewWork | HIGH |
| `CrewWorkSnapshotAdapter` | credential-free CrewWork dashboard snapshot | `crew-work-assistant` / Crew (Work Assistant) | normalized accounts/transactions and commitment candidates via `sync_live_crew` | yes, `app.py:840-901`, `meridian/live.py` | HIGH |
| `SimpleFinAdapter` | injected account/transaction fetchables | `simplefin-access` / SimpleFin | emits snapshot; no active Meridian registration found | no/unknown; legacy helpers remain in app.py | HIGH |
| `LunchFlowAdapter` | injected account/transaction fetchables | `lunchflow-user` / LunchFlow | emits snapshot; no active registration found | no/unknown | HIGH |
| `SplitwiseAdapter` | injected friends/expenses and current user id | `user:<id>` / Splitwise | reimbursement account/transactions/inflows/candidates; no active registration found | no/unknown; legacy helpers remain | HIGH |
| Gmail/iCloud/Calendar connectors | read-only OAuth email/calendar transports | connection authorization/provider IDs | evidence/context/connection tables through API jobs | partial; configuration/authorization unknown | MEDIUM |

### External binaries/CLIs
- `meridian/live.py:19`: `/Users/stephenwest/Applications/CrewWorkAssistantOTP/.venv/bin/crew-readonly`, `subprocess.run`; overrideable `binary` argument.
- `meridian/crew_write.py:41`: `/Users/stephenwest/Applications/CrewWorkAssistantOTP/.venv/bin/crew-write`, approved write executor via `subprocess.run`.
- No other financial CLI path was source-confirmed. **HIGH.**

## F. UI surface inventory

| Surface | Workspace/purpose | Main API calls | Status |
|---|---|---|---|
| `templates/meridian/index.html` + partials | Meridian shell: Today, Plan, Activity, Accounts, connections, actions, payday, trials, inspector | `/api/meridian/today`, `plan`, `accounts`, `activity`, `dial`, `actions`, `sync`, memory/assets/contracts/trials/settings | functional data-dependent shell; Observatory concepts are not screenshots-as-product |
| `templates/meridian/settings.html` + partials | settings, connections, security, payday | `/api/meridian/settings/*`, auth/passkeys, connection routes | functional/partial by config |
| `static/js/meridian/*.js` | controllers for today/plan/activity/accounts/dial/inspector/memory/actions/review/trials/connections/payday/theme/shell | `/api/meridian/*`, `/api/actions/*`, `/api/auth/passkeys` | functional modules with loading/empty/error states; reachability varies |
| legacy templates and `static/js/api/*.js`, `features/*.js` | account/activity/cards/credit/expenses/family/goals/pockets/splitwise | legacy `/api/*` routes in app.py | retained legacy functional paths, not Observatory shell |
| `static/meridian-observatory-preview.html`, `static/debug_functions.html` | static preview/debug artifacts | no guaranteed API wiring | preview/debug, not primary route |

## G. Test coverage map

Approximate `def test_` counts from file text; browser tests may skip without `APP_URL`. **HIGH.**

| Directory | Coverage | Approx tests |
|---|---|---:|
| `tests/crew/` | action store/executors, advisor, broker, credentials, transports, health, renewal, capture | 142 |
| `tests/meridian/providers/` | Crew, CrewWork, external adapter normalization | 24 |
| `tests/meridian/connectors/` | calendar/email/Gmail/OAuth/iCloud | 30 |
| `tests/meridian/documents/` | extraction/reconciliation/safety | 10 |
| `tests/meridian/services/` | accounts/connections/dial/memory/plan/today | 29 |
| `tests/meridian/ai/` | advisor/classifier | 11 |
| `tests/meridian/` remaining | API, repositories, sync/reconciliation, funding/commitments, evidence/context, assets/contracts, trials/cancellation, auth/settings, JS contracts, migrations | ~390 |
| `tests/browser/` | shell/workspaces/responsive/capture/plan/inspector/recovery/evidence/settings | 53 declared; skip-gated |
| top-level `tests/` | app integrations, redirects, production config, capture, workspace invariant, seed | 60 |

Domains with no obvious dedicated direct tests: `meridian/billers.py`, `deposit_discovery.py`, `gmail_intake.py`, standalone `payday.py`, and some proactive/refresh paths (indirect coverage may exist). No exhaustive per-table constraint test exists. No live network acceptance test for SimpleFin/LunchFlow/Splitwise; external adapter tests inject fixtures.

## H. Unknowns and contradictions

| Finding | Evidence | Confidence |
|---|---|---|
| CURRENT_STATUS/project memory call Slices 3–7 complete, but consolidated handoff says future Observatory and many behaviors are proposed/not shipped. | `docs/project/CURRENT_STATUS.md`; `docs/meridian-project-memory.md`; `docs/project/MERIDIAN_CONSOLIDATED_HANDOFF_2026-09-08.md:198-206` | HIGH |
| `app.py` performs legacy schema work in addition to versioned migrations; coexistence was not executed or DB-inspected under this pass. | `app.py:349-688`; `meridian/db.py` | HIGH |
| Active preview URL/process and whether source edits are loaded cannot be proven because runtime start/inspection was prohibited. | governing docs; no runtime action taken | HIGH |
| Dynamic/config-based registration of SimpleFin/LunchFlow/Splitwise is unknown beyond no static app imports. | provider modules/tests and app import scan | MEDIUM |
| Full handler list after app.py’s large legacy region and exact template-to-handler mapping were grouped rather than duplicated; source is the authority. | `app.py` | MEDIUM |
| Evidence graph, documents, life context, contracts, and cancellation have schema/modules/tests, but production ingestion and user-visible completeness are not established statically. | migrations 011–018; `meridian/api.py`; connectors/documents/cancellation | HIGH |
| No autonomous external transfer implementation was found; safety docs require proposal/approval/execution/provider verification. | `AGENTS.md`; `app.py`; `crew/executors.py` | HIGH |

## Method and boundary

Read source, migrations, templates, static JS, tests, and governing documents only. Did not start the app, run migrations, open/modify databases, read `.env`/`.env.save`, print credentials, stage, commit, or modify files other than this inventory. Line anchors are exact where cited; uncertain reachability is marked unknown/partial.
