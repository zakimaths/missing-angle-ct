from dataclasses import replace
from io import BytesIO
import zipfile

import numpy as np
import pytest

from missing_angle.bundle import export_bundle, load_bundle, verify_replay
from missing_angle.config import ExperimentConfig
from missing_angle.public_ct import run_public_ct
from missing_angle.refinement import refine, settings, iteration_history


def test_history_is_actual_calculation_and_replays_all_states():
    exp = run_public_ct(48, ExperimentConfig(size=64, views=24, noise=.006))
    enhanced = refine(exp, passes=4, weight=.002)
    assert enhanced.arrays['history'].shape == (5, 64, 64)
    assert not enhanced.arrays['history'][0].any()
    np.testing.assert_array_equal(enhanced.arrays['regularized'], enhanced.arrays['history'][-1])
    for passes in (1, 2, 3):
        partial = iteration_history(exp.arrays['measured'], exp.arrays['theta'], 64, settings(passes, .002))
        np.testing.assert_array_equal(partial[-1], enhanced.arrays['history'][passes])
    loaded, manifest = load_bundle(export_bundle(enhanced))
    assert manifest['schema'] == 'missing-angle/3'
    assert set(verify_replay(loaded)['checks']) == {'fbp', 'sart', 'regularized', 'history'}
    assert all(v['exact'] for v in verify_replay(loaded)['checks'].values())


def test_solver_does_not_use_reference_or_clean_measurements():
    exp = run_public_ct(80, ExperimentConfig(size=64, views=24, noise=.006))
    other = replace(exp, arrays={**exp.arrays, 'phantom': np.ones((64,64)), 'clean': np.zeros_like(exp.arrays['clean'])})
    a, b = refine(exp, 3), refine(other, 3)
    np.testing.assert_array_equal(a.arrays['regularized'], b.arrays['regularized'])
    np.testing.assert_array_equal(a.arrays['measured'], exp.arrays['measured'])
    np.testing.assert_array_equal(a.arrays['source_hu'], exp.arrays['source_hu'])
    assert a.metrics['methods']['regularized']['roi_contrast'] is None


def test_no_smoothing_matches_nonnegative_sart_at_equal_passes():
    exp = run_public_ct(64, ExperimentConfig(size=64, views=24, sart_passes=4, nonnegative=True))
    result = refine(exp, 4, 0)
    np.testing.assert_array_equal(result.arrays['regularized'], exp.arrays['sart'])


@pytest.mark.parametrize('passes,weight', [(0,.002),(21,.002),(True,.002),(2,-1),(2,float('nan'))])
def test_refinement_settings_are_bounded(passes, weight):
    with pytest.raises(ValueError):
        settings(passes, weight)


def test_missing_history_and_invalid_final_frame_are_rejected():
    exp = refine(run_public_ct(80, ExperimentConfig(size=64, views=12)), 2)
    exp.arrays['history'][-1] += .1
    with pytest.raises(ValueError, match='history'):
        load_bundle(export_bundle(exp))
    good = export_bundle(refine(run_public_ct(80, ExperimentConfig(size=64, views=12)), 2))
    output = BytesIO()
    with zipfile.ZipFile(BytesIO(good)) as archive, zipfile.ZipFile(output, 'w') as altered:
        for item in archive.infolist():
            if item.filename != 'arrays/history.npy':
                altered.writestr(item, archive.read(item.filename))
    with pytest.raises(ValueError):
        load_bundle(output.getvalue())
