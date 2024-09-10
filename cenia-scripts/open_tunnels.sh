#!/bin/bash

# Create a new tmux session for each SSH tunnel to enable communication between Ranokau and WebUI

tmux new-session -d -s ssh_tunnel1 "ssh user@146.155.155.83 -L 21001:localhost:21001; bash"
tmux new-session -d -s ssh_tunnel2 "ssh user@146.155.155.83 -L 31001:localhost:31001; bash"
tmux new-session -d -s ssh_tunnel3 "ssh user@146.155.155.83 -L 31002:localhost:31002; bash"
tmux new-session -d -s ssh_tunnel4 "ssh user@146.155.155.83 -L 31003:localhost:31003; bash"
tmux new-session -d -s ssh_tunnel5 "ssh user@146.155.155.83 -L 31004:localhost:31004; bash"
tmux new-session -d -s ssh_tunnel6 "ssh user@146.155.155.83 -L 31005:localhost:31005; bash"

# Display information about running tmux sessions
tmux list-sessions