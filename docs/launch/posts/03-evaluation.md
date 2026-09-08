# Post 3: Measuring whether refinement helps

## LinkedIn

When a CT reconstruction looks smoother, how do we check whether it is more accurate?

In Missing-Angle CT, I separated image appearance from evaluation. The demo reports errors against a comparison reference, agreement with the measurements used for reconstruction, and agreement with unused views. These scores answer different questions.

Named checkpoints let you return to an earlier image before trying another refinement. Region labels help track a particular edge or feature, and exported experiments preserve the inputs and settings needed to repeat the calculation.

The attached recording uses a real abdominal CT slice with simulated projections. It demonstrates reconstruction under that simulation model; it is not a reconstruction from the patient's original scanner measurements.

Demo: https://zakimaths.github.io/missing-angle-ct/
Methods and limitations: https://github.com/zakimaths/missing-angle-ct

This is a reconstruction and evaluation project, not a diagnostic tool.

## X

A smoother CT image is not necessarily a more accurate one.

Missing-Angle CT compares reference errors and unused-view agreement, with named checkpoints and replayable exports.

https://zakimaths.github.io/missing-angle-ct/

## Attachment

Use `body-reconstruction.mp4`, or `error-analysis.png` and `region-labels.png` together. The video uses simulated projections of an abdominal CT source distributed through 3D Slicer from the Medical Segmentation Decathlon, CC BY-SA 4.0. Dataset details and attribution: https://github.com/zakimaths/missing-angle-ct/blob/main/docs/BODY_CT.md
