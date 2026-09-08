"""Check every published experiment, image path and final animation frame."""
from pathlib import Path
import json

import numpy as np
from PIL import Image

from missing_angle.bundle import load_bundle, verify_replay

root = Path('demo')
cases = json.loads((root / 'experiments.json').read_text())['experiments']
assert len(cases) == 32
assert len({case['key'] for case in cases}) == 32
assert all(len(c['frames']) == len(c['frame_labels']) and len(c['frames']) > 11 for c in cases)
for case in cases:
    for path in case['frames']:
        assert (root / path).is_file()
    folder = root / case['folder']
    assert np.array_equal(np.asarray(Image.open(root / case['frames'][-1])),
                          np.asarray(Image.open(folder / 'regularized.png')))
    exp, manifest = load_bundle((folder / 'experiment.zip').read_bytes())
    assert manifest['id'] == case['id']
    assert manifest['schema'] == 'missing-angle/4'
    for method in ('fbp', 'sart', 'regularized'):
        assert (folder / f'{method}-error.png').is_file()
        assert (folder / f'{method}-error-detail.png').is_file()
    assert exp.geometry['source']['slice']['index'] == case['slice']
    assert exp.metrics['methods'] == case['metrics']
    if case['slice'] == 80:
        assert all(c['within_tolerance'] for c in verify_replay(exp)['checks'].values())
print('32 demo bundles validated; image paths and final frames match; four representative runs replayed.')

for key in ('ta', 'tb', 'tc'):
    data = json.loads((root / 'projection-data' / f'{key}.json').read_text())
    assert np.asarray(data['sinogram']).shape == (721, 140)
    assert 'image' not in data and 'reference' not in data
for filename in ('live.js', 'live.css', 'study.js', 'projection-core.js', 'projection-worker.js'):
    assert (root / filename).read_bytes() == (Path('src/missing_angle/web') / filename).read_bytes()
assert (Path('src/missing_angle/web/live-panel.html').read_text()) in (root / 'index.html').read_text()
print('Live calculator code matches packaged source; three acquired 721-view inputs contain no reconstruction image.')

for key in ("ta", "tb", "tc"):
    assert (root / "reference-data" / f"{key}.json").read_bytes() == (Path("src/missing_angle/web/reference-data") / f"{key}.json").read_bytes()
