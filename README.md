# Missing-Angle CT Detective

**A student lab for understanding how CT images are reconstructed—and what missing views can hide.** Start with a real chest CT slice, change the available X-ray views, compare reconstruction methods and watch the actual correction steps.

[**Try the interactive demo**](https://zakimaths.github.io/missing-angle-ct/) · [Methods and measured improvements](docs/RECONSTRUCTION.md) · [Data source and licence](docs/PUBLIC_CT.md)

The public demo contains **32 recorded experiments using eight real CT slices**. It runs on GitHub Pages without an account. The full local app computes new experiments on your Mac. The source CT images are real; the projections are simulated from those existing images. This is educational software, not a diagnostic tool or dose estimator.

## Run on your Mac

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (`brew install uv` if you use Homebrew), then:

```sh
git clone https://github.com/zakimaths/missing-angle-ct.git
cd missing-angle-ct
uv sync --locked --no-editable
uv run --locked --no-editable angle app --open
```

Or double-click **Launch Missing Angle.command** after installing uv. Setup downloads the pinned Python and dependencies; the app and bundled images then work offline. Open `http://127.0.0.1:8501`, and stop with Control-C in Terminal. Choose another port with `angle app --port 8502`.

Use uv 0.12.10 or newer for a fresh Python download. The Mac workflow pins uv 0.12.10 and installs Python directly, because setup-python does not distribute this security release for macOS. Python 3.12.14 is selected in `.python-version`; `uv.lock` records exact dependencies. `--no-editable` avoids a `.pth` import issue observed on this Mac. After changing source code, rerun the launch command and restart the server.

## What students can do

- **Real CT lab** opens first. Choose a chest slice, viewing angles, coverage and noise; press **Reconstruct this slice**. Display windows help you see lung, soft tissue or bone.
- **Watch the reconstruction** from the blank image through individual views in the first pass, then completed correction passes. Play, pause, step or scrub; no automatic animation starts on arrival.
- **Compare methods:** filtered back projection (FBP), repeated correction (SART), and SART with total-variation smoothing. Switch between images and absolute difference maps, with a shared scale and optional centre zoom. Smoothing can remove both artifacts and useful detail.
- **Download and recalculate** an experiment, including original pixels, measurements, settings and every saved step.
- **Optional synthetic practice, feature challenge and artifact examples** use shapes with known answers to explain concepts that cannot be scored reliably on unlabelled real CT images.

Version 0.3 preserves earlier synthetic and public-CT bundles. No trained model, AI service, GPU, database or user account is required.

## Reproduce an experiment

```sh
uv run --locked --no-editable angle public-ct --slice 80 --config experiments/baseline.json --refine --smoothing 0.002 --refinement-passes 10 --output runs/refined.zip
uv run --locked --no-editable angle replay runs/refined.zip
```

Replay checks FBP, SART, the smoothed result and every saved intermediate step. Exit code 0 means agreement within tolerance, 1 means a numerical mismatch, and 2 means invalid input. Exact equality is reported separately. Archive timestamps may differ; reproducibility concerns numerical contents, not ZIP bytes.

Use `angle run` instead of `angle public-ct` for synthetic experiments. Omitting `--refine` retains the earlier two-method CT format.

## Rebuild the GitHub demo

```sh
uv run --locked --no-editable python scripts/build_demo.py
uv run --locked --no-editable python scripts/verify_demo.py
python3 -m http.server 8000 --directory demo
```

Open `http://localhost:8000`. The builder computes eight slices × four acquisition conditions, actual iteration frames, original images, comparison images and downloadable experiments. It also writes `docs/reconstruction-results.json`, including a ten-pass unsmoothed control. Generated assets are excluded from Git; GitHub Actions rebuilds and deploys them to Pages on pushes to `main`.

Pages serves recorded results; it cannot run the Python server. Use the local app for arbitrary new settings. See [GitHub's Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

## Tests and reproducibility

```sh
uv run --locked --no-editable ruff check src tests scripts app
uv run --locked --no-editable pytest
```

The local installed package passed **67 tests** on Apple Silicon. Tests cover independent projection mathematics, official scikit-image comparators, source integrity, real-image preparation, measurement isolation, replay and application behavior. New checks prove that saved animation steps equal independently recomputed intermediate states and that the refinement solver does not use the reference image.

The scientific GitHub workflow runs Apple Silicon and Intel Mac checks and replays a shared experiment on both architectures. The Pages workflow tests and builds the demo on Linux before deployment. Workflow badges/status on GitHub show the current remote result; [validation records](docs/VALIDATION.md) distinguish local observations from remote execution. Cross-platform comparisons use stated tolerances, not a promise of universal bitwise identity.

## Real measured scanner data

A separate [reproducible walnut probe](docs/MEASURED_DATA.md) reconstructs acquired fan-beam measurements using the published scanner matrix. It checks withheld-ray prediction and runs on the existing CPU stack. This prototype is available from the command line; integration into the student interface and DICOM import are proposed next steps.

## Results and limits

The default refinement reduced mean reference RMSE by **6.9–32.7%** versus three-pass nonnegative SART across four conditions on seven evaluation slices. Slice 80 was used for initial smoothing exploration. All slices belong to one volume, so this is within-volume evidence, not patient-level validation. Ten-pass unsmoothed SART performed better than smoothing in the clean full-angle conditions. [Full methods, comparisons and caveats](docs/RECONSTRUCTION.md).

The source has no verified lesion labels, original scanner projections or documented acquiring hospital. Original CT images already contain reconstruction effects. Measurement count is not a radiation-dose estimate. Future work should use independently acquired volumes and measured sinograms with known scanner geometry.

## Project layout

| Folder | Contents |
|---|---|
| `src/missing_angle/` | Numerical methods, local interface, bundles and CLI |
| `src/missing_angle/data/` | Pinned public CT slices and source catalogue |
| `demo/` | Dependency-free student demo HTML, CSS and JavaScript |
| `scripts/` | Dataset preparation, demo generation and verification |
| `tests/` | Scientific, replay and interface checks |
| `docs/` | Methods, data provenance, results and validation |
| `research/` | Earlier source-based research and feasibility results |
| `.github/workflows/` | Mac reproducibility checks and Pages deployment |

Original application code is MIT licensed. CT data is covered separately by the [3D Slicer terms and attribution](THIRD_PARTY_NOTICES.md), included in every CT export and the demo. Dependencies retain their own licences.
