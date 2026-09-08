# Missing-Angle CT Detective

<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
Students learning CT reconstruction, with the project owner and portfolio reviewers as secondary audiences. Students should understand what a control changes, watch actual reconstruction steps and compare results. Educational effectiveness has not been measured.

## Product Purpose
Measure how incomplete projections, noise and reconstruction assumptions affect synthetic feature recovery and public CT reference fidelity. Every experiment must be testable and replayable locally on macOS.

## Operating Context
Local Python CPU application with a browser interface, command-line experiments and exported numerical bundles. The user requested a public GitHub repository and a working GitHub Pages demo. The demo explores reproducibly recorded real-CT runs; the local app computes new settings.

## Capabilities and Constraints
128 x 128 by default; synthetic 2D parallel-beam CT; FBP and SART; independently computed analytic ellipse projections; optional matched raster projection; explicit noise and angular weighting. No clinical use, radiation-dose claim, AI API or trained model. Explore, a hidden-target puzzle and an artifact atlas share a numerical core. Known-location ROI measurement must be labelled as such.

## Evidence on Hand
The cited research report and original local feasibility measurements are under research/ and output/pdf/. The numerical gallery was reproduced on an M3 Mac. Intel compatibility, educational effectiveness and clinical transfer have not been demonstrated.

## Product Principles
- Keep measurement, reconstruction, evaluation and presentation separate.
- Preserve actual data and settings; a seed alone is insufficient.
- Show fixed image scales and applied settings, including any limitations.
- Separate prediction from reveal in the puzzle.

## Open decisions
The user explicitly requested public / real hospital images in version 0.2. The Public CT workspace includes eight anonymised acquired CT slices from 3D Slicer, with source checksums, licence and preprocessing provenance. Projections are simulated from existing reconstructed images; no original scanner sinograms or verified clinical target labels are supplied. Do not call these references anatomical ground truth or claim a documented acquiring hospital. Version 0.3 makes real CT the default, adds SART/TV refinement and actual iteration playback, and publishes a static GitHub demo. Private hospital-system connections, native packaging and automatic diagnosis remain outside scope.
