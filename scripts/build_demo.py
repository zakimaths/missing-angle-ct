"""Rebuild the public student demo from the same measured-data solver as the local app."""
import argparse
from pathlib import Path
import json
import shutil
import runpy

from missing_angle.bundle import export_bundle, experiment_id, provenance
from missing_angle.config import ExperimentConfig
from missing_angle.playback import png_bytes, comparison_png, playback_sequence
from missing_angle.public_ct import catalogue, licence_text, run_public_ct
from missing_angle.refinement import refine

PROTOCOLS = {
    'full': ('Many views', 180, 180., 0., 'Start here: many views over the complete 180° range.'),
    'sparse': ('Fewer views', 48, 180., 0., 'Keep the full angle range but use fewer views. Compare streaks with Many views.'),
    'missing': ('Missing angles', 48, 120., 0., 'Keep 48 views, but leave a 60° gap. Look for edges that change with direction.'),
    'noisy': ('Missing angles + noise', 48, 120., .006, 'Use the same missing angles and add measurement noise. Compare detail with smoothing on and off.'),
}


def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    assets = destination / 'assets'
    assets.mkdir(exist_ok=True)
    entries = []
    rows = []
    for index in [s['index'] for s in catalogue()['slices']]:
        for key, (label, views, span, noise, lesson) in PROTOCOLS.items():
            config = ExperimentConfig(views=views, span=span, noise=noise, nonnegative=True)
            exp = refine(run_public_ct(index, config), passes=10, weight=.002)
            # Same pass count without TV separates extra iterations from the smoothing effect.
            control = refine(exp, passes=10, weight=0.)
            name = f'{index}-{key}-{experiment_id(exp)}'
            folder = assets / name
            folder.mkdir(exist_ok=True)
            for method in ('phantom', 'fbp', 'sart', 'regularized'):
                (folder / f'{method}.png').write_bytes(comparison_png(exp.arrays[method]))
                (folder / f'{method}-detail.png').write_bytes(comparison_png(exp.arrays[method], detail=True))
                if method != 'phantom':
                    for detail in (False, True):
                        suffix = '-detail' if detail else ''
                        (folder / f'{method}-error{suffix}.png').write_bytes(comparison_png(exp.arrays[method], exp.arrays['phantom'], detail))
            (folder / 'original.png').write_bytes(png_bytes(exp.arrays['source_hu'], -1350, 150))
            frames = []
            images, labels = playback_sequence(exp)
            for step, image in enumerate(images):
                frame = f'assets/{name}/step-{step}.png'
                (destination / frame).write_bytes(png_bytes(image))
                frames.append(frame)
            (folder / 'experiment.zip').write_bytes(export_bundle(exp))
            entry = {'key': name, 'slice': index, 'protocol': key, 'label': label, 'lesson': lesson,
                     'views': views, 'span': span, 'noise': noise, 'size': config.size,
                     'id': experiment_id(exp), 'frames': frames, 'frame_labels': labels, 'folder': f'assets/{name}',
                     'metrics': exp.metrics['methods'], 'refinement': exp.geometry['refinement']}
            entries.append(entry)
            rows.append({'slice': index, 'protocol': key,
                         'rmse': {k: v['rmse'] for k, v in exp.metrics['methods'].items()},
                         'sart_10_no_tv_rmse': control.metrics['methods']['regularized']['rmse']})
            print(name, flush=True)
    source = catalogue()
    source.pop('slices')
    (destination / 'experiments.json').write_text(json.dumps({'schema': 1, 'experiments': entries, 'source': source}, indent=2))
    (destination / 'DATA-LICENSE.txt').write_text(licence_text())
    (destination / '.nojekyll').write_text('')
    report = {'environment': provenance(), 'development_slice': 80,
              'evaluation_slices': [16, 32, 48, 64, 96, 112, 128],
              'scope': 'One public acquired CT volume; simulated projections. Within-volume evaluation, not clinical validation.',
              'rows': rows}
    Path('docs/reconstruction-results.json').write_text(json.dumps(report, indent=2))
    shutil.copyfile('docs/reconstruction-results.json', destination / 'reconstruction-results.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('demo'))
    destination = parser.parse_args().output
    build(destination)
    # Keep the live calculator independent of recorded reconstruction assets.
    runpy.run_path(str(Path(__file__).with_name("build_live_demo.py")), init_globals={"LIVE_DESTINATION": destination})
