// Render an .excalidraw file to SVG + PNG locally (no CDN): node render.mjs in.excalidraw
import { chromium } from 'playwright';
import fs from 'fs'; import path from 'path';
const inp = process.argv[2];
const data = JSON.parse(fs.readFileSync(inp, 'utf8'));
const lib = fs.readFileSync(new URL('./node_modules/@excalidraw/utils/dist/excalidraw-utils.min.js', import.meta.url), 'utf8');
const browser = await chromium.launch({ executablePath: fs.readdirSync('/opt/pw-browsers').filter(d=>d.startsWith('chromium-')).map(d=>`/opt/pw-browsers/${d}/chrome-linux/chrome`)[0] });
const page = await browser.newPage({ deviceScaleFactor: 2 });
page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
await page.setContent('<html><body style="margin:0;background:#fff"></body></html>');
await page.addScriptTag({ content: lib });
const svg = await page.evaluate(async (d) => {
  const el = await window.ExcalidrawUtils.exportToSvg({ elements: d.elements, appState: { ...d.appState, exportBackground: true, viewBackgroundColor: '#ffffff' }, files: d.files || {} });
  document.body.appendChild(el); return el.outerHTML;
}, data);
const base = inp.replace(/\.excalidraw$/, '');
fs.writeFileSync(base + '.svg', svg);
const box = await page.locator('svg').first().boundingBox();
await page.setViewportSize({ width: Math.ceil(box.width), height: Math.ceil(box.height) });
await page.locator('svg').first().screenshot({ path: base + '.png' });
await browser.close();
console.log('wrote', base + '.svg', base + '.png', Math.round(box.width), 'x', Math.round(box.height));
