// Liest alle Produkte aus dem offiziellen FitLine-Shop (Deutschland) und
// schreibt sie als JSON nach stdout. Der Shop lädt seine Daten erst im
// Browser, deshalb läuft das über Playwright (Chromium).
// Aufruf über: python3 rechnungen/kataloge/fitline_aktualisieren.py
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ locale: 'de-DE' });
  const anfrage = page.waitForRequest(r => r.url().includes('/api2/shops/de/products/'), { timeout: 90000 });
  await page.goto('https://www.fitline.com/de/de-de/products', { waitUntil: 'domcontentloaded', timeout: 90000 });
  const kopf = (await anfrage.catch(() => { throw new Error('Produktabfrage des Shops nicht gefunden – Seite geändert?'); })).headers();
  await page.waitForLoadState('networkidle').catch(() => {});
  const h = {};
  for (const [k, v] of Object.entries(kopf)) if (!k.startsWith(':') && !['host', 'content-length'].includes(k)) h[k] = v;
  const alle = [];
  for (let s = 1; s < 50; s++) {
    const url = 'https://www.fitline.com/api2/shops/de/products/?locale=de-de&page=' + s +
      '&perPage=50&tags=pim%3Aautoship%3Aregularorderonly&tags=pim%3Aautoship%3Aboth&isAutoship=false&isLeafletItem=false';
    const d = await page.evaluate(async ([u, k]) => {
      const r = await fetch(u, { headers: k });
      return r.ok ? r.json() : { fehler: r.status };
    }, [url, h]);
    if (d.fehler) throw new Error('HTTP ' + d.fehler);
    alle.push(...d.productCatalog.results);
    if (s >= d.productCatalog.paginationInfo.totalPages) break;
  }
  process.stdout.write(JSON.stringify(alle));
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
