const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  
  // Click API Access
  await page.click('#btn-switch-to-dev');
  
  await page.waitForTimeout(500);
  
  const state = await page.evaluate(() => {
     return {
         modalDisplay: window.getComputedStyle(document.getElementById('dev-login-modal')).display,
         modalOpacity: window.getComputedStyle(document.getElementById('dev-login-modal')).opacity
     };
  });
  console.log("State:", state);
  
  await browser.close();
})();
