"""Public acquired CT references; every projection generated here is simulated."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from skimage.transform import radon, resize

from .config import ExperimentConfig
from .experiment import Experiment, evaluate, reconstruct
from .geometry import acquisition_angles, add_noise, coordinates, detector_positions

DATA = Path(__file__).with_name("data")
KIND = "public_ct_simulated_projections"
WINDOWS = {"Lung": (-600, 1500), "Soft tissue": (40, 400), "Bone": (300, 1500)}


def catalogue():
    return json.loads((DATA / "ct-chest.json").read_text())


def licence_text():
    prefix = ('All or portions of this licensed product (such portions are the "Software") '
              "have been obtained under license from The Brigham and Women's Hospital, Inc. "
              "and are subject to the following terms and conditions:\n\n")
    return prefix + (DATA / "SLICER-LICENSE.txt").read_text()


def load_slice(index):
    meta = catalogue()
    entry = next((s for s in meta["slices"] if s["index"] == index), None)
    if entry is None:
        raise ValueError("Choose one of the bundled CT slices")
    path = DATA / entry["file"]
    if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Public CT slice checksum mismatch; restore the bundled dataset")
    raw = np.load(path, allow_pickle=False)
    if raw.shape != (512, 512) or raw.dtype != np.dtype("<i2"):
        raise ValueError("Unexpected public CT data format")
    source = {k: v for k, v in meta.items() if k != "slices"}
    source["slice"] = entry
    return raw.astype(np.float64), source


def validate_source(hu, source):
    meta = catalogue()
    entry = next((s for s in meta["slices"] if s["index"] == source["slice"]["index"]), None)
    expected = {k: v for k, v in meta.items() if k != "slices"}
    expected["slice"] = entry
    if entry is None or source != expected:
        raise ValueError("Unrecognised public CT source or attribution")
    if hu.min() < -32768 or hu.max() > 32767 or not np.array_equal(hu, np.round(hu)):
        raise ValueError("Saved CT pixels differ from the original integer sample")
    if sha256(hu.astype("<i2").tobytes()).hexdigest() != entry["pixel_sha256"]:
        raise ValueError("Saved CT pixels do not match the public source checksum")


def prepare_reference(hu, size, spacing):
    """Fit the entire physical source rectangle inside the circular reconstruction FOV."""
    if hu.ndim != 2 or not np.isfinite(hu).all():
        raise ValueError("A finite 2D CT reference is required")
    if len(spacing) != 2 or any(not np.isfinite(x) or x <= 0 for x in spacing):
        raise ValueError("Positive in-plane pixel spacing is required")
    physical = np.asarray(hu.shape)*spacing
    factor = (size-4)/np.linalg.norm(physical)
    shape = np.maximum(1, np.floor(physical*factor).astype(int))
    density = .2*np.clip(1+hu/1000, 0, 3)
    reduced = resize(density, tuple(shape), order=1, mode="reflect", anti_aliasing=True,
                     preserve_range=True)
    result = np.zeros((size, size), dtype=np.float64)
    top, left = (size-shape)//2
    result[top:top+shape[0], left:left+shape[1]] = reduced
    return result, {"recipe": "ct-relative-attenuation-v1", "water_scale": .2,
        "hu_mapping": "0.2 * clip(1 + HU/1000, 0, 3)", "resampled_shape": shape.tolist(),
        "placement_top_left": [int(top), int(left)],
        "resampling": "bilinear with anti-aliasing, reflect boundaries; full rectangle fitted inside circle",
        "length_units": "normalised field of view, not patient millimetres",
        "display_window_affects_measurements": False}


def run_public_ct(index=80, config=None):
    c = replace(config or ExperimentConfig(), projector="raster", present=False)
    hu, source = load_slice(index)
    reference, preprocessing = prepare_reference(hu, c.size, source["pixel_spacing_yx_mm"])
    theta = acquisition_angles(c)
    clean = radon(reference, theta=theta, circle=True)*(2/c.size)
    measured = add_noise(clean, theta, c.seed, c.noise)
    fbp, sart, times = reconstruct(measured, theta, c)
    x, y = coordinates(c.size)
    arrays = {"phantom": reference, "source_hu": hu,
        "feature_weight": np.zeros_like(reference),
        "background_mask": np.zeros_like(reference, dtype=bool), "support_mask": x*x+y*y <= 1,
        "theta": theta, "detector": detector_positions(c.size), "clean": clean,
        "measured": measured, "fbp": fbp, "sart": sart}
    geometry = {"kind": KIND, "source": source, "preprocessing": preprocessing,
        "field_of_view": 2., "pixel_pitch": 2/c.size,
        "projections": "Simulated raster Radon; no original scanner projection data",
        "reference": "Derived from an already reconstructed public CT image; not anatomical ground truth",
        "fbp_weighting": "restricted angular integral: iradon * span/180",
        "sart_relaxation": .15, "sart_constraints": "nonnegative" if c.nonnegative else "none"}
    return Experiment(c, arrays, geometry, evaluate(arrays, c), times)
