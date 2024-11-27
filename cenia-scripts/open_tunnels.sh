#!/bin/bash

# Script to create SSH tunnels for communication between Ranokau and WebUI
# Creates 6 different tmux sessions with SSH tunnels on different ports

# Function to create a new tunnel session
create_tunnel() {
    local port=$1
    local session_name="tunnel-${port}"
    
    # Check if session already exists
    if tmux has-session -t $session_name 2>/dev/null; then
        echo "Session $session_name already exists. Skipping..."
        return
    fi
    
    echo "Creating tunnel session: $session_name for port $port"
    tmux new-session -d -s $session_name "ssh sdonoso@146.155.155.83 -L ${port}:localhost:${port}; bash"
}

# Create tunnel sessions
create_tunnel "21001"
create_tunnel "31001"
create_tunnel "31002"
create_tunnel "31003"
create_tunnel "31004"
create_tunnel "31005"

# Display information about running tmux sessions
echo -e "\nActive tunnel sessions:"
tmux list-sessions

echo -e "\nAll SSH tunnels have been established"
echo "Use kill_tunnels.sh to terminate all sessions"
