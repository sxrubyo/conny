const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', error => console.log('BROWSER ERROR:', error.message));
  
  await page.goto('http://localhost:8003/login');
  await page.fill('#login-email', 'Santi21435@gmail.com');
  await page.fill('#login-password', 'Bichosiuu721@');
  await page.click('.btn-login-submit');
  
  await page.waitForTimeout(3000);
  console.log("Current URL:", page.url());
  
  await browser.close();
})();
