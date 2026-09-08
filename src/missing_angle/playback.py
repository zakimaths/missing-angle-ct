"""A small, offline player for PNGs made from actual numerical iteration states."""
import base64
from io import BytesIO
import json

import numpy as np
from PIL import Image


def png_bytes(array, low=0., high=.6):
    pixels = np.rint(255*np.clip((array-low)/(high-low), 0, 1)).astype(np.uint8)
    output = BytesIO()
    Image.fromarray(pixels).save(output, format="PNG")
    return output.getvalue()


def player_html(history):
    frames = ["data:image/png;base64," + base64.b64encode(png_bytes(frame)).decode()
              for frame in history]
    return '''<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;color:#172f3a;background:white;font:16px/1.5 system-ui,sans-serif}
img{display:block;width:100%;height:280px;object-fit:contain;background:#080b0c}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:12px 0}
button{font:inherit;min-height:44px;padding:8px 14px;border:1px solid #789398;background:#f0f5f5;color:#172f3a;cursor:pointer}
button:focus-visible,input:focus-visible{outline:3px solid #007f87;outline-offset:2px}
input{width:100%;accent-color:#007f87;min-height:32px}label{display:block}p{font-size:14px;margin:8px 0}
</style><img id="frame" alt="Reconstruction at step 0: the initial blank image">
<div class="controls"><button id="play" type="button">Play reconstruction</button><button id="back" type="button">Previous step</button><button id="next" type="button">Next step</button></div>
<label for="step">Reconstruction step <output id="count">0</output></label><input id="step" type="range" min="0" value="0" step="1">
<p id="explain">Step 0 starts with a blank image.</p><p>Recorded calculation steps, played slowly so you can inspect them. Brightness stays fixed. Playback speed is not calculation time.</p>
<script>
const frames=FRAMES;const image=document.getElementById('frame'),slider=document.getElementById('step'),button=document.getElementById('play');
let timer=null;slider.max=frames.length-1;
function stop(){clearInterval(timer);timer=null;button.textContent='Play reconstruction'}
function show(i){slider.value=i;image.src=frames[i];image.alt='Reconstruction after '+i+' full passes through the measurements';document.getElementById('count').textContent=i+' / '+slider.max;document.getElementById('explain').textContent=i===0?'Step 0 starts with a blank image.':'Pass '+i+': compare predicted X-ray measurements with the available measurements, correct the image, then gently smooth it.'}
slider.addEventListener('input',()=>{stop();show(Number(slider.value))});
button.onclick=()=>{if(timer){stop();return}if(Number(slider.value)===frames.length-1)show(0);button.textContent='Pause reconstruction';timer=setInterval(()=>{const next=Number(slider.value)+1;if(next<frames.length)show(next);if(next>=frames.length-1)stop()},650)};
document.getElementById('back').onclick=()=>{stop();show(Math.max(0,Number(slider.value)-1))};
document.getElementById('next').onclick=()=>{stop();show(Math.min(frames.length-1,Number(slider.value)+1))};
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stop()}).observe(image);
show(0);
</script></html>'''.replace('FRAMES', json.dumps(frames))
