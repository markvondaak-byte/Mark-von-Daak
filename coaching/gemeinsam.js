/* =========================================================================
   Coaching — gemeinsame Bausteine
   Datenunabhängige Helfer, die Klienten-App (app.js) und Coach-Ansicht
   (coach/coach.js) teilen: DOM-Helfer, Datumsrechnung, Formatierung,
   Blätter, Karten, Diagramme. Nichts hier greift auf gespeicherte Daten zu.
   ========================================================================= */
'use strict';

/** Verkleinert ein Foto auf höchstens 1000 px Kantenlänge als JPEG. */
/* --- Fotos ----------------------------------------------------------------- */
function fotoVerkleinern(datei, maxKante = 1000) {
  return new Promise((ok, fehler) => {
    const url = URL.createObjectURL(datei);
    const bild = new Image();
    bild.onload = () => {
      const faktor = Math.min(1, maxKante / Math.max(bild.width, bild.height));
      const leinwand = document.createElement('canvas');
      leinwand.width = Math.round(bild.width * faktor);
      leinwand.height = Math.round(bild.height * faktor);
      leinwand.getContext('2d').drawImage(bild, 0, 0, leinwand.width, leinwand.height);
      URL.revokeObjectURL(url);
      leinwand.toBlob((blob) => blob ? ok(blob) : fehler(new Error('Umwandlung fehlgeschlagen')),
                     'image/jpeg', 0.82);
    };
    bild.onerror = () => { URL.revokeObjectURL(url); fehler(new Error('Bild unlesbar')); };
    bild.src = url;
  });
}

/* --- Hilfen ---------------------------------------------------------------- */
const WOCHENTAGE = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];

const WT_KURZ = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];

const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'];

const el = (tag, klasse, text) => {
  const k = document.createElement(tag);
  if (klasse) k.className = klasse;
  if (text != null) k.textContent = text;
  return k;
};

const ikon = (name) => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;

const neueId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);

function knopf(text, klasse, beiKlick, ikonName) {
  const k = el('button', 'knopf' + (klasse ? ' ' + klasse : ''));
  k.type = 'button';
  if (ikonName) k.innerHTML = ikon(ikonName);
  k.append(document.createTextNode(text));
  if (beiKlick) k.onclick = beiKlick;
  return k;
}

function zahl(wert, stellen = 0) {
  if (wert == null || Number.isNaN(wert)) return '–';
  return Number(wert).toLocaleString('de-DE', { minimumFractionDigits: stellen, maximumFractionDigits: stellen });
}

