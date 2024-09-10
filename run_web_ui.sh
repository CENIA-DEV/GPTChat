#!/bin/bash

# Load environment variables from the .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Create a new tmux session for the remote logger server
tmux new-session -d -s logger_server "python3 -m gunicorn -w 2 -b 127.0.0.1:8080 'remote_logger_server:app'; bash"

# Create a new tmux session for the FastChat Gradio web server
tmux new-session -d -s gradio_server "python3 -m fastchat.serve.gradio_web_server_cenia --host localhost --port 7860 --controller http://localhost:21001 --share --register api_endpoints.json --gradio-auth-path user_pass; bash"

# Display information about running tmux sessions
tmux list-sessions