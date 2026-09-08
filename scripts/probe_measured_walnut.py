"""Reconstruct Helsinki's acquired walnut rays using their supplied fan-beam matrix.

Download Data82.mat from https://zenodo.org/records/1254206 (CC BY 4.0).
Run: python scripts/probe_measured_walnut.py FILE --output output/walnut
This is a separate measured-data feasibility probe, not the parallel-beam CT app.
"""

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import matplotlib
import numpy as np
import scipy
from scipy.io import loadmat
from scipy.sparse.linalg import LinearOperator, cg, lsqr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SOURCE_SHA = "03a35c57ae52026f980ffcf540a4243a02f198b3fcdd8dff72cb251f70b067cc"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    digest = hashlib.sha256(args.file.read_bytes()).hexdigest()
    if digest != SOURCE_SHA:
        raise ValueError("Expected the published Data82.mat file; SHA-256 differs")
    data = loadmat(args.file, spmatrix=True)
    matrix, measured = data["A"].tocsr(), data["m"]
    assert matrix.shape == (9840, 6724) and measured.shape == (82, 120)
    assert np.isfinite(matrix.data).all() and np.isfinite(measured).all()
    rng = np.random.default_rng(20260908)
    x, y = rng.normal(size=6724), rng.normal(size=9840)
    lhs, rhs = np.dot(matrix @ x, y), np.dot(x, matrix.T @ y)
    adjoint_error = abs(lhs - rhs) / max(abs(lhs), abs(rhs), 1)
    assert adjoint_error < 1e-12
    args.output.mkdir(parents=True, exist_ok=True)
    results, arrays = {}, {}
    alpha = 10.0  # Published example's choice; not tuned against these outputs.
    selections = {"all_120": np.arange(120), "spread_20": np.arange(0, 120, 6),
                  "limited_20": np.arange(20)}
    for name, views in selections.items():
        rows = (views[:, None] * 82 + np.arange(82)).ravel()
        a = matrix[rows]
        b = measured[:, views].ravel(order="F")
        assert np.array_equal(b, measured.ravel(order="F")[rows])
        start = time.perf_counter()
        solved = lsqr(a, b, damp=np.sqrt(alpha), atol=1e-8, btol=1e-8, iter_lim=500)
        elapsed = time.perf_counter() - start
        image = solved[0]
        assert solved[1] in (1, 2, 4, 5), f"LSQR did not converge: {solved[1]}"
        normal = LinearOperator((6724, 6724), matvec=lambda z: a.T @ (a @ z) + alpha * z)
        control, info = cg(normal, a.T @ b, rtol=1e-9, atol=0, maxiter=2000)
        assert info == 0
        relative_control = np.linalg.norm(image - control) / np.linalg.norm(control)
        assert relative_control < 1e-5
        prediction = (matrix @ image).reshape((82, 120), order="F")
        withheld = np.setdiff1d(np.arange(120), views)
        def relative_error(indices):
            return float(np.linalg.norm(prediction[:, indices] - measured[:, indices])
                         / np.linalg.norm(measured[:, indices]))
        arrays[name] = image.reshape((82, 82), order="F")
        arrays[name + "_views"] = views
        results[name] = {"views": views.tolist(), "lsqr_seconds": elapsed,
                         "iterations": solved[2], "stop_code": solved[1],
                         "observed_relative_residual": relative_error(views),
                         "withheld_relative_residual": relative_error(withheld) if len(withheld) else None,
                         "relative_difference_vs_cg": float(relative_control)}
    report = {"source": "https://zenodo.org/records/1254206", "source_sha256": digest,
              "licence": "CC BY 4.0", "attribution": "Hamaläinen et al. (2015), Tomographic X-ray data of a walnut",
              "geometry": "supplied measured fan-beam matrix; native 82 x 82 image",
              "alpha": alpha, "lsqr_atol_btol": 1e-8, "lsqr_iteration_limit": 500,
              "adjoint_relative_error": adjoint_error, "matrix_nonzeros": matrix.nnz,
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "scipy": scipy.__version__, "machine": platform.machine()},
              "cases": results,
              "limitations": "No independent image truth; held-out rays assess prediction, not anatomical accuracy. Fixed alpha is illustrative. First 20 view centres cover 0 to 57 degrees (60-degree sampling sector)."}
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    np.savez_compressed(args.output / "reconstructions.npz", **arrays)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), layout="constrained")
    vmax = float(np.percentile(arrays["all_120"], 99.5))
    for ax, (name, title) in zip(axes, zip(selections, ["120 acquired views", "20 views around the object", "20 views in one 60° sector"])):
        ax.imshow(arrays[name], cmap="gray", vmin=0, vmax=vmax)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.savefig(args.output / "comparison.png", dpi=180)
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
