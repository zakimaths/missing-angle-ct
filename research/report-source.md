# Missing-Angle CT Detective
## Research verdict and implementation blueprint

Prepared 7 September 2026 for Hasan and future technical portfolio reviewers.

**Recommendation: build it, with a more precise scientific claim and a smaller first release.** The strongest project is a reproducible investigation of feature recovery under incomplete measurements. Its contribution should be controlled experiments, visible assumptions and replayable failures. A reconstruction viewer alone would be difficult to distinguish from existing demonstrations.

Suggested description: “Explore how projection coverage, noise and reconstruction assumptions affect which synthetic structures survive. Replay every experiment and test whether the findings transfer to unfamiliar shapes.”

The foundation is credible: scikit-image provides an executable FBP/SART example, and limited-data tomography has established theory about directional boundary visibility. Neither establishes the proposed app's educational benefit or clinical usefulness. [scikit-image Radon example](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html); [Quinto, 2017](https://orbit.dtu.dk/files/151961241/LimitedData.pdf).

**Recommended first release:** 128 x 128 synthetic 2D parallel-beam CT; Python CPU core; command-line experiments; a thin Streamlit interface; FBP and explicitly configured SART; feature-present and feature-absent controls; downloadable numerical replay bundles. No AI API, model training, native Mac wrapper or clinical data is needed.

| Decision | Assessment |
| --- | --- |
| Scientific foundation | Strong; narrow the claims about impossibility |
| CPU feasibility on this Mac | Demonstrated by a small numerical probe |
| Distinctiveness of a basic simulator | Weak; closely related demos already exist |
| Distinctiveness of the proposed benchmark | Promising, if its tests are actually implemented |
| Cross-Mac reproducibility | Achievable engineering target; not yet demonstrated |
| Educational and clinical transfer | Unmeasured; require separate evaluation |

This research includes a local feasibility probe, not a finished application. It interprets “Astra” as the AI that proposed the idea and evaluates the ASTRA tomography toolkit separately. The unexplained C/E/F/P/M scores in the brief are not treated as evidence.

Reading route: scientific corrections and differentiation, pages 2-3; stack and measured feasibility, pages 4-5; verification and reproducibility, pages 6-10; build, transfer and publishing, pages 11-14; evidence notes, pages 15-17.

<!-- page -->
# What the concept can actually establish

**Replace “shows exactly when measurements cease to support a reconstruction” with “measures recovery and instability under a declared experiment.”** In ideal continuous, noiseless settings, compact-support assumptions can permit uniqueness even with incomplete angular coverage. Recovery can nevertheless be extremely unstable. A finite noisy numerical experiment cannot prove universal impossibility. [Zeng and Li, 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8294472/).

