"""A small, offline player for PNGs made from actual numerical iteration states."""
import base64
from io import BytesIO
import json

import numpy as np
from PIL import Image
from matplotlib import colormaps
from .refinement import early_counts


def png_bytes(array, low=0., high=.6):
    pixels = np.rint(255*np.clip((array-low)/(high-low), 0, 1)).astype(np.uint8)
    output = BytesIO()
    Image.fromarray(pixels).save(output, format="PNG")
    return output.getvalue()



def comparison_png(image, reference=None, detail=False):
    if reference is not None:
        image = np.abs(image-reference)
    if detail:
        n = image.shape[0]
        image = image[n//4:3*n//4, n//4:3*n//4]
    if reference is None:
        return png_bytes(image)
    pixels = np.rint(255*colormaps['magma'](np.clip(image/.03, 0, 1))[:, :, :3]).astype(np.uint8)
    output = BytesIO()
    Image.fromarray(pixels).save(output, format='PNG')
    return output.getvalue()


def playback_sequence(experiment):
    history = experiment.arrays['history']
    images = [history[0]]
    labels = ['Start: no measurements used yet.']
    if 'early_history' in experiment.arrays:
        for count, frame in zip(early_counts(experiment.config.views), experiment.arrays['early_history']):
            images.append(frame)
            labels.append(f'First pass: {count} of {experiment.config.views} views used. Each new view corrects the image from another direction.')
    for number, frame in enumerate(history[1:], 1):
        images.append(frame)
        smoothing = 'Smoothing applied.' if experiment.geometry['refinement']['weight'] else 'Smoothing is switched off.'
        labels.append(f'Pass {number} complete: all {experiment.config.views} views used. {smoothing} Later passes make smaller corrections.')
    return images, labels

def player_html(experiment):
    history, labels = playback_sequence(experiment)
    frames = ["data:image/png;base64," + base64.b64encode(png_bytes(frame)).decode()
              for frame in history]
    html = '''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;color:#172f3a;background:white;font:16px/1.5 system-ui,sans-serif}
img{display:block;width:100%;height:280px;object-fit:contain;background:#080b0c}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:12px 0}
button{font:inherit;min-height:44px;padding:8px 14px;border:1px solid #789398;background:#f0f5f5;color:#172f3a;cursor:pointer}
button:focus-visible,input:focus-visible{outline:3px solid #007f87;outline-offset:2px}
input{width:100%;accent-color:#007f87;min-height:32px}label{display:block}p{font-size:14px;margin:8px 0}
</style><img id="frame" alt="Reconstruction at step 0: the initial blank image">
<div class="controls"><button id="play" type="button">Play reconstruction</button><button id="back" type="button">Previous step</button><button id="next" type="button">Next step</button></div>
<label for="step">Snapshot <output id="count">0</output></label><input id="step" type="range" min="0" value="0" step="1">
<p id="explain">Step 0 starts with a blank image.</p><p>Recorded calculation steps, played slowly so you can inspect them. Brightness stays fixed. Playback speed is not calculation time.</p>
<script>
const frames=FRAMES,labels=LABELS;const image=document.getElementById('frame'),slider=document.getElementById('step'),button=document.getElementById('play');
let timer=null;slider.max=frames.length-1;
function stop(){clearInterval(timer);timer=null;button.textContent='Play reconstruction'}
function show(i){slider.value=i;image.src=frames[i];image.alt=labels[i];document.getElementById('count').textContent=i+' / '+slider.max;document.getElementById('explain').textContent=labels[i]}
slider.addEventListener('input',()=>{stop();show(Number(slider.value))});
button.onclick=()=>{if(timer){stop();return}if(Number(slider.value)===frames.length-1)show(0);button.textContent='Pause reconstruction';timer=setInterval(()=>{const next=Number(slider.value)+1;if(next<frames.length)show(next);if(next>=frames.length-1)stop()},850)};
document.getElementById('back').onclick=()=>{stop();show(Math.max(0,Number(slider.value)-1))};
document.getElementById('next').onclick=()=>{stop();show(Math.min(frames.length-1,Number(slider.value)+1))};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stop()}).observe(document.body);
show(0);
</script></html>'''.replace('FRAMES', json.dumps(frames)).replace('LABELS', json.dumps(labels))

    return html
