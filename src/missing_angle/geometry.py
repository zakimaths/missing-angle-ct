"""Coordinates: x right, y up; image rows down; detector normal (cos θ, sin θ)."""
from dataclasses import asdict, dataclass

import numpy as np

from .config import ExperimentConfig


@dataclass(frozen=True)
class Ellipse:
    x: float
    y: float
    a: float
    b: float
    angle: float
    density: float

    def to_dict(self):
        return asdict(self)


def coordinates(size):
    h = 2.0 / size
    x = (np.arange(size) - size // 2) * h
    return np.meshgrid(x, -x)


def inside(ellipse, x, y):
    alpha = np.deg2rad(ellipse.angle)
    dx, dy = x - ellipse.x, y - ellipse.y
    u = dx * np.cos(alpha) + dy * np.sin(alpha)
    v = -dx * np.sin(alpha) + dy * np.cos(alpha)
    return (u / ellipse.a)**2 + (v / ellipse.b)**2 <= 1


def rasterize(ellipses, size, samples=4):
    """Pixel-area approximation on a fixed physical grid, independently of projection."""
    if not 1 <= samples <= 16:
        raise ValueError("Raster samples must be 1..16")
    x, y = coordinates(size)
    out = np.zeros((size, size), dtype=np.float64)
    offsets = ((np.arange(samples) + .5) / samples - .5) * (2.0 / size)
    for e in ellipses:
        coverage = np.zeros_like(out)
        for dx in offsets:
            for dy in offsets:
                coverage += inside(e, x + dx, y + dy)
        out += e.density * coverage / samples**2
    return out


def analytic_projection(ellipses, detector, theta):
    """Exact ideal centre-ray chord integrals of continuous uniform ellipses."""
    theta_r = np.deg2rad(theta)
    out = np.zeros((len(detector), len(theta)), dtype=np.float64)
    for e in ellipses:
        phi = theta_r - np.deg2rad(e.angle)
        q = np.sqrt((e.a * np.cos(phi))**2 + (e.b * np.sin(phi))**2)
        t = detector[:, None] - (e.x*np.cos(theta_r) + e.y*np.sin(theta_r))[None, :]
        out += (2 * e.density * e.a * e.b / q)[None, :] * np.sqrt(np.maximum(1 - (t/q)**2, 0))
    return out


def make_phantom(config: ExperimentConfig):
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([config.seed, 101])))
    background = [Ellipse(0, 0, .77, .87, 0, .30),
                  Ellipse(-.30, .14, .17, .30, float(rng.uniform(-15, 15)), -.13),
                  Ellipse(-.22, -.32, .12, .16, float(rng.uniform(0, 180)), .11),
                  Ellipse(.05, -.48, .07, .10, 25, -.08)]
    b = config.feature_width / 128.0
    feature = Ellipse(.27 + float(rng.uniform(-.01, .01)), .12,
                      2.5 * b, b, config.feature_angle, config.contrast)
    ellipses = background + ([feature] if config.present else [])
    truth = rasterize(ellipses, config.size)
    feature_weight = rasterize([Ellipse(feature.x, feature.y, feature.a, feature.b,
                                         feature.angle, 1.0)], config.size)
    x, y = coordinates(config.size)
    radius = np.hypot(x-feature.x, y-feature.y)
    # An annulus entirely inside the homogeneous right-hand background.
    inner = max(.16, 2.5*b + .025)
    bg_mask = (radius > inner) & (radius < inner+.05)
    support = x*x + y*y <= 1
    return truth, feature_weight, bg_mask, support, ellipses, feature


def acquisition_angles(config):
    # Left-endpoint angular cells [start+k*span/K, start+(k+1)*span/K).
    # Divisor packs of 192 share exact angles, enabling repeated acquisition.
    return (config.rotation + np.arange(config.views)*config.span/config.views) % 180


def detector_positions(size):
    return (np.arange(size) - size//2) * 2.0 / size


def add_noise(clean, theta, seed, sigma):
    """Per-angle streams preserve acquired rays when nested view packs grow."""
    result = clean.copy()
    for j, angle in enumerate(theta):
        angle_key = int(round(float(angle) * 1_000_000))
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, 202, angle_key])))
        result[:, j] += rng.normal(0, sigma, len(clean))
    return result
