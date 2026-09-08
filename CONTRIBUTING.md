# Contributing to Missing-Angle CT

Contributions are welcome in reconstruction methods, independent validation, accessibility, documentation and public dataset preparation. Start with a small, reproducible change. You do not need to change the solver to make a useful contribution.

## Useful starting points

- Reproduce a published experiment on your Mac and report the platform, settings and numerical differences.
- Test keyboard or screen-reader access through a complete reconstruction, refinement and export.
- Improve an explanation using a concrete example and checked equations.
- Propose an independently acquired public projection dataset with documented geometry and redistribution terms.

Use the [issue forms](https://github.com/zakimaths/missing-angle-ct/issues/new/choose) for problems, proposals or a report of external use. Larger changes benefit from discussing the intended behavior first. Include enough detail for another person to repeat your observation.

## Local development

Follow the [Mac setup](README.md#run-on-your-mac), then install Node 22.23.2 for the browser solver and checks. Python dependencies are recorded in `uv.lock`; browser test dependencies are recorded in `qa/package-lock.json`.

```sh
uv sync --locked --no-editable
uv run --locked --no-editable ruff check src tests scripts app
uv run --locked --no-editable pytest
node --test tests/live_reconstruction.test.cjs
```

For browser changes, follow the [browser checks](qa/README.md), including the complete generated demo. Edit shared live-calculator files in `src/missing_angle/web/`; the demo builder copies them into `demo/`. Do not edit generated copies. Keep dependency updates separate from changes to numerical behavior where practical.

## What a good pull request contains

Explain the problem, the resulting behavior and how you checked it. Include a small reproduction for a bug. For a visual change, include before/after images at desktop and narrow widths. For a numerical change, include the acquisition settings, reference definition, metrics and an independent check where available.

Preserve existing import/export formats, checkpoint restoration and deterministic replay. If a format must change, introduce an explicit new schema with replay tests. A numerical change needs evidence beyond a more attractive image: use the [live benchmark](docs/LIVE_BENCHMARK.md) and report regressions and failure cases as well as improvements. Never use the reference image in a reconstruction update.

Keep interface explanations concrete: define unfamiliar terms near their first use, explain what each control changes and identify simulated measurements. Playback must show actual recorded calculations, start paused, support manual steps and retain a fixed display scale. Preserve the original source arrays. Do not add patient uploads, diagnosis claims or unverified clinical labels as incidental interface changes.

Generated demo assets stay out of Git. Rebuild with `scripts/build_demo.py` and validate with `scripts/verify_demo.py`.

## Data and attribution

Use redistributable public data or small generated fixtures in reports. Do not attach patient identifiers, confidential scans, tokens or private run exports. Record the source, licence, geometry and preparation steps for a new dataset. Browser body examples use simulated projections of real CT images; Helsinki examples use acquired object measurements. Preserve that distinction in descriptions and results.

New application code follows the project's MIT licence; adapted clinical code and third-party data retain their separate terms. See [third-party notices](THIRD_PARTY_NOTICES.md) and the [clinical notice](clinical/NOTICE).

## Reporting external use

If you use the project in a public course, research project, tool or independent reproduction, the usage form lets you share a link and explain what was used. Maintainers review evidence before including it in the [adoption record](docs/engagement/README.md). A star, fork or demo visit alone is not evidence of adoption. No usage reporting or telemetry is required to run the software.
