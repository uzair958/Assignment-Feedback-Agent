import json
import time
from typing import Any

from groq import Groq

from app.core.config import settings


class GroqClient:
    def __init__(self) -> None:
        self.enabled = bool(settings.groq_api_key)
        self.client = Groq(api_key=settings.groq_api_key) if self.enabled else None

    def call_json(self, prompt: str, system: str, retries: int = 3) -> dict[str, Any]:
        if not self.enabled:
            return {"_fallback": True, "message": "Groq API key not configured."}

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=2000,
                )
                return json.loads(response.choices[0].message.content)
            except Exception as exc:  # pragma: no cover - network-bound
                last_error = exc
                backoff = 2**attempt
                time.sleep(backoff)

        raise RuntimeError(f"Groq call failed after retries: {last_error}") from last_error

    def call_text(self, prompt: str, system: str, retries: int = 3) -> str:
        if not self.enabled:
            return ""

        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:  # pragma: no cover - network-bound
                last_error = exc
                backoff = 2**attempt
                time.sleep(backoff)

        raise RuntimeError(f"Groq text call failed after retries: {last_error}") from last_error


groq_client = GroqClient()
