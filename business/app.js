/* =========================================================================
   FitLine Business — Kontakte & Follow-up

   Kein Framework, kein Build, keine Abhängigkeiten zur Laufzeit. Reines
   JavaScript, genau wie die Programm-App nebenan — damit beide mit denselben
   Handgriffen wartbar bleiben.

   Alle Daten liegen im localStorage des Geräts. Das ist hier keine
   Bequemlichkeit, sondern Absicht: In dieser Datenbank stehen Namen,
   Telefonnummern und Notizen zu echten Menschen. Ohne Server gibt es keinen
   Ort, an dem sie außerhalb dieses Geräts liegen könnten.
   ========================================================================= */
'use strict';

/* --- Speicher ----------------------------------------------------------- */
const SCHLUESSEL = 'fitline-business.v1';

/* Voreinstellungen der Follow-up-Kadenz, alle in Tagen.
   Sie sind der eigentliche Motor der App: Aus einer Statusänderung wird
   automatisch der nächste Schritt mit Datum. Wer andere Rhythmen fährt,
   stellt sie unter Einstellungen um. */
const VORGABEN = {
  nachErstkontakt:   3,
  nachTermin:        2,
  nachPraesentation: 2,
  nachEntscheidung:  4,
  produktcheck:     10,
  nachbestellung:   30,
  startgespraech:    7,
  betreuungKunde:   60,
  betreuungPartner: 21,
  geburtstagVorlauf: 14,
  laendervorwahl:  '49'
};

const Speicher = {
  daten: null,

  leer() {
    return {
      version: 1,
      kontakte: [],
      aufgaben: [],
      einstellungen: Object.assign({}, VORGABEN)
    };
  },

  laden() {
    try {
      this.daten = JSON.parse(localStorage.getItem(SCHLUESSEL)) || null;
    } catch (e) {
      console.warn('Gespeicherte Daten unlesbar, starte neu.', e);
      this.daten = null;
    }
    if (!this.daten) this.daten = this.leer();
    this.aufraeumen();
    return this.daten;
  },

  /* Fehlende Felder ergänzen. Das erspart eine echte Migration, wenn später
     etwas dazukommt: Ein alter Datensatz bekommt die neuen Felder beim
     nächsten Start, ohne dass irgendwo undefined durchschlägt. */
  aufraeumen() {
    const d = this.daten;
    if (!Array.isArray(d.kontakte)) d.kontakte = [];
    if (!Array.isArray(d.aufgaben)) d.aufgaben = [];
    d.einstellungen = Object.assign({}, VORGABEN, d.einstellungen || {});
    d.kontakte.forEach((k) => {
      if (!Array.isArray(k.verlauf)) k.verlauf = [];
      if (!Array.isArray(k.tags)) k.tags = [];
      if (!k.typ) k.typ = 'interessent';
      if (!k.angelegt) k.angelegt = heuteText();
    });
    d.aufgaben.forEach((a) => {
      if (typeof a.erledigt !== 'boolean') a.erledigt = false;
    });
  },

  sichern() {
    try {
      localStorage.setItem(SCHLUESSEL, JSON.stringify(this.daten));
    } catch (e) {
      // Privates Surfen oder voller Speicher: nicht abstürzen, aber melden —
      // hier gehen sonst unbemerkt Kundendaten verloren.
      console.warn('Speichern fehlgeschlagen.', e);
      meldung('Speichern fehlgeschlagen — Speicher voll?');
    }
  },

  zuruecksetzen() {
    localStorage.removeItem(SCHLUESSEL);
    this.daten = this.leer();
  }
};

/* --- Farbmodus ----------------------------------------------------------- */
/* Drei Zustände: 'system' folgt dem Gerät, 'hell' und 'dunkel' überstimmen es.
   Eigener Schlüssel, damit die Wahl ein Zurücksetzen der Daten überlebt und
   das Skript im <head> sie lesen kann, ohne alles zu parsen. */
const MODUS_SCHLUESSEL = 'fitline-business.modus';

const Modus = {
  gewaehlt() {
    try { return localStorage.getItem(MODUS_SCHLUESSEL) || 'system'; }
    catch (e) { return 'system'; }
  },

  systemIstDunkel() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  },

  anwenden() {
    const wahl = this.gewaehlt();
    const dunkel = wahl === 'dunkel' || (wahl === 'system' && this.systemIstDunkel());
    document.documentElement.dataset.theme = dunkel ? 'dark' : 'light';
    const marke = document.querySelector('meta[name="theme-color"]');
    if (marke) marke.setAttribute('content', dunkel ? '#0F1615' : '#0E6B70');
  },

  setzen(wahl) {
    try {
      if (wahl === 'system') localStorage.removeItem(MODUS_SCHLUESSEL);
      else localStorage.setItem(MODUS_SCHLUESSEL, wahl);
    } catch (e) { /* privates Surfen: Wahl gilt dann nur für diese Sitzung */ }
    this.anwenden();
  },

  beobachten() {
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => {
        if (this.gewaehlt() === 'system') this.anwenden();
      });
  }
};

/* --- Begriffe ------------------------------------------------------------ */
const TYPEN = {
  interessent: 'Interessent',
  kunde:       'Kunde',
  partner:     'Teampartner',
  ruhend:      'Ruhend'
};

/* Die Strecke vom ersten Namen bis zur Entscheidung. Bewusst kurz gehalten:
   Fünf Stufen kann man im Kopf behalten, zwölf pflegt niemand. */
const STUFEN = [
  ['neu',           'Neu erfasst',        'Name steht in der Liste, sonst nichts'],
  ['kontaktiert',   'Erstkontakt',        'Angesprochen, Interesse geklärt'],
  ['termin',        'Termin steht',       'Gespräch oder Präsentation vereinbart'],
  ['praesentation', 'Vorgestellt',        'Produkt oder Geschäft gezeigt, Probe läuft'],
  ['entscheidung',  'Entscheidung offen', 'Alles gesagt — es fehlt das Ja']
];
const STUFENNAME = Object.fromEntries(STUFEN.map(([w, n]) => [w, n]));

const ARTEN = {
  anruf:         ['Anruf',           'telefon'],
  nachricht:     ['Nachricht',       'nachricht'],
  treffen:       ['Treffen',         'treffen'],
  produktcheck:  ['Produkt-Check',   'paket'],
  nachbestellung:['Nachbestellung',  'paket'],
  geburtstag:    ['Geburtstag',      'geschenk'],
  sonstige:      ['Sonstiges',       'stift']
};

const QUELLEN = {
  empfehlung:    'Empfehlung',
  direkt:        'Direkt angesprochen',
  social:        'Social Media',
  veranstaltung: 'Veranstaltung',
  bestand:       'Bestandskunde',
  wieder:        'Wiederaufnahme',
  sonstige:      'Sonstige'
};

/* --- Zustand ------------------------------------------------------------ */
const App = {
  ansicht: 'heute',
  kontaktFilter: 'alle',
  kontaktSuche: '',
  kontaktSortierung: 'schritt',
  aufgabenFilter: 'offen',
  sucheFokussieren: false
};

/* --- Hilfen ------------------------------------------------------------- */
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

const neueId = () =>
  Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);

