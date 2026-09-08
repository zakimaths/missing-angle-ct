"""Portable experiment data. Load bounded arrays without extracting files or objects."""
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import json
from pathlib import Path
import platform
import tomllib
import zipfile

import numpy as np

from .config import ExperimentConfig
from .experiment import Experiment, evaluate, replay_experiment
from .geometry import acquisition_angles, detector_positions
from .public_ct import KIND, licence_text, prepare_reference, validate_source
from .refinement import validate_settings, early_counts

SCHEMA = "missing-angle/1"
ARRAY_NAMES = {"phantom", "feature_weight", "background_mask", "support_mask", "theta",
               "detector", "clean", "measured", "fbp", "sart"}
MAX_BYTES = 16 * 1024 * 1024


def json_bytes(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False).encode("utf-8")


def array_digest(array):
    canonical = np.ascontiguousarray(array)
    return sha256(str(canonical.shape).encode() + canonical.dtype.str.encode()
                  + canonical.tobytes()).hexdigest()


def provenance():
    source = Path(__file__).parent
    digest = sha256()
    for path in sorted(source.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    lock = None
    for root in (Path.cwd(), source.parent.parent):
        project = root / "pyproject.toml"
        if (root / "uv.lock").is_file() and project.is_file():
            if tomllib.loads(project.read_text()).get("project", {}).get("name") == "missing-angle-ct":
                lock = root / "uv.lock"
                break
    return {"python": platform.python_version(), "system": platform.system(),
            "system_version": platform.release(), "machine": platform.machine(),
            "packages": {p: version(p) for p in ("missing-angle-ct", "numpy", "scipy",
                                                  "scikit-image", "streamlit", "matplotlib")},
            "source_sha256": digest.hexdigest(),
            "lock_sha256": sha256(lock.read_bytes()).hexdigest() if lock is not None else None}


def experiment_id(experiment):
    content = {"config": experiment.config.to_dict(),
               "arrays": {k: array_digest(v) for k, v in experiment.arrays.items()}}
    if "source_hu" in experiment.arrays:
        content["geometry"] = experiment.geometry
    return sha256(json_bytes(content)).hexdigest()[:16]


def export_bundle(experiment):
    public_ct = "source_hu" in experiment.arrays
    schema = ("missing-angle/4" if "early_history" in experiment.arrays else
              "missing-angle/3" if "history" in experiment.arrays else "missing-angle/2" if public_ct else SCHEMA)
    manifest = {"schema": schema, "id": experiment_id(experiment),
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "config": experiment.config.to_dict(), "geometry": experiment.geometry,
                "metrics": experiment.metrics, "timings": experiment.timings,
                "provenance": provenance(),
                "arrays": {k: array_digest(v) for k, v in experiment.arrays.items()}}
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json_bytes(manifest))
        if public_ct:
            archive.writestr("DATA-LICENSE.txt", licence_text())
        for name in sorted(experiment.arrays):
            buffer = BytesIO()
            np.save(buffer, experiment.arrays[name], allow_pickle=False)
            archive.writestr(f"arrays/{name}.npy", buffer.getvalue())
    return output.getvalue()


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def _read_array(raw, expected_shape, boolean=False):
    stream = BytesIO(raw)
    fmt = np.lib.format.read_magic(stream)
    if fmt == (1, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_1_0(stream, max_header_size=4096)
    elif fmt == (2, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_2_0(stream, max_header_size=4096)
    else:
        raise ValueError("Unsupported array format")
    expected_dtype = np.dtype("bool") if boolean else np.dtype("float64")
    if shape != expected_shape or dtype != expected_dtype or fortran:
        raise ValueError("Unexpected array shape, type or order")
    if len(raw) - stream.tell() != int(np.prod(shape)) * dtype.itemsize:
        raise ValueError("Array byte count does not match its dimensions")
    array = np.load(BytesIO(raw), allow_pickle=False, max_header_size=4096)
    if not np.isfinite(array).all():
        raise ValueError("Arrays must contain finite values")
    return array


def load_bundle(data):
    """Returns (experiment, manifest); hashes detect corruption, not authorship."""
    try:
        return _load_bundle(data)
    except (KeyError, TypeError, OSError, zipfile.BadZipFile, OverflowError,
            EOFError, RecursionError, RuntimeError, NotImplementedError) as error:
        raise ValueError("This is not a valid Missing-Angle experiment bundle") from error


def _load_bundle(data):
    if len(data) > MAX_BYTES:
        raise ValueError("Bundle exceeds the 16 MB limit")
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > 16 or len({i.filename for i in entries}) != len(entries):
            raise ValueError("Unexpected or duplicate bundle files")
        if any(i.flag_bits & 1 or i.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
               for i in entries):
            raise ValueError("Encrypted or unsupported ZIP compression")
        if sum(i.file_size for i in entries) > 2 * MAX_BYTES:
            raise ValueError("Expanded bundle exceeds the 32 MB limit")
        if archive.getinfo("manifest.json").file_size > 128 * 1024:
            raise ValueError("Manifest exceeds the size limit")
        manifest = json.loads(archive.read("manifest.json"), parse_constant=_reject_constant)
        early = manifest["schema"] == "missing-angle/4"
        enhanced = manifest["schema"] in ("missing-angle/3", "missing-angle/4")
        public_ct = manifest["schema"] in ("missing-angle/2", "missing-angle/3", "missing-angle/4")
        if manifest["schema"] not in (SCHEMA, "missing-angle/2", "missing-angle/3", "missing-angle/4"):
            raise ValueError("Unsupported bundle version")
        names = ARRAY_NAMES | {"source_hu"} if public_ct else ARRAY_NAMES
        if enhanced:
            names = names | {"regularized", "history"}
            recipe = validate_settings(manifest["geometry"]["refinement"])
        if early:
            names = names | {"early_history"}
        expected = {"manifest.json"} | {f"arrays/{n}.npy" for n in names}
        if public_ct:
            expected.add("DATA-LICENSE.txt")
        if {i.filename for i in entries} != expected:
            raise ValueError("Unexpected or duplicate bundle files")
        if public_ct and archive.read("DATA-LICENSE.txt").decode() != licence_text():
            raise ValueError("Missing or changed data licence")
        config = ExperimentConfig.from_dict(manifest["config"])
        if set(manifest["config"]) != set(config.to_dict()):
            raise ValueError("Bundle configuration must be complete")
        if set(manifest["arrays"]) != names:
            raise ValueError("Incomplete array checksums")
        arrays = {}
        for name in names:
            shape = ((len(early_counts(config.views)), config.size, config.size) if name == "early_history" else
                     (recipe["passes"]+1, config.size, config.size) if name == "history" else
                     (512, 512) if name == "source_hu" else
                     (config.views,) if name == "theta" else (config.size,) if name == "detector"
                     else (config.size, config.views) if name in ("clean", "measured")
                     else (config.size, config.size))
            array = _read_array(archive.read(f"arrays/{name}.npy"), shape, name.endswith("mask"))
            if array_digest(array) != manifest["arrays"][name]:
                raise ValueError(f"Checksum failed for {name}")
            arrays[name] = array
    if not np.array_equal(arrays["theta"], acquisition_angles(config)):
        raise ValueError("Angles do not match the declared uniform acquisition")
    if not np.array_equal(arrays["detector"], detector_positions(config.size)):
        raise ValueError("Detector coordinates do not match this format")
    if public_ct:
        geometry = manifest["geometry"]
        if not enhanced and "refinement" in geometry:
            raise ValueError("Refinement needs a version-3 bundle")
        if enhanced and (arrays["history"][0].any() or
                         not np.array_equal(arrays["history"][-1], arrays["regularized"])):
            raise ValueError("Iteration history must start at zero and end at the saved reconstruction")
        if geometry.get("kind") != KIND or config.projector != "raster" or config.present:
            raise ValueError("Invalid public CT experiment kind")
        if arrays["feature_weight"].any() or arrays["background_mask"].any():
            raise ValueError("Public CT experiments cannot contain invented target labels")
        spacing = geometry["source"]["pixel_spacing_yx_mm"]
        validate_source(arrays["source_hu"], geometry["source"])
        prepared, recipe = prepare_reference(arrays["source_hu"], config.size, spacing)
        if not np.allclose(prepared, arrays["phantom"], atol=1e-12, rtol=1e-12):
            raise ValueError("Prepared reference does not match saved source CT")
        if geometry["preprocessing"] != recipe:
            raise ValueError("Unsupported CT preprocessing recipe")
    else:
        _validate_synthetic_masks(arrays, manifest)
    if not arrays["support_mask"].any():
        raise ValueError("Empty support mask")
    experiment = Experiment(config, arrays, manifest["geometry"], {}, {})
    if experiment_id(experiment) != manifest["id"]:
        raise ValueError("Experiment identifier does not match its contents")
    experiment.metrics = evaluate(arrays, config)
    return experiment, manifest


def _validate_synthetic_masks(arrays, manifest):
    if (not arrays["background_mask"].any() or not arrays["support_mask"].any()
            or arrays["feature_weight"].sum() <= 0
            or np.min(arrays["feature_weight"]) < 0 or np.max(arrays["feature_weight"]) > 1):
        raise ValueError("Invalid evaluation masks")
    feature = manifest["geometry"]["feature_template"]
    if any(type(feature[k]) not in (int, float) or not np.isfinite(feature[k])
           for k in ("x", "y", "a", "b", "angle", "density")):
        raise ValueError("Invalid feature geometry")
    if not (-1 <= feature["x"] <= 1 and -1 <= feature["y"] <= 1
            and 0 < feature["a"] <= 1 and 0 < feature["b"] <= 1):
        raise ValueError("Feature geometry is out of bounds")


def verify_replay(experiment, manifest=None):
    replay = replay_experiment(experiment)
    checks = {}
    methods = ("fbp", "sart", "regularized", "history") if "history" in experiment.arrays else ("fbp", "sart")
    if "early_history" in experiment.arrays:
        methods += ("early_history",)
    for method in methods:
        before, after = experiment.arrays[method], replay.arrays[method]
        checks[method] = {"exact": bool(np.array_equal(before, after)),
                          "within_tolerance": bool(np.allclose(before, after, atol=1e-9, rtol=1e-10)),
                          "max_absolute_difference": float(np.max(np.abs(before-after)))}
    return {"id": experiment_id(experiment), "checks": checks,
            "tolerance": {"absolute": 1e-9, "relative": 1e-10},
            "saved_environment": manifest.get("provenance") if manifest else None,
            "current_environment": provenance()}