/** Liest eine Zahl aus einem Eingabefeld — Komma oder Punkt. */
function leseZahl(text) {
  if (text == null) return null;
  const s = String(text).trim().replace(',', '.');
  if (s === '') return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function heuteText() { return textAusDatum(new Date()); }

function datumAusText(text) {
  const [j, m, t] = text.split('-').map(Number);
  return new Date(j, m - 1, t);
}

function textAusDatum(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function tageVerschieben(text, anzahl) {
  const d = datumAusText(text);
  d.setDate(d.getDate() + anzahl);
  return textAusDatum(d);
}

function tageZwischen(von, bis) {
  return Math.round((datumAusText(bis) - datumAusText(von)) / 86400000);
}

function datumKurz(text) {
  const d = datumAusText(text);
  return `${d.getDate()}.${d.getMonth() + 1}.`;
}

function datumMittel(text) {
  const d = datumAusText(text);
  return `${WT_KURZ[d.getDay()]}, ${d.getDate()}. ${MONATE[d.getMonth()].slice(0, 3)}.`;
}

function datumLang(text) {
  const d = datumAusText(text);
  return `${WOCHENTAGE[d.getDay()]}, ${d.getDate()}. ${MONATE[d.getMonth()]}`;
}

/** Montag der Woche, in der das Datum liegt. */
function wochenstart(text) {
  const d = datumAusText(text);
  const versatz = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - versatz);
  return textAusDatum(d);
}

function dauerText(ms) {
  const min = Math.round(ms / 60000);
  if (min < 60) return `${min} Min.`;
  return `${Math.floor(min / 60)} Std. ${min % 60} Min.`;
}

function uhrzeit(sekunden) {
  const s = Math.max(0, Math.round(sekunden));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

function toast(text) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = text;
  t.classList.add('toast--an');
  clearTimeout(toast._zeit);
  toast._zeit = setTimeout(() => t.classList.remove('toast--an'), 2400);
}

/** Geschätztes Einwiederholungsmaximum nach Epley. */
/* --- Rechnungen ------------------------------------------------------------ */
function e1rm(kg, wdh) {
  if (!kg || !wdh) return 0;
  return wdh === 1 ? kg : kg * (1 + wdh / 30);
}

function volumen(w) {
  let summe = 0;
  w.uebungen.forEach((u) => u.saetze.forEach((s) => {
    if (s.fertig && s.kg && s.wdh) summe += s.kg * s.wdh;
  }));
  return summe;
}

function schlafDauer(schlaf) {
  if (!schlaf || !schlaf.von || !schlaf.bis) return null;
  const [vh, vm] = schlaf.von.split(':').map(Number);
  const [bh, bm] = schlaf.bis.split(':').map(Number);
  let min = (bh * 60 + bm) - (vh * 60 + vm);
  if (min <= 0) min += 24 * 60;
  return min / 60;
}

/* --- Blatt (Overlay) ------------------------------------------------------- */
function blattOeffnen(titel, aufbauen, { beimSchliessen, kopfExtra } = {}) {
  const halter = document.getElementById('blatt-halter');
  const blatt = el('div', 'blatt');
  blatt.setAttribute('role', 'dialog');
  blatt.setAttribute('aria-modal', 'true');
  blatt.setAttribute('aria-label', titel);

  const kopf = el('div', 'blatt__kopf');
  const zu = el('button', 'ikon-knopf');
  zu.innerHTML = ikon('schliessen');
  zu.setAttribute('aria-label', 'Schließen');
  const ueberschrift = el('h2', null, titel);
  kopf.append(ueberschrift);
  if (kopfExtra) kopf.append(kopfExtra);
  kopf.append(zu);

  const inhalt = el('div', 'blatt__inhalt');
  blatt.append(kopf, inhalt);
  blatt._beimSchliessen = beimSchliessen;
  blatt._titel = ueberschrift;
  const schliessen = () => blattSchliessen(blatt);
  zu.onclick = schliessen;

  halter.append(blatt);
  document.body.style.overflow = 'hidden';
  aufbauen(inhalt, schliessen, blatt);

  // Nur das oberste Blatt schließen, falls zwei übereinanderliegen.
  blatt._escape = (e) => {
    if (e.key === 'Escape' && blatt === halter.lastElementChild) schliessen();
  };
  document.addEventListener('keydown', blatt._escape);
  return blatt;
}

function blattSchliessen(blatt) {
  if (!blatt.isConnected) return;
  document.removeEventListener('keydown', blatt._escape);
  blatt.remove();
  if (!document.querySelector('.blatt')) document.body.style.overflow = '';
  if (blatt._beimSchliessen) blatt._beimSchliessen();
}

/** Blatt-Fußzeile mit festem Knopf, außerhalb des scrollenden Inhalts. */
function blattFuss(blatt, ...knoepfe) {
  const fuss = el('div', 'blatt__fuss');
  if (knoepfe.length > 1) {
    const reihe = el('div', 'reihe');
    reihe.append(...knoepfe);
    fuss.append(reihe);
  } else fuss.append(...knoepfe);
  blatt.append(fuss);
  return fuss;
}

/* --- Bausteine ------------------------------------------------------------- */
function karte(titel, ikonName, zaehler) {
  const k = el('div', 'karte');
  if (titel) {
    const t = el('div', 'karte__titel');
    if (ikonName) t.innerHTML = ikon(ikonName);
    t.append(document.createTextNode(titel));
    if (zaehler != null) t.append(el('span', 'zaehler', zaehler));
    k.append(t);
  }
  return k;
}

function abschnitt(text, link) {
  const t = el('div', 'abschnitt-titel', text);
  if (link) t.append(link);
  return t;
}

function linkKnopf(text, beiKlick, ikonName) {
  const k = el('button', 'link-knopf');
  k.type = 'button';
  k.append(document.createTextNode(text));
  if (ikonName) k.insertAdjacentHTML('beforeend', ikon(ikonName));
  k.onclick = beiKlick;
  return k;
}

function hakenReihe(text, note, aktiv, beiKlick, extra) {
  const reihe = el('div', 'haken-reihe' + (aktiv ? ' haken-reihe--erledigt' : ''));
  const k = el('button', 'haken');
  k.innerHTML = ikon('haken');
  k.setAttribute('aria-pressed', String(aktiv));
  k.setAttribute('aria-label', text);
  const beschriftung = el('div', 'haken-reihe__text');
  beschriftung.append(document.createTextNode(text));
  if (note) beschriftung.append(el('span', 'haken-reihe__note', note));
  k.onclick = () => {
    const neu = k.getAttribute('aria-pressed') !== 'true';
    k.setAttribute('aria-pressed', String(neu));
    reihe.classList.toggle('haken-reihe--erledigt', neu);
    beiKlick(neu);
  };
  reihe.append(k, beschriftung);
  if (extra) reihe.append(extra);
  return reihe;
}

function skala(wert, beiWahl, { von = 1, bis = 5, links, rechts, label = 'Wert' } = {}) {
  const halter = el('div');
  const feld = el('div', 'skala');
  for (let i = von; i <= bis; i++) {
    const k = el('button', null, String(i));
    k.type = 'button';
    k.setAttribute('aria-pressed', String(wert === i));
    k.setAttribute('aria-label', `${label} ${i} von ${bis}`);
    k.onclick = () => {
      feld.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', 'false'));
      k.setAttribute('aria-pressed', 'true');
      beiWahl(i);
    };
    feld.append(k);
  }
  halter.append(feld);
  if (links || rechts) {
    const enden = el('div', 'skala__enden');
    enden.append(el('span', null, links || ''), el('span', null, rechts || ''));
    halter.append(enden);
  }
  return halter;
}

/** Auswahl in Kacheln. optionen: [{id, name, text}] */
function wahl(optionen, aktuell, beiWahl, spalten) {
  const box = el('div', 'wahl' + (spalten ? ` wahl--${spalten}` : ''));
  optionen.forEach((o) => {
    const k = el('button', null, o.name);
    k.type = 'button';
    if (o.text) k.append(el('small', null, o.text));
    k.setAttribute('aria-pressed', String(o.id === aktuell));
    k.onclick = () => {
      box.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', 'false'));
      k.setAttribute('aria-pressed', 'true');
      beiWahl(o.id);
    };
    box.append(k);
  });
  return box;
}

function segment(optionen, aktuell, beiWahl) {
  const box = el('div', 'segment');
  box.setAttribute('role', 'tablist');
  optionen.forEach(([id, name]) => {
    const k = el('button', null, name);
    k.type = 'button';
    k.setAttribute('aria-pressed', String(id === aktuell));
    k.onclick = () => beiWahl(id);
    box.append(k);
  });
  return box;
}

function feld(label, eingabe, hilfe) {
  const f = el('div', 'feld');
  const l = el('label', null, label);
  if (!eingabe.id) eingabe.id = 'f-' + neueId();
  l.htmlFor = eingabe.id;
  f.append(l, eingabe);
  if (hilfe) f.append(el('div', 'feld__hilfe', hilfe));
  return f;
}

function eingabe(typ, wert, { platzhalter, schritt, modus, beiAenderung } = {}) {
  const e = el('input', 'eingabe');
  e.type = typ;
  if (wert != null) e.value = wert;
  if (platzhalter) e.placeholder = platzhalter;
  if (schritt) e.step = schritt;
  if (modus) e.inputMode = modus;
  if (beiAenderung) e.addEventListener('change', () => beiAenderung(e.value));
  return e;
}

function leerzustand(titel, text) {
  const box = el('div', 'leer');
  box.innerHTML = ikon('leer');
  box.append(el('div', 'leer__titel', titel), el('p', null, text));
  return box;
}

function ring(wert, ziel, farbe, zahlText, label, unterLabel, beiKlick) {
  const anteil = ziel ? Math.min(1, (wert || 0) / ziel) : 0;
  const r = 28, umfang = 2 * Math.PI * r;
  const box = el(beiKlick ? 'button' : 'div', 'ring');
  if (beiKlick) {
    box.type = 'button';
    box.style.cssText = 'appearance:none;border:0;background:none;padding:0;cursor:pointer;color:inherit';
    box.onclick = beiKlick;
  }
  const mitte = el('div', 'ring__mitte');
  mitte.innerHTML = `<svg viewBox="0 0 66 66" aria-hidden="true">
    <circle class="ring__spur" cx="33" cy="33" r="${r}"/>
    <circle class="ring__wert" cx="33" cy="33" r="${r}" stroke="${farbe}"
      stroke-dasharray="${umfang.toFixed(1)}" stroke-dashoffset="${(umfang * (1 - anteil)).toFixed(1)}"/>
  </svg>`;
  mitte.append(el('div', 'ring__zahl', zahlText));
  const l = el('div', 'ring__label', label);
  if (unterLabel) { const b = el('b', null, unterLabel); l.prepend(b); }
  box.setAttribute('aria-label', `${label}: ${zahlText} ${unterLabel || ''}`);
  box.append(mitte, l);
  return box;
}

function balkenZeile(name, wert, ziel, einheit, farbe) {
  const z = el('div', 'balken-zeile');
  const kopf = el('div', 'balken-zeile__kopf');
  kopf.append(el('b', null, name), el('span', null, `${zahl(wert)} / ${zahl(ziel)} ${einheit}`));
  const b = el('div', 'balken' + (ziel && wert > ziel * 1.08 ? ' balken--ueber' : ''));
  const i = el('i');
  i.style.width = `${ziel ? Math.min(100, (wert / ziel) * 100) : 0}%`;
  if (farbe) i.style.background = farbe;
  b.append(i);
  z.append(kopf, b);
  return z;
}

function wertKachel(label, zahlText, einheit, delta, gut) {
  const w = el('div', 'wert');
  w.append(el('div', 'wert__label', label));
  const z = el('div', 'wert__zahl', zahlText);
  if (einheit) z.append(el('small', null, einheit));
  w.append(z);
  if (delta) w.append(el('div', 'wert__delta' + (gut ? ' wert__delta--gut' : ''), delta));
  return w;
}

function stepper(wert, { schritt = 1, min = 0, max = 99999, beiAenderung, label }) {
  const box = el('div', 'stepper');
  const minus = el('button'); minus.type = 'button'; minus.innerHTML = ikon('minus');
  minus.setAttribute('aria-label', `${label || 'Wert'} verringern`);
  const plus = el('button'); plus.type = 'button'; plus.innerHTML = ikon('plus');
  plus.setAttribute('aria-label', `${label || 'Wert'} erhöhen`);
  const feldE = eingabe('text', wert, { modus: 'decimal' });
  if (label) feldE.setAttribute('aria-label', label);
  const setzen = (n) => {
    n = Math.min(max, Math.max(min, Math.round(n * 100) / 100));
    feldE.value = zahl(n, n % 1 ? (String(n).split('.')[1] || '').length : 0).replace(/\./g, '');
    beiAenderung(n);
  };
  minus.onclick = () => setzen((leseZahl(feldE.value.replace(/\./g, '')) || 0) - schritt);
  plus.onclick = () => setzen((leseZahl(feldE.value.replace(/\./g, '')) || 0) + schritt);
  feldE.addEventListener('change', () => setzen(leseZahl(feldE.value.replace(/\./g, '')) || 0));
  box.append(minus, feldE, plus);
  return box;
}

/* --- Diagramme ------------------------------------------------------------- */
const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs, klasse) {
  const e = document.createElementNS(SVG_NS, tag);
  if (klasse) e.setAttribute('class', klasse);
  Object.entries(attrs || {}).forEach(([k, v]) => e.setAttribute(k, v));
  return e;
}

