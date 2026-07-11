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
  const display = await page.evaluate(() => {
     return {
         login: document.getElementById('login-screen').style.display,
         dashboard: document.getElementById('dashboard-layout').style.display,
         dashboardClasses: document.getElementById('dashboard-layout').className,
         bodyClasses: document.body.className
     };
  });
  console.log("DOM State:", display);
  
  await browser.close();
})();
