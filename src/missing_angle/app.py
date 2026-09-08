"""Local interface. Scientific calculations live outside the UI and can run headlessly."""
import base64
import json

import streamlit as st
import streamlit.components.v1 as components

from missing_angle.bundle import (experiment_id, export_bundle, load_bundle, verify_replay)
from missing_angle.config import ExperimentConfig
from missing_angle.experiment import run_experiment
from missing_angle.game import Challenge, PACKS, PRESETS
from missing_angle.plots import image_figure, sinogram_figure, ct_source_figure
from missing_angle.public_ct import catalogue, licence_text, run_public_ct, WINDOWS
from missing_angle.refinement import refine
from missing_angle.playback import player_html


def social_links(location):
    profiles = (
        ("X", "https://x.com/vesperlemma",
         "M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.64 7.584H.47l8.6-9.835L0 1.154h7.594l5.243 6.932 6.064-6.933ZM17.61 20.644h2.039L6.486 3.24H4.298L17.61 20.644Z"),
        ("LinkedIn", "https://www.linkedin.com/in/alhasan-alkaseem/",
         "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.049c.476-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286ZM5.337 7.433a2.062 2.062 0 1 1 0-4.124 2.062 2.062 0 0 1 0 4.124ZM7.119 20.452H3.555V9h3.564v11.452ZM22.225 0H1.771C.792 0 0 .774 0 1.729V22.27C0 23.226.792 24 1.771 24h20.451C23.2 24 24 23.226 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003Z"),
        ("GitHub", "https://github.com/zakimaths",
         "M12 .297a12 12 0 0 0-3.793 23.385c.6.113.82-.258.82-.577v-2.234c-3.338.725-4.043-1.416-4.043-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.729.083-.729 1.205.085 1.838 1.237 1.838 1.237 1.07 1.834 2.807 1.304 3.492.997.108-.776.418-1.305.762-1.605-2.665-.305-5.467-1.334-5.467-5.931 0-1.31.469-2.381 1.236-3.221-.124-.303-.536-1.524.117-3.176 0 0 1.008-.323 3.301 1.23a11.52 11.52 0 0 1 6.006 0c2.291-1.553 3.297-1.23 3.297-1.23.655 1.652.243 2.873.119 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .322.216.694.825.576A12.001 12.001 0 0 0 12 .297Z"),
    )
    links = ""
    for name, url, path in profiles:
        # Streamlit sanitises inline SVG; an embedded image retains the icon offline.
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
               f'<path fill="#172F3A" d="{path}"/></svg>')
        icon = base64.b64encode(svg.encode()).decode()
        links += (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
            f'aria-label="{name} profile (opens in a new tab)" title="{name} profile — opens in a new tab">'
            f'<img src="data:image/svg+xml;base64,{icon}" width="20" height="20" alt="" '
            'aria-hidden="true"/></a>'
        )
    return f'<nav class="ma-social" aria-label="Social profiles in {location}">{links}</nav>'


@st.cache_data(max_entries=32, show_spinner=False)
def compute(config_json):
    return run_experiment(ExperimentConfig.from_dict(json.loads(config_json)))


def calculate(config):
    return compute(json.dumps(config.to_dict(), sort_keys=True))


def use_config(config):
    st.session_state.pending_config = config
    st.session_state.mode = "Explore"


