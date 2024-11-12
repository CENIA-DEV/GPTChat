#!/bin/bash

# Define the log directory
export LOGDIR=/home/sdonoso/projects/GPTChat/logs

# Define the path to the conda.sh script
CONDA_SH="/home/sdonoso/anaconda3/etc/profile.d/conda.sh"

# Function to check if a port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Function to check if tmux session exists
check_tmux_session() {
    tmux has-session -t $1 2>/dev/null
}

# Function to kill existing tmux session
kill_session() {
    if check_tmux_session $1; then
        echo "Killing existing session: $1"
        tmux kill-session -t $1
    fi
}

# Check if conda.sh exists
if [ ! -f "$CONDA_SH" ]; then
    echo "Error: conda.sh not found at $CONDA_SH"
    exit 1
fi

# Source conda
source "$CONDA_SH"

# Check if the conda environment exists
if ! conda env list | grep -q "fastchat-final"; then
    echo "Error: conda environment 'fastchat-final' not found"
    exit 1
fi

# Kill existing sessions if they exist
kill_session "controller"
kill_session "phi-model"
kill_session "gemma-model"
kill_session "llama-model"
kill_session "mistral-model"

# Check controller port
if ! check_port 21001; then
    echo "Error: Controller port 21001 is already in use"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$LOGDIR"

# Create a new tmux session for the controller
echo "Starting controller..."
tmux new-session -d -s controller "source $CONDA_SH && conda activate fastchat-final && python3 -m fastchat.serve.controller --host localhost --port 21001 2>&1 | tee $LOGDIR/controller.log; bash"

# Wait for controller to start
sleep 5

# Function to start a model worker
start_model_worker() {
    local session_name=$1
    local model_path=$2
    local gpu_id=$3
    local port=$4
    
    if ! check_port $port; then
        echo "Error: Port $port is already in use"
        return 1
    }
    
    echo "Starting $session_name on GPU $gpu_id, port $port..."
    tmux new-session -d -s $session_name "source $CONDA_SH && conda activate fastchat-final && CUDA_VISIBLE_DEVICES=$gpu_id python3 -m fastchat.serve.vllm_worker \
        --model-path $model_path \
        --controller http://localhost:21001 \
        --port $port \
        --worker-address http://localhost:$port \
        --num-gpus 1 \
        --gpu_memory_utilization 0.5 \
        --max-model-len 2048 \
        2>&1 | tee $LOGDIR/${session_name}.log; bash"
}

# Start model workers
start_model_worker "phi-model" "microsoft/Phi-3-small-128k-instruct" 6 31005
start_model_worker "gemma-model" "google/gemma-2-9b-it" 6 31001
start_model_worker "llama-model" "meta-llama/Meta-Llama-3.1-8B-Instruct" 7 31003
start_model_worker "mistral-model" "mistralai/Mistral-7B-Instruct-v0.3" 7 31004

# Wait for workers to initialize
sleep 5

# Display information about running tmux sessions
echo -e "\nRunning tmux sessions:"
tmux list-sessions

echo -e "\nLogs are being written to: $LOGDIR"
