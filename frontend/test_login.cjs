const puppeteer = require('puppeteer');

async function testLoginFlow() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  page.on('response', res => {
    if (res.url().includes('/api/v1/products') && res.request().method() === 'GET') {
      console.log(`[API ${res.status()}] GET /products`);
    }
  });

  console.log('Navigating to /login...');
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle0' });
  
  console.log('Filling login form...');
  await page.type('input[type="email"]', 'merchant@demo.com');
  await page.type('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  console.log('Waiting for navigation to dashboard...');
  await page.waitForNavigation({ waitUntil: 'networkidle0' });
  
  console.log('Navigating to /catalogue...');
  await page.goto('http://localhost:5173/catalogue', { waitUntil: 'networkidle0' });
  
  await new Promise(r => setTimeout(r, 2000));
  
  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  console.log('Token in localStorage:', !!token);
  
  const dashText = await page.evaluate(() => document.body.innerText);
  console.log('Has products?:', dashText.includes('Apex Audio')); // checking for product or brand text
  
  await browser.close();
}

testLoginFlow().catch(console.error);
