from dataclasses import replace

import numpy as np
import pytest
from skimage.data import shepp_logan_phantom
from skimage.transform import iradon, iradon_sart, radon, rescale

from missing_angle.config import ExperimentConfig
from missing_angle.experiment import reconstruct, run_experiment
from missing_angle.geometry import (Ellipse, acquisition_angles, add_noise, analytic_projection,
                                    detector_positions, inside, rasterize)


def test_official_gallery_reference():
    """Independent public comparator at the gallery's 160 × 160 resolution."""
    image = rescale(shepp_logan_phantom(), scale=.4, mode="reflect", channel_axis=None)
    theta = np.linspace(0, 180, max(image.shape), endpoint=False)
    measured = radon(image, theta=theta)
    fbp = iradon(measured, theta=theta, filter_name="ramp")
    sart = iradon_sart(measured, theta=theta)
    assert np.sqrt(np.mean((fbp-image)**2)) == pytest.approx(.0282741186, abs=2e-7)
    assert np.sqrt(np.mean((sart-image)**2)) == pytest.approx(.0329224247, abs=2e-7)
    sart = iradon_sart(measured, theta=theta, image=sart)
    assert np.sqrt(np.mean((sart-image)**2)) == pytest.approx(.0213778490, abs=2e-7)


def test_exact_disk_and_superposition():
    positions = np.array([-.5, -.25, 0, .25, .5])
    disk = Ellipse(0, 0, .5, .5, 27, 2)
    expected = 4*np.sqrt(np.maximum(.25-positions**2, 0))
    actual = analytic_projection([disk], positions, np.array([0, 32, 90, 179]))
    np.testing.assert_allclose(actual, np.repeat(expected[:, None], 4, axis=1), atol=1e-8)
    np.testing.assert_allclose(analytic_projection([disk, disk], positions, [0]), 2*actual[:, :1])
    assert np.count_nonzero(analytic_projection([], positions, [0])) == 0


def test_rotated_translated_ellipse_against_line_quadrature():
    """Integrate occupancy along rays, without using the analytic chord formula."""
    ellipse = Ellipse(.19, -.13, .35, .11, 37, .7)
    angles = np.array([0, 25, 90, 147])
    detectors = np.array([-.1, .03, .17])
    expected = analytic_projection([ellipse], detectors, angles)
    t = np.linspace(-1.5, 1.5, 150001)
    for j, angle in enumerate(np.deg2rad(angles)):
        for i, s in enumerate(detectors):
            x = s*np.cos(angle) - t*np.sin(angle)
            y = s*np.sin(angle) + t*np.cos(angle)
            integrated = np.trapezoid(inside(ellipse, x, y).astype(float)*ellipse.density, t)
            assert integrated == pytest.approx(expected[i, j], abs=3e-5)


def test_raster_projection_converges_to_analytic_disk():
    errors = []
    disk = Ellipse(.08, -.04, .43, .43, 0, 1)
    theta = np.arange(0, 180, 10)
    for size in (64, 128, 256):
        raster = radon(rasterize([disk], size), theta=theta, circle=True)*2/size
        exact = analytic_projection([disk], detector_positions(size), theta)
        errors.append(np.linalg.norm(raster-exact)/np.linalg.norm(exact))
    assert errors[2] < errors[1] < errors[0] < .04
    assert errors[2] < .01


def test_translated_phantom_agrees_with_raster_angle_convention():
    disk = Ellipse(.3, .2, .10, .10, 0, 1)
    detector = detector_positions(128)
    theta = np.array([0., 45., 90., 135.])
    exact = analytic_projection([disk], detector, theta)
    raster = radon(rasterize([disk], 128), theta=theta, circle=True)*2/128
    exact_centres = np.sum(exact*detector[:, None], axis=0)/exact.sum(axis=0)
    raster_centres = np.sum(raster*detector[:, None], axis=0)/raster.sum(axis=0)
    np.testing.assert_allclose(exact_centres, raster_centres, atol=.002)


def test_limited_angle_fbp_is_restricted_integral():
    config = ExperimentConfig(size=64, views=36, span=90, sart_passes=1)
    exp = run_experiment(config)
    unweighted = iradon(exp.arrays["measured"]/(2/64), theta=exp.arrays["theta"], circle=True)
    np.testing.assert_allclose(exp.arrays["fbp"], unweighted*.5, atol=1e-14)


def test_nested_purchases_keep_existing_measurements():
    small = ExperimentConfig(size=64, views=12, noise=.006, sart_passes=1)
    big = replace(small, views=48)
    a, b = run_experiment(small), run_experiment(big)
    np.testing.assert_array_equal(a.arrays["theta"], b.arrays["theta"][::4])
    np.testing.assert_array_equal(a.arrays["measured"], b.arrays["measured"][:, ::4])
    np.testing.assert_array_equal(a.arrays["phantom"], b.arrays["phantom"])


def test_solver_settings_do_not_change_measurements():
    config = ExperimentConfig(size=64, sart_passes=1, noise=.006)
    before = run_experiment(config)
    after = run_experiment(replace(config, sart_passes=2, nonnegative=True))
    np.testing.assert_array_equal(before.arrays["measured"], after.arrays["measured"])
    assert np.min(after.arrays["sart"]) >= 0
    assert np.min(before.arrays["sart"]) < 0


@pytest.mark.parametrize("size", [64, 128])
@pytest.mark.parametrize("width", [2., 6., 10.])
def test_absent_control_and_full_span_recovery(size, width):
    config = ExperimentConfig(size=size, views=128, span=180, present=False,
                              feature_width=width, sart_passes=1)
    absent = run_experiment(config)
    assert abs(absent.metrics["reference_roi_contrast"]) < 1e-12
    assert absent.metrics["methods"]["fbp"]["contrast_recovery"] is None
    present = run_experiment(replace(config, present=True))
    assert present.metrics["reference_roi_contrast"] > .05
    assert present.metrics["methods"]["fbp"]["rmse"] < .04
    assert present.metrics["methods"]["fbp"]["roi_contrast"] > absent.metrics["methods"]["fbp"]["roi_contrast"]


def test_zero_input_remains_zero():
    config = ExperimentConfig(size=64, sart_passes=1)
    theta = acquisition_angles(config)
    measurements = add_noise(np.zeros((64, config.views)), theta, 17, 0)
    fbp, sart, _ = reconstruct(measurements, theta, config)
    assert np.count_nonzero(fbp) == np.count_nonzero(sart) == 0
