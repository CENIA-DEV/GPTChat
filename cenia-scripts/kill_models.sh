#!/bin/bash

# Kill the tmux session for the controller
tmux kill-session -t controller

# Kill the tmux session for each worker
tmux kill-session -t phi-model
tmux kill-session -t gemma-model
tmux kill-session -t llama-model
tmux kill-session -t mistral-model

# Optionally, display the remaining tmux sessions
tmux list-sessions
