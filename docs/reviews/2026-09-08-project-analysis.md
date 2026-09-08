# Project analysis and proposed next release

Reviewed 8 September 2026 against commit `5c2024bb93ce1240eab47eab7bd2a5d58bc13391`.

## Assessment

Missing-Angle CT is a functioning, reproducible reconstruction project with a useful educational interface. Its strongest next step is to become a coherent workbench for comparing reconstruction experiments. The current limitation is the separation between workflows and the breadth of validation, rather than a lack of algorithms or animation.

The browser calculation is real. It starts from zero and updates an image using projection measurements. The measured patient workflow also performs an actual three-dimensional calculation. Neither finding establishes that a result recovers true anatomy or that refinement improves every acquisition.

## Evidence checked

This review inspected the browser solver and worker, evaluation and annotation code, Python embedding and import validation, clinical reconstruction and replay code, data preparation and benchmark scripts, documentation, dependency declarations and all three GitHub workflows.

Fresh local checks passed: 85 Python tests, 18 JavaScript tests, Ruff checks including the clinical directory, and all 120 benchmark comparisons at the committed absolute tolerance of 1e-9. The Python tests used the existing installed QA environment; JavaScript and lint checks read the checkout directly. This was not a fresh Mac installation test.

Remote evidence: [current scientific and Mac replay run](https://github.com/zakimaths/missing-angle-ct/actions/runs/34202969974) and [current Pages build](https://github.com/zakimaths/missing-angle-ct/actions/runs/34202969894) succeeded. The [clinical ARM and Intel run](https://github.com/zakimaths/missing-angle-ct/actions/runs/34201283638) succeeded on the earlier clinical commit; subsequent changes did not change that clinical implementation. The three-dimensional reconstruction was not rerun during this review.

The earlier accessibility/security review was inspected. No new browser-wide accessibility audit, manual VoiceOver assessment, penetration test or peak-memory measurement was performed here.

## What exists today

| Workflow | Demonstrated capability | Current boundary |
|---|---|---|
| Browser and embedded live lab | Ray-length SART from three measured Helsinki objects, four body slices with independently simulated projections, and analytic disks; real calculation snapshots, refinement, errors, manual regions, export and replay | 2D, 64–128 pixels per side; fixed fan/parallel geometry; prepared line integrals required |
| Python experiment tools and recorded gallery | FBP, SART and total-variation refinement; seeded experiments, public CT simulations, feature examples and replay | Different numerical model, units and refinement settings from the live browser workflow |
| Optional clinical command-line workflow | CPU FDK from 356 measured projections of COBRA2026 A002, physical geometry, masked reference comparison and offline repeat | One pinned patient acquisition, small output grids, separate environment, no integrated volume viewer |

The four live body slices represent two source volumes. The clinical reference is another RTK FDK reconstruction. Only the analytic control provides a known continuous object. These distinctions are already documented in places, but should govern all comparisons and claims.

## Highest-value changes

### 1. Make refinement a reversible comparison

The benchmark contains a useful counterexample to the word “enhance”. With 360 spread views, even the lowest-error tested enhancement increases reference RMSE by 2.9% for object A, 4.5% for B and 3.6% for C. The current three-extra-pass/light-smoothing recipe increases it by approximately 8.2%, 15.8% and 9.8%, respectively. At the same time, unused-ray error falls. Better agreement with measurements and better agreement with the authors' image are different objectives. The reference itself remains an estimate.

The interface already reports these disagreements. Improve the decision process by keeping named reconstruction checkpoints, offering one-click restoration of any stage, and comparing alternative recipes from the same checkpoint. The current first-pass button recalculates; intermediate refinement stages are not restorable calculation states. Record image and region metrics for every stage, alongside the existing ray-error history.

Acceptance: a user can compare two recipes from an identical starting image, restore either result, and export/replay the selected history. A worse reference score remains visibly worse. Any automatic stopping rule must be evaluated on data not used to tune it; do not use the displayed reference to silently choose the answer.

### 2. Integrate the measured patient workflow into the Mac app

Expose the existing verified case through a local interface: select case, download with progress and integrity checks, choose reconstruction settings, run or cancel, inspect slices, compare with the reference, save the experiment. Begin with the existing case before generalising ingestion. Keep the heavy numerical calculation in a separate local process so interface cancellation and failures do not leave a misleading completed result.

Add linked axial, sagittal and coronal views, physical spacing/orientation labels, shared display windows and physical-coordinate regions. Preserve the lightweight public browser lab. A published patient-study viewer can show saved results and provenance, with calculation clearly identified as local.

Acceptance: the existing 356-view calculation can be completed and repeated offline from the Mac interface; cancellation, failed downloads and reopening a saved result are verified.

### 3. Establish evaluation across independent acquisitions

Start with a modest proposed cohort, for example 6–12 available cases, and reserve cases before adjusting parameters. Use more than one centre only after implementing and verifying the relevant calibration and geometry adapters. The current A002 assumptions must not be reused blindly for another scanner.

COBRA2026 supplies measured projections, geometry and several reference products. Its released training collection provides a potential source for a project-specific development/evaluation split. Its official validation and test downloads currently list a later release date, so they should not be described as available. The dataset is CC BY-NC 4.0. [Official dataset record](https://zenodo.org/records/21322350).

Compare against the authors' RTK result for implementation agreement and, where compatible, the clinical reconstruction for a different reference. An aligned planning CT is another comparison target with registration and acquisition differences, not exact truth. Report the reference identity separately for each result.

Acceptance: fixed case manifests and settings reproduce a per-case report with failure cases, differences between methods, resolution, elapsed time and memory. Report distributions across acquisitions; do not treat thousands of correlated pixels or multiple slices from one volume as independent patients.

### 4. Strengthen measurement quality checks and image assessment

Import validation presently checks dimensions, ranges and supported geometry. Add acquisition checks for duplicate orientations, angular gaps, irregular ordering, detector coverage and clipping. Current “spread” and “sector” selection operate on row indices, so irregular imported angle ordering can produce a misleading interpretation. Preserve row-to-measurement correspondence when handling ordering.

Keep the adaptive full-circle sequence indicator requested for playback. Add a separate physical-angle coverage plot: a full sequence is not necessarily a complete angular acquisition.

Extend whole-image scores with a defined object/body mask, selected-region scores, edge profiles and small-feature contrast where a justified target exists. Keep selected-ray, unused-ray and reference-image errors separate. An uncertainty study could examine sensitivity to geometry and noise perturbations; call the resulting map sensitivity until its relationship to reconstruction error has been validated.

Acceptance: reordered and irregular-angle fixtures retain correct geometry; duplicated endpoints are identified without silently discarding legitimate repeat measurements; masks and regions survive export with physical coordinates and provenance.

### 5. Consolidate the software before adding more methods

Retain Python, NumPy/SciPy, scikit-image, RTK, the local interface and browser workers. RTK is an established cross-platform cone-beam reconstruction toolkit with CPU implementations, consistent with the project's Mac requirement. [RTK project](https://www.openrtk.org/).

Format and divide the dense browser source into numerical operations, experiment state, rendering and import/export modules. The live controller is roughly 20 KB in 67 lines; evaluation and annotations are roughly 17 KB in 88 lines. This makes state transitions difficult to review. Give experiments a shared manifest vocabulary for acquisition, method/version, units, geometry, reference, stages and annotations while retaining specialised 2D and 3D numerical implementations.

Name methods precisely: browser refinement currently uses neighbour averaging; the Python experiment tools use total variation. Their numerical strengths are not interchangeable. Introduce another regularised method only with an explicit objective, convergence checks and benchmark comparison.

Acceptance: existing replay and benchmark checks remain stable after structural changes. A user can tell which solver and regularisation produced every saved image.

### 6. Turn manual quality checks into durable release checks

Add browser interaction coverage for reconstruct, pause/step, cancellation, refinement, labels, malformed imports and export/replay, including rapid dataset switches. Add automated accessibility checks in CI and a documented Safari/VoiceOver pass. Pin Node explicitly and align setup-tool versions across workflows. Schedule dependency checks for both locked environments.

The clinical replay checker compares reported settings and voxel arrays, but does not compare the loaded image headers' origin, spacing and direction. Verify those physical properties as well: numerically equal arrays with different spatial metadata are not the same physical image.

Add opt-in local draft recovery, with a clear delete action, so labels and unfinished comparisons can survive an accidental refresh. Current browser state is held in memory and export is manual.

Acceptance: CI catches an incorrect displayed snapshot, a failed round trip, a lost label and a changed volume orientation. Define practical runtime and memory budgets before increasing resolution.

### 7. Refresh documentation and release identity

PRODUCT.md and DESIGN.md describe earlier workflows, student wording and unverified Intel support. README combines newer measured-data capabilities with older general statements about missing scanner projections, and its broad MIT summary needs the clinical Apache-2.0 exception linked clearly. Historical validation entries should remain dated, with a current status table first.

Publish a capability matrix for browser versus Mac, a current architecture diagram, a concise example report, versioned release notes and citation metadata. Keep code licences and each dataset's terms distinct. This will make the GitHub portfolio easier to assess than further promotional wording.

## Performance priorities

The worker separates computation from interaction, and the existing workload cap is useful. However, evaluation traces all available views even when only a subset is reconstructed, and uncached unused-view matrices are recreated at each assessment. The Mac embedding also serialises all seven projection/reference pairs, approximately 7.6 MB of raw JSON, into the interface. These are concrete profiling targets, not measured bottlenecks in this review.

Measure preparation, calculation, scoring, rendering and peak memory separately. Then consider bounded matrix caching, fewer retained snapshots outside teaching playback, and loading local data on demand. Choose WebAssembly or another backend only if measurements justify the added build and replay complexity.

## Recommended sequence

1. **Reliable comparisons:** reversible refinement, stage metrics, physical replay checks, current documentation and browser regression coverage.
2. **Usable real-data workflow:** integrate the existing clinical case into the Mac app with volume inspection and saved experiments.
3. **Evidence across cases:** verified adapters, a reserved evaluation cohort and a published comparative report.
4. **Research extension:** assess regularisation and measurement-budget strategies, including whether an additional view improves a chosen feature or error criterion on previously unused cases.

The final extension returns to the original “Missing-Angle” idea: explaining which measurements matter and which features remain unsupported. That is a stronger distinguishing contribution than another generic reconstruction or smoothing control. Synthetic controls should remain available for exact checks while acquired data leads the user experience.
