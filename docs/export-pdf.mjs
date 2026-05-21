import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { marked } from 'marked';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mdPath = path.join(__dirname, 'PROJECT_REPORT.md');
const pdfPath = path.join(__dirname, 'PROJECT_REPORT.pdf');
const screenshotPath = path.join(__dirname, 'assets/frontend-screenshot.png');

const md = fs.readFileSync(mdPath, 'utf8');
const screenshotData = fs.readFileSync(screenshotPath).toString('base64');

let htmlBody = marked.parse(md);
htmlBody = htmlBody.replace(
  'assets/frontend-screenshot.png',
  `data:image/png;base64,${screenshotData}`,
);

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Project Report</title>
  <style>
    @page { margin: 2.2cm; size: A4; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.45;
      color: #111;
      max-width: 100%;
    }
    h1 { font-size: 22pt; margin-top: 0; page-break-before: always; }
    h1:first-of-type { page-break-before: auto; }
    h2 { font-size: 15pt; margin-top: 1.2em; page-break-before: always; }
    h3 { font-size: 12pt; }
    table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
    th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
    th { background: #f5f5f5; }
    code, pre { font-family: Menlo, Monaco, Consolas, monospace; font-size: 9pt; }
    pre {
      background: #f6f8fa;
      padding: 10px;
      border-radius: 4px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }
    img { max-width: 100%; height: auto; margin: 1em auto; display: block; }
    hr { border: none; border-top: 1px solid #ddd; margin: 1.5em 0; }
    blockquote { border-left: 3px solid #ddd; margin: 1em 0; padding-left: 1em; color: #444; }
    ul, ol { padding-left: 1.4em; }
    div[align="center"] { text-align: center; }
  </style>
</head>
<body>${htmlBody}</body>
</html>`;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.setContent(html, { waitUntil: 'networkidle' });
await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
});
await browser.close();

console.log(`PDF written to ${pdfPath}`);
