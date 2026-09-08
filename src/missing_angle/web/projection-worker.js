'use strict';
if (typeof CT === 'undefined') importScripts('projection-core.js?v=11');
let input,options,image,baseline,baselineEvaluation,selected,order,cache,paused=false,resumeWait=null,delay=12,running=false;
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function gate(early=false){if(paused)await new Promise(resolve=>resumeWait=resolve);await sleep(delay && early ? 140 : delay);}
function snapshot(stage,done,total,view,pass){const copy=Float32Array.from(image);postMessage({type:'frame',stage,done,total,view,pass,image:copy},[copy.buffer]);}
async function evaluateImage(){
 const used=new Set(selected),x=[[],[]],y=[[],[]],angles=[],predictions=[];
 for(let i=0;i<input.angles_deg.length;i++){
  const matrix=cache.get(i)||CT.matrixForView(input,options.size,i),prediction=CT.forward(matrix,image),group=used.has(i)?0:1;
  predictions.push(prediction);for(let d=0;d<prediction.length;d++){x[group].push(input.sinogram[i][d]);y[group].push(prediction[d]);}
  angles.push({view:i,angle:input.angles_deg[i],selected:!group,...CT.paired(input.sinogram[i],prediction)});
  if(i%24===0)await sleep(0);
 }
 return {selected:CT.paired(x[0],y[0]),unused:x[1].length?CT.paired(x[1],y[1]):null,angles,predictions};
}
async function run(stage) {
  running=true;
  const passes=stage==='build'?1:options.passes,total=passes*order.length;
  if(stage==='build'){image=new Float64Array(options.size**2);snapshot(stage,0,total,null,0);}
  for(let pass=0;pass<passes;pass++)for(let k=0;k<order.length;k++) {
    await gate(stage==='build'&&k<12);const view=order[k];
    if(!cache.has(view))cache.set(view,CT.matrixForView(input,options.size,view));
    CT.update(cache.get(view),image,input.sinogram[view]);
    if(k===order.length-1&&stage==='refine')CT.smooth(image,options.size,options.smoothing);
    if(stage==='refine'&&k%20===0)postMessage({type:'progress',done:pass*order.length+k+1,total});
    if(stage==='build'||k===order.length-1)snapshot(stage,pass*order.length+k+1,total,view,pass+1);
  }
  if(stage==='build')baseline=image.slice();
  postMessage({type:'scoring'});
  const evaluation=await evaluateImage();
  if(stage==='build')baselineEvaluation={selected:evaluation.selected,unused:evaluation.unused};
  const observed=evaluation.selected.relative,withheld=evaluation.unused?.relative??null;
  const result=Float64Array.from(image);
  postMessage({type:'complete',stage,observed,withheld,evaluation,baselineEvaluation,image:result,baseline:Float64Array.from(baseline),selected,order,options,algorithm:CT.VERSION});running=false;
}
onmessage=async event=>{
  const m=event.data;
  if(m.type==='one'){if(paused&&resumeWait){resumeWait();resumeWait=null;}return;}
  if(m.type==='pause'){paused=true;return;}
  if(m.type==='resume'){paused=false;if(resumeWait){resumeWait();resumeWait=null;}return;}
  if(m.type==='speed'){delay=m.delay===0?0:12;return;}
  try {
    if(m.type==='start'){
      if(running)throw Error('A reconstruction is already running.');
      input=CT.validate(m.input);options=CT.settings(m.options,input.angles_deg.length);
      if(options.size*input.sinogram[0].length*options.views>14000000)throw Error('Reduce the selected views or image size to fit the browser memory budget.');
      selected=CT.selectViews(input.angles_deg.length,options.views,options.selection);order=CT.viewOrder(selected);
      cache=new Map();paused=false;delay=m.slow?12:0;await run('build');
    }else if(m.type==='refine'){
      if(running||!image)throw Error('Complete a reconstruction before refining it.');
      options=CT.settings({...options,passes:m.passes,smoothing:m.smoothing},input.angles_deg.length);paused=false;await run('refine');
    }
  }catch(error){running=false;postMessage({type:'error',message:error.message});}
};
