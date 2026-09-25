// meridian/memory-manage.js - asset/contract management via pipeline proposals
//
// Renders management forms (add/update/delete asset or contract) and surfaces
// pending memory proposals for owner approval. All mutations go through the
// action pipeline: management endpoints return 202 {"proposal": {id, state}}
// and the pending proposals are approved/executed via the existing
// /api/actions endpoints.

import { describeActionOutcome } from "./action-outcome.js";
import { renderActionReviewDetails } from "./action-review.js";

(function () {
    'use strict';

    const ASSET_CATEGORIES = [
        'electronics', 'furniture', 'appliance', 'vehicle', 'clothing', 'other',
    ];
    const CONTRACT_KINDS = [
        'insurance', 'subscription', 'lease', 'loan', 'service', 'other',
    ];

    const Management = {
        init() {
            document.querySelectorAll('[data-testid=add-asset]').forEach((button) => {
                button.addEventListener('click', () => this.openForm('asset', 'create'));
            });
            document.querySelectorAll('[data-testid=add-contract]').forEach((button) => {
                button.addEventListener('click', () => this.openForm('contract', 'create'));
            });
            this.loadPending();
        },

        async submit(kind, mode, payload) {
            const path = kind === 'asset' ? '/api/meridian/assets' : '/api/meridian/contracts';
            const method = mode === 'create' ? 'POST'
                : mode === 'delete' ? 'DELETE' : 'PATCH';
            const suffix = mode === 'create' ? '' : `/${payload.record_id}`;
            const response = await fetch(`${path}${suffix}`, {
                method,
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const body = await response.json().catch(() => ({}));
                throw new Error((body.error && body.error.message) || `Request failed (${response.status})`);
            }
            return response.json();
        },

        section() {
            return document.querySelector('.memory-management')
                || document.querySelector('[data-workspace="accounts"]');
        },

        openForm(kind, mode, record) {
            const host = this.section();
            if (!host) return;

            const existing = host.querySelector('[data-testid=management-form]');
            if (existing) existing.remove();

            const isAsset = kind === 'asset';
            const form = document.createElement('form');
            form.setAttribute('data-testid', 'management-form');
            form.setAttribute('data-kind', kind);
            form.setAttribute('data-mode', mode);
            form.className = 'memory-management__form';

            const nameField = document.createElement('label');
            nameField.className = 'memory-management__field';
            const nameSpan = document.createElement('span');
            nameSpan.textContent = isAsset ? 'Asset name' : 'Contract name';
            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.name = 'name';
            nameInput.setAttribute('data-testid', isAsset ? 'asset-name' : 'contract-name');
            nameInput.required = true;
            if (record && record.title) nameInput.value = record.title;
            nameField.appendChild(nameSpan);
            nameField.appendChild(nameInput);

            const kindField = document.createElement('label');
            kindField.className = 'memory-management__field';
            const kindSpan = document.createElement('span');
            kindSpan.textContent = isAsset ? 'Category' : 'Kind';
            const kindSelect = document.createElement('select');
            kindSelect.name = isAsset ? 'category' : 'kind';
            kindSelect.setAttribute('data-testid', isAsset ? 'asset-category' : 'contract-kind');
            const options = isAsset ? ASSET_CATEGORIES : CONTRACT_KINDS;
            options.forEach((value) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = value;
                kindSelect.appendChild(option);
            });
            kindField.appendChild(kindSpan);
            kindField.appendChild(kindSelect);

            // Hidden numeric record id. Accounts memory items carry ids like
            // "asset:7" / "contract:3"; the numeric part is the DB record id.
            const recordIdInput = document.createElement('input');
            recordIdInput.type = 'hidden';
            recordIdInput.name = 'record_id';

            if (mode === 'update' || mode === 'delete') {
                const numericId = record && record.id
                    ? parseInt(String(record.id).split(':')[1], 10) : NaN;
                if (!Number.isNaN(numericId)) recordIdInput.value = String(numericId);
            }
            if (mode === 'update' && record) {
                const currentKind = isAsset ? record.category : record.contract_kind;
                if (currentKind && [...kindSelect.options].some((option) => option.value === currentKind)) {
                    kindSelect.value = currentKind;
                }
            }

            const submit = document.createElement('button');
            submit.type = 'submit';
            submit.textContent = mode === 'delete' ? 'Delete'
                : mode === 'update' ? 'Update proposal' : 'Create proposal';
            submit.setAttribute('data-testid', isAsset ? 'submit-asset' : 'submit-contract');

            const cancel = document.createElement('button');
            cancel.type = 'button';
            cancel.textContent = 'Cancel';
            cancel.setAttribute('data-testid', 'cancel-management');
            cancel.addEventListener('click', () => form.remove());

            const status = document.createElement('p');
            status.className = 'memory-management__status';
            status.setAttribute('data-testid', 'management-status');
            status.hidden = true;

            form.appendChild(recordIdInput);
            if (mode !== 'delete') {
                form.appendChild(nameField);
                form.appendChild(kindField);
            }
            form.appendChild(submit);
            form.appendChild(cancel);
            form.appendChild(status);

            form.addEventListener('submit', async (event) => {
                event.preventDefault();
                if (mode === 'delete'
                    && !window.confirm('Delete this record? A delete proposal is created for owner approval.')) {
                    return;
                }
                const payload = {};
                if (mode !== 'delete') {
                    payload.name = nameInput.value.trim();
                    if (isAsset) {
                        payload.category = kindSelect.value;
                    } else {
                        payload.kind = kindSelect.value;
                    }
                }
                if (mode === 'update' || mode === 'delete') {
                    payload.record_id = parseInt(recordIdInput.value, 10);
                }
                if (mode === 'delete') {
                    payload.change_reason = 'Owner removed';
                }
                try {
                    await this.submit(kind, mode, payload);
                    status.textContent = 'proposal created';
                    status.hidden = false;
                    submit.disabled = true;
                    // Surface the freshly created proposal in the pending list.
                    await this.loadPending();
                } catch (error) {
                    status.textContent = error.message;
                    status.hidden = false;
                }
            });

            host.appendChild(form);
        },

        // Owner, 2026-09-25, on the Assets & Contracts plate: "remove essentially user facing nonesense
        // text like delete_asset: Meridian delete_asset". The label was
        // `${action.type}: ${action.rationale || action.id}` -- an internal action type, a colon, and a
        // 32-character id or an old machine summary. A proposal's label is the one line the owner reads
        // before deciding, so it now says what will happen.
        //
        // `machineSummary` recognises the strings the app itself used to write ("Meridian delete_asset:
        // 6", "delete_asset: 6") so proposals ALREADY in the store also read as sentences -- the fix is
        // in the display as well as in `app.py`'s generator, because stored rows are not migrated.
        // Nothing is hidden: the raw type and id stay on the row as data attributes for support.
        machineSummary(value) {
            return /^(Meridian\s+)?[a-z][a-z0-9]*(_[a-z0-9]+)*:\s*\S+$/.test(String(value || '').trim());
        },

        proposalSentence(action) {
            const machine = this.machineSummary.bind(this);
            for (const candidate of [action.rationale, action.summary]) {
                const text = String(candidate || '').trim();
                if (text && !machine(text)) return text;
            }
            const params = action.params || {};
            const name = params.name || params.title || params.label;
            const words = String(action.type || 'proposed change').replace(/_/g, ' ').trim();
            const sentence = words.charAt(0).toUpperCase() + words.slice(1);
            return name ? `${sentence} "${name}"` : sentence;
        },

        async loadPending() {
            const container = document.querySelector('[data-testid=pending-memory-proposals]');
            if (!container) return;
            const response = await fetch('/api/actions/pending', { credentials: 'same-origin' });
            if (!response.ok) return;
            const body = await response.json();
            const memoryTypes = new Set([
                'create_asset', 'update_asset', 'delete_asset',
                'create_contract', 'update_contract', 'delete_contract',
            ]);
            const pending = (body.actions || body.pending || []).filter(
                (action) => memoryTypes.has(action.type)
            );
            if (pending.length === 0) {
                container.hidden = true;
                return;
            }
            container.hidden = false;
            container.innerHTML = '';
            pending.forEach((action) => {
                const row = document.createElement('div');
                row.className = 'pending-memory-proposal';
                row.setAttribute('data-testid', 'pending-memory-proposal');
                // The raw type and id are kept on the row, not in the sentence: support and tests can
                // still identify exactly which action this is, and the owner does not have to read it.
                if (action.type) row.dataset.actionType = action.type;
                if (action.id) row.dataset.actionId = action.id;
                const label = document.createElement('span');
                label.textContent = this.proposalSentence(action);
                row.appendChild(label);
                row.appendChild(renderActionReviewDetails(action));
                const approve = document.createElement('button');
                approve.textContent = 'Approve';
                approve.setAttribute('data-testid', 'approve-proposal');
                // `data-action` is the hook the stylesheet needs to dress the two steps differently:
                // Approve is a decision, Execute is the mutation, and they must not look like one
                // button. The test ids stay as they are -- tests already depend on them.
                approve.dataset.action = 'approve';
                approve.addEventListener('click', () => this.decide(action.id, 'approve', approve));
                row.appendChild(approve);
                const execute = document.createElement('button');
                execute.textContent = 'Execute';
                execute.setAttribute('data-testid', 'execute-proposal');
                execute.dataset.action = 'execute';
                execute.disabled = true;
                execute.addEventListener('click', () => this.decide(action.id, 'execute', execute));
                row.appendChild(execute);
                const status = document.createElement('span');
                status.className = 'memory-management__status';
                status.setAttribute('data-testid', 'pending-proposal-status');
                row.appendChild(status);
                container.appendChild(row);
            });
        },

        async decide(id, step, button) {
            const row = button && button.parentElement;
            const statusEl = row && row.querySelector('[data-testid=pending-proposal-status]');
            const execute = row && row.querySelector('[data-testid=execute-proposal]');
            try {
                const response = await fetch(`/api/actions/${id}/${step}`, {
                    method: 'POST', credentials: 'same-origin',
                });
                if (!response.ok) {
                    const body = await response.json().catch(() => ({}));
                    throw new Error((body.error && body.error.message) || `Request failed (${response.status})`);
                }
                const body = await response.json();
                if (step === 'approve') {
                    // Approval succeeds: the action is no longer PROPOSED, so do
                    // NOT re-fetch pending (it would wipe the row). Instead enable
                    // this row's Execute button in place.
                    if (execute) execute.disabled = false;
                    if (statusEl) statusEl.textContent = 'approved';
                } else if (step === 'execute') {
                    const outcome = describeActionOutcome({ routing_direct: true, action: body });
                    if (statusEl) statusEl.textContent = outcome.message;
                    if (statusEl) statusEl.dataset.state = outcome.tone;
                    // A durable outcome is not a resend invitation. Keep failed,
                    // uncertain, or unverified rows visible and route recovery to
                    // Actions & Approvals rather than enabling another execution.
                    if (execute) execute.disabled = true;
                    if (outcome.refresh) {
                        if (row) row.remove();
                        // Hide the container only after verified execution removes
                        // its final pending row.
                        const container = document.querySelector('[data-testid=pending-memory-proposals]');
                        if (container && !container.querySelector('.pending-memory-proposal')) {
                            container.hidden = true;
                        }
                        document.dispatchEvent(new CustomEvent('memory:refresh', {
                            detail: { workspace: 'accounts' },
                        }));
                    }
                }
            } catch (error) {
                if (statusEl) statusEl.textContent = error.message;
            }
        },
    };

    document.addEventListener('DOMContentLoaded', () => Management.init());

    // Expose to window so memory.js can open per-record edit/delete forms.
    window.MeridianManagement = Management;
})();
