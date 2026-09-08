# Validation records

## Version 0.3.0 — student lab and recorded reconstruction

The installed package passed **65 tests in 12.29 seconds** on the same Apple Silicon Mac. Ruff checks and JavaScript syntax checks passed. All 32 demo bundles loaded with matching source, metrics and identifiers; every final animation image matched the displayed smoothed result; four representative cases replayed all saved numerical steps within tolerance. The player completed ten actual steps, supported stepping backward, and reset on changing slice/condition. Mobile content stacked without horizontal page overflow in the inspected viewport.

See [reconstruction evaluation](RECONSTRUCTION.md) for the 32 real-CT comparisons and same-pass unsmoothed controls. Earlier validation hashes below are historical, not current package identifiers. Remote workflow results are recorded on GitHub; local checks alone do not establish cross-Mac reproducibility.


## Version 0.2.0 — public CT addition

On the same M3 Mac and numerical dependency versions below, the installed 0.2.0 package passed **56 tests in 20.09 seconds**, with no warnings; Ruff checks passed. The eight bundled original CT slices passed source-file and pixel checksum checks. Re-extracting all eight slices and the catalogue from the pinned source volume reproduced every file byte for byte (`output/public-ct-preparation-check.json`). The desktop and narrow-screen Public CT interface were inspected in the browser; the final orientation-label correction was installed and the example replay repeated successfully. Tests cover physical-aspect-ratio preservation, full source fitting inside the reconstruction circle, no invented target scores, source attribution rejection, deterministic CT measurements, fresh-process CT regeneration, exact replay with licence retention, old version-1 bundle loading, CT display-window isolation and switching between synthetic and CT workspaces.

The CLI public CT example (slice 80; baseline 48 views / 120° / zero added noise / 128 × 128 / 3 SART passes) gave reference RMSE 0.0323296799 for FBP and 0.0218513201 for SART. These compare with a prepared existing CT image, not anatomical ground truth. Both saved reconstructions replayed exactly, maximum absolute difference 0. Example: `output/public-ct-example.zip`; record: `output/public-ct-replay.json`; content ID `59914b53c9d3b9ff`.

Package source hash: `e53c4cd929f81135b8a04962252675f423253a23987723683d1c128cb1f93003`. Lock hash: `9641f46782ac9574cc0bd238a1a26640111c9492389843f2a0c8f91238e03261`. The source download was independently checked against the SHA-256 in [public CT provenance](PUBLIC_CT.md). The prepared CI workflow now replays both synthetic and CT bundles on Apple Silicon and Intel; those remote jobs remain unrun. The slice subset is one volume, not an independent multi-patient clinical test.

## Version 0.1.0 — original synthetic release

Executed locally on 7 September 2026. This record applies to the initial synthetic release, not to later code changes or clinical use.

## Environment

- Apple M3 MacBook Air, 8 GB memory; arm64; macOS 26.6.2 (Darwin 25.6.0).
- Python 3.12.14; NumPy 2.5.3; SciPy 1.18.1; scikit-image 0.26.0; Streamlit 1.63.0; Matplotlib 3.11.1.
- uv 0.9.17, locked environment, non-editable installed application.
- Lock SHA-256: `1441d84ecf6d4c3f93abe9e664da3ef61813df3c329ce85afece470d0e95fedd`.
- Numerical package source SHA-256: `f2c2269e39c2bafaf4a7519e689ba2c1de3dfee5aeb1ebf537dcb9dfee7f57ce` (all package Python files, including UI).

## Executed checks

