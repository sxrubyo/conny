const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  
  await page.goto('http://localhost:8003/login');
  await page.fill('#login-email', 'Santi21435@gmail.com');
  await page.fill('#login-password', 'Bichosiuu721@');
  await page.click('.btn-login-submit');
  
  await page.waitForTimeout(3000);
  
  // Click agendados
  await page.click('.nav-item[data-view="appointments"]');
  
  await page.waitForTimeout(1000);
  
  const state = await page.evaluate(() => {
     return {
         appointmentsActive: document.getElementById('view-appointments').classList.contains('active'),
         appointmentsDisplay: window.getComputedStyle(document.getElementById('view-appointments')).display,
         chatsDisplay: window.getComputedStyle(document.getElementById('view-chats')).display
     };
  });
  console.log("State:", state);
  
  await browser.close();
})();
