/* Deterministic 2D ray-length projector and nonnegative SART. No image reference input. */
(function (root) {
  'use strict';
  const VERSION = 'ray-sart-1';
  function finite(x) { return typeof x === 'number' && Number.isFinite(x); }
  function validate(input) {
    if (!input || input.schema !== 'ct-projections/1') throw Error('Choose a compatible projection file containing detector readings, acquisition angles and scanner geometry.');
    const {angles_deg: angles, sinogram: sino, geometry: g} = input;
    if (!Array.isArray(angles) || angles.length < 4 || angles.length > 1440 || !angles.every(a => finite(a) && Math.abs(a) <= 3600)) throw Error('Provide 4 to 1440 finite angles in degrees.');
    if (!Array.isArray(sino) || sino.length !== angles.length || !Array.isArray(sino[0])) throw Error('One sinogram row is required for every angle.');
    const detectors = sino[0].length;
    if (detectors < 16 || detectors > 512 || !sino.every(row => Array.isArray(row) && row.length === detectors && row.every(v => finite(v) && Math.abs(v) <= 100))) throw Error('Each view needs the same 16 to 512 detector readings, with finite line-integral values between −100 and 100.');
    if (!g || !['fan', 'parallel'].includes(g.type) || !finite(g.fov_mm) || g.fov_mm < 1 || g.fov_mm > 1000 || !finite(g.detector_spacing_mm) || g.detector_spacing_mm < .01 || g.detector_spacing_mm > 20) throw Error('Provide fan or parallel geometry, field of view (1 to 1000 mm) and detector spacing (0.01 to 20 mm).');
    if (g.type === 'fan' && (!finite(g.source_distance_mm) || !finite(g.detector_distance_mm) || g.source_distance_mm <= g.fov_mm || g.detector_distance_mm <= g.fov_mm || g.source_distance_mm > 10000 || g.detector_distance_mm > 10000)) throw Error('Fan geometry needs source-to-origin and origin-to-detector distances larger than the field of view and at most 10000 mm.');
    if (typeof input.name !== 'string' || input.name.length > 160) throw Error('Provide a short dataset name (up to 160 characters).');
    return input;
  }
  function settings(options, count) {
    const o = {...options};
    if (![64, 96, 128].includes(o.size) || !Number.isInteger(o.views) || o.views < 4 || o.views > count || !['spread', 'sector'].includes(o.selection)) throw Error('Invalid image size, view count or angle selection.');
    if (!Number.isInteger(o.passes) || o.passes < 1 || o.passes > 6 || !finite(o.smoothing) || o.smoothing < 0 || o.smoothing > .15) throw Error('Choose 1 to 6 refinement passes and smoothing between 0 and 0.15.');
    return o;
  }
  function selectViews(count, wanted, selection) {
    return Array.from({length: wanted}, (_, k) => selection === 'sector' ? k : Math.floor(k * count / wanted));
  }
  function viewOrder(indices) {
    // Deterministic distributed ordering; visits each selected acquisition exactly once per pass.
    const count = indices.length;
    return indices.map((index, rank) => ({index, key: (rank * .6180339887498949) % 1})).sort((a,b) => a.key-b.key || a.index-b.index).map(v => v.index);
  }
  function rayEndpoints(g, angle, detector, count) {
    const a = angle * Math.PI / 180, s = Math.sin(a), c = Math.cos(a);
    const u = (detector - (count-1)/2) * g.detector_spacing_mm;
    if (g.type === 'fan') return [s*g.source_distance_mm, -c*g.source_distance_mm, -s*g.detector_distance_mm + c*u, c*g.detector_distance_mm + s*u];
    const extent = g.fov_mm * 2;
    return [c*u + s*extent, s*u - c*extent, c*u - s*extent, s*u + c*extent];
  }
  function traceRay(g, size, endpoints) {
    const [sx,sy,ex,ey] = endpoints, dx=ex-sx, dy=ey-sy, half=g.fov_mm/2, pixel=g.fov_mm/size;
    let lo=0, hi=1;
    for (const [start,dir] of [[sx,dx],[sy,dy]]) {
      if (Math.abs(dir)<1e-12) { if (start < -half || start > half) return [[],[]]; }
      else { const t1=(-half-start)/dir,t2=(half-start)/dir; lo=Math.max(lo,Math.min(t1,t2)); hi=Math.min(hi,Math.max(t1,t2)); }
    }
    if (hi<=lo) return [[],[]];
    const cuts=[lo,hi];
    for(let k=1;k<size;k++) {
      const boundary=-half+k*pixel;
      if(Math.abs(dx)>1e-12) {const t=(boundary-sx)/dx;if(t>lo&&t<hi)cuts.push(t);}
      if(Math.abs(dy)>1e-12) {const t=(boundary-sy)/dy;if(t>lo&&t<hi)cuts.push(t);}
    }
    cuts.sort((a,b)=>a-b);
    const indices=[],weights=[],length=Math.hypot(dx,dy);
    for(let k=0;k<cuts.length-1;k++) {
      const dt=cuts[k+1]-cuts[k];if(dt<1e-12)continue;
      const mid=(cuts[k]+cuts[k+1])/2;
      const col=Math.min(size-1,Math.max(0,Math.floor((sx+mid*dx+half)/pixel)));
      const row=Math.min(size-1,Math.max(0,Math.floor((half-sy-mid*dy)/pixel)));
      indices.push(row*size+col);weights.push(dt*length);
    }
    return [indices,weights];
  }
  function matrixForView(input,size,index) {
    const rowPtr=[0],indices=[],weights=[],rows=new Float64Array(input.sinogram[0].length),cols=new Float64Array(size*size);
    for(let d=0;d<rows.length;d++) {
      const [idx,w]=traceRay(input.geometry,size,rayEndpoints(input.geometry,input.angles_deg[index],d,rows.length));
      for(let j=0;j<idx.length;j++){indices.push(idx[j]);weights.push(w[j]);rows[d]+=w[j];cols[idx[j]]+=w[j];}
      rowPtr.push(indices.length);
    }
    return {ptr:Uint32Array.from(rowPtr),index:Uint16Array.from(indices),weight:Float64Array.from(weights),rows,cols};
  }
  function forward(matrix,image) {
    const out=new Float64Array(matrix.rows.length);
    for(let r=0;r<out.length;r++)for(let j=matrix.ptr[r];j<matrix.ptr[r+1];j++)out[r]+=matrix.weight[j]*image[matrix.index[j]];
    return out;
  }
  function update(matrix,image,measured,relaxation=.25) {
    const predicted=forward(matrix,image),correction=new Float64Array(image.length);
    for(let r=0;r<predicted.length;r++) {
      if(matrix.rows[r]<1e-12)continue;
      const residual=(measured[r]-predicted[r])/matrix.rows[r];
      for(let j=matrix.ptr[r];j<matrix.ptr[r+1];j++)correction[matrix.index[j]]+=matrix.weight[j]*residual;
    }
    for(let k=0;k<image.length;k++)if(matrix.cols[k]>1e-12)image[k]=Math.max(0,image[k]+relaxation*correction[k]/matrix.cols[k]);
    return image;
  }
  function smooth(image,size,strength) {
    if(!strength)return image;
    const original=image.slice();
    for(let y=0;y<size;y++)for(let x=0;x<size;x++) {
      const k=y*size+x;let sum=0,count=0;
      if(x>0){sum+=original[k-1];count++;}if(x<size-1){sum+=original[k+1];count++;}
      if(y>0){sum+=original[k-size];count++;}if(y<size-1){sum+=original[k+size];count++;}
      image[k]=(1-strength)*original[k]+strength*sum/count;
    }
    return image;
  }
  // Descriptive paired statistics: x is reference/measured, y is reconstructed/predicted.
  // Pearson correlation alone cannot detect scale or offset errors.
  function paired(x,y) {
    if(!x.length||x.length!==y.length)throw Error('Paired arrays must have the same nonzero length.');
    let mx=0,my=0,xx=0,yy=0,xy=0,se=0,ae=0,energy=0;
    for(let i=0;i<x.length;i++){
      if(!finite(x[i])||!finite(y[i]))throw Error('Statistics require finite values.');
      const dx=x[i]-mx,dy=y[i]-my;mx+=dx/(i+1);my+=dy/(i+1);
      xx+=dx*(x[i]-mx);yy+=dy*(y[i]-my);xy+=dx*(y[i]-my);
      const e=y[i]-x[i];se+=e*e;ae+=Math.abs(e);energy+=x[i]*x[i];
    }
    return {n:x.length,rmse:Math.sqrt(se/x.length),mae:ae/x.length,bias:my-mx,
      relative:energy>0?Math.sqrt(se/energy):null,
      correlation:xx>0&&yy>0?Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy))):null,
      slope:xx>0?xy/xx:null,intercept:xx>0?my-xy/xx*mx:null,
      r2:xx>0?1-se/xx:null};
  }
  const api={VERSION,validate,settings,selectViews,viewOrder,rayEndpoints,traceRay,matrixForView,forward,update,smooth,paired};
  root.CT=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
