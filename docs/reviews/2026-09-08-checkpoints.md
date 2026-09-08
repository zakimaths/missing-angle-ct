# Reversible reconstruction comparisons

Implemented the first comparison milestone from the project analysis on 8 September 2026.

Completed browser calculations now create named checkpoints. The first pass and up to twelve refinements are retained in the worker as full-precision image states. Restoring a checkpoint also restores its calculation settings and playback branch. Further correction starts from that image while other completed branches remain selectable. Imported reference or saved-answer pixels never seed the worker.

The comparison table identifies the starting checkpoint and reports selected-ray error, unused-ray error and reference RMSE, MAE and bias. Error reports include every checkpoint's region scores under the current reference and annotations. Exports preserve the current checkpoint name and its ordered refinement branch. Alternative branches remain session-local and should be exported individually before starting a new reconstruction or closing the page.

The clinical replay checker now compares loaded volume origin, spacing and direction, in addition to voxel arrays and reported settings. Existing cached 356-view volumes matched exactly in voxel values and passed the physical-header comparison.

Verification:

- 88 Python tests and Ruff checks passed after rebuilding the installed package from the checkout.
- 20 JavaScript tests passed, including exact restoration, independent branches and enforcement of the checkpoint limit.
- All 120 benchmark results remained exactly equal to the preceding report. Only runtime/source provenance changed.
- Real Chromium tests passed on Helsinki measurements, a body-scan simulation and analytic disks. They checked actual displayed-image restoration, labels, stage scores, alternative branch export, command-line replay, browser replay, narrow reflow and invalid-import recovery.
- The GitHub Pages interface was inspected locally at desktop width; the checkpoint controls remained within narrow-screen bounds and no browser warnings/errors were reported in the inspected session.

The new browser workflow runs in GitHub Actions. It uses a separately locked test dependency and does not add a runtime dependency to the public lab. These checks do not replace manual VoiceOver testing or a wider compatibility assessment. Clinical GUI integration, additional patient cases and draft recovery remain later roadmap work.
