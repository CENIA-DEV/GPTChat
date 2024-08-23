export LOGDIR=/home/sdonoso/projects/GPTChat/logs
CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path lmsys/vicuna-7b-v1.5 --controller  http://localhost:21001 --port 31001 --worker-address  http://localhost:31001 --num-gpus 1 --gpu_memory_utilization 0.3 --conv-template vicuna_test 
CUDA_VISIBLE_DEVICES=6 python3 -m fastchat.serve.vllm_worker --model-path google/gemma-2-9b-it --controller  http://localhost:21001 --port 31003 --worker-address  http://localhost:31003 --num-gpus 1 --gpu_memory_utilization 0.5
CUDA_VISIBLE_DEVICES=7 python3 -m fastchat.serve.vllm_worker --model-path meta-llama/Meta-Llama-3.1-8B-Instruct --controller  http://localhost:21001 --port 31002 --worker-address  http://localhost:31002 --num-gpus 1 --gpu_memory_utilization 0.5 --conv-template llama-3-cenia

