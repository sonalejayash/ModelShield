"""Optional Ollama transport for the read-only explanation adapter."""

import json
from collections.abc import Callable
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaCompleter:
    """Call a local Ollama generate endpoint without granting tool access."""

    def __init__(
        self,
        *,
        model: str = "llama3.2:3b",
        endpoint: str = "http://127.0.0.1:11434/api/generate",
        timeout_seconds: float = 15.0,
        transport: Callable[..., object] = urlopen,
    ) -> None:
        if not model.strip() or not endpoint.startswith("http"):
            raise ValueError("model and endpoint must be valid")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def __call__(self, prompt: str) -> str:
        """Return Ollama's generated text or fail closed."""
        payload = json.dumps(
            {"model": self.model, "prompt": prompt, "stream": False},
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.transport(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise ValueError("Ollama explanation request failed") from error
        generated = body.get("response") if isinstance(body, dict) else None
        if not isinstance(generated, str) or not generated.strip():
            raise ValueError("Ollama response did not contain generated text")
        return generated