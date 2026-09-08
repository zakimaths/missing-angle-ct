from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).parents[1] / "app" / "main.py"


def test_explore_apply_reset_and_atlas():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    at.radio(key="mode").set_value("Explore").run()
    at.number_input(key="c_views").set_value(24)
    next(b for b in at.button if b.label == "Run experiment").click().run()
    assert not at.exception
    assert at.session_state["experiment"].config.views == 24
    at.radio(key="mode").set_value("Atlas").run()
    assert not at.exception
    at.radio(key="atlas_preset").set_value("Missing angles").run()
    next(b for b in at.button if b.label == "Try these settings in practice").click().run()
    assert not at.exception
    assert at.session_state["experiment"].config.span == 90
    assert at.slider(key="c_span").value == 90
    next(b for b in at.button if b.label == "Reset to baseline").click().run()
    assert at.session_state["experiment"].config.views == 48


def test_detective_purchase_reveal_and_reset():
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    at.radio(key="mode").set_value("Detective").run()
    assert not at.exception
    assert not any("Known answer:" in s.value for s in at.success)
    at.button(key="buy_48").click().run()
    assert at.session_state["challenge"].views == 48
    assert at.session_state["challenge"].remaining == 48
    next(b for b in at.button if b.label == "Reveal ground truth").click().run()
    assert not at.session_state["challenge"].revealed
    assert len(at.warning) == 1
    at.radio(key="guess").set_value("Present")
    at.radio(key="confidence").set_value("Medium")
    next(b for b in at.button if b.label == "Reveal ground truth").click().run()
    assert not at.exception
    assert at.session_state["challenge"].revealed
    assert at.button(key="buy_96").disabled
    next(b for b in at.button if b.label == "Start next case").click().run()
    assert at.session_state["challenge"].views == 12
    assert not at.session_state["challenge"].revealed
    assert at.radio(key="guess").value is None
    at.radio(key="mode").set_value("Explore").run()
    assert not at.exception
    assert at.number_input(key="c_views").value == at.session_state["experiment"].config.views
