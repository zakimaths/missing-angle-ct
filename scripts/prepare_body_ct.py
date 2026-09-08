"""Prepare real CT slices and independent parallel-ray simulations for the live lab.

Run with --liver-volume PATH once to extract the checksum-pinned public volume.
Subsequent runs use the verified bundled slices, without a network connection.
"""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates
from skimage.transform import resize

from missing_angle.public_ct import load_slice

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/missing_angle/data'
WEB = ROOT / 'src/missing_angle/web'
LIVER_HASH = 'e16eae0ae6fefa858c5c11e58f0f1bb81834d81b7102e021571056324ef6f37e'
LIVER_URL = 'https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/' + LIVER_HASH
SOURCE_LIST = 'https://github.com/Slicer/Slicer/blob/main/Modules/Scripted/SampleData/SampleData.py'


def write_json(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'), sort_keys=True) + '\n')


def extract_liver(path):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != LIVER_HASH:
        raise ValueError('Abdominal CT source checksum mismatch')
    header, payload = raw.split(b'\n\n', 1)
    fields = dict(line.split(': ', 1) for line in header.decode().splitlines()
                  if ': ' in line and not line.startswith('#'))
    assert fields['type'] == 'float' and fields['sizes'] == '512 512 685'
    assert fields['encoding'] == 'gzip' and fields['endian'] == 'little'
    assert fields['space'] == 'left-posterior-superior'
    assert fields['space directions'].startswith('(-0.69921875,0,0) (0,-0.69921875,0)')
    volume = np.frombuffer(gzip.decompress(payload), dtype='<f4').reshape(685, 512, 512)
    meta = {'source_url': LIVER_URL, 'source_sha256': LIVER_HASH,
            'original_shape_zyx': [685, 512, 512], 'pixel_spacing_yx_mm': [.69921875] * 2,
            'title': 'Medical Segmentation Decathlon liver CT, distributed by 3D Slicer',
            'original_case': 'Task03_Liver / imagesTr / liver_100', 'units': 'HU',
            'licence': 'CC BY-SA 4.0', 'licence_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'attribution_url': SOURCE_LIST,
            'orientation': 'Rows and columns reversed from source: columns increase patient left; rows increase posterior.',
            'modification': 'Two axial slices retained as float32 HU; both in-plane axes reversed.',
            'slices': []}
    for index in (400, 480):
        filename = f'ct-abdomen-{index}.npy'
        np.save(DATA / filename, volume[index, ::-1, ::-1].astype('<f4'), allow_pickle=False)
        meta['slices'].append({'index': index, 'file': filename,
                               'sha256': sha256((DATA / filename).read_bytes()).hexdigest()})
    write_json(DATA / 'ct-abdomen.json', meta)


def sample_physical(mu, spacing, x, y):
    """Bilinear source sampling; x rightward and y upward, in millimetres."""
    row = (mu.shape[0] - 1) / 2 - y / spacing[0]
    col = (mu.shape[1] - 1) / 2 + x / spacing[1]
    row, col = np.broadcast_arrays(row, col)
    return map_coordinates(mu, [row, col], order=1, mode='grid-constant', cval=0,
                           prefilter=False)


def project(mu, spacing, angles, fov, detectors=192, step=None):
    """Midpoint quadrature on the source grid, independent of solver pixel rays."""
    steps = int(np.ceil(fov * np.sqrt(2) / (step or min(spacing) / 2)))
    dt = fov * np.sqrt(2) / steps
    t = ((np.arange(steps) + .5) * dt - fov / np.sqrt(2))[None, :]
    u = ((np.arange(detectors) - (detectors - 1) / 2) * fov / detectors)[:, None]
    sino = []
    for angle in angles:
        a = np.deg2rad(angle)
        x, y = u * np.cos(a) - t * np.sin(a), u * np.sin(a) + t * np.cos(a)
        sino.append(sample_physical(mu, spacing, x, y).sum(axis=1) * dt)
    return np.asarray(sino)


def prepare(key, title, hu, spacing, source, window):
    if hu.shape != (512, 512) or not np.isfinite(hu).all():
        raise ValueError('Expected a finite 512 by 512 HU slice')
    mu = .02 * np.clip(1 + hu.astype(np.float64) / 1000, 0, 3)
    fov = float(np.ceil(np.linalg.norm(np.asarray(hu.shape) * spacing) * 1.02))
    angles = np.arange(360) / 2
    sino = project(mu, spacing, angles, fov)
    # Reference pixels average 4 x 4 samples, separately from all projection calculations.
    n = 128
    axis = (np.arange(n * 4) + .5) * fov / (n * 4) - fov / 2
    ref = sample_physical(mu, spacing, axis[None, :], -axis[:, None])
    ref = ref.reshape(n, 4, n, 4).mean(axis=(1, 3))
    preview = resize(hu, (256, 256), preserve_range=True, anti_aliasing=True)
    preview = np.rint(np.clip((preview - window[0] + window[1] / 2) / window[1], 0, 1) * 255)
    source = {**source, 'preparation_version': 'body-ct-parallel-v1',
              'preparation': 'Real CT image; simulated noiseless parallel projections. Original scanner projections are unavailable.',
              'attenuation_mapping': '0.02 * clip(1 + HU/1000, 0, 3) /mm; illustrative water scale, not energy-calibrated.',
              'projection_integration': 'Bilinear source-grid sampling with midpoint quadrature at <= half source pixel pitch.',
              'reference_sampling': '128 by 128 pixels, 4 by 4 subpixel averaging; same physical field of view.',
              'pixel_spacing_yx_mm': list(spacing)}
    write_json(WEB / 'projection-data' / f'{key}.json', {
        'schema': 'ct-projections/1', 'name': title, 'kind': 'body_ct_simulated',
        'angles_deg': angles.tolist(), 'sinogram': np.round(sino, 8).tolist(),
        'geometry': {'type': 'parallel', 'fov_mm': fov, 'detector_spacing_mm': fov / 192},
        'source': source})
    write_json(WEB / 'reference-data' / f'{key}.json', {
        'schema': 'ct-reference/1', 'name': title + ' · source CT reference',
        'kind': 'body_ct_source', 'size': n, 'image': np.round(ref.ravel(), 10).tolist(),
        'fov_mm': fov, 'units': '1/mm', 'orientation': 'row-major-top-left', 'source': source,
        'preview': {'size': 256, 'image': preview.astype(int).ravel().tolist(),
                    'window_center_hu': window[0], 'window_width_hu': window[1]}})
    print(f'Prepared {key}: 360 views, 192 detectors, {fov:g} mm field of view')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--liver-volume', type=Path)
    args = parser.parse_args()
    if args.liver_volume:
        extract_liver(args.liver_volume)
    for index in (64, 96):
        hu, source = load_slice(index)
        prepare(f'chest-{index}', f'Chest CT · slice {index}', hu,
                source['pixel_spacing_yx_mm'], source, (-600, 1500))
    meta = json.loads((DATA / 'ct-abdomen.json').read_text())
    for entry in meta['slices']:
        path = DATA / entry['file']
        if sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Bundled abdominal CT slice checksum mismatch')
        source = {k: v for k, v in meta.items() if k != 'slices'}
        source['slice'] = entry
        prepare(f'abdomen-{entry["index"]}', f'Abdominal CT · slice {entry["index"]}',
                np.load(path, allow_pickle=False), meta['pixel_spacing_yx_mm'], source, (40, 400))


if __name__ == '__main__':
    main()
