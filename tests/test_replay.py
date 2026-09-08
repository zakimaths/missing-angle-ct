from io import BytesIO
import json
import subprocess
import sys
import zipfile

import numpy as np
import pytest

from missing_angle.bundle import export_bundle, load_bundle, verify_replay
from missing_angle.config import ExperimentConfig
from missing_angle.experiment import run_experiment


@pytest.fixture
def experiment():
    return run_experiment(ExperimentConfig(size=64, views=24, noise=.01, sart_passes=1))


def test_bundle_roundtrip_and_replay(experiment):
    loaded, manifest = load_bundle(export_bundle(experiment))
    for key in experiment.arrays:
        np.testing.assert_array_equal(loaded.arrays[key], experiment.arrays[key])
    report = verify_replay(loaded, manifest)
    assert all(c["exact"] for c in report["checks"].values())
    assert manifest["provenance"]["source_sha256"]
    assert manifest["provenance"]["lock_sha256"]


def rewrite_bundle(data, transform):
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(data)) as source, zipfile.ZipFile(output, "w") as target:
        for name in source.namelist():
            target.writestr(name, transform(name, source.read(name)))
    return output.getvalue()


def test_corrupted_measurement_is_rejected(experiment):
    def change(name, data):
        if name != "arrays/measured.npy":
            return data
        array = np.load(BytesIO(data))
        array[0, 0] += 1
        out = BytesIO()
        np.save(out, array)
        return out.getvalue()
    with pytest.raises(ValueError, match="Checksum"):
        load_bundle(rewrite_bundle(export_bundle(experiment), change))


def test_untrusted_object_array_rejected_before_loading(experiment):
    def change(name, data):
        if name != "arrays/phantom.npy":
            return data
        out = BytesIO()
        np.save(out, np.full((64, 64), {"object": "not allowed"}, dtype=object))
        return out.getvalue()
    with pytest.raises(ValueError, match="shape, type"):
        load_bundle(rewrite_bundle(export_bundle(experiment), change))


def test_metadata_metrics_are_recomputed(experiment):
    def change(name, data):
        if name != "manifest.json":
            return data
        manifest = json.loads(data)
        manifest["metrics"] = {"fake": "do not display"}
        return json.dumps(manifest).encode()
    loaded, _ = load_bundle(rewrite_bundle(export_bundle(experiment), change))
    assert loaded.metrics == experiment.metrics


def test_invalid_zip_and_extra_file_rejected(experiment):
    with pytest.raises(ValueError):
        load_bundle(b"not a zip")
    output = BytesIO(export_bundle(experiment))
    with zipfile.ZipFile(output, "a") as archive:
        archive.writestr("../escape", "no")
    with pytest.raises(ValueError, match="Unexpected"):
        load_bundle(output.getvalue())


def test_fresh_process_reproduces_same_arrays(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(json.dumps(ExperimentConfig(size=64, views=24, noise=.006, sart_passes=1).to_dict()))
    bundles = []
    for n in range(2):
        dest = tmp_path / f"{n}.zip"
        subprocess.run([sys.executable, "-m", "missing_angle.cli", "run", "--config", str(config),
                        "--output", str(dest)], check=True, capture_output=True)
        bundles.append(load_bundle(dest.read_bytes())[0])
    for name in bundles[0].arrays:
        np.testing.assert_array_equal(bundles[0].arrays[name], bundles[1].arrays[name])
    replay = subprocess.run([sys.executable, "-m", "missing_angle.cli", "replay", str(dest)],
                            check=True, capture_output=True, text=True)
    assert all(c["exact"] for c in json.loads(replay.stdout)["checks"].values())