def controls():
    with st.sidebar:
        st.markdown("### Practise with a known shape")
        st.caption("Change the views or noise, then press Run experiment. This practice image is made from ellipses.")
        with st.form("acquisition"):
            st.number_input("Shape seed (repeat the same image)", min_value=0, max_value=4294967295, key="c_seed")
            st.number_input("Number of viewing angles", min_value=4, max_value=360, step=4, key="c_views")
            st.slider("Angle coverage", 30.0, 180.0, step=5.0, key="c_span", format="%.0f°",
                      help="The measured part of a 180° parallel-beam acquisition.")
            st.slider("Small feature angle", 0.0, 179.999999, step=1.0, key="c_feature_angle", format="%.1f°")
            st.slider("Measurement noise", 0.0, .05, step=.002, format="%.3f", key="c_noise",
                      help="Additive Gaussian noise in line-integral units. This is not a dose model.")
            st.checkbox("Include the small feature", key="c_present")
            with st.expander("More image and method settings"):
                st.selectbox("Image size", [64, 128, 256], key="c_size", format_func=lambda x: f"{x} × {x}")
                st.slider("Rotate the available angles", 0.0, 179.999999, step=1.0, key="c_rotation", format="%.1f°")
                st.slider("Small feature width", 2.0, 10.0, step=1.0, key="c_feature_width",
                          help="Minor diameter in reference pixels at 128 × 128. Physical size stays fixed when resolution changes.")
                st.slider("Small feature brightness", .02, .25, step=.01, key="c_contrast")
                st.selectbox("How to calculate X-ray measurements", ["analytic", "raster"], key="c_projector",
                             format_func=lambda x: "Exact ellipse calculations" if x == "analytic" else "Calculate from image pixels")
                st.number_input("SART correction passes", 1, 10, key="c_sart_passes")
                st.checkbox("Keep SART values above zero", key="c_nonnegative",
                            help="An explicit assumption: negative reconstructed values are clipped after each view update.")
            submitted = st.form_submit_button("Run experiment", type="primary", width="stretch")
        if submitted:
            config = ExperimentConfig.from_dict({k: st.session_state[f"c_{k}"] for k in ExperimentConfig().to_dict()})
            with st.spinner("Calculating measurements and rebuilding the image…"):
                st.session_state.experiment = calculate(config)
            st.session_state.pop("replay_report", None)
        st.button("Reset to baseline", on_click=use_config, args=(ExperimentConfig(),), width="stretch")
        st.divider()
        st.caption("This practice activity uses invented shapes with known answers. Return to Real CT lab to work with acquired images.")


def result_images(exp, truth=True, mark=False):
    methods = [("phantom", "Prepared reference" if "source_hu" in exp.arrays else "Known answer"), ("fbp", "FBP"), ("sart", "SART")]
    if not truth:
        methods = methods[1:]
    for column, (method, label) in zip(st.columns(len(methods)), methods):
        with column:
            st.markdown(f"**{label}**")
            st.image(image_figure(exp, method, mark=mark), width="stretch")
    st.caption("FBP: filtered back projection. SART: iterative reconstruction. Shared grayscale: 0 to 0.6 attenuation units. Values outside this range are display-clipped; metrics use the full arrays."
               + (" Gold outline: the known target location and shape." if mark else ""))


def metrics_table(exp):
    rows = []
    for method, title in (("fbp", "Filtered back projection"), ("sart", "SART")):
        m = exp.metrics["methods"][method]
        recovery = m["contrast_recovery"]
        rows.append({"Method": title, "Image difference (RMSE) ↓": f"{m['rmse']:.4f}",
                     "Feature brightness difference": f"{m['roi_contrast']:+.4f}",
                     "Fraction of original contrast": f"{recovery:.1%}" if recovery is not None else "— absent control"})
    st.table(rows)
    st.caption(f"We measure brightness inside the outlined feature and compare it with the surrounding area. Reference contrast: {exp.metrics['reference_roi_contrast']:+.4f}. "
               "The target mean uses its saved area weights; background is a surrounding annulus. "
               "Contrast can exceed 100% or be negative. It is not a detection probability.")


def export_control(exp, key):
    identifier = experiment_id(exp)
    st.download_button("Download experiment (.zip)", data=export_bundle(exp),
                       file_name=f"missing-angle-{identifier}.zip", mime="application/zip", key=key)
    st.caption(f"Experiment {identifier} · includes images, X-ray measurements, settings and software versions.")


