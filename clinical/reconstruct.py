# SPDX-License-Identifier: Apache-2.0
"""Reconstruct the pinned COBRA2026 A002 acquisition on the CPU.

This deliberately supports one verified case, not arbitrary clinical files.
The reference is loaded only after all FDK reconstructions are complete.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tempfile
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import numpy as np

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / 'case.json').read_text())
ALGORITHM = 'cobra-a002-cpu-fdk-1'


def digest(path):
    h = sha256()
    with path.open('rb') as source:
        while chunk := source.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def verify_files(directory, download=False):
    """Only the fixed public manifest can supply paths, URLs and byte limits."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, spec in MANIFEST['files'].items():
        target = directory / name
        if not target.exists() and download:
            url = ('https://tomoradio-warehouse.creatis.insa-lyon.fr/api/v1/item/'
                   + spec['item'] + '/download')
            print(f'Downloading {name} ({spec["bytes"] / 1e6:.1f} MB)', flush=True)
            # Atomic replacement prevents a failed transfer from appearing complete.
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as out:
                temporary = Path(out.name)
                try:
                    total = 0
                    with urlopen(url, timeout=60) as source:
                        while chunk := source.read(1024 * 1024):
                            total += len(chunk)
                            if total > spec['bytes']:
                                raise ValueError('Download exceeds the pinned byte count')
                            out.write(chunk)
                    out.flush()
                    if total != spec['bytes'] or digest(temporary) != spec['sha256']:
                        raise ValueError(f'Checksum mismatch: {name}')
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)
        if not target.exists():
            raise ValueError('Missing case files. Use --download once, then repeat offline.')
        if target.stat().st_size != spec['bytes'] or digest(target) != spec['sha256']:
            raise ValueError(f'Pinned source verification failed: {name}')


def detector_bin(raw, factor):
    """Average counts before the logarithm, preserving detector physical centres."""
    if factor not in (1, 2, 4) or raw.ndim != 3:
        raise ValueError('Detector binning must be 1, 2 or 4')
    views, rows, cols = raw.shape
    if rows % factor or cols % factor or not np.isfinite(raw).all() or np.min(raw) <= 0:
        raise ValueError('Expected positive finite counts and divisible detector dimensions')
    return raw.reshape(views, rows // factor, factor, cols // factor, factor).mean(
        axis=(2, 4), dtype=np.float32)


def incident_counts(config):
    """Elekta flood-field exposure normalisation used by the dataset authors."""
    r = config['RECONSTRUCTION']
    if r['kvfilter'] != 'F1':
        raise ValueError('This pinned acquisition requires the F1 flood calibration')
    values = [float(r[k]) for k in ('floodimagefilternorm', 'tubema', 'tubekvlength',
                                   'floodimagefilterma', 'floodimagefilterms')]
    if not all(np.isfinite(v) and v > 0 for v in values):
        raise ValueError('Invalid exposure calibration')
    norm, ma, ms, air_ma, air_ms = values
    return norm * ma * ms / (air_ma * air_ms)


def select_indices(count, wanted):
    if not isinstance(wanted, int) or not 16 <= wanted <= count:
        raise ValueError(f'Choose 16 to {count} views')
    return np.floor(np.arange(wanted) * count / wanted).astype(int)


def reference_to_rtk(array):
    """Inverse of the authors' fixed Elekta array permutation and superior-axis flip."""
    return np.transpose(np.flip(array, axis=0), (2, 0, 1))


def sample_reference(array, shape, order=1):
    from scipy.ndimage import map_coordinates
    coordinates = np.meshgrid(*[
        (np.arange(n) + .5) * old / n - .5 for n, old in zip(shape, array.shape)
    ], indexing='ij', sparse=False)
    return map_coordinates(array.astype(np.float32), coordinates, order=order,
                           mode='nearest', prefilter=False)


def paired(reference, image, mask):
    x, y = reference[mask].astype(float), image[mask].astype(float)
    if not x.size or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Invalid comparison samples')
    error = y - x
    centred = x - x.mean()
    ss = centred @ centred
    correlation = np.corrcoef(x, y)[0, 1] if x.std() and y.std() else None
    return {'voxels': int(x.size), 'rmse_hu': float(np.sqrt(np.mean(error**2))),
            'mae_hu': float(np.mean(np.abs(error))), 'bias_hu': float(error.mean()),
            'pearson_r': None if correlation is None else float(correlation),
            'prediction_r2': float(1 - error @ error / ss) if ss else None}


