from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from missing_angle.bundle import export_bundle, load_bundle, verify_replay
from missing_angle.config import ExperimentConfig
from missing_angle.public_ct import catalogue, load_slice, prepare_reference, run_public_ct, validate_source


@pytest.mark.parametrize("index", [16, 32, 48, 64, 80, 96, 112, 128])
def test_original_public_slices_match_pinned_pixels(index):
    image, source = load_slice(index)
    validate_source(image, source)
    assert image.shape == (512, 512)
    assert np.isfinite(image).all()
    assert image.min() <= -1000 and image.max() > 500
    assert source["slice"]["index"] == index


def test_invalid_source_selection():
    with pytest.raises(ValueError, match="bundled"):
        load_slice(999)


@pytest.mark.parametrize("size", [64, 128, 256])
def test_preprocessing_preserves_whole_rectangle_inside_circle(size):
    hu = np.zeros((100, 200))  # uniform water, with anisotropic spacing
    ref, recipe = prepare_reference(hu, size, [2., 1.])
    rows, cols = recipe["resampled_shape"]
    assert rows == cols  # physical aspect ratio, not pixel aspect ratio
    assert np.count_nonzero(ref) == rows*cols
    np.testing.assert_allclose(ref[ref > 0], .2)
    yy, xx = np.indices(ref.shape)-size//2
    assert np.count_nonzero(ref[xx*xx+yy*yy > (size//2)**2]) == 0


def test_public_reference_has_no_invented_target_metrics():
    exp = run_public_ct(80, ExperimentConfig(size=64, views=90, span=180, sart_passes=1))
    assert not exp.arrays["feature_weight"].any()
    assert not exp.arrays["background_mask"].any()
    assert exp.metrics["reference_roi_contrast"] is None
    assert all(m["roi_contrast"] is None and m["contrast_recovery"] is None
               for m in exp.metrics["methods"].values())
    assert exp.metrics["methods"]["fbp"]["rmse"] < .02


def test_public_bundle_preserves_source_licence_and_exact_replay():
    exp = run_public_ct(64, ExperimentConfig(size=64, noise=.006, sart_passes=1))
    data = export_bundle(exp)
    with zipfile.ZipFile(BytesIO(data)) as archive:
        assert "PART B. DOWNLOADING AGREEMENT" in archive.read("DATA-LICENSE.txt").decode()
    loaded, manifest = load_bundle(data)
    assert manifest["schema"] == "missing-angle/2"
    for name in exp.arrays:
        np.testing.assert_array_equal(loaded.arrays[name], exp.arrays[name])
    assert all(c["exact"] for c in verify_replay(loaded)["checks"].values())


def test_source_attribution_and_pixels_cannot_be_substituted():
    hu, source = load_slice(80)
    with pytest.raises(ValueError, match="attribution"):
        validate_source(hu, {**source, "title": "A different hospital"})
    hu[0, 0] += 1
    with pytest.raises(ValueError, match="checksum"):
        validate_source(hu, source)


def test_existing_synthetic_bundle_remains_readable():
    data = (Path(__file__).parent / "fixtures/v1-baseline.zip").read_bytes()
    exp, manifest = load_bundle(data)
    assert manifest["schema"] == "missing-angle/1"
    assert "source_hu" not in exp.arrays
    assert all(c["within_tolerance"] for c in verify_replay(exp)["checks"].values())


def test_ct_noise_and_reconstruction_changes_preserve_source():
    a = run_public_ct(80, ExperimentConfig(size=64, views=12, noise=.006, sart_passes=1))
    b = run_public_ct(80, replace(a.config, views=48, sart_passes=2))
    np.testing.assert_array_equal(a.arrays["source_hu"], b.arrays["source_hu"])
    np.testing.assert_array_equal(a.arrays["measured"], b.arrays["measured"][:, ::4])


def test_public_ct_cli_fresh_process_and_replay(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps(ExperimentConfig(size=64, views=24, noise=.006, sart_passes=1).to_dict()))
    runs = []
    for number in (1, 2):
        output = tmp_path / f"ct-{number}.zip"
        subprocess.run([sys.executable, "-m", "missing_angle.cli", "public-ct", "--slice", "80",
                        "--config", str(config), "--output", str(output)], check=True, capture_output=True)
        runs.append(load_bundle(output.read_bytes())[0])
    for name in runs[0].arrays:
        np.testing.assert_array_equal(runs[0].arrays[name], runs[1].arrays[name])


def test_public_ct_ui_apply_window_and_mode_isolation():
    app = Path(__file__).parents[1] / "app/main.py"
    at = AppTest.from_file(str(app), default_timeout=30).run()
    at.radio(key="mode").set_value("Public CT").run()
    assert not at.exception
    before = at.session_state["ct_experiment"].arrays["measured"].copy()
    at.selectbox(key="ct_window").set_value("Bone").run()
    np.testing.assert_array_equal(at.session_state["ct_experiment"].arrays["measured"], before)
    at.selectbox(key="p_slice").set_value(48)
    at.slider(key="p_span").set_value(90.)
    next(b for b in at.button if b.label == "Reconstruct this slice").click().run()
    assert not at.exception
    exp = at.session_state["ct_experiment"]
    assert exp.geometry["source"]["slice"]["index"] == 48 and exp.config.span == 90
    at.radio(key="mode").set_value("Explore").run()
    assert at.session_state["experiment"].config.present
    at.radio(key="mode").set_value("Public CT").run()
    assert at.selectbox(key="p_slice").value == 48
    assert not at.exception


def test_catalogue_does_not_claim_acquiring_hospital():
    assert "not documented" in catalogue()["origin_note"]
