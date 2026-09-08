/* Release checks against the complete generated demo, including its real assets. */
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http');
const {chromium,webkit}=require('playwright');
const {default:AxeBuilder}=require('@axe-core/playwright');
const root=path.resolve(__dirname,'..'),demo=path.join(root,'demo');
async function main(){
 const server=http.createServer(async(req,res)=>{
  try{
   const url=new URL(req.url,'http://localhost'),file=path.resolve(demo,'.'+(url.pathname==='/'?'/index.html':url.pathname));
   if(!file.startsWith(demo+path.sep))throw Error('Invalid path');
   res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json','.png':'image/png','.txt':'text/plain'})[path.extname(file)]||'application/octet-stream');
   res.end(await fs.readFile(file));
  }catch{res.statusCode=404;res.end();}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const engine=process.env.CT_BROWSER==='webkit'?webkit:chromium;
 let browser;
 try{
  browser=await engine.launch();
  const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'light'});
  const page=await context.newPage(),errors=[],requests=[],failures=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
  page.on('response',r=>{if(r.status()>=400)failures.push(r.url());});
  const c=id=>page.locator('#live-'+id);
  async function ready(){await page.waitForFunction(()=>!document.querySelector('#live-start').disabled);}
  async function complete(){await page.waitForFunction(()=>!document.querySelector('#live-download').disabled);}
  async function reflow(){
   const report=await page.evaluate(()=>{
    const result={width:innerWidth,scroll:document.documentElement.scrollWidth};
    if(result.scroll<=result.width)return result;
    result.controls=[...document.querySelectorAll('select,input,button,progress')].map(el=>{const prior=el.style.display;el.style.display='none';const width=document.documentElement.scrollWidth;el.style.display=prior;return {id:el.id,tag:el.tagName,width};}).filter(entry=>entry.width<result.scroll);
    return result;
   });
   assert(report.scroll<=report.width,JSON.stringify(report));
  }
  async function accessibility(stage){
   const r=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
   assert.deepEqual(r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],stage);
   console.log(`${engine.name()} ${stage}: axe passed (${r.passes.length} checks; ${r.incomplete.length} require review)`);
   for(const item of r.incomplete)console.log('Manual review:',item.id,JSON.stringify(item.nodes.map(n=>({target:n.target,summary:n.failureSummary}))));
  }
  await page.goto(origin);await ready();
  assert(!requests.some(url=>url.includes('experiments.json')||url.includes('/assets/')),'Recorded gallery must not load on arrival');
  assert.equal(await page.locator('meta[property="og:image"]').getAttribute('content'),'https://zakimaths.github.io/missing-angle-ct/share-card.png');
  await page.keyboard.press(engine===webkit&&process.platform==='darwin'?'Alt+Tab':'Tab');assert.equal(await page.locator(':focus').innerText(),'Skip to reconstruction controls');
  await page.keyboard.press('Enter');assert.equal(await page.locator(':focus').getAttribute('id'),'live-inputs');
  await accessibility('initial desktop');
  for(const theme of ['pink','dark']) {
   await page.locator('#theme-choice').selectOption(theme);
   await accessibility(theme+' desktop');
   await page.setViewportSize({width:375,height:812});await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   await reflow();
   await accessibility(theme+' mobile');
   await page.setViewportSize({width:1440,height:1000});
  }
  await page.reload();await ready();
  assert.equal(await page.locator('#theme-choice').inputValue(),'dark','Theme preference survives reload');
  // A public shared link sets controls but does not start an unrequested calculation.
  await page.goto(origin+'/?sample=chest-64&views=90&selection=sector&size=64');await ready();
  assert.equal(await c('source').inputValue(),'chest-64');assert.equal(await c('count').inputValue(),'90');
  assert.equal(await c('size').inputValue(),'64');assert.equal(await c('selection').inputValue(),'sector');
  assert(await c('download').isDisabled());
  await c('share').click();const shared=new URL(await c('share-url').inputValue());
  assert.equal(shared.searchParams.get('sample'),'chest-64');assert.equal(shared.searchParams.get('selection'),'sector');
  await c('slow').uncheck();await c('preset-spread').click();await complete();
  assert.equal(await c('count').inputValue(),'90');assert.equal(await c('selection').inputValue(),'spread');assert.equal(await c('size').inputValue(),'96');
  await c('region-name').fill('Boundary');await c('add-label').click();
  await c('refine').click();await complete();await c('first-pass').click();await complete();
  assert.match(await c('labels-list').innerText(),/Boundary/);
  await accessibility('calculated image and checkpoints');
  const pixels=await c('image').evaluate(canvas=>canvas.toDataURL());
  for(const theme of ['pink','light','dark']) {
   await page.locator('#theme-choice').selectOption(theme);
   assert.equal(await c('image').evaluate(canvas=>canvas.toDataURL()),pixels,'Changing appearance preserves reconstructed pixels');
   await accessibility(theme+' calculated state');
  }
  await c('preset-sector').click();await complete();assert.equal(await c('selection').inputValue(),'sector');
  await page.setViewportSize({width:375,height:812});await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  await reflow();
  await accessibility('narrow screen');
  if(process.env.CT_SCREENSHOTS){
   const folder=path.join(root,'output/launch');await fs.mkdir(folder,{recursive:true});
   await page.goto(origin);await ready();await page.screenshot({path:path.join(folder,engine.name()+'-mobile.png')});
   await page.setViewportSize({width:1440,height:1000});await page.goto(origin);await ready();
   await page.screenshot({path:path.join(folder,engine.name()+'-desktop.png')});
  }
  // Recorded comparisons remain usable when explicitly opened.
  await page.locator('#recorded-gallery > summary').click();
  await page.locator('#result').waitFor({state:'visible'});
  assert(requests.some(url=>url.includes('experiments.json')));
  await page.locator('#next').click();assert.equal(await page.locator('#step').inputValue(),'1');
  await accessibility('recorded comparisons');
  await page.goto(origin+'/?sample=unrecognised&views=Infinity');await ready();
  assert(await c('error').isVisible());assert.equal(await c('source').inputValue(),'ta');
  // Pause, step and cancellation must not expose an incomplete export.
  await c('slow').check();await c('start').click();await c('pause').click();
  await page.waitForFunction(()=>document.querySelector('#live-pause').textContent==='Continue');
  await c('one').click();await c('stop').click();assert(await c('download').isDisabled());
  assert(await c('restore-checkpoint').isDisabled());
  // Recover a failed source download with the visible retry action.
  await page.route('**/projection-data/ta.json',route=>route.abort());
  await page.goto(origin);await c('retry').waitFor({state:'visible'});
  assert(await c('start').isDisabled());
  await page.unroute('**/projection-data/ta.json');await c('retry').click();await ready();
  assert(await c('retry').isHidden());
  assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
  console.log(`${engine.name()}: complete demo, shared links, quick comparisons, cancellation, gallery and reflow passed`);
 }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
