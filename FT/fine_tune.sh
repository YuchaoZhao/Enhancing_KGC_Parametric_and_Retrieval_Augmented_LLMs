#!/bin/bash
#SBATCH --job-name=job_zyc
#SBATCH --time=12:00:00
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
#SBATCH --gpus=1
#SBATCH --gpus-per-node=1


# This loads the anaconda virtual environment with our packages

source $HOME/.bashrc
conda activate

# Base directory for the experiment
mkdir $HOME/experiments
cd $HOME/experiments

# Simple trick to create a unique directory for each run of the script
echo $$
mkdir o`echo $$`
cd o`echo $$`

export TRANSFORMERS_CACHE=/scratch-shared/yzhao/.transformers
export HF_DATASETS_CACHE=/scratch-shared/yzhao/.huggingface

# Add parent directory to python path to access lightning_base.py
export PYTHONPATH="../":"${PYTHONPATH}"

# A sample finetuning run, you need to specify data_dir, output_dir and model_name_or_path
# run ./examples/rag/finetune_rag.sh --help to see all the possible options

# Start a single-node Ray cluster.
ray start --head

python /home/yzhao/transformers/examples/research_projects/rag/finetune_rag.py \
    --data_dir /home/yzhao/KAMEL/FT/datasets_mini \
    --output_dir /home/yzhao/KAMEL/FT/output_dir \
    --model_name_or_path facebook/rag-token-base \
    --model_type rag_token \
    --fp16 \
    --gpus 1 \
    --do_train \
    --num_train_epochs 1 \
    --train_batch_size 8 \
    --eval_batch_size 1 \
    --gradient_accumulation_steps 1 \
    --learning_rate 3e-05 \
    --adam_epsilon 1e-08 \
    --distributed_retriever ray \
    --num_retrieval_workers 4 \
    --check_val_every_n_epoch 1 \
    --max_epochs 1 \
    --warmup_steps 200 \
# Stop the ray cluster once fine-tuning has finished.
ray stop