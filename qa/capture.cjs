/* Capture real browser interactions. No result images or completion states are injected. */
const {chromium}=require('playwright');
const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
const destination=path.resolve(__dirname,'../output/playwright/social');
const origin=process.env.CT_URL||'https://zakimaths.github.io/missing-angle-ct/';
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function main(){
 await fs.mkdir(path.join(destination,'raw'),{recursive:true});
 const browser=await chromium.launch();
 const evidence=[];
 try {
  for(const sample of ['ta','abdomen-400']) {
   const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'light',recordVideo:{dir:path.join(destination,'raw'),size:{width:1440,height:1000}}});
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
   const c=id=>page.locator('#live-'+id);
   const shot=async name=>{await page.screenshot({path:path.join(destination,name+'.png')});};
   const ready=()=>page.waitForFunction(()=>!document.querySelector('#live-start').disabled);
   const done=()=>page.waitForFunction(()=>!document.querySelector('#live-download').disabled);
   const workspace=async()=>{await page.locator('.live-workspace').evaluate(el=>el.scrollIntoView({block:'start'}));await page.evaluate(()=>scrollBy(0,-100));};
   await page.goto(origin);await ready();
   if(sample==='ta') {
    for(const theme of ['light','pink','dark']) {
     await page.locator('#theme-choice').selectOption(theme);await page.evaluate(()=>scrollTo(0,0));await delay(300);
     await shot('overview-'+theme);
    }
    await page.locator('#theme-choice').selectOption('light');
   } else {await page.locator('#theme-choice').selectOption('dark');await c('source').selectOption(sample);await ready();}
   await c('count').fill('360');await c('count').press('Tab');await c('size').selectOption('96');await c('slow').check();
   await page.locator('.view-library > summary').click();await c('page-next').click();await delay(900);
   await c('start').click();await workspace();
   await page.waitForFunction(()=>Number(document.querySelector('#live-progress').value)>0);
   const first=await c('image').evaluate(el=>el.toDataURL());
   await done();await delay(1200);
   const final=await c('image').evaluate(el=>el.toDataURL());assert.notEqual(first,final,'Actual reconstruction must change on screen');
   await workspace();await page.locator('.live-workspace').screenshot({path:path.join(destination,(sample==='ta'?'measured-reconstruction':'body-reconstruction')+'.png')});
   const description=await c('source-info').innerText();
   if(sample==='ta') {
    await c('refine').click();await workspace();await done();await delay(1000);
    await page.locator('#live-analysis-title').evaluate(el=>el.scrollIntoView({block:'start'}));await page.evaluate(()=>scrollBy(0,-24));await shot('error-analysis');await page.locator('#live-reference-figures').screenshot({path:path.join(destination,'reference-comparison.png')});
    await c('run-name').fill('Helsinki object A: 360 measured views');
    await c('region-name').fill('Central feature');await c('add-label').click();
    await page.locator('#live-label-title').evaluate(el=>el.scrollIntoView({block:'start'}));await page.evaluate(()=>scrollBy(0,-24));await delay(900);await shot('region-labels');
   }
   await delay(1200);assert.deepEqual(errors,[]);
   const video=page.video();await context.close();
   const name=sample==='ta'?'measured-reconstruction':'body-reconstruction';
   await video.saveAs(path.join(destination,name+'.webm'));
   evidence.push({sample,description,views:360,size:96,source:origin,video:name+'.webm',actual_frames_differ:true,page_errors:errors});
  }
  const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,colorScheme:'light'});
  const page=await context.newPage();await page.goto(origin);await page.waitForFunction(()=>!document.querySelector('#live-start').disabled);
  await page.locator('#theme-choice').selectOption('dark');await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(destination,'mobile-dark.png')});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await context.close();
  await fs.writeFile(path.join(destination,'capture-evidence.json'),JSON.stringify({captured_at:new Date().toISOString(),runs:evidence},null,2)+'\n');
  console.log('Captured nine screenshots and two real reconstruction recordings at '+destination);
 } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
