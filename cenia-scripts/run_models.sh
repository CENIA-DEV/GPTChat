#!/bin/bash

# Define the log directory
export LOGDIR=/home/sdonoso/projects/GPTChat/logs

# Create a new tmux session for the controller
tmux new-session -d -s controller "python3.9 -m fastchat.serve.controller --host localhost --port 21001; bash"

# Create a new tmux session for each worker
tmux new-session -d -s phi-model "CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path microsoft/Phi-3-small-128k-instruct --controller http://localhost:21001 --port 31005 --worker-address http://localhost:31005 --num-gpus 1 --gpu_memory_utilization 0.5; bash"

tmux new-session -d -s gemma-model "CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path google/gemma-2-9b-it --controller http://localhost:21001 --port 31001 --worker-address http://localhost:31001 --num-gpus 1 --gpu_memory_utilization 0.5; bash"

tmux new-session -d -s llama-model "CUDA_VISIBLE_DEVICES=7 python3 -m fastchat.serve.vllm_worker --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --controller http://localhost:21001 --port 31003 --worker-address http://localhost:31003 --num-gpus 1 --gpu_memory_utilization 0.5; bash"

tmux new-session -d -s mistral-model "CUDA_VISIBLE_DEVICES=7 python3 -m fastchat.serve.vllm_worker --model-path mistralai/Mistral-7B-Instruct-v0.3 --controller http://localhost:21001 --port 31004 --worker-address http://localhost:31004 --num-gpus 1 --gpu_memory_utilization 0.5; bash"

# Display information about running tmux sessions
tmux list-sessions
