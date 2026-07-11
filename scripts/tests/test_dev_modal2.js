const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('LOG:', msg.text()));
  page.on('pageerror', err => console.log('ERROR:', err.message));
  
  await page.goto('http://localhost:8003/login');
  
  await page.click('#btn-switch-to-dev');
  
  await page.waitForTimeout(500);
  
  const state = await page.evaluate(() => {
     return {
         btn: !!document.getElementById('btn-switch-to-dev'),
         modal: !!document.getElementById('dev-login-modal'),
         display: window.getComputedStyle(document.getElementById('dev-login-modal')).display
     };
  });
  console.log("State:", state);
  
  await browser.close();
})();
