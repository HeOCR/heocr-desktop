const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const jobs = JSON.parse(fs.readFileSync(process.argv[2]));
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ deviceScaleFactor: 1 })).newPage();
  for (const j of jobs) {
    const svg = fs.readFileSync(j.svg, 'utf8');
    await page.setViewportSize({ width: j.w || j.px, height: j.h || j.px });
    await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:100vw;height:100vh}</style>${svg}`);
    fs.mkdirSync(path.dirname(j.out), { recursive: true });
    await page.screenshot({ path: j.out, omitBackground: !!j.transparent });
  }
  await b.close();
})();
