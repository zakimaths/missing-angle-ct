"""Small CPU feasibility probe; not the project or a clinical validation.

Reproduces the numerical part of the scikit-image Radon gallery (160 px),
then checks 128 px timing, independent analytic-disk convergence, and the
effect of FBP angle normalization. Run from a pinned Python environment.
"""
import argparse
import hashlib
import inspect
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy
import skimage
from skimage.data import shepp_logan_phantom
from skimage.transform import iradon, iradon_sart, radon, rescale, resize


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def timed(fn):
    fn()  # one warm-up; excludes imports and installation
    ts = []
    for _ in range(3):
        t = perf_counter()
        a = fn()
        ts.append(perf_counter() - t)
    return a, float(np.median(ts))


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    arrays = {}
    report = {"scope": "Local CPU smoke check only; no feature, user, Intel Mac, or CI evaluation",
              "python": platform.python_version(), "platform": platform.platform(),
              "machine": platform.machine(),
              "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "scikit-image": skimage.__version__},
              "timing_protocol": "one warm-up, median of 3 serial calls; imports excluded; no thread overrides"}
    # Match the official gallery's numerical setup, without its plots.
    official = rescale(shepp_logan_phantom(), scale=0.4, mode="reflect", channel_axis=None)
    theta = np.linspace(0.0, 180.0, max(official.shape), endpoint=False)
    sino = radon(official, theta=theta)
    fbp = iradon(sino, theta=theta, filter_name="ramp")
    sart1 = iradon_sart(sino, theta=theta)
    sart2 = iradon_sart(sino, theta=theta, image=sart1.copy())
    report["official_gallery"] = {"size": list(official.shape), "views": len(theta),
        "fbp_rmse": rmse(fbp, official), "sart1_rmse": rmse(sart1, official), "sart2_rmse": rmse(sart2, official)}
    for name, a in [("official_phantom", official), ("official_sinogram", sino),
                    ("official_fbp", fbp), ("official_sart1", sart1), ("official_sart2", sart2)]:
        arrays[name] = a
    # The 128-pixel result is a separate setup, not the official gallery target.
    phantom = resize(shepp_logan_phantom(), (128, 128), anti_aliasing=True, preserve_range=True)
    theta = np.arange(180.0)
    sino, fwd_time = timed(lambda: radon(phantom, theta=theta, circle=True))
    fbp, fbp_time = timed(lambda: iradon(sino, theta=theta, output_size=128, filter_name="ramp", circle=True))
    sart, sart_time = timed(lambda: iradon_sart(sino, theta=theta, relaxation=0.15))
    report["cpu_128"] = {"views": 180, "forward_median_s": fwd_time, "fbp_median_s": fbp_time,
        "sart1_median_s": sart_time, "fbp_rmse": rmse(fbp, phantom), "sart1_rmse": rmse(sart, phantom)}
    keep = theta < 90
    acquired = sino[:, keep]
    direct = iradon(acquired, theta=theta[keep], output_size=128, circle=True)
    filled = np.zeros_like(sino)
    filled[:, keep] = acquired
    restricted = iradon(filled, theta=theta, output_size=128, circle=True)
    report["restricted_fbp"] = {"observed_angles": "0..89 degrees", "full_grid": "0..179 degrees in 1-degree steps",
        "max_abs_direct_minus_2x_restricted": float(np.max(np.abs(direct - 2 * restricted))),
        "note": "Both use zero angular completion; the direct subset call has twice the angular weight per retained view. This is a convention difference, not proof of a better reconstruction."}
    # This is analytic chord length, not the reconstruction operator used as truth.
    # Fixed physical FOV [-1,1); radius 0.43; 8x8 pixel-area supersampling.
    # Compare center-line analytic rays with the raster projector under refinement.
    convergence = []
    for n in (64, 128, 256):
        dx = 2.0 / n
        coords = (np.arange(n) - n // 2) * dx
        yy, xx = np.meshgrid(coords, coords, indexing="ij")
        raster = np.zeros((n, n), dtype=np.float64)
        offsets = ((np.arange(8) + 0.5) / 8 - 0.5) * dx
        for ox in offsets:
            for oy in offsets:
                raster += ((xx + ox) ** 2 + (yy + oy) ** 2 < 0.43 ** 2)
        raster /= 64
        angles = np.arange(0.0, 180.0, 5.0)
        simulated = radon(raster, theta=angles, circle=True) * dx
        exact = np.broadcast_to((2 * np.sqrt(np.maximum(0.43 ** 2 - coords ** 2, 0)))[:, None], simulated.shape)
        err = float(np.linalg.norm(simulated - exact) / np.linalg.norm(exact))
        convergence.append({"n": n, "pixel_pitch": dx, "relative_l2_projection_error": err})
        arrays[f"disk_raster_{n}"] = raster
        arrays[f"disk_sinogram_{n}"] = simulated
        arrays[f"disk_analytic_{n}"] = exact
    report["analytic_disk"] = {"radius": 0.43, "attenuation": 1, "subsamples_per_axis": 8,
        "angle_step_degrees": 5, "results": convergence,
        "limitation": "Centered disk alone does not validate angle signs, translations, off-axis geometry or independent ellipse inversion."}
    arrays.update(phantom_128=phantom, theta_128=theta, sinogram_128=sino, fbp_128=fbp,
                  sart1_128=sart, acquired_mask=keep, direct_subset_fbp=direct, restricted_fbp=restricted)
    again = iradon(sino, theta=theta, output_size=128, filter_name="ramp", circle=True)
    report["same_process_fbp_bitwise_repeat"] = bool(np.array_equal(again, fbp))
    report["raw_array_sha256"] = {k: digest(v) for k, v in arrays.items()}
    report["iradon_source_sha256"] = hashlib.sha256(inspect.getsource(iradon).encode()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    np.savez_compressed(out / "arrays.npz", **arrays)
    (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k != "raw_array_sha256"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("probe-output"))
    main(parser.parse_args().output)
