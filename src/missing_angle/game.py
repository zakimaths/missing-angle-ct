"""Finite measurement budget; the hidden answer never changes after purchase."""
from dataclasses import dataclass

import numpy as np

from .config import ExperimentConfig

PACKS = (12, 24, 48, 96)


@dataclass(frozen=True)
class Challenge:
    seed: int = 41
    views: int = 12
    revealed: bool = False

    @property
    def present(self):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([self.seed, 303])))
        return bool(rng.integers(0, 2))

    @property
    def remaining(self):
        return 96 - self.views

    def config(self):
        return ExperimentConfig(seed=self.seed, views=self.views, span=120, noise=.006,
                                present=self.present, feature_width=4, sart_passes=3)

    def buy(self, views):
        if self.revealed or views not in PACKS or views <= self.views:
            raise ValueError("Choose a larger pack before revealing the answer")
        return Challenge(self.seed, views, False)

    def reveal(self):
        return Challenge(self.seed, self.views, True)


PRESETS = {
    "Sparse views": {
        "config": ExperimentConfig(views=12, span=180),
        "description": "Twelve views cover the whole half-turn. Look for streaks from coarse angular sampling.",
    },
    "Missing angles": {
        "config": ExperimentConfig(views=48, span=90, feature_angle=90),
        "description": "Half of the angular domain is unmeasured. Compare directional blur with the full-span case.",
    },
    "Noisy measurements": {
        "config": ExperimentConfig(views=192, span=180, noise=.02),
        "description": "Full angular coverage with additive measurement noise. Watch the trade-off between texture and small-feature contrast.",
    },
}
