"""Small Ollama/Qwen client with strict JSON responses."""
from __future__ import annotations

import json
import urllib.request
from urllib.parse import urlparse


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "qwen2.5:7b-instruct", timeout: int = 120):
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) URL")
        if parsed.hostname not in {"127.0.0.1", "localhost"} and parsed.scheme != "https":
            raise ValueError("Remote Ollama endpoints must use HTTPS")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def plan(self, objective: str, capabilities: list[str]) -> dict:
        system = (
            "You are the MOSUL HERITAGE planning engine. Return JSON only with a top-level actions array. "
            "Every action must use one supplied capability. Never invent historical facts, credentials, prices, "
            "wallet authority, or completed sales. Mainnet and real-value operations are prohibited."
        )
        prompt = json.dumps({"objective": objective, "allowed_capabilities": capabilities}, ensure_ascii=False)
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "options": {"temperature": 0.1},
        }
        request = urllib.request.Request(
            self.base_url + "/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = json.loads(response.read(2_000_000))
        content = raw.get("message", {}).get("content")
        result = json.loads(content) if isinstance(content, str) else None
        if not isinstance(result, dict) or not isinstance(result.get("actions"), list):
            raise ValueError("Planner returned an invalid action plan")
        return result
