/* Reproducible comparison: each enhancement starts from the same first pass. */
const fs=require('node:fs'),path=require('node:path');
const web=path.join(__dirname,'../src/missing_angle/web');
const CT=require(path.join(web,'projection-core.js')),Study=require(path.join(web,'study.js'));
const results=[];
for(const key of ['ta','tb','tc','synthetic']){
 const input=key==='synthetic'?Study.synthetic():JSON.parse(fs.readFileSync(path.join(web,'projection-data',key+'.json')));
 const reference=key==='synthetic'?Study.syntheticReference():JSON.parse(fs.readFileSync(path.join(web,'reference-data',key+'.json')));
 for(const [views,selection]of [[360,'spread'],[90,'spread'],[90,'sector']]){
  const selected=CT.selectViews(input.angles_deg.length,views,selection),used=new Set(selected),order=CT.viewOrder(selected),cache=new Map(),baseline=new Float64Array(96**2);
  const matrix=i=>{if(!cache.has(i))cache.set(i,CT.matrixForView(input,96,i));return cache.get(i);};
  for(const i of order)CT.update(matrix(i),baseline,input.sinogram[i]);
  for(const [name,smoothing]of [['First pass',null],['3 corrections, no smoothing',0],['3 corrections, light smoothing',.03],['3 corrections, stronger smoothing',.1]]){
   const image=baseline.slice();if(smoothing!==null)for(let p=0;p<3;p++){for(const i of order)CT.update(matrix(i),image,input.sinogram[i]);CT.smooth(image,96,smoothing);}
   const x=[[],[]],y=[[],[]];for(let i=0;i<input.angles_deg.length;i++){const predicted=CT.forward(matrix(i),image),g=used.has(i)?0:1;for(let d=0;d<predicted.length;d++){x[g].push(input.sinogram[i][d]);y[g].push(predicted[d]);}}
   results.push({dataset:key,kind:input.kind,views,selection,size:96,method:name,smoothing,image:CT.paired(reference.image,image),selected:CT.paired(x[0],y[0]),unused:x[1].length?CT.paired(x[1],y[1]):null});
  }
  process.stdout.write(`${key}: ${views} ${selection} compared\n`);
 }
}
const report={schema:'ct-benchmark/1',algorithm:CT.VERSION,node:process.version,description:'Three physical HTC objects plus exact analytic disks. Authors full-data FBP is a reference estimate, not exact truth. Deterministic 96 square grid, each enhancement starts from identical first pass; no reference used in solver. Smoothing is not tuned by this script.',results};
fs.writeFileSync(path.join(__dirname,'../docs/LIVE_BENCHMARK.json'),JSON.stringify(report,null,2)+'\n');
const lines=['# Live reconstruction benchmark','','Run `node scripts/benchmark_live.cjs` to reproduce the numerical report. Three measured HTC2022 objects dominate the evaluation; the fourth case uses analytic disk projections. Real references are the authors’ full-data FBP estimates at 96 × 96, not exact physical truth.','','Each enhancement starts from the same first-pass reconstruction and adds three passes. “Best” below means lowest reference RMSE among the three enhancement choices tested; it is not a general ranking. Unused rays are withheld from updates, but come from the same acquisition.','','| Sample | Views / selection | First-pass RMSE | Lowest enhanced RMSE | Best tested enhancement |','|---|---|---:|---:|---|'];
for(let i=0;i<results.length;i+=4){const group=results.slice(i,i+4),base=group[0],best=group.slice(1).sort((a,b)=>a.image.rmse-b.image.rmse)[0];lines.push(`| ${base.dataset} | ${base.views} / ${base.selection} | ${base.image.rmse.toFixed(6)} | ${best.image.rmse.toFixed(6)} | ${best.method} |`);}
lines.push('','RMSE units: 1/mm. The complete JSON also records MAE, bias, Pearson correlation, regression slope/intercept, prediction R², and selected/unused ray errors. The 90 consecutive views cover 0–44.5° in both acquisitions. Spread selections cover the 360° measured scan or 180° synthetic scan. No clinical or unseen-object claim follows from this small benchmark.','','Source: [HTC2022 v1.4.0](https://zenodo.org/records/8041800), Meaney and colleagues (2023), CC BY 4.0.');
fs.writeFileSync(path.join(__dirname,'../docs/LIVE_BENCHMARK.md'),lines.join('\n')+'\n');
