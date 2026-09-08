---
name: Missing-Angle CT Detective
description: A quiet local workstation for comparing measured evidence and synthetic CT reconstructions.
colors:
  primary: "#007F87"
  canvas: "#FFFFFF"
  secondary-surface: "#F0F5F5"
  ink: "#172F3A"
  divider: "#DCE5E5"
  target-outline: "#F0B95C"
typography:
  body:
    fontFamily: "sans-serif"
  headline:
    fontSize: "1.8rem"
    letterSpacing: "-0.035em"
  section:
    fontSize: "1.5rem"
    letterSpacing: "-0.025em"
  title:
    fontSize: "1.12rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.canvas}"
  work-surface:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
---

# Design System: Missing-Angle CT Detective

## Current live interface

The default surface is the shared browser reconstruction lab in `src/missing_angle/web/`, embedded in the local Mac app and published to GitHub Pages. Its CSS and panel are the visual authority for that surface. The detailed Streamlit descriptions below describe the earlier Python experiment workspaces where they differ.

Use formal, educational language for general users. The public demo offers Light (white, ink and teal), Pink (pale pink with a dark rose accent), and Dark (deep plum with a light pink accent) appearances. Preserve native controls, clear focus and labelled scientific figures. The selected appearance persists locally; the system preference supplies the initial light or dark appearance. Reconstruction pixels and the signed-error colour scale never change with the interface theme. Scientific scatter plots retain white axes and their labelled teal/rust series. Saved checkpoints sit beside refinement controls. Show each checkpoint's starting image and scores, and allow exact restoration before testing an alternative. The angular ring represents relative sequence position; physical angles remain explicit in labels. Clinical 3D calculation currently links to its separate local workflow.

## Overview

**Creative North Star: "Quiet scientific workstation"**

The interface puts measurements and their limitations beside the images they produce. Its white work surface, cool supporting surface and restrained teal controls continue the research report's visual language. Numerical images provide the visual detail; explanatory text helps the reader compare them.

This is an operating tool built with native Streamlit controls. The project owns the theme, compact heading hierarchy, outer layout, focus override and scientific figure conventions. Streamlit owns the remaining control geometry and state styling; those framework defaults are not a separate custom component system.

**Key Characteristics:**

- Applied acquisition settings stay beside the displayed results.
- Scientific comparisons share scales and coordinate conventions.
- Original CT pixels, prepared references and simulated reconstructions retain distinct labels and units.
- Teal identifies interaction; gold identifies the known target outline.
- Secondary evidence appears in expanders after the main comparison.
- Native controls retain their keyboard and disabled-state behaviour.

This document records the implemented interface in `src/missing_angle/app.py`, figure conventions in `src/missing_angle/plots.py`, and the theme in `.streamlit/config.toml`. It is an implementation record, not a separately approved branding exercise.

## Colors

One cool action accent sits on white and pale cool surfaces, with dark blue-grey text.

### Primary

- **Instrument Teal** (`primary`): the Streamlit theme accent for primary actions and selected controls; also the explicit keyboard focus outline.

### Neutral

- **White Canvas** (`canvas`): the main work surface and exported figure background; also primary-button text through the native light theme.
- **Cool Supporting Surface** (`secondary-surface`): the theme's secondary background, most visibly the sidebar and native supporting control surfaces.
- **Ink** (`ink`): application text and the reconstruction figures' axis labels and ticks.
- **Quiet Divider** (`divider`): the sidebar's thin separating border. Other dividers use the framework theme.

The **Gold Target Outline** (`target-outline`) is a scientific annotation, not a second action accent. It marks the known synthetic target location and shape in both reference and reconstructed images; Public CT has no target annotation. Signed error figures use Matplotlib's `RdBu_r` colour map; ordinary reconstruction figures and original CT slices use `gray`. Native success, information, warning and error colours retain their framework meanings.

The sidecar's derived tonal ramps are palette-preview aids, not additional colours applied by the app. Its portable component samples show the project-owned theme and focus rules; the running Streamlit app remains the authority for native widget styling.

**The Shared Scale Rule.** Compare the prepared reference, FBP and SART images with the same grayscale limits. Image appearance must not silently rescale each method. Display the original CT separately in labelled Hounsfield units with its selected display window.

