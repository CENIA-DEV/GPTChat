export LOGDIR=/home/sdonoso/projects/GPTChat/logs
CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path microsoft/Phi-3.5-mini-instruct --controller  http://localhost:21001 --port 31001 --worker-address  http://localhost:31001 --num-gpus 1 --gpu_memory_utilization 0.5 --conv-template vicuna_test 
CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path google/gemma-2-9b-it --controller  http://localhost:21001 --port 31002 --worker-address  http://localhost:31002 --num-gpus 1 --gpu_memory_utilization 0.5
CUDA_VISIBLE_DEVICES=7 python3 -m fastchat.serve.vllm_worker --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --controller  http://localhost:21001 --port 31003 --worker-address  http://localhost:31003 --num-gpus 1 --gpu_memory_utilization 0.5 --conv-template llama-3-cenia
CUDA_VISIBLE_DEVICES=7 python3 -m fastchat.serve.vllm_worker --model-path mistralai/Mistral-7B-Instruct-v0.3 --controller  http://localhost:21001 --port 31004 --worker-address  http://localhost:31004 --num-gpus 1 --gpu_memory_utilization 0.5 --conv-template llama-3-cenia

