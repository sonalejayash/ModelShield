import json
from typing import Any

import pytest

from intelligence.ollama import OllamaCompleter


class FakeResponse:
    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: Any) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_completer_posts_prompt_and_returns_text() -> None:
    captured: list[Any] = []

    def transport(request: Any, *, timeout: float) -> FakeResponse:
        captured.append((request, timeout))
        return FakeResponse({"response": "{\"decision\": \"PROMOTE\"}"})

    response = OllamaCompleter(transport=transport)("structured evidence")

    assert response == '{"decision": "PROMOTE"}'
    request, timeout = captured[0]
    assert timeout == 15.0
    assert json.loads(request.data)["prompt"] == "structured evidence"


def test_ollama_completer_rejects_missing_response() -> None:
    with pytest.raises(ValueError, match="generated text"):
        OllamaCompleter(transport=lambda *_args, **_kwargs: FakeResponse({}))("prompt")