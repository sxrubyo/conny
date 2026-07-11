const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('LOG:', msg.text()));
  
  await page.goto('http://localhost:8003/login');
  
  await page.evaluate(() => {
     document.addEventListener('click', e => {
         console.log("Global click on:", e.target.id || e.target.tagName);
     });
  });
  
  await page.click('#btn-switch-to-dev');
  
  await page.waitForTimeout(500);
  
  await browser.close();
})();
