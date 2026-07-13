"""Deterministic mock client for pipeline development (PRD Phase 2): exercises
prompt building, parsing, scoring, and the batch runner without touching any
real API or free-tier quota. Picks uniformly among the valid options that
are actually present in the prompt -- it has no access to ground truth, so
resulting "accuracy" is expected to hover near chance. That's fine: its job
is to prove the pipeline works, not to produce a meaningful result."""
from __future__ import annotations

import hashlib
import random
import re


class MockClient:
    def __init__(self, name: str = "mock-model", seed: int = 0):
        self.name = name
        self.seed = seed
        self.min_interval_seconds = 0.0

    def generate(self, prompt: str) -> str:
        h = int(hashlib.sha256(f"{self.name}:{self.seed}:{prompt}".encode()).hexdigest(), 16)
        rng = random.Random(h)

        m = re.search(r"Valid locations:\s*(.+)", prompt)
        if m:
            rooms = [r.strip() for r in m.group(1).split(",")]
            choice = rng.choice(rooms)
            return f'{{"assist_location": "{choice}"}}'

        letters = re.findall(r"^([A-C])\)\s*.+$", prompt, re.M)
        if letters:
            letter = rng.choice(letters)
            return f'{{"answer": "{letter}"}}'

        return '{"assist_location": "unknown"}'