def explore():
    controls()
    exp = st.session_state.experiment
    c = exp.config
    st.markdown("## Which details survive when some views are missing?")
    st.write("Compare the practice image with two attempts to rebuild it from the available X-ray measurements.")
    st.markdown(f"**{c.views} measured views** · {c.span:g}° covered / {180-c.span:g}° missing · "
                f"noise σ {c.noise:g} · seed {c.seed} · {c.size} × {c.size}")
    result_images(exp, mark=True)
    metrics_table(exp)
    with st.expander("See the measurements and where the images differ"):
        st.image(sinogram_figure(exp), width="stretch")
        st.caption("Blank angular cells are unmeasured, not measured zeros. Angles wrap at 180°. "
                   "Negative noisy values and integrals above 0.6 are display-clipped in this figure.")
        for col, method in zip(st.columns(2), ("fbp", "sart")):
            with col:
                st.markdown(f"**{method.upper()} − ground truth**")
                st.image(image_figure(exp, method, error=True), width="stretch")
        st.caption("Signed error scale: blue −0.2, white 0, red +0.2 attenuation units. Saturation uses the same limits in both images.")
    with st.expander("Understand the method assumptions"):
        st.write(f"{c.projector.capitalize()} parallel-beam projection on a two-unit field of view. "
                 "The analytic model integrates continuous ellipses along ideal centre rays. "
                 "The displayed reference is independently rasterised using 4 × 4 samples per pixel.")
        st.write(f"FBP uses the ramp filter and weights the measured angular interval by {c.span/180:.3f} "
                 "relative to a full half-turn. This changes amplitude as coverage shrinks. "
                 f"SART uses {c.sart_passes} passes, relaxation 0.15, and "
                 f"{'a nonnegative constraint' if c.nonnegative else 'no positivity constraint'}. "
                 "Neither method receives ground truth or the target mask.")
        st.caption("Anatomy-inspired ellipses are not a realistic organ model. Sparse views, missing angles and noise "
                   "are different sources of error. Projection count is an educational budget, not a radiation-dose estimate.")
    st.divider()
    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Download this practice experiment")
        export_control(exp, "export_explore")
    with right:
        st.markdown("### Open a saved experiment")
        replay_upload("explore")
    replay_status("replay_report")


def restore_bundle(loaded, report):
    if "source_hu" in loaded.arrays:
        st.session_state.ct_experiment = loaded
        st.session_state.ct_pending = True
        st.session_state.ct_replay_report = report
        st.session_state.pending_mode = "Public CT"
    else:
        st.session_state.pending_config = loaded.config
        st.session_state.pending_experiment = loaded
        st.session_state.replay_report = report
        st.session_state.pending_mode = "Explore"


def replay_upload(key):
    uploaded = st.file_uploader("Choose an experiment ZIP file", type=["zip"], max_upload_size=16, key=f"{key}_upload")
    if st.button("Recalculate saved experiment", disabled=uploaded is None, key=f"{key}_replay"):
        try:
            with st.spinner("Opening your saved measurements and calculating the images again…"):
                loaded, manifest = load_bundle(uploaded.getvalue())
                report = verify_replay(loaded, manifest)
            restore_bundle(loaded, report)
            st.rerun()
        except ValueError as error:
            st.error(f"Could not open this bundle: {error}")


def replay_status(key):
    if key in st.session_state:
        report = st.session_state[key]
        checks = report["checks"]
        if all(x["exact"] for x in checks.values()):
            st.success("Recalculation complete: every checked image and saved step matches exactly.")
        elif all(x["within_tolerance"] for x in checks.values()):
            st.info("Recalculation complete: tiny numerical differences are within the allowed tolerance.")
        else:
            st.warning("These results differ from the saved experiment. Open the details below to compare software versions and differences.")
        with st.expander("Recalculation details"):
            st.json(report)


@st.cache_data(max_entries=24, show_spinner=False)
def compute_ct(index, config_json, passes=10, weight=.002):
    return refine(run_public_ct(index, ExperimentConfig.from_dict(json.loads(config_json))), passes, weight)


