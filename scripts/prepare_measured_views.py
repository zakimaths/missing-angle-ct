"""Extract measured HTC2022 rays; no reconstruction images enter the live solver."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import zipfile
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'data-cache/htc2022_teaching_data.zip'
raw = source.read_bytes()
assert hashlib.md5(raw).hexdigest() == '185a0ad518e4c6cd9c4153f6060ef327'
archive = zipfile.ZipFile(BytesIO(raw))
destination = ROOT / 'src/missing_angle/web/projection-data'
destination.mkdir(exist_ok=True, parents=True)
for key in ('ta', 'tb', 'tc'):
    member = f'htc2022_teaching_data/htc2022_{key}_full.mat'
    original = archive.read(member)
    data = loadmat(BytesIO(original), simplify_cells=True)['CtDataFull']
    params = data['parameters']
    # Average four neighbouring, already log-transformed detector readings.
    # Preserve all 721 measured angles, including the repeated end orientation.
    measured = data['sinogram'].reshape(721, 140, 4).mean(axis=2)
    result = {'schema': 'ct-projections/1', 'name': f'Helsinki test object {key.upper()}',
              'kind': 'measured', 'angles_deg': params['angles'].tolist(),
              'sinogram': np.round(measured, 8).tolist(),
              'geometry': {'type': 'fan', 'source_distance_mm': float(params['distanceSourceOrigin']),
                           'detector_distance_mm': float(params['distanceSourceDetector'] - params['distanceSourceOrigin']),
                           'detector_spacing_mm': float(params['pixelSizePost'] * 4),
                           'fov_mm': float(params['effectivePixelSizePost'] * 512)},
              'source': {'url': 'https://zenodo.org/records/8041800', 'doi': '10.5281/zenodo.8041800',
                         'licence': 'CC BY 4.0', 'attribution': 'Alexander Meaney, Fernando Silva de Moura, Markus Juvonen and Samuli Siltanen (2023), HTC2022 v1.4.0.',
                         'sha256': hashlib.sha256(original).hexdigest(), 'archive_sha256': hashlib.sha256(raw).hexdigest(),
                         'preparation': 'All 721 acquired angles preserved; 560 detector bins averaged in groups of four to 140. Input is already corrected and log-transformed. 2D central-plane approximation of cone-beam acquisition. No reference reconstruction included.'}}
    path = destination / f'{key}.json'
    path.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(key, measured.shape, 'range', measured.min(), measured.max(), 'bytes', path.stat().st_size)
