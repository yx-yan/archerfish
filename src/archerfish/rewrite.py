"""Turn a raw transcript into a clean prompt with DeepSeek."""

import os
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI, OpenAIError

PROMPT = (Path(__file__).parent / "prompts" / "rewrite.md").read_text()


@dataclass
class Rewrite:
    text: str
    fell_back: bool = False


class Rewriter:
    def __init__(self, client: OpenAI | None = None, model: str = "deepseek-flash", timeout: float = 5):
        self.client = client or OpenAI(
            # A missing key fails on the first call, which falls back to the raw transcript.
            api_key=os.environ.get("DEEPSEEK_API_KEY") or "missing",
            base_url="https://api.deepseek.com",
            max_retries=0,
        )
        self.model = model
        self.timeout = timeout

    def rewrite(self, transcript: str) -> Rewrite:
        """Return the cleaned text, or the raw transcript if the API fails."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": transcript},
                ],
                temperature=0,
                timeout=self.timeout,
                extra_body={"thinking": {"type": "disabled"}},
            )
            text = (response.choices[0].message.content or "").strip()
        except OpenAIError:
            return Rewrite(transcript, fell_back=True)
        return Rewrite(text) if text else Rewrite(transcript, fell_back=True)
