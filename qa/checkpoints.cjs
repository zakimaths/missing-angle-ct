/* Exercise the shipped lab through controls and exported files, with a real worker. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const os = require('node:os');
const {execFileSync} = require('node:child_process');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const web = path.join(root, 'src/missing_angle/web');
async function main() {
  const panel = await fs.readFile(path.join(web, 'live-panel.html'), 'utf8');
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Reconstruction checks</title><link rel="stylesheet" href="/live.css"></head><body><main>${panel}</main><script src="/projection-core.js"></script><script src="/study.js"></script><script src="/live.js"></script></body></html>`;
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      if (pathname === '/') { res.setHeader('Content-Type', 'text/html'); res.end(html); return; }
      const file = path.resolve(web, '.' + pathname);
      if (!file.startsWith(web + path.sep)) throw Error('Invalid path');
      res.setHeader('Content-Type', ({'.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)] || 'application/octet-stream');
      res.end(await fs.readFile(file));
    } catch { res.statusCode = 404; res.end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'ct-checkpoints-'));
  let browser;
  try {
    browser = await chromium.launch();
    const page = await browser.newPage({viewport: {width: 1280, height: 900}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const control = name => page.locator('#live-' + name);
    const ready = () => page.waitForFunction(() => !document.querySelector('#live-start').disabled && !document.querySelector('#live-download').disabled);
    async function download() {
      const waiting = page.waitForEvent('download');
      await control('download').click();
      return JSON.parse(await fs.readFile(await (await waiting).path(), 'utf8'));
    }
    for (const key of ['ta', 'chest-64', 'synthetic']) {
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      await control('source').selectOption(key);
      await page.waitForFunction(() => !document.querySelector('#live-start').disabled);
      await control('size').selectOption('64');
      await control('count').fill('12');
      await control('count').press('Tab');
      await control('slow').uncheck();
      await control('start').click(); await ready();
      const baseline = await download();
      const firstPixels = await control('image').screenshot();
      await control('region-name').fill('Feature <test>');
      await control('add-label').click();
      await control('passes').selectOption('1');
      await control('smoothing').selectOption('0.03');
      await control('refine').click(); await ready();
      await control('checkpoint-name').fill('Light smoothing');
      await control('rename-checkpoint').click();
      const a = await download();
      await control('first-pass').click(); await ready();
      assert.deepEqual((await download()).image, baseline.image);
      assert.deepEqual(await control('image').screenshot(), firstPixels);
      await control('smoothing').selectOption('0');
      await control('passes').selectOption('3');
      await control('refine').click(); await ready();
      await control('checkpoint-name').fill('Corrections only');
      await control('rename-checkpoint').click();
      const b = await download();
      assert.deepEqual(b.refinements, [{passes:3,smoothing:0}]);
      assert.equal(b.evaluation.stages.length, 3);
      assert.equal(b.evaluation.stages[1].parent, 0);
      assert.equal(b.evaluation.stages[2].parent, 0);
      assert.equal(b.evaluation.stages[2].name, 'Corrections only');
      assert(b.evaluation.stages.every(stage => Number.isFinite(stage.image.rmse)));
      assert(b.evaluation.stages.every(stage => stage.regions[0].name === 'Feature <test>'));
      await control('checkpoint').selectOption('1');
      await control('restore-checkpoint').click(); await ready();
      assert.deepEqual((await download()).image, a.image);
      assert.match(await control('labels-list').innerText(), /Feature <test>/);
      const exported = path.join(temporary, key + '.json');
      await fs.writeFile(exported, JSON.stringify(b));
      execFileSync(process.execPath, [path.join(root, 'scripts/replay_live.cjs'), exported]);
      await control('file').setInputFiles(exported);
      await control('start').click(); await ready();
      await page.waitForFunction(() => document.querySelector('#live-status').textContent.includes('Saved-run replay: matches'));
      const replay = await download();
      assert.deepEqual(replay.image, b.image);
      assert.deepEqual(replay.labels, b.labels);
      assert.equal(replay.checkpoint_name, b.checkpoint_name);
      await page.setViewportSize({width: 375, height: 812});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.setViewportSize({width: 1280, height: 900});
      console.log(`${key}: exact restoration, independent branches, stage scores, labels and export/replay passed`);
    }
    await control('file').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{}')});
    await page.waitForFunction(() => document.querySelector('#live-status').textContent.includes('No input loaded'));
    assert(await control('start').isDisabled());
    assert(await control('restore-checkpoint').isDisabled());
    assert(await control('download').isDisabled());
    await control('source').selectOption('ta');
    await page.waitForFunction(() => !document.querySelector('#live-start').disabled);
    assert.deepEqual(errors, []);
    console.log('Invalid import recovery and browser error checks passed.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
    await fs.rm(temporary, {recursive:true, force:true});
  }
}
main().catch(error => {console.error(error);process.exitCode=1;});
