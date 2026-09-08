/* Public acquisition links contain settings for bundled samples only. */
(function(root) {
  'use strict';
  const samples = ['ta','tb','tc','chest-64','chest-96','abdomen-400','abdomen-480','synthetic'];
  function read(search) {
    const p = new URLSearchParams(search);
    if (!['sample','views','selection','size'].some(key => p.has(key))) return null;
    const value = {sample:p.get('sample') || 'ta',views:Number(p.get('views') || 90),selection:p.get('selection') || 'spread',size:Number(p.get('size') || 96)};
    if (!samples.includes(value.sample) || !Number.isInteger(value.views) || value.views<4 || value.views>1440 || !['spread','sector'].includes(value.selection) || ![64,96,128].includes(value.size)) throw Error('This experiment link has unsupported settings. The default measured scan is available below.');
    return value;
  }
  function link(sample, options) {
    if (!samples.includes(sample)) throw Error('Links are available for the included samples. Download imported measurements and settings to share a custom run.');
    const p = new URLSearchParams({sample,views:options.views,selection:options.selection,size:options.size});
    read(p.toString());
    return 'https://zakimaths.github.io/missing-angle-ct/?'+p.toString()+'#live-inputs';
  }
  root.CTConfig={read,link,samples};
  if(typeof module!=='undefined')module.exports=root.CTConfig;
})(globalThis);
