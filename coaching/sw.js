/* Service Worker — macht die App offline nutzbar.
   Strategie: App-Hülle und Daten beim ersten Aufruf
   in den Cache legen und danach zuerst von dort ausliefern. Bei jedem
   Release VERSION erhöhen, sonst sehen bestehende Nutzer das Update nie. */

const VERSION = 'coaching-v2';

const DATEIEN = [
  './',
  './index.html',
  './app.css',
  './app.js',
  './manifest.webmanifest',
  './daten/uebungen.json',
  './daten/lebensmittel.json',
  './daten/rezepte.json',
  './icons/icon-180.png',
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
        namen.filter((n) => n.startsWith('coaching-') && n !== VERSION).map((n) => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  // Nur eigene Dateien — WhatsApp- und Mail-Links gehen am Cache vorbei.
  if (new URL(e.request.url).origin !== self.location.origin) return;

  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((treffer) => {
      if (treffer) return treffer;
      return fetch(e.request)
        .then((antwort) => {
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