def reconstruct(data, output, size=96, binning=2, view_counts=(89, 178, 356), threads=4):
    import itk
    from itk import RTK as rtk
    import yaml

    itk.MultiThreaderBase.SetGlobalDefaultNumberOfThreads(threads)
    image_type = itk.Image[itk.F, 3]
    config = yaml.safe_load((data / 'reconstruction.yaml').read_text())
    i0 = incident_counts(config)
    raw = itk.imread(str(data / 'projections.mha'))
    raw_array = itk.array_view_from_image(raw)
    if raw_array.shape != (356, 504, 504):
        raise ValueError('Unexpected detector dimensions for the pinned case')
    counts = detector_bin(raw_array, binning)
    line_integrals = -np.log(counts / i0).astype(np.float32)
    origin = [float(raw.GetOrigin()[k]) + (binning - 1) * raw.GetSpacing()[k] / 2
              for k in (0, 1)] + [0.0]
    spacing = [float(raw.GetSpacing()[k]) * binning for k in (0, 1)] + [1.0]
    del raw_array, raw, counts
    # Fixed acquired reconstruction field in RTK x/y/z, independent of reference pixels.
    output_size = [size, round(size * 264 / 410), size]
    output_spacing = [extent / n for extent, n in zip((410, 264, 410), output_size)]
    output_origin = [-(n - 1) * s / 2 for n, s in zip(output_size, output_spacing)]
    results = []
    for wanted in view_counts:
        selected = select_indices(356, wanted)
        tree = ET.parse(data / 'geometry.xml')
        projections = tree.getroot().findall('Projection')
        if len(projections) != 356:
            raise ValueError('Geometry does not match the measured views')
        kept = set(selected.tolist())
        for index, projection in enumerate(projections):
            if index not in kept:
                tree.getroot().remove(projection)
        geometry_path = output / f'geometry-{wanted}.xml'
        tree.write(geometry_path, encoding='utf-8', xml_declaration=True)
        reader = rtk.ThreeDCircularProjectionGeometryXMLFileReader.New()
        reader.SetFilename(str(geometry_path))
        reader.GenerateOutputInformation()
        geometry = reader.GetOutputObject()
        measured = itk.image_from_array(line_integrals[selected].copy())
        measured.SetOrigin(origin)
        measured.SetSpacing(spacing)
        blank = rtk.ConstantImageSource[image_type].New()
        blank.SetSize(output_size)
        blank.SetSpacing(output_spacing)
        blank.SetOrigin(output_origin)
        blank.SetConstant(0.)
        displaced = rtk.DisplacedDetectorForOffsetFieldOfViewImageFilter[image_type].New()
        displaced.SetInput(measured)
        displaced.SetGeometry(geometry)
        displaced.SetDisable(False)
        parker = rtk.ParkerShortScanImageFilter[image_type].New()
        parker.SetInput(displaced.GetOutput())
        parker.SetGeometry(geometry)
        parker.InPlaceOff()
        parker.SetAngularGapThreshold(np.deg2rad(20))
        fdk = rtk.FDKConeBeamReconstructionFilter[image_type].New()
        fdk.SetInput(0, blank.GetOutput())
        fdk.SetInput(1, parker.GetOutput())
        fdk.SetGeometry(geometry)
        fdk.GetRampFilter().SetTruncationCorrection(.2)
        fdk.GetRampFilter().SetHannCutFrequency(.99)
        fdk.GetRampFilter().SetHannCutFrequencyY(.99)
        print(f'Reconstructing {wanted} measured views on {threads} CPU threads', flush=True)
        fdk.Update()
        volume = itk.array_from_image(fdk.GetOutput())
        if not np.isfinite(volume).all():
            raise ValueError('Reconstruction produced non-finite values')
        itk.imwrite(fdk.GetOutput(), str(output / f'reconstruction-{wanted}.mha'), compression=True)
        # This is the authors' display conversion, not an independent HU calibration.
        results.append((wanted, selected.tolist(), volume * 65536 - 1024))
        del fdk, parker, displaced, measured, blank
    del line_integrals

    # References cannot influence calibration, reconstruction or parameter selection above.
    reference_raw = itk.array_from_image(itk.imread(str(data / 'cbct_rtk.mha')))
    mask_raw = itk.array_from_image(itk.imread(str(data / 'fov_cbct.mha')))
    if reference_raw.shape != (264, 410, 410) or mask_raw.shape != reference_raw.shape:
        raise ValueError('Reference grid differs from the documented case')
    shape = results[0][2].shape
    reference = sample_reference(reference_to_rtk(reference_raw), shape)
    mask = sample_reference(reference_to_rtk(mask_raw), shape, order=0) > 0
    del reference_raw, mask_raw
    report = {'schema': 'ct-clinical-benchmark/1', 'algorithm': ALGORITHM,
              'case': MANIFEST['case'], 'license': MANIFEST['license'],
              'attribution': MANIFEST['attribution'],
              'source_record': MANIFEST['record'], 'source_sha256': {
                  k: v['sha256'] for k, v in MANIFEST['files'].items()},
              'python': platform.python_version(), 'platform': platform.platform(),
              'packages': {k: importlib.metadata.version(k) for k in
                           ('itk', 'itk-rtk', 'numpy', 'scipy')},
              'settings': {'detector_binning': binning, 'incident_counts': i0,
                           'size_xyz': output_size, 'spacing_xyz_mm': output_spacing,
                           'origin_xyz_mm': output_origin, 'threads': threads,
                           'hann_xy': .99, 'truncation_correction': .2},
              'comparison': 'Authors full-data RTK FDK reference; same algorithm family. '
                            'Fixed documented axis conversion; no fitted alignment or scaling. '
                            'Errors use the supplied field-of-view mask. Display HU uses '
                            '65536 * attenuation - 1024, following the authors. '
                            'This is a numerical reproduction check, not clinical validation.',
              'results': []}
    for wanted, indices, volume in results:
        report['results'].append({'views': wanted, 'selected_indices': indices,
                                  **paired(reference, volume, mask)})
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    (output / 'DATA-LICENSE.txt').write_text(
        (HERE.parent / 'docs/clinical/LICENSE.txt').read_text())
    draw_comparison(reference, mask, results, output)
    return report


