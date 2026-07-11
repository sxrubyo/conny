const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  
  const layout = await page.evaluate(() => {
     const dash = document.getElementById('dashboard-layout');
     return {
         isChildOfLogin: document.getElementById('login-screen').contains(dash),
         parentTag: dash ? dash.parentElement.tagName : 'NULL',
         parentId: dash ? dash.parentElement.id : 'NULL'
     };
  });
  console.log("Nested State:", layout);
  
  await browser.close();
})();
