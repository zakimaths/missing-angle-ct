# Demo wording, themes and media review

The demo now offers Light, Pink and Dark appearances, with a persistent local preference and the system's light/dark setting as the initial fallback. Pink and Dark use rose accents. Reconstruction pixels, signed error maps and plot-series meanings retain their scientific display scales.

The wording pass corrected the shared-link description, capitalisation and possessive grammar in reference information, clarified the dataset selector and angle selection, and replaced informal gallery headings with method names. Downloads and links now distinguish a saved calculation from settings that the recipient still needs to run.

A failed measurement download exposes a retry action. Theme changes redraw the angular diagram and its legend without recomputing or recolouring the reconstruction. Native select content is contained to prevent a narrow-screen overflow observed in WebKit. The appearance control and header reflow on narrow screens.

## Verification

The complete-demo browser checks cover all themes at desktop and mobile widths, calculated-image accessibility, theme persistence, unchanged reconstruction pixels, error recovery, cancellation and recorded-gallery loading. Separate checkpoint tests cover measured, body-simulation and analytic examples. The numerical benchmark was checked against the established report using Node 22.23.2; all 120 cases agree within 1e-9. Only the analytic generator's source checksum changed because the shared file also contains edited display text.

A local run on Node 26.7.0 produced a discrepant statistics row. That output was discarded; the existing numerical baseline was retained and passed with the pinned release runtime. The cause of the Node 26 discrepancy was not established. The Mac workflow and local runtime file now also pin Node 22.23.2.

The capture script records actual browser calculations, asserts that early and final image pixels differ, and saves the source URL and acquisition settings. The final media pack includes both measured object data and a body-slice simulation, with that distinction retained in the recordings and suggested posts. These captures do not claim clinical validation or original patient projections in the browser.
