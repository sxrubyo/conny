const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err));
  
  await page.goto('http://localhost:8003/login');
  
  // Try to login
  await page.fill('#login-email', 'Santi21435@gmail.com');
  await page.fill('#login-password', 'Bichosiuu721@');
  
  console.log('Clicking login...');
  await page.click('.btn-login-submit');
  
  await page.waitForTimeout(2000);
  
  const currentUrl = page.url();
  console.log('Current URL after click:', currentUrl);
  
  // Output any errors in the UI
  const errorText = await page.locator('#login-error').innerText();
  if (errorText) console.log('Login Error UI:', errorText);
  
  await browser.close();
})();