**The Meaningful Colour Rule.** Keep action colour, target annotation and numerical error colour distinct. A failed prediction uses warning feedback; an exact successful replay uses success feedback.

## Typography

**Body Font:** the Streamlit `sans serif` theme option. The concrete font family, base size, weights and line heights remain framework defaults.

**Character:** compact application headings introduce a dense but readable working surface. Bold labels identify the scientific images; captions carry units, applied limitations and measurement definitions.

### Hierarchy

- **Headline** (`headline`): the application name. It becomes `1.6rem` at the project's narrow-screen breakpoint.
- **Section** (`section`): the current workspace question or comparison task.
- **Title** (`title`): sidebar setup and save/replay subsection headings.
- **Body and label** (`body`): native Streamlit prose, form labels, tables and captions; retain the framework hierarchy instead of adding a separate type scale.
- **Figure labels:** reconstruction axes use Matplotlib labels and ticks at 9 points. Figure typography is rendered into the exported image and scales with it in the browser.

**The Units Beside Evidence Rule.** Keep image scales, physical units and the meaning of each metric close to their figures or table. Captions are part of the scientific reading order.

## Layout

The app uses Streamlit's wide layout and a supporting sidebar. The main container is capped at `1500px` and uses top, horizontal and bottom padding of `4rem`, `2rem` and `3rem`. At widths up to `700px`, horizontal padding becomes `1rem`; the other padding remains unchanged. Sidebar collapse and column wrapping use Streamlit's responsive behaviour rather than a project-defined breakpoint system.

Explore places the applied view count, coverage, noise, seed and image size before equal-width reference, FBP and SART columns. Detective uses two reconstruction columns until reveal; the reference then joins the comparison. Metrics follow images. Measurements, reconstruction error and assumptions use expandable sections. Save and replay occupy two equal-width columns after a divider.

Public CT first pairs the original CT image with an explanation of what the experiment measures, then presents the prepared reference, FBP and SART in the shared three-column comparison. The applied source slice, source dimensions, simulated view count and working-grid size precede these figures. Preprocessing and source attribution use separate expanders; save and replay retain the same two-column arrangement.

Explore, Public CT, Detective and Atlas share a horizontal native radio control. Plot images stretch to their columns, and the scientific coordinate system stays inside each image. There is no custom spacing scale beyond the explicitly controlled outer container; ordinary gaps and form spacing are framework defaults.

**The Applied State Rule.** Result headings, metrics and downloads describe the last applied experiment. Pending form edits must not relabel an older reconstruction.

## Elevation & Depth

The project adds no shadow system. The white canvas, pale sidebar, thin boundary and native dividers separate regions; expanders reveal secondary evidence without introducing overlay panels. Native popovers and other framework controls may have their own elevation. Preserve that distinction instead of treating “flat” as a prohibition on framework behaviour.

## Shapes

Scientific images are square, unclipped figures. Their axes have no visible surrounding spines. The target outline follows the saved ellipse geometry and is a thin, unfilled annotation. The application does not define a radius scale: buttons, inputs, expanders and form outlines keep Streamlit's native shape language.

## Components

### Buttons

Primary actions apply an experiment, reveal an answer, or open an atlas preset. Reset, save, replay and case navigation use native secondary actions. Sidebar actions and purchase buttons stretch to their available columns where the code specifies it.

Buttons retain Streamlit's native hover, active and disabled styling. Buttons and inputs receive the project's visible teal focus outline (`3px` solid, offset `2px`). Unavailable purchase actions and replay without a selected file are disabled; colour alone does not communicate availability.

### Inputs / Fields

Number inputs, sliders, checkboxes and select boxes keep visible labels and contextual help. Explore groups acquisition controls in a form with an explicit Run action; less frequently changed geometry and reconstruction controls sit in an expander. Public CT groups source selection and simulated acquisition controls in its own form. Its original-image display-window selector sits outside that form and changes only the displayed HU window, without changing the prepared reference or simulated measurements. The project does not override field padding, radius, text size or native error treatment.

### Navigation

