#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "This bootstrap supports Linux x86_64 only." >&2
  exit 2
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "NVIDIA driver is missing. Install the vendor driver, reboot, and run again." >&2
  exit 3
fi
if ! nvidia-smi >/dev/null 2>&1; then
  echo "The NVIDIA driver cannot communicate with the GPU." >&2
  exit 4
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required." >&2
  exit 5
fi

INSTALL_ROOT="${MOSUL_RUNNER_ROOT:-/opt/mosul-runner}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo mkdir -p "$INSTALL_ROOT"
sudo chown "$(id -u):$(id -g)" "$INSTALL_ROOT"

python3 -m venv "$INSTALL_ROOT/venv"
"$INSTALL_ROOT/venv/bin/python" -m pip install --disable-pip-version-check --upgrade pip
"$INSTALL_ROOT/venv/bin/python" -m pip install --disable-pip-version-check \
  -r "$REPO_ROOT/requirements.txt" -r "$REPO_ROOT/requirements-gpu.txt"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed. Install it from https://ollama.com/download/linux and rerun." >&2
  exit 6
fi

if ! systemctl is-active --quiet ollama 2>/dev/null; then
  sudo systemctl enable --now ollama
fi
ollama pull "${OLLAMA_MODEL:-qwen2.5:7b-instruct}"

"$INSTALL_ROOT/venv/bin/python" "$REPO_ROOT/runner/validate_gpu.py"
echo "GPU software is ready. Register this host as a GitHub runner with labels: self-hosted,linux,x64,gpu"
