# Demo sharing pack

[Open the public demo](https://zakimaths.github.io/missing-angle-ct/).

Use the introductory comparison as the post image. Both images were calculated from measured Helsinki object A projections, with the same 90-view budget, one SART pass, 96 × 96 pixels and a shared display scale. The angular coverage changes. Neither image is ground truth.

- [X draft](x-post.txt)
- [LinkedIn draft](linkedin-post.txt)
- [1200 × 630 comparison image](../../demo/share-card.png)
- [Image attribution](../../demo/share-attribution.txt)
- [Source checksum, selected angles and calculation settings](../../demo/share-provenance.json)

Suggested image description: “Two calculated CT cross-sections of the same measured Helsinki object. Ninety spread views retain the internal holes; ninety consecutive views produce directional blur and streaks.”

## A short demonstration

1. Open the reconstruction lab with Helsinki object A selected.
2. Choose **Run 90 spread views** and watch the first pass form an image.
3. Inspect the reconstruction and reference errors, then choose **Run 90 consecutive views** to see the effect of limited angular coverage.
4. Try a refinement and compare the error scores before and after. Name a checkpoint, mark a region, and download the experiment to retain it.

The acquisition-link button shares sample, view count, selection and resolution. It opens those settings without starting a calculation. Labels, private files, refinements and calculated results are not included; download the experiment to preserve those. For a direct starting point, use [90 spread views of Helsinki object A](https://zakimaths.github.io/missing-angle-ct/?sample=ta&views=90&selection=spread&size=96#live-inputs).

## Release checks

The complete generated demo passed Chromium and WebKit checks on macOS: live calculation, quick comparisons, shared links, checkpoint controls, labels, cancellation, recorded-gallery loading and narrow-screen reflow. Automated WCAG A/AA checks reported no violations or unresolved checks in four tested page states in each engine. Keyboard skip navigation and desktop/mobile layouts were also inspected. These checks do not constitute complete assistive-technology or device coverage.

The sharing image and Open Graph/X metadata are included in the site. Actual X and LinkedIn preview rendering has not been checked inside those services. No social posts have been sent.

The body samples use simulated projections of real CT images. Acquired measurements in the browser come from Helsinki objects. The demo is a reconstruction and evaluation tool, not a diagnostic system.
