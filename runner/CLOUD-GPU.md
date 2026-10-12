# Cloud GPU runner

MOSUL HERITAGE does not require buying a local GPU. A persistent Linux cloud instance can run Ollama, FLUX, and the GitHub self-hosted runner.

## Recommended starting profile

- Ubuntu 24.04 LTS, x86_64
- One NVIDIA RTX 4090-class GPU with 24 GB VRAM
- 8 or more vCPUs and 32 GB or more system RAM
- 100 GB persistent storage for models, caches, and generated previews
- A dedicated non-root runner account
- Outbound HTTPS access to GitHub; no public Ollama port

Move to an A40 or RTX A6000 with 48 GB VRAM only when the chosen FLUX/Ollama model does not fit the 24 GB profile.

## Provider options

1. [Runpod Pods](https://www.runpod.io/product/cloud-gpus): simplest default for a persistent GPU pod and attached storage.
2. [Vast.ai GPU Cloud](https://vast.ai/products/gpu-cloud): marketplace pricing can be lower, but host reliability and security attributes must be reviewed per offer.
3. [Lambda GPU Cloud](https://lambda.ai/instances): managed NVIDIA instances with straightforward VM-style operation, usually better suited to stable production capacity than minimum cost.

Serverless inference is useful for burst traffic, but it is not a permanent GitHub self-hosted runner. For the repository workflow, use a persistent instance or add a separate API-based generation backend.

## Connection procedure

1. Create the cloud instance and persistent volume.
2. Restrict SSH to an administrator IP or private tunnel; do not expose ports `11434` or `7860` publicly.
3. Clone this repository and run `bash runner/bootstrap_gpu.sh`.
4. In repository settings, create a short-lived self-hosted runner registration and apply labels `self-hosted`, `linux`, `x64`, and `gpu`.
5. Install the runner as a service and dispatch **Validate self-hosted GPU runner**.
6. Enable the FLUX/Ollama repository variables only after validation succeeds.

## Cost control

- Stop compute when no generation job is queued, but retain the persistent model volume.
- Set provider spending limits and usage alerts before enabling scheduled generation.
- Treat marketplace/spot instances as interruptible; never store the only copy of an artwork or database on the instance disk.
- Keep signing keys, wallets, and payment secrets out of the GPU host.
