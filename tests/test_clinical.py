"""Independent calibration, coordinate and input-integrity checks without ITK."""
from hashlib import sha256
import importlib.util
import io
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clinical', ROOT / 'clinical/reconstruct.py')
clinical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clinical)
replay_spec = importlib.util.spec_from_file_location('clinical_replay', ROOT / 'clinical/verify_run.py')
replay = importlib.util.module_from_spec(replay_spec)
replay_spec.loader.exec_module(replay)


@pytest.mark.parametrize('field', ['origin', 'spacing', 'direction'])
def test_replay_rejects_changed_physical_geometry(field):
    header = {'origin': np.array([-4., -5., -6.]), 'spacing': np.array([1., 2., 3.]),
              'direction': np.eye(3)}
    replay.verify_geometry(header, header)
    changed = {key: value.copy() for key, value in header.items()}
    changed[field].flat[0] += .01
    with pytest.raises(ValueError, match=field):
        replay.verify_geometry(header, changed)
    changed[field].flat[0] = np.nan
    with pytest.raises(ValueError, match=field):
        replay.verify_geometry(header, changed)


def test_detector_counts_are_averaged_before_logarithm():
    raw = np.array([[[1, 3], [5, 7]]], dtype=np.float32)
    binned = clinical.detector_bin(raw, 2)
    np.testing.assert_array_equal(binned, [[[4.]]])
    assert not np.isclose(-np.log(binned / 10).item(), np.mean(-np.log(raw / 10)))
    for invalid in (raw * 0, raw * np.nan, raw[:, :, :1]):
        with pytest.raises(ValueError):
            clinical.detector_bin(invalid, 2)


def test_incident_counts_follow_exposure_ratio_without_reference_fitting():
    r = dict(kvfilter='F1', floodimagefilternorm='35168', tubema='80', tubekvlength='40',
             floodimagefilterma='25', floodimagefilterms='20')
    assert clinical.incident_counts({'RECONSTRUCTION': r}) == 225075.2
    with pytest.raises(ValueError):
        clinical.incident_counts({'RECONSTRUCTION': {**r, 'floodimagefilterma': '0'}})


def test_view_selection_is_unique_spread_and_bounded():
    np.testing.assert_array_equal(clinical.select_indices(356, 89), np.arange(0, 356, 4))
    for views in (0, 357, 89.5):
        with pytest.raises(ValueError):
            clinical.select_indices(356, views)


def test_reference_axis_mapping_uses_documented_landmark_coordinates():
    # Explicit index correspondence for the authors' (1,2,0) array permutation.
    source = np.zeros((3, 4, 5))
    source[0, 1, 2] = 17
    result = clinical.reference_to_rtk(source)
    assert result.shape == (5, 3, 4)
    assert result[2, 2, 1] == 17
    assert np.count_nonzero(result) == 1


def test_reference_resampling_preserves_centres_of_a_linear_physical_field():
    z, y, x = np.indices((8, 8, 8))
    source = 2 * x + 3 * y + 5 * z
    result = clinical.sample_reference(source, (4, 4, 4))
    z, y, x = np.indices((4, 4, 4))
    np.testing.assert_allclose(result, 2 * (2*x + .5) + 3 * (2*y + .5) + 5 * (2*z + .5))


def test_masked_statistics_detect_bias_despite_perfect_correlation():
    reference = np.array([1., 2., 3., 1000.])
    image = np.array([3., 4., 5., -1000.])
    result = clinical.paired(reference, image, np.array([True, True, True, False]))
    assert result['voxels'] == 3 and result['rmse_hu'] == 2 and result['bias_hu'] == 2
    assert result['pearson_r'] == 1 and result['prediction_r2'] < 0


def test_source_verification_fails_before_any_image_parser(tmp_path, monkeypatch):
    original = b'verified data'
    monkeypatch.setattr(clinical, 'MANIFEST', {'files': {'input.mha': {
        'bytes': len(original), 'sha256': sha256(original).hexdigest()}}})
    (tmp_path / 'input.mha').write_bytes(original)
    clinical.verify_files(tmp_path)
    (tmp_path / 'input.mha').write_bytes(b'unverified!!!')
    with pytest.raises(ValueError, match='verification failed'):
        clinical.verify_files(tmp_path)


def test_failed_downloads_leave_no_partial_input(tmp_path, monkeypatch):
    original = b'verified data'
    monkeypatch.setattr(clinical, 'MANIFEST', {'files': {'input.mha': {
        'item': 'fixed-public-item', 'bytes': len(original),
        'sha256': sha256(original).hexdigest()}}})
    for payload in (original + b'excess', original[:-1], b'corrupt data!'):
        monkeypatch.setattr(clinical, 'urlopen', lambda *a, value=payload, **k: io.BytesIO(value))
        with pytest.raises(ValueError):
            clinical.verify_files(tmp_path, download=True)
        assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr(clinical, 'urlopen', lambda *a, **k: io.BytesIO(original))
    clinical.verify_files(tmp_path, download=True)
    assert (tmp_path / 'input.mha').read_bytes() == original
