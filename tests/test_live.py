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
    assert Path(WEB / 'live.js').read_text().replace("load('ta');", "load('custom');") in html
    assert 'window.CT_EMBEDDED_REFERENCES=' in html
    assert Path(WEB / 'study.js').read_text() in html


def test_mat_import_bounds_compression_before_scipy(monkeypatch):
    import struct
    import zlib
    import missing_angle.live as live
    header = b'MATLAB 5.0 MAT-file'.ljust(124, b' ') + b'\x00\x01IM'
    compressed = zlib.compress(b'x' * 4097)
    raw = header + struct.pack('<II', 15, len(compressed)) + compressed
    monkeypatch.setattr(live, 'MAX_EXPANDED', 4096)
    monkeypatch.setattr(live, 'loadmat', lambda *a, **k: pytest.fail('Unsafe data reached SciPy'))
    with pytest.raises(ValueError, match='Expanded MATLAB'):
        live.import_htc_mat(raw)


def test_mat_preflight_rejects_forged_dimensions_before_loading(monkeypatch):
    import struct
    import missing_angle.live as live
    buf = BytesIO()
    savemat(buf, {'x': np.ones((2, 3))})
    raw = bytearray(buf.getvalue())
    # Top-level miMATRIX tag, eight-byte array flags, then dimensions tag/data.
    struct.pack_into('<ii', raw, 160, 2_000_000, 2_000_000)
    monkeypatch.setattr(live, 'loadmat', lambda *a, **k: pytest.fail('Unsafe dimensions reached SciPy'))
    with pytest.raises(ValueError, match='dimensions exceed'):
        live.import_htc_mat(raw)


def test_mat_compressed_and_uncompressed_imports_match():
    from missing_angle.live import _bounded_mat
    d = {'CtDataFull': {'sinogram': np.ones((4, 32)), 'parameters': {
        'angles': [0, 30, 60, 90], 'numDetectorsPost': 32,
        'distanceSourceOrigin': 410.66, 'distanceSourceDetector': 553.74,
        'pixelSizePost': .8, 'effectivePixelSizePost': .1483223173330444}}}
    results = []
    for compressed in (False, True):
        buf = BytesIO()
        savemat(buf, d, do_compression=compressed)
        results.append(import_htc_mat(buf.getvalue()))
        with pytest.raises(ValueError):
            _bounded_mat(buf.getvalue()[:-9])
    assert results[0] == results[1]


def test_mat_preflight_rejects_short_payload_and_objects():
    from missing_angle.live import _bounded_mat
    import struct
    buf = BytesIO()
    savemat(buf, {'x': np.ones((2, 3))})
    raw = bytearray(buf.getvalue())
    struct.pack_into('<ii', raw, 160, 2, 4)
    with pytest.raises(ValueError, match='payload'):
        _bounded_mat(raw)
    struct.pack_into('<I', raw, 144, 3)
    with pytest.raises(ValueError, match='objects'):
        _bounded_mat(raw)


def test_mat_preflight_accepts_compact_storage_of_declared_doubles():
    import struct
    from scipy.io import loadmat
    from missing_angle.live import _bounded_mat
    buf = BytesIO()
    savemat(buf, {'x': np.ones((2, 3))})
    raw = bytearray(buf.getvalue()[:176])
    raw.extend(struct.pack('<II', 2, 6) + bytes([1] * 6) + b'\0\0')
    struct.pack_into('<I', raw, 132, len(raw) - 136)
    decoded = loadmat(BytesIO(_bounded_mat(raw)))
    np.testing.assert_array_equal(decoded['x'], np.ones((2, 3)))
