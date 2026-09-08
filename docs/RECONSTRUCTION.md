# Reconstruction methods and student playback

Version 0.3 adds **nonnegative SART with total-variation (TV) smoothing**, alongside the original FBP and three-pass SART comparators. It starts at zero, applies one complete `iradon_sart` pass (relaxation 0.15; nonnegative clipping), then `denoise_tv_chambolle` (weight 0.002; epsilon 0.0002; maximum 100 TV iterations). Repeat ten times. The local app exposes smoothing strength and 1–20 passes; the demo uses the fixed recipe.

The solver receives only the noisy measurements, angles, image size and method settings. It never receives the reference image, clean projections or a target mask. This is an alternating reconstruction/denoising heuristic, not a proven solution to a jointly optimised objective. TV favours smooth regions and may remove texture or small features. More iterations can amplify noise. The existing restricted-angle FBP scaling is retained so old experiments replay unchanged.

Sources: [scikit-image Radon/SART example](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html), [TV denoising documentation](https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.denoise_tv_chambolle).

## What improved in the measured comparison?

Evaluated all eight bundled real CT slices under four conditions at 128 × 128. Each method receives the same simulated measurements. Slice 80 was used to explore smoothing strengths; the table below averages the other seven slices. Those slices are from the **same volume**, so this is within-volume evaluation, not independent patient validation. Defaults were frozen before computing those seven cases. No method chooses its output by inspecting the reference score.

| Condition | Original SART, 3 passes | SART + TV, 10 passes | SART alone, 10 passes | Reduction vs 3 passes |
|---|---:|---:|---:|---:|
| 180 views, 180°, no noise | 0.002616 | 0.002093 | 0.001700 | 20.0% |
| 48 views, 180°, no noise | 0.006281 | 0.004230 | 0.003452 | 32.7% |
| 48 views, 120°, no noise | 0.017369 | 0.014955 | 0.015004 | 13.9% |
| 48 views, 120°, noise σ 0.006 | 0.019768 | 0.018405 | 0.022391 | 6.9% |

Numbers are mean whole-image RMSE against the prepared CT reference, in relative attenuation units. SART + TV beat three-pass SART on all 28 evaluation cases. **Smoothing was worse than ten-pass unsmoothed SART in the clean full-angle cases.** The 10-pass control separates the effect of extra iterations from smoothing. These findings do not establish better clinical detail recovery. See [raw results](reconstruction-results.json) for every slice, FBP comparisons and recorded environment.

## Actual steps, not a loading animation

Version 0.3.1 also saves individual-view snapshots during the first pass, where most of the visible build-up occurs. The saved history retains the initial zero image and the numerical image after every full correction/smoothing pass. First-pass views use scikit-image's golden-angle order; the last early snapshot followed by TV smoothing equals the first complete pass. Playback renders those arrays at a fixed 0–0.6 display scale. Its last frame is exactly the saved smoothed reconstruction before display conversion. Playback does not interpolate between images or imply wall-clock computation speed. It starts paused, supports play/pause, previous/next and a keyboard-operable step slider, and stops when hidden or scrolled away.

Version-4 CT bundles contain the original 11 arrays plus `regularized`, `history` and `early_history`, with the complete method recipe, source attribution and licence. Import validates bounded settings, history dimensions, source hashes and start/final frames. Replay checks every saved intermediate image as well as FBP, SART and the final smoothed image. Versions 1, 2 and 3 remain supported.

The comparison defaults to absolute difference maps on a shared 0–0.03 relative-attenuation scale. These show error, not anatomy; the reference stays grayscale. Students can switch back to reconstructions or enlarge the central half of each image. Complete-angle reconstructions can look similar because their errors are small, rather than because images are duplicated.

## Reproduce

```sh
uv sync --locked --no-editable
uv run --locked --no-editable angle public-ct --slice 80 --config experiments/baseline.json --refine --smoothing 0.002 --refinement-passes 10 --output runs/refined.zip
uv run --locked --no-editable angle replay runs/refined.zip
uv run --locked --no-editable python scripts/build_demo.py
uv run --locked --no-editable python scripts/verify_demo.py
```

The demo builder recomputes all 32 real-CT runs, a same-pass-count unsmoothed control for each, the full iteration images and downloadable bundles. It writes `docs/reconstruction-results.json`. The browser demo loads those recorded results; arbitrary fresh calculations run in the local Python app. Original data provenance and exact source extraction are documented in [PUBLIC_CT.md](PUBLIC_CT.md).
