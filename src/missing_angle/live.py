"""Local embedding and bounded import of acquired projection data."""
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

WEB = Path(__file__).parent / 'web'
MAX_INPUT = 16 * 1024 * 1024


def import_htc_mat(raw):
    """Read the documented HTC structure, not arbitrary scanner/raw-image formats."""
    if len(raw) > MAX_INPUT:
        raise ValueError('The MATLAB file exceeds the 16 MB input limit.')
    data = loadmat(BytesIO(raw), simplify_cells=True)
    scan = data.get('CtDataFull', data.get('CtDataLimited'))
    if not isinstance(scan, dict) or 'parameters' not in scan:
        raise ValueError('Expected HTC2022 CtDataFull or CtDataLimited with scanner parameters.')
    p = scan['parameters']
    measured = np.asarray(scan['sinogram'], dtype=float)
    angles = np.asarray(p['angles'], dtype=float).reshape(-1)
    if measured.ndim != 2 or measured.shape[0] != len(angles) or not 4 <= len(angles) <= 1440:
        raise ValueError('Expected 4–1440 views, one sinogram row per angle.')
    if measured.shape[1] != int(p['numDetectorsPost']):
        raise ValueError('Detector count does not match the scanner metadata.')
    if not np.isfinite(measured).all() or not np.isfinite(angles).all():
        raise ValueError('Projection data contains non-finite values.')
    factor = 4 if measured.shape[1] == 560 else 1
    measured = measured.reshape(len(angles), -1, factor).mean(axis=2)
    if not 16 <= measured.shape[1] <= 512 or np.max(np.abs(measured)) > 100:
        raise ValueError('Unsupported detector count or line-integral range.')
    return {'schema': 'ct-projections/1', 'name': 'Imported HTC measurements', 'kind': 'measured',
            'angles_deg': angles.tolist(), 'sinogram': measured.tolist(),
            'geometry': {'type': 'fan', 'source_distance_mm': float(p['distanceSourceOrigin']),
                         'detector_distance_mm': float(p['distanceSourceDetector'] - p['distanceSourceOrigin']),
                         'detector_spacing_mm': float(p['pixelSizePost']) * factor,
                         'fov_mm': float(p['effectivePixelSizePost']) * 512},
            'source': {'preparation': f'HTC central-plane measurements; mean of {factor} adjacent log-transformed detector bins. All supplied angles preserved.'}}


def live_html(custom=None):
    inputs = {key: json.loads((WEB / 'projection-data' / f'{key}.json').read_text())
              for key in ('ta', 'tb', 'tc')}
    panel = (WEB / 'live-panel.html').read_text()
    if custom is not None:
        inputs['ta'] = custom
        panel = panel.replace('Helsinki object A · 721 measured views', 'Imported HTC measurements')
    worker = (WEB / 'projection-core.js').read_text() + '\n' + (WEB / 'projection-worker.js').read_text()
    # Escape HTML-significant characters in data and code embedded in script strings.
    def script_json(value):
        return json.dumps(value, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{margin:0;background:white}'+(WEB/'live.css').read_text()+'</style></head><body>'
            + panel + '<script>window.CT_EMBEDDED_DATA='+script_json(inputs)+';window.CT_WORKER_CODE='
            + script_json(worker) + ';</script><script>'+(WEB/'projection-core.js').read_text()
            + '</script><script>'+(WEB/'live.js').read_text()+'</script></body></html>')
