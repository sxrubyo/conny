const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  
  const state = await page.evaluate(() => {
     return {
         btnCount: document.querySelectorAll('#btn-switch-to-dev').length,
         btnDisplay: window.getComputedStyle(document.getElementById('btn-switch-to-dev')).display
     };
  });
  console.log("State:", state);
  
  await browser.close();
})();
