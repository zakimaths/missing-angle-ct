# Real measured-data feasibility probe

The student app now includes a [live HTC2022 measured-projection calculator](LIVE_RECONSTRUCTION.md), alongside the earlier simulated parallel-beam experiments on real CT images. The separate probe below reconstructs **acquired scanner measurements** using the supplied fan-beam matrix. It does not send fan-beam data into the app's parallel-beam solver.

Download `Data82.mat` (8.1 MB) from [Hämäläinen et al., Tomographic X-ray data of a walnut, 2015](https://zenodo.org/records/1254206). The [Finnish Inverse Problems Society dataset page](https://fips.fi/open-datasets/x-ray-tomographic-datasets/tomographic-x-ray-data-of-a-walnut/) specifies CC BY 4.0. Attribution: Keijo Hämäläinen, Lauri Harhanen, Aki Kallonen, Antti Kujanpää, Esa Niemi and Samuli Siltanen. The probe adapts their Tikhonov example to the smaller Data82 matrix, using SciPy LSQR instead of MATLAB PCG. The source file is not committed.

```sh
uv run --locked --no-editable python scripts/probe_measured_walnut.py /path/to/Data82.mat --output output/walnut
```

The script checks the exact source SHA-256, uses MATLAB column-major ray ordering and solves `||Ax-b||² + 10 ||x||²`. It compares all 120 views, 20 evenly spaced views and the first 20 views (centres 0–57°, a 60° sampling sector). It writes arrays, view indices, method settings, environment, metrics and a comparison image. Alpha 10 comes from the authors' example; it was not tuned using the withheld rays. Negative values are retained in numerical results; only the shared grayscale display clips them.

## Observed on Apple Silicon, 8 September 2026

| Selection | Observed-ray relative residual | Withheld-ray relative residual | LSQR iterations |
|---|---:|---:|---:|
| All 120 views | 3.74% | Not applicable | 59 |
| 20 spread views | 6.96% | 12.72% | 27 |
| 20 views in one sector | 5.14% | 32.98% | 34 |

Residual = Euclidean norm of prediction error divided by the norm of measured rays in that set. The withheld sets differ between the two 20-view selections, so this is an illustrative comparison, not a controlled performance benchmark. A narrower acquisition fitted its observed rays better but predicted withheld rays worse. This is one walnut, not patient validation, and no independent image ground truth was used.

All runs converged. An independent conjugate-gradient normal-equation solve agreed to relative image error below 1.2e-7. The adjoint identity check passed; a second fresh process produced identical numerical arrays on this Mac. Numerical checks are performed by the script. Intel execution of this optional external-data probe has not been tested. It is separate from the Mac CI checks of the main app.

## Next useful functionality

1. Integrate this measured-data adapter into the local lab with explicit geometry, actual per-iteration images and hidden-ray prediction. Keep a fixed evaluation set when comparing methods; reserve another validation set if tuning parameters.
2. Add local conventional CT DICOM import for slice browsing, display windows, physical distances, ROI statistics and line profiles. Importing a reconstructed CT file does not recover the original scanner projections.
3. Extend to [HTC2022](https://zenodo.org/records/8041800), which supplies measured limited-angle data and geometry for physical plastic objects, using a verified fan-beam operator. Hold out entire objects for final evaluation.

Update in version 0.4: the website and Mac app now reconstruct HTC2022 measured projections using a direct fan-beam ray-length solver. The walnut SciPy probe remains separate. DICOM image import is still outside the projection workflow.