| Check | Observed result |
|---|---|
| Installed-package test suite | 36 passed in 5.65 seconds, no warnings |
| Ruff static checks | Passed |
| Official 160 × 160 gallery comparator | FBP RMSE 0.0282741186; one-pass SART 0.0329224247; two-pass SART 0.0213778490, within 2e−7 |
| Analytic disk / superposition / empty object | Passed independent mathematical expectations |
| Translated and rotated ellipse | Agreed with independent sampled line integration within 3e−5 |
| Coordinate orientation | Analytic and raster projected centres agreed within 0.002 physical units |
| Resolution convergence | Disk projection errors decreased over 64, 128, 256; relative error below 0.01 at 256 |
| Acquisition budget | Existing rays and noise identical between 12 and 48 nested views |
| Solver isolation | Changing SART passes/positivity preserved measurements exactly |
| Absent controls | Ground-truth target contrast below 1e−12 for tested widths and grids; no recovery ratio reported |
| Separate-process regeneration | All ten arrays identical between two independent runs of a noisy 64 × 64 case |
| Saved-data replay | FBP and SART bit-for-bit identical, maximum difference 0 |
| Bundle validation | Corrupted arrays, object arrays, invalid ZIPs and unexpected files rejected; imported metrics recomputed |
| Application state | Apply/reset, Atlas-to-Explore, purchases, required prediction/confidence, reveal and new-case reset passed |
| Browser import | Loaded a 192-view, full-span, noisy absent-control bundle; restored controls and displayed exact replay success |
| Interface inspection | Desktop comparison and narrow stacked layout inspected; no horizontal page overflow observed at 487 CSS pixels |
| Independent visual review | Complete; incorrect predictions changed from success styling to warning styling |
| Benchmark smoke | 48 experiments, 96 method observations, all 48 actual-data ZIP bundles saved |

The smoke benchmark used 2 development seeds and 4 held-out test seeds per condition, each paired present/absent. It exercised full, sparse, limited-angle and noisy cases. This is a workflow test, not a meaningful detection performance estimate. Its raw output is under `runs/benchmark-smoke/`; regenerate using the README command.

## Saved baseline

The complete baseline configuration is `experiments/baseline.json`: seed 17, 128 × 128, 48 views, 120° coverage, zero added noise, analytic projection, 3 SART passes without positivity.

| Method | Whole-image RMSE | Known-target contrast | Contrast / reference |
|---|---:|---:|---:|
| Restricted-integral FBP | 0.0917427310 | 0.0512793979 | 34.5481% |
| SART, 3 passes | 0.0334032406 | 0.0660859518 | 44.5236% |

Reference target contrast is 0.1484289497. These values describe one synthetic case, not a general ranking. Experiment identifier: `0071e2288208679f`. The baseline bundle and machine-readable replay record are generated at `runs/baseline.zip` and `runs/replay.json`.

## Not yet established

- Cross-machine or cross-architecture reproducibility. The prepared GitHub workflow uses Apple Silicon and Intel runner labels from the [official runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), but it has not been executed. Its shared-bundle replay will test the current numerical tolerance.
- The full 288-experiment benchmark, statistical uncertainty, threshold calibration adequacy or transfer to unseen phantom families.
- Exhaustive parameter sweeps, arbitrary-angle adaptive acquisition, measured-data geometry, 3D, scanner physics or radiation dose.
- Clinical lesion detection, patient outcomes, medical-device suitability or educational learning gains.
- Bitwise identity of ZIP files, screenshots or floating-point output on every supported dependency/platform combination.

The application preserves sufficient data to inspect and replay a run. That is narrower than guaranteeing that every future environment will reproduce every bit. See [methods](METHODS.md) for the numerical contract and [README](../README.md) for exact commands.

## Version 0.4: live measured projections

Locally passed 70 Python tests and 9 JavaScript tests. The new kernel was checked against analytic ray geometry, disk convergence, the adjoint identity, three independent HTC2022 FBP references, measurement isolation and repeated runs. Browser import/recalculation of a saved 360-view run matched the headless output to a maximum difference of 3.68e-16. A 721-view calculation and subsequent refinement completed in the browser; the same worker also ran in the local Streamlit iframe. Original HTC2022 MATLAB import preserved 721 views and converted the detector spacing correctly.

Visual checks covered the view gallery, selected-angle profile, mobile layout, 200% CSS layout zoom and keyboard view navigation. Non-animated calculation displays the final image and keeps all numerical snapshots for manual inspection; reduced-motion preferences select this mode initially.

CI now runs the JavaScript kernel tests on Linux, Apple Silicon and Intel and exchanges a measured-data JSON run between the two Mac architectures. Check the workflow result for the current commit; these additions do not turn the specimen tests into clinical validation.
