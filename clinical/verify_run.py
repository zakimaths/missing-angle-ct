"""Verify an offline repeat against a completed clinical reconstruction."""
import argparse
import json
from pathlib import Path

import numpy as np


def verify_geometry(first, repeated):
    """Compare physical headers, independently of report metadata and voxel values."""
    for name in ('origin', 'spacing', 'direction'):
        a, b = np.asarray(first[name]), np.asarray(repeated[name])
        if (a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all()
                or not np.allclose(a, b, rtol=0, atol=1e-8)):
            raise ValueError(f'Volume physical {name} differs')


def verify(first, repeated, check_reference=False):
    import itk

    baseline = json.loads((first / 'report.json').read_text())
    replay = json.loads((repeated / 'report.json').read_text())
    if not replay.get('results'):
        raise ValueError('Replay contains no calculated results')
    for key in ('algorithm', 'source_sha256', 'settings', 'packages'):
        if baseline[key] != replay[key]:
            raise ValueError(f'Replay configuration differs: {key}')
    results = []
    for row in replay['results']:
        views = row['views']
        original = next((r for r in baseline['results'] if r['views'] == views), None)
        if original is None or row['selected_indices'] != original['selected_indices']:
            raise ValueError('Replay has different view selections')
        if check_reference and views == 356:
            # Regression bounds for this pinned case at the tested 64/96 grids and binning 2.
            # These are not clinical acceptance criteria.
            if (replay['settings']['size_xyz'][0] not in (64, 96)
                    or replay['settings']['detector_binning'] != 2):
                raise ValueError('Reference regression bounds require the tested configuration')
            if row['rmse_hu'] >= 25 or row['pearson_r'] is None or row['pearson_r'] <= .995:
                raise ValueError('Full-data reconstruction failed the reference regression bounds')
        original_image = itk.imread(str(first / f'reconstruction-{views}.mha'))
        repeated_image = itk.imread(str(repeated / f'reconstruction-{views}.mha'))

        def header(image):
            return {'origin': tuple(image.GetOrigin()), 'spacing': tuple(image.GetSpacing()),
                    'direction': itk.array_from_matrix(image.GetDirection())}

        verify_geometry(header(original_image), header(repeated_image))
        a = itk.array_from_image(original_image)
        b = itk.array_from_image(repeated_image)
        if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError('Invalid reconstruction volume')
        difference = float(np.max(np.abs(a - b)))
        # Float32 FDK volumes are compared in attenuation units, before HU conversion.
        if difference > 1e-6:
            raise ValueError(f'Volume differs by {difference}, tolerance 1e-6')
        results.append({'views': views, 'maximum_absolute_difference': difference,
                        'tolerance': 1e-6, 'physical_geometry_matched': True,
                        'geometry_tolerance': 1e-8, 'matched': True})
    value = {'schema': 'ct-clinical-replay/1', 'results': results}
    (repeated / 'replay.json').write_text(json.dumps(value, indent=2) + '\n')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('repeated', type=Path)
    parser.add_argument('--check-reference', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.first, args.repeated, args.check_reference), indent=2))
