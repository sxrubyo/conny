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
     return {
         bw: document.body.clientWidth,
         bh: document.body.clientHeight,
         dashboardClasses: document.getElementById('dashboard-layout').className
     };
  });
  console.log("Body Layout:", layout);
  
  await browser.close();
})();
