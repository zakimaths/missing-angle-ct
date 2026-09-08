# Public demo release review

The demo now opens with a measured-data comparison and a direct route into the reconstruction controls. Two 90-view shortcuts make angular coverage easy to compare. Acquisition links reproduce public sample settings while excluding private files and labels. Recorded comparisons load only when their section opens, reducing initial downloads.

## Evidence

- 88 installed-package Python tests and 21 JavaScript tests passed locally on Apple Silicon. Static Python checks passed.
- Chromium and WebKit exercised the complete generated demo. Both completed all flows without page errors or failed asset responses.
- Automated axe WCAG A/AA checks passed in initial, reconstructed, narrow-screen and recorded-gallery states: no violations and no unresolved checks in either engine.
- The existing browser regression checked exact checkpoint restoration, alternative branches, region labels and downloaded-run replay for measured, body-simulation and analytic inputs.
- The introductory and social images use actual solver outputs. Their provenance records source checksum, selected views, angles, settings and calculated-image checksums. Both use the same display scale.
- A static design scan flagged six recorded images without initial sources. These sources are intentionally assigned when the gallery loads; browser verification confirmed they load successfully. No unrelated placeholder sources were added.
- Desktop and mobile screenshots were inspected. A missing word space caused by hiding a desktop line break was corrected for narrow layouts.

## Deployment gate and limits

The Pages workflow now requires complete-demo Chromium and WebKit checks before deployment, alongside the existing numerical tests, benchmark and generated-bundle verification. The test dependencies do not ship to the browser.

No VoiceOver session, complete assistive-technology audit, physical mobile-device test or social-platform preview inspection is claimed. The numerical method has not changed in this release. Clinical reconstruction work remains separate from the browser demo.