/** Linie mit Rohwerten als Punkte und geglättetem Verlauf. */
function liniendiagramm(punkte, { einheit = 'kg', glatt, label }) {
  const b = 320, h = 170, rand = { o: 14, u: 24, l: 46, r: 10 };
  const alle = punkte.map((p) => p.wert).concat(glatt ? glatt.map((p) => p.wert) : []);
  let min = Math.min(...alle), max = Math.max(...alle);
  if (max - min < 1) { min -= 0.5; max += 0.5; }
  const innenB = b - rand.l - rand.r, innenH = h - rand.o - rand.u;
  const t0 = datumAusText(punkte[0].datum).getTime();
  const t1 = datumAusText(punkte[punkte.length - 1].datum).getTime();
  const x = (d) => rand.l + (t1 === t0 ? innenB / 2 : ((datumAusText(d).getTime() - t0) / (t1 - t0)) * innenB);
  const y = (v) => rand.o + innenH - ((v - min) / (max - min)) * innenH;

  const svg = svgEl('svg', { viewBox: `0 0 ${b} ${h}`, role: 'img', 'aria-label': label }, 'diagramm');
  svg.append(svgEl('line', { x1: rand.l, x2: b - rand.r, y1: rand.o + innenH, y2: rand.o + innenH }, 'achse'));

  const reihe = glatt && glatt.length > 1 ? glatt : punkte;
  const pfad = reihe.map((p, i) => `${i ? 'L' : 'M'}${x(p.datum).toFixed(1)},${y(p.wert).toFixed(1)}`).join(' ');
  svg.append(svgEl('path', { d: `${pfad} L${x(reihe[reihe.length - 1].datum).toFixed(1)},${rand.o + innenH} L${x(reihe[0].datum).toFixed(1)},${rand.o + innenH} Z` }, 'flaeche'));
  if (glatt && glatt.length > 1) {
    const roh = punkte.map((p, i) => `${i ? 'L' : 'M'}${x(p.datum).toFixed(1)},${y(p.wert).toFixed(1)}`).join(' ');
    svg.append(svgEl('path', { d: roh }, 'linie linie--roh'));
  }
  svg.append(svgEl('path', { d: pfad }, 'linie'));
  if (punkte.length <= 60) {
    punkte.forEach((p) => svg.append(svgEl('circle', { cx: x(p.datum), cy: y(p.wert), r: 2.6 }, 'punkt')));
  }
  [[max, rand.o + 4], [min, rand.o + innenH - 2]].forEach(([wert, py]) => {
    const t = svgEl('text', { x: 2, y: py }, 'beschriftung');
    t.textContent = `${zahl(wert, 1)} ${einheit}`;
    svg.append(t);
  });
  [[punkte[0].datum, rand.l, 'start'], [punkte[punkte.length - 1].datum, b - rand.r, 'end']].forEach(([d, px, anker]) => {
    const t = svgEl('text', { x: px, y: h - 6, 'text-anchor': anker }, 'beschriftung');
    t.textContent = datumKurz(d);
    svg.append(t);
  });
  return svg;
}