Explore, Public CT, Detective and Atlas are choices in a native horizontal radio group. Its selection follows application state, including reopening a saved bundle in the appropriate workspace. Atlas uses another native radio group for presets. These remain controls, not decorative tabs with a separate custom interaction model.

### Scientific Comparison

The recurring signature is an aligned comparison of actual numerical images. The synthetic ground truth or CT prepared reference and their reconstructions use attenuation limits from `0` to `0.6`, nearest-neighbour display and shared physical coordinates. Values outside the displayed limits remain in the underlying arrays and metrics. The known-location gold annotation is drawn consistently over each synthetic target image.

Public CT labels the source image **Original CT slice** and retains a HU colour bar. Its Lung, Soft tissue and Bone display windows use centre/width pairs of `−600/1500`, `40/400` and `300/1500` HU respectively. These are display settings, separate from the fixed preparation used for the simulated projections. The source-axis labels say **Source columns · patient left →** and **Rows increase toward posterior**; a rotated arrow must not substitute for the latter direction statement. Below, **Prepared reference** distinguishes the processed comparison image from anatomical ground truth. Source pixel spacing is stated in millimetres, while the simulation uses a normalised field of view.

Signed error figures share limits from `−0.2` to `+0.2`, with blue for negative error, white at zero and red for positive error. The measured sinogram uses a fixed grayscale and labels the blank unmeasured angular interval. An unmeasured interval must stay visually distinct from a measured zero.

### Evidence, Feedback & Replay

For synthetic targets, the metric table pairs RMSE with known-location target contrast and reference-relative contrast. Explanatory captions keep these distinct from detection probability. Public CT instead reports RMSE against the prepared reference and raster residual RMSE. It has no lesion-recovery score or verified target masks. The nearby information banner distinguishes acquired source images from the simulated projections, and the metric caption states that the shared raster discretisation is not independent scanner validation.

Expanders hold the sinogram, error figures, assumptions and replay details. Public CT adds **Data source, attribution & licence**, containing the 3D Slicer documentation and licensing-clarification links, origin and modification notes, source checksum and licence text. Its export caption states that original pixels, preprocessing, source checksums and the data licence travel with the experiment. Native banners report successful, approximate or differing replay; correct and incorrect guesses receive different semantic feedback.

**The Source and Simulation Rule.** Keep the acquired CT source, its prepared reference and the simulated measurements visibly distinct. Preserve source attribution and licence access beside the experiment, and never imply that a display window changes the numerical experiment.

The reduced-motion media query disables transitions and smooth scrolling. The app adds no ornamental animation.

## Do's and Don'ts

### Do:

- **Do** preserve one action accent and the separate scientific annotation colours.
- **Do** align comparison images and retain their shared numerical display limits.
- **Do** keep units, assumptions and applied settings beside the evidence they explain.
- **Do** label the original HU display separately from the prepared reference and simulated reconstructions.
- **Do** keep source attribution, modification notes and licence access with Public CT experiments.
- **Do** use native control states, visible labels and keyboard focus treatment.
- **Do** let supporting details expand after the main comparison.

### Don't:

- **Don't** auto-normalise each reconstruction image independently.
- **Don't** render missing angular measurements as measured zeros.
- **Don't** style incorrect guesses or differing replay as successful outcomes.
- **Don't** present a known-location contrast measurement as a detection probability.
- **Don't** assign lesion-recovery metrics to Public CT without verified target masks.
- **Don't** present the acquired CT reconstruction as anatomical ground truth or its simulated projections as original scanner measurements.
- **Don't** turn unspecified framework defaults into invented project tokens.

## Student workflow and recorded playback (0.3)

Real CT lab opens first. The other activities are Synthetic practice, Feature challenge and Artifact examples. The top introduction explains CT reconstruction and missing-angle experiments in formal, accessible language for general users. Method names are paired with explanations; preparation and numerical details remain available in expanders. Header and footer retain the owner’s three social links.

The main teaching moment is the original CT image alongside a paused player showing actual correction states. Play/pause, previous/next and a labelled step slider are required. Brightness is fixed; playback speed is not calculation time. Stop playback when hidden or offscreen. The local app calculates new runs; GitHub Pages presents 32 recorded runs with original data and downloads. The public demo uses the existing white, ink and teal palette, a responsive image grid and readable system typography.
