const { chromium, devices } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    ...devices['iPhone 12']
  });
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  await page.screenshot({ path: 'mobile_login.png' });
  
  await browser.close();
})();
