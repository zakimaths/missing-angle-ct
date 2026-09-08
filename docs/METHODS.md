# Methods and numerical contract

The sections below describe the original synthetic experiment contract. Version 0.2 also supports public acquired CT references with simulated projections, no target masks and version-2 bundles; see [the separate CT method and provenance contract](PUBLIC_CT.md). The original synthetic format remains compatible.

## Scope and geometry

Synthetic 2D parallel-beam tomography uses a two-unit field of view. Default resolution is 128 × 128; bounded alternatives are 64 and 256. With pitch `h=2/N`, pixel centres are `x=(column−N/2)h`, `y=(N/2−row)h`; detector centres are `s=(index−N/2)h`. Ray normals are `(cos θ, sin θ)`, with degrees modulo 180.

Views begin at `rotation + k × span/views`, for `k=0…views−1`: left endpoints of equal angular integration cells. The sinogram displays cells on an unwrapped half-turn, with ticks labelled modulo 180. No duplicate endpoint is acquired.

Seeded uniform ellipses generate an anatomy-inspired phantom and optional target. These are not a realistic organ. Target width is the minor diameter in reference pixels at N=128, preserving physical size under grid refinement. The target's major/minor axis ratio is 2.5.

## Independent forward model

For an ellipse with centre `c`, semiaxes `a,b`, orientation `α` and constant density `ρ`:

```text
q(θ) = sqrt(a² cos²(θ−α) + b² sin²(θ−α))
t = s − cx cos θ − cy sin θ
p(s,θ) = 2ρab/q × sqrt(max(1 − (t/q)², 0))
```

Contributions add by superposition. This is the exact line integral of the continuous ideal centre-ray model, not an exact reconstruction. The displayed reference separately estimates pixel-area averages with 4 × 4 samples. The optional raster projector uses `skimage.transform.radon(reference) × h` and is labelled as a matched-model comparator. Finite detector and angular sampling remain assumptions.

Tests integrate occupancy along translated, rotated rays without using the chord formula. A separate raster-to-analytic disk comparison checks error reduction across 64, 128 and 256 pixels.

## Reconstruction

Line integrals are divided by `h` before calling scikit-image, which uses unit pixel pitch. FBP uses the ramp filter and `circle=True`. With measured span Ω, the `iradon` result is multiplied by `Ω/180`: its final `π/(2K)` factor otherwise weights K angles as a whole half-turn. This is a restricted-angular-integral baseline. Its amplitude loss is part of the declared method. Missing angles are not supplied to SART as measured zeros.

SART starts from zero, uses relaxation 0.15 and 1–10 complete passes over measured views. The default has no positivity constraint. Optional nonnegativity clips after each view update, as implemented by scikit-image. SART interpolation can leave small values outside the nominal reconstruction circle; these remain in saved arrays and whole-image metrics.

The residual diagnostic uses a zero-padded raster projection of the whole reconstructed square, retaining the original detector range. It does not silently discard exterior SART values. On analytic data, this residual also includes projector mismatch and cannot independently prove reconstruction correctness.

The official [Radon example](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html), [transform API](https://scikit-image.org/docs/stable/api/skimage.transform.html) and [v0.26.0 implementation](https://github.com/scikit-image/scikit-image/blob/v0.26.0/skimage/transform/radon_transform.py) define the comparators. Gallery reproduction is tested separately at 160 × 160; it does not establish recovery of every limited-angle feature.

## Randomness and budget

NumPy PCG64 uses explicit streams: phantom geometry `SeedSequence([seed,101])`; measurement noise `SeedSequence([seed,202,round(angle_degrees×10^6)])` per angle; puzzle answer stream 303. Nested view packs preserve earlier measurements. Noise is additive Gaussian standard deviation in physical line-integral units. No photon-count, spectrum, scatter, Poisson or dose model is implied. Present/absent benchmark pairs share background and noise.

The puzzle starts with 12 of 96 views. Larger packs cost their additional unique views. Reveal closes purchasing. This is a local educational puzzle, not a secure exam; local source/process inspection can reveal the answer.

## Evaluation

Whole-image RMSE includes all pixels. Support RMSE is separately stored. Target contrast is the area-weighted target mean minus the mean of the saved surrounding annulus. The target's location and shape are supplied even for absent controls; neither enters reconstruction. Present-case contrast recovery divides by the corresponding reference contrast. It can be negative or exceed 100%. Absent controls have no recovery ratio. This is a known-location contrast probe, not autonomous detection or a probability.

Each benchmark panel/method threshold is the 95th percentile (`method="higher"`) of development absent scores. A score strictly greater predicts present. Test seeds are disjoint; observed false-positive and true-positive counts determine performance, not the nominal quantile. The small development set makes thresholds uncertain. Paired seeds are the independent units for later uncertainty analysis, not individual images or pixels. The first smoke run supplies no confidence intervals or transfer claims. Full and sparse panels differ only in view count; full and limited differ only in span; full and noisy differ only in noise.

## Replay and provenance

Each ZIP contains a manifest and ten individual NumPy arrays: reference, target weights, background/support masks, angles, detector coordinates, clean/noisy measurements, FBP and SART. No pickle is accepted and files are never extracted. Imports bound file count, compressed/expanded sizes, array headers, types, dimensions and geometry. SHA-256 hashes and a content identifier detect corruption; they do not authenticate authorship.

Replay reconstructs directly from saved noisy measurements and angles, without regenerating them from a seed. Imported headline metrics are recomputed. The manifest records package/Python/platform versions, source and available lockfile hashes, physical model and parameters. The source hash covers package Python files. A standalone wheel outside the project can lack its original lockfile; that hash is then null. Full environment recreation also needs the repository and lockfile.

Bit-for-bit equality is reported separately from `atol=1e−9, rtol=1e−10` agreement. These are an initial test contract, not yet calibrated across Mac architectures. ZIP timestamps and runtime timings are outside the stable identifier.
