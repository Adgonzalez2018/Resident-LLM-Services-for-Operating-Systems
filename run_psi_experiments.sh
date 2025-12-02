#!/bin/bash
# Script 2: Run all cgroups+PSI experiments (concurrency 1,2,4,8)

source ~/llm_experiments/bin/activate

VENV_PYTHON=$HOME/llm_experiments/bin/python3
RESULTS_DIR=~/llm_experiments/results

echo "=== Running CGROUPS+PSI experiments ==="

# Set up cgroup
sudo mkdir -p /sys/fs/cgroup/llm_service
echo "50000 100000" | sudo tee /sys/fs/cgroup/llm_service/cpu.max
echo "4294967296" | sudo tee /sys/fs/cgroup/llm_service/memory.max

CONCURRENCY_LEVELS=(1 2 4 8)

for conc in "${CONCURRENCY_LEVELS[@]}"; do
    echo "  Concurrency: $conc"
    sudo cgexec -g cpu,memory:llm_service $VENV_PYTHON request_generator.py \
        --concurrency $conc \
        --requests 20 \
        --mode psi \
        --output $RESULTS_DIR/psi_c${conc}.csv
    
    echo "    Completed: psi_c${conc}.csv"
done

echo "=== All PSI Experiments Complete! ==="
echo "Results saved to: $RESULTS_DIR/psi_c*.csv"

alexg ALL=(ALL) NOPASSWD: ALL