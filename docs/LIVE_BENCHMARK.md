# Live reconstruction benchmark

Run `node scripts/benchmark_live.cjs` to reproduce the report, or add `--check` to compare all 120 results with the committed values at absolute tolerance 1e-9. Source and reference checksums are recorded.

Eight samples: three measured HTC2022 objects, four body slices from two real CT volumes with independently simulated projections, and one analytic disk object. HTC references are the authors’ full-data FBP estimates. Body references are the prepared source images, resampled to the 96 × 96 reconstruction grid. Only the disks have known continuous ground truth.

Each enhancement starts from the same first-pass reconstruction and adds one or three passes. “Best” below means lowest reference RMSE among the four enhancement choices tested; it is not a general ranking or a setting selected by the solver. Unused rays are withheld from updates, but come from the same acquisition or simulation.

| Sample | Views / selection | First-pass RMSE | Lowest enhanced RMSE | Best tested enhancement |
|---|---|---:|---:|---|
| ta | 360 / spread | 0.001929 | 0.001985 | 1 correction, light smoothing |
| ta | 90 / spread | 0.003163 | 0.002005 | 3 corrections, light smoothing |
| ta | 90 / sector | 0.010940 | 0.010434 | 3 corrections, stronger smoothing |
| tb | 360 / spread | 0.001710 | 0.001787 | 1 correction, light smoothing |
| tb | 90 / spread | 0.003968 | 0.001862 | 3 corrections, light smoothing |
| tb | 90 / sector | 0.011749 | 0.011492 | 3 corrections, stronger smoothing |
| tc | 360 / spread | 0.002020 | 0.002093 | 1 correction, light smoothing |
| tc | 90 / spread | 0.003442 | 0.002121 | 3 corrections, light smoothing |
| tc | 90 / sector | 0.011521 | 0.010923 | 3 corrections, stronger smoothing |
| chest-64 | 360 / spread | 0.000386 | 0.000321 | 1 correction, light smoothing |
| chest-64 | 90 / spread | 0.001672 | 0.000403 | 3 corrections, no smoothing |
| chest-64 | 90 / sector | 0.004564 | 0.004064 | 3 corrections, stronger smoothing |
| chest-96 | 360 / spread | 0.000383 | 0.000319 | 1 correction, light smoothing |
| chest-96 | 90 / spread | 0.001647 | 0.000397 | 3 corrections, no smoothing |
| chest-96 | 90 / sector | 0.004500 | 0.004024 | 3 corrections, stronger smoothing |
| abdomen-400 | 360 / spread | 0.000384 | 0.000317 | 1 correction, light smoothing |
| abdomen-400 | 90 / spread | 0.001283 | 0.000402 | 3 corrections, no smoothing |
| abdomen-400 | 90 / sector | 0.006541 | 0.005248 | 3 corrections, stronger smoothing |
| abdomen-480 | 360 / spread | 0.000352 | 0.000308 | 1 correction, light smoothing |
| abdomen-480 | 90 / spread | 0.001222 | 0.000372 | 3 corrections, no smoothing |
| abdomen-480 | 90 / sector | 0.006448 | 0.005049 | 3 corrections, stronger smoothing |
| synthetic | 360 / spread | 0.000697 | 0.000331 | 3 corrections, stronger smoothing |
| synthetic | 90 / spread | 0.002420 | 0.000709 | 3 corrections, no smoothing |
| synthetic | 90 / sector | 0.011551 | 0.009318 | 3 corrections, stronger smoothing |

RMSE units: 1/mm. JSON also records MAE, bias, Pearson correlation, regression slope/intercept, prediction R², and selected/unused ray errors. The 90 consecutive views cover 0–44.5°. Spread selections cover the 360° measured scan or 180° simulated scan. Four slices do not represent four independent patients. No clinical or unseen-patient claim follows from this benchmark.

Sources: [HTC2022 v1.4.0](https://zenodo.org/records/8041800), Meaney and colleagues (2023), CC BY 4.0; [body CT provenance and licences](BODY_CT.md). Measured patient cone-beam projections are evaluated separately in the [clinical workflow](../clinical/README.md).
