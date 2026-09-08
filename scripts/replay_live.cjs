/* Headless replay of the exact kernel used by the live browser and Mac app. */
const fs=require('node:fs'),path=require('node:path'),CT=require('../src/missing_angle/web/projection-core.js');
const args=process.argv.slice(2),file=args[0],output=args.indexOf('--output');
try {
  if(!file)throw Error('Usage: node scripts/replay_live.cjs INPUT.json [--output RUN.json]');
  if(fs.statSync(file).size>16*1024*1024)throw Error('Input exceeds 16 MB.');
  const saved=JSON.parse(fs.readFileSync(file,'utf8')),replay=saved.schema==='ct-reconstruction/1',input=CT.validate(replay?saved.input:saved);
  const options=CT.settings(replay?saved.options:{size:96,views:Math.min(360,input.angles_deg.length),selection:'spread',passes:3,smoothing:.03},input.angles_deg.length);
  if(options.views*input.sinogram[0].length*options.size>14000000)throw Error('Workload exceeds the browser budget.');
  const refinements=replay?saved.refinements:[{passes:3,smoothing:.03}];
  if(!Array.isArray(refinements)||refinements.length>12)throw Error('Invalid refinement stages.');
  for(const r of refinements)CT.settings({...options,...r},input.angles_deg.length);
  if(replay&&(saved.algorithm!==CT.VERSION||!Array.isArray(saved.image)||saved.image.length!==options.size**2||!saved.image.every(Number.isFinite)))throw Error('Unsupported saved algorithm or image.');
  const selected=CT.selectViews(input.angles_deg.length,options.views,options.selection),order=CT.viewOrder(selected),cache=new Map(),image=new Float64Array(options.size**2);
  function pass(smoothing){for(const v of order){if(!cache.has(v))cache.set(v,CT.matrixForView(input,options.size,v));CT.update(cache.get(v),image,input.sinogram[v]);}CT.smooth(image,options.size,smoothing);}
  pass(0);const baseline=image.slice();for(const r of refinements)for(let p=0;p<r.passes;p++)pass(r.smoothing);
  const max_difference=replay?Math.max(...image.map((v,k)=>Math.abs(v-saved.image[k]))):null;
  const result={schema:'ct-reconstruction/1',algorithm:CT.VERSION,input,options,selected,order,refinements,image:Array.from(image),baseline:Array.from(baseline),replay:{maximum_absolute_difference:max_difference,tolerance:1e-9,matched:replay?max_difference<=1e-9:null}};
  if(output>=0){const target=args[output+1];fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(result)+'\n');}
  console.log(JSON.stringify({dataset:input.name,views:options.views,size:options.size,refinements,replay:result.replay}));
  if(replay&&max_difference>1e-9)process.exitCode=1;
}catch(error){console.error(error.message);process.exitCode=2;}
