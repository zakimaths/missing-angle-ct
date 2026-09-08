# Public acquired CT references

Version 0.2 includes eight original 512 × 512 axial slices from **3D Slicer CTChest**. They are lossless pixel subsets of a public anonymised legacy volume. The acquiring hospital, demographics, diagnosis and original scanner projections are not documented. No institutional endorsement or hospital connection is implied.

Sources: [Slicer sample-data documentation](https://www.slicer.org/wiki/Documentation/4.10/Modules/SampleData), [maintainer clarification of origin and licensing](https://discourse.slicer.org/t/origin-of-ct-chest-sample-data/37731), [official sample registry](https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SampleData/SampleData.py). Data supplied with Slicer is covered by its licence. The full licence and required attribution are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md), the app's source expander and every exported CT bundle.

## Exactly what is included

- Original volume: 139 × 512 × 512 (z, y, x); NRRD int32, gzip.
- Bundled zero-based slice indices: 16, 32, 48, 64, 80, 96, 112, 128. These sample positions across one volume, not eight independent patients.
- In-plane spacing: 0.7617189884185793 mm; slice spacing: 2.5 mm.
- Source coordinates: left-posterior-superior; columns increase toward patient left, rows toward posterior. Original array orientation is preserved.
- Bundled pixels: losslessly converted to int16 after checking range; all other volume metadata omitted. Per-file and pixel checksums are recorded in `src/missing_angle/data/ct-chest.json`.
- Modified products: slice subset, CT display windows, normalised working references, simulated projections and reconstructions. These are identified as derivatives, not original scanner output.

## Display and simulation are separate

The original slice uses standard display presets: lung centre −600 / width 1500 HU, soft tissue 40 / 400, bone 300 / 1500. Window changes never alter source arrays, preprocessing or measurements.

The simulation maps HU using `0.2 × clip(1 + HU/1000, 0, 3)`. This is a declared relative attenuation approximation with an arbitrary water scale. It does not establish a calibrated spectrum, scanner attenuation or patient dose. The entire source rectangle is fitted into the circular two-unit working field, respecting physical aspect ratio, and downsampled with bilinear interpolation and anti-aliasing. No source cropping occurs, though clipping and resampling change the working image. Source pixels remain separately available in the bundle.

The forward model is the raster Radon transform of the prepared reference. FBP and SART reconstruct simulated measurements; RMSE compares them with that reference. This is a matched-discretisation experiment and the source CT already has reconstruction artifacts. It cannot establish clinical accuracy or recoverability from original hospital scanner data. No lesion mask, disease label, ground-truth anatomy or recovery probability is invented.

## Rebuild the bundled subset

The app requires no runtime dataset download. To independently rebuild its eight slice files, obtain the pinned source and run the extraction script:

```sh
mkdir -p data-cache
curl -L --fail 'https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/4507b664690840abb6cb9af2d919377ffc4ef75b167cb6fd0f747befdb12e38e' -o data-cache/CT-chest.nrrd
uv run --locked --no-editable python scripts/prepare_public_ct.py
```

The script rejects a source that does not match SHA-256 `4507b664690840abb6cb9af2d919377ffc4ef75b167cb6fd0f747befdb12e38e` before decoding. It handles only this exact known source format, not arbitrary NRRD imports. Retain the accompanying Slicer licence when redistributing the subset or derivatives.

## Portable experiments

CT bundles use `missing-angle/2`; synthetic bundles retain `missing-angle/1`. CT bundles contain eleven arrays, including original HU pixels, plus the complete acquisition configuration, preprocessing, data source and licence. Import verifies the source against the bundled catalogue's pinned pixel hashes and checks the prepared reference against its saved recipe. Geometry and attribution contribute to the version-2 content identifier. Reconstruction replay uses saved noisy measurements; it does not fetch the source volume or regenerate noise.

The first CT addition is an input-family expansion, not a completed transfer study. Frozen protocols on multiple independently acquired scans, measured sinograms with actual geometry, uncertainty estimates and cross-Mac runs are still future work.
