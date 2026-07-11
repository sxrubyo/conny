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
     const children = Array.from(document.body.children);
     return children.map(c => ({
         id: c.id,
         tag: c.tagName,
         w: c.clientWidth,
         h: c.clientHeight,
         display: window.getComputedStyle(c).display,
         className: c.className
     }));
  });
  console.log("Body Children:", layout);
  
  await browser.close();
})();
