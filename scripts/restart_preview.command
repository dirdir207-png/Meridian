#!/bin/bash
#
# Meridian preview launcher (restart).
#
# Double-click this file to (re)start the local Meridian preview at http://127.0.0.1:8081.
# Safe to run repeatedly: it stops the preview already listening on the port, then starts a
# fresh one. That is exactly what is needed after a Python change or a schema migration.
#
# WHAT IT DOES NOT DO. It never talks to Crew, never moves money, never writes to the
# provider, and never touches the preview database except through the app itself. It starts a
# local web server that reads a local snapshot. No credentials are involved.
#
# WHY A RESTART IS EVER NEEDED. run_preview.py loads Python at process start
# (use_reloader = False), so changed Python code is not picked up until the process restarts:
#   - meridian/**.py, app.py, run_preview.py  -> RESTART NEEDED
#   - a migration that ALTERs a table whose record is built as Model(**dict(row))
#                                            -> RESTART AS PART OF SHIPPING IT, or the running
#                                               process applies the schema and then fails its
#                                               reads (this 503'd the dial on 2026-09-20)
#   - templates/**                           -> no restart (TEMPLATES_AUTO_RELOAD is on)
#   - static/** (JS, CSS)                    -> no restart (served from disk)
#   - docs/**                                -> no restart
#
# If a restart is needed and the preview is running, the symptom is stale behaviour, or a 503
# on the dial specifically, not a crash of the whole app.

set -u

REPO="/Users/stephenwest/Openrouter/simplecrew-latest"
PORT=8081
LOG="/tmp/gate-preview/run_preview.log"
PY="$REPO/.venv311/bin/python"

# Only ever consider LISTENING sockets: without -sTCP:LISTEN this would also match clients
# connected to the port and could kill the browser opening the page.
listeners() {
    lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null
}

echo "Meridian preview launcher"
echo "-------------------------"

if [ ! -x "$PY" ]; then
    echo "ERROR: no Python at $PY"
    echo "Is the repository still at $REPO ?"
    exit 1
fi

cd "$REPO" || { echo "ERROR: cannot enter $REPO"; exit 1; }
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true

# 1. Stop the preview that is already running on this port, politely first.
EXISTING="$(listeners)"
if [ -n "$EXISTING" ]; then
    echo "Stopping the preview already running (PID $EXISTING)..."
    kill $EXISTING 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        sleep 1
        [ -z "$(listeners)" ] && break
    done
    STILL="$(listeners)"
    if [ -n "$STILL" ]; then
        echo "It ignored the polite request, so forcing PID $STILL..."
        kill -9 $STILL 2>/dev/null
        sleep 1
    fi
fi

if [ -n "$(listeners)" ]; then
    echo
    echo "ERROR: port $PORT is still in use, so the preview was NOT started."
    echo "See what holds it with:"
    echo "    lsof -nP -iTCP:$PORT -sTCP:LISTEN"
    exit 1
fi

# 2. Start it detached, so closing this window does not stop the preview.
echo "Starting a fresh preview..."
nohup "$PY" run_preview.py > "$LOG" 2>&1 &
NEW_PID=$!
disown 2>/dev/null || true

# 3. Confirm it actually came up, rather than assuming.
for _ in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    [ -n "$(listeners)" ] && break
done

echo
if [ -n "$(listeners)" ]; then
    echo "Meridian preview is running (PID $NEW_PID)."
    echo "    http://127.0.0.1:8081"
    echo "    log: $LOG"
    echo
    echo "You can close this window; the preview keeps running."
    if [ "${NO_OPEN:-0}" != "1" ]; then
        open "http://127.0.0.1:8081" 2>/dev/null || true
    fi
else
    echo "The preview did NOT come up. The last lines of its log:"
    echo
    tail -15 "$LOG" 2>/dev/null || echo "(no log written yet)"
    echo
    echo "Most likely cause: a Python error in the working tree."
    exit 1
fi
