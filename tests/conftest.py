"""Prepare plotting resources before timed Streamlit interactions."""

import pytest


@pytest.fixture(scope="session", autouse=True)
def prepare_plotting_fonts():
    # A fresh Intel runner can spend over 30 seconds indexing system fonts.
    # Keep this one-time setup outside AppTest's widget-response deadline.
    import matplotlib.font_manager  # noqa: F401
