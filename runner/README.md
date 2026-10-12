# Owner-managed GPU runner

Use a dedicated Linux x86_64 host with an NVIDIA GPU and current vendor driver. This can be a physical machine or a rented cloud GPU instance. A practical minimum for the current quantized FLUX path is 16 GB VRAM; 24 GB or more is preferred. Do not run the GitHub runner as root and do not place wallet keys on this host.

For an online rental, follow [CLOUD-GPU.md](CLOUD-GPU.md). A persistent 24 GB RTX 4090-class instance is the default starting point; use an A40/A6000 48 GB instance when a selected FLUX or Ollama model needs more VRAM. The scheduled hourly workflow requires the runner to stay online in local FLUX mode.

1. Install the NVIDIA driver and Python 3 with `venv` support.
2. Install Ollama from its official Linux package.
3. Clone this repository and run `bash runner/bootstrap_gpu.sh`.
4. In GitHub, create a new self-hosted runner registration for this repository and assign `self-hosted`, `linux`, `x64`, and `gpu` labels.
5. Install the GitHub runner as a dedicated system service, then manually dispatch **Validate self-hosted GPU runner**.
6. Set repository variables `ARTWORK_BACKEND=flux-local`, `AI_PLANNER_ENABLED=1`, `OLLAMA_BASE_URL=http://127.0.0.1:11434`, and `OLLAMA_MODEL=qwen2.5:7b-instruct` only after validation succeeds.

The registration token is short-lived and must be obtained from GitHub while configuring the physical host. This repository intentionally does not store it. Workflows from untrusted forks must never run on the self-hosted runner.