def public_ct():
    metadata = catalogue()
    if "ct_experiment" not in st.session_state:
        c = ExperimentConfig(views=48, span=120, projector="raster", present=False, nonnegative=True)
        st.session_state.ct_experiment = compute_ct(80, json.dumps(c.to_dict(), sort_keys=True))
    exp = st.session_state.ct_experiment
    fields = ("views", "span", "noise", "size", "rotation", "seed", "sart_passes", "nonnegative")
    defaults = {f"p_{k}": getattr(exp.config, k) for k in fields}
    defaults["p_slice"] = exp.geometry["source"]["slice"]["index"]
    defaults["p_refine_passes"] = exp.geometry.get("refinement", {}).get("passes", 10)
    defaults["p_smoothing"] = exp.geometry.get("refinement", {}).get("weight", .002)
    reset = st.session_state.pop("ct_pending", False)
    for key, value in defaults.items():
        if reset or key not in st.session_state:
            st.session_state[key] = value
    with st.sidebar:
        st.markdown("### Choose a real CT slice")
        st.write("3D Slicer · CT Chest")
        st.caption("Eight horizontal slices from one real chest CT scan. These images are bundled so the lab works offline.")
        with st.form("ct_acquisition"):
            st.selectbox("Chest slice", [s["index"] for s in metadata["slices"]], key="p_slice",
                         format_func=lambda x: f"Slice {x}")
            st.number_input("Number of viewing angles", 4, 360, key="p_views")
            st.slider("Angle coverage", 30., 180., step=5., key="p_span", format="%.0f°")
            st.slider("Measurement noise", 0., .05, step=.002, key="p_noise", format="%.3f")
            with st.expander("Reconstruction settings"):
                st.selectbox("Reconstruction size (pixels)", [64, 128, 256], key="p_size")
                st.slider("Rotate the available angles", 0., 179.999999, step=1., key="p_rotation", format="%.1f°")
                st.number_input("Noise seed", 0, 4294967295, key="p_seed")
                st.number_input("Basic SART: number of passes", 1, 10, key="p_sart_passes")
                st.checkbox("Keep basic SART values above zero", key="p_nonnegative", help="An assumption about attenuation, not extra measurements.")
                st.number_input("Smoothing method: number of passes", 1, 20, key="p_refine_passes")
                st.slider("Smoothing strength", 0., .02, step=.001, format="%.3f", key="p_smoothing", help="Higher values reduce grain and streaks, but may erase small details. Zero switches smoothing off.")
            if st.form_submit_button("Reconstruct this slice", type="primary", width="stretch"):
                c = ExperimentConfig(**{k: st.session_state[f"p_{k}"] for k in fields},
                                     projector="raster", present=False)
                with st.spinner("Calculating X-ray measurements and rebuilding the image…"):
                    exp = compute_ct(st.session_state.p_slice, json.dumps(c.to_dict(), sort_keys=True),
                                     st.session_state.p_refine_passes, st.session_state.p_smoothing)
                st.session_state.ct_experiment = exp
                st.session_state.pop("ct_replay_report", None)
        window = st.selectbox("Show tissues in the original image", list(WINDOWS), key="ct_window")
        st.caption("The tissue display changes immediately. Other settings take effect when you press Reconstruct this slice.")
    c = exp.config
    source = exp.geometry["source"]
    st.markdown("## Rebuild a real chest CT image")
    st.write("Choose a slice and a set of viewing angles on the left, then press **Reconstruct this slice**. "
             "Try reducing the angle coverage to see which edges become harder to recover.")
    st.caption("These are real, anonymised CT images from a public 3D Slicer dataset. "
               "We simulate new X-ray measurements from each image; the original scanner measurements are not available.")
    st.markdown(f"**Slice {source['slice']['index']} · {c.views} viewing angles · {c.span:g}° covered / {180-c.span:g}° missing** "
                f"· added noise {c.noise:g} · {c.size} × {c.size} reconstruction")
    left, right = st.columns([1, 1])
    with left:
        st.markdown("### The original CT image")
        st.image(ct_source_figure(exp.arrays["source_hu"], window), width="stretch")
        st.caption("This is one horizontal slice through the chest. Display windows change which tissues are easiest to see; "
                   "they do not change the experiment. HU (Hounsfield units) describe how strongly tissue attenuates X-rays.")
    with right:
        st.markdown("### Watch the image take shape")
        if "history" in exp.arrays:
            components.html(player_html(exp.arrays["history"], smoothing=bool(exp.geometry["refinement"]["weight"])), height=510, scrolling=True)
        else:
            st.info("This older experiment has no saved steps. Press Reconstruct this slice to record them.")
        st.caption("Each pass reuses all available viewing angles. The method corrects the image and uses smoothing when its strength is above zero. "
                   "Extra passes do not add measurements from missing angles.")
    st.markdown("### Compare reconstruction methods")
    items = [("fbp", "Fast method · FBP"), ("sart", "Repeated correction · SART")]
    if "regularized" in exp.arrays:
        items.append(("regularized", "Correction + smoothing"))
    for col, (method, label) in zip(st.columns(len(items)), items):
        with col:
            st.markdown(f"**{label}**")
            st.image(image_figure(exp, method), width="stretch")
    st.write("**FBP** combines the views using a filter. **SART** repeatedly corrects an image to fit the measurements. "
             "**Correction + smoothing** adds gentle total-variation (TV) smoothing between corrections. "
             "Smoothing can reduce streaks and grain, but it can also remove small details.")
    st.caption(f"Basic SART: {c.sart_passes} passes. Correction + smoothing: {exp.geometry.get('refinement', {}).get('passes', 0)} passes. "
               "All methods use the same brightness scale: 0–0.6 relative attenuation. A brighter display does not mean a better reconstruction.")
    st.table([{"Method": label, "Difference from reference ↓": f"{exp.metrics['methods'][method]['rmse']:.5f}",
               "Mismatch with measurements ↓": f"{exp.metrics['methods'][method]['raster_residual_rmse']:.5f}"}
              for method, label in items])
    st.caption("Both scores use root mean square error (RMSE): smaller means closer. The first compares pixels with the smaller, "
               "prepared CT reference; the second compares predicted measurements with the available measurements. "
               "A low score is not proof that every anatomical detail is correct.")
    with st.expander("What is the reference image, and what can this experiment tell me?"):
        st.image(image_figure(exp, "phantom"), width="stretch")
        st.write("We convert the original CT values to a simple relative-attenuation model and shrink the whole image into a circular "
                 "field. This prepared image is the target for comparison. We keep the original pixels in your download.")
        st.write("The source CT is already a reconstruction, not perfect knowledge of anatomy. These simulations help you study "
                 "missing views, noise and assumptions; they do not test diagnosis, patient dose or a real scanner.")
        st.caption(f"Source pixel spacing: {source['pixel_spacing_yx_mm'][0]:.4f} mm. The simulation uses a normalised two-unit field.")
    with st.expander("See the X-ray measurements and preparation details"):
        st.image(sinogram_figure(exp), width="stretch")
        st.json(exp.geometry["preprocessing"])
    with st.expander("Data source, attribution & licence"):
        st.markdown("[3D Slicer sample-data documentation](https://www.slicer.org/wiki/Documentation/4.10/Modules/SampleData) · "
                    "[Source and licensing clarification](https://discourse.slicer.org/t/origin-of-ct-chest-sample-data/37731)")
        st.write(source["origin_note"])
        st.write(source["modification"])
        st.code(source["source_sha256"], language=None)
        st.text(licence_text())
    st.divider()
    a, b = st.columns(2)
    with a:
        st.markdown("### Download this experiment")
        export_control(exp, "export_ct")
        st.caption("Includes original CT pixels, preprocessing, source checksums and the data licence.")
    with b:
        st.markdown("### Open a saved experiment")
        replay_upload("ct")
    replay_status("ct_replay_report")


