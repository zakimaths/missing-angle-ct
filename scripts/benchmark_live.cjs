/* Reproducible comparison: each enhancement starts from the same first pass. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const web=path.join(__dirname,'../src/missing_angle/web');
const CT=require(path.join(web,'projection-core.js')),Study=require(path.join(web,'study.js'));
const results=[],sources={},check=process.argv.includes('--check');
const reportPath=path.join(__dirname,'../docs/LIVE_BENCHMARK.json');
for(const key of ['ta','tb','tc','chest-64','chest-96','abdomen-400','abdomen-480','synthetic']){
 const input=key==='synthetic'?Study.synthetic():JSON.parse(fs.readFileSync(path.join(web,'projection-data',key+'.json')));
 const reference=key==='synthetic'?Study.syntheticReference():JSON.parse(fs.readFileSync(path.join(web,'reference-data',key+'.json')));
 CT.validate(input);Study.validateReference(reference,input);
 const target=Study.resample(reference.image,96);
 // Hash stored source bytes. Generated floating-point values are compared numerically below.
 const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
 sources[key]=key==='synthetic'?{generator_sha256:hash(path.join(web,'study.js'))}:{input_sha256:hash(path.join(web,'projection-data',key+'.json')),reference_sha256:hash(path.join(web,'reference-data',key+'.json'))};
 for(const [views,selection]of [[360,'spread'],[90,'spread'],[90,'sector']]){
  const selected=CT.selectViews(input.angles_deg.length,views,selection),used=new Set(selected),order=CT.viewOrder(selected),cache=new Map(),baseline=new Float64Array(96**2);
  const matrix=i=>{if(!cache.has(i))cache.set(i,CT.matrixForView(input,96,i));return cache.get(i);};
  for(const i of order)CT.update(matrix(i),baseline,input.sinogram[i]);
  for(const [name,passes,smoothing]of [['First pass',0,0],['1 correction, light smoothing',1,.04],['3 corrections, no smoothing',3,0],['3 corrections, light smoothing',3,.03],['3 corrections, stronger smoothing',3,.1]]){
   const image=baseline.slice();for(let p=0;p<passes;p++){for(const i of order)CT.update(matrix(i),image,input.sinogram[i]);CT.smooth(image,96,smoothing);}
   const x=[[],[]],y=[[],[]];for(let i=0;i<input.angles_deg.length;i++){const predicted=CT.forward(matrix(i),image),g=used.has(i)?0:1;for(let d=0;d<predicted.length;d++){x[g].push(input.sinogram[i][d]);y[g].push(predicted[d]);}}
   results.push({dataset:key,kind:input.kind,views,selection,size:96,method:name,passes,smoothing,image:CT.paired(target,image),selected:CT.paired(x[0],y[0]),unused:x[1].length?CT.paired(x[1],y[1]):null});
  }
  process.stdout.write(`${key}: ${views} ${selection} compared\n`);
 }
}
const report={schema:'ct-benchmark/2',algorithm:CT.VERSION,node:process.version,sources,description:'Three measured HTC objects, four real body slices with simulated projections, and exact analytic disks. Body slices come from two volumes. Authors FBP and source CT references are estimates, not anatomical truth. Each enhancement starts from the same first pass; no reference enters the solver. No smoothing selection or parameter fitting occurs.',results};
if(check){
 const expected=JSON.parse(fs.readFileSync(reportPath));
 if(expected.schema!==report.schema||expected.algorithm!==report.algorithm||expected.results.length!==results.length)throw Error('Benchmark configuration differs.');
 for(const key of Object.keys(sources))if(JSON.stringify(expected.sources[key])!==JSON.stringify(sources[key]))throw Error(`Source provenance differs for ${key}: expected ${JSON.stringify(expected.sources[key])}, received ${JSON.stringify(sources[key])}`);
 for(let i=0;i<results.length;i++)for(const [key,value]of Object.entries(results[i])){
  const old=expected.results[i][key];
  if(value&&typeof value==='object'){
   for(const [metric,v]of Object.entries(value))if(typeof v==='number'?typeof old?.[metric]!=='number'||!Number.isFinite(v)||Math.abs(v-old[metric])>1e-9:v!==old?.[metric])throw Error(`Numerical regression: row ${i}, ${key}.${metric}`);
  }else if(value!==old)throw Error(`Configuration mismatch: row ${i}, ${key}`);
 }
 console.log(`${results.length} benchmark results match the pinned report within 1e-9.`);
 process.exit(0);
}
fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
const lines=['# Live reconstruction benchmark','','Run `node scripts/benchmark_live.cjs` to reproduce the report, or add `--check` to compare all 120 results with the committed values at absolute tolerance 1e-9. Stored input/reference file checksums are recorded. The analytic control records its generator checksum; generated floating-point values are checked numerically.','','Eight samples: three measured HTC2022 objects, four body slices from two real CT volumes with independently simulated projections, and one analytic disk object. HTC references are the authors’ full-data FBP estimates. Body references are the prepared source images, resampled to the 96 × 96 reconstruction grid. Only the disks have known continuous ground truth.','','Each enhancement starts from the same first-pass reconstruction and adds one or three passes. “Best” below means lowest reference RMSE among the four enhancement choices tested; it is not a general ranking or a setting selected by the solver. Unused rays are withheld from updates, but come from the same acquisition or simulation.','','| Sample | Views / selection | First-pass RMSE | Lowest enhanced RMSE | Best tested enhancement |','|---|---|---:|---:|---|'];
for(let i=0;i<results.length;i+=5){const group=results.slice(i,i+5),base=group[0],best=group.slice(1).sort((a,b)=>a.image.rmse-b.image.rmse)[0];lines.push(`| ${base.dataset} | ${base.views} / ${base.selection} | ${base.image.rmse.toFixed(6)} | ${best.image.rmse.toFixed(6)} | ${best.method} |`);}
lines.push('','RMSE units: 1/mm. JSON also records MAE, bias, Pearson correlation, regression slope/intercept, prediction R², and selected/unused ray errors. The 90 consecutive views cover 0–44.5°. Spread selections cover the 360° measured scan or 180° simulated scan. Four slices do not represent four independent patients. No clinical or unseen-patient claim follows from this benchmark.','','Sources: [HTC2022 v1.4.0](https://zenodo.org/records/8041800), Meaney and colleagues (2023), CC BY 4.0; [body CT provenance and licences](BODY_CT.md). Measured patient cone-beam projections are evaluated separately in the [clinical workflow](../clinical/README.md).');
fs.writeFileSync(path.join(__dirname,'../docs/LIVE_BENCHMARK.md'),lines.join('\n')+'\n');
