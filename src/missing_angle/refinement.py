"""Measured-data-only SART + TV refinement, with exact saved iteration states."""
import numpy as np
from skimage.restoration import denoise_tv_chambolle
from skimage.transform import iradon_sart, order_angles_golden_ratio

ALGORITHM = "sart-tv-v1"


def settings(passes=10, weight=.002):
    if type(passes) is not int or not 1 <= passes <= 20:
        raise ValueError("Refinement passes must be an integer from 1 to 20")
    if type(weight) not in (int, float) or not np.isfinite(weight) or not 0 <= weight <= .02:
        raise ValueError("Smoothing strength must be between 0 and 0.02")
    return {"algorithm": ALGORITHM, "passes": passes, "weight": weight,
            "relaxation": .15, "tv_max_iterations": 100, "tv_eps": .0002,
            "nonnegative": True, "initial_image": "zeros"}


def validate_settings(value):
    if not isinstance(value, dict) or value != settings(value.get("passes"), value.get("weight")):
        raise ValueError("Unsupported refinement settings")
    return value


def iteration_history(measured, theta, size, recipe):
    """No reference image, target mask or clean sinogram is accepted by this solver."""
    validate_settings(recipe)
    image = np.zeros((size, size), dtype=np.float64)
    history = [image.copy()]
    for _ in range(recipe["passes"]):
        image = iradon_sart(measured/(2/size), theta=theta, image=image,
                            relaxation=recipe["relaxation"], clip=(0, np.inf))
        if recipe["weight"]:
            image = denoise_tv_chambolle(image, weight=recipe["weight"],
                                         eps=recipe["tv_eps"],
                                         max_num_iter=recipe["tv_max_iterations"])
        history.append(image.copy())
    return np.stack(history)


def early_counts(views):
    """Bounded checkpoints, dense at the start where image formation is most visible."""
    return sorted({n for n in (1, 2, 3, 4, 6, 8, 12, 20, 32, 64, 128, views) if n <= views})


def first_pass_history(measured, theta, size, recipe):
    """Same SART updates and ordering as one full pass, before its TV step."""
    validate_settings(recipe)
    checkpoints = set(early_counts(len(theta)))
    image = np.zeros((size, size), dtype=np.float64)
    frames = []
    for count, index in enumerate(order_angles_golden_ratio(theta), 1):
        image = iradon_sart(measured[:, index:index+1]/(2/size), theta=theta[index:index+1],
                            image=image, relaxation=recipe['relaxation'], clip=(0, np.inf))
        if count in checkpoints:
            frames.append(image.copy())
    return np.stack(frames)


def refine(experiment, passes=10, weight=.002):
    from .experiment import Experiment, evaluate
    if "source_hu" not in experiment.arrays:
        raise ValueError("This refinement workflow requires a public CT reference")
    recipe = settings(passes, weight)
    arrays = dict(experiment.arrays)
    arrays["history"] = iteration_history(arrays["measured"], arrays["theta"],
                                         experiment.config.size, recipe)
    arrays["regularized"] = arrays["history"][-1].copy()
    arrays["early_history"] = first_pass_history(arrays["measured"], arrays["theta"],
                                                experiment.config.size, recipe)
    return Experiment(experiment.config, arrays, {**experiment.geometry, "refinement": recipe},
                      evaluate(arrays, experiment.config), dict(experiment.timings))
