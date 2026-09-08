"""Small, bounded configuration surface; physical field of view is always 2 units."""
from dataclasses import asdict, dataclass, fields
import math


@dataclass(frozen=True)
class ExperimentConfig:
    seed: int = 17
    size: int = 128
    views: int = 48
    span: float = 120.0
    rotation: float = 0.0
    feature_angle: float = 60.0
    feature_width: float = 6.0  # minor diameter in pixels at the 128 reference grid
    contrast: float = 0.16
    present: bool = True
    noise: float = 0.0  # standard deviation in physical line-integral units
    projector: str = "analytic"
    sart_passes: int = 3
    nonnegative: bool = False

    def __post_init__(self):
        for name in ("seed", "size", "views", "sart_passes"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if not 0 <= self.seed <= 2**32 - 1:
            raise ValueError("seed must be between 0 and 4294967295")
        if self.size not in (64, 128, 256):
            raise ValueError("size must be 64, 128 or 256")
        if not 4 <= self.views <= 360 or not 1 <= self.sart_passes <= 10:
            raise ValueError("views must be 4..360 and SART passes 1..10")
        for name, lo, hi in [("span", 30, 180), ("rotation", 0, 179.999999),
                             ("feature_angle", 0, 179.999999), ("feature_width", 2, 10),
                             ("contrast", 0.02, 0.25), ("noise", 0, 0.05)]:
            val = getattr(self, name)
            if type(val) not in (float, int) or not math.isfinite(val) or not lo <= val <= hi:
                raise ValueError(f"{name} must be a finite number in [{lo}, {hi}]")
        if type(self.present) is not bool or type(self.nonnegative) is not bool:
            raise ValueError("present and nonnegative must be booleans")
        if self.projector not in ("analytic", "raster"):
            raise ValueError("projector must be analytic or raster")

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise ValueError("configuration must be a JSON object")
        unknown = set(value) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown configuration fields: {', '.join(sorted(unknown))}")
        return cls(**value)
