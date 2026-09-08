from io import BytesIO
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.io import savemat
from missing_angle.live import WEB, import_htc_mat, live_html


def test_measured_inputs_have_hundreds_of_views_and_no_answer_image():
    for key in ('ta', 'tb', 'tc'):
        data = json.loads((WEB / 'projection-data' / f'{key}.json').read_text())
        assert np.asarray(data['sinogram']).shape == (721, 140)
        assert data['angles_deg'] == list(np.arange(0, 360.1, .5))
        assert not {'image', 'reconstruction', 'reference'} & set(data)
        assert data['source']['licence'] == 'CC BY 4.0'


def test_mat_import_preserves_projection_values_and_physical_geometry():
    sino = np.arange(4 * 560).reshape(4, 560) / 100
    data = {'sinogram': sino, 'parameters': {'angles': [0, .5, 1, 1.5],
            'numDetectorsPost': 560, 'distanceSourceOrigin': 410.66,
            'distanceSourceDetector': 553.74, 'pixelSizePost': .2,
            'effectivePixelSizePost': .1483223173330444}}
    file = BytesIO()
    savemat(file, {'CtDataLimited': data})
    loaded = import_htc_mat(file.getvalue())
    np.testing.assert_array_equal(loaded['sinogram'], sino.reshape(4, 140, 4).mean(axis=2))
    assert loaded['geometry']['detector_spacing_mm'] == .8
    assert loaded['geometry']['fov_mm'] == .1483223173330444 * 512
    assert loaded['angles_deg'] == [0, .5, 1, 1.5]
    with pytest.raises(ValueError):
        import_htc_mat(b'x' * (16 * 1024 * 1024 + 1))


def test_local_html_embeds_same_calculator_offline_without_script_injection():
    custom = json.loads((WEB / 'projection-data' / 'ta.json').read_text())
    custom['name'] = '</script><script>alert(1)</script>'
    html = live_html(custom)
    assert '</script><script>alert(1)' not in html
    assert 'window.CT_EMBEDDED_DATA=' in html
    assert 'window.CT_WORKER_CODE=' in html
    assert (WEB / 'projection-core.js').read_text() in html
    assert Path(WEB / 'live.js').read_text() in html
