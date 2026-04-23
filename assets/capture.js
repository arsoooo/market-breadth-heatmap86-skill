#!/usr/bin/env node

const path = require('path');

async function main() {
  const args = process.argv.slice(2);
  const htmlPath = args[0];
  const outputPath = args[1];
  const width = parseInt(args[2]) || 1080;
  const height = parseInt(args[3]) || 1440;
  const dpr = parseInt(args[4]) || 2;

  if (!htmlPath || !outputPath) {
    console.error('Usage: node capture.js <html> <png> [width] [height] [dpr]');
    process.exit(1);
  }

  let chromium;
  try {
    chromium = require('playwright').chromium;
  } catch {
    console.error('Playwright not found. Run: npx playwright install chromium');
    process.exit(1);
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: dpr,
  });
  const page = await context.newPage();

  const fileUrl = 'file://' + path.resolve(htmlPath);
  await page.goto(fileUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);

  await page.screenshot({
    path: path.resolve(outputPath),
    type: 'png',
  });

  await browser.close();
  console.log('OK: ' + path.resolve(outputPath) + ` (${width * dpr}x${height * dpr} actual pixels, ${dpr}x DPR)`);
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
