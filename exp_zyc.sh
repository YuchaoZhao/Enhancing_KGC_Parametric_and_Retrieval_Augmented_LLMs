#!/bin/bash
#SBATCH --job-name=job_zyc
#SBATCH --time=00:40:00
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=72
#SBATCH --gpus=4
#SBATCH --gpus-per-node=4


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

# # Copy input file to scratch
# cp -r $HOME/KAMEL/data/kamel "$TMPDIR"
# cp $HOME/KAMEL/question-templates.csv "$TMPDIR"
 
# #Create output directory on scratch
# mkdir "$TMPDIR"/output_dir
# mkdir /scratch-shared/yzhao/.transformers
export TRANSFORMERS_CACHE=/scratch-shared/yzhao/.transformers
export HF_DATASETS_CACHE=/scratch-shared/yzhao/.huggingface
#Execute a Python program located in $HOME, that takes an input file and output directory as arguments.
# python $HOME/KAMEL/predict.py --input "$TMPDIR"/KAMEL/data/kamel --fewshot 10 --templates "$TMPDIR"/KAMEL/question-templates.csv
python $HOME/KAMEL/predict_ensemble_model.py --input $HOME/KAMEL/data/kamel_20_pop --fewshot 10 --templates $HOME/KAMEL/question-templates.csv
#python $HOME/KAMEL/ft_mc.py
# #Copy output directory from scratch to home
# cp -r "$TMPDIR"/output_dir $HOME