The theory is directional. Boundary segments tangent to measured rays are more stably recoverable; angular endpoints can introduce tangent streaks. This motivates an orientation experiment, but does not imply an entire ellipse contributes nothing to the measurements when its long axis points a particular way. [Quinto, 2017](https://orbit.dtu.dk/files/151961241/LimitedData.pdf).

Three acquisition limitations must have separate controls:

| Limitation | Controlled comparison | What otherwise gets confused |
| --- | --- | --- |
| Sparse views | Reduce count across the same 180-degree span | Sampling density |
| Limited angle | Reduce span while holding count fixed | Directional coverage |
| Measurement noise | Hold geometry fixed and change a declared noise model | Signal quality |

A second limited-angle experiment may keep angular spacing fixed. Its count then falls as the angular span shrinks. Label this combined change explicitly. Store actual angles; “60 projections” alone does not define the experiment.

The projection budget is an educational resource. For a first noisy mode, additive Gaussian noise in line-integral units is a useful controlled perturbation, clearly labelled as such. Later, simulate Poisson photon counts before the logarithm, with explicit attenuation units and zero-count handling. The physics distinction is documented in the LoDoPaB technical paper. [Leuschner et al., preprint revised 2020](https://arxiv.org/pdf/1910.01113).

A low residual on acquired measurements does not establish that a missing feature was recovered correctly. Two algorithms agreeing does not produce calibrated uncertainty. Call disagreement an “assumption sensitivity” view. Reserve “confidence” for a defined and evaluated statistical quantity or a user's self-reported belief.

Use “synthetic target” or “organ-like phantom” in the interface. Ellipses are useful exact geometry; they do not model realistic anatomy. Synthetic feature detection is not lesion detection, and projection count is not a clinically validated radiation-dose estimate.

<!-- page -->
# Make the project distinctive

Existing work already covers the obvious interface. EPFL documents Radon projection, filtering and backprojection demonstrations. A public repository, xray-ct-recon, describes a Streamlit viewer, reconstruction comparisons and exported arrays with metadata. Those are documented features; its numerical claims were not independently audited here. [EPFL demonstration](https://bigwww.epfl.ch/demo/jtomography/index.html); [xray-ct-recon repository](https://github.com/Ash-119/xray-ct-recon).

The scikit-image example supplies a reproducible baseline, while HTC2022 already provides a real limited-angle reconstruction challenge. This project should credit both rather than claim a new reconstruction method or the first CT teaching simulator. [Radon example](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html); [HTC2022 protocol](https://fips.fi/wp-content/uploads/2024/06/Helsinki_Tomography_Challenge_2022_v11.pdf).

**Recommended differentiator: a “failure case file” for every conclusion.** Each case should contain the hypothesis, target geometry, acquired angles, algorithm assumptions, raw result, feature score, counterexample and replay command. Show both successful and failed cases selected by a declared rule.

Use three modes with the same numerical core:

1. **Explore:** reveal ground truth, vary one parameter and compare reconstruction, error and feature response on fixed display scales.
2. **Detective:** hide the target, buy a predefined projection pack, predict whether a feature exists and record confidence before revealing the answer.
3. **Atlas:** open frozen cases explaining sparse-view streaks, missing-boundary degradation, noise, smoothing and false features. Each card replays a real exported run.

For v1, sell predefined acquisition packs rather than arbitrary individual angles. This keeps comparisons interpretable and avoids prematurely implementing adaptive acquisition and irregular angular quadrature. A later angle-selection game can compare people or a policy with uniform and seeded-random schedules at equal budgets.

Keep hidden truth away from reconstruction and scoring decisions. The evaluator may use feature masks after the prediction; the detector and acquisition policy must receive only their declared inputs. A local educational app cannot provide a secure hidden-test competition when users can inspect its files.

The intended portfolio claim is demonstrable engineering: “I converted a visually plausible simulation into experiments that can expose their own failure modes.” It is not a claim of new mathematics, clinical validation, or proven learning improvement. Search was targeted, so no exhaustive originality guarantee is made.

<!-- page -->
# A practical macOS stack

**Use a Python package plus CLI, then add Streamlit.** This keeps simulation, evaluation and replay in one codebase. The recommendation is architectural judgment supported by the local timings on page 5 and official platform documentation.

| Layer | Recommendation | Reason |
| --- | --- | --- |
| Numerical core | NumPy, SciPy, scikit-image; float64 reference path | Existing transforms; transparent arrays |
| Experiments | Standard-library CLI, typed configuration, JSON | Runs without a browser or notebook |
| Interface | Streamlit; plots from the core's results | One language and a local browser UI |
| Visual exports | Matplotlib, PNG/SVG plus numerical arrays | Consistent scales and reusable figures |
| Verification | pytest; Streamlit AppTest; browser smoke checks | Scientific, state and interaction tests |
| Environment | Exact Python patch, pyproject.toml, uv.lock | Reviewable dependency resolution |

The verified probe used Python 3.12.14 and scikit-image 0.26.0. Start from that tested combination; resolve and test the full app's dependencies before claiming a supported release. scikit-image documents macOS Intel and ARM support. [Installation guide](https://scikit-image.org/docs/stable/user_guide/install.html).

**ASTRA is a later option, not a Mac impossibility.** Its current documentation supports Apple Silicon through conda-forge with CPU-only 2D functionality. Its main Windows/Linux package routes are CUDA-oriented. An optional separate ASTRA environment could supply a second projector or geometry support. It was not installed in this research. [ASTRA installation](https://astra-toolbox.com/docs/install.html).

TIGRE's official Python setup expects NVIDIA CUDA hardware and documents Windows/Linux; no supported Apple Silicon route was established. It adds no clear advantage for this first build. [TIGRE installation](https://github.com/CERN/TIGRE/blob/master/Frontispiece/python_installation.md).

Defer a React/Python service until the interaction design outgrows Streamlit. Pyodide is a possible later static browser route: its package inventory includes the scientific libraries, but version compatibility, SART execution and browser performance still need testing. [Pyodide packages](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).

Avoid a database, accounts, distributed jobs, GPU kernels and a desktop wrapper in v1. A local browser app satisfies “works on macOS”; a signed native application is a different delivery requirement. Do not duplicate the numerical implementation in JavaScript merely to make the portfolio page easier to host.

<!-- page -->
# What was tested on this Mac

**A small CPU probe ran successfully.** Hardware: Apple M3 MacBook Air, 8 GB RAM; macOS 26.6.2 arm64; Python 3.12.14; NumPy 2.5.3; SciPy 1.18.1; scikit-image 0.26.0. The probe and exact installed package pins are preserved with this research.

The numerical steps of the official gallery were reproduced at their original 160 x 160 resolution, 160 equally spaced views and no added noise. Plotting was omitted. These values round to the gallery's published 0.0283, 0.0329 and 0.0214. [Official gallery](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html).

| Original gallery calculation | Locally measured RMSE |
| --- | --- |
| Ramp FBP | 0.02827412 |
| SART, one pass | 0.03292242 |
| SART, two passes | 0.02137785 |

A separate resized 128 x 128 phantom used 180 views. Timing was one warm-up followed by the median of three serial calls; imports, installation, plotting and UI startup were excluded. No thread-count overrides were applied.

| 128 x 128 operation | Warm median | RMSE, where applicable |
| --- | --- | --- |
| Forward projection | 19.0 ms | Not applicable |
| Ramp FBP | 17.0 ms | 0.03179243 |
| SART, one pass | 51.4 ms | 0.02963279 |

An independent disk chord formula was compared with raster projections at fixed physical size. Relative projection L2 error decreased from **2.20% at 64**, to **0.697% at 128**, to **0.406% at 256** pixels. Rasterization used 8 x 8 subpixel samples per pixel and angles every 5 degrees. This is encouraging convergence evidence, not a validation of off-centre or rotated-ellipse geometry.

Two separate process runs produced identical raw-byte hashes for all 22 saved arrays. One additional same-process FBP call was bitwise identical. Timings differed slightly, as expected. A 90-degree FBP normalization experiment is explained on page 10.

**Limits:** this establishes local numerical feasibility and a narrow repeatability result. It does not test an interactive app, seeded feature recovery, noise sweeps, learning, ASTRA, Intel Macs, GitHub CI or cross-platform tolerances. The probe uses a temporary Python environment; the full application and its uv lockfile have not been built.

<!-- page -->
# Independent numerical verification

The original proposal correctly identifies the inverse-crime risk: using closely matched simulation and inversion can make recovery look better than it is under model mismatch. A finer forward discretization and detector sampling are established ways to stress that assumption. A matched model remains useful as a labelled ideal control. [Nuyts et al., 2013](https://johannuyts.github.io/publications/PhysMedBiol2013.pdf).

**Define geometry before implementing more features.** Fix the physical field of view, pixel centres, axis directions, detector centres/pitch, angle units and convention, support mask and interpolation. State whether detector data are ideal centre rays or averages over finite detector bins. Refine pixel pitch while holding physical object size fixed.

For a uniform disk of radius R, density rho and centre c, the analytic line integral is:

`p(theta,s) = 2 rho sqrt(R^2 - (s - c dot n_theta)^2)`

inside its support, and zero outside; `n_theta = (cos(theta), sin(theta))`. This is the geometric chord length times density. It provides a forward reference that does not call the reconstruction implementation.

For an ellipse with semiaxes a,b and rotation alpha, an additional analytic check can use `q^2 = a^2 cos^2(theta-alpha) + b^2 sin^2(theta-alpha)` and `t = s - c dot n_theta`, giving `p = 2 rho a b / q * sqrt(1 - (t/q)^2)` for `|t| < q`. Independently check this derived formula by numerical line quadrature before treating it as a reference. Superposition handles overlapping signed ellipse contributions; ensure final attenuation is nonnegative when simulating transmission counts.

| Required test | Failure it can reveal |
| --- | --- |
| Zero image, linearity, scaled attenuation | Offsets and normalization errors |
| Centred and translated disks | Detector origin, pitch and centre shifts |
| Rotated unequal-axis ellipse | Angle signs, transpose and 90-degree errors |
| 64/128/256 convergence at fixed field of view | Resolution-dependent conclusions |
| Fine-grid forward / coarse-grid inverse | Matched-discretization optimism |
| A different rasterizer and subpixel offsets | Dependence on one edge-rendering method |

Use a high-resolution pixel-area reference for image metrics; do not score against a different definition of ground truth accidentally. The current probe completes only part of this ladder. Acceptance tolerances should be derived on development cases, recorded and frozen before held-out evaluation. Never demand exact equality between different discretizations.

<!-- page -->
# A bounded, interpretable experiment plan

All settings and sample counts below are **proposed starting values**, not measured outcomes or statistical power calculations. First use 20 development phantom seeds; then freeze decisions and evaluate 60 separate seeds. Keep target-present and target-absent versions of each background together. Use three independent noise replicates for noisy panels and retain the phantom as the resampling unit.

| Panel | Change | Hold fixed |
| --- | --- | --- |
| A: sparse views | 12, 24, 48, 96, 192 views over 180 degrees | Phantom, noise convention, algorithm settings |
| B: missing angle | Spans of 180, 150, 120, 90 degrees at 48 views | Count, feature geometry, noise |
| C: orientation | Rotate feature or acquisition window in 30-degree steps | Span, count, feature size and contrast |
| D: noise | Zero and three specified line-integral noise levels | Geometry and signal scale |
| E: feature scale | Equivalent diameters 2, 4, 8 pixels at 128 resolution | Contrast and a chosen acquisition geometry |

Treat the 2-pixel target as a deliberate sampling stress case. It is not a well-resolved anatomical feature. If refining resolution, convert these sizes to fixed physical diameters rather than keeping their pixel counts fixed.

Start with panels A and B noiseless. Add orientation and feature controls after geometry checks pass. Use a fixed global signal scale for noise; do not normalize every sinogram or reconstruction independently. Add Poisson noise only after physical attenuation and detector conventions are verified.

For photon experiments, separate fixed incident photons per ray/view from a fixed total incident-photon budget. Adding views increases total exposure in the first design and divides a fixed budget in the second. Neither is a calibrated patient-dose model. Record the selected convention in every comparison.

FBP-ramp, SART with one pass, and SART with a development-selected fixed pass count make a sufficient initial comparator set. Every method receives identical acquired data for a case. Record initialization, relaxation and any clipping. Do not let one method use known target intensity limits while another is evaluated without declaring that advantage.

Avoid the full Cartesian product of counts, spans, orientations, sizes, contrasts, noise, seeds and methods. Use the panels above to expose main effects, then investigate only interactions that materially alter a conclusion. Report uncertainty across phantoms, failure counts and representative extremes, not just a mean image score.

Predeclare each question: for example, “At fixed view count, how does angular span change target sensitivity?” More views and more SART passes need not improve every metric on every noisy case. A surprising reversal is a result to investigate, not automatically a failing test.

<!-- page -->
# Measure missing and invented features

**Use RMSE as context and feature performance as the central outcome.** Task-based detectability has established CT evaluation precedent, including low-contrast and wire targets; those clinical-geometry studies do not validate this synthetic detector. [Bian et al., 2010](https://iacl.ece.jhu.edu/proceedings/iacl/2010/BiaxPhysMedBio10-Evaluation_of_Cone-Beam_CT.pdf).

Proposed v1 detector: a fixed multiscale contrast/template score over declared candidate locations, followed by a development-selected threshold. Use known-location ROI scores as a separate controlled experiment. Do not call a method “detection” when it receives the true target location or mask without saying so.

| Outcome | Operational definition |
| --- | --- |
| Global fidelity | RMSE on the fixed image support, plus full-frame RMSE |
| Contrast recovery | Reconstructed feature-minus-background contrast divided by the true contrast |
| Sensitivity | Fraction of present targets detected at a threshold frozen on development cases |
| False positives | Fraction of absent cases flagged, plus false candidate detections per image |
| Localization | Centre error and, if segmentation exists, overlap at a frozen threshold |
| Data consistency | Residual on acquired projections under the declared forward operator |

Predeclare the background annulus and exclude other known structures for the controlled ROI measurement. Near-zero true contrast makes the contrast ratio unstable; report absolute contrast for that regime. If SSIM is included, specify its data range and window. Never normalize each image to its own min/max before quantitative comparison.

A development target such as 5% false-positive rate is a threshold-selection rule, not a guaranteed held-out rate. Report the actual held-out false-positive rate with uncertainty. If an algorithm is tuned separately, apply the same tuning budget and freeze every selected parameter before final evaluation.

Create absent cases by removing the target while preserving the background definition. Apply the same detection search space to present and absent cases. Save target identity, mask and candidate matching rules so sensitivity cannot silently change between runs. Resample by phantom, keeping its acquisition settings and noise replicates grouped; pixels and correlated variants are not independent observations.

For robustness, hold out entire shape families, such as irregular holes, bars or textured backgrounds, as well as seeds. New seeds drawn from the same ellipse generator test interpolation within that family. They do not establish transfer to new artifacts, anatomy or measurement physics.

<!-- page -->
# Repeatability and reproducibility contract

Use explicit terms. **Repeatability:** the same saved experiment reruns in the same environment. **Reproducibility:** another supported Mac can rerun it within declared tolerances. **Independent validation:** another forward model or implementation supports the conclusion. None follows from a seed alone.

NumPy's random-stream guarantees depend on the generator, seed, sequence of calls, build, environment and machine. Preserve numerical inputs as well as the recipe. Name the BitGenerator and split phantom and noise randomness into independent streams. [NumPy compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html).

Every experiment bundle should include:

| File/content | Required information |
| --- | --- |
| manifest.json | Schema version; code commit; lockfile hash; Python/packages; OS/architecture; backend; dtype |
| configuration.json | Explicit ellipses; coordinate system; support; actual angles and order; detector pitch; noise and reconstruction settings |
| arrays.npz | Phantom; raw/processed measurements; acquisition mask; reconstruction; feature masks; optional noiseless reference |
| metrics.json | Metric definitions/version; support masks; all scalar results; timing protocol |
| preview.png | Display scales, units, method and experiment identifier |
| provenance | Seeds/RNG; warnings; package/source hashes; replay instructions |

Keep “measured zero” distinct from “unmeasured.” Save raw photon counts if using count noise, plus log conversion and clipping rules. Save the noisy measurements once so changing reconstruction does not silently draw new noise.

Commit an exact Python patch and uv.lock; use `uv sync --locked` in the eventual project. This checks that metadata and lock agree rather than silently updating dependencies. [uv locking documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

CI should test explicit current runner labels for both architectures, such as `macos-15` and `macos-15-intel`, and record the runner image. Those labels are available now but do not freeze every future image update. [GitHub runner documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job).

Require exact checks for configuration and saved inputs; use calibrated numerical tolerances for cross-machine outputs. Hash canonical array content with shape, dtype and byte order specified, rather than promising identical ZIP files. Pinning alone is not a scientific validity test. This research's same-Mac hash match is narrower than the proposed cross-Mac contract.

<!-- page -->
# Algorithm and efficiency traps to prevent

**FBP angular weighting needs an explicit policy.** Inspection of installed scikit-image 0.26.0 showed a final factor of `pi / (2 * angles_count)`. The local probe confirmed that reconstructing 90 acquired columns at angles 0-89 degrees directly produces exactly twice the amplitude of keeping them in a 180-column 0-179-degree grid with the other columns zero-filled. This is a weighting convention difference, not evidence that either image is more correct.

For a sparse, evenly spaced full-span scan, ordinary FBP weights represent the whole 180-degree angular interval. For a restricted-angle FBP baseline, integrate only the measured angular cells: use a declared regular full grid and missing-column mask, or independently verify angular quadrature. With uniform cells spanning Omega degrees, scaling a direct equal-weight subset reconstruction by Omega/180 implements that restricted weighting convention. Define cell boundaries; the first-to-last angle difference alone can be off by one angular step.

Do not reuse the sparse full-span convention blindly for limited or irregular data. Label angular completion and normalization in exports. Display absent sinogram columns as missing, even if a particular FBP computation fills them with zero. **SART receives only actual measurements.** Fake zeros would tell it that unmeasured rays have zero attenuation.

SART is one iteration per call; additional calls, initialization, relaxation and clipping change the algorithm. Pass a copy of a saved initial image where necessary to avoid mutation affecting later comparisons. [scikit-image transform API](https://scikit-image.org/docs/stable/api/skimage.transform.html#skimage.transform.iradon_sart).

Keep the first implementation efficient:

- Cache a phantom and its clean sinogram when their complete configuration matches. Cache keys must include angles, geometry, numerical settings and generator version.
- Keep noise realization and reconstruction separate. A filter change should not reacquire data or reset the experiment.
- Use a Run control with batched form inputs; Streamlit forms support this behavior. [Streamlit forms](https://docs.streamlit.io/develop/concepts/architecture/forms).
- Record the applied configuration alongside the displayed result. Pending slider edits must not relabel an old image or export stale data.
- Defer a dense system matrix at 128 resolution. If showing singular vectors or ambiguity pairs, use a small, explicitly defined discretization as a separate teaching case.

Do not assume unfiltered `iradon` is the exact adjoint of `radon`. Any custom iterative optimizer requires its own inner-product adjoint test. TV regularization can wait until this operator contract and feature evaluation are stable.

<!-- page -->
# Build within Astra's actual role

OpenAI documents Astra as a general model for complex reasoning and coding. Its guidance also identifies workflow tendencies such as sensitivity to instructions, clarification pauses and extensive testing. These descriptions are not CT-specific accuracy guarantees. [Astra model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra); [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model).

**Use Astra to implement a written scientific contract, and judge the artifacts it produces.** The main project risks are plausible but wrong coordinate conventions, normalization, physics, thresholds, and tests that repeat the same mistake as the code. These are engineering risk judgments, not measured failure rates for Astra.

Give each build task a small scope: required behavior, relevant source, known assumptions, an independent check and an explicit completion condition. Keep the geometry specification and immutable reference cases in the repository. Long conversation context should not be the only place where these decisions exist.

| Milestone | Deliverable | Gate before moving on |
| --- | --- | --- |
| 1. Numerical core | Package and CLI; official baseline; fixed geometry | Baseline reproduction and analytic scale/orientation tests |
| 2. Independent checks | Disk/ellipse references; finer forward grid | Quantified convergence and mismatch results |
| 3. Feature benchmark | Present/absent pairs; fixed metrics and splits | Thresholds frozen; held-out misses and false positives reported |
| 4. Interface and replay | Three modes; export/import; case atlas | UI state matches exports; exact saved-input replay |
| 5. Mac release | Locked environment; both Mac CI jobs; documentation | Clean setup on supported architectures; known limits listed |

Astra can write code, tests, documentation and analysis scripts. Require the human owner to review the physics conventions, interpret failures, freeze the evaluation protocol and explain the final results. For specialist claims beyond the cited theory, seek a tomography researcher or medical physicist's review before adopting the claim.

Avoid asking the same agent to generate implementation, expected values and an unsupported declaration of correctness in one step. Cross-check expectations against analytic geometry, the library's established example and a differently discretized forward model. Independent sources and tools matter more than a second AI simply agreeing.

The runtime remains deterministic numerical software. No Astra API, generated narrative grader or AI vision judge is needed inside the product. The build ends when the gates pass, not when the interface looks convincing or an agent reports completion.

<!-- page -->
# Test the user experience and learning separately

A computational benchmark can establish properties of the implementation and synthetic cases. It cannot establish that people learn transferable reasoning from the puzzle.

**Functional UI checks:** a purchased pack is charged once; reset restores the intended state; changing reconstruction preserves acquired data; changing the case invalidates stale outputs; export describes exactly the visible result; revealed ground truth is absent from hidden-mode prompts. A replay opened in a fresh session should recover the same measurements and settings.

Streamlit AppTest can simulate inputs and inspect application outputs in automated tests. It complements, rather than replaces, a real-browser check of rendering and interaction. [Streamlit AppTest](https://docs.streamlit.io/develop/concepts/app-testing).

For the eventual browser smoke check, complete one case on Safari and one on Chromium on a supported Mac. Check keyboard navigation, readable axes, explicit units, contrast, downloads and a narrow viewport. Use fixed image windowing for comparison; offer zoomed feature panels rather than allowing autoscaling to conceal amplitude errors.

**Proposed learning pilot:** first recruit roughly 8-12 volunteers to discover confusing instructions and controls. This is a usability sample, not a powered learning-effect study. Ask users to explain a failure in their own words and observe whether they can replay a case without assistance.

For an educational evaluation, predefine questions and an outcome such as artifact-identification accuracy on unseen examples. Compare interactive practice with a static explanation of the same content. Where feasible, randomize the condition or counterbalance order; balance baseline experience and include a later retention test. Estimate a suitable sample size using pilot variability and the smallest effect worth detecting.

Hold out examples by generator family, orientation, severity and acquisition pattern. Test whether users distinguish sparse-view artifacts from limited-angle loss and whether they recognize an assumption-dependent false feature. Record confidence as well as accuracy so persuasive visuals do not increase unjustified certainty.

Report participant count, exclusions, question wording and uncertainty, including negative results. Use no patient data. For formal research participation, obtain the appropriate institutional review before recruitment. Do not claim “improves diagnostic skill” from a general-audience synthetic puzzle.

The learning study is a later optional branch. A well-documented computational instrument can already be a strong portfolio release while explicitly saying that educational effectiveness remains untested.

<!-- page -->
# Transfer and future applications

**First transfer within simulation, then change the acquisition model.** Keep seeds, phantom families and artifact mechanisms as separate hold-outs. A new random ellipse is not the same test as detector blur or a centre-of-rotation error.

| Step | Candidate test | What it would establish |
| --- | --- | --- |
| 1 | New ellipse seeds, subpixel positions, feature sizes | Robustness within a defined generator |
| 2 | Irregular holes, bars and textured backgrounds | Transfer beyond the development shape family |
| 3 | Fine-grid projector, detector blur, small geometry shifts | Sensitivity to a specified model mismatch |
| 4 | Measured nonclinical projections | Transfer to physical data under matched geometry |
| 5 | Clinical question with expert oversight | A separate research programme, not a v1 extension |

**HTC2022 is the most relevant measured-data next step.** Its targets are acrylic disks with irregular holes; it provides geometry metadata, development/test targets and progressively restricted views. Its reference is derived from full-angle reconstruction and segmentation rather than exact physical truth. Respect its supplied geometry; a parallel-beam scikit-image pipeline is not a drop-in reader. [Organizer protocol, 2022](https://fips.fi/wp-content/uploads/2024/06/Helsinki_Tomography_Challenge_2022_v11.pdf).

**LoDoPaB is useful for anatomy-shaped synthetic transfer.** It pairs CT-derived reference images with simulated low-dose parallel-beam measurements. This does not equal validation on raw clinical acquisition data. Preserve patient-level separation and its documented geometry; do not casually resize measurements into a 128-pixel toy setup and present the result as the original benchmark. [LoDoPaB paper](https://arxiv.org/abs/1910.01113).

**The 42-walnut collection is a later geometry expansion.** It supplies measured cone-beam data with multiple acquisition orbits. Its 3D geometry and reference construction add scope that the first project does not need. [Der Sarkissian et al. dataset, 2019](https://zenodo.org/records/2686725).

Before any dataset is integrated, inspect its actual files, geometry, current licence and attribution conditions. These datasets were researched, not downloaded or executed here. Keep optional large datasets outside the basic installation.

Plausible application directions are inverse-problem teaching, acquisition-design experiments and nondestructive material inspection. A later “choose the next view” policy must be compared with uniform and random baselines at equal budgets and evaluated on held-out phantoms. It must not inspect the hidden target. Geometry visibility alone is not a guarantee of optimal acquisition.

A useful later teaching case would find two constrained phantoms with different features but nearly indistinguishable acquired data at a specified noise tolerance. On a small verified operator, this can demonstrate ambiguity within that defined model. It is stronger evidence about measurement support than one reconstruction's failure, but still not a universal impossibility theorem.

<!-- page -->
# Prepare an evidence-led public release

**GitHub first, then short demonstrations that link to a frozen result.** Publish source, installation steps, tests, the scientific conventions, a small sample bundle, limitations and an explicit account of AI assistance and your own decisions. Create a tagged release so the public demonstration refers to a stable version.

Suggested repository layout: `src/missing_angle/` for the core; `app/` for the interface; `tests/` for numerical and replay checks; `experiments/` for frozen configurations; `docs/` for methods and case files; `sample_runs/` for small reproducible examples. Keep notebooks exploratory. Put complete sweeps in release assets rather than flooding version control with binary outputs.

Include an appropriate code licence, third-party attribution and CITATION.cff. GitHub recognises that file for citation guidance; Zenodo can archive a GitHub release and assign a DOI. [GitHub citation files](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files); [Zenodo release archiving](https://help.zenodo.org/docs/github/archive-software/github-upload/).

A static artifact atlas is the lowest-maintenance public demo. GitHub Pages hosts static content; a Python Streamlit process needs a suitable server if you want arbitrary live reconstructions online. Start with precomputed replayable cases and the local app. [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

**Demonstration sequence:** show the acquisition geometry; ask viewers which feature survives; reveal reconstruction and ground truth; show a miss or false feature; finish with the exact case identifier, metric definition and replay link. Use real software outputs and fixed scales. A 30-60 second clip is a suggested editorial format, not a platform-performance claim.

Draft LinkedIn announcement for use after the release gates pass:

“I built Missing-Angle CT Detective to explore how incomplete measurements change what a reconstruction can support. It uses synthetic targets, FBP/SART comparisons and tests for both missing and false features. The work that mattered most was validating the geometry, separating angle coverage from view count, and making every result replayable. This is an educational experiment, not a clinical tool. The repository explains the assumptions, tests and remaining limits.” Add the actual release link and verified results at publication.

Draft short X/Twitter post for the same stage:

“Which details survive when CT projections are missing? Missing-Angle CT Detective explores that with synthetic targets, FBP/SART and replayable failure cases. Built for macOS; assumptions and tests included. Educational, not clinical.” Add the verified link; check the platform's length limit then.

Nothing was published or posted during this research. Avoid unsupported claims about dose savings, diagnostic accuracy, novelty or learning gains. The most persuasive story is one precise result that someone else can reproduce.

<!-- page -->
# Evidence and source notes

Research used original papers, institutional manuscripts, official software documentation and first-party project records. A scientific lane and a platform lane were reconciled with direct checks of consequential sources and a local numerical probe. Discovery covered CT visibility, inverse-crime controls, task metrics, Mac backends, reproducibility, prior art and transfer datasets. Follow-up resolved uniqueness versus stability, ASTRA's Apple Silicon support and FBP normalization.

Search stopped when material recommendations had primary support or an explicit experimental limitation. Further general searching would not establish Intel-Mac execution, feature-detector validity or human learning. Those require the proposed tests.

Some publisher/dataset pages intermittently refused direct access. For LoDoPaB, an accessible author preprint was read alongside indexed publication metadata; the final 2021 publication is identified separately. HTC2022's accessible organiser PDF supplied its protocol. No inaccessible full text is presented as having been reviewed.

All web sources were accessed 7 September 2026. Living documentation dates are not inferred from crawl dates. Local numerical results are original measurements from the included probe. Recommendations, test sizes and delivery stages are design judgments rather than externally validated project outcomes.

## Scientific and baseline sources

**scikit-image contributors. Radon transform.** Documentation v0.26.0; page update date not stated. Executable baseline and reference RMS values. [Official example](https://scikit-image.org/docs/stable/auto_examples/transform/plot_radon_transform.html).

**scikit-image contributors. skimage.transform API.** Documentation v0.26.0; update date not stated. Parameters and behavior of Radon, FBP and SART. [Transform API](https://scikit-image.org/docs/stable/api/skimage.transform.html#skimage.transform.iradon_sart).

**Eric Todd Quinto. Artifacts and Visible Singularities in Limited Data X-Ray Tomography.** Sensing and Imaging 18, 2017; DOI 10.1007/s11220-017-0158-7. Institutional author manuscript. [DTU manuscript](https://orbit.dtu.dk/files/151961241/LimitedData.pdf).

**Gengsheng L. Zeng and Ya Li. Analytic continuation and incomplete data tomography.** Journal of Radiology and Imaging 5(2), 5-11; 4 March 2021. Continuous-data uniqueness and numerical instability. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC8294472/).

**Johan Nuyts, Bruno De Man, Jeffrey A. Fessler, Wojciech Zbijewski and Freek J. Beekman. Modelling the physics in iterative reconstruction for transmission computed tomography.** Physics in Medicine and Biology 58, R63-R96, 2013. Author-hosted review and demonstrations. [Author PDF](https://johannuyts.github.io/publications/PhysMedBiol2013.pdf).

**Junguo Bian et al. Evaluation of sparse-view reconstruction from flat-panel-detector cone-beam CT.** Physics in Medicine and Biology 55, 6575-6599, 2010. Task-based evaluation precedent. [Institutional full text](https://iacl.ece.jhu.edu/proceedings/iacl/2010/BiaxPhysMedBio10-Evaluation_of_Cone-Beam_CT.pdf).

<!-- page -->
# Platform and reproducibility sources

**scikit-image contributors. Installing scikit-image.** Documentation v0.26.0; update date not stated. macOS platform and dependency requirements. [Installation documentation](https://scikit-image.org/docs/stable/user_guide/install.html).

**ASTRA Toolbox contributors. Installation instructions.** Documentation v2.5.0; update date not stated. CPU-only Apple Silicon route and CUDA-oriented upstream packages. [ASTRA installation](https://astra-toolbox.com/docs/install.html).

**CERN/TIGRE maintainers. Installation Instructions for Python.** Repository master branch; commit date not established. Hardware and platform requirements. [Official installation document](https://github.com/CERN/TIGRE/blob/master/Frontispiece/python_installation.md).

**Pyodide contributors. Packages built in Pyodide.** Documentation runtime 314.0.6 at access; update date not stated. Inventory evidence only; project-specific operation was not tested. [Package inventory](https://pyodide.org/en/stable/usage/packages-in-pyodide.html).

**NumPy developers. Compatibility policy.** Stable random-number documentation; update date not stated. Conditions on random-stream reproducibility. [Compatibility policy](https://numpy.org/doc/stable/reference/random/compatibility.html).

**Astral. Locking and syncing.** uv living documentation; update date not relied upon. Lockfile checking and environment synchronization. [uv documentation](https://docs.astral.sh/uv/concepts/projects/sync/).

**GitHub. Choosing the runner for a job.** Living documentation; update date not stated. Current arm64 and Intel macOS labels. [Runner documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job).

**Streamlit/Snowflake. Using forms.** Living documentation; update date not stated. Batched widget submission. [Forms documentation](https://docs.streamlit.io/develop/concepts/architecture/forms).

**Streamlit/Snowflake. Streamlit's native app testing framework.** Living documentation; update date not stated. AppTest capabilities and automated functional checks. [Testing documentation](https://docs.streamlit.io/develop/concepts/app-testing).

**OpenAI. GPT-6 Astra Model; Model guidance.** Living official documentation; update date not stated. General model capabilities and documented workflow tendencies; no project-specific performance guarantee. [Model page](https://developers.openai.com/api/docs/models/gpt-6-astra); [Model guidance](https://developers.openai.com/api/docs/guides/latest-model).

These sources support technical choices, not the claim that the proposed application has passed them. The probe confirms a narrower native Python CPU path; uv, Streamlit, browser execution, Intel CI and optional toolkits remain implementation work.

<!-- page -->
# Prior art, datasets and publication sources

**Michael Liebling / EPFL Biomedical Imaging Group. Computerized Tomography.** Page footer 11 August 2022. Documented educational projection/filter/backprojection demonstration; live operation not tested. [EPFL demo documentation](https://bigwww.epfl.ch/demo/jtomography/index.html).

**Ash-119. xray-ct-recon.** Public GitHub repository, accessed current README; commit date not established. Documented interface and export overlap; repository performance was not independently reproduced. [Repository](https://github.com/Ash-119/xray-ct-recon).

**Salla Latva-Aijo, Alexander Meaney, Siiri Rautio, Samuli Siltanen, Fernando Silva de Moura and Tommi Heikkila. Helsinki Tomography Challenge 2022.** Finnish Inverse Problems Society, protocol v1.1, updated 28 October 2022. Targets, metadata, splits and reference reconstruction. [Organiser PDF](https://fips.fi/wp-content/uploads/2024/06/Helsinki_Tomography_Challenge_2022_v11.pdf).

**Johannes Leuschner, Maximilian Schmidt, Daniel Otero Baguer and Peter Maass. The LoDoPaB-CT Dataset: A Benchmark Dataset for Low-Dose CT Reconstruction Methods.** arXiv:1910.01113, submitted 2019, revised 3 May 2020. Related final article: LoDoPaB-CT, a benchmark dataset for low-dose computed tomography reconstruction, Scientific Data 8, 109, 16 April 2021; DOI 10.1038/s41597-021-00893-z. [Accessible author preprint](https://arxiv.org/abs/1910.01113); [Final publication](https://www.nature.com/articles/s41597-021-00893-z).

**Henri Der Sarkissian, Felix Lucka, Maureen van Eijnatten, Giulia Colacicco, Sophia Bethany Coban and K. Joost Batenburg. Cone-Beam X-Ray CT Data Collection Designed for Machine Learning: Samples 1-8.** Zenodo, v1, 9 May 2019; part of the 42-walnut collection. Dataset metadata consulted; files not downloaded. [Dataset record](https://zenodo.org/records/2686725).

**GitHub. What is GitHub Pages?** Living documentation; update date not stated. Static hosting scope. [Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

**GitHub. About CITATION files.** Living documentation; update date not stated. Repository citation support. [Citation documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files).

**Zenodo. Archive a release from GitHub.** Living help documentation; update date not stated. Release preservation workflow. [Archiving guide](https://help.zenodo.org/docs/github/archive-software/github-upload/).

**Companion research probe.** Original code and measurements dated 7 September 2026. Includes numerical outputs, package pins, source hashes and instructions for a second-process comparison. It is a feasibility experiment and starting reference, not the finished Missing-Angle CT Detective application.
