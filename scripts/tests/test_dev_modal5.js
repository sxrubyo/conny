const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => {
      if (msg.type() === 'error') {
          console.log('LOG ERROR:', msg.text());
      }
  });
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  await page.goto('http://localhost:8003/login');
  await page.waitForTimeout(1000);
  
  await browser.close();
})();
