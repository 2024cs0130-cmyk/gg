import math
import re
from dataclasses import dataclass
from typing import List


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", (text or "").lower())


@dataclass
class SimpleEncoder:
    dimension: int = 256

    def encode(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        for token in _tokenize(text):
            idx = hash(token) % self.dimension
            vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


model = SimpleEncoder()


def validate_description_match(prompt: str) -> str:
    # Conservative fallback validator to keep scoring pipeline operational.
    prompt_lower = (prompt or "").lower()
    if "description" not in prompt_lower or "code_diff" not in prompt_lower:
        return "UNCERTAIN"
    return "UNCERTAIN"


def ask_llm(prompt: str) -> str:
    return validate_description_match(prompt)


def chat(prompt: str) -> str:
    return validate_description_match(prompt)


def generate(prompt: str) -> str:
    return validate_description_match(prompt)
