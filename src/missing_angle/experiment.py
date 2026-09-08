"""Measurement and reconstruction are separate; evaluation never enters the solver."""
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from skimage.transform import iradon, iradon_sart, radon

from .config import ExperimentConfig
from .geometry import (acquisition_angles, add_noise, analytic_projection,
                       detector_positions, make_phantom)


@dataclass
class Experiment:
    config: ExperimentConfig
    arrays: dict
    geometry: dict
    metrics: dict
    timings: dict


def reconstruct(measurements, theta, config):
    h = 2.0 / config.size
    # scikit-image uses unit pixel pitch; convert physical integrals explicitly.
    pixel_sino = measurements / h
    start = perf_counter()
    fbp = iradon(pixel_sino, theta=theta, output_size=config.size,
                 filter_name="ramp", circle=True) * (config.span/180.0)
    fbp_time = perf_counter()-start
    start = perf_counter()
    sart = np.zeros((config.size, config.size), dtype=np.float64)
    for _ in range(config.sart_passes):
        sart = iradon_sart(pixel_sino, theta=theta, image=sart, relaxation=.15,
                           clip=(0, np.inf) if config.nonnegative else None)
    return fbp, sart, {"fbp_seconds": fbp_time, "sart_seconds": perf_counter()-start}


def roi_contrast(image, weight, background):
    return float(np.sum(image * weight)/weight.sum() - np.mean(image[background]))


def evaluate(arrays, config):
    truth = arrays["phantom"]
    public_ct = "source_hu" in arrays
    reference = None if public_ct else roi_contrast(truth, arrays["feature_weight"], arrays["background_mask"])
    definition = ("Error relative to a prepared CT image, not anatomical ground truth; no target labels"
                  if public_ct else "Known-location, known-shape contrast probe; not an autonomous detector")
    metrics = {"reference_roi_contrast": reference, "definition": definition, "methods": {}}
    for method in ("fbp", "sart", "regularized") if "regularized" in arrays else ("fbp", "sart"):
        image = arrays[method]
        error = image - truth
        response = None if public_ct else roi_contrast(image, arrays["feature_weight"], arrays["background_mask"])
        # Raster residual is a declared diagnostic projector, including for analytic data.
        # SART can leave small interpolation values just outside the unit circle.
        # Zero-pad the square for this diagnostic; retain the measured detector range.
        projected = radon(image, theta=arrays["theta"], circle=False)
        first = projected.shape[0]//2 - config.size//2
        residual = projected[first:first+config.size] * (2/config.size) - arrays["measured"]
        metrics["methods"][method] = {
            "rmse": float(np.sqrt(np.mean(error**2))),
            "support_rmse": float(np.sqrt(np.mean(error[arrays["support_mask"]]**2))),
            "roi_contrast": response,
            "contrast_recovery": response/reference if not public_ct and config.present and abs(reference)>1e-8 else None,
            "raster_residual_rmse": float(np.sqrt(np.mean(residual**2))),
        }
    return metrics


def run_experiment(config: ExperimentConfig):
    start = perf_counter()
    truth, weight, bg, support, ellipses, feature = make_phantom(config)
    theta = acquisition_angles(config)
    detector = detector_positions(config.size)
    clean = (analytic_projection(ellipses, detector, theta) if config.projector == "analytic"
             else radon(truth, theta=theta, circle=True) * (2/config.size))
    measured = add_noise(clean, theta, config.seed, config.noise)
    acquisition_time = perf_counter()-start
    fbp, sart, times = reconstruct(measured, theta, config)
    arrays = {"phantom": truth, "feature_weight": weight, "background_mask": bg,
              "support_mask": support, "theta": theta, "detector": detector,
              "clean": clean, "measured": measured, "fbp": fbp, "sart": sart}
    geometry = {"field_of_view": 2.0, "pixel_pitch": 2/config.size,
                "axes": "x right, y up; array rows down",
                "angle_convention": "detector normal (cos(theta), sin(theta)); degrees; left-endpoint angular cells",
                "detector_model": "ideal centre rays", "raster_samples_per_axis": 4,
                "ellipses": [e.to_dict() for e in ellipses], "feature_template": feature.to_dict(),
                "noise_model": "additive Gaussian line-integral noise; PCG64; per-angle streams, root seed plus stream 202",
                "fbp_weighting": "restricted angular integral: iradon * span/180",
                "sart_relaxation": .15,
                "sart_constraints": "nonnegative" if config.nonnegative else "none"}
    metrics = evaluate(arrays, config)
    return Experiment(config, arrays, geometry, metrics, {"acquisition_seconds": acquisition_time, **times})


def replay_experiment(experiment):
    """Reuse saved noisy measurements, never regenerate phantom or randomness."""
    arrays = {k:v.copy() for k,v in experiment.arrays.items()}
    arrays["fbp"], arrays["sart"], times = reconstruct(arrays["measured"], arrays["theta"], experiment.config)
    result = Experiment(experiment.config, arrays, experiment.geometry,
                        evaluate(arrays, experiment.config), times)
    if "refinement" in experiment.geometry:
        from .refinement import refine
        recipe = experiment.geometry["refinement"]
        result = refine(result, recipe["passes"], recipe["weight"])
    return result
