const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const root = path.join(__dirname, '..');
const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, 'screen_jobs.json')));
const only = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const sizes = [[412, 915], [360, 800]];
  for (const [w, h] of sizes) for (const theme of ['light', 'night']) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, colorScheme: theme === 'night' ? 'dark' : 'light' });
    const page = await ctx.newPage();
    for (const j of jobs) {
      if (only && !j.name.startsWith(only)) continue;
      await page.goto('file://' + path.join(root, 'mockups', j.lang, j.name + '.html'));
      await page.evaluate(() => { document.documentElement.setAttribute('data-still', ''); return document.fonts.ready; });
      await page.waitForTimeout(80);
      if (j.name.startsWith('12')) await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
      const dir = path.join(root, 'mockups/png', `${w}x${h}`, theme, j.lang); fs.mkdirSync(dir, { recursive: true });
      await page.screenshot({ path: path.join(dir, j.name + '.png') });
      const ov = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (ov > 0) console.log('H-OVERFLOW', w, theme, j.lang, j.name, ov);
      if ((j.name === '04-result' || j.name === '11-about') && w === 412) {
        const d2 = path.join(root, 'mockups/png/full-length', theme, j.lang); fs.mkdirSync(d2, { recursive: true });
        await page.screenshot({ path: path.join(d2, j.name + '-full.png'), fullPage: true });
      }
    }
    await ctx.close();
  }
  await b.close();
})();
