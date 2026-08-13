"""Noise generation utilities for OrbusSim Dummy V2."""
import random
from typing import Optional


def create_rng(seed: Optional[int]) -> random.Random:
    """Erstellt einen seeded Random-Generator. Wenn seed None ist, nutzt er System-Zufall."""
    rng = random.Random()
    if seed is not None:
        rng.seed(seed)
    return rng


def add_noise(value: float, std: float, rng: random.Random) -> float:
    """Fügt Gaussian Noise hinzu."""
    if std <= 0:
        return value
    return value + rng.gauss(0, std)
