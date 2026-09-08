"""Render truthful launch figures from the same measured-data solver as the demo."""
import hashlib
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def build(destination):
    calculated = json.loads(subprocess.check_output(
        ['node', str(ROOT / 'scripts/launch_comparison.cjs')], text=True))
    ink, muted, teal = '#172f3a', '#46616b', '#007f87'
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'text.color': ink})
    for social in (False, True):
        width, height = (1200, 630) if social else (900, 540)
        fig = plt.figure(figsize=(width / 100, height / 100), dpi=100, facecolor='white')
        if social:
            fig.text(.05, .91, 'Missing-Angle CT', fontsize=30, weight='bold')
            fig.text(.05, .845, 'Every view changes the picture.', fontsize=19, color=muted)
        bottom, side = (.19, .52) if social else (.17, .68)
        for i, result in enumerate(calculated['images']):
            side_width = side * height / width
            left = (.15 if social else .07) + i * (.43 if social else .48)
            ax = fig.add_axes((left, bottom, side_width, side))
            ax.imshow(np.array(result['image']).reshape(96, 96), cmap='gray', vmin=0, vmax=.06,
                      interpolation='bilinear')
            ax.set_axis_off()
            title = '90 spread views' if i == 0 else '90 consecutive views'
            fig.text(left, bottom+side+.04, title, fontsize=18 if social else 17,
                     color=teal if i == 0 else ink, weight='bold')
            fig.text(left, bottom-.055, f"{result['angles'][0]:g}° to {result['angles'][-1]:g}°",
                     fontsize=14, color=muted)
        if social:
            fig.text(.05, .05, 'Measured X-ray projections. Live browser reconstruction.', fontsize=15)
            fig.text(.05, .015, 'HTC2022 · Meaney et al. · CC BY 4.0 | zakimaths.github.io/missing-angle-ct', fontsize=10, color=muted)
        else:
            fig.text(.07, .03, 'One SART pass · same measured object and display scale', fontsize=12, color=muted)
        name = 'share-card.png' if social else 'comparison-preview.png'
        fig.savefig(destination / name, dpi=100, metadata={'Software': 'Missing-Angle CT'})
        plt.close(fig)
    report = {**calculated, 'display_limits_per_mm': [0, .06],
              'source': 'https://zenodo.org/records/8041800', 'license': 'CC BY 4.0'}
    for result in report['images']:
        pixels = np.asarray(result.pop('image'), dtype='<f8')
        result['calculated_image_sha256'] = hashlib.sha256(pixels.tobytes()).hexdigest()
    (destination / 'share-attribution.txt').write_text(
        'Derived from HTC2022 v1.4.0, Meaney, Silva de Moura, Juvonen and Siltanen (2023).\n'
        'Source: https://zenodo.org/records/8041800\n'
        'Licence: CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\n'
        'Two new 96 by 96 reconstructions, one nonnegative SART pass, 90 selected views.\n'
        'Identical 0 to 0.06 per-mm display scale. Images are calculated results, not ground truth.\n')
    (destination / 'share-provenance.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__' or 'LAUNCH_DESTINATION' in globals():
    build(Path(globals().get('LAUNCH_DESTINATION', ROOT / 'demo')))