/** Säulen mit optionaler Ziellinie. werte: [{label, wert}] */
function saeulendiagramm(werte, { ziel, einheit = '', label, farbe, stellen = 0 }) {
  const b = 320, h = 150, rand = { o: 16, u: 22, l: 6, r: 6 };
  const max = Math.max(ziel || 0, ...werte.map((w) => w.wert || 0)) * 1.1 || 1;
  const innenB = b - rand.l - rand.r, innenH = h - rand.o - rand.u;
  const breite = innenB / werte.length;
  const svg = svgEl('svg', { viewBox: `0 0 ${b} ${h}`, role: 'img', 'aria-label': label }, 'diagramm');
  svg.style.height = '150px';
  werte.forEach((w, i) => {
    const hoehe = w.wert ? (w.wert / max) * innenH : 0;
    const x = rand.l + i * breite + breite * 0.18;
    const leer = !w.wert;
    const r = svgEl('rect', { x, y: rand.o + innenH - Math.max(hoehe, leer ? 3 : 0), width: breite * 0.64,
      height: Math.max(hoehe, leer ? 3 : 0), rx: 5 }, 'saeule' + (leer ? ' saeule--leer' : ''));
    if (farbe && !leer) r.style.fill = farbe;
    svg.append(r);
    const t = svgEl('text', { x: x + breite * 0.32, y: h - 6, 'text-anchor': 'middle' }, 'beschriftung');
    t.textContent = w.label;
    svg.append(t);
    // Ab 9 Säulen stoßen die Zahlen aneinander — dann trägt die Ziellinie die Aussage.
    if (w.wert && werte.length <= 8) {
      const v = svgEl('text', { x: x + breite * 0.32, y: rand.o + innenH - hoehe - 4, 'text-anchor': 'middle' }, 'beschriftung');
      v.textContent = w.wert >= 10000 ? zahl(w.wert / 1000, 1) + 'k' : zahl(w.wert, stellen);
      svg.append(v);
    }
  });
  if (ziel) {
    const zy = rand.o + innenH - (ziel / max) * innenH;
    svg.append(svgEl('line', { x1: rand.l, x2: b - rand.r, y1: zy, y2: zy }, 'ziel'));
  }
  return svg;
}

