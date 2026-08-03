/* Service Worker — macht die App offline nutzbar.
   Strategie: App-Hülle und Daten beim ersten Aufruf in den Cache legen und
   danach zuerst von dort ausliefern. Das ist hier richtig, weil sich die
   Inhalte nur bei einem neuen Release ändern — dann wird VERSION erhöht und
   der alte Cache verworfen. */

const VERSION = 'stoffwechsel-reset-v3';

const DATEIEN = [
  './',
  './index.html',
  './app.css',
  './app.js',
  './manifest.webmanifest',
  './daten/programm.json',
  './daten/rezepte.json',
  './daten/wissen.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(VERSION)
      .then((cache) => cache.addAll(DATEIEN))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((namen) => Promise.all(
        namen.filter((n) => n !== VERSION).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;

  e.respondWith(
    caches.match(e.request).then((treffer) => {
      if (treffer) return treffer;
      return fetch(e.request)
        .then((antwort) => {
          // Nur eigene, erfolgreiche Antworten nachlegen.
          if (antwort.ok && antwort.type === 'basic') {
            const kopie = antwort.clone();
            caches.open(VERSION).then((cache) => cache.put(e.request, kopie));
          }
          return antwort;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
