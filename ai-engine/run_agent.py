#!/usr/bin/env python3
"""CLI entry point for the governed local planning engine."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mosul_ai.ollama import OllamaClient
from mosul_ai.orchestrator import Orchestrator, artwork_adapter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objective", default="Generate one source-aware heritage-inspired preview")
    parser.add_argument("--registry", default=str(ROOT.parent / "config" / "ai-capabilities.json"))
    parser.add_argument("--audit", default="data/ai-audit.jsonl")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--generator", default=str(ROOT.parent / "scripts" / "generate_artwork.py"))
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args()
    planner = None
    if os.environ.get("AI_PLANNER_ENABLED", "0") == "1":
        planner = OllamaClient(os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"), os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct"))
    engine = Orchestrator(args.registry, args.audit, planner)
    adapters = {"generate_preview": artwork_adapter(args.output_dir, args.generator)}
    return engine.run(args.objective, adapters, execute=not args.no_execute)


if __name__ == "__main__":
    raise SystemExit(main())
