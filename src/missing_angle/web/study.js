/* Evaluation and annotations are kept outside the reconstruction worker. */
(function(root){
'use strict';
const CT=root.CT||(typeof require!=='undefined'?require('./projection-core.js'):null);
const disks=[[0,0,25,.035],[-10,7,5,-.025],[10,-8,3,-.025],[9,10,1.5,.015]];
function synthetic(){
 const angles=Array.from({length:360},(_,i)=>i*.5),detectors=140,pitch=.5;
 // Exact continuous disk chords, independent of the pixel-grid ray projector.
 const sinogram=angles.map(angle=>{const a=angle*Math.PI/180;return Array.from({length:detectors},(_,d)=>disks.reduce((sum,[x,y,r,mu])=>{const u=(d-(detectors-1)/2)*pitch-x*Math.cos(a)-y*Math.sin(a);return sum+2*mu*Math.sqrt(Math.max(0,r*r-u*u));},0));});
 return {schema:'ct-projections/1',name:'Analytic disks · exact continuous projections',kind:'synthetic',angles_deg:angles,sinogram,geometry:{type:'parallel',fov_mm:70,detector_spacing_mm:pitch},source:{preparation:'Deterministic analytic disk chord lengths; no raster forward transform or random noise.'}};
}
function syntheticReference(size=96){
 // 8×8 subpixel area sampling of the known continuous object, not the solver grid.
 const image=Array.from({length:size*size},(_,k)=>{let sum=0;for(let sy=0;sy<8;sy++)for(let sx=0;sx<8;sx++){const x=((k%size)+(sx+.5)/8)*70/size-35,y=35-(Math.floor(k/size)+(sy+.5)/8)*70/size;for(const [cx,cy,r,mu]of disks)if(Math.hypot(x-cx,y-cy)<r)sum+=mu;}return sum/64;});
 return {schema:'ct-reference/1',name:'Known analytic disks · 8 × 8 area sampling',kind:'analytic',size,fov_mm:70,units:'1/mm',orientation:'row-major-top-left',image};
}
function validateReference(ref,input){
 if(!ref||ref.schema!=='ct-reference/1'||!Number.isInteger(ref.size)||ref.size<16||ref.size>512||!Array.isArray(ref.image)||ref.image.length!==ref.size**2||!ref.image.every(v=>Number.isFinite(v)&&Math.abs(v)<=100)||typeof ref.name!=='string'||ref.name.length>160||ref.units!=='1/mm'||ref.orientation!=='row-major-top-left'||!Number.isFinite(ref.fov_mm)||Math.abs(ref.fov_mm-input.geometry.fov_mm)>1e-6)throw Error('The reference must be a square image with 16 to 512 pixels per side, the same physical field of view as the scan, attenuation values per millimetre, and pixels ordered from the top-left corner.');
 return ref;
}
function resample(image,size){
 const n=Math.sqrt(image.length);if(n===size)return Float64Array.from(image);
 return Float64Array.from({length:size*size},(_,k)=>{const x=Math.max(0,Math.min(n-1,((k%size)+.5)*n/size-.5)),y=Math.max(0,Math.min(n-1,(Math.floor(k/size)+.5)*n/size-.5)),x0=Math.floor(x),y0=Math.floor(y),dx=x-x0,dy=y-y0,x1=Math.min(n-1,x0+1),y1=Math.min(n-1,y0+1);return (1-dy)*((1-dx)*image[y0*n+x0]+dx*image[y0*n+x1])+dy*((1-dx)*image[y1*n+x0]+dx*image[y1*n+x1]);});
}
function regionStats(image,reference,roi){const n=Math.sqrt(image.length),values=[],truth=[];for(let y=0;y<n;y++)for(let x=0;x<n;x++)if((x+.5)/n>=roi.x&&(x+.5)/n<roi.x+roi.w&&(y+.5)/n>=roi.y&&(y+.5)/n<roi.y+roi.h){values.push(image[y*n+x]);if(reference)truth.push(reference[y*n+x]);}if(!values.length)return null;return {pixels:values.length,mean:values.reduce((a,b)=>a+b,0)/values.length,...(reference?CT.paired(truth,values):{})};}
function validateLabels(data){
 if(!data)return {name:'',regions:[]};
 if(typeof data.name!=='string'||data.name.length>120||!Array.isArray(data.regions)||data.regions.length>30||!data.regions.every(r=>typeof r.name==='string'&&r.name.length>0&&r.name.length<=80&&['x','y','w','h'].every(k=>Number.isFinite(r[k]))&&r.x>=0&&r.y>=0&&r.w>0&&r.h>0&&r.x+r.w<=1.000001&&r.y+r.h<=1.000001))throw Error('Labels need a run name and up to 30 named regions inside the image.');return {name:data.name,regions:data.regions.map(r=>({name:r.name,x:r.x,y:r.y,w:r.w,h:r.h}))};
}
const api={synthetic,syntheticReference,validateReference,resample,regionStats,validateLabels};root.CTStudy=api;if(typeof module!=='undefined')module.exports=api;
if(typeof document==='undefined')return;
const $=id=>document.getElementById('live-'+id),number=v=>v===null||v===undefined?'Unavailable':Number(v).toPrecision(4);
let input=null,reference=null,result=null,regions=[],history=[],generation=0,referenceMessage='No reference loaded.';
function save(text,name,type='application/json'){const u=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function table(headers,rows){const t=document.createElement('table'),head=t.createTHead().insertRow();for(const name of headers){const th=document.createElement('th');th.scope='col';th.textContent=name;head.append(th);}const body=t.createTBody();for(const values of rows){const row=body.insertRow();values.forEach((v,i)=>{const cell=document.createElement(i?'td':'th');if(!i)cell.scope='row';cell.textContent=v;row.append(cell);});}return t;}
function draw(canvas,image,signed=false){const n=Math.sqrt(image.length);canvas.width=canvas.height=n;const ctx=canvas.getContext('2d'),p=ctx.createImageData(n,n),upper=Number($('window').value);for(let i=0;i<image.length;i++){const value=Math.min(1,Math.abs(image[i])*(signed?10:1)/upper),v=Math.round(255*value),j=i*4;if(signed){p.data[j]=image[i]>=0?v:0;p.data[j+1]=image[i]<0?Math.round(v*.6):Math.round(v*.25);p.data[j+2]=image[i]<0?v:0;}else p.data[j]=p.data[j+1]=p.data[j+2]=v;p.data[j+3]=255;}ctx.putImageData(p,0,0);}
function plot(canvas,points,xlabel,ylabel,identity=false){
 const side=440,h=300;canvas.width=880;canvas.height=600;const ctx=canvas.getContext('2d');ctx.scale(2,2);ctx.fillStyle='#fff';ctx.fillRect(0,0,side,h);if(!points.length)return;
 let xmin=Math.min(0,...points.map(p=>p[0])),xmax=Math.max(.001,...points.map(p=>p[0])),ymin=Math.min(0,...points.map(p=>p[1])),ymax=Math.max(.001,...points.map(p=>p[1]));if(identity){xmin=ymin=Math.min(xmin,ymin);xmax=ymax=Math.max(xmax,ymax);}const x=v=>55+(v-xmin)/(xmax-xmin)*365,y=v=>250-(v-ymin)/(ymax-ymin)*220;
 ctx.strokeStyle='#9aafb3';ctx.beginPath();ctx.moveTo(55,25);ctx.lineTo(55,250);ctx.lineTo(425,250);ctx.stroke();ctx.setLineDash([4,4]);ctx.beginPath();if(identity){ctx.moveTo(x(xmin),y(xmin));ctx.lineTo(x(xmax),y(xmax));}else{ctx.moveTo(x(xmin),y(0));ctx.lineTo(x(xmax),y(0));}ctx.stroke();ctx.setLineDash([]);
 for(const p of points){ctx.fillStyle=p[2]?'#007f8790':'#bc5935b0';ctx.fillRect(x(p[0])-1.5,y(p[1])-1.5,3,3);}ctx.fillStyle='#526975';ctx.font='12px system-ui';ctx.fillText(String(Number(xmin.toPrecision(3))),55,267);ctx.fillText(String(Number(xmax.toPrecision(3))),390,267);ctx.fillText(String(Number(ymax.toPrecision(3))),2,30);ctx.fillText(String(Number(ymin.toPrecision(3))),2,250);ctx.textAlign='center';ctx.fillText(xlabel,240,291);ctx.textAlign='left';ctx.fillText(ylabel,55,15);
}
function sourcePreview(){
 const p=reference?.preview,valid=reference?.kind==='body_ct_source'&&p&&p.size===256&&Array.isArray(p.image)&&p.image.length===256**2&&p.image.every(v=>Number.isInteger(v)&&v>=0&&v<=255);
 $('body-preview').hidden=!valid;if(!valid)return;
 const canvas=$('source-image'),ctx=canvas.getContext('2d'),pixels=ctx.createImageData(256,256);canvas.width=canvas.height=256;
 for(let k=0;k<p.image.length;k++){pixels.data[k*4]=pixels.data[k*4+1]=pixels.data[k*4+2]=p.image[k];pixels.data[k*4+3]=255;}ctx.putImageData(pixels,0,0);
 $('source-window').textContent=`Source CT display · centre ${p.window_center_hu} HU · width ${p.window_width_hu} HU`;
 $('body-description').textContent=input.name+'. The source image shows the original CT values in a tissue display window. Reconstruction and error maps below share an attenuation scale, so their brightness differs from this preview.';
}
function refs(){return reference&&result?resample(reference.image,result.options.size):null;}
function imageMetrics(){const r=refs();return r?{baseline:CT.paired(r,result.baseline),current:CT.paired(r,result.image)}:null;}
function annotations(){if(!result)return;const canvas=$('label-image');draw(canvas,result.image);const copy=document.createElement('canvas');copy.width=copy.height=canvas.width;copy.getContext('2d').drawImage(canvas,0,0);canvas.width=canvas.height=768;const ctx=canvas.getContext('2d'),n=canvas.width;ctx.drawImage(copy,0,0,n,n);ctx.lineWidth=n/220;ctx.font=`${n/25}px system-ui`;regions.forEach((r,i)=>{ctx.strokeStyle='#ffc658';ctx.strokeRect(r.x*n,r.y*n,r.w*n,r.h*n);ctx.fillStyle='#172f3a';ctx.fillRect(r.x*n,r.y*n, n*.07,n*.065);ctx.fillStyle='#fff';ctx.fillText(String(i+1),r.x*n+n*.01,r.y*n+n*.05);});const ref=refs();$('labels-list').replaceChildren();regions.forEach((r,i)=>{const row=document.createElement('div'),s=regionStats(result.image,ref,r);row.className='live-label-row';const text=document.createElement('span');text.textContent=`${i+1}. ${r.name} · ${s?s.pixels+' pixels; mean '+number(s.mean)+' /mm'+(ref?'; RMSE '+number(s.rmse)+' /mm':''):'No pixel centres in this region'}`;const button=document.createElement('button');button.type='button';button.textContent='Remove';button.setAttribute('aria-label',`Remove region ${i+1}: ${r.name}`);button.onclick=()=>{regions.splice(i,1);annotations();};row.append(text,button);$('labels-list').append(row);});}
function render(){
 $('reference-info').textContent=referenceMessage;sourcePreview();
 if(!result)return;
 const e=result.evaluation,b=result.baselineEvaluation,im=imageMetrics();
 $('score-table').replaceChildren(table(['Check','First pass','Current image'],[['Selected rays · RMSE',number(b.selected.rmse),number(e.selected.rmse)],['Unused rays · RMSE',number(b.unused?.rmse),number(e.unused?.rmse)],['Reference image · RMSE (/mm)',number(im?.baseline.rmse),number(im?.current.rmse)],['Reference image · MAE (/mm)',number(im?.baseline.mae),number(im?.current.mae)],['Reference image · mean bias (/mm)',number(im?.baseline.bias),number(im?.current.bias)],['Reference image · Pearson r',number(im?.baseline.correlation),number(im?.current.correlation)]]));
 const assessment=[];for(const [name,oldValue,newValue]of [['reference-image RMSE',im?.baseline.rmse,im?.current.rmse],['unused-ray RMSE',b.unused?.rmse,e.unused?.rmse]])if(oldValue!==undefined){const difference=newValue-oldValue;assessment.push(Math.abs(difference)<1e-12?`${name} is unchanged`:`${name} is ${difference<0?'lower':'higher'} than the first pass (${oldValue?Math.abs(difference/oldValue*100).toFixed(1)+'%':number(Math.abs(difference))})`);}
 $('verdict').textContent=assessment.length?assessment.join('; ')+'. These checks can disagree; smoothing is not guaranteed to improve reconstruction.':'Only selected-ray agreement is available. Add a matching reference or leave some views unused to assess more than the fitted measurements.';
 $('reference-figures').hidden=!reference;if(im){const r=refs();draw($('reference-image'),r);draw($('reference-error'),result.image.map((v,k)=>v-r[k]),true);}
 const group=$('stats-group').value,indices=e.angles.filter(a=>group==='all'||a.selected===(group==='selected')).map(a=>a.view),x=[],y=[],points=[];
 for(const i of indices)for(let d=0;d<input.sinogram[i].length;d++){x.push(input.sinogram[i][d]);y.push(e.predictions[i][d]);}
 if(x.length){const stats=CT.paired(x,y),stride=Math.max(1,Math.ceil(x.length/1800));for(let i=0;i<x.length;i+=stride)points.push([x[i],y[i],true]);plot($('scatter'),points,input.kind==='body_ct_simulated'?'Simulated line integral':'Input line integral','Predicted line integral',true);$('paired-stats').textContent=`${stats.n.toLocaleString()} paired detector readings · RMSE ${number(stats.rmse)} · MAE ${number(stats.mae)} · bias ${number(stats.bias)} · Pearson r ${number(stats.correlation)} · prediction R² ${number(stats.r2)}. Fitted prediction = ${number(stats.slope)} × measurement + ${number(stats.intercept)}. Plot displays ${points.length} evenly sampled pairs; statistics use every pair.`;}else{$('scatter').getContext('2d').clearRect(0,0,880,600);$('paired-stats').textContent='No unused views: choose fewer views and reconstruct again to create a check set.';}
 plot($('angle-error'),e.angles.map(a=>[a.angle,a.rmse,a.selected]),'Acquisition angle (degrees)','Per-view RMSE');
 const worst=[...e.angles].sort((a,b)=>b.rmse-a.rmse).slice(0,5);$('worst-angles').textContent='Largest ray errors: '+worst.map(a=>`view ${a.view+1} at ${number(a.angle)}° (${number(a.rmse)}, ${a.selected?'used':'unused'})`).join('; ')+'.';
 $('history-table').replaceChildren(table(['Checkpoint','Starting image','Selected-ray RMSE','Unused-ray RMSE','Reference RMSE (/mm)','Reference MAE (/mm)','Reference bias (/mm)'],stageMetrics().map(v=>[v.name+(v.current?' · current':''),v.parent_name||'Blank image',number(v.selected.rmse),number(v.unused?.rmse),number(v.image?.rmse),number(v.image?.mae),number(v.image?.bias)])));
 annotations();
}
function stageMetrics() {
 const ref=refs();
 return history.map(v=>({id:v.id,name:v.name,parent:v.parent,parent_name:history.find(p=>p.id===v.parent)?.name||null,current:v.current,refinements:v.refinements,selected:v.selected,unused:v.unused,image:ref?CT.paired(ref,v.image):null,regions:regions.map(r=>({...r,statistics:regionStats(v.image,ref,r)}))}));
}
api.checkpoints=(points,current)=>{history=points.map(p=>({id:p.id,parent:p.parent,name:p.name,image:p.image,selected:p.selected,unused:p.unused,refinements:p.refinements,current:p.id===current}));render();};
api.clearInput=()=>{generation++;input=null;reference=null;referenceMessage='No reference loaded.';api.reset();render();};
api.hide=()=>{$('evaluation').hidden=true;$('label-tools').hidden=true;};
api.reset=()=>{result=null;history=[];$('body-preview').hidden=true;$('evaluation').hidden=true;$('label-tools').hidden=true;};
api.useInput=async(data,key)=>{
 input=data;reference=null;regions=[];api.reset();$('run-name').value=data.name.slice(0,120);referenceMessage='No reference loaded. Ray errors remain available; a true image error needs an aligned reference.';render();const ticket=++generation;
 try{let r=null;if(key==='synthetic')r=syntheticReference();else if(['ta','tb','tc','chest-64','chest-96','abdomen-400','abdomen-480'].includes(key)){r=window.CT_EMBEDDED_REFERENCES?.[key]||await fetch(`reference-data/${key}.json`).then(r=>{if(!r.ok)throw Error('Reference download failed.');return r.json();});}
 if(ticket!==generation)return;if(r){reference=validateReference(r,data);referenceMessage=reference.kind==='analytic'?'Known continuous object, sampled into pixels. Projection values use exact disk chords.':reference.kind==='body_ct_source'?`${reference.name}. Real CT values mapped to an illustrative attenuation scale. This reference defines the simulated object; it is not an independent scanner reconstruction or exact anatomical truth. Reference and result use the same physical field of view.`:`${reference.name}. Full-scan FBP estimate from the dataset authors, reduced to 96 × 96; not exact physical truth. Reference is resampled to the chosen grid, with no fitted alignment or intensity scaling.`;}render();}catch(e){if(ticket===generation){referenceMessage=e.message+' You can still reconstruct and inspect ray errors.';render();}}
};
api.show=m=>{result=m;$('evaluation').hidden=false;$('label-tools').hidden=false;render();};
api.export=()=>({labels:validateLabels({name:$('run-name').value,regions}),reference,evaluation:result?{schema:'ct-statistics/1',image:imageMetrics(),stages:stageMetrics(),angles:result.evaluation.angles,regions:regions.map(r=>({...r,statistics:regionStats(result.image,refs(),r)}))}:null});
api.restore=data=>{const v=validateLabels(data.labels);if(data.reference)reference=validateReference(data.reference,input);if(v.name)$('run-name').value=v.name;regions=v.regions;if(data.reference)referenceMessage=`Restored reference: ${reference.name}. Supplied for comparison only; alignment must match the acquisition.`;render();};
api.render=render;
$('stats-group').onchange=render;
$('reference-file').onchange=async()=>{const f=$('reference-file').files[0],ticket=generation;if(!f)return;try{if(f.size>8*1024*1024)throw Error('Reference exceeds 8 MB.');const data=JSON.parse(await f.text());if(ticket!==generation)return;reference=validateReference(data,input);referenceMessage=`User-supplied reference: ${reference.name}. Confirm orientation and registration; equal dimensions alone do not establish alignment.`;render();}catch(e){$('reference-info').textContent=e.message;}finally{$('reference-file').value='';}};
$('add-label').onclick=()=>{try{$('region-name').removeAttribute('aria-invalid');const r={name:$('region-name').value.trim(),x:Number($('roi-x').value)/100,y:Number($('roi-y').value)/100,w:Number($('roi-w').value)/100,h:Number($('roi-h').value)/100};regions=validateLabels({name:$('run-name').value,regions:[...regions,r]}).regions;$('label-message').textContent='Region added. Labels and region errors are included in your saved run.';annotations();}catch(e){$('label-message').textContent=e.message;if(!$('region-name').value.trim()){$('region-name').setAttribute('aria-invalid','true');$('region-name').focus();}}};
$('label-image').onclick=e=>{const b=e.currentTarget.getBoundingClientRect();$('roi-x').value=Math.min(100-Number($('roi-w').value),Math.max(0,Math.round((e.clientX-b.left)/b.width*100)));$('roi-y').value=Math.min(100-Number($('roi-h').value),Math.max(0,Math.round((e.clientY-b.top)/b.height*100)));$('label-message').textContent='Region position set. Enter a name and choose Add region.';};
$('download-pairs').onclick=()=>{if(!result)return;const used=new Set(result.selected),rows=['view,angle_deg,detector,used_in_reconstruction,measured,predicted,error'];for(let i=0;i<input.angles_deg.length;i++)for(let d=0;d<input.sinogram[i].length;d++){const x=input.sinogram[i][d],y=result.evaluation.predictions[i][d];rows.push([i+1,input.angles_deg[i],d+1,used.has(i),x,y,y-x].join(','));}save(rows.join('\n'),'ct-paired-readings.csv','text/csv');};
$('download-report').onclick=()=>save(JSON.stringify({schema:'ct-evaluation/1',dataset:input.name,algorithm:CT.VERSION,options:result.options,...api.export()}),'ct-evaluation.json');
})(globalThis);
