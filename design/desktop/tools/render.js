const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const root = path.join(__dirname, '..'); const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, 'jobs.json')));
(async () => { const b = await chromium.launch();
  for (const [w, h, save] of [[1100, 760, true], [720, 520, true], [1600, 1000, false]]) for (const theme of save ? ['light', 'night'] : ['light']) {
    const p = await (await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1, colorScheme: theme === 'night' ? 'dark' : 'light' })).newPage();
    for (const j of jobs) {
      await p.goto('file://' + path.join(root, 'mockups', j.lang, j.name + '.html'));
      await p.evaluate(() => { document.documentElement.setAttribute('data-still', ''); return document.fonts.ready; }); await p.waitForTimeout(60);
      const ov = await p.evaluate(() => [document.documentElement.scrollWidth - innerWidth, document.documentElement.scrollHeight - innerHeight]);
      if (ov[0] > 0 || ov[1] > 0) console.log('OVERFLOW', w, j.lang, j.name, ov);
      const d = path.join(root, 'mockups/png', `${w}x${h}`, theme, j.lang); fs.mkdirSync(d, { recursive: true });
      await p.screenshot({ path: path.join(d, j.name + '.png') }); }
    await p.context().close(); }
  await b.close(); })();
