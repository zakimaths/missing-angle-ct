# Human body CT examples

The live calculator includes four real human CT cross-sections alongside the three Helsinki objects: two chest slices and two abdominal slices from two public volumes. These are actual CT images, not generated anatomy. Their original scanner projection measurements are unavailable. The lab calculates 360 noiseless parallel projections from each image, then reconstructs from those projections starting at zero.

The source preview displays CT values in Hounsfield units (HU). It is separate from the calculated reconstruction. Enhancement, per-angle statistics, source-image errors, region labels and saved-run replay work on all four examples.

## Sources and permissions

| Samples | Original source | Permission |
| --- | --- | --- |
| Chest 64 and 96 | 3D Slicer CTChest, 512 × 512 × 139; 0.7617189884 mm in-plane spacing | 3D Slicer sample-data licence, Part B |
| Abdomen 400 and 480 | Medical Segmentation Decathlon Task03 Liver, case liver_100, distributed as Slicer CTLiver, 512 × 512 × 685; 0.69921875 mm in-plane spacing | CC BY-SA 4.0 |

The [official Slicer sample catalogue](https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SampleData/SampleData.py) identifies the abdominal dataset and its licence. The Medical Segmentation Decathlon dataset is described by [Antonelli and colleagues, Nature Communications (2022)](https://doi.org/10.1038/s41467-022-30695-9). Original image, derived reference and simulated projections retain the applicable source licence; the application code remains MIT. No endorsement by the source institutions is implied.

- [Pinned chest volume](https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/4507b664690840abb6cb9af2d919377ffc4ef75b167cb6fd0f747befdb12e38e)
- [Pinned abdominal volume](https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/e16eae0ae6fefa858c5c11e58f0f1bb81834d81b7102e021571056324ef6f37e)
- [Chest licence](../src/missing_angle/data/SLICER-LICENSE.txt)
- [Attribution and derivative licence notices](../src/missing_angle/data/BODY-CT-LICENSE.txt)
- [CC BY-SA 4.0 terms](https://creativecommons.org/licenses/by-sa/4.0/)

SHA-256 hashes of the original volumes and selected slice files are recorded in the bundled manifests and every derived dataset. Abdominal slices retain float32 HU values; both in-plane axes are reversed to match the chest display convention. Columns increase toward patient left, rows toward posterior. The source images and their existing artifacts are retained. No lesion annotation or diagnosis is inferred.

## Reproduce preparation

The repository includes the four verified source slices, so a normal build and offline use need no large-volume download. In the locked Python environment:

```sh
uv run --locked --no-editable python scripts/prepare_body_ct.py
uv run --locked --no-editable python scripts/build_live_demo.py
```

To independently re-extract abdominal slices, download the pinned abdominal volume above and provide its location:

```sh
uv run --locked --no-editable python scripts/prepare_body_ct.py --liver-volume CTLiver.nrrd
```

The extractor verifies the entire volume checksum before reading its pixels. Re-running preparation with the same locked dependencies produces identical JSON contents. Source projections and reference images are separate files; the worker only receives projection readings and geometry.

## Physical model

HU values map to `0.02 × clip(1 + HU/1000, 0, 3)` per millimetre. The water scale is illustrative, with no assumed match to the scanner's energy spectrum. This is not an absolute calibration of tissue attenuation. Pixel spacing is taken from source metadata.

The square reconstruction field contains the complete original slice, including the table, with a 2% margin around the physical diagonal. There are 360 directions from 0° to 179.5° at 0.5° increments and 192 detector samples across that field. For parallel geometry, 180° spans the distinct line orientations. A view here is a row of calculated detector readings, not a photograph.

Projection preparation uses bilinear sampling of the 512-pixel source and midpoint line integration with steps no larger than half a source pixel. Reconstruction uses a different operator: exact ray lengths through the selected 64, 96 or 128 square pixel grid. The reference independently averages 4 × 4 subpixel samples into 128-pixel reference cells. This avoids using the reconstruction matrix to generate its own test inputs. Comparison at other grid sizes uses the lab's documented bilinear resampling.

## Checks and interpretation

An off-centre Gaussian with an analytic projection checks physical scale, angle convention and orientation independently of any body image. Tests verify source checksums, absence of an answer image in projection inputs, deterministic replay, finite nonnegative results, and both 90-view and 360-view reconstructions of every sample.

At 96 × 96, with all 360 views and one extra pass with light smoothing:

| Sample | First-pass reference RMSE (/mm) | After one extra pass (/mm) | Pearson r after refinement |
| --- | ---: | ---: | ---: |
| Chest 64 | 0.000386 | 0.000326 | 0.9986 |
| Chest 96 | 0.000383 | 0.000324 | 0.9986 |
| Abdomen 400 | 0.000384 | 0.000322 | 0.9993 |
| Abdomen 480 | 0.000352 | 0.000312 | 0.9994 |

These results concern the prepared CT reference and this simulation, not anatomical ground truth. Additional passes beyond this can increase source-reference error despite improving agreement with some projection readings. The body examples therefore default to one extra pass; all refinement settings remain available.

No photon noise, beam hardening, scatter, motion, cone-beam or helical acquisition is reproduced. Withheld simulated views assess this numerical model only. The Helsinki datasets continue to provide a separate test using acquired measurements and the authors' full-scan reconstruction references. Neither dataset establishes clinical validity. Four slices from two volumes are not a population benchmark.
