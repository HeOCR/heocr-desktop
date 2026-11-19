const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const jobs = JSON.parse(fs.readFileSync(path.join(__dirname, 'store_jobs.json')));
(async () => {
  const b = await chromium.launch();
  for (const theme of ['light', 'night']) {
    const ctx = await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2, colorScheme: theme === 'night' ? 'dark' : 'light' });
    const page = await ctx.newPage();
    for (const c of jobs.captures.filter(c => c.theme === theme)) {
      await page.goto('file://' + c.page);
      await page.evaluate((sel) => { document.documentElement.setAttribute('data-still', '');
        if (sel) { const r = document.querySelector(sel).getBoundingClientRect(); window.scrollTo(0, r.top + window.scrollY - 330); }
        return document.fonts.ready; }, c.sel);
      await page.waitForTimeout(80);
      await page.screenshot({ path: c.out });
    }
    await ctx.close();
  }
  const ctx = await b.newContext({ deviceScaleFactor: 1 }); const page = await ctx.newPage();
  for (const c of jobs.compositions) {
    await page.setViewportSize({ width: c.w, height: c.h });
    await page.goto('file://' + c.html); await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(80);
    fs.mkdirSync(path.dirname(c.out), { recursive: true });
    await page.screenshot({ path: c.out });
  }
  await b.close();
})();
