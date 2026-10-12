#!/usr/bin/env python3
"""Fail-fast validation for the owner-managed generation runner."""
from __future__ import annotations

import json
import subprocess
import urllib.request


def main() -> int:
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not gpu:
        raise RuntimeError("No NVIDIA GPU was reported")
    import torch
    import diffusers
    if not torch.cuda.is_available():
        raise RuntimeError("PyTorch CUDA is unavailable")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=10) as response:
        ollama = json.loads(response.read(2_000_000))
    names = [item.get("name", "") for item in ollama.get("models", [])]
    if not any(name.startswith("qwen2.5:7b-instruct") for name in names):
        raise RuntimeError("Required Qwen model is not installed in Ollama")
    print(json.dumps({
        "gpu": gpu,
        "cuda": torch.version.cuda,
        "torch": torch.__version__,
        "diffusers": diffusers.__version__,
        "ollama_models": names,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