def detective():
    with st.sidebar:
        st.markdown("### Investigate a small feature")
        st.write("A small feature may be present at the outlined location. Spend views to investigate, then make a prediction.")
        st.caption("This optional challenge uses an invented image so we know the answer. The image stays the same as you add views.")
        st.divider()
        st.write("120° angular span · noise σ 0.006 · 128 × 128 · 3 SART correction passes")
        st.caption("More views refine sampling inside the same span. They do not fill its missing 60°.")
    if "challenge" not in st.session_state:
        st.session_state.challenge = Challenge()
    case = st.session_state.challenge
    exp = calculate(case.config())
    st.markdown("## Is the small feature present?")
    st.write("The outline tells you where to look. Both reconstructions use only the views you have bought.")
    st.markdown(f"**Case {case.seed}** · {case.views} / 96 views spent · {case.remaining} remaining")
    for col, pack in zip(st.columns(4), PACKS):
        with col:
            label = f"{pack} views · +{max(0, pack-case.views)}" if pack > case.views else f"{pack} views acquired"
            if st.button(label, disabled=case.revealed or pack <= case.views, width="stretch", key=f"buy_{pack}"):
                st.session_state.challenge = case.buy(pack)
                st.rerun()
    result_images(exp, truth=case.revealed, mark=True)
    if not case.revealed:
        with st.form("prediction"):
            a, b = st.columns(2)
            with a:
                st.radio("Your prediction", ["Present", "Absent"], index=None, key="guess")
            with b:
                st.radio("Your confidence", ["Low", "Medium", "High"], index=None, key="confidence")
            if st.form_submit_button("Reveal ground truth", type="primary"):
                if st.session_state.guess is None or st.session_state.confidence is None:
                    st.warning("Choose a prediction and confidence before revealing.")
                else:
                    st.session_state.verdict = {"prediction": st.session_state.guess,
                                                "confidence": st.session_state.confidence}
                    st.session_state.challenge = case.reveal()
                    st.rerun()
    else:
        prediction = st.session_state.verdict
        answer = "Present" if case.present else "Absent"
        matched = prediction["prediction"] == answer
        feedback = st.success if matched else st.warning
        feedback(f"Known answer: {answer.lower()}. Your prediction was {'correct' if matched else 'incorrect'}. "
                 f"You used {case.views} views with {prediction['confidence'].lower()} confidence.")
        st.caption("One case does not measure diagnostic skill or calibrate confidence. "
                   "Compare both present and absent cases, and look for artifacts that mimic the target.")
        metrics_table(exp)
        export_control(exp, "export_case")
    if st.button("Start next case"):
        st.session_state.challenge = Challenge(seed=(case.seed+1) % (2**32))
        for key in ("guess", "confidence", "verdict"):
            st.session_state.pop(key, None)
        st.rerun()


