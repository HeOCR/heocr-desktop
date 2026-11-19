// 200% font-scale check: Android WebView applies the system font scale as text zoom (text only, not layout).
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const root = path.join(__dirname, '..');
(async () => {
  const b = await chromium.launch();
  for (const lang of ['he', 'en']) {
    const ctx = await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    for (const n of ['01-home', '03-reading', '04-result', '06-result-more', '08-problem-needs-converter', '11-about']) {
      await page.goto('file://' + path.join(root, 'mockups', lang, n + '.html'));
      await page.addStyleTag({ content: 'html{-webkit-text-size-adjust:200% !important;text-size-adjust:200% !important}' }).catch(e => console.log('style blocked', e.message.slice(0, 80)));
      await page.evaluate(() => { document.documentElement.setAttribute('data-still', ''); return document.fonts.ready; });
      await page.waitForTimeout(100);
      const d = path.join(root, 'mockups/png/font-scale-200', lang); fs.mkdirSync(d, { recursive: true });
      await page.screenshot({ path: path.join(d, n + '.png'), fullPage: n !== '06-result-more' && n !== '04-result' });
      const m = await page.evaluate(() => ({ fs: getComputedStyle(document.querySelector('.btn, .lede, p')).fontSize, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth }));
      console.log(lang, n, JSON.stringify(m));
    }
    await ctx.close();
  }
  await b.close();
})();
