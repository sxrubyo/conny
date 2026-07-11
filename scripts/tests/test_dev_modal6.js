const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('http://localhost:8003/login');
  
  const state = await page.evaluate(() => {
     return {
         btn: typeof btnSwitchToDev,
         btnValue: btnSwitchToDev === null,
         modal: typeof devLoginModal,
         modalValue: devLoginModal === null
     };
  });
  console.log("State:", state);
  
  await browser.close();
})();
