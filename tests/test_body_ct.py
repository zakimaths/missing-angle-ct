"""Independent forward calibration and original body-data integrity checks."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare_body_ct', ROOT / 'scripts/prepare_body_ct.py')
body = importlib.util.module_from_spec(spec)
spec.loader.exec_module(body)


def test_body_projector_matches_off_centre_gaussian_in_physical_units():
    # Analytic Radon transform of a shifted Gaussian checks scale, angles and handedness.
    spacing = (.7, .7)
    axis = (np.arange(257) - 128) * spacing[0]
    x, y = axis[None, :], -axis[:, None]
    mu = .02 * np.exp(-((x - 12)**2 + (y + 9)**2) / (2 * 8**2))
    angles = np.array([0, 30, 90, 150])
    got = body.project(mu, spacing, angles, 180, detectors=121)
    u = (np.arange(121) - 60) * 180 / 121
    centre = 12 * np.cos(np.deg2rad(angles)) - 9 * np.sin(np.deg2rad(angles))
    expected = .02 * np.sqrt(2 * np.pi) * 8 * np.exp(-(u[None, :] - centre[:, None])**2 / 128)
    np.testing.assert_allclose(got, expected, atol=.0006, rtol=0)


def test_body_sources_are_verified_real_hu_slices_and_projections_have_no_answer():
    meta = json.loads((body.DATA / 'ct-abdomen.json').read_text())
    assert meta['source_sha256'] == body.LIVER_HASH
    assert meta['licence'] == 'CC BY-SA 4.0'
    for entry in meta['slices']:
        raw = body.DATA / entry['file']
        assert sha256(raw.read_bytes()).hexdigest() == entry['sha256']
        hu = np.load(raw, allow_pickle=False)
        assert hu.shape == (512, 512) and hu.dtype == np.dtype('<f4')
        assert np.isfinite(hu).all() and hu.min() < -900 and hu.max() > 500
    for key in ('chest-64', 'chest-96', 'abdomen-400', 'abdomen-480'):
        d = json.loads((body.WEB / 'projection-data' / f'{key}.json').read_text())
        r = json.loads((body.WEB / 'reference-data' / f'{key}.json').read_text())
        assert d['kind'] == 'body_ct_simulated'
        assert np.asarray(d['sinogram']).shape == (360, 192)
        assert d['angles_deg'] == (np.arange(360) / 2).tolist()
        assert not {'image', 'reference', 'reconstruction', 'preview'} & set(d)
        assert r['kind'] == 'body_ct_source' and r['units'] == '1/mm'
        assert r['source'] == d['source']
        assert r['fov_mm'] == d['geometry']['fov_mm']
        assert len(r['preview']['image']) == 256**2
