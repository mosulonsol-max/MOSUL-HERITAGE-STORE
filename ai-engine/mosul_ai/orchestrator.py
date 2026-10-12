"""Plan, authorize, audit, and execute a tiny set of fixed adapters."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .capabilities import implemented_actions, load_registry
from .ollama import OllamaClient
from .policy import authorize


class Orchestrator:
    def __init__(self, registry_path: str | Path, audit_path: str | Path, planner: OllamaClient | None = None):
        self.registry = load_registry(registry_path)
        self.audit_path = Path(audit_path)
        self.planner = planner

    def _audit(self, event: dict) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        event = {"at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), **event}
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def plan(self, objective: str, executable: list[str] | None = None) -> dict:
        if not self.planner:
            return {"actions": [{"name": "generate_preview", "context": {}}]}
        available = implemented_actions(self.registry)
        if executable is not None:
            available = [name for name in available if name in executable]
        return self.planner.plan(objective, available)

    def run(self, objective: str, adapters: dict[str, Callable[[dict], int]], execute: bool = True) -> int:
        plan = self.plan(objective, sorted(adapters))
        for item in plan["actions"]:
            name = item.get("name") if isinstance(item, dict) else None
            context = item.get("context", {}) if isinstance(item, dict) else {}
            decision = authorize(str(name), context if isinstance(context, dict) else {})
            self._audit({"action": name, "allowed": decision.allowed, "code": decision.code})
            if not decision.allowed:
                return 2
            if execute:
                adapter = adapters.get(str(name))
                if adapter is None:
                    self._audit({"action": name, "allowed": False, "code": "NO_ADAPTER"})
                    return 3
                result = adapter(context)
                if result:
                    return result
        return 0


def artwork_adapter(output_dir: str, generator: str) -> Callable[[dict], int]:
    def execute(_: dict) -> int:
        completed = subprocess.run([sys.executable, generator, "--output-dir", output_dir], env=os.environ.copy(), check=False)
        return completed.returncode
    return execute
