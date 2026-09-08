# Live reconstruction benchmark

Run `node scripts/benchmark_live.cjs` to reproduce the numerical report. Three measured HTC2022 objects dominate the evaluation; the fourth case uses analytic disk projections. Real references are the authors’ full-data FBP estimates at 96 × 96, not exact physical truth.

Each enhancement starts from the same first-pass reconstruction and adds three passes. “Best” below means lowest reference RMSE among the three enhancement choices tested; it is not a general ranking. Unused rays are withheld from updates, but come from the same acquisition.

| Sample | Views / selection | First-pass RMSE | Lowest enhanced RMSE | Best tested enhancement |
|---|---|---:|---:|---|
| ta | 360 / spread | 0.001929 | 0.001996 | 3 corrections, stronger smoothing |
| ta | 90 / spread | 0.003163 | 0.002005 | 3 corrections, light smoothing |
| ta | 90 / sector | 0.010940 | 0.010434 | 3 corrections, stronger smoothing |
| tb | 360 / spread | 0.001710 | 0.001824 | 3 corrections, stronger smoothing |
| tb | 90 / spread | 0.003968 | 0.001862 | 3 corrections, light smoothing |
| tb | 90 / sector | 0.011749 | 0.011492 | 3 corrections, stronger smoothing |
| tc | 360 / spread | 0.002020 | 0.002112 | 3 corrections, stronger smoothing |
| tc | 90 / spread | 0.003442 | 0.002121 | 3 corrections, light smoothing |
| tc | 90 / sector | 0.011521 | 0.010923 | 3 corrections, stronger smoothing |
| synthetic | 360 / spread | 0.000697 | 0.000331 | 3 corrections, stronger smoothing |
| synthetic | 90 / spread | 0.002420 | 0.000709 | 3 corrections, no smoothing |
| synthetic | 90 / sector | 0.011551 | 0.009318 | 3 corrections, stronger smoothing |

RMSE units: 1/mm. The complete JSON also records MAE, bias, Pearson correlation, regression slope/intercept, prediction R², and selected/unused ray errors. The 90 consecutive views cover 0–44.5° in both acquisitions. Spread selections cover the 360° measured scan or 180° synthetic scan. No clinical or unseen-object claim follows from this small benchmark.

Source: [HTC2022 v1.4.0](https://zenodo.org/records/8041800), Meaney and colleagues (2023), CC BY 4.0.
