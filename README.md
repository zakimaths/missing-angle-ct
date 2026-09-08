# Missing-Angle CT Detective

**Reconstruct a new image from hundreds of measured X-ray views, directly on your device.** Inspect the angles, choose a view budget, watch the calculation and refine the image. A reconstruction lab for examining how measurement coverage affects image detail.

[**Try the interactive demo**](https://zakimaths.github.io/missing-angle-ct/) · [Methods and measured improvements](docs/RECONSTRUCTION.md) · [Data source and licence](docs/PUBLIC_CT.md)

The public site now includes a **live reconstruction calculator with three acquired object datasets with 721 views each, plus four real body CT samples with 360 simulated views each**. It computes on your device from projection readings and scanner geometry; no existing reconstruction is used as an answer. Open your own projection JSON or an exported run. The Mac app also imports original HTC2022 MATLAB projection files. [Body CT sources and reproducible preparation](docs/BODY_CT.md). Chest and abdominal samples include source previews, live reconstruction, enhancement, statistics and labels. The separate gallery retains 32 recorded experiments on real chest images with simulated projections. [Live workflow, input format, data attribution and methods](docs/LIVE_RECONSTRUCTION.md). This is educational software, not a diagnostic tool or dose estimator.

## Run on your Mac

**Measured patient projections are available through the optional [clinical CPU workflow](clinical/README.md).** It reconstructs a full 3D volume from 356 acquired views in one public COBRA2026 case, compares subsets with the authors' reference, and verifies an offline repeat. This workflow has its own locked dependencies; the browser's body examples remain simulations. [Measured clinical results](clinical/README.md#observed-comparison).

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (`brew install uv` if you use Homebrew), then:

```sh
git clone https://github.com/zakimaths/missing-angle-ct.git
cd missing-angle-ct
uv sync --locked --no-editable
uv run --locked --no-editable angle app --open
```

Or double-click **Launch Missing Angle.command** after installing uv. Setup downloads the pinned Python and dependencies; the app and bundled images then work offline. Open `http://127.0.0.1:8501`, and stop with Control-C in Terminal. Choose another port with `angle app --port 8502`.

Use uv 0.12.10 or newer for a fresh Python download. The Mac workflow pins uv 0.12.10 and installs Python directly, because setup-python does not distribute this security release for macOS. Python 3.12.14 is selected in `.python-version`; `uv.lock` records exact dependencies. `--no-editable` avoids a `.pth` import issue observed on this Mac. After changing source code, rerun the launch command and restart the server.

## Available functions

- **Reconstruct from views** opens first: inspect 721 measured angles, choose a subset, calculate from zero, pause or step one view, and refine with further corrections. Download and replay the run.
- **CT image experiments** remain available. Choose a chest slice, viewing angles, coverage and noise; press **Reconstruct this slice**. Display windows help you see lung, soft tissue or bone.
- **Watch the reconstruction** from the blank image through individual views in the first pass, then completed correction passes. Play, pause, step or scrub; no automatic animation starts on arrival.
- **Compare methods:** filtered back projection (FBP), repeated correction (SART), and SART with total-variation smoothing. Switch between images and absolute difference maps, with a shared scale and optional centre zoom. Smoothing can remove both artifacts and useful detail.
- **Restore and compare checkpoints:** name completed images and return to an earlier result before trying another refinement. Compare each checkpoint with its starting image and export the calculation branch you want to retain.
- **Download and recalculate** an experiment, including original pixels, measurements, settings and every saved step.
- **Optional synthetic practice, feature challenge and artifact examples** use shapes with known answers to explain concepts that cannot be scored reliably on unlabelled real CT images.

Version 0.4 preserves earlier synthetic and public-CT bundles. No trained model, AI service, GPU, database or user account is required.

## Reproduce an experiment

```sh
uv run --locked --no-editable angle public-ct --slice 80 --config experiments/baseline.json --refine --smoothing 0.002 --refinement-passes 10 --output runs/refined.zip
uv run --locked --no-editable angle replay runs/refined.zip
```

Replay checks FBP, SART, the smoothed result and every saved intermediate step. Exit code 0 means agreement within tolerance, 1 means a numerical mismatch, and 2 means invalid input. Exact equality is reported separately. Archive timestamps may differ; reproducibility concerns numerical contents, not ZIP bytes.

Use `angle run` instead of `angle public-ct` for synthetic experiments. Omitting `--refine` retains the earlier two-method CT format.

## Rebuild the GitHub demo

Install Node 22.23.2 alongside the Python environment. The builder uses the browser solver to generate the introductory comparison from measured projections.

```sh
uv run --locked --no-editable python scripts/build_demo.py
uv run --locked --no-editable python scripts/verify_demo.py
python3 -m http.server 8000 --directory demo
```

Open `http://localhost:8000`. The builder computes eight slices × four acquisition conditions, actual iteration frames, original images, comparison images and downloadable experiments. It also writes `docs/reconstruction-results.json`, including a ten-pass unsmoothed control. Generated assets are excluded from Git; GitHub Actions rebuilds and deploys them to Pages on pushes to `main`.

Pages runs the new JavaScript reconstruction worker and also serves the recorded chest-image gallery. It cannot run the Python server; the local app adds MATLAB ingestion and the full earlier Python tools. See [GitHub's Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Tests and reproducibility

```sh
uv run --locked --no-editable ruff check src tests scripts app
uv run --locked --no-editable pytest
```

The local installed package passed **88 Python tests and 21 JavaScript tests** on Apple Silicon. Tests cover independent projection mathematics, official scikit-image comparators, source integrity, real-image preparation, measurement isolation, replay and application behavior. New checks prove that saved animation steps equal independently recomputed intermediate states and that the refinement solver does not use the reference image.

The scientific GitHub workflow runs Apple Silicon and Intel Mac checks and replays a shared experiment on both architectures. The Pages workflow tests and builds the demo on Linux before deployment. Workflow badges/status on GitHub show the current remote result; [validation records](docs/VALIDATION.md) distinguish local observations from remote execution. Cross-platform comparisons use stated tolerances, not a promise of universal bitwise identity.

The [browser regression workflow](qa/README.md) exercises checkpoint restoration, alternative refinements, labels and exported-run replay on measured, body-simulation and analytic examples. Pages deployment also requires complete-demo checks in Chromium and WebKit, including keyboard access, automated accessibility, narrow reflow, shared links, quick comparisons and the recorded gallery.

The introduction includes two actual 90-view reconstructions. Quick comparisons calculate spread and consecutive selections, and acquisition links share sample and control settings without including private inputs or labels. Recorded experiments load only when opened. [Sharing image, attribution and post drafts](docs/launch/README.md).

## Real measured scanner data

The [live measured-view lab](docs/LIVE_RECONSTRUCTION.md) is integrated into both the website and local app. A separate [walnut probe](docs/MEASURED_DATA.md) remains available as an independent SciPy baseline. DICOM image import is outside the projection-input workflow.

## Results and limits

The default refinement reduced mean reference RMSE by **6.9–32.7%** versus three-pass nonnegative SART across four conditions on seven evaluation slices. Slice 80 was used for initial smoothing exploration. All slices belong to one volume, so this is within-volume evidence, not patient-level validation. Ten-pass unsmoothed SART performed better than smoothing in the clean full-angle conditions. [Full methods, comparisons and caveats](docs/RECONSTRUCTION.md).

The chest-image source used for that refinement study has no verified lesion labels, original scanner projections or documented acquiring hospital. Original CT images already contain reconstruction effects. Measurement count is not a radiation-dose estimate. Future work should use independently acquired volumes and measured sinograms with known scanner geometry.

## Project layout

| Folder | Contents |
|---|---|
| `src/missing_angle/` | Numerical methods, local interface, bundles and CLI |
| `src/missing_angle/data/` | Pinned public CT slices and source catalogue |
| `demo/` | Dependency-free reconstruction demo HTML, CSS and JavaScript |
| `scripts/` | Dataset preparation, demo generation and verification |
| `tests/` | Scientific, replay and interface checks |
| `docs/` | Methods, data provenance, results and validation |
| `research/` | Earlier source-based research and feasibility results |
| `.github/workflows/` | Mac reproducibility checks and Pages deployment |

Original application code is MIT licensed, except the adapted [clinical module](clinical/NOTICE), which is Apache-2.0. COBRA2026 data and derived images have separate CC BY-NC 4.0 terms. CT data is covered separately by the [3D Slicer terms and attribution](THIRD_PARTY_NOTICES.md), included in every CT export and the demo. Dependencies retain their own licences.

The live lab also includes reference-image error maps, paired measurement statistics, before/after enhancement scores and saved region labels. Three real measured objects remain the default examples; an analytic disk test adds known ground truth. See the [live benchmark](docs/LIVE_BENCHMARK.md) and [comparison guide](docs/LIVE_RECONSTRUCTION.md#reference-comparisons-error-statistics-and-labels).

[Accessibility, security and design review](docs/reviews/2026-09-08-quality.md) records the checks, fixes and remaining verification limits.
