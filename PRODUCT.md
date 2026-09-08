# Missing-Angle CT Detective

<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
General users exploring reconstruction methods, including learners, researchers and portfolio reviewers. Use formal, educational explanations of controls, assumptions and results. Avoid patronising language, unexplained implementation details and diagnostic claims. Educational effectiveness has not been measured.

## Product Purpose
Measure how incomplete projections, noise and reconstruction assumptions affect synthetic feature recovery and public CT reference fidelity. Every experiment must be testable and replayable locally on macOS.

## Operating Context
Local Python CPU application with a browser interface, command-line experiments and exported numerical bundles. The user requested a public GitHub repository and a working GitHub Pages demo. The public demo and local app share a live 2D calculation worker. A recorded chest-image gallery remains available. An optional, separately locked Mac command-line workflow reconstructs measured patient cone-beam data in 3D.

## Capabilities and Constraints
The shared live lab reconstructs 64, 96 or 128 pixel images from acquired Helsinki fan-beam measurements, independently simulated projections of real chest and abdominal CT slices, or exact analytic disk projections. It uses nonnegative ray-length SART and optional neighbour smoothing. Completed results become named, restorable checkpoints with alternative refinement branches, image and measurement errors, manual regions, export and deterministic replay. References never enter the solver.

The Python experiment tools additionally provide FBP, scikit-image SART and total-variation refinement. The optional clinical workflow supports one pinned COBRA2026 acquisition with 356 measured views, CPU RTK FDK, physical geometry and reference comparison. Its integration into the Mac interface remains future work. No clinical use, radiation-dose claim, trained model or inference service.

## Evidence on Hand
The cited research report and original local feasibility measurements are under research/ and output/pdf/. The numerical gallery was reproduced on an M3 Mac. Scientific replay and the pinned clinical workflow have passed GitHub checks on Apple Silicon and Intel Macs. Four live body slices come from two volumes; the measured clinical workflow covers one patient acquisition. Clinical transfer and educational effectiveness have not been demonstrated. Current reports distinguish reference estimates from known analytic truth.

## Product Principles
- Keep measurement, reconstruction, evaluation and presentation separate.
- Preserve actual data and settings; a seed alone is insufficient.
- Show fixed image scales and applied settings, including any limitations.
- Separate prediction from reveal in the puzzle.

## Next priorities
Integrate the verified clinical workflow into the Mac interface; broaden evaluation across independent acquisitions; add acquisition quality checks and physical-angle coverage; profile memory and runtime before increasing resolution. Retain exact synthetic controls for verification while acquired examples lead the interface. Native packaging, hospital-system connections and automatic diagnosis are outside the current build.
