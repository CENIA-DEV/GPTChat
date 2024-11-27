#!/bin/bash

# Script to kill all SSH tunnel tmux sessions

# Function to kill a tmux session safely
kill_session() {
    local session=$1
    if tmux has-session -t $session 2>/dev/null; then
        echo "Killing session: $session"
        tmux kill-session -t $session
    else
        echo "Session $session not found"
    fi
}

# Kill all tunnel sessions
kill_session "tunnel-21001"
kill_session "tunnel-31001"
kill_session "tunnel-31002"
kill_session "tunnel-31003"
kill_session "tunnel-31004"
kill_session "tunnel-31005"

echo "All tunnel sessions have been terminated"