/* --- Teilen ---------------------------------------------------------------- */
async function teilen(text, titel) {
  if (navigator.share) {
    try { await navigator.share({ title: titel, text }); return; } catch (e) { if (e.name === 'AbortError') return; }
  }
  kopieren(text);
}

async function kopieren(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast('In die Zwischenablage kopiert');
  } catch (e) {
    const t = el('textarea'); t.value = text; document.body.append(t); t.select();
    try { document.execCommand('copy'); toast('In die Zwischenablage kopiert'); } catch (e2) { toast('Kopieren nicht möglich'); }
    t.remove();
  }
}

/* --- Körpermaße und Fotos ------------------------------------------------ */
const MASSE = [['taille', 'Taille'], ['huefte', 'Hüfte'], ['brust', 'Brust'], ['arm', 'Oberarm'], ['oberschenkel', 'Oberschenkel']];

const POSEN = [['vorn', 'Vorn'], ['seite', 'Seite'], ['hinten', 'Hinten']];

function blobZuDataUrl(blob) {
  return new Promise((ok, fehler) => {
    const r = new FileReader();
    r.onload = () => ok(r.result);
    r.onerror = () => fehler(r.error);
    r.readAsDataURL(blob);
  });
}

/* --- Offline und Updates ------------------------------------------------- */
/** Registriert den Service Worker und bringt Updates ohne mehrfaches Öffnen an.
 *
 *  Der Service Worker liefert die App aus dem Cache. Ein neuer Stand wird im
 *  Hintergrund geladen und übernimmt dann sofort (skipWaiting/claim). Das
 *  meldet controllerchange — daraufhin lädt die Seite neu, sofern dabei nichts
 *  verloren geht. Sonst erscheint ein Hinweis zum Antippen.
 *
 *  darfNeuLaden: optionale Prüfung der Seite, z. B. ob ein Entwurf offen ist. */