function heuteDatum() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function textAusDatum(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function datumAusText(text) {
  const [j, m, t] = String(text).split('-').map(Number);
  return new Date(j, m - 1, t);
}

const heuteText = () => textAusDatum(heuteDatum());

function plusTage(tage, ab) {
  const d = ab ? datumAusText(ab) : heuteDatum();
  d.setDate(d.getDate() + tage);
  return textAusDatum(d);
}

/** Tage von heute bis zum Datum. Negativ heißt: liegt in der Vergangenheit. */
function tageBis(text) {
  if (!text) return null;
  return Math.round((datumAusText(text) - heuteDatum()) / 86400000);
}

function datumKurz(text) {
  if (!text) return '';
  const d = datumAusText(text);
  return `${d.getDate()}.${d.getMonth() + 1}.${String(d.getFullYear()).slice(2)}`;
}

function datumLang(text) {
  const d = datumAusText(text);
  return `${WOCHENTAGE[d.getDay()]}, ${d.getDate()}. ${MONATE[d.getMonth()]} ${d.getFullYear()}`;
}

/** „heute", „morgen", „seit 4 Tagen überfällig", „Di, 12.8." */
function faelligText(text) {
  const t = tageBis(text);
  if (t === null) return '';
  if (t === 0) return 'heute';
  if (t === 1) return 'morgen';
  if (t === -1) return 'seit gestern überfällig';
  if (t < 0) return `seit ${-t} Tagen überfällig`;
  if (t <= 6) return `in ${t} Tagen · ${WT_KURZ[datumAusText(text).getDay()]}`;
  return datumKurz(text);
}

function vorTagenText(text) {
  const t = tageBis(text);
  if (t === null) return '—';
  if (t === 0) return 'heute';
  if (t === -1) return 'gestern';
  if (t < 0) return `vor ${-t} Tagen`;
  return datumKurz(text);
}

const zahl = (n) => Number(n).toLocaleString('de-DE');

function name(k) {
  return [k.vorname, k.nachname].filter(Boolean).join(' ').trim() || 'Ohne Namen';
}

function initialen(k) {
  const a = (k.vorname || '').trim()[0] || '';
  const b = (k.nachname || '').trim()[0] || '';
  return (a + b).toUpperCase() || '?';
}

/** Telefonnummer für wa.me: nur Ziffern, führende Null wird zur Vorwahl. */
function whatsappNummer(nummer) {
  if (!nummer) return null;
  let n = String(nummer).replace(/[^\d+]/g, '');
  const vorwahl = Speicher.daten.einstellungen.laendervorwahl || '49';
  if (n.startsWith('+')) n = n.slice(1);
  else if (n.startsWith('00')) n = n.slice(2);
  else if (n.startsWith('0')) n = vorwahl + n.slice(1);
  return n.length >= 8 ? n : null;
}

/* --- Abfragen über den Datenbestand -------------------------------------- */
function kontakt(id) {
  return Speicher.daten.kontakte.find((k) => k.id === id) || null;
}

function aktiveKontakte() {
  return Speicher.daten.kontakte.filter((k) => !k.archiviert);
}

function offeneAufgaben(kontaktId) {
  return Speicher.daten.aufgaben.filter((a) =>
    !a.erledigt && (!kontaktId || a.kontaktId === kontaktId));
}

/** Die nächste offene Aufgabe eines Kontakts — das „was steht als Nächstes an". */
function naechsterSchritt(kontaktId) {
  return offeneAufgaben(kontaktId)
    .sort((a, b) => a.faellig.localeCompare(b.faellig))[0] || null;
}

function letzterKontaktDatum(k) {
  if (!k.verlauf.length) return null;
  return k.verlauf.map((e) => e.datum).sort().slice(-1)[0];
}

/** Aufgaben, die heute oder früher fällig sind — sortiert, älteste zuerst. */
function faelligeAufgaben() {
  const h = heuteText();
  return offeneAufgaben()
    .filter((a) => a.faellig <= h)
    .sort((a, b) => a.faellig.localeCompare(b.faellig));
}

function ueberfaellig() {
  const h = heuteText();
  return faelligeAufgaben().filter((a) => a.faellig < h);
}

function heuteFaellig() {
  const h = heuteText();
  return offeneAufgaben().filter((a) => a.faellig === h);
}

/** Geburtstage in den nächsten N Tagen, Jahreswechsel eingerechnet. */
function geburtstageDemnaechst(tage) {
  const heute = heuteDatum();
  const treffer = [];
  aktiveKontakte().forEach((k) => {
    if (!k.geburtstag) return;
    const teile = k.geburtstag.split('-').map(Number);
    const monat = teile.length === 3 ? teile[1] : teile[0];
    const tagImMonat = teile.length === 3 ? teile[2] : teile[1];
    if (!monat || !tagImMonat) return;

    let naechster = new Date(heute.getFullYear(), monat - 1, tagImMonat);
    if (naechster < heute) naechster = new Date(heute.getFullYear() + 1, monat - 1, tagImMonat);
    const inTagen = Math.round((naechster - heute) / 86400000);
    if (inTagen <= tage) treffer.push({ kontakt: k, inTagen, datum: naechster });
  });
  return treffer.sort((a, b) => a.inTagen - b.inTagen);
}

/** Kunden, deren üblicher Bestellrhythmus abgelaufen ist.
 *
 *  Wer dafür schon eine offene Erinnerung hat, taucht hier nicht auf: Der
 *  Fall steht dann bereits im Follow-up, und zweimal dasselbe zu melden
 *  macht beide Listen unglaubwürdig.
 */
function nachbestellungFaellig() {
  const grenze = Speicher.daten.einstellungen.nachbestellung;
  return aktiveKontakte()
    .filter((k) => k.typ === 'kunde' && k.letzteBestellung && !k.autoship)
    .filter((k) => !offeneAufgaben(k.id).some((a) => a.art === 'nachbestellung'))
    .map((k) => ({ kontakt: k, tage: -tageBis(plusTage(grenze, k.letzteBestellung)) }))
    .filter((x) => x.tage >= 0)
    .sort((a, b) => b.tage - a.tage);
}

/** Kunden und Partner, bei denen zu lange nichts passiert ist.
 *
 *  Ein Kontakt, für den in den nächsten Tagen ohnehin etwas geplant ist, gilt
 *  nicht als vernachlässigt — sonst steht er auf der Mahnliste, obwohl der
 *  Termin schon im Kalender steht.
 */
function betreuungFaellig() {
  const e = Speicher.daten.einstellungen;
  const bald = plusTage(7);
  return aktiveKontakte()
    .filter((k) => k.typ === 'kunde' || k.typ === 'partner')
    .filter((k) => !offeneAufgaben(k.id).some((a) => a.faellig <= bald))
    .map((k) => {
      const letzter = letzterKontaktDatum(k);
      const grenze = k.typ === 'partner' ? e.betreuungPartner : e.betreuungKunde;
      const tage = letzter ? -tageBis(letzter) : -tageBis(k.angelegt);
      return { kontakt: k, tage, grenze };
    })
    .filter((x) => x.tage >= x.grenze)
    .sort((a, b) => b.tage - a.tage);
}

/** Aktive Kontakte ohne offene Aufgabe — das klassische Leck im Vertrieb. */
function ohneNaechstenSchritt() {
  return aktiveKontakte()
    .filter((k) => k.typ !== 'ruhend')
    .filter((k) => !naechsterSchritt(k.id));
}

/* --- Kadenz: aus einem Status wird der nächste Schritt ------------------- */
/** Was nach einer Status- oder Stufenänderung als Nächstes ansteht.
 *
 *  Gibt {art, text, tage} zurück oder null, wenn sich nichts aufdrängt.
 *  Der Aufrufer entscheidet, ob daraus eine Aufgabe wird — angelegt wird sie
 *  nur, wenn für den Kontakt ohnehin nichts Offenes vorliegt. Sonst stapeln
 *  sich bei jedem Antippen neue Erinnerungen.
 */
function kadenzVorschlag(k) {
  const e = Speicher.daten.einstellungen;
  if (k.typ === 'kunde') {
    return { art: 'produktcheck', tage: e.produktcheck,
             text: 'Nachfassen: Wie kommt er mit den Produkten zurecht?' };
  }
  if (k.typ === 'partner') {
    return { art: 'treffen', tage: e.startgespraech,
             text: 'Startgespräch und erste Schritte durchgehen' };
  }
  if (k.typ === 'ruhend') return null;

  switch (k.stufe) {
    case 'neu':
      return { art: 'anruf', tage: 1, text: 'Erstkontakt aufnehmen' };
    case 'kontaktiert':
      return { art: 'anruf', tage: e.nachErstkontakt,
               text: 'Nachfassen und Termin vereinbaren' };
    case 'termin':
      return { art: 'treffen', tage: e.nachTermin, text: 'Termin durchführen' };
    case 'praesentation':
      return { art: 'anruf', tage: e.nachPraesentation,
               text: 'Nachfassen: offene Fragen klären' };
    case 'entscheidung':
      return { art: 'anruf', tage: e.nachEntscheidung,
               text: 'Entscheidung nachfassen' };
    default:
      return null;
  }
}

/** Legt den Kadenz-Vorschlag als Aufgabe an, sofern nichts Offenes existiert. */
function kadenzAnlegen(k) {
  if (naechsterSchritt(k.id)) return null;
  const v = kadenzVorschlag(k);
  if (!v) return null;
  const a = aufgabeAnlegen(k.id, plusTage(v.tage), v.art, v.text);
  return a;
}

/* --- Schreibende Vorgänge ------------------------------------------------ */
function aufgabeAnlegen(kontaktId, faellig, art, text) {
  const a = {
    id: neueId(), kontaktId, faellig, art: art || 'anruf',
    text: text || '', erledigt: false, erledigtAm: null, erstellt: heuteText()
  };
  Speicher.daten.aufgaben.push(a);
  Speicher.sichern();
  return a;
}

function verlaufAnlegen(kontaktId, art, text, datum) {
  const k = kontakt(kontaktId);
  if (!k) return null;
  const eintrag = { id: neueId(), datum: datum || heuteText(), art: art || 'sonstige', text: text || '' };
  k.verlauf.push(eintrag);
  Speicher.sichern();
  return eintrag;
}

/** Aufgabe abhaken: sie wandert in den Verlauf des Kontakts und die Kadenz
 *  schlägt den nächsten Schritt vor. Genau das ist der Unterschied zwischen
 *  einer Aufgabenliste und einem Follow-up-System. */
function aufgabeErledigen(a, mitVerlauf) {
  a.erledigt = true;
  a.erledigtAm = heuteText();
  if (mitVerlauf !== false) {
    verlaufAnlegen(a.kontaktId, a.art, a.text || ARTEN[a.art][0]);
  }
  Speicher.sichern();
  const k = kontakt(a.kontaktId);
  if (k) return kadenzAnlegen(k);
  return null;
}

function aufgabeVerschieben(a, tage) {
  // Ab heute, nicht ab dem alten Termin: Eine dreimal verschobene Aufgabe soll
  // in einer Woche wieder auftauchen und nicht rückwirkend schon wieder
  // überfällig sein.
  const basis = a.faellig < heuteText() ? heuteText() : a.faellig;
  a.faellig = plusTage(tage, basis);
  Speicher.sichern();
}

function kontaktLoeschen(id) {
  Speicher.daten.kontakte = Speicher.daten.kontakte.filter((k) => k.id !== id);
  Speicher.daten.aufgaben = Speicher.daten.aufgaben.filter((a) => a.kontaktId !== id);
  // Verweise anderer Kontakte auf den gelöschten auflösen, sonst zeigt der
  // Teambaum ins Leere.
  Speicher.daten.kontakte.forEach((k) => {
    if (k.sponsor === id) k.sponsor = '';
    if (k.empfehlungVon === id) k.empfehlungVon = '';
  });
  Speicher.sichern();
}

/* --- Blatt (Overlay) ---------------------------------------------------- */
/** Öffnet ein Vollbild-Blatt. `aufbauen(inhalt, schliessen, neu)` füllt es;
 *  `neu()` zeichnet dasselbe Blatt noch einmal — nötig, weil sich Kontakte
 *  im Blatt selbst ändern (Stufe setzen, Aufgabe abhaken). */
function blattOeffnen(titel, aufbauen, kopfKnoepfe) {
  const halter = document.getElementById('blatt-halter');
  const blatt = el('div', 'blatt');
  blatt.setAttribute('role', 'dialog');
  blatt.setAttribute('aria-modal', 'true');
  blatt.setAttribute('aria-label', titel);

  const kopf = el('div', 'blatt__kopf');
  const zu = el('button', 'ikon-knopf');
  zu.innerHTML = ikon('schliessen');
  zu.setAttribute('aria-label', 'Schließen');
  zu.onclick = () => blattSchliessen(blatt);
  const ueberschrift = el('h2', null, titel);
  kopf.append(ueberschrift);
  (kopfKnoepfe || []).forEach((k) => kopf.append(k));
  kopf.append(zu);

  const inhalt = el('div', 'blatt__inhalt');
  const neu = () => {
    inhalt.replaceChildren();
    aufbauen(inhalt, () => blattSchliessen(blatt), neu, ueberschrift);
  };
  neu();

  blatt.append(kopf, inhalt);
  halter.append(blatt);
  document.body.style.overflow = 'hidden';

  // Nur das oberste Blatt schließen: Aus einem Kontakt heraus lässt sich eine
  // Aufgabe öffnen — dann liegen zwei übereinander, und Escape darf nicht
  // beide auf einmal wegräumen.
  blatt._escape = (e) => {
    if (e.key === 'Escape' && blatt === halter.lastElementChild) blattSchliessen(blatt);
  };
  document.addEventListener('keydown', blatt._escape);
  zu.focus();
  blatt._neu = neu;
  return blatt;
}

function blattSchliessen(blatt) {
  document.removeEventListener('keydown', blatt._escape);
  blatt.remove();
  if (!document.querySelector('.blatt')) document.body.style.overflow = '';
  neuZeichnen();
}

/** Kurzer Hinweis am unteren Rand. */
let meldungsUhr = null;
function meldung(text) {
  document.querySelectorAll('.meldung').forEach((m) => m.remove());
  const m = el('div', 'meldung', text);
  m.setAttribute('role', 'status');
  document.body.append(m);
  clearTimeout(meldungsUhr);
  meldungsUhr = setTimeout(() => m.remove(), 2800);
}

/* --- Bausteine ---------------------------------------------------------- */
function plakette(typ) {
  return el('span', `plakette plakette--${typ}`, TYPEN[typ] || typ);
}

function initialenkreis(k, gross) {
  const kreis = el('div', `initialen initialen--${k.typ}${gross ? ' initialen--gross' : ''}`,
    initialen(k));
  kreis.setAttribute('aria-hidden', 'true');
  return kreis;
}

function leerzustand(titel, text, klein) {
  const box = el('div', 'leer' + (klein ? ' leer--klein' : ''));
  box.innerHTML = ikon('leer');
  box.append(el('div', 'leer__titel', titel), el('p', null, text));
  return box;
}

function abschnitt(ziel, titel, anzahl, warn) {
  const t = el('div', 'abschnitt-titel' + (warn ? ' abschnitt-titel--warn' : ''), titel);
  if (anzahl != null) t.append(el('span', 'zaehler', zahl(anzahl)));
  ziel.append(t);
}

/** Eine Kontaktzeile mit Untertext. Klick öffnet den Kontakt. */
function kontaktzeile(k, unten, tonart) {
  const z = el('button', 'zeile');
  z.append(initialenkreis(k));
  const text = el('div', 'zeile__text');
  const nameZeile = el('div', 'zeile__name');
  nameZeile.append(document.createTextNode(name(k)));
  nameZeile.append(plakette(k.typ));
  text.append(nameZeile);
  if (unten) text.append(el('div', 'zeile__meta' + (tonart ? ` zeile__meta--${tonart}` : ''), unten));
  z.append(text);
  const pfeil = el('div', 'zeile__pfeil');
  pfeil.innerHTML = ikon('weiter');
  z.append(pfeil);
  z.onclick = () => kontaktBlatt(k.id);
  return z;
}

/** Eine Aufgabenzeile mit Haken, Kurzaktionen und Verschieben. */
function aufgabenzeile(a, beiAenderung) {
  const k = kontakt(a.kontaktId);
  if (!k) return el('div');

  const tage = tageBis(a.faellig);
  const ueber = !a.erledigt && tage < 0;
  const heute = !a.erledigt && tage === 0;

  const box = el('div', 'aufgabe' +
    (ueber ? ' aufgabe--warn' : '') + (a.erledigt ? ' aufgabe--erledigt' : ''));

  const haken = el('button', 'haken');
  haken.innerHTML = ikon('haken');
  haken.setAttribute('aria-pressed', String(a.erledigt));
  haken.setAttribute('aria-label', a.erledigt ? 'Wieder öffnen' : 'Erledigt');
  haken.onclick = () => {
    if (a.erledigt) {
      a.erledigt = false;
      a.erledigtAm = null;
      Speicher.sichern();
    } else {
      const folge = aufgabeErledigen(a);
      meldung(folge
        ? `Erledigt · nächster Schritt am ${datumKurz(folge.faellig)}`
        : 'Erledigt und im Verlauf vermerkt');
    }
    beiAenderung();
  };
  box.append(haken);

  const rechts = el('div');
  rechts.style.flex = '1';
  rechts.style.minWidth = '0';

  const text = el('div', 'aufgabe__text');
  text.append(el('div', 'aufgabe__name', name(k)));
  text.append(el('div', 'aufgabe__was', a.text || ARTEN[a.art][0]));

  const meta = el('div', 'aufgabe__meta' +
    (ueber ? ' aufgabe__meta--warn' : heute ? ' aufgabe__meta--acht' : ''));
  meta.append(el('span', null, ARTEN[a.art][0]));
  meta.append(el('span', null, '·'));
  meta.append(el('span', null, a.erledigt
    ? `erledigt ${vorTagenText(a.erledigtAm)}`
    : faelligText(a.faellig)));
  text.append(meta);
  text.onclick = () => kontaktBlatt(k.id);
  text.setAttribute('role', 'button');
  text.setAttribute('tabindex', '0');
  text.onkeydown = (e) => { if (e.key === 'Enter') kontaktBlatt(k.id); };
  rechts.append(text);

  // Die Knöpfe stehen unter der Aufgabe, nicht in der Zeile. Bewusst nur vier:
  // anrufen, schreiben, verschieben. Zum Ändern führt der Weg über den
  // Kontakt — das kommt selten vor und würde die Liste sonst zumüllen.
  if (!a.erledigt) {
    const knoepfe = el('div', 'aufgabe__knoepfe');
    const wa = whatsappNummer(k.telefon);
    if (k.telefon) knoepfe.append(linkKnopf('Anrufen', `tel:${k.telefon}`));
    if (wa) knoepfe.append(linkKnopf('WhatsApp', `https://wa.me/${wa}`, true));
    knoepfe.append(kleinerKnopf('+1 Tag', () => {
      aufgabeVerschieben(a, 1); beiAenderung();
    }));
    knoepfe.append(kleinerKnopf('+1 Woche', () => {
      aufgabeVerschieben(a, 7); beiAenderung();
    }));
    rechts.append(knoepfe);
  }

  box.append(rechts);
  return box;
}

function kleinerKnopf(beschriftung, beiKlick, art) {
  const k = el('button', `knopf knopf--klein ${art || 'knopf--zweit'}`, beschriftung);
  k.onclick = beiKlick;
  return k;
}

function linkKnopf(beschriftung, ziel, extern) {
  const a = el('a', 'knopf knopf--klein knopf--zweit', beschriftung);
  a.href = ziel;
  a.style.textAlign = 'center';
  a.style.textDecoration = 'none';
  if (extern) { a.target = '_blank'; a.rel = 'noopener'; }
  return a;
}

function feld(label, eingabe, hilfe) {
  const f = el('div', 'feld');
  const l = el('label', null, label);
  const id = 'f-' + neueId();
  l.htmlFor = id;
  eingabe.id = id;
  f.append(l, eingabe);
  if (hilfe) f.append(el('div', 'feld__hilfe', hilfe));
  return f;
}

function textfeld(wert, platzhalter, typ) {
  const e = el('input', 'eingabe');
  e.type = typ || 'text';
  e.value = wert || '';
  if (platzhalter) e.placeholder = platzhalter;
  return e;
}

/** Nimmt ein Objekt oder — wenn die Reihenfolge zählt — eine Liste von Paaren.
 *
 *  Der Umweg über die Liste ist nötig, weil JavaScript in Objekten alle
 *  zahlartigen Schlüssel nach vorn sortiert. Eine Auswahl mit den Schlüsseln
 *  '', '1', '3' zeigt sonst „Nichts planen" ganz unten statt oben.
 */
function auswahlfeld(optionen, wert) {
  const s = el('select', 'eingabe');
  const paare = Array.isArray(optionen) ? optionen : Object.entries(optionen);
  paare.forEach(([w, beschriftung]) => {
    const o = el('option', null, beschriftung);
    o.value = w;
    if (w === wert) o.selected = true;
    s.append(o);
  });
  return s;
}

function wertkachel(label, wertText, note, tonart) {
  const w = el('div', 'wert');
  w.append(el('div', 'wert__label', label));
  w.append(el('div', 'wert__zahl', wertText));
  if (note) w.append(el('div', 'wert__note' + (tonart ? ` wert__note--${tonart}` : ''), note));
  return w;
}

/* =========================================================================
   Ansicht: Heute
   ========================================================================= */
function ansichtHeute(ziel) {
  const alle = aktiveKontakte();
  if (!alle.length) return startbildschirm(ziel);

  const e = Speicher.daten.einstellungen;
  const ueber = ueberfaellig();
  const heute = heuteFaellig();
  const gespraeche7 = alle.reduce((summe, k) =>
    summe + k.verlauf.filter((v) => tageBis(v.datum) >= -6).length, 0);

  /* Kopfkarte */
  const held = el('div', 'held');
  held.append(el('div', 'held__datum', datumLang(heuteText())));
  const offen = ueber.length + heute.length;
  held.append(el('div', 'held__zeile', offen === 0
    ? 'Nichts offen für heute'
    : `${offen} ${offen === 1 ? 'Kontakt wartet' : 'Kontakte warten'} auf dich`));
  held.append(el('div', 'held__sub', ueber.length
    ? `Davon ${ueber.length} ${ueber.length === 1 ? 'überfällig' : 'überfällig'} — die zuerst.`
    : 'Sauber geführt. Weiter so.'));

  const zahlen = el('div', 'held__zahlen');
  [[zahl(alle.length), 'Kontakte'],
   [zahl(offeneAufgaben().length), 'offen'],
   [zahl(gespraeche7), '7 Tage aktiv']].forEach(([b, s]) => {
    const kachel = el('div', 'held__zahl');
    kachel.append(el('b', null, b), el('span', null, s));
    zahlen.append(kachel);
  });
  held.append(zahlen);
  ziel.append(held);

  let etwasZuTun = false;

  /* Überfällig */
  if (ueber.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Überfällig', ueber.length, true);
    ueber.forEach((a) => ziel.append(aufgabenzeile(a, neuZeichnen)));
  }

  /* Heute */
  if (heute.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Heute fällig', heute.length);
    heute.forEach((a) => ziel.append(aufgabenzeile(a, neuZeichnen)));
  }

  /* Geburtstage */
  const geburtstage = geburtstageDemnaechst(e.geburtstagVorlauf);
  if (geburtstage.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Geburtstage', geburtstage.length);
    geburtstage.forEach(({ kontakt: k, inTagen }) => {
      const text = inTagen === 0 ? 'heute — gratulieren'
        : inTagen === 1 ? 'morgen' : `in ${inTagen} Tagen`;
      ziel.append(kontaktzeile(k, `Geburtstag ${text}`, inTagen <= 1 ? 'acht' : null));
    });
  }

  /* Nachbestellung */
  const nachbestellung = nachbestellungFaellig();
  if (nachbestellung.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Nachbestellung fällig', nachbestellung.length);
    nachbestellung.slice(0, 8).forEach(({ kontakt: k, tage }) => {
      ziel.append(kontaktzeile(k,
        `${tage} Tage über dem Rhythmus · zuletzt ${vorTagenText(k.letzteBestellung)}`,
        tage > 14 ? 'warn' : 'acht'));
    });
  }

  /* Betreuung */
  const betreuung = betreuungFaellig();
  if (betreuung.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Zu lange nichts gehört', betreuung.length);
    betreuung.slice(0, 8).forEach(({ kontakt: k, tage }) => {
      const letzter = letzterKontaktDatum(k);
      ziel.append(kontaktzeile(k, letzter
        ? `Letzter Kontakt ${vorTagenText(letzter)}`
        : `Seit ${tage} Tagen erfasst, noch kein Eintrag im Verlauf`, 'acht'));
    });
  }

  /* Ohne nächsten Schritt */
  const ohne = ohneNaechstenSchritt();
  if (ohne.length) {
    etwasZuTun = true;
    abschnitt(ziel, 'Ohne nächsten Schritt', ohne.length);
    const karte = el('div', 'karte karte--flach');
    karte.append(el('p', null,
      'Für diese Kontakte steht kein Termin und keine Aufgabe. Genau hier ' +
      'gehen im Vertrieb die meisten Menschen verloren — nicht am Nein, ' +
      'sondern am Vergessen.'));
    karte.querySelector('p').style.fontSize = '13.5px';
    karte.querySelector('p').style.margin = '0 0 12px';
    const knopf = el('button', 'knopf', 'Für alle einen Schritt planen');
    knopf.onclick = () => {
      let angelegt = 0;
      ohne.forEach((k) => { if (kadenzAnlegen(k)) angelegt++; });
      meldung(angelegt
        ? `${angelegt} Follow-ups angelegt`
        : 'Nichts anzulegen — Status prüfen');
      neuZeichnen();
    };
    karte.append(knopf);
    ziel.append(karte);
    ohne.slice(0, 6).forEach((k) => {
      const letzter = letzterKontaktDatum(k);
      const stand = k.typ === 'interessent'
        ? (STUFENNAME[k.stufe] || 'Neu erfasst')
        : TYPEN[k.typ];
      ziel.append(kontaktzeile(k, letzter
        ? `${stand} · zuletzt ${vorTagenText(letzter)}`
        : `${stand} · noch kein Eintrag im Verlauf`));
    });
    if (ohne.length > 6) {
      const mehr = kleinerKnopf(`Alle ${ohne.length} in den Kontakten zeigen`, () => {
        App.ansicht = 'kontakte';
        App.kontaktFilter = 'ohneschritt';
        neuZeichnen();
      });
      mehr.style.width = '100%';
      ziel.append(mehr);
    }
  }

  if (!etwasZuTun) {
    ziel.append(leerzustand('Alles abgearbeitet',
      'Kein offener Follow-up, keine Lücke in der Betreuung. Zeit für neue Kontakte.'));
  }
}

/** Wird nur beim allerersten Start gezeigt. */
function startbildschirm(ziel) {
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Willkommen'));
  const p1 = el('p', null,
    'Diese App ist deine Kontaktdatenbank und dein Follow-up-System: jeder ' +
    'Interessent, jeder Kunde und jeder Teampartner an einem Ort, und zu ' +
    'jedem ein nächster Schritt mit Datum.');
  const p2 = el('p', null,
    'Alles bleibt auf diesem Gerät. Kein Konto, kein Server, keine ' +
    'Übertragung — sichere deine Daten deshalb regelmäßig über den Export ' +
    'in den Einstellungen.');
  [p1, p2].forEach((p) => { p.style.fontSize = '14.5px'; p.style.margin = '0 0 12px'; });
  karte.append(p1, p2);

  const anlegen = el('button', 'knopf', 'Ersten Kontakt anlegen');
  anlegen.onclick = () => kontaktBearbeiten(null);
  karte.append(anlegen);

  const demo = el('button', 'knopf knopf--zweit', 'Mit Beispieldaten ansehen');
  demo.style.marginTop = '8px';
  demo.onclick = () => {
    beispieldaten();
    meldung('Beispieldaten geladen');
    neuZeichnen();
  };
  karte.append(demo);
  ziel.append(karte);

  const hinweis = el('div', 'hinweis');
  hinweis.append(el('div', 'hinweis__titel', 'Zu den Daten anderer Menschen'));
  hinweis.append(el('p', null,
    'Hier stehen Namen, Nummern und Notizen zu echten Personen. Erfasse nur, ' +
    'was du für die Betreuung wirklich brauchst, und lösche Kontakte, die ' +
    'nicht mehr von dir hören wollen — vollständig, nicht nur archiviert.'));
  ziel.append(hinweis);
}

/* =========================================================================
   Ansicht: Kontakte
   ========================================================================= */
const KONTAKT_FILTER = {
  alle:        'Alle',
  interessent: 'Interessenten',
  kunde:       'Kunden',
  partner:     'Partner',
  ruhend:      'Ruhend',
  ohneschritt: 'Ohne Schritt',
  archiv:      'Archiv'
};

const SORTIERUNGEN = {
  schritt: 'Nächster Schritt',
  name:    'Name',
  neu:     'Zuletzt angelegt',
  aktiv:   'Längste Funkstille'
};

function ansichtKontakte(ziel) {
  /* Suche */
  const suchbox = el('div', 'suchfeld');
  suchbox.innerHTML = ikon('suche');
  const suche = textfeld(App.kontaktSuche, 'Name, Ort, Telefon, Notiz, Schlagwort', 'search');
  suche.setAttribute('aria-label', 'Kontakte durchsuchen');
  suche.oninput = () => {
    App.kontaktSuche = suche.value;
    zeichneListe();
  };
  suchbox.append(suche);
  ziel.append(suchbox);

  /* Filter */
  const filter = el('div', 'filter');
  Object.entries(KONTAKT_FILTER).forEach(([wert, beschriftung]) => {
    const c = el('button', 'chip', beschriftung);
    c.setAttribute('aria-pressed', String(App.kontaktFilter === wert));
    c.onclick = () => {
      App.kontaktFilter = wert;
      neuZeichnen();
    };
    filter.append(c);
  });
  ziel.append(filter);

  /* Sortierung */
  const sortZeile = el('div', 'abschnitt-titel');
  sortZeile.append(document.createTextNode('Sortierung'));
  const sortWahl = auswahlfeld(SORTIERUNGEN, App.kontaktSortierung);
  sortWahl.style.width = 'auto';
  sortWahl.style.marginLeft = 'auto';
  sortWahl.style.padding = '5px 9px';
  sortWahl.style.fontSize = '12.5px';
  sortWahl.style.textTransform = 'none';
  sortWahl.style.letterSpacing = '0';
  sortWahl.setAttribute('aria-label', 'Sortierung');
  sortWahl.onchange = () => {
    App.kontaktSortierung = sortWahl.value;
    zeichneListe();
  };
  sortZeile.append(sortWahl);
  ziel.append(sortZeile);

  const liste = el('div');
  ziel.append(liste);

  function zeichneListe() {
    liste.replaceChildren();
    const treffer = gefilterteKontakte();

    if (!treffer.length) {
      liste.append(leerzustand('Kein Treffer',
        App.kontaktSuche
          ? 'Keine Übereinstimmung. Vielleicht ein anderer Suchbegriff?'
          : 'In diesem Filter steht noch niemand.'));
      return;
    }

    const zaehler = el('div', 'fusstext',
      `${zahl(treffer.length)} ${treffer.length === 1 ? 'Kontakt' : 'Kontakte'}`);
    zaehler.style.margin = '0 2px 10px';
    liste.append(zaehler);

    treffer.forEach((k) => {
      const naechste = naechsterSchritt(k.id);
      let unten, ton = null;
      if (k.archiviert) {
        unten = 'Archiviert';
      } else if (naechste) {
        const t = tageBis(naechste.faellig);
        unten = `${ARTEN[naechste.art][0]} · ${faelligText(naechste.faellig)}`;
        ton = t < 0 ? 'warn' : t === 0 ? 'acht' : null;
      } else if (k.typ === 'interessent') {
        unten = `${STUFENNAME[k.stufe] || 'Neu erfasst'} · kein nächster Schritt`;
      } else {
        const letzter = letzterKontaktDatum(k);
        unten = letzter ? `Letzter Kontakt ${vorTagenText(letzter)}` : 'Noch kein Eintrag im Verlauf';
      }
      liste.append(kontaktzeile(k, unten, ton));
    });
  }

  zeichneListe();

  if (App.sucheFokussieren) {
    App.sucheFokussieren = false;
    suche.focus();
  }
}

function gefilterteKontakte() {
  const f = App.kontaktFilter;
  let liste = Speicher.daten.kontakte.filter((k) =>
    f === 'archiv' ? k.archiviert : !k.archiviert);

  if (['interessent', 'kunde', 'partner', 'ruhend'].includes(f)) {
    liste = liste.filter((k) => k.typ === f);
  } else if (f === 'ohneschritt') {
    liste = liste.filter((k) => k.typ !== 'ruhend' && !naechsterSchritt(k.id));
  }

  const suchtext = App.kontaktSuche.trim().toLowerCase();
  if (suchtext) {
    liste = liste.filter((k) => [
      name(k), k.ort, k.telefon, k.email, k.notiz, k.produkte,
      k.kundennummer, k.rang, (k.tags || []).join(' ')
    ].filter(Boolean).join(' ').toLowerCase().includes(suchtext));
  }

  const nachName = (a, b) => name(a).localeCompare(name(b), 'de');

  switch (App.kontaktSortierung) {
    case 'name':
      return liste.sort(nachName);
    case 'neu':
      return liste.sort((a, b) => (b.angelegt || '').localeCompare(a.angelegt || '') || nachName(a, b));
    case 'aktiv':
      return liste.sort((a, b) =>
        (letzterKontaktDatum(a) || a.angelegt || '').localeCompare(
          letzterKontaktDatum(b) || b.angelegt || '') || nachName(a, b));
    default: {
      // Nach nächstem Schritt: fällig zuerst, ohne Schritt ans Ende — dort
      // fällt am ehesten auf, dass etwas fehlt.
      return liste.sort((a, b) => {
        const sa = naechsterSchritt(a.id), sb = naechsterSchritt(b.id);
        if (sa && sb) return sa.faellig.localeCompare(sb.faellig) || nachName(a, b);
        if (sa) return -1;
        if (sb) return 1;
        return nachName(a, b);
      });
    }
  }
}

/* =========================================================================
   Kontaktblatt — die Akte zu einem Menschen
   ========================================================================= */
function kontaktBlatt(id) {
  const k = kontakt(id);
  if (!k) return;

  blattOeffnen(name(k), (inhalt, schliessen, neu, ueberschrift) => {
    const aktuell = kontakt(id);
    if (!aktuell) return schliessen();
    ueberschrift.textContent = name(aktuell);

    /* Kopf */
    const kopf = el('div', 'karte');
    const kopfZeile = el('div');
    kopfZeile.style.display = 'flex';
    kopfZeile.style.gap = '13px';
    kopfZeile.style.alignItems = 'center';
    kopfZeile.append(initialenkreis(aktuell, true));
    const kopfText = el('div');
    kopfText.style.minWidth = '0';
    kopfText.append(el('div', 'zeile__name', name(aktuell)));
    const untertitel = [
      TYPEN[aktuell.typ],
      aktuell.typ === 'interessent' ? STUFENNAME[aktuell.stufe] : null,
      aktuell.ort
    ].filter(Boolean).join(' · ');
    kopfText.append(el('div', 'zeile__meta', untertitel));
    kopfZeile.append(kopfText);
    kopf.append(kopfZeile);

    /* Schnellaktionen */
    const aktionen = el('div', 'aktionen');
    const wa = whatsappNummer(aktuell.telefon);
    aktionen.append(aktionsknopf('Anrufen', 'telefon',
      aktuell.telefon ? `tel:${aktuell.telefon}` : null, () =>
        verlaufDialog(aktuell.id, 'anruf', neu)));
    aktionen.append(aktionsknopf('WhatsApp', 'nachricht',
      wa ? `https://wa.me/${wa}` : null, () =>
        verlaufDialog(aktuell.id, 'nachricht', neu)));
    aktionen.append(aktionsknopf('E-Mail', 'mail',
      aktuell.email ? `mailto:${aktuell.email}` : null, () =>
        verlaufDialog(aktuell.id, 'nachricht', neu)));
    kopf.append(aktionen);
    inhalt.append(kopf);

    /* Nächster Schritt */
    inhalt.append(schrittKarte(aktuell, neu));

    /* Pipeline — nur für Interessenten */
    if (aktuell.typ === 'interessent') {
      inhalt.append(stufenKarte(aktuell, neu));
    }

    /* Stammdaten */
    inhalt.append(stammdatenKarte(aktuell));

    /* Rollenabhängige Daten */
    if (aktuell.typ === 'kunde') inhalt.append(kundenKarte(aktuell, neu));
    if (aktuell.typ === 'partner') inhalt.append(partnerKarte(aktuell));

    /* Notiz */
    if (aktuell.notiz) {
      const notiz = el('div', 'karte');
      notiz.append(el('div', 'karte__titel', 'Notiz'));
      const p = el('p', null, aktuell.notiz);
      p.style.cssText = 'margin:0;font-size:14px;white-space:pre-wrap';
      notiz.append(p);
      inhalt.append(notiz);
    }

    /* Verlauf */
    inhalt.append(verlaufKarte(aktuell, neu));

    /* Verwaltung */
    const verwaltung = el('div', 'reihe');
    verwaltung.style.marginTop = '4px';
    verwaltung.append(kleinerKnopf('Bearbeiten', () => kontaktBearbeiten(aktuell.id, neu)));
    verwaltung.append(kleinerKnopf(aktuell.archiviert ? 'Zurückholen' : 'Archivieren', () => {
      aktuell.archiviert = !aktuell.archiviert;
      Speicher.sichern();
      meldung(aktuell.archiviert ? 'Archiviert' : 'Zurückgeholt');
      neu();
    }));
    verwaltung.querySelectorAll('.knopf').forEach((b) => { b.style.width = '100%'; });
    inhalt.append(verwaltung);

    const loeschen = el('button', 'knopf knopf--klein knopf--warn', 'Kontakt löschen');
    loeschen.style.cssText = 'width:100%;margin-top:8px';
    loeschen.onclick = () => {
      if (!confirm(`${name(aktuell)} endgültig löschen? Verlauf und Follow-ups ` +
                   'werden mitgelöscht. Das lässt sich nicht rückgängig machen.')) return;
      kontaktLoeschen(aktuell.id);
      meldung('Kontakt gelöscht');
      schliessen();
    };
    inhalt.append(loeschen);

    inhalt.append(el('div', 'fusstext',
      `Angelegt am ${datumKurz(aktuell.angelegt)} · Quelle: ${QUELLEN[aktuell.quelle] || 'nicht erfasst'}`));
  });
}

function aktionsknopf(beschriftung, symbol, ziel, beiNutzung) {
  if (!ziel) {
    const aus = el('div', 'aktion');
    aus.setAttribute('aria-disabled', 'true');
    aus.innerHTML = ikon(symbol);
    aus.append(el('span', null, beschriftung));
    return aus;
  }
  const a = el('a', 'aktion');
  a.href = ziel;
  if (ziel.startsWith('http')) { a.target = '_blank'; a.rel = 'noopener'; }
  a.innerHTML = ikon(symbol);
  a.append(el('span', null, beschriftung));
  // Nach dem Griff zum Telefon soll der Verlaufseintrag angeboten werden —
  // sonst ist die Historie nach zwei Wochen wertlos.
  a.onclick = () => setTimeout(beiNutzung, 600);
  return a;
}

function schrittKarte(k, neu) {
  const karte = el('div', 'karte');
  const naechste = naechsterSchritt(k.id);
  const titel = el('div', 'karte__titel', 'Nächster Schritt');
  karte.append(titel);

  if (naechste) {
    const tage = tageBis(naechste.faellig);
    const zeile = el('div');
    zeile.style.cssText = 'display:flex;align-items:flex-start;gap:11px';

    const haken = el('button', 'haken');
    haken.innerHTML = ikon('haken');
    haken.setAttribute('aria-pressed', 'false');
    haken.setAttribute('aria-label', 'Erledigt');
    haken.onclick = () => {
      const folge = aufgabeErledigen(naechste);
      meldung(folge
        ? `Erledigt · nächster Schritt am ${datumKurz(folge.faellig)}`
        : 'Erledigt und im Verlauf vermerkt');
      neu();
    };

    const text = el('div');
    text.style.flex = '1';
    text.append(el('div', 'aufgabe__was', naechste.text || ARTEN[naechste.art][0]));
    const meta = el('div', 'aufgabe__meta' +
      (tage < 0 ? ' aufgabe__meta--warn' : tage === 0 ? ' aufgabe__meta--acht' : ''),
      `${ARTEN[naechste.art][0]} · ${faelligText(naechste.faellig)}`);
    text.append(meta);

    const knoepfe = el('div', 'aufgabe__knoepfe');
    knoepfe.append(kleinerKnopf('+1 Tag', () => { aufgabeVerschieben(naechste, 1); neu(); }));
    knoepfe.append(kleinerKnopf('+1 Woche', () => { aufgabeVerschieben(naechste, 7); neu(); }));
    knoepfe.append(kleinerKnopf('Ändern', () => aufgabenBlatt(naechste, neu)));
    text.append(knoepfe);

    zeile.append(haken, text);
    karte.append(zeile);

    const weitere = offeneAufgaben(k.id).filter((a) => a.id !== naechste.id);
    if (weitere.length) {
      karte.append(el('div', 'fusstext',
        `${weitere.length} weitere offene ${weitere.length === 1 ? 'Aufgabe' : 'Aufgaben'} · ` +
        weitere.map((a) => datumKurz(a.faellig)).join(', ')));
    }
  } else {
    const hinweis = el('p', null,
      'Nichts geplant. Ein Kontakt ohne nächsten Schritt ist ein Kontakt, ' +
      'den du verlierst.');
    hinweis.style.cssText = 'margin:0 0 12px;font-size:13.5px;color:var(--ink-soft)';
    karte.append(hinweis);
  }

  const planen = el('button', 'knopf' + (naechste ? ' knopf--zweit' : ''),
    naechste ? 'Weiteren Schritt planen' : 'Follow-up planen');
  planen.style.marginTop = '10px';
  planen.onclick = () => aufgabenBlatt(null, neu, k.id);
  karte.append(planen);

  return karte;
}

function stufenKarte(k, neu) {
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Stand'));
  const erreichtIndex = STUFEN.findIndex(([w]) => w === k.stufe);

  const stufen = el('div', 'stufen');
  STUFEN.forEach(([wert, beschriftung, note], i) => {
    const s = el('button', 'stufe' +
      (i < erreichtIndex ? ' stufe--erreicht' : '') +
      (i === erreichtIndex ? ' stufe--aktiv stufe--erreicht' : ''));
    s.append(el('div', 'stufe__nr', String(i + 1)));
    const text = el('div', 'stufe__text');
    text.append(document.createTextNode(beschriftung));
    text.append(el('span', 'stufe__note', note));
    s.append(text);
    s.setAttribute('aria-pressed', String(i === erreichtIndex));
    s.onclick = () => {
      if (k.stufe === wert) return;
      k.stufe = wert;
      Speicher.sichern();
      verlaufAnlegen(k.id, 'sonstige', `Stand: ${beschriftung}`);
      const folge = kadenzAnlegen(k);
      meldung(folge
        ? `${beschriftung} · Follow-up am ${datumKurz(folge.faellig)}`
        : beschriftung);
      neu();
    };
    stufen.append(s);
  });
  karte.append(stufen);

  /* Abschluss: aus dem Interessenten wird Kunde oder Partner. */
  const abschluss = el('div', 'reihe');
  abschluss.style.marginTop = '12px';
  abschluss.append(kleinerKnopf('Wurde Kunde', () => rolleWechseln(k, 'kunde', neu)));
  abschluss.append(kleinerKnopf('Wurde Partner', () => rolleWechseln(k, 'partner', neu)));
  abschluss.append(kleinerKnopf('Ruhend', () => rolleWechseln(k, 'ruhend', neu)));
  abschluss.querySelectorAll('.knopf').forEach((b) => { b.style.width = '100%'; });
  karte.append(abschluss);
  return karte;
}

function rolleWechseln(k, typ, neu) {
  k.typ = typ;
  if (typ === 'kunde' && !k.letzteBestellung) k.letzteBestellung = heuteText();
  if (typ === 'partner' && !k.partnerSeit) k.partnerSeit = heuteText();
  Speicher.sichern();
  verlaufAnlegen(k.id, 'sonstige', `Neuer Status: ${TYPEN[typ]}`);

  if (typ === 'ruhend') {
    // Bei „ruhend" bleiben offene Aufgaben stehen wäre falsch: Der Kontakt
    // will gerade nicht — aber ganz aus dem Blick soll er auch nicht geraten.
    offeneAufgaben(k.id).forEach((a) => { a.erledigt = true; a.erledigtAm = heuteText(); });
    const wieder = aufgabeAnlegen(k.id, plusTage(90), 'nachricht',
      'Locker wieder melden — ist die Situation noch dieselbe?');
    Speicher.sichern();
    meldung(`Ruhend · Wiedervorlage am ${datumKurz(wieder.faellig)}`);
  } else {
    const folge = kadenzAnlegen(k);
    meldung(folge
      ? `${TYPEN[typ]} · nächster Schritt am ${datumKurz(folge.faellig)}`
      : TYPEN[typ]);
  }
  neu();
}

function stammdatenKarte(k) {
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Stammdaten'));

  const zeilen = [
    ['Telefon', k.telefon, k.telefon ? `tel:${k.telefon}` : null],
    ['E-Mail', k.email, k.email ? `mailto:${k.email}` : null],
    ['Ort', k.ort],
    ['Geburtstag', k.geburtstag ? geburtstagText(k.geburtstag) : null],
    ['Quelle', QUELLEN[k.quelle]],
    ['Empfohlen von', k.empfehlungVon ? namensLink(k.empfehlungVon) : null]
  ].filter(([, wert]) => wert);

  if (!zeilen.length) {
    karte.append(el('p', null, 'Noch keine Angaben erfasst.'));
    karte.querySelector('p').style.cssText = 'margin:0;font-size:13.5px;color:var(--ink-soft)';
  }

  zeilen.forEach(([label, wert, verweis]) => {
    const z = el('div', 'datenzeile');
    z.append(el('div', 'datenzeile__label', label));
    const w = el('div', 'datenzeile__wert');
    if (verweis) {
      const a = el('a', null, wert);
      a.href = verweis;
      w.append(a);
    } else if (wert instanceof Node) {
      w.append(wert);
    } else {
      w.textContent = wert;
    }
    z.append(w);
    karte.append(z);
  });

  if (k.tags && k.tags.length) {
    const marken = el('div', 'marken');
    marken.style.marginTop = '11px';
    k.tags.forEach((t) => marken.append(el('span', 'marke', t)));
    karte.append(marken);
  }
  return karte;
}

function namensLink(id) {
  const k = kontakt(id);
  if (!k) return null;
  const a = el('a', null, name(k));
  a.href = '#';
  a.onclick = (e) => { e.preventDefault(); kontaktBlatt(id); };
  return a;
}

function geburtstagText(wert) {
  const teile = wert.split('-').map(Number);
  if (teile.length === 3) {
    const alter = new Date().getFullYear() - teile[0];
    return `${teile[2]}. ${MONATE[teile[1] - 1]} ${teile[0]} (${alter})`;
  }
  return `${teile[1]}. ${MONATE[teile[0] - 1]}`;
}

function kundenKarte(k, neu) {
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Als Kunde'));
  const zeilen = [
    ['Kundennummer', k.kundennummer],
    ['Produkte', k.produkte],
    ['Letzte Bestellung', k.letzteBestellung
      ? `${datumKurz(k.letzteBestellung)} · ${vorTagenText(k.letzteBestellung)}` : null],
    ['Autoship', k.autoship ? 'Ja — läuft automatisch' : 'Nein']
  ].filter(([, wert]) => wert);

  zeilen.forEach(([label, wert]) => {
    const z = el('div', 'datenzeile');
    z.append(el('div', 'datenzeile__label', label), el('div', 'datenzeile__wert', wert));
    karte.append(z);
  });

  if (k.letzteBestellung && !k.autoship) {
    const faellig = plusTage(Speicher.daten.einstellungen.nachbestellung, k.letzteBestellung);
    const t = tageBis(faellig);
    const hinweis = el('div', 'fusstext',
      t < 0 ? `Nachbestellung seit ${-t} Tagen überfällig.`
            : `Nächste Nachbestellung rechnerisch am ${datumKurz(faellig)}.`);
    if (t < 0) hinweis.style.color = 'var(--warn-ink)';
    karte.append(hinweis);
  }

  const bestellt = el('button', 'knopf knopf--zweit knopf--klein', 'Bestellung heute eintragen');
  bestellt.style.cssText = 'width:100%;margin-top:10px';
  bestellt.onclick = () => {
    k.letzteBestellung = heuteText();
    Speicher.sichern();
    verlaufAnlegen(k.id, 'nachbestellung', 'Bestellung aufgegeben');
    // Offene Nachbestell-Erinnerungen sind damit erledigt.
    offeneAufgaben(k.id)
      .filter((a) => a.art === 'nachbestellung')
      .forEach((a) => { a.erledigt = true; a.erledigtAm = heuteText(); });
    Speicher.sichern();
    meldung('Bestellung eingetragen');
    neu();
  };
  karte.append(bestellt);
  return karte;
}

function partnerKarte(k) {
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Als Teampartner'));
  const untergeordnete = Speicher.daten.kontakte.filter((x) => x.sponsor === k.id);
  const zeilen = [
    ['Partner seit', k.partnerSeit ? `${datumKurz(k.partnerSeit)} · ${vorTagenText(k.partnerSeit)}` : null],
    ['Rang', k.rang],
    ['Kundennummer', k.kundennummer],
    ['Sponsor', k.sponsor ? namensLink(k.sponsor) : 'Erstlinie (von dir eingeschrieben)'],
    ['Eigene Linie', untergeordnete.length ? `${untergeordnete.length} direkt` : 'noch niemand']
  ].filter(([, wert]) => wert);

  zeilen.forEach(([label, wert]) => {
    const z = el('div', 'datenzeile');
    const w = el('div', 'datenzeile__wert');
    if (wert instanceof Node) w.append(wert); else w.textContent = wert;
    z.append(el('div', 'datenzeile__label', label), w);
    karte.append(z);
  });

  const letzter = letzterKontaktDatum(k);
  const grenze = Speicher.daten.einstellungen.betreuungPartner;
  if (letzter && -tageBis(letzter) >= grenze) {
    const hinweis = el('div', 'fusstext',
      `Letzter Kontakt ${vorTagenText(letzter)} — dein Betreuungsintervall sind ${grenze} Tage.`);
    hinweis.style.color = 'var(--warn-ink)';
    karte.append(hinweis);
  }
  return karte;
}

function verlaufKarte(k, neu) {
  const karte = el('div', 'karte');
  const titel = el('div', 'karte__titel', 'Verlauf');
  titel.append(el('span', 'zaehler', `${k.verlauf.length} ${k.verlauf.length === 1 ? 'Eintrag' : 'Einträge'}`));
  karte.append(titel);

  const eintragen = el('button', 'knopf knopf--zweit knopf--klein', 'Kontakt festhalten');
  eintragen.style.cssText = 'width:100%;margin-bottom:12px';
  eintragen.onclick = () => verlaufDialog(k.id, 'anruf', neu);
  karte.append(eintragen);

  if (!k.verlauf.length) {
    karte.append(leerzustand('Noch nichts festgehalten',
      'Jedes Gespräch, jede Nachricht — was hier steht, weißt du in einem halben Jahr noch.', true));
    return karte;
  }

  const liste = el('div', 'verlauf');
  const sortiert = k.verlauf.slice().sort((a, b) => b.datum.localeCompare(a.datum));
  sortiert.slice(0, 40).forEach((e) => {
    const eintrag = el('div', 'eintrag');
    const kopf = el('div', 'eintrag__kopf');
    kopf.append(el('span', 'eintrag__art', (ARTEN[e.art] || ARTEN.sonstige)[0]));
    kopf.append(el('span', 'eintrag__datum', `${datumKurz(e.datum)} · ${vorTagenText(e.datum)}`));
    eintrag.append(kopf);
    if (e.text) eintrag.append(el('div', 'eintrag__text', e.text));

    // Löschen über langes Antippen wäre auf dem Handy unauffindbar; ein
    // kleiner Knopf am Eintrag ist ehrlicher.
    eintrag.oncontextmenu = (ev) => {
      ev.preventDefault();
      if (!confirm('Diesen Eintrag löschen?')) return;
      k.verlauf = k.verlauf.filter((x) => x.id !== e.id);
      Speicher.sichern();
      neu();
    };
    liste.append(eintrag);
  });
  karte.append(liste);

  if (sortiert.length > 40) {
    karte.append(el('div', 'fusstext', `${sortiert.length - 40} ältere Einträge nicht angezeigt.`));
  }
  return karte;
}

/** Kleiner Dialog: Was ist passiert? */
function verlaufDialog(kontaktId, artVorgabe, beiFertig) {
  const k = kontakt(kontaktId);
  if (!k) return;

  blattOeffnen('Kontakt festhalten', (inhalt, schliessen) => {
    const artWahl = auswahlfeld(
      Object.fromEntries(Object.entries(ARTEN).map(([w, [n]]) => [w, n])), artVorgabe);
    const datum = textfeld(heuteText(), null, 'date');
    const text = el('textarea', 'eingabe');
    text.placeholder = 'Worum ging es? Was wurde vereinbart?';

    inhalt.append(el('div', 'karte__titel', name(k)));
    inhalt.append(feld('Art', artWahl));
    inhalt.append(feld('Datum', datum));
    inhalt.append(feld('Notiz', text));

    /* Direkt den nächsten Schritt mitplanen — das ist der halbe Zweck. */
    const folgeFeld = el('div', 'karte karte--flach');
    folgeFeld.append(el('div', 'karte__titel', 'Und als Nächstes?'));
    const vorschlag = kadenzVorschlag(k);
    const abstaende = [
      ['', 'Nichts planen'], ['1', 'Morgen'], ['3', 'In 3 Tagen'],
      ['7', 'In einer Woche'], ['14', 'In zwei Wochen'], ['30', 'In einem Monat']
    ];
    // Schlägt die Kadenz einen Abstand vor, den die Liste nicht kennt, kommt
    // er dazu — sonst fiele die Auswahl still auf „Nichts planen" zurück.
    if (vorschlag && !abstaende.some(([w]) => w === String(vorschlag.tage))) {
      abstaende.push([String(vorschlag.tage), `In ${vorschlag.tage} Tagen`]);
    }
    const folgeWahl = auswahlfeld(abstaende, String(vorschlag ? vorschlag.tage : ''));
    const folgeText = textfeld(vorschlag ? vorschlag.text : '', 'Was steht dann an?');
    folgeFeld.append(feld('Wiedervorlage', folgeWahl));
    folgeFeld.append(feld('Aufgabe', folgeText));
    inhalt.append(folgeFeld);

    const sichern = el('button', 'knopf', 'Speichern');
    sichern.onclick = () => {
      verlaufAnlegen(k.id, artWahl.value, text.value.trim(), datum.value || heuteText());
      if (folgeWahl.value) {
        const a = aufgabeAnlegen(k.id, plusTage(Number(folgeWahl.value)),
          artWahl.value === 'geburtstag' ? 'nachricht' : artWahl.value,
          folgeText.value.trim() || 'Nachfassen');
        meldung(`Festgehalten · Wiedervorlage am ${datumKurz(a.faellig)}`);
      } else {
        meldung('Festgehalten');
      }
      schliessen();
      if (beiFertig) beiFertig();
    };
    inhalt.append(sichern);
  });
}

/* =========================================================================
   Kontakt anlegen und bearbeiten
   ========================================================================= */
function kontaktBearbeiten(id, beiFertig) {
  const vorhanden = id ? kontakt(id) : null;
  const k = vorhanden ? Object.assign({}, vorhanden) : {
    id: neueId(), vorname: '', nachname: '', telefon: '', email: '', ort: '',
    geburtstag: '', typ: 'interessent', stufe: 'neu', quelle: 'direkt',
    empfehlungVon: '', sponsor: '', kundennummer: '', produkte: '',
    autoship: false, letzteBestellung: '', partnerSeit: '', rang: '',
    notiz: '', tags: [], angelegt: heuteText(), verlauf: [], archiviert: false
  };
  let tags = (k.tags || []).slice();

  blattOeffnen(vorhanden ? 'Kontakt bearbeiten' : 'Neuer Kontakt', (inhalt, schliessen) => {
    const vorname = textfeld(k.vorname, 'Vorname');
    const nachname = textfeld(k.nachname, 'Nachname');
    const telefon = textfeld(k.telefon, '0170 1234567', 'tel');
    const email = textfeld(k.email, 'name@beispiel.de', 'email');
    const ort = textfeld(k.ort, 'Ort');
    const geburtstag = textfeld(k.geburtstag, null, 'date');
    const typWahl = auswahlfeld(TYPEN, k.typ);
    const stufeWahl = auswahlfeld(Object.fromEntries(STUFEN.map(([w, n]) => [w, n])), k.stufe);
    const quelleWahl = auswahlfeld(QUELLEN, k.quelle);
    const notiz = el('textarea', 'eingabe');
    notiz.value = k.notiz || '';
    notiz.placeholder = 'Was ist wichtig? Familie, Beruf, Beweggrund, Ziel …';

    /* Auswahllisten über andere Kontakte */
    const andere = Speicher.daten.kontakte
      .filter((x) => x.id !== k.id)
      .sort((a, b) => name(a).localeCompare(name(b), 'de'));
    const namensliste = Object.assign({ '': '—' },
      Object.fromEntries(andere.map((x) => [x.id, name(x)])));
    const empfehlungWahl = auswahlfeld(namensliste, k.empfehlungVon || '');
    const partnerListe = Object.assign({ '': 'Erstlinie (von mir)' },
      Object.fromEntries(andere.filter((x) => x.typ === 'partner').map((x) => [x.id, name(x)])));
    const sponsorWahl = auswahlfeld(partnerListe, k.sponsor || '');

    /* Rollenabhängige Felder */
    const kundennummer = textfeld(k.kundennummer, 'PM-Kundennummer');
    const produkte = textfeld(k.produkte, 'Activize, Restorate, Basics …');
    const letzteBestellung = textfeld(k.letzteBestellung, null, 'date');
    const autoship = el('input');
    autoship.type = 'checkbox';
    autoship.checked = !!k.autoship;
    const partnerSeit = textfeld(k.partnerSeit, null, 'date');
    const rang = textfeld(k.rang, 'Manager, Sales Manager …');

    /* Aufbau */
    inhalt.append(el('div', 'abschnitt-titel', 'Person'));
    const namensreihe = el('div', 'reihe');
    namensreihe.append(feld('Vorname', vorname), feld('Nachname', nachname));
    inhalt.append(namensreihe);
    inhalt.append(feld('Telefon', telefon, 'Für Anruf und WhatsApp direkt aus der App.'));
    inhalt.append(feld('E-Mail', email));
    inhalt.append(feld('Ort', ort));
    inhalt.append(feld('Geburtstag', geburtstag, 'Erscheint rechtzeitig unter „Heute".'));

    inhalt.append(el('div', 'abschnitt-titel', 'Einordnung'));
    inhalt.append(feld('Status', typWahl));
    const stufeFeld = feld('Stand im Gespräch', stufeWahl);
    inhalt.append(stufeFeld);
    inhalt.append(feld('Quelle', quelleWahl));
    inhalt.append(feld('Empfohlen von', empfehlungWahl));

    const kundenblock = el('div');
    kundenblock.append(el('div', 'abschnitt-titel', 'Als Kunde'));
    kundenblock.append(feld('Kundennummer', kundennummer));
    kundenblock.append(feld('Produkte', produkte));
    kundenblock.append(feld('Letzte Bestellung', letzteBestellung));
    const autoshipZeile = el('label', 'datenzeile');
    autoshipZeile.style.cursor = 'pointer';
    autoshipZeile.append(autoship);
    autoshipZeile.append(el('div', 'datenzeile__wert',
      'Autoship aktiv — keine Nachbestell-Erinnerung'));
    kundenblock.append(autoshipZeile);
    inhalt.append(kundenblock);

    const partnerblock = el('div');
    partnerblock.append(el('div', 'abschnitt-titel', 'Als Teampartner'));
    partnerblock.append(feld('Partner seit', partnerSeit));
    partnerblock.append(feld('Rang', rang));
    partnerblock.append(feld('Sponsor', sponsorWahl,
      'Leer heißt: von dir persönlich eingeschrieben — deine Erstlinie.'));
    inhalt.append(partnerblock);

    /* Schlagwörter */
    inhalt.append(el('div', 'abschnitt-titel', 'Schlagwörter'));
    const markenBox = el('div', 'marken');
    markenBox.style.marginBottom = '10px';
    const markenZeichnen = () => {
      markenBox.replaceChildren();
      tags.forEach((t) => {
        const m = el('span', 'marke', t);
        const weg = el('button', null, '×');
        weg.setAttribute('aria-label', `${t} entfernen`);
        weg.onclick = () => { tags = tags.filter((x) => x !== t); markenZeichnen(); };
        m.append(weg);
        markenBox.append(m);
      });
      if (!tags.length) markenBox.append(el('span', 'fusstext',
        'Zum Beispiel: Sportler, Schichtdienst, Empfehlungsgeber, Messe 2026'));
    };
    markenZeichnen();
    inhalt.append(markenBox);
    const neueMarke = textfeld('', 'Schlagwort und Enter');
    neueMarke.onkeydown = (e) => {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      const wert = neueMarke.value.trim();
      if (wert && !tags.includes(wert)) tags.push(wert);
      neueMarke.value = '';
      markenZeichnen();
    };
    inhalt.append(neueMarke);

    inhalt.append(el('div', 'abschnitt-titel', 'Notiz'));
    inhalt.append(notiz);

    /* Rollenabhängige Blöcke ein- und ausblenden */
    const blockeSetzen = () => {
      stufeFeld.classList.toggle('versteckt', typWahl.value !== 'interessent');
      kundenblock.classList.toggle('versteckt', typWahl.value !== 'kunde');
      partnerblock.classList.toggle('versteckt', typWahl.value !== 'partner');
    };
    typWahl.onchange = blockeSetzen;
    blockeSetzen();

    const sichern = el('button', 'knopf', 'Speichern');
    sichern.style.marginTop = '18px';
    sichern.onclick = () => {
      if (!vorname.value.trim() && !nachname.value.trim()) {
        meldung('Ohne Namen geht es nicht');
        vorname.focus();
        return;
      }
      Object.assign(k, {
        vorname: vorname.value.trim(),
        nachname: nachname.value.trim(),
        telefon: telefon.value.trim(),
        email: email.value.trim(),
        ort: ort.value.trim(),
        geburtstag: geburtstag.value,
        typ: typWahl.value,
        stufe: stufeWahl.value,
        quelle: quelleWahl.value,
        empfehlungVon: empfehlungWahl.value,
        sponsor: sponsorWahl.value,
        kundennummer: kundennummer.value.trim(),
        produkte: produkte.value.trim(),
        letzteBestellung: letzteBestellung.value,
        autoship: autoship.checked,
        partnerSeit: partnerSeit.value,
        rang: rang.value.trim(),
        notiz: notiz.value.trim(),
        tags
      });

      if (vorhanden) {
        Object.assign(vorhanden, k);
        Speicher.sichern();
        meldung('Gespeichert');
      } else {
        Speicher.daten.kontakte.push(k);
        Speicher.sichern();
        const folge = kadenzAnlegen(k);
        meldung(folge
          ? `Angelegt · erster Schritt am ${datumKurz(folge.faellig)}`
          : 'Angelegt');
      }
      schliessen();
      if (beiFertig) beiFertig();
      else if (!vorhanden) kontaktBlatt(k.id);
    };
    inhalt.append(sichern);
  });
}

/* =========================================================================
   Aufgabe anlegen und bearbeiten
   ========================================================================= */
function aufgabenBlatt(vorhandene, beiFertig, kontaktVorgabe) {
  blattOeffnen(vorhandene ? 'Follow-up ändern' : 'Follow-up planen', (inhalt, schliessen) => {
    const auswahl = aktiveKontakte().sort((a, b) => name(a).localeCompare(name(b), 'de'));
    if (!auswahl.length) {
      inhalt.append(leerzustand('Noch keine Kontakte',
        'Lege zuerst einen Kontakt an — ein Follow-up braucht jemanden, dem es gilt.'));
      return;
    }

    const kontaktWahl = auswahlfeld(
      Object.fromEntries(auswahl.map((k) => [k.id, name(k)])),
      vorhandene ? vorhandene.kontaktId : (kontaktVorgabe || auswahl[0].id));
    const artWahl = auswahlfeld(
      Object.fromEntries(Object.entries(ARTEN).map(([w, [n]]) => [w, n])),
      vorhandene ? vorhandene.art : 'anruf');
    const datum = textfeld(vorhandene ? vorhandene.faellig : plusTage(1), null, 'date');
    const text = textfeld(vorhandene ? vorhandene.text : '', 'Was ist zu tun?');

    if (!vorhandene && kontaktVorgabe) {
      const k = kontakt(kontaktVorgabe);
      const v = k && kadenzVorschlag(k);
      if (v) { text.value = v.text; datum.value = plusTage(v.tage); artWahl.value = v.art; }
    }

    inhalt.append(feld('Kontakt', kontaktWahl));
    inhalt.append(feld('Art', artWahl));
    inhalt.append(feld('Fällig am', datum));
    inhalt.append(feld('Aufgabe', text));

    /* Schnellwahl fürs Datum — schneller als der Datumswähler des Systems. */
    const schnell = el('div', 'filter');
    [['Heute', 0], ['Morgen', 1], ['In 3 Tagen', 3], ['1 Woche', 7],
     ['2 Wochen', 14], ['1 Monat', 30]].forEach(([beschriftung, tage]) => {
      const c = el('button', 'chip', beschriftung);
      c.onclick = () => {
        datum.value = plusTage(tage);
        schnell.querySelectorAll('.chip').forEach((x) => x.setAttribute('aria-pressed', 'false'));
        c.setAttribute('aria-pressed', 'true');
      };
      schnell.append(c);
    });
    inhalt.append(schnell);

    const sichern = el('button', 'knopf', 'Speichern');
    sichern.onclick = () => {
      if (!datum.value) { meldung('Ohne Datum kein Follow-up'); return; }
      if (vorhandene) {
        Object.assign(vorhandene, {
          kontaktId: kontaktWahl.value, art: artWahl.value,
          faellig: datum.value, text: text.value.trim()
        });
        Speicher.sichern();
        meldung('Geändert');
      } else {
        aufgabeAnlegen(kontaktWahl.value, datum.value, artWahl.value, text.value.trim());
        meldung(`Geplant für ${datumKurz(datum.value)}`);
      }
      schliessen();
      if (beiFertig) beiFertig();
    };
    inhalt.append(sichern);

    if (vorhandene) {
      const weg = el('button', 'knopf knopf--klein knopf--warn', 'Follow-up löschen');
      weg.style.cssText = 'width:100%;margin-top:10px';
      weg.onclick = () => {
        Speicher.daten.aufgaben = Speicher.daten.aufgaben.filter((a) => a.id !== vorhandene.id);
        Speicher.sichern();
        meldung('Gelöscht');
        schliessen();
        if (beiFertig) beiFertig();
      };
      inhalt.append(weg);
    }
  });
}

/* =========================================================================
   Ansicht: Follow-up
   ========================================================================= */
function ansichtFollowup(ziel) {
  const filter = el('div', 'filter');
  const filterOptionen = { offen: 'Offen', woche: 'Diese Woche', alle: 'Alle offenen', erledigt: 'Erledigt' };
  Object.entries(filterOptionen).forEach(([wert, beschriftung]) => {
    const c = el('button', 'chip', beschriftung);
    c.setAttribute('aria-pressed', String(App.aufgabenFilter === wert));
    c.onclick = () => { App.aufgabenFilter = wert; neuZeichnen(); };
    filter.append(c);
  });
  ziel.append(filter);

  if (App.aufgabenFilter === 'erledigt') {
    const erledigt = Speicher.daten.aufgaben
      .filter((a) => a.erledigt)
      .sort((a, b) => (b.erledigtAm || '').localeCompare(a.erledigtAm || ''))
      .slice(0, 60);
    if (!erledigt.length) {
      ziel.append(leerzustand('Nichts erledigt', 'Sobald du Follow-ups abhakst, stehen sie hier.'));
      return;
    }
    abschnitt(ziel, 'Zuletzt erledigt', erledigt.length);
    erledigt.forEach((a) => ziel.append(aufgabenzeile(a, neuZeichnen)));
    return;
  }

  const offen = offeneAufgaben().sort((a, b) => a.faellig.localeCompare(b.faellig));
  if (!offen.length) {
    ziel.append(leerzustand('Kein offenes Follow-up',
      'Alles abgearbeitet. Plane den nächsten Schritt bei den Kontakten, ' +
      'die noch keinen haben.'));
    const ohne = ohneNaechstenSchritt();
    if (ohne.length) {
      const knopf = el('button', 'knopf', `${ohne.length} Kontakte ohne Schritt anzeigen`);
      knopf.onclick = () => {
        App.ansicht = 'kontakte';
        App.kontaktFilter = 'ohneschritt';
        neuZeichnen();
      };
      ziel.append(knopf);
    }
    return;
  }

  const h = heuteText();
  const wocheEnde = plusTage(7);
  const gruppen = [
    ['Überfällig', offen.filter((a) => a.faellig < h), true],
    ['Heute', offen.filter((a) => a.faellig === h), false],
    ['Morgen', offen.filter((a) => a.faellig === plusTage(1)), false],
    ['Diese Woche', offen.filter((a) => a.faellig > plusTage(1) && a.faellig <= wocheEnde), false],
    ['Später', offen.filter((a) => a.faellig > wocheEnde), false]
  ];

  const sichtbar = App.aufgabenFilter === 'offen'
    ? gruppen.filter(([name]) => ['Überfällig', 'Heute', 'Morgen'].includes(name))
    : App.aufgabenFilter === 'woche'
      ? gruppen.filter(([name]) => name !== 'Später')
      : gruppen;

  let gezeigt = 0;
  sichtbar.forEach(([titel, liste, warn]) => {
    if (!liste.length) return;
    gezeigt += liste.length;
    abschnitt(ziel, titel, liste.length, warn);
    liste.forEach((a) => ziel.append(aufgabenzeile(a, neuZeichnen)));
  });

  if (!gezeigt) {
    ziel.append(leerzustand('Hier ist nichts',
      `${offen.length} offene Follow-ups liegen weiter in der Zukunft. ` +
      'Wechsle auf „Alle offenen", um sie zu sehen.'));
  }
}

/* =========================================================================
   Ansicht: Team
   ========================================================================= */
function ansichtTeam(ziel) {
  const partner = aktiveKontakte().filter((k) => k.typ === 'partner');
  const kunden = aktiveKontakte().filter((k) => k.typ === 'kunde');

  if (!partner.length && !kunden.length) {
    ziel.append(leerzustand('Noch kein Team',
      'Sobald ein Kontakt Kunde oder Teampartner wird, siehst du ihn hier — ' +
      'samt Struktur und Betreuungsstand.'));
    return;
  }

  /* Kennzahlen */
  const erstlinie = partner.filter((k) => !k.sponsor);
  const neu30 = partner.filter((k) => k.partnerSeit && tageBis(k.partnerSeit) >= -30);
  const karte = el('div', 'karte');
  karte.append(el('div', 'karte__titel', 'Überblick'));
  const werte = el('div', 'werte werte--drei');
  werte.append(wertkachel('Partner', zahl(partner.length),
    `${erstlinie.length} in der Erstlinie`));
  werte.append(wertkachel('Kunden', zahl(kunden.length),
    `${kunden.filter((k) => k.autoship).length} mit Autoship`));
  werte.append(wertkachel('Neu (30 T.)', zahl(neu30.length),
    neu30.length ? 'Startphase begleiten' : 'nichts Neues'));
  karte.append(werte);
  ziel.append(karte);

  /* Betreuung */
  const faellig = betreuungFaellig();
  if (faellig.length) {
    abschnitt(ziel, 'Betreuung fällig', faellig.length, true);
    const erklaerung = el('div', 'fusstext');
    erklaerung.style.margin = '-4px 2px 10px';
    erklaerung.textContent =
      `Partner nach ${Speicher.daten.einstellungen.betreuungPartner} Tagen ohne Kontakt, ` +
      `Kunden nach ${Speicher.daten.einstellungen.betreuungKunde}.`;
    ziel.append(erklaerung);
    faellig.forEach(({ kontakt: k, tage }) => {
      ziel.append(kontaktzeile(k, `${TYPEN[k.typ]} · seit ${tage} Tagen kein Kontakt`, 'warn'));
    });
  }

  /* Struktur */
  if (partner.length) {
    abschnitt(ziel, 'Struktur', partner.length);
    const baum = el('div');
    let gezeichnet = 0;

    const zeichneEbene = (sponsorId, ebene) => {
      const kinder = partner
        .filter((k) => (k.sponsor || '') === sponsorId)
        .sort((a, b) => name(a).localeCompare(name(b), 'de'));
      kinder.forEach((k) => {
        gezeichnet++;
        const eigene = partner.filter((x) => x.sponsor === k.id).length;
        const letzter = letzterKontaktDatum(k);
        const zeile = kontaktzeile(k, [
          `Ebene ${ebene}`,
          eigene ? `${eigene} eigene` : null,
          k.rang || null,
          letzter ? `zuletzt ${vorTagenText(letzter)}` : 'kein Verlauf'
        ].filter(Boolean).join(' · '));
        // Einrückung zeigt die Tiefe, gedeckelt bei Ebene 5 — sonst bleibt
        // auf dem Handy für den Namen kein Platz mehr.
        zeile.style.marginLeft = `${Math.min(ebene - 1, 4) * 14}px`;
        baum.append(zeile);
        zeichneEbene(k.id, ebene + 1);
      });
    };
    zeichneEbene('', 1);

    // Partner, deren Sponsor gelöscht wurde oder im Kreis zeigt, würden sonst
    // unsichtbar. Sie kommen ans Ende, damit die Liste vollständig bleibt.
    const gezeigt = new Set();
    const sammle = (sponsorId) => {
      partner.filter((k) => (k.sponsor || '') === sponsorId).forEach((k) => {
        if (gezeigt.has(k.id)) return;
        gezeigt.add(k.id);
        sammle(k.id);
      });
    };
    sammle('');
    const verwaist = partner.filter((k) => !gezeigt.has(k.id));
    verwaist.forEach((k) => baum.append(kontaktzeile(k, 'Sponsor nicht auffindbar')));

    ziel.append(baum);
    if (!gezeichnet && !verwaist.length) {
      ziel.append(leerzustand('Keine Struktur hinterlegt',
        'Trage bei den Partnern ein, wer wen eingeschrieben hat.', true));
    }
  }

  /* Kunden */
  if (kunden.length) {
    abschnitt(ziel, 'Kunden', kunden.length);
    kunden
      .sort((a, b) => (a.letzteBestellung || '').localeCompare(b.letzteBestellung || ''))
      .forEach((k) => {
        const teile = [];
        if (k.letzteBestellung) teile.push(`Bestellung ${vorTagenText(k.letzteBestellung)}`);
        if (k.autoship) teile.push('Autoship');
        if (k.produkte) teile.push(k.produkte);
        const ueberfaellig = k.letzteBestellung && !k.autoship &&
          tageBis(plusTage(Speicher.daten.einstellungen.nachbestellung, k.letzteBestellung)) < 0;
        ziel.append(kontaktzeile(k, teile.join(' · ') || 'Keine Bestelldaten',
          ueberfaellig ? 'acht' : null));
      });
  }
}

/* =========================================================================
   Ansicht: Zahlen
   ========================================================================= */
function ansichtZahlen(ziel) {
  const alle = aktiveKontakte();
  if (!alle.length) {
    ziel.append(leerzustand('Noch nichts zu rechnen',
      'Sobald Kontakte in der Datenbank stehen, siehst du hier deine Aktivität, ' +
      'den Trichter und die Quellen, die wirklich tragen.'));
    return;
  }

  const interessenten = alle.filter((k) => k.typ === 'interessent');
  const kunden = alle.filter((k) => k.typ === 'kunde');
  const partner = alle.filter((k) => k.typ === 'partner');

  /* Bestand */
  const bestand = el('div', 'karte');
  bestand.append(el('div', 'karte__titel', 'Bestand'));
  const werte = el('div', 'werte');
  werte.append(wertkachel('Kontakte', zahl(alle.length),
    `${Speicher.daten.kontakte.filter((k) => k.archiviert).length} archiviert`));
  werte.append(wertkachel('Interessenten', zahl(interessenten.length),
    `${interessenten.filter((k) => naechsterSchritt(k.id)).length} mit Termin`));
  werte.append(wertkachel('Kunden', zahl(kunden.length)));
  werte.append(wertkachel('Partner', zahl(partner.length)));
  bestand.append(werte);
  ziel.append(bestand);

  /* Aktivität der letzten 30 Tage */
  const eintraege30 = alle.reduce((s, k) =>
    s + k.verlauf.filter((v) => tageBis(v.datum) >= -29).length, 0);
  const neu30 = alle.filter((k) => tageBis(k.angelegt) >= -29).length;
  const abschluesse30 = alle.filter((k) =>
    (k.typ === 'kunde' || k.typ === 'partner') &&
    k.verlauf.some((v) => v.text && v.text.startsWith('Neuer Status:') && tageBis(v.datum) >= -29)
  ).length;

  const aktivitaet = el('div', 'karte');
  aktivitaet.append(el('div', 'karte__titel', 'Letzte 30 Tage'));
  const werte2 = el('div', 'werte werte--drei');
  werte2.append(wertkachel('Kontakte', zahl(eintraege30), 'Gespräche, Nachrichten'));
  werte2.append(wertkachel('Neu erfasst', zahl(neu30), 'Namen dazugekommen'));
  werte2.append(wertkachel('Abschlüsse', zahl(abschluesse30), 'Kunde oder Partner'));
  aktivitaet.append(werte2);
  aktivitaet.append(wochendiagramm());
  aktivitaet.append(el('div', 'fusstext',
    'Kontakte je Woche, die letzten acht Wochen. Was hier flach wird, ' +
    'wird zwei Monate später in der Provision flach.'));
  ziel.append(aktivitaet);

  /* Trichter */
  const trichterKarte = el('div', 'karte');
  trichterKarte.append(el('div', 'karte__titel', 'Trichter'));
  const stufenZahlen = STUFEN.map(([wert, beschriftung]) => [
    beschriftung, interessenten.filter((k) => k.stufe === wert).length
  ]);
  stufenZahlen.push(['Kunde oder Partner', kunden.length + partner.length]);
  const maximum = Math.max(1, ...stufenZahlen.map(([, n]) => n));

  const trichter = el('div', 'trichter');
  stufenZahlen.forEach(([beschriftung, n]) => {
    const zeile = el('div', 'trichter__stufe');
    zeile.append(el('div', 'trichter__name', beschriftung));
    const aussen = el('div', 'trichter__balken-aussen');
    const balken = el('div', 'trichter__balken');
    balken.style.width = `${Math.round((n / maximum) * 100)}%`;
    aussen.append(balken);
    zeile.append(aussen, el('div', 'trichter__zahl', zahl(n)));
    trichter.append(zeile);
  });
  trichterKarte.append(trichter);

  const gesamtEingang = alle.length;
  const gewonnen = kunden.length + partner.length;
  trichterKarte.append(el('div', 'fusstext',
    `${zahl(gewonnen)} von ${zahl(gesamtEingang)} erfassten Kontakten sind heute Kunde ` +
    `oder Partner — ${Math.round((gewonnen / gesamtEingang) * 100)} Prozent.`));
  ziel.append(trichterKarte);

  /* Quellen */
  const quellenKarte = el('div', 'karte');
  quellenKarte.append(el('div', 'karte__titel', 'Woher sie kommen'));
  const nachQuelle = {};
  alle.forEach((k) => {
    const q = k.quelle || 'sonstige';
    if (!nachQuelle[q]) nachQuelle[q] = { gesamt: 0, gewonnen: 0 };
    nachQuelle[q].gesamt++;
    if (k.typ === 'kunde' || k.typ === 'partner') nachQuelle[q].gewonnen++;
  });
  const sortiert = Object.entries(nachQuelle).sort((a, b) => b[1].gesamt - a[1].gesamt);
  sortiert.forEach(([q, z]) => {
    const zeile = el('div', 'datenzeile');
    zeile.append(el('div', 'datenzeile__label', QUELLEN[q] || q));
    const quote = Math.round((z.gewonnen / z.gesamt) * 100);
    // Geschütztes Leerzeichen vor dem Prozentzeichen: Sonst rutscht es auf
    // dem schmalen Handydisplay allein in die nächste Zeile.
    zeile.append(el('div', 'datenzeile__wert',
      `${z.gesamt} ${z.gesamt === 1 ? 'Kontakt' : 'Kontakte'} · ` +
      `${z.gewonnen} gewonnen · ${quote} %`));
    quellenKarte.append(zeile);
  });
  if (sortiert.length > 1) {
    const beste = sortiert.slice().sort((a, b) =>
      (b[1].gewonnen / b[1].gesamt) - (a[1].gewonnen / a[1].gesamt))[0];
    quellenKarte.append(el('div', 'fusstext',
      `Beste Quote: ${QUELLEN[beste[0]] || beste[0]}. Dort lohnt sich mehr Aufwand.`));
  }
  ziel.append(quellenKarte);

  /* Hygiene der Datenbank */
  const hygiene = el('div', 'karte');
  hygiene.append(el('div', 'karte__titel', 'Pflegezustand'));
  const ohne = ohneNaechstenSchritt().length;
  const ueber = ueberfaellig().length;
  const ohneTelefon = alle.filter((k) => !k.telefon && !k.email).length;
  const werte3 = el('div', 'werte werte--drei');
  werte3.append(wertkachel('Ohne Schritt', zahl(ohne), ohne ? 'nachplanen' : 'sauber',
    ohne ? 'warn' : 'gut'));
  werte3.append(wertkachel('Überfällig', zahl(ueber), ueber ? 'abarbeiten' : 'sauber',
    ueber ? 'warn' : 'gut'));
  werte3.append(wertkachel('Ohne Kontaktweg', zahl(ohneTelefon),
    ohneTelefon ? 'ergänzen' : 'vollständig', ohneTelefon ? 'warn' : 'gut'));
  hygiene.append(werte3);
  ziel.append(hygiene);
}

/** Balken je Kalenderwoche, acht Wochen zurück. */
function wochendiagramm() {
  const wochen = [];
  for (let i = 7; i >= 0; i--) {
    const bis = -i * 7;
    const von = bis - 6;
    let anzahl = 0;
    aktiveKontakte().forEach((k) => {
      k.verlauf.forEach((v) => {
        const t = tageBis(v.datum);
        if (t >= von && t <= bis) anzahl++;
      });
    });
    const ende = plusTage(bis);
    wochen.push({ anzahl, beschriftung: datumKurz(ende).replace(/\.\d\d$/, '.') });
  }

  const breite = 320, hoehe = 150, unten = 122, links = 4;
  const maximum = Math.max(1, ...wochen.map((w) => w.anzahl));
  const saeulenBreite = (breite - links * 2) / wochen.length;

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'diagramm');
  svg.setAttribute('viewBox', `0 0 ${breite} ${hoehe}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label',
    'Kontakte je Woche: ' + wochen.map((w) => w.anzahl).join(', '));

  const mach = (tag, attribute) => {
    const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.entries(attribute).forEach(([k, v]) => e.setAttribute(k, v));
    return e;
  };

  wochen.forEach((w, i) => {
    const h = Math.round((w.anzahl / maximum) * 96);
    const x = links + i * saeulenBreite + saeulenBreite * 0.18;
    const b = saeulenBreite * 0.64;
    svg.append(mach('rect', {
      class: i === wochen.length - 1 ? 'saeule' : 'saeule saeule--schwach',
      x, y: unten - Math.max(h, 2), width: b, height: Math.max(h, 2), rx: 3
    }));
    const zahlText = mach('text', {
      class: 'beschriftung', x: x + b / 2, y: unten - Math.max(h, 2) - 5,
      'text-anchor': 'middle'
    });
    zahlText.textContent = w.anzahl || '';
    svg.append(zahlText);

    const label = mach('text', {
      class: 'beschriftung', x: x + b / 2, y: unten + 15, 'text-anchor': 'middle'
    });
    label.textContent = w.beschriftung;
    svg.append(label);
  });

  svg.append(mach('line', { class: 'achse', x1: links, y1: unten + 1, x2: breite - links, y2: unten + 1 }));
  return svg;
}

/* =========================================================================
   Einstellungen
   ========================================================================= */
function einstellungenBlatt() {
  blattOeffnen('Einstellungen', (inhalt, schliessen, neu) => {
    const e = Speicher.daten.einstellungen;

    /* Darstellung */
    const darstellung = el('div', 'karte');
    darstellung.append(el('div', 'karte__titel', 'Darstellung'));
    const modus = el('div', 'modus');
    [['hell', 'Hell', 'sonne'], ['dunkel', 'Dunkel', 'mond'], ['system', 'System', 'system']]
      .forEach(([wert, beschriftung, symbol]) => {
        const b = el('button');
        b.innerHTML = ikon(symbol);
        b.append(el('span', null, beschriftung));
        b.setAttribute('aria-pressed', String(Modus.gewaehlt() === wert));
        b.onclick = () => {
          Modus.setzen(wert);
          modus.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', 'false'));
          b.setAttribute('aria-pressed', 'true');
        };
        modus.append(b);
      });
    darstellung.append(modus);
    inhalt.append(darstellung);

    /* Kadenz */
    const kadenz = el('div', 'karte');
    kadenz.append(el('div', 'karte__titel', 'Follow-up-Rhythmus'));
    const erklaerung = el('p', null,
      'Nach jeder Statusänderung legt die App den nächsten Schritt selbst an. ' +
      'Hier stellst du ein, wie viele Tage sie dabei rechnet.');
    erklaerung.style.cssText = 'margin:0 0 14px;font-size:13.5px;color:var(--ink-soft)';
    kadenz.append(erklaerung);

    const felder = [
      ['nachErstkontakt', 'Nach dem Erstkontakt nachfassen'],
      ['nachTermin', 'Vor dem vereinbarten Termin erinnern'],
      ['nachPraesentation', 'Nach der Präsentation nachfassen'],
      ['nachEntscheidung', 'Entscheidung nachfassen'],
      ['produktcheck', 'Neukunde nach Produkten fragen'],
      ['nachbestellung', 'Nachbestellung erwarten nach'],
      ['startgespraech', 'Startgespräch mit neuem Partner'],
      ['betreuungKunde', 'Kunde gilt als vernachlässigt nach'],
      ['betreuungPartner', 'Partner gilt als vernachlässigt nach'],
      ['geburtstagVorlauf', 'Geburtstage vorher anzeigen']
    ];
    felder.forEach(([schluessel, beschriftung]) => {
      const eingabe = textfeld(String(e[schluessel]), null, 'number');
      eingabe.min = '0';
      eingabe.max = '365';
      eingabe.onchange = () => {
        const wert = parseInt(eingabe.value, 10);
        if (Number.isNaN(wert) || wert < 0) {
          eingabe.value = String(e[schluessel]);
          return;
        }
        e[schluessel] = wert;
        Speicher.sichern();
      };
      kadenz.append(feld(`${beschriftung} (Tage)`, eingabe));
    });

    const vorwahl = textfeld(e.laendervorwahl, '49');
    vorwahl.onchange = () => {
      e.laendervorwahl = vorwahl.value.replace(/\D/g, '') || '49';
      vorwahl.value = e.laendervorwahl;
      Speicher.sichern();
    };
    kadenz.append(feld('Ländervorwahl für WhatsApp', vorwahl,
      'Ohne Plus. Aus einer 0170… wird damit die internationale Nummer.'));

    const zurueck = el('button', 'knopf knopf--zweit knopf--klein', 'Auf Vorgaben zurücksetzen');
    zurueck.style.cssText = 'width:100%;margin-top:6px';
    zurueck.onclick = () => {
      Speicher.daten.einstellungen = Object.assign({}, VORGABEN);
      Speicher.sichern();
      meldung('Zurückgesetzt');
      neu();
    };
    kadenz.append(zurueck);
    inhalt.append(kadenz);

    /* Daten */
    const daten = el('div', 'karte');
    daten.append(el('div', 'karte__titel', 'Daten sichern'));
    const dp = el('p', null,
      `${zahl(Speicher.daten.kontakte.length)} Kontakte, ` +
      `${zahl(Speicher.daten.aufgaben.length)} Follow-ups, ` +
      `${zahl(Speicher.daten.kontakte.reduce((s, k) => s + k.verlauf.length, 0))} Verlaufseinträge. ` +
      'Alles liegt ausschließlich auf diesem Gerät. Geht es verloren, sind ' +
      'die Daten weg — sichere sie regelmäßig.');
    dp.style.cssText = 'margin:0 0 12px;font-size:13.5px;color:var(--ink-soft)';
    daten.append(dp);

    const exportKnopf = el('button', 'knopf', 'Sicherung exportieren (JSON)');
    exportKnopf.onclick = datenExportieren;
    daten.append(exportKnopf);

    const csvKnopf = el('button', 'knopf knopf--zweit', 'Kontakte als CSV exportieren');
    csvKnopf.style.marginTop = '8px';
    csvKnopf.onclick = csvExportieren;
    daten.append(csvKnopf);

    const importKnopf = el('button', 'knopf knopf--zweit', 'Sicherung einlesen');
    importKnopf.style.marginTop = '8px';
    importKnopf.onclick = () => datenImportieren(neu);
    daten.append(importKnopf);
    inhalt.append(daten);

    /* Beispieldaten und Zurücksetzen */
    const gefahr = el('div', 'karte');
    gefahr.append(el('div', 'karte__titel', 'Aufräumen'));

    if (!Speicher.daten.kontakte.length) {
      const demo = el('button', 'knopf knopf--zweit', 'Beispieldaten laden');
      demo.onclick = () => {
        beispieldaten();
        meldung('Beispieldaten geladen');
        neu();
      };
      gefahr.append(demo);
    }

    const erledigteWeg = el('button', 'knopf knopf--zweit', 'Erledigte Follow-ups löschen');
    erledigteWeg.style.marginTop = '8px';
    erledigteWeg.onclick = () => {
      const vorher = Speicher.daten.aufgaben.length;
      Speicher.daten.aufgaben = Speicher.daten.aufgaben.filter((a) => !a.erledigt);
      Speicher.sichern();
      meldung(`${vorher - Speicher.daten.aufgaben.length} gelöscht`);
      neu();
    };
    gefahr.append(erledigteWeg);

    const alles = el('button', 'knopf knopf--warn', 'Alle Daten löschen');
    alles.style.marginTop = '8px';
    alles.onclick = () => {
      if (!confirm('Wirklich alles löschen? Kontakte, Verlauf und Follow-ups ' +
                   'sind danach weg. Vorher exportieren!')) return;
      if (!confirm('Letzte Sicherheitsfrage: unwiderruflich löschen?')) return;
      Speicher.zuruecksetzen();
      meldung('Alles gelöscht');
      schliessen();
    };
    gefahr.append(alles);
    inhalt.append(gefahr);

    /* Rechtliches */
    const recht = el('div', 'hinweis');
    recht.append(el('div', 'hinweis__titel', 'Verantwortung für fremde Daten'));
    recht.append(el('p', null,
      'In dieser Datenbank stehen personenbezogene Daten anderer Menschen. ' +
      'Erfasse nur, was du für die Betreuung brauchst, gib niemandem sonst ' +
      'Zugriff auf dieses Gerät und lösche Kontakte vollständig, sobald ' +
      'jemand nicht mehr von dir hören möchte. Ein Widerspruch gegen die ' +
      'Kontaktaufnahme wiegt schwerer als jede Wiedervorlage.'));
    inhalt.append(recht);

    inhalt.append(el('div', 'fusstext',
      'FitLine Business — persönliches Arbeitsmittel für den eigenen ' +
      'Vertriebsaufbau. Keine Anwendung von PM-International, keine ' +
      'Verbindung zu deren Systemen.'));
  });
}

/* --- Export und Import --------------------------------------------------- */
function dateiAnbieten(inhalt, dateiname, typ) {
  const blob = new Blob([inhalt], { type: typ });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = dateiname;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function datenExportieren() {
  const inhalt = JSON.stringify({
    app: 'fitline-business',
    version: 1,
    erstellt: new Date().toISOString(),
    daten: Speicher.daten
  }, null, 2);
  dateiAnbieten(inhalt, `fitline-business-${heuteText()}.json`, 'application/json');
  meldung('Sicherung erstellt');
}

function csvExportieren() {
  const spalten = [
    ['Vorname', (k) => k.vorname],
    ['Nachname', (k) => k.nachname],
    ['Status', (k) => TYPEN[k.typ]],
    ['Stand', (k) => k.typ === 'interessent' ? (STUFENNAME[k.stufe] || '') : ''],
    ['Telefon', (k) => k.telefon],
    ['E-Mail', (k) => k.email],
    ['Ort', (k) => k.ort],
    ['Geburtstag', (k) => k.geburtstag],
    ['Quelle', (k) => QUELLEN[k.quelle] || ''],
    ['Kundennummer', (k) => k.kundennummer],
    ['Produkte', (k) => k.produkte],
    ['Letzte Bestellung', (k) => k.letzteBestellung],
    ['Autoship', (k) => k.autoship ? 'ja' : 'nein'],
    ['Partner seit', (k) => k.partnerSeit],
    ['Rang', (k) => k.rang],
    ['Sponsor', (k) => k.sponsor ? name(kontakt(k.sponsor) || {}) : ''],
    ['Schlagwörter', (k) => (k.tags || []).join(', ')],
    ['Letzter Kontakt', (k) => letzterKontaktDatum(k) || ''],
    ['Nächster Schritt', (k) => {
      const s = naechsterSchritt(k.id);
      return s ? `${s.faellig} ${s.text}` : '';
    }],
    ['Notiz', (k) => (k.notiz || '').replace(/\r?\n/g, ' ')],
    ['Angelegt', (k) => k.angelegt]
  ];

  const feldMachen = (wert) => {
    const s = String(wert == null ? '' : wert);
    return /[";\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };

  const zeilen = [spalten.map(([kopf]) => feldMachen(kopf)).join(';')];
  Speicher.daten.kontakte.forEach((k) => {
    zeilen.push(spalten.map(([, hole]) => feldMachen(hole(k))).join(';'));
  });

  // BOM voran, sonst zeigt Excel unter Windows die Umlaute falsch an.
  dateiAnbieten('﻿' + zeilen.join('\r\n'),
    `fitline-kontakte-${heuteText()}.csv`, 'text/csv;charset=utf-8');
  meldung('CSV erstellt');
}

function datenImportieren(beiFertig) {
  const wahl = document.createElement('input');
  wahl.type = 'file';
  wahl.accept = 'application/json,.json';
  wahl.onchange = () => {
    const datei = wahl.files && wahl.files[0];
    if (!datei) return;
    const leser = new FileReader();
    leser.onload = () => {
      let geladen;
      try {
        geladen = JSON.parse(leser.result);
      } catch (e) {
        meldung('Datei nicht lesbar');
        return;
      }
      const daten = geladen && geladen.daten ? geladen.daten : geladen;
      if (!daten || !Array.isArray(daten.kontakte)) {
        meldung('Keine gültige Sicherung');
        return;
      }
      const anzahl = daten.kontakte.length;
      if (!confirm(`${anzahl} Kontakte einlesen? Der aktuelle Bestand ` +
                   `(${Speicher.daten.kontakte.length} Kontakte) wird dabei ersetzt.`)) return;
      Speicher.daten = daten;
      Speicher.aufraeumen();
      Speicher.sichern();
      meldung(`${anzahl} Kontakte eingelesen`);
      if (beiFertig) beiFertig();
      neuZeichnen();
    };
    leser.readAsText(datei);
  };
  wahl.click();
}

/* --- Beispieldaten ------------------------------------------------------- */
/** Ein kleiner, realistischer Bestand zum Ausprobieren. Nur ladbar, solange
 *  die Datenbank leer ist — echte Kontakte sollen nie mit erfundenen
 *  durcheinandergeraten. */
function beispieldaten() {
  if (Speicher.daten.kontakte.length) return;

  const machen = (vorname, nachname, felder) => Object.assign({
    id: neueId(), vorname, nachname, telefon: '', email: '', ort: '',
    geburtstag: '', typ: 'interessent', stufe: 'neu', quelle: 'direkt',
    empfehlungVon: '', sponsor: '', kundennummer: '', produkte: '',
    autoship: false, letzteBestellung: '', partnerSeit: '', rang: '',
    notiz: '', tags: [], angelegt: heuteText(), verlauf: [], archiviert: false
  }, felder);

  const anna = machen('Anna', 'Berger', {
    typ: 'partner', telefon: '0170 1234567', ort: 'Kassel',
    partnerSeit: plusTage(-260), rang: 'Manager', quelle: 'empfehlung',
    kundennummer: '90012345', angelegt: plusTage(-280),
    notiz: 'Physiotherapeutin, arbeitet viel mit Sportlern. Will nebenbei aufbauen.',
    tags: ['Sport', 'Erstlinie'],
    verlauf: [
      { id: neueId(), datum: plusTage(-9), art: 'treffen', text: 'Teamabend, drei neue Namen besprochen.' },
      { id: neueId(), datum: plusTage(-30), art: 'anruf', text: 'Zielgespräch fürs Quartal.' }
    ]
  });

  const tobias = machen('Tobias', 'Klein', {
    typ: 'partner', telefon: '0151 9876543', ort: 'Göttingen',
    partnerSeit: plusTage(-40), rang: 'Teampartner', quelle: 'empfehlung',
    sponsor: anna.id, angelegt: plusTage(-70),
    notiz: 'Kam über Anna. Braucht noch Sicherheit beim Erstgespräch.',
    tags: ['Neustart'],
    verlauf: [
      { id: neueId(), datum: plusTage(-26), art: 'treffen', text: 'Startgespräch, erste Namensliste erarbeitet.' }
    ]
  });

  const sabine = machen('Sabine', 'Wolf', {
    typ: 'kunde', telefon: '0176 5551234', email: 'sabine.wolf@beispiel.de',
    ort: 'Kassel', quelle: 'direkt', kundennummer: '90055512',
    produkte: 'Activize, Restorate', letzteBestellung: plusTage(-38),
    // Geburtstag in fünf Tagen, damit die Erinnerung im Beispiel auch auftaucht.
    geburtstag: '1979' + plusTage(5).slice(4),
    angelegt: plusTage(-120),
    notiz: 'Schichtdienst im Krankenhaus, Thema Energie am Nachmittag.',
    tags: ['Schichtdienst'],
    verlauf: [
      { id: neueId(), datum: plusTage(-38), art: 'nachbestellung', text: 'Bestellung aufgegeben' },
      { id: neueId(), datum: plusTage(-95), art: 'anruf', text: 'Erste Woche gut vertragen, mehr Energie.' }
    ]
  });

  const markus = machen('Markus', 'Reinhardt', {
    typ: 'kunde', telefon: '0162 3334455', ort: 'Baunatal',
    quelle: 'veranstaltung', produkte: 'Basics, PowerCocktail',
    letzteBestellung: plusTage(-12), autoship: true, angelegt: plusTage(-60),
    tags: ['Handball'],
    verlauf: [{ id: neueId(), datum: plusTage(-12), art: 'nachbestellung', text: 'Autoship läuft' }]
  });

  const julia = machen('Julia', 'Hoffmann', {
    telefon: '0170 4445566', ort: 'Fritzlar', stufe: 'praesentation',
    quelle: 'empfehlung', empfehlungVon: sabine.id, angelegt: plusTage(-11),
    notiz: 'Zwei Kinder, wenig Zeit, sucht etwas Nebenberufliches.',
    tags: ['Nebenverdienst'],
    verlauf: [
      { id: neueId(), datum: plusTage(-4), art: 'treffen', text: 'Geschäft vorgestellt, überlegt bis nächste Woche.' },
      { id: neueId(), datum: plusTage(-10), art: 'anruf', text: 'Ersten Kontakt über Sabine hergestellt.' }
    ]
  });

  const peter = machen('Peter', 'Lang', {
    telefon: '0157 2223344', ort: 'Kassel', stufe: 'kontaktiert',
    quelle: 'social', angelegt: plusTage(-5),
    verlauf: [{ id: neueId(), datum: plusTage(-5), art: 'nachricht', text: 'Auf Instagram geschrieben, Interesse an Ernährung.' }]
  });

  const dana = machen('Dana', 'Schuster', {
    telefon: '0159 8887766', ort: 'Melsungen', stufe: 'neu',
    quelle: 'empfehlung', empfehlungVon: anna.id, angelegt: plusTage(-1)
  });

  const heiko = machen('Heiko', 'Brandt', {
    typ: 'ruhend', telefon: '0176 1112233', ort: 'Homberg',
    quelle: 'direkt', angelegt: plusTage(-200),
    notiz: 'Aktuell kein Thema, Wiedervorlage im Frühjahr.',
    verlauf: [{ id: neueId(), datum: plusTage(-150), art: 'anruf', text: 'Freundlich abgesagt, offen für später.' }]
  });

  Speicher.daten.kontakte = [anna, tobias, sabine, markus, julia, peter, dana, heiko];
  Speicher.daten.aufgaben = [
    { id: neueId(), kontaktId: julia.id, faellig: plusTage(-2), art: 'anruf',
      text: 'Nachfassen: offene Fragen klären', erledigt: false, erledigtAm: null, erstellt: plusTage(-4) },
    { id: neueId(), kontaktId: peter.id, faellig: heuteText(), art: 'anruf',
      text: 'Nachfassen und Termin vereinbaren', erledigt: false, erledigtAm: null, erstellt: plusTage(-5) },
    { id: neueId(), kontaktId: dana.id, faellig: heuteText(), art: 'anruf',
      text: 'Erstkontakt aufnehmen', erledigt: false, erledigtAm: null, erstellt: plusTage(-1) },
    { id: neueId(), kontaktId: sabine.id, faellig: plusTage(2), art: 'nachbestellung',
      text: 'Nachbestellung ansprechen', erledigt: false, erledigtAm: null, erstellt: plusTage(-3) },
    { id: neueId(), kontaktId: tobias.id, faellig: plusTage(3), art: 'treffen',
      text: 'Erste eigene Kontakte durchgehen', erledigt: false, erledigtAm: null, erstellt: plusTage(-6) },
    { id: neueId(), kontaktId: heiko.id, faellig: plusTage(45), art: 'nachricht',
      text: 'Locker wieder melden', erledigt: false, erledigtAm: null, erstellt: plusTage(-150) }
  ];
  Speicher.sichern();
}

/* =========================================================================
   Gerüst: Ansichten, Reiter, Start
   ========================================================================= */
const ANSICHTEN = {
  heute:    ['Heute', ansichtHeute],
  kontakte: ['Kontakte', ansichtKontakte],
  followup: ['Follow-up', ansichtFollowup],
  team:     ['Team', ansichtTeam],
  zahlen:   ['Zahlen', ansichtZahlen]
};

function untertitel() {
  const alle = aktiveKontakte();
  switch (App.ansicht) {
    case 'heute': {
      const offen = faelligeAufgaben().length;
      return offen ? `${offen} ${offen === 1 ? 'Aufgabe' : 'Aufgaben'} fällig`
                   : 'nichts fällig';
    }
    case 'kontakte':
      return `${zahl(alle.length)} in der Datenbank`;
    case 'followup': {
      const offen = offeneAufgaben().length;
      return `${zahl(offen)} offen · ${ueberfaellig().length} überfällig`;
    }
    case 'team': {
      const partner = alle.filter((k) => k.typ === 'partner').length;
      const kunden = alle.filter((k) => k.typ === 'kunde').length;
      return `${partner} Partner · ${kunden} Kunden`;
    }
    case 'zahlen':
      return 'Aktivität, Trichter, Quellen';
    default:
      return '';
  }
}

function neuZeichnen() {
  const [titel, aufbauen] = ANSICHTEN[App.ansicht];
  document.getElementById('kopf-titel').textContent = titel;
  document.getElementById('kopf-sub').textContent = untertitel();

  const inhalt = document.getElementById('inhalt');
  inhalt.replaceChildren();
  aufbauen(inhalt);

  document.querySelectorAll('.tab').forEach((t) => {
    t.setAttribute('aria-selected', String(t.dataset.ansicht === App.ansicht));
  });
  reiterZaehler();

  // Der Schnellknopf legt in der Follow-up-Ansicht eine Aufgabe an, sonst
  // einen Kontakt — das ist jeweils das, was man dort will.
  const knopf = document.getElementById('knopf-neu');
  knopf.setAttribute('aria-label',
    App.ansicht === 'followup' ? 'Neues Follow-up' : 'Neuer Kontakt');
}

function reiterZaehler() {
  const reiter = document.querySelector('.tab[data-ansicht="followup"]');
  if (!reiter) return;
  reiter.querySelectorAll('.tab__punkt').forEach((p) => p.remove());
  const ueber = ueberfaellig().length;
  const faellig = faelligeAufgaben().length;
  if (!faellig) return;
  const punkt = el('span', 'tab__punkt' + (ueber ? ' tab__punkt--warn' : ''),
    faellig > 99 ? '99+' : String(faellig));
  punkt.setAttribute('aria-hidden', 'true');
  reiter.append(punkt);
}

function starten() {
  Speicher.laden();
  Modus.anwenden();
  Modus.beobachten();

  document.querySelectorAll('.tab').forEach((t) => {
    t.onclick = () => {
      App.ansicht = t.dataset.ansicht;
      document.getElementById('inhalt').scrollIntoView({ block: 'start' });
      window.scrollTo(0, 0);
      neuZeichnen();
    };
  });

  document.getElementById('knopf-einstellungen').onclick = einstellungenBlatt;

  document.getElementById('knopf-suche').onclick = () => {
    App.ansicht = 'kontakte';
    App.sucheFokussieren = true;
    neuZeichnen();
  };

  document.getElementById('knopf-neu').onclick = () => {
    if (App.ansicht === 'followup') aufgabenBlatt(null, neuZeichnen);
    else kontaktBearbeiten(null);
  };

  neuZeichnen();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('sw.js').catch((e) =>
        console.warn('Service Worker nicht registriert.', e));
    });
  }

  // Über Nacht offen gelassen: Beim Zurückkehren sind Datumsangaben sonst
  // falsch — „heute fällig" wäre dann noch das Gestern.
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !document.querySelector('.blatt')) neuZeichnen();
  });
}

starten();
