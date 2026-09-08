/* Calculate the launch figures with the browser's actual measured-data solver. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'..'),web=path.join(root,'src/missing_angle/web');
const CT=require(path.join(web,'projection-core.js'));
const raw=fs.readFileSync(path.join(web,'projection-data/ta.json'));
const input=CT.validate(JSON.parse(raw)),size=96;
const images=['spread','sector'].map(selection=>{
  const selected=CT.selectViews(input.angles_deg.length,90,selection),image=new Float64Array(size*size);
  for(const i of CT.viewOrder(selected))CT.update(CT.matrixForView(input,size,i),image,input.sinogram[i]);
  return {selection,views:90,size,passes:1,smoothing:0,selected,angles:selected.map(i=>input.angles_deg[i]),image:Array.from(image)};
});
process.stdout.write(JSON.stringify({algorithm:CT.VERSION,input_sha256:crypto.createHash('sha256').update(raw).digest('hex'),sample:'Helsinki object A',images}));
