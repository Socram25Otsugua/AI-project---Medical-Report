import path from 'node:path';
import { fileURLToPath } from 'node:url';
import playwright from '../promptfoo/node_modules/playwright/index.js';

const { chromium } = playwright;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(__dirname, 'assets/frontend-screenshot.png');

const screenshotStyles = `
  input, select, textarea, .fieldInput, .checkRow, .chatComposerInput,
  .sidebarSearch, .formCard, .fields, .field {
    background: #ffffff !important;
    background-color: #ffffff !important;
    box-shadow: none !important;
    outline: none !important;
  }
  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
    box-shadow: 0 0 0 1000px #ffffff inset !important;
    -webkit-text-fill-color: #0b192e !important;
  }
  *:focus, *:focus-visible {
    outline: none !important;
    box-shadow: none !important;
  }
`;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' });
await page.addStyleTag({ content: screenshotStyles });

const fillField = async (label, value) => {
  const field = page.locator('label.field', { has: page.locator('.fieldLabel', { hasText: label }) }).locator('input, textarea').first();
  if (await field.count()) {
    await field.fill(value);
  }
};

await fillField('Full name', 'Maria');
await fillField('Birthdate / CPR', '2507974321');
await fillField('Nationality', 'Portuguese');
await fillField('UTC time', '04:18');
await fillField('Ship name', 'MV Nordvind');
await fillField('Satellite call no.', '+870 123456789');
await fillField('Coordinates', '55.6761° N, 12.5683° E');

await page.waitForTimeout(600);
await page.screenshot({ path: out, fullPage: false });
await browser.close();
console.log(`Saved ${out}`);
