import pytest

from missing_angle.config import ExperimentConfig
from missing_angle.game import Challenge


@pytest.mark.parametrize("field,value", [("views", 0), ("views", True), ("size", 512),
    ("span", 181), ("noise", float("nan")), ("sart_passes", 11), ("seed", -1),
    ("projector", "unknown"), ("present", "yes"), ("rotation", float("inf"))])
def test_invalid_configuration(field, value):
    with pytest.raises(ValueError):
        ExperimentConfig(**{field: value})


def test_unknown_fields_rejected():
    with pytest.raises(ValueError, match="Unknown"):
        ExperimentConfig.from_dict({"viewz": 12})


def test_budget_and_hidden_answer_are_stable():
    case = Challenge()
    for views in (24, 48, 96):
        updated = case.buy(views)
        assert updated.present == case.present
        assert updated.remaining == 96-views
        case = updated
    with pytest.raises(ValueError):
        case.buy(96)
    with pytest.raises(ValueError):
        Challenge().reveal().buy(24)


def test_case_series_contains_present_and_absent_controls():
    assert {Challenge(seed=s).present for s in range(41, 61)} == {False, True}
