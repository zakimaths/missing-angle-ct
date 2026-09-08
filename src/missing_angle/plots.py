"""Scientific figures use shared physical coordinates and fixed display scales."""
from io import BytesIO

from matplotlib.figure import Figure
from matplotlib.patches import Ellipse as EllipsePatch
import numpy as np

INK = "#172F3A"
TEAL = "#007F87"


def _png(figure):
    output = BytesIO()
    figure.savefig(output, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    return output.getvalue()


def image_figure(experiment, method, error=False, mark=False):
    image = experiment.arrays[method]
    if error:
        image = image - experiment.arrays["phantom"]
    n = experiment.config.size
    h = 2/n
    fig = Figure(figsize=(4, 4))
    ax = fig.subplots()
    ax.imshow(image, origin="upper", extent=(-1-h/2, 1-h/2, -1+h/2, 1+h/2),
              cmap="RdBu_r" if error else "gray", vmin=-.2 if error else 0,
              vmax=.2 if error else .6, interpolation="nearest")
    if mark:
        feature = experiment.geometry["feature_template"]
        ax.add_patch(EllipsePatch((feature["x"], feature["y"]), 2*feature["a"]+.035,
                                  2*feature["b"]+.035, angle=feature["angle"],
                                  fill=False, edgecolor="#F0B95C", linewidth=1))
    ax.set_xticks([-.5, 0, .5])
    ax.set_yticks([-.5, 0, .5])
    ax.tick_params(labelsize=9, colors=INK, length=2)
    ax.set_xlabel("x · physical units", fontsize=9, color=INK)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return _png(fig)


def sinogram_figure(experiment):
    c = experiment.config
    fig = Figure(figsize=(9, 3.2))
    ax = fig.subplots()
    h = 2/c.size
    # Horizontal cells show acquisition indices on an unwrapped angular axis.
    im = ax.imshow(experiment.arrays["measured"], origin="lower", aspect="auto",
                   extent=(c.rotation, c.rotation+c.span, -1-h/2, 1-h/2),
                   cmap="gray", vmin=0, vmax=.6, interpolation="nearest")
    ax.set_xlim(c.rotation, c.rotation+180)
    ax.set_facecolor("#EDF2F2")
    if c.span < 180:
        ax.text(c.rotation+(c.span+180)/2, 0, "Unmeasured", ha="center", color=INK,
                fontsize=10, rotation=90 if c.span > 140 else 0)
    ticks = np.linspace(c.rotation, c.rotation+180, 7)
    ax.set_xticks(ticks, [f"{t % 180:g}°" for t in ticks])
    ax.set_xlabel("Detector-normal angle · each cell begins at its measured angle", fontsize=9)
    ax.set_ylabel("Detector position", fontsize=9)
    ax.tick_params(labelsize=9)
    fig.colorbar(im, ax=ax, label="Line integral", fraction=.025, pad=.02)
    return _png(fig)


def ct_source_figure(hu, window):
    """Display only: CT windows never enter preprocessing or projection."""
    from .public_ct import WINDOWS
    centre, width = WINDOWS[window]
    fig = Figure(figsize=(5, 4.5))
    ax = fig.subplots()
    im = ax.imshow(hu, cmap="gray", origin="upper", interpolation="nearest",
                   vmin=centre-width/2, vmax=centre+width/2)
    ax.set_xlabel("Source columns · patient left →", fontsize=9)
    ax.set_ylabel("Rows increase toward posterior", fontsize=9)
    ax.tick_params(labelsize=8)
    fig.colorbar(im, ax=ax, label="Hounsfield units", fraction=.04, pad=.025)
    return _png(fig)
