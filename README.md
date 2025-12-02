# Pressure-Aware Resource Management for Resident LLM Services

**Research on OS-level resource management for LLM inference workloads**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.linux.org/)

## Overview

Operating systems increasingly host large language models (LLMs) as resident services, but traditional OS resource controls are poorly suited for LLM inference patterns. This research evaluates three resource management strategies using **cgroups v2** and **Pressure Stall Information (PSI)** to manage GPT-2 inference under concurrent load.

**Key Finding:** Static resource limits cause 20-40× latency degradation, but PSI-gated admission control achieves **6.8× better p95 latency** at high concurrency by dynamically deferring requests during CPU pressure.

## Problem Statement

LLM inference exhibits highly variable, bursty execution patterns that differ fundamentally from traditional workloads:
- Token generation depends on prompt length, model size, and concurrent load
- Static OS controls (fixed CPU quotas, memory limits) lack dynamic responsiveness
- Tail latencies explode under resource contention

**Research Question:** Can OS-native pressure-aware mechanisms prevent performance collapse for resident LLM services?

## Approach

We evaluated three configurations under 1-8 concurrent requests:

1. **Baseline** - Unrestricted resource access
2. **cgroups-only** - Static limits (50% CPU quota, 4GB memory)
3. **cgroups+PSI** - Static limits + dynamic admission control using Pressure Stall Information

The PSI-gated system monitors `/proc/pressure/cpu` and defers requests when average CPU pressure over 10 seconds exceeds 95%.

## Results

| Concurrency | Baseline p95 (s) | cgroups-only p95 (s) | cgroups+PSI p95 (s) | Speedup |
|-------------|------------------|----------------------|---------------------|---------|
| 1           | 4.6              | 106.7                | 74.7                | 1.4×    |
| 2           | 3.6              | 103.7                | 73.0                | 1.4×    |
| 4           | 2.4              | 82.1                 | 60.4                | 1.4×    |
| 8           | 3.2              | 171.1                | 25.1                | **6.8×**|

**Key Insights:**
- Static limits cause severe degradation (20-40× latency increases)
- PSI-aware admission prevents tail-latency explosions
- Improvement scales with concurrency: 1.4× at low load → 6.8× at high load
- Dynamic feedback mechanisms outperform static isolation under contention

## Architecture

```
┌─────────────────────────────────────────┐
│         User Application Requests        │
└───────────────┬─────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│      PSI-Gated Admission Controller       │
│   Monitors /proc/pressure/cpu (avg10)     │
│   Defers requests if pressure > 95%       │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│         cgroups v2 Resource Limits        │
│     CPU: 50% quota │ Memory: 4GB cap      │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│       GPT-2 Inference (124M params)       │
└───────────────────────────────────────────┘
```

## Requirements

- **OS:** Linux with cgroups v2 support (tested on Ubuntu 25.10)
- **Python:** 3.8+
- **Root access:** Required for cgroups configuration

```bash
pip install -r requirements.txt
```

## Usage

### Running Experiments

```bash
# Baseline (unrestricted)
python llm_server.py --config baseline --concurrency 4

# cgroups-only (static limits)
sudo bash run_experiments.sh

# cgroups+PSI (pressure-aware)
sudo bash run_psi_experiments.sh
```

### Generate Test Requests

```bash
# Generate concurrent requests with varied prompts
python request_generator.py --num-requests 20 --concurrency 8
```

### Monitoring PSI

```bash
# View CPU pressure metrics
cat /proc/pressure/cpu

# some avg10=2.50 avg60=1.75 avg300=0.83 total=12849123
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

## Repository Structure

```
.
├── README.md
├── requirements.txt             # Python dependencies
├── paper.pdf                    # Full research paper
├── llm_server.py                # GPT-2 inference server
├── psi_admission.py             # PSI-gated admission controller
├── request_generator.py         # Concurrent request generator
├── run_experiments.sh           # cgroups-only experiments
├── run_psi_experiments.sh       # cgroups+PSI experiments
└── results/                     # Experiment outputs
    └── latency_distributions.csv
```

## Key Takeaways

1. **Static resource controls are inadequate for LLM workloads** - Performance degrades catastrophically under contention
2. **Pressure-aware admission is effective** - Dynamic feedback prevents tail-latency explosions
3. **Benefit scales with load** - PSI becomes more effective precisely when needed most
4. **Resident AI services need adaptive management** - Traditional OS isolation mechanisms must evolve

## Future Work

- Evaluate larger models (GPT-3 scale) and production workloads
- Explore optimal resource allocations and adaptive PSI thresholds
- Investigate multi-tenant scenarios with competing LLM services
- Test on real hardware (vs. virtualized environment)
- Integrate with ML serving frameworks (vLLM, TensorRT-LLM)

## Citation

If you use this work, please cite:

```bibtex
@article{gonzalez2024pressure,
  title={Pressure-Aware Resource Management for Resident LLM Services in Operating Systems},
  author={Gonzalez, Alex},
  journal={New York University},
  year={2024}
}
```

## Related Work

- [FlexGen](https://github.com/FMInference/FlexGen) - Efficient LLM inference with limited GPU memory
- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving with PagedAttention
- [cgroups v2 Documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

## License

MIT License - see LICENSE file for details

## Contact

Alex Gonzalez - [adgonzalez2023@gmail.com](mailto:adgonzalez2023@gmail.com)

---

⭐ If you find this research useful, please consider starring the repository!
