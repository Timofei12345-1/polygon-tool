"""Общие данные для демо-скриптов профилирования."""
import math
import sys
from pathlib import Path

# чтобы скрипты работали из корня проекта без pip install -e .
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def make_polygon(n: int = 60, radius: float = 100.0):
    """Правильный n-угольник: корректный, без самопересечений."""
    return [
        (
            radius * math.cos(2 * math.pi * i / n),
            radius * math.sin(2 * math.pi * i / n),
        )
        for i in range(n)
    ]
