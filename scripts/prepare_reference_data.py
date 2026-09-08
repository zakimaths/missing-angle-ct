"""Publish separately stored evaluation references from the pinned test oracle.

The oracle records original HTC FBP member hashes, unit conversion and resizing.
These files are served to the evaluation UI only, never to the solver worker.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
web = root / 'src/missing_angle/web'
oracle = json.loads((root / 'tests/fixtures/htc_reference.json').read_text())
for key in ('ta', 'tb', 'tc'):
    data = json.loads((web / 'projection-data' / f'{key}.json').read_text())
    source = {**oracle['source'], 'sha256': oracle[key]['source_sha256']}
    source['preparation'] = source['preparation'].replace(
        'Test oracle only; never supplied to live reconstruction.',
        'Comparison only; never supplied to the reconstruction worker.')
    reference = {'schema': 'ct-reference/1',
                 'name': f'Authors full-scan FBP · Helsinki object {key.upper()}',
                 'kind': 'measured-reference', 'size': 96,
                 'fov_mm': data['geometry']['fov_mm'], 'units': '1/mm',
                 'orientation': 'row-major-top-left', 'image': oracle[key]['reference'],
                 'source': source}
    (web / 'reference-data' / f'{key}.json').write_text(
        json.dumps(reference, separators=(',', ':')) + '\n')