function offlineUndUpdates(pfad, { darfNeuLaden } = {}) {
  if (!('serviceWorker' in navigator)) return;
  // Beim allerersten Besuch gibt es noch keinen Service Worker; dessen
  // Übernahme ist kein Update und soll nicht neu laden.
  const hatteSteuerung = !!navigator.serviceWorker.controller;
  let gemeldet = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hatteSteuerung || gemeldet) return;
    gemeldet = true;
    const aktiv = document.activeElement;
    const tipptGerade = aktiv && /^(INPUT|TEXTAREA|SELECT)$/.test(aktiv.tagName);
    const sicher = !document.querySelector('.blatt') && !tipptGerade && (!darfNeuLaden || darfNeuLaden());
    if (sicher) location.reload();
    else updateHinweisZeigen();
  });
  navigator.serviceWorker.register(pfad).then((reg) => {
    // Homescreen-Apps bleiben oft tagelang im Speicher und fragen von sich aus
    // selten nach. Beim Zurückholen in den Vordergrund deshalb nachsehen.
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') reg.update().catch(() => {});
    });
  }).catch((e) => console.warn('Offline-Betrieb nicht verfügbar.', e));
}

function updateHinweisZeigen() {
  if (document.querySelector('.update-hinweis')) return;
  const k = el('button', 'update-hinweis', 'Neue Version bereit — tippen zum Aktualisieren');
  k.type = 'button';
  k.onclick = () => location.reload();
  document.body.append(k);
}
