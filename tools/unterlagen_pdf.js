// Erzeugt die Druckvorlagen unter unterlagen/ aus unterlagen/vorlagen/*.html.
//
//     node tools/unterlagen_pdf.js
//
// Braucht Playwright mit Chromium. Die Unterlagen gehören nicht zur Website.
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const wurzel = path.join(__dirname, '..', 'unterlagen');
const vorlagen = [
  ['trainingsplan-blanko.html', 'Trainingsplan-Blanko.pdf'],
  ['rechnung.html?leer', 'Rechnung-Vorlage.pdf'],
];

(async () => {
  const browser = await chromium.launch();
  const seite = await browser.newPage();
  for (const [quelle, ziel] of vorlagen) {
    const [datei, abfrage] = quelle.split('?');
    await seite.goto(pathToFileURL(path.join(wurzel, 'vorlagen', datei)).href + (abfrage ? '?' + abfrage : ''));
    await seite.evaluate(() => document.fonts.ready);
    await seite.pdf({ path: path.join(wurzel, ziel), printBackground: true, preferCSSPageSize: true });
    console.log(path.join(wurzel, ziel));
  }
  await browser.close();
})();
