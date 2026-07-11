const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  await page.fill('#login-email', 'Santi21435@gmail.com');
  await page.fill('#login-password', 'Bichosiuu721@');
  await page.click('.btn-login-submit');
  
  await page.waitForTimeout(3000);
  const layout = await page.evaluate(() => {
     const dash = document.getElementById('dashboard-layout');
     return {
         w: dash.clientWidth,
         h: dash.clientHeight,
         sidebar: document.querySelector('.sidebar').clientWidth,
         main: document.querySelector('.workspace').clientWidth,
         dashDisplay: window.getComputedStyle(dash).display,
         dashOpacity: window.getComputedStyle(dash).opacity
     };
  });
  console.log("Layout:", layout);
  
  await browser.close();
})();
