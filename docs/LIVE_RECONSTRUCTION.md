# Live reconstruction from measured views

Version 0.4 adds a real calculator to [GitHub Pages](https://zakimaths.github.io/missing-angle-ct/). It runs a deterministic JavaScript worker on the user's device, also embedded offline in the Mac app. Clicking **Reconstruct from views** starts from zero and calculates an image using only the selected projection readings and geometry. No existing reconstruction, target image, learned model or remote AI service is passed to this solver.

## Workflow

1. Choose one of three measured HTC2022 objects, four real body CT examples with simulated views, or open a projection JSON file.
2. Inspect every available angle through the sinogram, view slider, detector profile and paginated view gallery.
3. Choose 4–721 views for the bundled data, either distributed through the acquisition or the first angles. Choose a 64, 96 or 128 pixel square grid.
4. Reconstruct. Pause, continue, or advance one view. Every incorporated view produces a real saved first-pass snapshot. The initial 12 views play more slowly to expose image formation. Uncheck view-by-view animation to calculate faster and show only the completed image. This is the default with reduced-motion preferences; all numerical steps remain available for manual inspection.
5. Refine with 1–6 extra correction passes and optional light neighbour smoothing. Inspect the initial image and the change introduced by refinement. Smoothing may soften edges; it is not guaranteed to improve anatomy.
6. Name and restore completed checkpoints to compare alternative refinements from the same image. The first pass and up to 12 refinement checkpoints remain available until a new reconstruction starts. Restoration uses exact completed worker values; it does not use imported reference pixels.
7. Download the current result before leaving. Its calculation branch and checkpoint name are preserved. Other branches remain in this session; export each result you want to retain. Opening a saved run recalculates its branch from measurements and checks the final values.

The stage comparison table identifies each checkpoint's starting image and reports ray RMSE, reference RMSE, MAE and bias. Error reports also include region statistics for every checkpoint using the currently selected reference and regions. Restoring an image preserves the run's region labels. A lower measurement error can accompany a higher reference error; checkpoints make both outcomes reviewable.

The live body CT samples have 360 simulated views each; see [sources, preparation and checks](BODY_CT.md). The older recorded chest-image experiments remain separately labelled: their new projections are simulated and their public playback is recorded. Source references are kept separate from the live reconstruction worker.

## Acquired data and preparation

The source is [HTC2022 v1.4.0, Meaney, Silva de Moura, Juvonen and Siltanen (2023)](https://zenodo.org/records/8041800), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as also recorded by the [University of Helsinki](https://datakatalogi.helsinki.fi/items/855e0fe3-8898-49fc-85a2-876df8e79492/full). The examples are three physical plastic test objects, not patient scans and not digital synthetic shapes.

Each source contains 721 acquired central-plane views at 0.5-degree steps from 0 to 360 degrees. The first and last share an orientation; they are separate acquired readings, not 721 distinct directions. All angles are retained. The authors already corrected and log-transformed the sinograms. We average four adjacent log readings to reduce 560 detector bins to 140; spacing increases from 0.2 to 0.8 mm. This is a detector-resolution reduction, not a new scan or an intensity-domain noise model. Values are rounded to eight decimal places for compact JSON.

Source-to-origin distance is 410.66 mm; source-to-detector distance is 553.74 mm. The 75.941 mm image field of view follows the authors' 512-pixel reference extent and effective pixel spacing. Each packaged input records attribution, original MATLAB member SHA-256, archive SHA-256 and preprocessing. `scripts/prepare_measured_views.py` checks the published archive MD5 before rebuilding those files. Original download: `htc2022_teaching_data.zip` on the source record.

## Input format

JSON schema `ct-projections/1` requires:

| Field | Meaning |
|---|---|
| `name` | Short dataset description, at most 160 characters |
| `angles_deg` | 4–1440 finite acquisition angles in degrees, in acquisition order |
| `sinogram` | One row per angle; 16–512 equally spaced detector readings per row |
| `geometry.type` | `fan` for a flat detector, or `parallel` |
| `geometry.fov_mm` | Square image extent in millimetres (1–1000) |
| `geometry.detector_spacing_mm` | Detector pitch in millimetres (0.01–20) |
| `geometry.source_distance_mm` | Fan only: source to origin |
| `geometry.detector_distance_mm` | Fan only: origin to detector; **not** source to detector |
| `kind` | `measured` for acquired projections; otherwise label supplied data appropriately |
| `source` | Optional provenance, attribution, licence and preprocessing notes |

Input must contain corrected, log-transformed line integrals, not raw counts, projection photographs or reconstructed CT slices. Entries are bounded to absolute value 100; fan distances must exceed the field of view and be at most 10000 mm. JSON input is limited to 16 MB. A workload cap limits selected views × detector bins × grid width to 14 million. Larger scans require deliberate preprocessing. No arbitrary scanner format or 3D cone-beam reconstruction is claimed.

Download a bundled input for a complete valid example. The Mac app additionally imports the documented HTC2022 `CtDataFull` / `CtDataLimited` MATLAB structure with its calibration metadata. A conventional DICOM image series is not a raw projection file.

## Numerical method

Coordinates follow the [ASTRA fan-flat definition](https://astra-toolbox.com/docs/geom2d.html) and the [authors' HelTomo geometry construction](https://github.com/Diagonalizable/HelTomo/blob/master/create_ct_operator_2d_fan_astra.m). Rows run from positive to negative y; columns run from negative to positive x. At angle zero the source is on negative y and detector index increases along positive x.

The projector calculates each ray's exact segment length through square, constant-valued pixels. Its transpose uses the same lengths. For each selected view, nonnegative SART applies:

`x <- max(0, x + 0.25 * C^-1 * A^T * R^-1 * (b - A*x))`

`R` and `C` are per-view row and column sums of ray lengths. Zero-sensitivity rows and pixels do not contribute an update. The deterministic distributed order visits each selected acquisition exactly once per pass. It is not the scanner's chronological acquisition order. This implementation uses centre rays rather than the authors' strip projector, and a 2D central-plane approximation rather than a full cone model.

Optional smoothing, after each additional full pass, blends each pixel with its four neighbours using strength 0, 0.03 or 0.1. It is a simple smoothing heuristic, **not** TV denoising or learned restoration. Display limits and the ×10 change-map contrast never alter numerical results. Display units are inverse millimetres under the supplied model, not HU.

Agreement is `||A*x - b|| / ||b||`, computed separately for selected and unused views. Unused rays are scored only after reconstruction and never used for correction. Their sets differ when the angle selection changes, so these scores are educational comparisons rather than a controlled algorithm benchmark. Low residual does not establish anatomical correctness.

## Repeat and verify

A `ct-reconstruction/1` download contains the input, geometry, exact selected indices and update order, algorithm version, grid size, complete refinement sequence, initial and final arrays, scores and display limit. It omits intermediate arrays to keep downloads small; replay regenerates the numerical steps. Imported saved images are comparison targets only and never seed a reconstruction. Replay reports maximum absolute difference against a 1e-9 tolerance. Sources and settings remain on the device unless the user explicitly shares the downloaded file.

The shared JavaScript kernel is tested with Node's built-in test runner:

```sh
node --test tests/live_reconstruction.test.cjs
uv run --locked --no-editable pytest
uv run --locked --no-editable python scripts/build_demo.py
```

Checks cover exact square chord lengths, convergence against analytic disk projections, the adjoint identity, input validation, pause/one-view stepping, repeatability and isolation of unused measurements. Three 360-view reconstructions are compared with the authors' independent full-data FBP references (resized, with units converted). Those reference arrays are independently checked against test fixtures and separately available to the comparison UI; they never enter the solver. The initial local check gave correlation above 0.98 and RMSE below 0.004 /mm for all three objects; these are low-resolution implementation checks, not challenge submissions or clinical validation. The Mac workflow runs both Python and JavaScript tests on Apple Silicon and Intel; the Pages build runs them on Linux.

Headless calculation and replay (Node 20 or newer, for developers):

```sh
node scripts/replay_live.cjs src/missing_angle/web/projection-data/ta.json --output runs/live.json
node scripts/replay_live.cjs runs/live.json --output runs/live-replay.json
```

The same measured run is exchanged between Apple Silicon and Intel in CI and checked at 1e-9 absolute tolerance.

## Reference comparisons, error statistics and labels

The lab now defaults to three **real measured** Helsinki objects and also offers a deterministic synthetic test. The synthetic measurements are continuous analytic disk chord lengths, independent of the grid projector. The known shapes are sampled at 8 × 8 subpixels per displayed reference pixel; this introduces a documented raster approximation rather than claiming an exact pixel integral.

The authors’ full-scan FBP images are available separately in `reference-data/`, converted to 1/mm and reduced from 512 to 96 pixels using anti-aliasing. They provide a reconstruction comparator, not exact knowledge of the physical attenuation field. The UI resamples that reference to the selected grid without fitting intensity, rotation, or translation. At 128 pixels the reference still contains only 96-pixel detail. Reference files and labels never enter the reconstruction worker.

The error calculator reports image RMSE, MAE, mean bias and Pearson correlation for the first pass and current result. A signed difference map shows excess attenuation in orange and deficits in blue at ×10 contrast. Labelled rectangular regions provide local mean attenuation and reference RMSE; a large difference is evidence of disagreement, not automatic identification of missing anatomy.

For each detector reading, the reconstructed image is projected through the acquisition geometry. Paired data use **x = measured** and **y = predicted**. Statistics include RMSE, MAE, bias, Pearson r, regression slope and intercept, and prediction R² = 1 − Σ(y−x)² / Σ(x−mean(x))². Prediction R² is distinct from squared correlation and may be negative. Constant or zero-energy data return unavailable values for undefined statistics. Statistics use every pair; the scatter plot shows at most 1,800 evenly sampled pairs. The angle plot scores all acquired views. Download the CSV to examine all readings yourself.

Selected and unused rays are scored separately. Unused rays are not used in image updates, but repeated selection of settings using their errors makes them validation data rather than an untouched final test. Rays are spatially correlated; no independence-based confidence intervals or p-values are claimed. These conventions follow standard [NIST correlation definitions](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm).

Enhancement adds 1, 3 or 6 nonnegative SART passes, optionally followed by neighbour smoothing. The comparison states which errors fell or rose; it does not label every enhancement an improvement. The [reproducible benchmark](LIVE_BENCHMARK.md) compares three additional passes with no, light and stronger smoothing on all three measured objects and the analytic sample, using 360 spread views, 90 spread views and 90 consecutive views.

### Import an aligned reference

Use `ct-reference/1` JSON with `name`, integer `size` (16–512), a flat row-major `image` of `size²` finite attenuation values, `fov_mm` matching the projection input, `units: "1/mm"`, and `orientation: "row-major-top-left"`. Maximum file size: 8 MB. Coordinates must already be registered to the acquisition: matching dimensions alone does not prove alignment. Ordinary HU-valued CT images are not directly compatible with this attenuation reference format.

### Save labels and reproduce comparisons

Name the reconstruction and add up to 30 rectangular regions using percentages from the top-left corner. The image click sets the rectangle position; all coordinates also have keyboard-accessible numeric inputs. Labels are user observations, not AI classifications. The reconstruction export keeps the name, normalised region coordinates, reference, enhancement recipes and numerical results. Reopening it recalculates the image from the measurements and restores the labels. CSV and report JSON exports do not replace the replayable reconstruction file.

## Interface and import safeguards

The live lab provides section navigation, a text table for each selected detector profile and descriptive playback sliders. Every first-pass view remains available; later refinement retains one image per completed pass to bound memory. Importing original MATLAB files checks decompressed size, array dimensions, numeric payload sizes and structure depth before parsing with SciPy. See the [quality review](reviews/2026-09-08-quality.md).
