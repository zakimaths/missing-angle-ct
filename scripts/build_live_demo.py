"""Publish executable reconstruction code and measurements, never prepared results."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'src/missing_angle/web'
DEMO = Path(globals().get('LIVE_DESTINATION', ROOT / 'demo'))
for name in ('live.css', 'live.js', 'study.js', 'projection-core.js', 'projection-worker.js'):
    shutil.copy2(WEB / name, DEMO / name)
shutil.copytree(WEB / 'projection-data', DEMO / 'projection-data', dirs_exist_ok=True)
shutil.copytree(WEB / 'reference-data', DEMO / 'reference-data', dirs_exist_ok=True)
index = (DEMO / 'index.html' if (DEMO / 'index.html').exists() else ROOT / 'demo/index.html').read_text()
a, b = '<!-- LIVE-LAB-START -->', '<!-- LIVE-LAB-END -->'
if a not in index:
    index = index.replace('<section class="lab"', a + b + '\n<section class="lab"', 1)
before, rest = index.split(a, 1)
_, after = rest.split(b, 1)
index = before + a + '\n' + (WEB / 'live-panel.html').read_text() + '\n' + b + after
(DEMO / 'index.html').write_text(index)
print('Live reconstruction code and three measured datasets published to demo/.')
