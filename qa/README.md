# Browser regression checks

From the repository root, with Node 22.23.2 or newer:

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
