#!/usr/bin/env bash

echo "🐝 Activating all 12 specialized SEO Swarm agents..."

for i in {1..12}; do
    WORKER_ID="swarm$i"
    SESSION_NAME="swarm-$WORKER_ID"
    PROFILE_PATH="/Users/tirthpatel/.hermes/profiles/$WORKER_ID"
    CWD="/Users/tirthpatel/Desktop/my-seo-improve"
    HERMES_BIN="/Users/tirthpatel/.local/bin/hermes"

    # Check if session already exists
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        echo "✅ Worker $WORKER_ID is already running."
    else
        echo "🚀 Starting $WORKER_ID..."
        # Start a detached tmux session running the hermes TUI for that profile
        tmux new-session -d -s "$SESSION_NAME" -c "$CWD" "HERMES_HOME='$PROFILE_PATH' HERMES_CLI_BIN='$HERMES_BIN' exec '$HERMES_BIN' chat --tui"
    fi
done

echo "✨ All 12 agents are now active and reachable at http://localhost:3001/swarm"
