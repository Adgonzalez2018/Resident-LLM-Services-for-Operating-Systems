#!/bin/bash
# Master script to run all experiments

# activate virtual environment
source ~/llm_experiments/bin/activate

VENV_PYTHON=$HOME/llm_experiments/bin/python3
set -e

RESULTS_DIR=~/llm_experiments/results
mkdir -p $RESULTS_DIR

echo "=== Starting Experiments ==="

# Concurrency levels to test
CONCURRENCY_LEVELS=(1 2 4 8)

# Number of requests per experiment
NUM_REQUESTS=20

# Run baseline (no cgroups, no PSI)
echo "Running BASELINE experiments..."
for conc in "${CONCURRENCY_LEVELS[@]}"; do
	echo " Concurrency: $conc"
	python3 request_generator.py \
		--concurrency $conc \
		--requests $NUM_REQUESTS \
		--mode baseline \
		--output $RESULTS_DIR/baseline_c${conc}.csv
done

# Run cgroups-only (fixed limits, no PSI)
echo "Running CGROUPS-ONLY experiments..."
#set up cgroup
sudo mkdir -p /sys/fs/cgroup/llm_service
echo "50000 100000" | sudo tee /sys/fs/cgroup/llm_service/cpu.max	# 50% CPU
echo "4294967296" | sudo tee /sys/fs/cgroup/llm_service/memory.max 	# 4GB	

for conc in "${CONCURRENCY_LEVELS[@]}"; do
	echo " Concurrency: $conc"
	# Run in cgroup
	sudo cgexec -g cpu,memory:llm_service $VENV_PYTHON request_generator.py \
		--concurrency $conc \
		--requests $NUM_REQUESTS \
		--mode cgroups \
		--output $RESULTS_DIR/cgroups_c${conc}.csv
done

# Run cgroups+PSI (my method)
echo "Running CGROUPS + PSI experiments..."
for conc in "${CONCURRENCY_LEVELS[@]}"; do
	echo " Concurrency: $conc"
	sudo cgexec -g cpu,memory:llm_service $VENV_PYTHON request_generator.py \
	--concurrency $conc \
	--requests $NUM_REQUESTS \
	--mode psi \
	--output $RESULTS_DIR/psi_c${conc}.csv
done

echo "=== Experiments Complete! ==="
echo "Results saved to: $RESULTS_DIR"	