def atlas():
    with st.sidebar:
        st.markdown("### Reconstruction examples")
        st.write("Compare too few views, missing angles and noisy measurements.")
        st.caption("These are computed synthetic examples. Each preset uses the same phantom seed and can be opened in Explore.")
    st.markdown("## Explore common reconstruction problems")
    selected = st.radio("Choose a problem to explore", list(PRESETS), horizontal=True, key="atlas_preset")
    preset = PRESETS[selected]
    st.write(preset["description"])
    exp = calculate(preset["config"])
    c = exp.config
    st.caption(f"{c.views} views · {c.span:g}° coverage · noise σ {c.noise:g} · seed {c.seed}")
    result_images(exp, mark=True)
    metrics_table(exp)
    st.button("Try these settings in practice", on_click=use_config, args=(c,), type="primary")
    st.info("For a controlled comparison, hold the view count fixed when changing angular span. "
            "Hold span and noise fixed when changing view count. These three starting points are not a ranking of methods.")


def main():
    st.set_page_config(page_title="Missing-Angle CT Detective", page_icon="◌", layout="wide",
                       initial_sidebar_state="auto")
    st.html("""<style>
    .stApp {color: #172F3A;}
    .block-container {padding: 4rem 2rem 3rem; max-width: 1500px;}
    h1 {font-size: 1.8rem !important; letter-spacing: -.035em;}
    h2 {font-size: 1.5rem !important; letter-spacing: -.025em;}
    h3 {font-size: 1.12rem !important;}
    button:focus-visible, input:focus-visible {outline: 3px solid #007F87 !important; outline-offset: 2px;}
    [data-testid="stSidebar"] {border-right: 1px solid #DCE5E5;}
    [data-testid="stAppDeployButton"] {display: none;}
    .ma-heading {display: flex; align-items: center; flex-wrap: wrap; gap: 16px 24px;}
    .ma-heading h1 {margin: 0; padding: 0; flex: 1 1 400px;}
    .ma-social {display: flex; justify-content: flex-end; gap: 8px; margin-left: auto;}
    .ma-social a {display: inline-flex; align-items: center; justify-content: center;
        width: 44px; height: 44px; color: #172F3A; background: #FFFFFF;
        border: 1px solid #789398; border-radius: 0; text-decoration: none;
        transition: color 120ms ease, background-color 120ms ease;}
    .ma-social img {flex-shrink: 0;}
    .ma-social a:hover {background: #F0F5F5; border-color: #007F87;}
    .ma-social a:focus-visible {outline: 3px solid #007F87; outline-offset: 3px;}
    @media(max-width: 700px) {.block-container {padding: 4rem 1rem 3rem;} h1 {font-size: 1.6rem !important;}}
    @media(prefers-reduced-motion: reduce) {* {scroll-behavior: auto !important; transition: none !important;}}
    </style>""")
    if "experiment" not in st.session_state:
        st.session_state.pending_config = ExperimentConfig()
    if "pending_config" in st.session_state:
        config = st.session_state.pop("pending_config")
        for name, value in config.to_dict().items():
            st.session_state[f"c_{name}"] = value
        saved = st.session_state.pop("pending_experiment", None)
        st.session_state.experiment = saved if saved is not None else calculate(config)
        if saved is None:
            st.session_state.pop("replay_report", None)
    for name, value in st.session_state.experiment.config.to_dict().items():
        st.session_state.setdefault(f"c_{name}", value)
    st.html('<header class="ma-heading"><h1 id="missing-angle-ct-detective">'
            'Missing-Angle CT Detective</h1>' + social_links("header") + '</header>')
    st.markdown("**How does a CT scanner build an image—and what happens when some views are missing?**")
    st.write("This lab is for students learning CT reconstruction. Start with a real chest CT slice, choose how many X-ray views "
             "are available, and watch a computer rebuild the image. Compare methods to see how missing angles, noise and smoothing change the result.")
    if "pending_mode" in st.session_state:
        st.session_state.mode = st.session_state.pop("pending_mode")
    st.session_state.setdefault("mode", "Public CT")
    mode = st.radio("Choose an activity", ["Public CT", "Explore", "Detective", "Atlas"], horizontal=True,
                    format_func=lambda x: {"Public CT": "Real CT lab", "Explore": "Synthetic practice", "Detective": "Feature challenge", "Atlas": "Artifact examples"}[x],
                    key="mode", label_visibility="collapsed")
    st.divider()
    {"Explore": explore, "Public CT": public_ct, "Detective": detective, "Atlas": atlas}[mode]()
    st.divider()
    st.caption("Learn with real CT images and optional synthetic practice. X-ray measurements are simulated. This is a teaching lab, not a diagnostic tool.")
    st.html(social_links("footer"))


if __name__ == "__main__":
    main()
