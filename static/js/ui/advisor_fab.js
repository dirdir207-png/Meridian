/**
 * @file advisor_fab.js
 * @description Meridian contextual advisor — in-context control (desktop right
 * rail, mobile full-height sheet). Via window.advisorSetOpen() the shell's
 * in-context [data-open-advisor] buttons open it; the floating trigger is a
 * discreet secondary entry point. Chat history persists across sessions via
 * localStorage. Proposals still require owner approval in Pending Actions; the
 * advisor can only propose.
 */

const ADVISOR_HISTORY_KEY = 'sc_advisor_history_v1';
let advisorFabHistory = [];
let advisorFabReady = false;
let advisorConfigured = null;

function _advisorLog() {
    return document.getElementById('advisor-fab-log');
}

/** Scroll the panel's content region to its end.
 *
 *  The scrolling element is the VIEW that holds the briefing and the transcript, not
 *  the transcript alone — the log stopped being its own scroller when the briefing was
 *  added, so scrolling it would silently do nothing and leave new messages off-screen.
 */
function _advisorScrollToEnd() {
    const log = _advisorLog();
    if (!log) return;
    const scroller = log.closest('.m-virgil-view');
    if (scroller) {
        scroller.scrollTop = scroller.scrollHeight;
    } else {
        log.scrollTop = log.scrollHeight;
    }
}

function advisorLoadPersisted() {
    try {
        const raw = localStorage.getItem(ADVISOR_HISTORY_KEY);
        advisorFabHistory = raw ? JSON.parse(raw) : [];
        if (!Array.isArray(advisorFabHistory)) advisorFabHistory = [];
        if (advisorFabHistory.length > 20) advisorFabHistory = advisorFabHistory.slice(-20);
    } catch (e) {
        advisorFabHistory = [];
    }
    const log = _advisorLog();
    if (log) {
        log.innerHTML = '';
        if (advisorFabHistory.length === 0) {
            advisorBubble('assistant', "Hi! I'm Virgil. Ask about your balances, pockets, or spending — or tell me to move money and I'll draft a proposal for your approval.");
        } else {
            for (const m of advisorFabHistory) {
                if (m && m.content) advisorBubble(m.role, m.content, true);
            }
        }
    }
}

function advisorPersist() {
    try {
        localStorage.setItem(ADVISOR_HISTORY_KEY, JSON.stringify(advisorFabHistory.slice(-20)));
    } catch (e) { /* storage unavailable */ }
}

function advisorBubble(role, text, skipPersist) {
    const log = _advisorLog();
    if (!log || !text) return;
    const bubble = document.createElement('div');
    bubble.className = role === 'user'
        ? 'm-advisor-bubble m-advisor-bubble--user'
        : 'm-advisor-bubble m-advisor-bubble--assistant';
    bubble.textContent = text;
    log.appendChild(bubble);
    _advisorScrollToEnd();
    if (!skipPersist && role !== undefined) {
        // persisted by caller for user/assistant real messages
    }
}

