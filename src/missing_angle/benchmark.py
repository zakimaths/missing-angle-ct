"""A declared development/test split for a simple known-location contrast threshold."""
import csv
from dataclasses import replace
from pathlib import Path

import numpy as np

from .bundle import export_bundle, json_bytes, provenance
from .config import ExperimentConfig
from .experiment import run_experiment

PANELS = {
    "full": ExperimentConfig(views=192, span=180, noise=.006),
    "sparse": ExperimentConfig(views=12, span=180, noise=.006),
    "limited": ExperimentConfig(views=192, span=90, noise=.006),
    "noisy": ExperimentConfig(views=192, span=180, noise=.02),
}


def benchmark(output, smoke=False, save_bundles=False, progress=print):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    dev_count, test_count = (2, 4) if smoke else (12, 24)
    rows = []
    for panel, base in PANELS.items():
        progress(f"Computing {panel}…")
        for split, seeds in (("development", range(dev_count)), ("test", range(1000, 1000+test_count))):
            for seed in seeds:
                for present in (False, True):
                    config = replace(base, seed=seed, present=present)
                    exp = run_experiment(config)
                    if save_bundles:
                        (output / f"{panel}-{split}-{seed}-{int(present)}.zip").write_bytes(export_bundle(exp))
                    for method, metrics in exp.metrics["methods"].items():
                        rows.append({"panel": panel, "split": split, "seed": seed,
                                     "present": present, "method": method,
                                     "roi_contrast": metrics["roi_contrast"], "rmse": metrics["rmse"]})
    with (output / "observations.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summaries = []
    for panel in PANELS:
        for method in ("fbp", "sart"):
            group = [r for r in rows if r["panel"] == panel and r["method"] == method]
            dev = [r["roi_contrast"] for r in group if r["split"] == "development" and not r["present"]]
            threshold = float(np.quantile(dev, .95, method="higher"))
            results = {"panel": panel, "method": method, "threshold": threshold}
            for present, label in ((True, "true_positive"), (False, "false_positive")):
                test = [r for r in group if r["split"] == "test" and r["present"] == present]
                count = sum(r["roi_contrast"] > threshold for r in test)
                results[label] = {"count": count, "total": len(test), "rate": count/len(test)}
            summaries.append(results)
    summary = {"purpose": "Pipeline smoke check; too small for performance claims" if smoke else
               "Exploratory known-location contrast threshold evaluation within one phantom family",
               "threshold_rule": "95th percentile of development absent controls, method=higher; score > threshold",
               "limits": "Not autonomous detection, clinical validation, or transfer to unseen phantom families. The target shape and location are supplied. Thresholds are calibrated separately by panel and method. Counts, not nominal 5% FPR, determine observed performance.",
               "development_seeds": list(range(dev_count)),
               "test_seeds": list(range(1000, 1000+test_count)),
               "paired_design": "Present/absent cases share background and noise. Seeds, not individual paired images, are the independent units.",
               "panels": {k: v.to_dict() for k, v in PANELS.items()},
               "provenance": provenance(), "results": summaries}
    (output / "summary.json").write_bytes(json_bytes(summary))
    return summary
