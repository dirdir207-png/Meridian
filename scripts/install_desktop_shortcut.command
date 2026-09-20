#!/bin/bash
#
# Installs (or refreshes) the "Meridian Preview" shortcut on the Desktop.
#
# Run it once by double-clicking this file in Finder, or from a terminal:
#     /Users/stephenwest/Openrouter/simplecrew-latest/scripts/install_desktop_shortcut.command
#
# It writes a one-line shortcut that calls scripts/restart_preview.command, so the launcher
# itself stays in the repository and there is only ever one copy to maintain. Running this
# again after a change to the launcher is harmless: the shortcut only ever points at it.

set -u

SRC="/Users/stephenwest/Openrouter/simplecrew-latest/scripts/restart_preview.command"
DEST="$HOME/Desktop/Meridian Preview.command"

if [ ! -x "$SRC" ]; then
    echo "ERROR: $SRC is missing or not executable."
    exit 1
fi

if [ ! -d "$HOME/Desktop" ]; then
    echo "ERROR: no Desktop folder at $HOME/Desktop"
    exit 1
fi

cat > "$DEST" <<SHORTCUT
#!/bin/bash
#
# Meridian Preview - desktop shortcut.
#
# Double-click to (re)start the local Meridian preview at http://127.0.0.1:8081.
# Safe to run repeatedly. It only starts a local web server that reads a local snapshot:
# it never talks to Crew and never moves money.
#
# The real logic lives in the repository, so there is one copy to maintain:
#     $SRC
# Read that file for what the launcher does and exactly when a restart is needed.
#
exec "$SRC"
SHORTCUT

chmod +x "$DEST"
xattr -d com.apple.quarantine "$DEST" 2>/dev/null || true

echo "Installed: $DEST"
echo
echo "Double-click it any time to restart the preview."
echo "It points at: $SRC"
