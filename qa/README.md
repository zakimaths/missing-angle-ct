# Browser regression checks

From the repository root, with Node 22.23.2:

```sh
npm ci --prefix qa --ignore-scripts
qa/node_modules/.bin/playwright install chromium webkit
npm test --prefix qa
npm run test:demo --prefix qa
CT_BROWSER=webkit npm run test:demo --prefix qa
```

The script serves the shared reconstruction panel on a temporary loopback port, launches an isolated headless browser, and closes both afterwards. It exercises acquired Helsinki measurements, body-image simulations and an analytic control through actual controls and downloads. It verifies exact checkpoint restoration, alternative refinement branches, stage and region scores, labels, export/replay, narrow reflow and invalid-import recovery. The independent command-line replay also checks each exported branch. No page state is injected to simulate a completed calculation.

The complete-demo commands require a generated `demo/` directory (see the main README). They cover shared acquisition links, quick comparisons, cancellation, gallery loading, desktop and 375-pixel reflow, keyboard skip navigation and axe WCAG A/AA checks. Set `CT_SCREENSHOTS=1` to save desktop and mobile captures in `output/launch/`. On macOS WebKit, the keyboard check uses Option-Tab, the browser convention for tabbing to links.

Automated checks do not replace assistive-technology testing or a complete browser compatibility assessment. These test dependencies are separate from the application; they do not add a runtime dependency to the public demo or Mac app.

## Capture screenshots and recordings

```sh
node qa/capture.cjs
```

This opens isolated Chromium sessions against the public demo. Set `CT_URL` to a local preview address to capture an unpublished build. The script operates actual controls, records a 360-view measured-object calculation and a 360-view body simulation, and checks that early and final reconstruction images differ. It saves nine PNG screenshots, two original WebM recordings and capture provenance under `output/playwright/social/`. No results are injected into the page. Source data and scientific display scales remain unchanged.

Use FFmpeg to convert each WebM recording to MP4 with H.264, `yuv420p` and `+faststart`; preserve the original timing. The source recordings have no audio. The capture outputs are local sharing artifacts and are excluded from Git.
