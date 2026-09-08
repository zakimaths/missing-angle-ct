# Contributing

Use the locked environment and run the checks in the README before opening a pull request. Keep solver inputs separate from reference-based evaluation. Preserve older bundle formats or introduce an explicit new schema with replay tests. Every numerical change needs a reproducible comparison, including failure cases.

Keep student-facing language concrete: define an unfamiliar term near its first use, explain what a control changes, and identify simulated measurements. Preserve the original source arrays and data licences. Do not add patient uploads, diagnosis claims or unverified clinical labels as incidental UI changes.

Generated demo assets stay out of Git. Rebuild with `scripts/build_demo.py` and validate with `scripts/verify_demo.py`. Any playback must show actual recorded calculations, start paused, support manual steps and retain a fixed display scale.
