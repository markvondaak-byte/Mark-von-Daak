// Erzeugt die Druckvorlagen unter unterlagen/ aus unterlagen/vorlagen/*.html.
//
//     node tools/unterlagen_pdf.js
//
// Braucht Playwright mit Chromium. Die Unterlagen gehören nicht zur Website.
const fs = require('fs');
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

  // Optional: Fassung mit Bankverbindung aus unterlagen/bank.json (gitignored).
  // Ergibt unterlagen/Rechnung-Mark.html (zum Ausfüllen) und Rechnung-Vorlage-Bank.pdf.
  const bankDatei = path.join(wurzel, 'bank.json');
  if (fs.existsSync(bankDatei)) {
    const bank = JSON.parse(fs.readFileSync(bankDatei, 'utf8'));
    const attr = (t) => String(t).replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    let html = fs.readFileSync(path.join(wurzel, 'vorlagen', 'rechnung.html'), 'utf8');
    for (const id of ['inhaber', 'iban', 'bic', 'bank']) {
      if (!bank[id]) continue;
      const muster = new RegExp('<input id="' + id + '"[^>]*>');
      if (!muster.test(html)) throw new Error('Feld ' + id + ' nicht gefunden');
      html = html.replace(muster, '<input id="' + id + '" value="' + attr(bank[id]) + '">');
    }
    // Pfade zu Schriften gelten von unterlagen/ aus eine Ebene höher
    html = html.split('../../personal-training/').join('../personal-training/');
    const privat = path.join(wurzel, 'Rechnung-Mark.html');
    fs.writeFileSync(privat, html);
    console.log(privat);
    await seite.goto(pathToFileURL(privat).href + '?leer');
    await seite.evaluate(() => document.fonts.ready);
    const ziel = path.join(wurzel, 'Rechnung-Vorlage-Bank.pdf');
    await seite.pdf({ path: ziel, printBackground: true, preferCSSPageSize: true });
    console.log(ziel);
  }
  await browser.close();
})();
