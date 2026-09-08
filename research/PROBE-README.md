# Missing-Angle CT research probe

This is the small feasibility experiment supporting the research report dated 7 September 2026. It is not the proposed application, a feature-recovery benchmark, or clinical validation.

The probe reproduces the numerical calculations of the [official scikit-image Radon gallery](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html), times a separate 128 x 128 setup, compares a raster disk projector with analytic chord lengths under resolution refinement, and checks FBP angular normalization. Code follows the gallery's public numerical setup; the probe and disk test were written for this research. Retain scikit-image's upstream licence and attribution when reusing upstream material.

## Tested environment

- Apple M3 MacBook Air, 8 GB RAM
- macOS 26.6.2 arm64
- Python 3.12.14
- Exact installed scientific package versions in `probe-requirements.txt`
- No GPU, trained model, API key, or dataset download

These are package version pins, not a hash-locked or cross-platform-certified application environment. Dependency installation needs network access. After installation the probe itself runs locally without network requests.

## Re-run

Use Python 3.12.14 for closest reproduction. From the extracted probe folder:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r probe-requirements.txt
.venv/bin/python probe.py --output first-run
.venv/bin/python probe.py --output second-run
.venv/bin/python verify_repeat.py first-run second-run
```

To compare with the research's recorded results:

```sh
.venv/bin/python verify_repeat.py probe-output first-run
```

The comparison checks all actual saved arrays, their shape/dtype, and their reported raw-content SHA-256 values. Exact equality was observed for two independent processes on the original Mac. A failure elsewhere must be investigated; exact cross-Mac equality is not promised. Do not treat this script's assertions as a calibrated scientific tolerance test.

`results.json` records parameters, versions, source hashes and timings; `arrays.npz` contains numerical inputs and outputs. Load with `numpy.load(..., allow_pickle=False)`. Timing is the median of three calls after one warm-up and excludes imports, UI and plotting. Performance will vary with hardware and environment.

The saved centered-disk experiment does not validate translation, angle signs or rotated ellipses. No noisy feature test, user study, browser test, Intel test, ASTRA installation or GitHub CI was run. See the report for the required next validation stages.
