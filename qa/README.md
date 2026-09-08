# Browser regression checks

From the repository root, with Node 22.23.2 or newer:

```sh
npm ci --prefix qa --ignore-scripts
qa/node_modules/.bin/playwright install chromium
npm test --prefix qa
```

The script serves the shared reconstruction panel on a temporary loopback port, launches an isolated headless browser, and closes both afterwards. It exercises acquired Helsinki measurements, body-image simulations and an analytic control through actual controls and downloads. It verifies exact checkpoint restoration, alternative refinement branches, stage and region scores, labels, export/replay, narrow reflow and invalid-import recovery. The independent command-line replay also checks each exported branch. No page state is injected to simulate a completed calculation.

This is functional regression coverage, not a complete accessibility or browser compatibility assessment. These test dependencies are separate from the application; they do not add a runtime dependency to the public demo or Mac app.