function advisorSetOpen(open) {
    const panel = document.getElementById('advisor-panel');
    if (!panel) return;
    const shell = window.MeridianShell || null;
    if (open) {
        if (!advisorFabReady) { advisorLoadPersisted(); advisorFabReady = true; }
        ensureAdvisorStatus();
        advisorLoadBriefing();
        if (shell && typeof shell.openSheet === 'function') {
            // Reuse the shell's sheet primitive: it handles Escape, inert
            // background until the final close, focus restore, and the initial
            // focus target (`[data-sheet-initial-focus]`).
            shell.openSheet(panel, { modal: true });
        } else {
            panel.hidden = false;
            panel.setAttribute('data-open', '');
            panel.setAttribute('role', 'dialog');
            panel.setAttribute('aria-modal', 'true');
            // The same initial-focus rule the shell applies, so the two paths agree about where
            // focus lands instead of one focusing the composer and the other the panel.
            const initial = panel.querySelector('[data-sheet-initial-focus]');
            if (initial && typeof initial.focus === 'function') initial.focus();
        }
        // OPENING VIRGIL MUST NOT SUMMON THE SOFT KEYBOARD. Focus still moves INTO the dialog --
        // it has to, or the sheet becomes a keyboard trap -- but it lands on the panel rather than
        // on the composer. On a phone the keyboard covers the briefing and the transcript the
        // owner opened the panel to read, which made the surface feel broken. The keyboard
        // appears when he taps the composer, which is when he wants it.
        //
        // This used to call `input.focus()` here, and removing only this line would NOT have
        // fixed the defect: the input also carried `data-sheet-initial-focus`, which the shell
        // focuses on open. Two causes, one symptom -- and fixing the visible one alone would have
        // produced a "fixed" claim with the keyboard still appearing.
        try { localStorage.setItem('sc_advisor_open', '1'); } catch (e) {}
        const log = _advisorLog();
        if (log) _advisorScrollToEnd();
    } else {
        if (shell && typeof shell.closeSheet === 'function') {
            shell.closeSheet();
        }
        // The closed state is asserted on the ELEMENT, in both paths, rather than left to the
        // shell's stack bookkeeping. `#advisor-panel` is `display: none` only while it lacks
        // [data-open] (advisor.css:105,145), and on a phone it covers everything but a 12px margin
        // with a `--m-surface` fill, which is dark navy in the dark theme. So one missed stack pop
        // left a near-full-screen dark sheet the owner could not dismiss: "a black or partially
        // black screen". Doing the teardown here makes the visual outcome independent of whether
        // the pop happened, and it is idempotent when the shell already did it.
        panel.hidden = true;
        panel.removeAttribute('data-open');
        panel.removeAttribute('role');
        panel.removeAttribute('aria-modal');
        if (!shell || typeof shell.closeSheet !== 'function') {
            const fab = document.getElementById('advisor-fab');
            if (fab && typeof fab.focus === 'function') fab.focus();
        }
        try { localStorage.setItem('sc_advisor_open', '0'); } catch (e) {}
    }
}

async function ensureAdvisorStatus() {
    const statusEl = document.getElementById('advisor-fab-status');
    if (advisorConfigured !== null && statusEl) {
        statusEl.textContent = advisorConfigured ? '' : 'not configured';
        return;
    }
    try {
        const response = await fetch('/api/advisor/status', { credentials: 'same-origin' });
        const data = await response.json();
        advisorConfigured = !!data.configured;
        if (statusEl) statusEl.textContent = advisorConfigured ? '' : 'not configured';
        if (!advisorConfigured) {
            advisorBubble('assistant', 'AI provider not configured yet.\nAdd OPENAI_API_KEY (or OPENROUTER_API_KEY) to your .env and restart.');
        }
    } catch (e) {
        if (statusEl) statusEl.textContent = 'offline';
    }
}

async function advisorFabSend() {
    const input = document.getElementById('advisor-fab-input');
    const sendBtn = document.getElementById('advisor-fab-send');
    const message = ((input && input.value) || '').trim();
    if (!message) return;

    input.value = '';
    advisorBubble('user', message);
    advisorFabHistory.push({ role: 'user', content: message });
    advisorBubble('assistant', 'Thinking…');

    if (sendBtn) sendBtn.disabled = true;
    try {
        const contextualNode = document.querySelector('[data-advisor-context]:not([hidden])');
        const isMeridian = document.querySelector('[data-meridian-shell]') !== null;
        const context = contextualNode
            ? {
                kind: contextualNode.dataset.advisorContext,
                object_id: contextualNode.dataset.objectId || 'current',
                evidence_ids: contextualNode.dataset.objectId
                    ? [`${contextualNode.dataset.advisorContext}:${contextualNode.dataset.objectId}`]
                    : [],
            }
            : { kind: 'forecast', object_id: 'current', evidence_ids: [] };
        const response = await fetch(isMeridian ? '/api/meridian/advisor' : '/api/advisor/chat', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(isMeridian
                ? { question: message, context }
                : { message, history: advisorFabHistory.slice(-10) }),
        });
        const data = await response.json();
        const log = _advisorLog();
        if (log.lastChild) log.lastChild.remove();

        let replyText;
        if (!response.ok) {
            replyText = data.error || 'Advisor error.';
        } else {
            replyText = isMeridian ? (data.answer || '') : (data.reply || '');
            const proposal = data.proposal || ((data.proposals || [])[0]);
            if (proposal) {
                replyText += `\n\nProposal drafted: ${proposal.summary || proposal.type}\nReview it before approval.`;
                if (typeof loadPendingActions === 'function') loadPendingActions();
                if (typeof haptic === 'function') haptic([15, 40, 15]);
            }
        }
        advisorBubble('assistant', replyText);
        advisorFabHistory.push({ role: 'assistant', content: replyText });
        if (advisorFabHistory.length > 20) advisorFabHistory = advisorFabHistory.slice(-20);
        advisorPersist();
    } catch (error) {
        const log = _advisorLog();
        if (log.lastChild) log.lastChild.remove();
        advisorBubble('assistant', 'Could not reach the advisor.');
    } finally {
        if (sendBtn) sendBtn.disabled = false;
    }
}

