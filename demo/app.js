'use strict';
const byId = id => document.getElementById(id);
let experiments = [], current = null, timer = null, selection = 0;
function stop() {
  clearInterval(timer); timer = null;
  byId('play').textContent = current && Number(byId('step').value) === current.frames.length - 1 ? 'Replay from the start' : 'Play reconstruction';
}
function showStep(step) {
  byId('step').value = step;
  byId('animation').src = current.frames[step];
  byId('animation').alt = current.frame_labels[step];
  byId('step-label').textContent = `${step} / ${current.frames.length - 1}`;
  byId('step-explanation').textContent = current.frame_labels[step];
}
function showComparison() {
  if (!current) return;
  const errors = byId('comparison').value === 'errors', detail = byId('detail').checked;
  for (const method of ['phantom', 'fbp', 'sart', 'regularized']) {
    const suffix = (errors && method !== 'phantom' ? '-error' : '') + (detail ? '-detail' : '');
    byId(method).src = `${current.folder}/${method}${suffix}.png`;
    byId(method).alt = `${method === 'phantom' ? 'Prepared reference' : method + (errors ? ' absolute difference from reference' : ' reconstruction')}${detail ? ', centre detail' : ''}`;
  }
  byId('comparison-explanation').textContent = errors
    ? 'Difference maps: black means a match; purple, orange and yellow show increasing absolute pixel error. Yellow means 0.03 or more. Every method uses this same scale. The prepared reference stays grayscale; coloured maps show error, not anatomy.'
    : 'Reconstructed images use the same 0 to 0.6 relative-attenuation scale. With complete angle coverage they should look similar. Switch to difference maps or centre zoom to inspect small errors.';
}
async function selectExperiment() {
  stop(); const request = ++selection;
  byId('result').hidden = true;
  byId('status').textContent = 'Loading the selected CT images and recorded steps…';byId('gallery-retry').hidden=true;
  const chosen = experiments.find(e => e.slice === Number(byId('slice').value) && e.protocol === byId('protocol').value);
  try {
    const images = [...chosen.frames, `${chosen.folder}/original.png`];
    for (const method of ['phantom', 'fbp', 'sart', 'regularized']) {
      for (const suffix of ['', '-detail', ...(method === 'phantom' ? [] : ['-error', '-error-detail'])]) images.push(`${chosen.folder}/${method}${suffix}.png`);
    }
    await Promise.all(images.map(src => new Promise((resolve, reject) => {
      const image = new Image(); image.onload = resolve; image.onerror = reject; image.src = src;
    })));
    if (request !== selection) return;
    current = chosen;
    byId('settings-summary').textContent = `${current.views} views · ${current.span}° covered · ${180-current.span}° missing`;
    byId('lesson').textContent = current.lesson;
    byId('original').src = `${current.folder}/original.png`;
    showComparison();
    for (const method of ['fbp', 'sart', 'regularized']) byId(`${method}-score`).textContent = `Image difference (RMSE): ${current.metrics[method].rmse.toFixed(5)}`;
    byId('download').href = `${current.folder}/experiment.zip`;
    byId('experiment-id').textContent = 'Includes measurements, settings and results.';
    byId('step').max = current.frames.length - 1;
    showStep(0); stop();
    byId('status').textContent = ''; byId('result').hidden = false;
  } catch {
    if(request===selection){byId('status').textContent='The comparison images could not load. Retry when your connection is available.';byId('gallery-retry').hidden=false;}
  }
}
byId('play').onclick = () => {
  if (timer) { stop(); return; }
  if (Number(byId('step').value) === current.frames.length - 1) showStep(0);
  byId('play').textContent = 'Pause reconstruction';
  timer = setInterval(() => {
    const next = Number(byId('step').value) + 1;
    showStep(Math.min(next, current.frames.length - 1));
    if (next >= current.frames.length - 1) stop();
  }, 850);
};
byId('step').oninput = () => { stop(); showStep(Number(byId('step').value)); };
byId('previous').onclick = () => { stop(); showStep(Math.max(0, Number(byId('step').value)-1)); };
byId('next').onclick = () => { stop(); showStep(Math.min(current.frames.length-1, Number(byId('step').value)+1)); };
byId('slice').onchange = byId('protocol').onchange = selectExperiment;
byId('comparison').onchange = byId('detail').onchange = showComparison;
document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
// Watch the whole player: on narrow screens the controls can be below the image.
new IntersectionObserver(entries => { if (!entries[0].isIntersecting) stop(); }).observe(byId('player'));
let libraryLoading=false,libraryLoaded=false;
function loadLibrary() {
 if(libraryLoading||libraryLoaded)return;
 libraryLoading=true;byId('gallery-retry').hidden=true;byId('status').textContent='Loading the recorded comparison library…';
 fetch('experiments.json?v=4', {cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('Missing data');return r.json();}).then(data=>{
  experiments=data.experiments;
  byId('slice').replaceChildren();
  for(const index of [...new Set(experiments.map(e=>e.slice))]){const option=document.createElement('option');option.value=index;option.textContent=`Chest slice ${index}`;byId('slice').append(option);}
  byId('slice').value='80';byId('slice').disabled=byId('protocol').disabled=false;libraryLoaded=true;
  return selectExperiment();
 }).catch(()=>{byId('status').textContent='The comparison library could not load. Retry when your connection is available.';byId('gallery-retry').hidden=false;}).finally(()=>{libraryLoading=false;});
}
byId('recorded-gallery').ontoggle=()=>{if(byId('recorded-gallery').open)loadLibrary();else stop();};
byId('gallery-retry').onclick=()=>libraryLoaded?selectExperiment():loadLibrary();
