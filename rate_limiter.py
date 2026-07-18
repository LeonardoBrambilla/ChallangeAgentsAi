import time
from collections import deque
from typing import Deque


class RateLimiter:
    """Rate limiter simples em memória (janela deslizante de 60s), para proteger
    APIs externas de terceiros com cota gratuita limitada."""

    def __init__(self, max_per_minute: int, name: str) -> None:
        self.max_per_minute = max_per_minute
        self.name = name
        self._calls: Deque[float] = deque()

    def check(self) -> None:
        now = time.monotonic()
        while self._calls and now - self._calls[0] > 60:
            self._calls.popleft()
        if len(self._calls) >= self.max_per_minute:
            raise RuntimeError(f"Rate limit da tool '{self.name}' excedido. Tente novamente em instantes.")
        self._calls.append(now)
