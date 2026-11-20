// Erzeugt personal-training/firmenfitness/infoblatt.pdf aus _infoblatt.html.
//
//     node tools/infoblatt_pdf.js
//
// Braucht Playwright mit Chromium. Die Quelle `_infoblatt.html` wird vom
// Build nicht veröffentlicht (Dateien mit „_“ am Anfang bleiben draußen),
// nur das fertige PDF.
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const ordner = path.join(__dirname, '..', 'personal-training', 'firmenfitness');

(async () => {
  const browser = await chromium.launch();
  const seite = await browser.newPage();
  await seite.goto(pathToFileURL(path.join(ordner, '_infoblatt.html')).href);
  await seite.evaluate(() => document.fonts.ready);
  await seite.pdf({ path: path.join(ordner, 'infoblatt.pdf'), printBackground: true, preferCSSPageSize: true });
  await browser.close();
  console.log(path.join(ordner, 'infoblatt.pdf'));
})();
