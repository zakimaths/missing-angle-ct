# Live reconstruction from measured views

Version 0.4 adds a real calculator to [GitHub Pages](https://zakimaths.github.io/missing-angle-ct/). It runs a deterministic JavaScript worker on the user's device, also embedded offline in the Mac app. Clicking **Reconstruct from views** starts from zero and calculates an image using only the selected projection readings and geometry. No existing reconstruction, target image, learned model or remote AI service is passed to this solver.

## Student workflow

1. Choose one of three measured HTC2022 objects, or open a projection JSON file.
2. Inspect every available angle through the sinogram, view slider, detector profile and paginated view gallery.
3. Choose 4–721 views for the bundled data, either distributed through the acquisition or the first angles. Choose a 64, 96 or 128 pixel square grid.
4. Reconstruct. Pause, continue, or advance one view. Every incorporated view produces a real saved first-pass snapshot. The initial 12 views play more slowly to expose image formation. Uncheck view-by-view animation to calculate faster and show only the completed image. This is the default with reduced-motion preferences; all numerical steps remain available for manual inspection.
5. Refine with 1–6 extra correction passes and optional light neighbour smoothing. Inspect the initial image and the change introduced by refinement. Smoothing may soften edges; it is not guaranteed to improve anatomy.
6. Download the measurements or a complete run. Open the saved run and reconstruct again to compare numerical results. Further refinement stages are replayed in order.

The old chest-image experiments remain separately labelled: their new projections are simulated and their public playback is recorded. They do not supply images to the live calculator.

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

Checks cover exact square chord lengths, convergence against analytic disk projections, the adjoint identity, input validation, pause/one-view stepping, repeatability and isolation of unused measurements. Three 360-view reconstructions are compared with the authors' independent full-data FBP references (resized, with units converted). Those reference arrays live only in test fixtures. The initial local check gave correlation above 0.98 and RMSE below 0.004 /mm for all three objects; these are low-resolution implementation checks, not challenge submissions or clinical validation. The Mac workflow runs both Python and JavaScript tests on Apple Silicon and Intel; the Pages build runs them on Linux.

Headless calculation and replay (Node 20 or newer, for developers):

```sh
node scripts/replay_live.cjs src/missing_angle/web/projection-data/ta.json --output runs/live.json
node scripts/replay_live.cjs runs/live.json --output runs/live-replay.json
```

The same measured run is exchanged between Apple Silicon and Intel in CI and checked at 1e-9 absolute tolerance.