/* ---------------------------------------------------------------------------
 * Virgil briefing — the concept's cards, fed by read models that already exist.
 *
 * Both sources are plain GETs over read-only endpoints that predate this surface:
 *   /api/meridian/weather  (proactive weather built from the Observatory dial)
 *   /api/actions/pending   (proposals awaiting the owner's approval)
 * Nothing here writes, proposes, approves or mutates, and no new endpoint is
 * introduced by this surface. Both calls fail soft: a briefing that cannot be
 * loaded leaves the conversation fully usable rather than breaking the panel.
 * ------------------------------------------------------------------------- */

/** Number words for the count in the card title. An unmapped count falls back to
 *  digits, so the title can never quietly show the wrong word. */
const ADVISOR_COUNT_WORDS = { 1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five' };

function _advisorCountWord(n) {
    return ADVISOR_COUNT_WORDS[n] || String(n);
}

function _advisorMonthDay(iso) {
    const parsed = new Date(`${String(iso).slice(0, 10)}T12:00:00Z`);
    if (Number.isNaN(parsed.getTime())) return String(iso || '');
    return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
}

/** Flatten the weather payload's groups into the near-term items, capped.
 *
 *  The title states the REAL count. The concept's fixed "Two things worth a look"
 *  is only true when there are exactly two, and a hardcoded count is the defect
 *  BUILD_HANDOFF.md names for the Review concept ("render the actual total, never
 *  hardcode three"). With nothing to report the card is hidden entirely rather
 *  than shown empty with an assuring title.
 */
function advisorWeatherItems(weather, limit) {
    const items = [];
    for (const group of (weather && weather.groups) || []) {
        for (const event of (group && group.events) || []) {
            items.push(event);
            if (items.length >= limit) return items;
        }
    }
    return items;
}

function advisorRenderEvidence(weather) {
    const card = document.querySelector('[data-virgil-evidence]');
    if (!card) return;
    const items = advisorWeatherItems(weather, 3);
    if (!items.length) {
        // ABSENCE IS THE HONEST ANSWER. The concept draws a filled card because it
        // is a mock with mock data; an empty one would imply Meridian has something
        // to say when it does not.
        card.hidden = true;
        return;
    }
    card.hidden = false;
    const title = card.querySelector('[data-virgil-evidence-title]');
    if (title) {
        // "One thing" / "Two things" / "Three things" — the plural follows the count.
        const word = _advisorCountWord(items.length);
        title.textContent = items.length === 1
            ? `${word} thing worth a look`
            : `${word} things worth a look`;
    }
    const list = card.querySelector('[data-virgil-evidence-items]');
    if (list) {
        list.replaceChildren();
        for (const item of items) {
            const li = document.createElement('li');
            li.textContent = item.explanation || item.title || 'An event needs attention.';
            list.appendChild(li);
        }
    }
    // Support links: real navigation into the surface that holds the record. Never
    // a dead affordance, and never a claim that the record has been opened.
    const links = card.querySelector('[data-virgil-evidence-links]');
    if (links) {
        links.replaceChildren();
        const first = items[0];
        const link = document.createElement('a');
        link.className = 'm-virgil-evidence-link';
        link.href = '/meridian?workspace=activity';
        link.textContent = first && first.date
            ? `Activity · ${_advisorMonthDay(first.date)}`
            : 'Activity';
        links.appendChild(link);
    }
}

function advisorRenderReview(pendingActions) {
    const card = document.querySelector('[data-virgil-review]');
    if (!card) return;
    const first = Array.isArray(pendingActions) ? pendingActions[0] : null;
    // Shown ONLY when something genuinely awaits review. A decorative "Draft" card
    // leading nowhere is the ambiguous-emptiness the ledger forbids.
    if (!first) {
        card.hidden = true;
        return;
    }
    card.hidden = false;
    const title = card.querySelector('[data-virgil-review-title]');
    if (title) title.textContent = first.summary || first.title || first.type || 'A proposal is waiting';
    const sub = card.querySelector('[data-virgil-review-sub]');
    if (sub) sub.textContent = 'Review it before anything is actioned.';
    // The state line is fixed text by design: a pending action HAS taken no action,
    // and the dot beside it is neutral/lilac, NOT the concept's confirmed-green.
}

function advisorRenderSources(weather) {
    const body = document.querySelector('[data-virgil-sources-body]');
    if (!body) return;
    body.replaceChildren();
    if (!weather) {
        body.appendChild(element('p', 'm-virgil-sources-empty', 'Sources are unavailable right now.'));
        return;
    }
    const facts = [];
    if (weather.freshness) facts.push(`Source age: ${weather.freshness}.`);
    if (weather.observedAt) facts.push(`Observed ${weather.observedAt}.`);
    if (weather.windowDays) facts.push(`Window: the next ${weather.windowDays} days.`);
    if (typeof weather.suppressed === 'number' && weather.suppressed > 0) {
        facts.push(`${weather.suppressed} event(s) were left out because they could not be identified.`);
    }
    for (const fact of facts) body.appendChild(element('p', '', fact));
    const assumptions = Array.isArray(weather.assumptions) ? weather.assumptions : [];
    if (assumptions.length) {
        body.appendChild(element('p', 'm-virgil-sources-heading', 'Assumptions'));
        const ul = document.createElement('ul');
        for (const assumption of assumptions) {
            const li = document.createElement('li');
            li.textContent = assumption;
            ul.appendChild(li);
        }
        body.appendChild(ul);
    } else {
        body.appendChild(element('p', '', 'No assumptions were stated for this view.'));
    }
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
}

let advisorBriefingLoaded = false;

async function advisorLoadBriefing() {
    if (advisorBriefingLoaded) return;
    advisorBriefingLoaded = true;
    let weather = null;
    try {
        const response = await fetch('/api/meridian/weather', { credentials: 'same-origin' });
        if (response.ok) weather = await response.json();
    } catch (e) { /* the briefing is optional; the conversation is not */ }
    let pending = [];
    try {
        const response = await fetch('/api/actions/pending', { credentials: 'same-origin' });
        if (response.ok) {
            const data = await response.json();
            pending = (data && data.actions) || [];
        }
    } catch (e) { /* same */ }
    advisorRenderEvidence(weather);
    advisorRenderReview(pending);
    advisorRenderSources(weather);
}

function advisorSetTab(name) {
    const tabs = document.querySelectorAll('[data-virgil-tab]');
    if (!tabs.length) return;
    for (const tab of tabs) {
        const selected = tab.dataset.virgilTab === name;
        tab.setAttribute('aria-selected', selected ? 'true' : 'false');
        tab.classList.toggle('is-active', selected);
    }
    const conversation = document.getElementById('virgil-view-conversation');
    const tasks = document.getElementById('virgil-view-tasks');
    if (conversation) conversation.hidden = name !== 'conversation';
    if (tasks) tasks.hidden = name !== 'tasks';
}

// Wire up on DOM ready
document.addEventListener('DOMContentLoaded', function () {
    for (const tab of document.querySelectorAll('[data-virgil-tab]')) {
        tab.addEventListener('click', () => advisorSetTab(tab.dataset.virgilTab));
    }
    const suggest = document.querySelector('[data-virgil-suggest]');
    if (suggest) suggest.addEventListener('click', () => {
        // Fills the composer only. Asking stays the owner's action, and Send still
        // goes through the single advisor call this panel has always made.
        const input = document.getElementById('advisor-fab-input');
        if (!input) return;
        input.value = suggest.textContent.trim();
        input.focus();
    });

    const fab = document.getElementById('advisor-fab');
    const close = document.getElementById('advisor-close');
    const send = document.getElementById('advisor-fab-send');
    const input = document.getElementById('advisor-fab-input');

    if (fab) fab.addEventListener('click', () => {
        if (typeof haptic === 'function') haptic(8);
        advisorSetOpen(true);
    });
    if (close) close.addEventListener('click', () => advisorSetOpen(false));
    if (send) send.addEventListener('click', advisorFabSend);
    if (input) input.addEventListener('keydown', (e) => { if (e.key === 'Enter') advisorFabSend(); });

    let shouldOpen = false;
    try { shouldOpen = localStorage.getItem('sc_advisor_open') === '1'; } catch (e) {}
    if (shouldOpen) advisorSetOpen(true);
});