def draw_comparison(reference, mask, results, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    middle = reference.shape[1] // 2
    fig, axes = plt.subplots(2, len(results) + 1, figsize=(4 * (len(results) + 1), 8),
                             layout='constrained')
    # Display in the authors' in-plane array order; numerical volumes remain in RTK axes.
    axes[0, 0].imshow(reference[:, middle, :].T, cmap='gray', vmin=-1000, vmax=800)
    axes[0, 0].set_title('Authors full-data reference')
    axes[1, 0].text(.05, .9, 'Measured patient projections\nCOBRA2026 A002\n\n'
                    'CPU cone-beam FDK\nSame display window in every image\n\n'
                    'Error: result minus reference\nWithin supplied field of view\n\n'
                    'Display conversion follows the authors.\nReference is an estimate.',
                    transform=axes[1, 0].transAxes, va='top', fontsize=11)
    for column, (wanted, _, volume) in enumerate(results, 1):
        axes[0, column].imshow(volume[:, middle, :].T, cmap='gray', vmin=-1000, vmax=800)
        axes[0, column].set_title(f'{wanted} acquired views')
        error = np.where(mask[:, middle, :], (volume - reference)[:, middle, :], np.nan)
        picture = axes[1, column].imshow(error.T, cmap='RdBu_r', vmin=-250, vmax=250)
        axes[1, column].set_title('Difference from reference')
    for axis in axes.flat:
        axis.set_axis_off()
    fig.colorbar(picture, ax=list(axes[1, 1:]), label='Difference in authors’ HU scale', shrink=.65)
    fig.suptitle('Clinical cone-beam reconstruction from measured projections', fontsize=17)
    fig.savefig(output / 'comparison.png', dpi=140)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=HERE.parent / 'data-cache/cobra-a002')
    parser.add_argument('--output', type=Path, default=HERE.parent / 'runs/clinical-a002')
    parser.add_argument('--download', action='store_true', help='Fetch the pinned 150 MB case once')
    parser.add_argument('--size', type=int, choices=(64, 96, 128), default=96)
    parser.add_argument('--binning', type=int, choices=(1, 2, 4), default=2)
    parser.add_argument('--views', type=int, nargs='+', default=[89, 178, 356])
    parser.add_argument('--threads', type=int, choices=range(1, 9), default=4)
    args = parser.parse_args()
    if len(args.views) != len(set(args.views)) or len(args.views) > 4:
        parser.error('Choose up to four distinct view counts')
    for views in args.views:
        select_indices(356, views)
    verify_files(args.data, args.download)
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error('Use an empty output directory to preserve earlier results')
    os.environ.setdefault('MPLCONFIGDIR', str(args.output / '.matplotlib'))
    report = reconstruct(args.data, args.output, args.size, args.binning, args.views, args.threads)
    for row in report['results']:
        print(f'{row["views"]} views: RMSE {row["rmse_hu"]:.2f}; Pearson r {row["pearson_r"]:.4f}')


if __name__ == '__main__':
    main()
