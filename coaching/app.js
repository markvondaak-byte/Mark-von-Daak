/* =========================================================================
   Coaching — App
   Kein Framework, kein Build. Reines JavaScript, damit die App ohne
   Werkzeugkette wartbar bleibt und offline ohne Ballast läuft.

   Inhalte (Übungen, Lebensmittel, Rezepte) stehen in daten/*.json. Alles,
   was der Klient einträgt, bleibt im localStorage seines Geräts; Fotos
   liegen wegen ihrer Größe in IndexedDB. Es gibt keinen Server — der
   wöchentliche Check-in geht als fertiger Text per WhatsApp oder E-Mail an
   den Coach.
   ========================================================================= */
'use strict';
/* --- Speicher ----------------------------------------------------------- */

const SCHLUESSEL = 'coaching.v1';

const STANDARD_GEWOHNHEITEN = [
  'Gemüse zu jeder Hauptmahlzeit',
  '10 Minuten Mobility oder Dehnen',
  '30 Minuten vor dem Schlafen kein Bildschirm',
  'Bewusst gegessen — ohne Handy'
];

const Speicher = {
  daten: null,

  leer() {
    return {
      version: 1,
      profil: null,
      ziele: null,
      // Bewusst leer: Den Kontakt des Coachs trägt der Klient selbst ein.
      coach: { whatsapp: '', email: '', checkinTag: 0 },
      plan: { tage: [] },
      workouts: [],
      aktiv: null,
      tage: {},
      gewohnheiten: STANDARD_GEWOHNHEITEN.map((name, i) => ({ id: 'g' + (i + 1), name })),
      messungen: [],
      checkins: [],
      einkauf: { rezepte: {}, abgehakt: {} },
      zuletzt: []
    };
  },

  laden() {
    let gelesen = null;
    try {
      gelesen = JSON.parse(localStorage.getItem(SCHLUESSEL));
    } catch (e) {
      console.warn('Gespeicherte Daten unlesbar, starte neu.', e);
    }
    // Fehlende Felder aus der Vorlage ergänzen — so übersteht ein älterer
    // Datenstand jede spätere Erweiterung ohne eigene Migration.
    this.daten = Object.assign(this.leer(), gelesen || {});
    // Die ID ordnet Fortschrittsdateien beim Coach dem richtigen Klienten zu.
    // Profile von vor ihrer Einführung bekommen sie hier nachträglich.
    if (this.daten.profil && !this.daten.profil.id) {
      this.daten.profil.id = neueId();
      this.sichern();
    }
    return this.daten;
  },

  sichern() {
    try {
      localStorage.setItem(SCHLUESSEL, JSON.stringify(this.daten));
    } catch (e) {
      console.warn('Speichern fehlgeschlagen.', e);
      toast('Speichern fehlgeschlagen — Speicher voll?');
    }
  },

  tag(datum) {
    if (!this.daten.tage[datum]) {
      this.daten.tage[datum] = { essen: [], wasser: 0, schritte: null, schlaf: null,
                                 gewicht: null, gewohnheiten: {}, energie: null };
    }
    return this.daten.tage[datum];
  },

  /** Lesender Zugriff, ohne einen leeren Tag anzulegen. */
  tagLesen(datum) {
    return this.daten.tage[datum] || null;
  },

  zuruecksetzen() {
    try { localStorage.removeItem(SCHLUESSEL); } catch (e) { /* egal */ }
    this.daten = this.leer();
  }
};

/* --- Fotos (IndexedDB) -------------------------------------------------- */

// Fotos sprengen den localStorage (meist 5 MB). IndexedDB fasst ein
// Vielfaches und speichert Blobs direkt.
const Fotos = {
  db: null,

  oeffnen() {
    if (this.db) return Promise.resolve(this.db);
    return new Promise((ok, fehler) => {
      if (!('indexedDB' in window)) return fehler(new Error('Kein IndexedDB'));
      const anfrage = indexedDB.open('coaching-fotos', 1);
      anfrage.onupgradeneeded = () => {
        anfrage.result.createObjectStore('fotos', { keyPath: 'id' });
      };
      anfrage.onsuccess = () => { this.db = anfrage.result; ok(this.db); };
      anfrage.onerror = () => fehler(anfrage.error);
    });
  },

  async _tx(modus, arbeit) {
    const db = await this.oeffnen();
    return new Promise((ok, fehler) => {
      const tx = db.transaction('fotos', modus);
      const ergebnis = arbeit(tx.objectStore('fotos'));
      tx.oncomplete = () => ok(ergebnis && 'result' in ergebnis ? ergebnis.result : undefined);
      tx.onerror = () => fehler(tx.error);
    });
  },

  alle() {
    return this._tx('readonly', (s) => s.getAll())
      .then((liste) => (liste || []).sort((a, b) => a.datum.localeCompare(b.datum)))
      .catch(() => []);
  },
  speichern(eintrag) { return this._tx('readwrite', (s) => s.put(eintrag)); },
  loeschen(id) { return this._tx('readwrite', (s) => s.delete(id)); },
  leeren() { return this._tx('readwrite', (s) => s.clear()).catch(() => {}); }
};

/* --- Farbmodus ---------------------------------------------------------- */

const MODUS_SCHLUESSEL = 'coaching.modus';

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
    if (marke) marke.setAttribute('content', dunkel ? '#17140F' : '#C2410C');
  },
  setzen(wahl) {
    try {
      if (wahl === 'system') localStorage.removeItem(MODUS_SCHLUESSEL);
      else localStorage.setItem(MODUS_SCHLUESSEL, wahl);
    } catch (e) { /* gilt dann nur für diese Sitzung */ }
    this.anwenden();
  },
  beobachten() {
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', () => { if (this.gewaehlt() === 'system') this.anwenden(); });
  }
};

/* --- Zustand ------------------------------------------------------------ */

const App = {
  uebungen: null,     // { gruppen, uebungen }
  lebensmittel: null, // { kategorien, lebensmittel }
  rezepte: null,      // { kategorien, rezepte }
  ansicht: 'heute',
  training: 'plan',
  ernaehrung: 'tagebuch',
  checkin: 'heute',
  essensDatum: null,
  rezeptFilter: 'alle',
  uebungFilter: 'alle',
  uebungSuche: '',
  gewichtZeitraum: 90
};

/* --- Hilfen ------------------------------------------------------------- */

const MAHLZEITEN = [
  { id: 'fruehstueck', name: 'Frühstück' },
  { id: 'mittag', name: 'Mittagessen' },
  { id: 'abend', name: 'Abendessen' },
  { id: 'snack', name: 'Snacks' }
];

const D = () => Speicher.daten;

/** WhatsApp braucht die Nummer international ohne +: aus 0170 … wird 49170 … */
function whatsappNummer(text) {
  let n = String(text || '').replace(/\D/g, '');
  if (n.startsWith('00')) n = n.slice(2); else if (n.startsWith('0')) n = '49' + n.slice(1);
  return n;
}

/* --- Berechnungen: Energiebedarf und Makros ----------------------------- */

const AKTIVITAET = [
  { id: 'sitzend', faktor: 1.3, name: 'Überwiegend sitzend', text: 'Büro, wenig Bewegung im Alltag' },
  { id: 'leicht', faktor: 1.45, name: 'Leicht aktiv', text: 'Etwas zu Fuß, gelegentlich Treppen' },
  { id: 'aktiv', faktor: 1.6, name: 'Aktiv', text: 'Viel auf den Beinen, regelmäßig Sport' },
  { id: 'sehr', faktor: 1.8, name: 'Sehr aktiv', text: 'Körperliche Arbeit oder tägliches Training' }
];

const ZIELE = {
  fett: { name: 'Fett verlieren', text: 'Gewicht reduzieren, Muskeln halten', faktor: 0.8, eiweiss: 2.0 },
  muskel: { name: 'Muskeln aufbauen', text: 'Kraft und Muskelmasse steigern', faktor: 1.1, eiweiss: 1.8 },
  fitness: { name: 'Fitter & gesünder', text: 'Form verbessern, Gewicht halten', faktor: 1.0, eiweiss: 1.6 }
};

/** Grundumsatz nach Mifflin-St Jeor. */
function grundumsatz(p) {
  return 10 * p.gewicht + 6.25 * p.groesse - 5 * p.alter + (p.geschlecht === 'w' ? -161 : 5);
}

function zieleBerechnen(p) {
  const akt = AKTIVITAET.find((a) => a.id === p.aktivitaet) || AKTIVITAET[1];
  const ziel = ZIELE[p.ziel] || ZIELE.fitness;
  const bedarf = grundumsatz(p) * akt.faktor;
  // Nie unter den Grundumsatz gehen — darunter wird es unsinnig hart und
  // kostet Muskulatur.
  const kcal = Math.round(Math.max(bedarf * ziel.faktor, grundumsatz(p)) / 10) * 10;

  // Bei starkem Übergewicht Eiweiß und Fett auf ein Bezugsgewicht (BMI 27)
  // beziehen, sonst werden die Mengen unrealistisch hoch.
  const m = p.groesse / 100;
  const bezug = p.gewicht / (m * m) > 30 ? 27 * m * m : p.gewicht;
  const e = Math.round(bezug * ziel.eiweiss / 5) * 5;
  const f = Math.round(bezug * 0.8 / 5) * 5;
  const kh = Math.max(50, Math.round((kcal - e * 4 - f * 9) / 4 / 5) * 5);
  return { kcal, e, kh, f, bedarf: Math.round(bedarf), manuell: false };
}

/* --- Übungen und Trainingsplan ------------------------------------------ */

function uebung(id) {
  return App.uebungen.uebungen.find((u) => u.id === id) ||
    { id, name: id, gruppe: 'Ganzkörper', orte: ['studio', 'zuhause'], gewicht: true, schritte: [], tipp: '' };
}

// Ersatz, wenn eine Studio-Übung zuhause nicht geht. Zuhause heißt hier:
// Kurzhanteln, eine Bank oder ein stabiler Stuhl und ein Widerstandsband.
const ERSATZ_ZUHAUSE = {
  'bankdruecken': 'kh-bankdruecken', 'kabelzug-flys': 'liegestuetz', 'dips': 'bank-dips',
  'latzug': 'band-rudern', 'rudern-lh': 'kh-rudern', 'kabelrudern': 'band-rudern',
  'kreuzheben': 'rumaenisches-kh', 'kniebeuge': 'goblet-squat', 'beinpresse': 'bulgarian-split',
  'beinstrecker': 'ausfallschritt', 'beinbeuger': 'glute-bridge', 'abduktion': 'glute-bridge',
  'trizeps-kabel': 'ueberkopf-trizeps', 'beinheben': 'dead-bug', 'rudergeraet': 'mountain-climbers'
};

// Vorlagen: [Übung, Sätze, Wiederholungen, Pause in Sekunden]
const T = {
  gkA: ['Ganzkörper A', [['kniebeuge', 3, '6–10', 150], ['bankdruecken', 3, '6–10', 150], ['latzug', 3, '8–12', 120],
        ['rumaenisches-kh', 3, '8–12', 120], ['seitheben', 2, '12–15', 60], ['plank', 3, '30–45', 60]]],
  gkB: ['Ganzkörper B', [['beinpresse', 3, '8–12', 120], ['schraegbank-kh', 3, '8–12', 120], ['kabelrudern', 3, '10–12', 90],
        ['hip-thrust', 3, '8–12', 90], ['face-pulls', 2, '12–15', 60], ['dead-bug', 3, '8–10', 60]]],
  gkC: ['Ganzkörper C', [['kreuzheben', 3, '5–8', 180], ['kh-bankdruecken', 3, '8–12', 120], ['klimmzug', 3, '5–10', 120],
        ['ausfallschritt', 3, '10–12', 90], ['bizeps-curl', 2, '10–12', 60], ['trizeps-kabel', 2, '10–12', 60]]],
  o1: ['Oberkörper 1', [['bankdruecken', 3, '6–10', 150], ['rudern-lh', 3, '6–10', 150], ['schulterdruecken-kh', 3, '8–12', 120],
       ['latzug', 3, '8–12', 90], ['bizeps-curl', 2, '10–12', 60], ['trizeps-kabel', 2, '10–12', 60]]],
  u1: ['Unterkörper 1', [['kniebeuge', 3, '6–10', 180], ['rumaenisches-kh', 3, '8–10', 120], ['beinpresse', 3, '10–12', 120],
       ['beinbeuger', 3, '10–12', 90], ['wadenheben', 3, '12–15', 60], ['plank', 3, '30–45', 60]]],
  o2: ['Oberkörper 2', [['schraegbank-kh', 3, '8–12', 120], ['kh-rudern', 3, '8–12', 90], ['klimmzug', 3, '5–10', 120],
       ['seitheben', 3, '12–15', 60], ['face-pulls', 2, '12–15', 60], ['hammer-curl', 2, '10–12', 60]]],
  u2: ['Unterkörper 2', [['kreuzheben', 3, '5–8', 180], ['bulgarian-split', 3, '8–10', 90], ['hip-thrust', 3, '8–12', 90],
       ['beinstrecker', 3, '12–15', 60], ['wadenheben', 3, '12–15', 60], ['beinheben', 3, '8–12', 60]]],
  push: ['Push', [['bankdruecken', 3, '6–10', 150], ['schulterdruecken-kh', 3, '8–12', 120], ['schraegbank-kh', 3, '8–12', 90],
         ['seitheben', 3, '12–15', 60], ['trizeps-kabel', 3, '10–12', 60]]],
  pull: ['Pull', [['klimmzug', 3, '5–10', 150], ['rudern-lh', 3, '8–10', 120], ['kabelrudern', 3, '10–12', 90],
         ['face-pulls', 3, '12–15', 60], ['bizeps-curl', 3, '10–12', 60]]],
  beine: ['Beine', [['kniebeuge', 3, '6–10', 180], ['rumaenisches-kh', 3, '8–10', 120], ['beinpresse', 3, '10–12', 120],
          ['beinbeuger', 3, '10–12', 90], ['wadenheben', 3, '12–15', 60], ['pallof-press', 3, '10–12', 60]]]
};

const PLAN_VORLAGEN = {
  2: ['gkA', 'gkB'],
  3: ['gkA', 'gkB', 'gkC'],
  4: ['o1', 'u1', 'o2', 'u2'],
  5: ['push', 'pull', 'beine', 'o2', 'u2']
};

function ersatzFinden(id, ort, schonDrin) {
  const u = uebung(id);
  if (u.orte.includes(ort) && !schonDrin.has(id)) return id;
  const vorschlag = ERSATZ_ZUHAUSE[id];
  if (vorschlag && !schonDrin.has(vorschlag) && uebung(vorschlag).orte.includes(ort)) return vorschlag;
  const andere = App.uebungen.uebungen.find((x) =>
    x.gruppe === u.gruppe && x.orte.includes(ort) && !schonDrin.has(x.id));
  return andere ? andere.id : id;
}

function planErstellen(profil) {
  const vorlagen = PLAN_VORLAGEN[profil.tage] || PLAN_VORLAGEN[3];
  const fortgeschritten = profil.erfahrung === 'fortgeschritten';
  return {
    tage: vorlagen.map((schluessel, nr) => {
      const [name, liste] = T[schluessel];
      const schonDrin = new Set();
      const uebungen = liste.map(([id, saetze, wdh, pause], i) => {
        const echt = ersatzFinden(id, profil.ort, schonDrin);
        schonDrin.add(echt);
        // Fortgeschrittene bekommen bei den beiden Hauptübungen einen Satz mehr.
        return { uid: echt, saetze: saetze + (fortgeschritten && i < 2 ? 1 : 0), wdh, pause, notiz: '' };
      });
      return { id: 't' + (nr + 1), name, uebungen };
    })
  };
}

/** Welcher Plantag als Nächstes dran ist: der nach dem zuletzt trainierten. */
function naechsterPlantag() {
  const tage = D().plan.tage;
  if (!tage.length) return null;
  const letztes = [...D().workouts].reverse().find((w) => tage.some((t) => t.id === w.tagId));
  if (!letztes) return tage[0];
  const i = tage.findIndex((t) => t.id === letztes.tagId);
  return tage[(i + 1) % tage.length];
}

function workoutsInWoche(datum = heuteText()) {
  const start = wochenstart(datum);
  const ende = tageVerschieben(start, 6);
  return D().workouts.filter((w) => w.datum >= start && w.datum <= ende);
}

/** Letzte Sätze einer Übung vor einem bestimmten Workout. */
function letzteSaetze(uid, ausserId) {
  for (let i = D().workouts.length - 1; i >= 0; i--) {
    const w = D().workouts[i];
    if (w.id === ausserId) continue;
    const u = w.uebungen.find((x) => x.uid === uid);
    if (u && u.saetze.some((s) => s.fertig)) return u.saetze.filter((s) => s.fertig);
  }
  return null;
}

function bestwert(uid, ausserId) {
  let best = 0;
  D().workouts.forEach((w) => {
    if (w.id === ausserId) return;
    w.uebungen.forEach((u) => {
      if (u.uid !== uid) return;
      u.saetze.forEach((s) => { if (s.fertig) best = Math.max(best, e1rm(s.kg, s.wdh)); });
    });
  });
  return best;
}

/* --- Ernährung ---------------------------------------------------------- */

function tagesSumme(datum) {
  const t = Speicher.tagLesen(datum);
  const s = { kcal: 0, e: 0, kh: 0, f: 0 };
  if (!t) return s;
  t.essen.forEach((x) => { s.kcal += x.kcal; s.e += x.e; s.kh += x.kh; s.f += x.f; });
  return s;
}

function naehrwerteFuer(lm, gramm) {
  const f = gramm / 100;
  return {
    kcal: Math.round(lm.kcal * f),
    e: Math.round(lm.e * f * 10) / 10,
    kh: Math.round(lm.kh * f * 10) / 10,
    f: Math.round(lm.f * f * 10) / 10
  };
}

/* --- Schlaf, Schritte, Gewicht ------------------------------------------ */

function gewichtsreihe() {
  return Object.keys(D().tage).sort()
    .filter((d) => D().tage[d].gewicht != null)
    .map((d) => ({ datum: d, wert: D().tage[d].gewicht }));
}

/** Mittelwert der Messungen in den 7 Tagen bis einschließlich datum. */
function gewichtMittel(datum, reihe = gewichtsreihe()) {
  const von = tageVerschieben(datum, -6);
  const fenster = reihe.filter((r) => r.datum >= von && r.datum <= datum);
  if (!fenster.length) return null;
  return fenster.reduce((a, r) => a + r.wert, 0) / fenster.length;
}

function aktuellesGewicht() {
  const reihe = gewichtsreihe();
  if (reihe.length) return reihe[reihe.length - 1].wert;
  return D().profil ? D().profil.gewicht : null;
}

/* --- Gewohnheiten ------------------------------------------------------- */

function gewohnheitErledigt(id, datum) {
  const t = Speicher.tagLesen(datum);
  return !!(t && t.gewohnheiten && t.gewohnheiten[id]);
}

/** Serie in Tagen. Ist heute noch offen, zählt die Serie bis gestern. */
function serie(id) {
  let datum = heuteText();
  if (!gewohnheitErledigt(id, datum)) datum = tageVerschieben(datum, -1);
  let n = 0;
  while (gewohnheitErledigt(id, datum) && n < 3650) { n++; datum = tageVerschieben(datum, -1); }
  return n;
}

/* --- Check-in ----------------------------------------------------------- */

function letzterCheckin() {
  const c = D().checkins;
  return c.length ? c[c.length - 1] : null;
}

/** Fällig am festgelegten Wochentag — oder wenn der letzte älter als 7 Tage ist. */
function checkinFaellig() {
  if (!D().profil) return false;
  const heute = heuteText();
  const letzter = letzterCheckin();
  if (letzter && letzter.datum === heute) return false;
  if (new Date().getDay() === Number(D().coach.checkinTag)) return true;
  const seit = letzter ? letzter.datum : D().profil.start;
  return tageZwischen(seit, heute) >= 7;
}

const TIPPS = [
  'Eiweiß zuerst: Fang jede Mahlzeit mit der Eiweißquelle an — das sättigt am längsten.',
  'Progressive Überlastung: Versuche jede Woche eine Wiederholung oder 1–2 kg mehr als beim letzten Mal.',
  'Wiege dich morgens nach dem Toilettengang. Entscheidend ist der Wochenschnitt, nicht der einzelne Tag.',
  'Schlaf ist dein stärkstes legales Leistungsmittel. 7–9 Stunden machen Training und Diät leichter.',
  'Meal Prep am Sonntag spart dir unter der Woche jede Menge Entscheidungen — und Ausrutscher.',
  'Schritte sind der unterschätzteste Fettverbrenner. 8.000–10.000 am Tag machen einen echten Unterschied.',
  'Trink ein großes Glas Wasser direkt nach dem Aufstehen.',
  'Perfektion ist nicht nötig. 80 % Konsequenz über Monate schlagen 100 % für zwei Wochen.',
  'Technik vor Gewicht. Saubere Wiederholungen bauen Muskeln — unsaubere bauen Verletzungen.',
  'Eine schlechte Mahlzeit ruiniert keinen Plan. Einfach mit der nächsten wieder einsteigen.',
  'Gemüse bringt Volumen auf den Teller, aber kaum Kalorien. Mach die Hälfte deines Tellers grün.',
  'Plane Ruhetage bewusst ein. Muskeln wachsen in der Erholung, nicht im Training.',
  'Fotos und Umfänge zeigen oft Fortschritt, wenn die Waage stehen bleibt.',
  'Bereite für Heißhunger-Momente einen eiweißreichen Snack vor: Skyr, Quark oder Eier.',
  'Schreib deinem Coach Fragen sofort auf — im Check-in gehen sie sonst verloren.',
  'Alkohol bremst Regeneration und Fettabbau. Wenn, dann bewusst und selten.',
  'Ein kurzer Spaziergang nach dem Essen stabilisiert den Blutzucker.',
  'Halte die letzten 1–2 Wiederholungen eines Satzes schwer — sonst fehlt der Wachstumsreiz.',
  'Stress erhöht den Hunger. Atemübungen oder ein Spaziergang helfen mehr als Willenskraft.',
  'Feiere kleine Siege: jede erledigte Einheit, jeder erfasste Tag zählt.'
];

function tippDesTages() {
  const d = new Date();
  const tagImJahr = Math.floor((d - new Date(d.getFullYear(), 0, 0)) / 86400000);
  return TIPPS[tagImJahr % TIPPS.length];
}

/* --- Einrichtung -------------------------------------------------------- */

function einrichtung(ziel) {
  document.querySelector('.tabs').classList.add('versteckt');
  document.getElementById('einstellungen-auf').classList.add('versteckt');
  document.getElementById('titel').textContent = 'Willkommen';
  document.getElementById('untertitel').textContent = 'Dein Coaching';

  const p = einrichtung.entwurf || (einrichtung.entwurf = {
    name: '', ziel: null, geschlecht: null, alter: null, groesse: null, gewicht: null,
    aktivitaet: null, tage: 3, ort: 'studio', erfahrung: 'einsteiger', schrittziel: 8000, schlafziel: 7.5,
    coachWhatsapp: '', coachEmail: ''
  });
  const schritte = 6;
  const nr = einrichtung.schritt || 1;

  const box = el('div', 'einrichtung');
  const balken = el('div', 'einrichtung__fortschritt');
  const fuell = el('i'); fuell.style.width = `${(nr / schritte) * 100}%`;
  balken.append(fuell);
  box.append(balken, el('div', 'einrichtung__schritt', `Schritt ${nr} von ${schritte}`));

  const weiter = knopf(nr === schritte ? 'Los geht’s' : 'Weiter', null, null);
  const fehler = el('p', 'leise');
  fehler.style.color = 'var(--accent-ink)';
  const gehe = (n) => { einrichtung.schritt = n; neuZeichnen(); window.scrollTo({ top: 0 }); };

  if (nr === 1) {
    box.append(el('h2', null, 'Schön, dass du da bist!'));
    box.append(el('p', 'leise', 'Diese App begleitet dich durch dein Coaching: Training, Ernährung, Meal Prep, Schritte, Schlaf und dein wöchentlicher Check-in — alles an einem Ort.'));
    const name = eingabe('text', p.name, { platzhalter: 'Dein Vorname' });
    name.autocomplete = 'given-name';
    name.oninput = () => { p.name = name.value.trim(); };
    box.append(feld('Wie heißt du?', name));
    const h = el('div', 'hinweis');
    h.append(el('div', 'hinweis__titel', 'Bevor es losgeht'));
    h.append(el('p', null, 'Die App ersetzt keine ärztliche Beratung. Bei Vorerkrankungen, Schmerzen, in der Schwangerschaft oder bei Medikamenteneinnahme sprich bitte vor Trainings- oder Ernährungsumstellungen mit deiner Ärztin oder deinem Arzt.'));
    h.append(el('p', null, 'Deine Daten bleiben auf diesem Gerät. Nur was du im Check-in selbst abschickst, erreicht deinen Coach.'));
    box.append(h);
    weiter.onclick = () => { if (!p.name) { fehler.textContent = 'Bitte gib deinen Vornamen ein.'; return; } gehe(2); };
  }

  if (nr === 2) {
    box.append(el('h2', null, `Was ist dein Ziel, ${p.name}?`));
    box.append(el('p', 'leise', 'Danach richten sich Kalorienziel und Eiweißmenge. Du kannst es jederzeit ändern.'));
    box.append(wahl(Object.entries(ZIELE).map(([id, z]) => ({ id, name: z.name, text: z.text })), p.ziel,
      (id) => { p.ziel = id; }));
    box.lastChild.style.gridTemplateColumns = '1fr';
    weiter.onclick = () => { if (!p.ziel) { fehler.textContent = 'Bitte wähle ein Ziel.'; return; } gehe(3); };
  }

  if (nr === 3) {
    box.append(el('h2', null, 'Ein paar Körperdaten'));
    box.append(el('p', 'leise', 'Daraus berechnet die App deinen Energiebedarf.'));
    const g = el('div', 'feld');
    g.append(el('div', 'feld__label', 'Geschlecht'));
    g.append(wahl([{ id: 'w', name: 'Weiblich' }, { id: 'm', name: 'Männlich' }], p.geschlecht, (id) => { p.geschlecht = id; }));
    box.append(g);
    const reihe = el('div', 'reihe');
    const alter = eingabe('number', p.alter, { platzhalter: '35', modus: 'numeric' });
    alter.oninput = () => { p.alter = leseZahl(alter.value); };
    const groesse = eingabe('number', p.groesse, { platzhalter: '175', modus: 'numeric' });
    groesse.oninput = () => { p.groesse = leseZahl(groesse.value); };
    reihe.append(feld('Alter', alter), feld('Größe (cm)', groesse));
    box.append(reihe);
    const gewicht = eingabe('text', p.gewicht != null ? String(p.gewicht).replace('.', ',') : '', { platzhalter: '80,0', modus: 'decimal' });
    gewicht.oninput = () => { p.gewicht = leseZahl(gewicht.value); };
    box.append(feld('Aktuelles Gewicht (kg)', gewicht));
    weiter.onclick = () => {
      if (!p.geschlecht || !(p.alter >= 14 && p.alter <= 100) || !(p.groesse >= 120 && p.groesse <= 230) ||
          !(p.gewicht >= 35 && p.gewicht <= 300)) {
        fehler.textContent = 'Bitte alle Felder ausfüllen (Alter 14–100, Größe 120–230 cm, Gewicht 35–300 kg).';
        return;
      }
      gehe(4);
    };
  }

  if (nr === 4) {
    box.append(el('h2', null, 'Wie aktiv ist dein Alltag?'));
    box.append(el('p', 'leise', 'Gemeint ist der Alltag inklusive Training. Im Zweifel die niedrigere Stufe wählen.'));
    const w = wahl(AKTIVITAET.map((a) => ({ id: a.id, name: a.name, text: a.text })), p.aktivitaet, (id) => { p.aktivitaet = id; });
    w.style.gridTemplateColumns = '1fr';
    box.append(w);
    const reihe = el('div', 'reihe');
    reihe.style.marginTop = '14px';
    const sz = eingabe('number', p.schrittziel, { modus: 'numeric' });
    sz.oninput = () => { p.schrittziel = leseZahl(sz.value) || 8000; };
    const sl = eingabe('text', String(p.schlafziel).replace('.', ','), { modus: 'decimal' });
    sl.oninput = () => { p.schlafziel = leseZahl(sl.value) || 7.5; };
    reihe.append(feld('Schrittziel pro Tag', sz), feld('Schlafziel (Std.)', sl));
    box.append(reihe);
    weiter.onclick = () => { if (!p.aktivitaet) { fehler.textContent = 'Bitte wähle eine Stufe.'; return; } gehe(5); };
  }

  if (nr === 5) {
    box.append(el('h2', null, 'Dein Training'));
    const f1 = el('div', 'feld');
    f1.append(el('div', 'feld__label', 'Wie oft pro Woche kannst du trainieren?'));
    f1.append(wahl([2, 3, 4, 5].map((n) => ({ id: n, name: `${n}×` })), p.tage, (id) => { p.tage = id; }, 4));
    const f2 = el('div', 'feld');
    f2.append(el('div', 'feld__label', 'Wo trainierst du?'));
    f2.append(wahl([{ id: 'studio', name: 'Fitnessstudio', text: 'Geräte, Lang- und Kurzhanteln' },
                    { id: 'zuhause', name: 'Zuhause', text: 'Kurzhanteln, Bank/Stuhl, Band' }], p.ort, (id) => { p.ort = id; }));
    const f3 = el('div', 'feld');
    f3.append(el('div', 'feld__label', 'Erfahrung mit Krafttraining'));
    f3.append(wahl([{ id: 'einsteiger', name: 'Einsteiger', text: 'Weniger als 1 Jahr' },
                    { id: 'fortgeschritten', name: 'Fortgeschritten', text: 'Regelmäßig seit über 1 Jahr' }], p.erfahrung, (id) => { p.erfahrung = id; }));
    box.append(f1, f2, f3);
    weiter.onclick = () => gehe(6);
  }

  if (nr === 6) {
    const z = zieleBerechnen(p);
    const plan = planErstellen(p);
    box.append(el('h2', null, 'Dein Startpaket'));
    box.append(el('p', 'leise', 'Berechnet aus deinen Angaben. Dein Coach kann die Werte später anpassen — unter Einstellungen.'));
    const k1 = karte('Ernährung pro Tag', 'ernaehrung');
    const werte = el('div', 'werte');
    werte.append(wertKachel('Kalorien', zahl(z.kcal), 'kcal', `Bedarf ca. ${zahl(z.bedarf)} kcal`),
                 wertKachel('Eiweiß', zahl(z.e), 'g'), wertKachel('Kohlenhydrate', zahl(z.kh), 'g'), wertKachel('Fett', zahl(z.f), 'g'));
    k1.append(werte);
    const k2 = karte(`Trainingsplan · ${p.tage}× pro Woche`, 'training');
    plan.tage.forEach((t) => {
      const z2 = el('div', 'zeile');
      z2.style.cursor = 'default';
      const text = el('div', 'zeile__text');
      text.append(el('div', 'zeile__titel', t.name),
                  el('div', 'zeile__meta', t.uebungen.map((u) => uebung(u.uid).name).join(' · ')));
      z2.append(text);
      k2.append(z2);
    });
    const k3 = karte('Tägliche Ziele', 'checkin');
    k3.append(el('p', 'leise', `${zahl(p.schrittziel)} Schritte · ${zahl(p.schlafziel, 1)} Std. Schlaf · 8 Gläser Wasser`));
    const k4 = karte('Dein Coach (optional)', 'senden');
    k4.append(el('p', 'leise', 'Dorthin schickst du deinen wöchentlichen Check-in. Kannst du auch später unter Einstellungen eintragen.'));
    const wa = eingabe('tel', p.coachWhatsapp, { platzhalter: 'z. B. 0170 1234567' });
    wa.oninput = () => { p.coachWhatsapp = wa.value; };
    const em = eingabe('email', p.coachEmail, { platzhalter: 'coach@beispiel.de' });
    em.oninput = () => { p.coachEmail = em.value.trim(); };
    k4.append(feld('WhatsApp-Nummer', wa), feld('E-Mail', em));
    box.append(k1, k2, k3, k4);
    weiter.onclick = () => {
      const d = D();
      const { coachWhatsapp, coachEmail, ...profil } = p;
      d.profil = { ...profil, id: neueId(), start: heuteText(), wasserziel: 8 };
      d.coach.whatsapp = whatsappNummer(coachWhatsapp);
      d.coach.email = coachEmail.includes('@') ? coachEmail : '';
      d.ziele = z;
      d.plan = plan;
      Speicher.tag(heuteText()).gewicht = p.gewicht;
      Speicher.sichern();
      einrichtung.entwurf = null;
      einrichtung.schritt = 1;
      document.querySelector('.tabs').classList.remove('versteckt');
      document.getElementById('einstellungen-auf').classList.remove('versteckt');
      wechseln('heute');
      toast(`Willkommen an Bord, ${p.name}!`);
    };
  }

  box.append(fehler);
  const fuss = el('div');
  fuss.style.marginTop = '18px';
  fuss.append(weiter);
  if (nr > 1) {
    const zurueck = knopf('Zurück', 'knopf--zweit', () => gehe(nr - 1));
    fuss.append(zurueck);
  }
  box.append(fuss);
  ziel.append(box);
}

/* --- Ansicht: Heute ----------------------------------------------------- */

function begruessung() {
  const h = new Date().getHours();
  if (h < 5) return 'Gute Nacht';
  if (h < 11) return 'Guten Morgen';
  if (h < 17) return 'Hallo';
  return 'Guten Abend';
}

function ansichtHeute(ziel) {
  const d = D();
  const heute = heuteText();
  const tag = Speicher.tagLesen(heute) || {};
  const p = d.profil;

  // Held: das Training des Tages
  const held = el('div', 'held');
  const oben = el('div', 'held__oben');
  oben.append(el('span', 'held__label', `${begruessung()}, ${p.name}`));
  const woche = workoutsInWoche();
  const plak = el('span', 'held__plakette');
  plak.innerHTML = ikon('training');
  plak.append(document.createTextNode(`${woche.length}/${p.tage} diese Woche`));
  oben.append(plak);
  held.append(oben);

  const heuteTrainiert = d.workouts.filter((w) => w.datum === heute);
  if (d.aktiv) {
    held.append(el('div', 'held__titel', d.aktiv.name));
    held.append(el('div', 'held__text', `Training läuft seit ${dauerText(Date.now() - d.aktiv.start)}.`));
    held.append(knopf('Training fortsetzen', null, () => workoutOeffnen(), 'training'));
  } else if (heuteTrainiert.length) {
    const w = heuteTrainiert[heuteTrainiert.length - 1];
    held.append(el('div', 'held__titel', 'Training erledigt 💪'));
    held.append(el('div', 'held__text', `${w.name} · ${dauerText(w.ende - w.start)} · ${zahl(volumen(w))} kg bewegt`));
    held.append(knopf('Details ansehen', null, () => workoutDetail(w)));
  } else {
    const naechster = naechsterPlantag();
    const genug = woche.length >= p.tage;
    held.append(el('div', 'held__titel', genug ? 'Wochenziel erreicht' : (naechster ? naechster.name : 'Freies Training')));
    held.append(el('div', 'held__text', genug
      ? 'Heute ist Erholung angesagt — ein Spaziergang zählt trotzdem für deine Schritte.'
      : naechster ? `${naechster.uebungen.length} Übungen · ca. ${Math.round(naechster.uebungen.reduce((a, u) => a + u.saetze * (u.pause + 45), 0) / 60)} Min.` : ''));
    if (naechster) held.append(knopf(genug ? 'Trotzdem trainieren' : 'Training starten', null, () => workoutStarten(naechster), 'training'));
  }
  ziel.append(held);

  // Check-in fällig?
  if (checkinFaellig()) {
    const k = el('button', 'karte karte--klick');
    k.type = 'button';
    k.style.cssText += ';width:100%;text-align:left;display:flex;gap:12px;align-items:center;border-color:var(--accent)';
    const i = el('div', 'zeile__ikon'); i.innerHTML = ikon('checkin');
    const t = el('div', 'zeile__text');
    t.append(el('div', 'zeile__titel', 'Dein Wochen-Check-in ist fällig'),
             el('div', 'zeile__meta', 'Dauert 3 Minuten — dein Coach wartet auf dein Update.'));
    const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
    k.append(i, t, pf);
    k.onclick = () => { App.checkin = 'woche'; wechseln('checkin'); };
    ziel.append(k);
  }

  // Ringe
  const summe = tagesSumme(heute);
  const schlafH = schlafDauer(tag.schlaf);
  const ringe = el('div', 'ringe');
  ringe.append(
    ring(summe.kcal, d.ziele.kcal, 'var(--accent)', zahl(summe.kcal), `von ${zahl(d.ziele.kcal)}`, 'kcal',
         () => { App.essensDatum = heute; App.ernaehrung = 'tagebuch'; wechseln('ernaehrung'); }),
    ring(summe.e, d.ziele.e, 'var(--c-eiweiss)', `${zahl(summe.e)} g`, `von ${zahl(d.ziele.e)} g`, 'Eiweiß',
         () => { App.essensDatum = heute; App.ernaehrung = 'tagebuch'; wechseln('ernaehrung'); }),
    ring(tag.schritte || 0, p.schrittziel, 'var(--c-schritte)',
         tag.schritte ? (tag.schritte >= 10000 ? zahl(tag.schritte / 1000, 1) + 'k' : zahl(tag.schritte)) : '0',
         `von ${zahl(p.schrittziel)}`, 'Schritte', () => { App.checkin = 'heute'; wechseln('checkin'); }),
    ring(schlafH || 0, p.schlafziel, 'var(--c-schlaf)', schlafH ? `${zahl(schlafH, 1)} h` : '–',
         `von ${zahl(p.schlafziel, 1)} h`, 'Schlaf', () => { App.checkin = 'heute'; wechseln('checkin'); })
  );
  const kr = karte('Dein Tag', 'feuer');
  kr.append(ringe);
  ziel.append(kr);

  // Wasser
  const kw = karte('Wasser', 'wasser', `${tag.wasser || 0} von ${p.wasserziel || 8} Gläsern`);
  kw.append(wasserPerlen(heute, () => { kw.querySelector('.zaehler').textContent = `${Speicher.tagLesen(heute).wasser} von ${p.wasserziel || 8} Gläsern`; }));
  ziel.append(kw);

  // Gewohnheiten
  const kg = karte('Gewohnheiten', 'haken');
  const erledigt = d.gewohnheiten.filter((g) => gewohnheitErledigt(g.id, heute)).length;
  kg.querySelector('.karte__titel').append(el('span', 'zaehler', `${erledigt}/${d.gewohnheiten.length}`));
  gewohnheitsListe(kg, heute);
  ziel.append(kg);

  // Schnellzugriff
  const schnell = el('div', 'reihe');
  schnell.style.marginBottom = '14px';
  schnell.append(
    knopf('Gewicht', 'knopf--zweit knopf--klein', () => gewichtBlatt(heute), 'plus'),
    knopf('Mahlzeit', 'knopf--zweit knopf--klein', () => essenHinzufuegen(heute, mahlzeitJetzt()), 'plus'),
    knopf('Schritte', 'knopf--zweit knopf--klein', () => { App.checkin = 'heute'; wechseln('checkin'); }, 'plus')
  );
  ziel.append(schnell);

  // Tipp
  const tipp = el('div', 'hinweis');
  tipp.append(el('div', 'hinweis__titel', 'Tipp des Tages'), el('p', null, tippDesTages()));
  ziel.append(tipp);
}

function mahlzeitJetzt() {
  const h = new Date().getHours();
  if (h < 11) return 'fruehstueck';
  if (h < 15) return 'mittag';
  if (h < 17) return 'snack';
  return 'abend';
}

function wasserPerlen(datum, nachher) {
  const ziel = D().profil.wasserziel || 8;
  const box = el('div', 'perlen');
  const zeichnen = () => {
    box.replaceChildren();
    const stand = (Speicher.tagLesen(datum) || {}).wasser || 0;
    // Ein Glas über dem Ziel anbieten erst, wenn das Ziel erreicht ist.
    for (let i = 1; i <= Math.max(ziel, stand >= ziel ? stand + 1 : 0); i++) {
      const k = el('button', 'perle');
      k.type = 'button';
      k.innerHTML = ikon('wasser');
      k.setAttribute('aria-pressed', String(i <= stand));
      k.setAttribute('aria-label', `${i} Glas Wasser`);
      k.onclick = () => {
        const t = Speicher.tag(datum);
        t.wasser = t.wasser === i ? i - 1 : i;
        Speicher.sichern();
        zeichnen();
        if (nachher) nachher();
      };
      box.append(k);
    }
  };
  zeichnen();
  return box;
}

function gewohnheitsListe(ziel, datum) {
  if (!D().gewohnheiten.length) {
    ziel.append(el('p', 'leise', 'Keine Gewohnheiten angelegt. Unter Check-in → Gewohnheiten kannst du welche hinzufügen.'));
    return;
  }
  D().gewohnheiten.forEach((g) => {
    const s = serie(g.id);
    const extra = el('span', 'haken-reihe__serie');
    const serieZeichnen = (n) => {
      extra.innerHTML = n >= 2 ? ikon('feuer') : '';
      extra.append(document.createTextNode(n >= 2 ? `${n}` : ''));
      extra.title = n >= 2 ? `${n} Tage in Folge` : '';
    };
    serieZeichnen(s);
    ziel.append(hakenReihe(g.name, null, gewohnheitErledigt(g.id, datum), (an) => {
      const t = Speicher.tag(datum);
      if (an) t.gewohnheiten[g.id] = true; else delete t.gewohnheiten[g.id];
      Speicher.sichern();
      serieZeichnen(serie(g.id));
      if (an && D().gewohnheiten.every((x) => gewohnheitErledigt(x.id, datum))) toast('Alle Gewohnheiten erledigt — stark!');
    }, extra));
  });
}

/* --- Ansicht: Training -------------------------------------------------- */

function ansichtTraining(ziel) {
  ziel.append(segment([['plan', 'Plan'], ['verlauf', 'Verlauf'], ['uebungen', 'Übungen']], App.training,
    (id) => { App.training = id; neuZeichnen(); }));
  if (App.training === 'plan') trainingPlan(ziel);
  if (App.training === 'verlauf') trainingVerlauf(ziel);
  if (App.training === 'uebungen') uebungsBibliothek(ziel, (u) => uebungBlatt(u.id));
}

function trainingPlan(ziel) {
  const d = D();
  const heute = heuteText();
  const start = wochenstart(heute);

  const kw = karte('Diese Woche', 'training', `${workoutsInWoche().length} von ${d.profil.tage} Einheiten`);
  const punkte = el('div', 'woche-punkte');
  for (let i = 0; i < 7; i++) {
    const datum = tageVerschieben(start, i);
    const zelle = el('div');
    zelle.append(el('div', 'woche-punkte__tag', WT_KURZ[(i + 1) % 7]));
    const voll = d.workouts.some((w) => w.datum === datum);
    const p = el('div', 'woche-punkte__punkt' + (voll ? ' woche-punkte__punkt--voll' : '') +
                 (datum === heute ? ' woche-punkte__punkt--heute' : ''));
    if (voll) p.innerHTML = ikon('haken');
    zelle.append(p);
    punkte.append(zelle);
  }
  kw.append(punkte);
  ziel.append(kw);

  if (d.aktiv) {
    ziel.append(knopf(`${d.aktiv.name} fortsetzen`, null, () => workoutOeffnen(), 'training'));
    ziel.lastChild.style.marginBottom = '14px';
  }

  ziel.append(abschnitt('Dein Plan', linkKnopf('Neu erstellen', () => planNeuBlatt())));
  const naechster = naechsterPlantag();
  d.plan.tage.forEach((t, i) => {
    const k = el('button', 'plan-tag' + (naechster && t.id === naechster.id ? ' plan-tag--naechster' : ''));
    k.type = 'button';
    k.append(el('div', 'plan-tag__nr', String(i + 1)));
    const text = el('div', 'plan-tag__text');
    const name = el('div', 'plan-tag__name', t.name);
    if (naechster && t.id === naechster.id) { name.append(' '); name.append(el('span', 'marke marke--akzent', 'Als Nächstes')); }
    text.append(name, el('div', 'plan-tag__meta', t.uebungen.map((u) => uebung(u.uid).name).join(' · ')));
    const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
    k.append(text, pf);
    k.onclick = () => plantagBlatt(t);
    ziel.append(k);
  });

  const reihe = el('div', 'reihe');
  reihe.style.marginTop = '6px';
  reihe.append(
    knopf('Freies Training', 'knopf--zweit knopf--klein', () => workoutStarten(null), 'plus'),
    knopf('Tag hinzufügen', 'knopf--zweit knopf--klein', () => {
      const t = { id: 't' + neueId(), name: `Tag ${d.plan.tage.length + 1}`, uebungen: [] };
      d.plan.tage.push(t); Speicher.sichern(); neuZeichnen(); planTagBearbeiten(t);
    }, 'plus'));
  ziel.append(reihe);

  const h = el('p', 'fusstext', 'Die Trainingstage sind an keinen Wochentag gebunden: Trainiere, wann es passt — die App merkt sich, welcher Tag als Nächstes dran ist. Zwischen zwei Einheiten für dieselben Muskeln mindestens einen Tag Pause.');
  ziel.append(h);
}

function plantagBlatt(t) {
  blattOeffnen(t.name, (inhalt, schliessen, blatt) => {
    const k = karte(null);
    t.uebungen.forEach((pu, i) => {
      const u = uebung(pu.uid);
      const z = el('button', 'zeile');
      z.type = 'button';
      z.append(el('div', 'zeile__ikon', String(i + 1)));
      const text = el('div', 'zeile__text');
      text.append(el('div', 'zeile__titel', u.name),
                  el('div', 'zeile__meta', `${pu.saetze} Sätze × ${pu.wdh} ${u.zeit ? 'Sek.' : 'Wdh.'} · ${pu.pause} s Pause`));
      const best = bestwert(pu.uid);
      if (best && u.gewicht) text.append(el('div', 'zeile__meta', `Bestwert (1RM geschätzt): ${zahl(best, 1)} kg`));
      z.append(text);
      z.onclick = () => uebungBlatt(pu.uid);
      k.append(z);
    });
    if (!t.uebungen.length) k.append(el('p', 'leise', 'Noch keine Übungen. Tippe auf „Bearbeiten".'));
    inhalt.append(k);
    blattFuss(blatt,
      knopf('Bearbeiten', 'knopf--zweit', () => { schliessen(); planTagBearbeiten(t); }),
      knopf('Starten', null, () => { schliessen(); workoutStarten(t); }, 'training'));
  });
}

function planTagBearbeiten(t) {
  blattOeffnen('Plantag bearbeiten', (inhalt, schliessen, blatt) => {
    const zeichnen = () => {
      inhalt.replaceChildren();
      const name = eingabe('text', t.name, { beiAenderung: (v) => { t.name = v.trim() || t.name; Speicher.sichern(); } });
      inhalt.append(feld('Name', name));
      t.uebungen.forEach((pu, i) => {
        const u = uebung(pu.uid);
        const k = el('div', 'karte uebung-karte');
        const kopf = el('div', 'uebung-karte__kopf');
        kopf.append(el('div', 'uebung-karte__name', u.name));
        const hoch = el('button', 'ikon-knopf ikon-knopf--plain'); hoch.innerHTML = ikon('zurueck');
        hoch.style.transform = 'rotate(90deg)'; hoch.setAttribute('aria-label', 'Nach oben');
        hoch.disabled = i === 0;
        hoch.onclick = () => { t.uebungen.splice(i - 1, 0, t.uebungen.splice(i, 1)[0]); Speicher.sichern(); zeichnen(); };
        const weg = el('button', 'ikon-knopf ikon-knopf--plain'); weg.innerHTML = ikon('muell');
        weg.setAttribute('aria-label', 'Entfernen');
        weg.onclick = () => { t.uebungen.splice(i, 1); Speicher.sichern(); zeichnen(); };
        kopf.append(hoch, weg);
        k.append(kopf);
        const reihe = el('div', 'reihe');
        const s = eingabe('number', pu.saetze, { modus: 'numeric', beiAenderung: (v) => { pu.saetze = Math.max(1, Math.min(10, leseZahl(v) || 3)); Speicher.sichern(); } });
        const w = eingabe('text', pu.wdh, { beiAenderung: (v) => { pu.wdh = v.trim() || pu.wdh; Speicher.sichern(); } });
        const p = eingabe('number', pu.pause, { modus: 'numeric', beiAenderung: (v) => { pu.pause = Math.max(0, leseZahl(v) || 90); Speicher.sichern(); } });
        reihe.append(feld('Sätze', s), feld(u.zeit ? 'Sekunden' : 'Wdh.', w), feld('Pause (s)', p));
        k.append(reihe);
        const n = eingabe('text', pu.notiz, { platzhalter: 'Notiz vom Coach, z. B. „Tempo 3-1-1"', beiAenderung: (v) => { pu.notiz = v; Speicher.sichern(); } });
        n.setAttribute('aria-label', 'Notiz');
        k.append(n);
        inhalt.append(k);
      });
      inhalt.append(knopf('Übung hinzufügen', 'knopf--zweit', () => uebungWaehlen(null, (u) => {
        t.uebungen.push({ uid: u.id, saetze: 3, wdh: u.zeit ? '30–45' : '8–12', pause: 90, notiz: '' });
        Speicher.sichern(); zeichnen();
      }), 'plus'));
      const loeschen = knopf('Plantag löschen', 'knopf--gefahr', () => {
        if (!confirm(`„${t.name}" wirklich löschen?`)) return;
        D().plan.tage = D().plan.tage.filter((x) => x !== t);
        Speicher.sichern(); schliessen();
      });
      loeschen.style.marginTop = '20px';
      inhalt.append(loeschen);
    };
    zeichnen();
  }, { beimSchliessen: neuZeichnen });
}

function planNeuBlatt() {
  blattOeffnen('Plan neu erstellen', (inhalt, schliessen, blatt) => {
    const p = { ...D().profil };
    inhalt.append(el('p', 'leise', 'Erstellt einen neuen Plan aus den Vorlagen. Dein bisheriger Plan wird ersetzt, der Trainingsverlauf bleibt erhalten.'));
    const f1 = el('div', 'feld'); f1.append(el('div', 'feld__label', 'Einheiten pro Woche'));
    f1.append(wahl([2, 3, 4, 5].map((n) => ({ id: n, name: `${n}×` })), p.tage, (id) => { p.tage = id; }, 4));
    const f2 = el('div', 'feld'); f2.append(el('div', 'feld__label', 'Ort'));
    f2.append(wahl([{ id: 'studio', name: 'Fitnessstudio' }, { id: 'zuhause', name: 'Zuhause' }], p.ort, (id) => { p.ort = id; }));
    const f3 = el('div', 'feld'); f3.append(el('div', 'feld__label', 'Erfahrung'));
    f3.append(wahl([{ id: 'einsteiger', name: 'Einsteiger' }, { id: 'fortgeschritten', name: 'Fortgeschritten' }], p.erfahrung, (id) => { p.erfahrung = id; }));
    inhalt.append(f1, f2, f3);
    blattFuss(blatt, knopf('Plan erstellen', null, () => {
      Object.assign(D().profil, { tage: p.tage, ort: p.ort, erfahrung: p.erfahrung });
      D().plan = planErstellen(D().profil);
      Speicher.sichern(); schliessen(); neuZeichnen(); toast('Neuer Plan erstellt');
    }));
  });
}

function trainingVerlauf(ziel) {
  const liste = [...D().workouts].reverse();
  if (!liste.length) {
    ziel.append(leerzustand('Noch kein Training', 'Sobald du dein erstes Workout abschließt, erscheint es hier — mit Dauer, Volumen und Rekorden.'));
    return;
  }
  const gesamt = el('div', 'werte werte--3');
  gesamt.style.marginBottom = '14px';
  const minuten = liste.reduce((a, w) => a + (w.ende - w.start), 0);
  gesamt.append(wertKachel('Einheiten', zahl(liste.length)),
                wertKachel('Trainingszeit', zahl(minuten / 3600000, 1), 'h'),
                wertKachel('Volumen', zahl(liste.reduce((a, w) => a + volumen(w), 0) / 1000, 1), 't'));
  ziel.append(gesamt);
  const k = karte(null);
  liste.forEach((w) => {
    const z = el('button', 'zeile');
    z.type = 'button';
    const i = el('div', 'zeile__ikon'); i.innerHTML = ikon('training');
    const text = el('div', 'zeile__text');
    text.append(el('div', 'zeile__titel', w.name),
                el('div', 'zeile__meta', `${datumMittel(w.datum)} · ${dauerText(w.ende - w.start)} · ${zahl(volumen(w))} kg`));
    const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
    z.append(i, text);
    if (w.rekorde && w.rekorde.length) { const r = el('span', 'marke marke--akzent', `${w.rekorde.length} PR`); z.append(r); }
    z.append(pf);
    z.onclick = () => workoutDetail(w);
    k.append(z);
  });
  ziel.append(k);
}

function workoutDetail(w) {
  blattOeffnen(w.name, (inhalt, schliessen) => {
    const werte = el('div', 'werte werte--3');
    werte.style.marginBottom = '14px';
    const saetze = w.uebungen.reduce((a, u) => a + u.saetze.filter((s) => s.fertig).length, 0);
    werte.append(wertKachel('Dauer', dauerText(w.ende - w.start)), wertKachel('Sätze', zahl(saetze)),
                 wertKachel('Volumen', zahl(volumen(w)), 'kg'));
    inhalt.append(el('p', 'leise', datumLang(w.datum)), werte);
    if (w.rekorde && w.rekorde.length) {
      const r = el('div', 'hinweis');
      r.append(el('div', 'hinweis__titel', '🏆 Neue Bestwerte'));
      w.rekorde.forEach((x) => r.append(el('p', null, `${uebung(x.uid).name}: ${zahl(x.kg, 1)} kg × ${x.wdh} (≈ ${zahl(x.e1rm, 1)} kg 1RM)`)));
      inhalt.append(r);
    }
    w.uebungen.forEach((u) => {
      const fertig = u.saetze.filter((s) => s.fertig);
      if (!fertig.length) return;
      const k = karte(uebung(u.uid).name);
      fertig.forEach((s, i) => {
        const z = el('div', 'zeile'); z.style.cursor = 'default';
        z.append(el('div', 'zeile__text', `Satz ${i + 1}`),
                 el('div', 'zeile__rechts', `${s.kg ? zahl(s.kg, s.kg % 1 ? 1 : 0) + ' kg × ' : ''}${s.wdh}${uebung(u.uid).zeit ? ' s' : ''}`));
        k.append(z);
      });
      inhalt.append(k);
    });
    if (w.notiz) { const n = karte('Notiz'); n.append(el('p', null, w.notiz)); inhalt.append(n); }
    inhalt.append(knopf('Training löschen', 'knopf--gefahr', () => {
      if (!confirm('Dieses Training wirklich löschen?')) return;
      D().workouts = D().workouts.filter((x) => x.id !== w.id);
      Speicher.sichern(); schliessen(); neuZeichnen();
    }));
  });
}

/* --- Übungsbibliothek --------------------------------------------------- */

function uebungsBibliothek(ziel, beiWahl, { ort, gruppe } = {}) {
  const suche = el('div', 'suche');
  suche.innerHTML = ikon('suche');
  const e = eingabe('search', App.uebungSuche, { platzhalter: 'Übung suchen' });
  e.setAttribute('aria-label', 'Übung suchen');
  suche.append(e);
  const filter = el('div', 'filter');
  const liste = el('div');
  let aktGruppe = gruppe || App.uebungFilter;
  ['alle', ...App.uebungen.gruppen].forEach((g) => {
    const c = el('button', 'chip', g === 'alle' ? 'Alle' : g);
    c.type = 'button';
    c.setAttribute('aria-pressed', String(g === aktGruppe));
    c.onclick = () => {
      aktGruppe = g;
      if (!gruppe) App.uebungFilter = g;
      filter.querySelectorAll('.chip').forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
      zeichnen();
    };
    filter.append(c);
  });
  const zeichnen = () => {
    liste.replaceChildren();
    const q = e.value.trim().toLowerCase();
    const treffer = App.uebungen.uebungen.filter((u) =>
      (aktGruppe === 'alle' || u.gruppe === aktGruppe) &&
      (!ort || u.orte.includes(ort)) &&
      (!q || u.name.toLowerCase().includes(q) || u.gruppe.toLowerCase().includes(q)));
    if (!treffer.length) { liste.append(leerzustand('Nichts gefunden', 'Versuche einen anderen Suchbegriff.')); return; }
    const k = karte(null);
    treffer.forEach((u) => {
      const z = el('button', 'zeile');
      z.type = 'button';
      z.append(el('div', 'zeile__ikon', u.gruppe.slice(0, 2)));
      const text = el('div', 'zeile__text');
      text.append(el('div', 'zeile__titel', u.name),
                  el('div', 'zeile__meta', `${u.gruppe} · ${u.orte.map((o) => o === 'studio' ? 'Studio' : 'Zuhause').join(' & ')}`));
      const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
      z.append(text, pf);
      z.onclick = () => beiWahl(u);
      k.append(z);
    });
    liste.append(k);
  };
  e.oninput = () => { if (!gruppe) App.uebungSuche = e.value; zeichnen(); };
  ziel.append(suche, filter, liste);
  zeichnen();
}

function uebungWaehlen(gruppe, beiWahl) {
  blattOeffnen(gruppe ? `Ersatz: ${gruppe}` : 'Übung wählen', (inhalt, schliessen) => {
    uebungsBibliothek(inhalt, (u) => { schliessen(); beiWahl(u); }, { gruppe: gruppe || undefined });
  });
}

function uebungBlatt(id) {
  const u = uebung(id);
  blattOeffnen(u.name, (inhalt) => {
    const marken = el('p');
    marken.append(el('span', 'marke marke--akzent', u.gruppe));
    u.orte.forEach((o) => marken.append(el('span', 'marke', o === 'studio' ? 'Studio' : 'Zuhause')));
    inhalt.append(marken);
    inhalt.append(abschnitt('Ausführung'));
    u.schritte.forEach((s, i) => {
      const z = el('div', 'schritt');
      z.append(el('div', 'schritt__nr', String(i + 1)), el('div', 'schritt__text', s));
      inhalt.append(z);
    });
    if (u.tipp) {
      const h = el('div', 'hinweis'); h.style.marginTop = '12px';
      h.append(el('div', 'hinweis__titel', 'Coach-Tipp'), el('p', null, u.tipp));
      inhalt.append(h);
    }
    // Eigener Verlauf
    const verlauf = [];
    D().workouts.forEach((w) => w.uebungen.forEach((x) => {
      if (x.uid !== id) return;
      const fertig = x.saetze.filter((s) => s.fertig);
      if (!fertig.length) return;
      verlauf.push({ datum: w.datum, wert: Math.max(...fertig.map((s) => u.gewicht ? e1rm(s.kg, s.wdh) : (s.wdh || 0))), saetze: fertig });
    }));
    inhalt.append(abschnitt('Dein Verlauf'));
    if (!verlauf.length) { inhalt.append(el('p', 'leise', 'Noch nicht trainiert.')); return; }
    if (verlauf.length > 1) {
      const k = karte(u.gewicht ? 'Geschätztes 1RM' : (u.zeit ? 'Beste Zeit' : 'Beste Wiederholungen'));
      k.append(liniendiagramm(verlauf, { einheit: u.gewicht ? 'kg' : (u.zeit ? 's' : ''), label: `Verlauf ${u.name}` }));
      inhalt.append(k);
    }
    const k = karte(null);
    [...verlauf].reverse().slice(0, 8).forEach((v) => {
      const z = el('div', 'zeile'); z.style.cursor = 'default';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', datumMittel(v.datum)),
               el('div', 'zeile__meta', v.saetze.map((s) => `${s.kg ? zahl(s.kg, s.kg % 1 ? 1 : 0) + '×' : ''}${s.wdh}`).join('  ·  ')));
      z.append(t);
      if (u.gewicht) z.append(el('div', 'zeile__rechts', `${zahl(v.wert, 1)} kg`));
      k.append(z);
    });
    inhalt.append(k);
  });
}

/* --- Workout-Modus ------------------------------------------------------ */

function workoutStarten(plantag) {
  const d = D();
  if (d.aktiv) {
    if (!confirm(`„${d.aktiv.name}" läuft noch. Verwerfen und neu starten?`)) { workoutOeffnen(); return; }
  }
  d.aktiv = {
    id: neueId(),
    tagId: plantag ? plantag.id : null,
    name: plantag ? plantag.name : 'Freies Training',
    datum: heuteText(),
    start: Date.now(),
    uebungen: (plantag ? plantag.uebungen : []).map((pu) => ({
      uid: pu.uid, ziel: pu.wdh, pause: pu.pause, notiz: pu.notiz,
      saetze: Array.from({ length: pu.saetze }, () => ({ kg: null, wdh: null, fertig: false }))
    }))
  };
  Speicher.sichern();
  workoutOeffnen();
}

function workoutOeffnen() {
  const w = D().aktiv;
  if (!w) return;
  const uhr = el('span', 'marke marke--akzent');
  uhr.style.cssText = 'font-size:13px;padding:4px 10px;font-variant-numeric:tabular-nums';
  let takt;
  blattOeffnen(w.name, (inhalt, schliessen, blatt) => {
    const kennzahlen = el('div', 'workout-kopf');
    const aktualisieren = () => {
      uhr.textContent = uhrzeit((Date.now() - w.start) / 1000);
      const alle = w.uebungen.reduce((a, u) => a + u.saetze.length, 0);
      const fertig = w.uebungen.reduce((a, u) => a + u.saetze.filter((s) => s.fertig).length, 0);
      kennzahlen.replaceChildren(
        wertKachel('Sätze', `${fertig}/${alle}`),
        wertKachel('Volumen', zahl(volumen(w)), 'kg'),
        wertKachel('Übungen', zahl(w.uebungen.length)));
    };
    takt = setInterval(() => { uhr.textContent = uhrzeit((Date.now() - w.start) / 1000); }, 1000);

    const liste = el('div');
    const zeichnen = () => {
      liste.replaceChildren();
      if (!w.uebungen.length) liste.append(leerzustand('Noch keine Übung', 'Füge unten deine erste Übung hinzu.'));
      w.uebungen.forEach((wu, ui) => liste.append(uebungKarte(w, wu, ui, zeichnen, aktualisieren)));
      aktualisieren();
    };
    inhalt.append(kennzahlen, liste);
    zeichnen();

    inhalt.append(knopf('Übung hinzufügen', 'knopf--zweit', () => uebungWaehlen(null, (u) => {
      w.uebungen.push({ uid: u.id, ziel: u.zeit ? '30–45' : '8–12', pause: 90, notiz: '',
                        saetze: Array.from({ length: 3 }, () => ({ kg: null, wdh: null, fertig: false })) });
      Speicher.sichern(); zeichnen();
    }), 'plus'));
    const verwerfen = linkKnopf('Training verwerfen', () => {
      if (!confirm('Training verwerfen? Eingetragene Sätze gehen verloren.')) return;
      D().aktiv = null; Speicher.sichern(); Pause.stopp(); schliessen(); neuZeichnen();
    });
    verwerfen.style.cssText = 'display:block;margin:18px auto 0;color:var(--ink-soft)';
    inhalt.append(verwerfen);

    blattFuss(blatt, knopf('Training beenden', null, () => workoutBeenden(schliessen), 'haken'));
  }, { kopfExtra: uhr, beimSchliessen: () => { clearInterval(takt); neuZeichnen(); } });
}

function uebungKarte(w, wu, ui, neuAufbauen, aktualisieren) {
  const u = uebung(wu.uid);
  const k = el('div', 'karte uebung-karte');
  const kopf = el('div', 'uebung-karte__kopf');
  const name = el('div', 'uebung-karte__name', u.name);
  name.append(el('div', 'uebung-karte__ziel', `Ziel: ${wu.saetze.length} × ${wu.ziel} ${u.zeit ? 'Sek.' : 'Wdh.'} · Pause ${wu.pause} s`));
  name.style.cursor = 'pointer';
  name.onclick = () => uebungBlatt(u.id);
  const tauschen = el('button', 'ikon-knopf ikon-knopf--plain'); tauschen.innerHTML = ikon('tauschen');
  tauschen.setAttribute('aria-label', 'Übung tauschen');
  tauschen.onclick = () => uebungWaehlen(u.gruppe, (neu) => { wu.uid = neu.id; Speicher.sichern(); neuAufbauen(); });
  const weg = el('button', 'ikon-knopf ikon-knopf--plain'); weg.innerHTML = ikon('muell');
  weg.setAttribute('aria-label', 'Übung entfernen');
  weg.onclick = () => {
    if (wu.saetze.some((s) => s.fertig) && !confirm(`${u.name} mit allen Sätzen entfernen?`)) return;
    w.uebungen.splice(ui, 1); Speicher.sichern(); neuAufbauen();
  };
  kopf.append(name, tauschen, weg);
  k.append(kopf);
  if (wu.notiz) k.append(el('div', 'uebung-karte__notiz', `📝 ${wu.notiz}`));

  const vorher = letzteSaetze(wu.uid, w.id) || [];
  const tabelle = el('table', 'saetze');
  tabelle.innerHTML = `<thead><tr><th>Satz</th><th>Zuletzt</th><th>kg</th><th>${u.zeit ? 'Sek.' : 'Wdh.'}</th><th><span class="versteckt">Erledigt</span></th></tr></thead>`;
  const tbody = el('tbody');
  wu.saetze.forEach((s, si) => {
    const tr = el('tr', s.fertig ? 'fertig' : '');
    const v = vorher[si] || vorher[vorher.length - 1];
    const vorText = v ? `${v.kg ? zahl(v.kg, v.kg % 1 ? 1 : 0) + '×' : ''}${v.wdh}` : '–';
    // Vorschlag: was in diesem Workout im Satz davor stand, sonst das letzte Mal.
    const davor = si > 0 ? wu.saetze[si - 1] : null;
    const kgVorschlag = (davor && davor.kg) || (v && v.kg) || '';
    const wdhVorschlag = (davor && davor.wdh) || (v && v.wdh) || '';
    // Echte Vorschläge stehen zusätzlich in data-vorschlag. Nur die werden
    // beim Abhaken übernommen — die untere Zielgrenze als Platzhalter ist
    // bloß Orientierung und soll nie ungefragt im Protokoll landen.
    const kg = eingabe('text', s.kg != null ? String(s.kg).replace('.', ',') : '', { modus: 'decimal', platzhalter: kgVorschlag ? String(kgVorschlag).replace('.', ',') : (u.gewicht ? 'kg' : '–') });
    kg.setAttribute('aria-label', `Satz ${si + 1} Gewicht`);
    if (kgVorschlag) kg.dataset.vorschlag = kgVorschlag;
    const wdh = eingabe('text', s.wdh != null ? s.wdh : '', { modus: 'numeric', platzhalter: wdhVorschlag ? String(wdhVorschlag) : wu.ziel.split('–')[0] });
    wdh.setAttribute('aria-label', `Satz ${si + 1} ${u.zeit ? 'Sekunden' : 'Wiederholungen'}`);
    if (wdhVorschlag) wdh.dataset.vorschlag = wdhVorschlag;
    kg.oninput = () => { s.kg = leseZahl(kg.value); Speicher.sichern(); };
    wdh.oninput = () => { s.wdh = leseZahl(wdh.value); Speicher.sichern(); };
    const h = el('button', 'haken'); h.type = 'button';
    h.innerHTML = ikon('haken');
    h.setAttribute('aria-pressed', String(s.fertig));
    h.setAttribute('aria-label', `Satz ${si + 1} erledigt`);
    h.onclick = () => {
      Pause.vorbereiten();
      if (!s.fertig) {
        if (s.kg == null && kg.dataset.vorschlag) { s.kg = Number(kg.dataset.vorschlag); kg.value = kg.dataset.vorschlag.replace('.', ','); }
        if (s.wdh == null && wdh.dataset.vorschlag) { s.wdh = Number(wdh.dataset.vorschlag); wdh.value = wdh.dataset.vorschlag; }
        if (!s.wdh) { wdh.focus(); toast(u.zeit ? 'Bitte Sekunden eintragen' : 'Bitte Wiederholungen eintragen'); return; }
      }
      s.fertig = !s.fertig;
      tr.className = s.fertig ? 'fertig' : '';
      h.setAttribute('aria-pressed', String(s.fertig));
      Speicher.sichern();
      aktualisieren();
      if (s.fertig) {
        // Nächsten offenen Satz vorbereiten: dessen Vorschlag zeigt jetzt diese Werte.
        const naechste = tbody.children[si + 1];
        if (naechste) {
          const [, , nKg, nWdh] = naechste.children;
          if (s.kg) { nKg.firstChild.placeholder = String(s.kg).replace('.', ','); nKg.firstChild.dataset.vorschlag = String(s.kg); }
          nWdh.firstChild.placeholder = String(s.wdh);
          nWdh.firstChild.dataset.vorschlag = String(s.wdh);
        }
        if (wu.pause) Pause.start(wu.pause, u.name);
      }
    };
    const zellen = [el('td', null, String(si + 1)), el('td', 'vorher', vorText), el('td'), el('td'), el('td')];
    zellen[2].append(kg); zellen[3].append(wdh); zellen[4].append(h);
    tr.append(...zellen);
    tbody.append(tr);
  });
  tabelle.append(tbody);
  k.append(tabelle);

  const aktionen = el('div', 'satz-aktionen');
  aktionen.append(linkKnopf('Satz', () => { wu.saetze.push({ kg: null, wdh: null, fertig: false }); Speicher.sichern(); neuAufbauen(); }, 'plus'));
  if (wu.saetze.length > 1) {
    aktionen.append(linkKnopf('Satz', () => { wu.saetze.pop(); Speicher.sichern(); neuAufbauen(); }, 'minus'));
  }
  k.append(aktionen);
  return k;
}

function workoutBeenden(schliessen) {
  const d = D();
  const w = d.aktiv;
  const fertig = w.uebungen.reduce((a, u) => a + u.saetze.filter((s) => s.fertig).length, 0);
  if (!fertig) {
    if (confirm('Noch kein Satz abgehakt. Training ohne Speichern beenden?')) {
      d.aktiv = null; Speicher.sichern(); Pause.stopp(); schliessen();
    }
    return;
  }
  const offen = w.uebungen.reduce((a, u) => a + u.saetze.filter((s) => !s.fertig).length, 0);
  if (offen && !confirm(`${offen} Sätze sind noch offen. Trotzdem beenden?`)) return;

  // Rekorde gegen alles vor diesem Training prüfen.
  const rekorde = [];
  w.uebungen.forEach((u) => {
    if (!uebung(u.uid).gewicht) return;
    const vorher = bestwert(u.uid, w.id);
    let best = null;
    u.saetze.forEach((s) => {
      if (!s.fertig || !s.kg) return;
      const wert = e1rm(s.kg, s.wdh);
      if (wert > vorher && (!best || wert > best.e1rm)) best = { uid: u.uid, kg: s.kg, wdh: s.wdh, e1rm: wert };
    });
    // Erstes Mal zählt nicht als Rekord — sonst wäre jede neue Übung einer.
    if (best && vorher > 0) rekorde.push(best);
  });

  const fertigesWorkout = { ...w, ende: Date.now(), rekorde,
    uebungen: w.uebungen.map((u) => ({ uid: u.uid, saetze: u.saetze.filter((s) => s.fertig) })).filter((u) => u.saetze.length) };
  d.workouts.push(fertigesWorkout);
  d.aktiv = null;
  Speicher.sichern();
  Pause.stopp();
  schliessen();
  workoutZusammenfassung(fertigesWorkout);
}

function workoutZusammenfassung(w) {
  blattOeffnen('Training abgeschlossen', (inhalt, schliessen, blatt) => {
    const held = el('div', 'held');
    held.append(el('div', 'held__label', datumLang(w.datum)),
                el('div', 'held__titel', `${w.name} geschafft! 🎉`),
                el('div', 'held__text', `Das war Einheit ${workoutsInWoche(w.datum).length} von ${D().profil.tage} diese Woche.`));
    inhalt.append(held);
    const werte = el('div', 'werte werte--3');
    werte.style.marginBottom = '14px';
    werte.append(wertKachel('Dauer', dauerText(w.ende - w.start)),
                 wertKachel('Sätze', zahl(w.uebungen.reduce((a, u) => a + u.saetze.length, 0))),
                 wertKachel('Volumen', zahl(volumen(w)), 'kg'));
    inhalt.append(werte);
    if (w.rekorde.length) {
      const k = karte('Neue Bestwerte', 'pokal');
      w.rekorde.forEach((r) => {
        const z = el('div', 'zeile'); z.style.cursor = 'default';
        const t = el('div', 'zeile__text');
        t.append(el('div', 'zeile__titel', uebung(r.uid).name), el('div', 'zeile__meta', `${zahl(r.kg, r.kg % 1 ? 1 : 0)} kg × ${r.wdh}`));
        z.append(t, el('div', 'zeile__rechts', `≈ ${zahl(r.e1rm, 1)} kg`));
        k.append(z);
      });
      inhalt.append(k);
    }
    const notiz = el('textarea', 'eingabe');
    notiz.placeholder = 'Wie lief es? Schmerzen, Energie, Besonderheiten …';
    notiz.oninput = () => { w.notiz = notiz.value; Speicher.sichern(); };
    inhalt.append(feld('Notiz (optional)', notiz));
    blattFuss(blatt, knopf('Fertig', null, schliessen));
  }, { beimSchliessen: neuZeichnen });
}

/* --- Pausentimer -------------------------------------------------------- */

const Pause = {
  ende: 0, dauer: 0, takt: null, box: null, ton: null,

  /** Muss in einer Nutzeraktion laufen, sonst sperrt iOS den Ton. */
  vorbereiten() {
    if (this.ton || !(window.AudioContext || window.webkitAudioContext)) return;
    try { this.ton = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { this.ton = null; }
  },

  piep() {
    if (!this.ton) return;
    try {
      const o = this.ton.createOscillator(), g = this.ton.createGain();
      o.frequency.value = 880; o.connect(g); g.connect(this.ton.destination);
      g.gain.setValueAtTime(0.25, this.ton.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, this.ton.currentTime + 0.5);
      o.start(); o.stop(this.ton.currentTime + 0.5);
    } catch (e) { /* kein Ton, kein Problem */ }
  },

  start(sekunden, name) {
    this.stopp();
    this.dauer = sekunden;
    this.ende = Date.now() + sekunden * 1000;
    const box = el('div', 'pausentimer');
    box.setAttribute('role', 'timer');
    const zeit = el('span', 'pausentimer__zeit');
    const label = el('span', 'pausentimer__label', `Pause · ${name}`);
    const minus = el('button', null, '−15'); minus.type = 'button';
    minus.setAttribute('aria-label', 'Pause 15 Sekunden kürzer');
    const plus = el('button', null, '+15'); plus.type = 'button';
    plus.setAttribute('aria-label', 'Pause 15 Sekunden länger');
    const weg = el('button', null, 'Weiter'); weg.type = 'button';
    const balken = el('div', 'pausentimer__balken'); const fuell = el('i'); balken.append(fuell);
    minus.onclick = () => { this.ende -= 15000; this.dauer = Math.max(1, this.dauer - 15); };
    plus.onclick = () => { this.ende += 15000; this.dauer += 15; };
    weg.onclick = () => this.stopp();
    box.append(zeit, label, minus, plus, weg, balken);
    document.body.append(box);
    this.box = box;
    const tick = () => {
      const rest = (this.ende - Date.now()) / 1000;
      zeit.textContent = uhrzeit(rest);
      fuell.style.width = `${Math.max(0, Math.min(100, (rest / this.dauer) * 100))}%`;
      if (rest <= 0) {
        if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
        this.piep();
        toast('Pause vorbei — nächster Satz!');
        this.stopp();
      }
    };
    tick();
    this.takt = setInterval(tick, 250);
  },

  stopp() {
    clearInterval(this.takt);
    this.takt = null;
    if (this.box) { this.box.remove(); this.box = null; }
  }
};

/* --- Ansicht: Ernährung ------------------------------------------------- */

function ansichtErnaehrung(ziel) {
  const anzahl = Object.keys(D().einkauf.rezepte).length;
  ziel.append(segment([['tagebuch', 'Tagebuch'], ['mealprep', 'Meal Prep'], ['einkauf', `Einkauf${anzahl ? ` (${anzahl})` : ''}`]],
    App.ernaehrung, (id) => { App.ernaehrung = id; neuZeichnen(); }));
  if (App.ernaehrung === 'tagebuch') ernaehrungTagebuch(ziel);
  if (App.ernaehrung === 'mealprep') mealPrep(ziel);
  if (App.ernaehrung === 'einkauf') einkaufsliste(ziel);
}

function datumsleiste(datum, beiWechsel) {
  const leiste = el('div', 'datumsleiste');
  const zurueck = el('button', 'ikon-knopf'); zurueck.innerHTML = ikon('zurueck');
  zurueck.setAttribute('aria-label', 'Vorheriger Tag');
  zurueck.onclick = () => beiWechsel(tageVerschieben(datum, -1));
  const vor = el('button', 'ikon-knopf'); vor.innerHTML = ikon('weiter');
  vor.setAttribute('aria-label', 'Nächster Tag');
  vor.disabled = datum >= heuteText();
  vor.style.opacity = vor.disabled ? '.35' : '';
  vor.onclick = () => { if (!vor.disabled) beiWechsel(tageVerschieben(datum, 1)); };
  const heute = heuteText();
  const text = el('div', 'datumsleiste__text',
    datum === heute ? 'Heute' : datum === tageVerschieben(heute, -1) ? 'Gestern' : datumMittel(datum));
  text.append(el('small', null, datumLang(datum)));
  leiste.append(zurueck, text, vor);
  return leiste;
}

function ernaehrungTagebuch(ziel) {
  const d = D();
  const datum = App.essensDatum || heuteText();
  ziel.append(datumsleiste(datum, (neu) => { App.essensDatum = neu; neuZeichnen(); }));

  const s = tagesSumme(datum);
  const rest = d.ziele.kcal - s.kcal;
  const k = karte(null);
  const oben = el('div');
  oben.style.cssText = 'display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:14px;gap:10px';
  const links = el('div');
  links.append(el('div', 'leise', rest >= 0 ? 'Noch übrig' : 'Über dem Ziel'));
  const gz = el('div', 'gross-zahl', zahl(Math.abs(rest)));
  gz.append(el('small', null, 'kcal'));
  if (rest < 0) gz.style.color = 'var(--warn)';
  links.append(gz);
  const rechts = el('div', 'leise');
  rechts.style.textAlign = 'right';
  rechts.innerHTML = `Ziel <b style="color:var(--ink)">${zahl(d.ziele.kcal)}</b><br>Gegessen <b style="color:var(--ink)">${zahl(s.kcal)}</b>`;
  oben.append(links, rechts);
  k.append(oben,
    balkenZeile('Eiweiß', Math.round(s.e), d.ziele.e, 'g', 'var(--c-eiweiss)'),
    balkenZeile('Kohlenhydrate', Math.round(s.kh), d.ziele.kh, 'g', 'var(--c-kh)'),
    balkenZeile('Fett', Math.round(s.f), d.ziele.f, 'g', 'var(--c-fett)'));
  ziel.append(k);

  const tag = Speicher.tagLesen(datum) || { essen: [] };
  MAHLZEITEN.forEach((m) => {
    const eintraege = tag.essen.filter((x) => x.mahlzeit === m.id);
    const mk = el('div', 'karte');
    const kopf = el('div', 'mahlzeit__kopf');
    kopf.append(el('h3', null, m.name));
    if (eintraege.length) kopf.append(el('span', 'mahlzeit__kcal', `${zahl(eintraege.reduce((a, x) => a + x.kcal, 0))} kcal`));
    const plus = el('button', 'ikon-knopf'); plus.innerHTML = ikon('plus');
    plus.setAttribute('aria-label', `${m.name}: Eintrag hinzufügen`);
    plus.onclick = () => essenHinzufuegen(datum, m.id);
    kopf.append(plus);
    mk.append(kopf);
    eintraege.forEach((x) => {
      const z = el('button', 'zeile');
      z.type = 'button';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', x.name),
               el('div', 'zeile__meta', `${x.menge ? `${zahl(x.menge)} ${x.einheit} · ` : ''}E ${zahl(x.e)} · KH ${zahl(x.kh)} · F ${zahl(x.f)}`));
      z.append(t, el('div', 'zeile__rechts', `${zahl(x.kcal)}`));
      z.onclick = () => eintragBearbeiten(datum, x);
      mk.append(z);
    });
    ziel.append(mk);
  });

  const kw = karte('Wasser', 'wasser', `${tag.wasser || 0} × 250 ml`);
  kw.append(wasserPerlen(datum, () => { kw.querySelector('.zaehler').textContent = `${Speicher.tagLesen(datum).wasser} × 250 ml`; }));
  ziel.append(kw);
}

function eintragSpeichern(datum, eintrag) {
  const t = Speicher.tag(datum);
  t.essen.push({ id: neueId(), ...eintrag });
  // Zuletzt gegessen: ohne Doppelte, die neuesten vorn.
  const vorlage = { ...eintrag }; delete vorlage.mahlzeit;
  D().zuletzt = [vorlage, ...D().zuletzt.filter((z) => z.name !== eintrag.name)].slice(0, 15);
  Speicher.sichern();
}

function essenHinzufuegen(datum, mahlzeit) {
  let reiter = 'lebensmittel';
  blattOeffnen(`${MAHLZEITEN.find((m) => m.id === mahlzeit).name} · ${datum === heuteText() ? 'heute' : datumKurz(datum)}`, (inhalt, schliessen) => {
    const fertig = (eintrag) => {
      eintragSpeichern(datum, { ...eintrag, mahlzeit });
      toast(`${eintrag.name} eingetragen`);
      schliessen();
    };
    const bereich = el('div');
    const zeichnen = () => {
      bereich.replaceChildren();
      if (reiter === 'lebensmittel') lebensmittelSuche(bereich, fertig);
      if (reiter === 'rezepte') rezeptAuswahl(bereich, fertig);
      if (reiter === 'schnell') schnellEintrag(bereich, fertig);
    };
    const seg = () => segment([['lebensmittel', 'Lebensmittel'], ['rezepte', 'Rezepte'], ['schnell', 'Schnell']], reiter,
      (id) => { reiter = id; inhalt.firstChild.replaceWith(seg()); zeichnen(); });
    inhalt.append(seg(), bereich);
    zeichnen();
  }, { beimSchliessen: neuZeichnen });
}

function lebensmittelSuche(ziel, fertig) {
  const suche = el('div', 'suche');
  suche.innerHTML = ikon('suche');
  const e = eingabe('search', '', { platzhalter: 'Lebensmittel suchen, z. B. Skyr' });
  e.setAttribute('aria-label', 'Lebensmittel suchen');
  suche.append(e);
  const liste = el('div');
  const zeichnen = () => {
    liste.replaceChildren();
    const q = e.value.trim().toLowerCase();
    if (!q && D().zuletzt.length) {
      liste.append(abschnitt('Zuletzt gegessen'));
      const k = karte(null);
      D().zuletzt.forEach((z) => {
        const r = el('button', 'zeile'); r.type = 'button';
        const t = el('div', 'zeile__text');
        t.append(el('div', 'zeile__titel', z.name), el('div', 'zeile__meta', `${z.menge ? `${zahl(z.menge)} ${z.einheit} · ` : ''}E ${zahl(z.e)} g`));
        const p = el('span', 'zeile__pfeil'); p.innerHTML = ikon('plus');
        r.append(t, el('div', 'zeile__rechts', `${zahl(z.kcal)} kcal`), p);
        r.onclick = () => fertig({ ...z });
        k.append(r);
      });
      liste.append(k);
      liste.append(abschnitt('Alle Lebensmittel'));
    }
    const treffer = App.lebensmittel.lebensmittel.filter((l) => !q || l.name.toLowerCase().includes(q) || l.kat.toLowerCase().includes(q));
    if (!treffer.length) {
      liste.append(leerzustand('Nicht in der Liste', 'Nutze „Schnell", um Kalorien und Makros direkt einzutragen — z. B. von der Verpackung.'));
      return;
    }
    const k = karte(null);
    treffer.forEach((l) => {
      const r = el('button', 'zeile'); r.type = 'button';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', l.name), el('div', 'zeile__meta', `100 g · E ${zahl(l.e, 1)} · KH ${zahl(l.kh, 1)} · F ${zahl(l.f, 1)}`));
      r.append(t, el('div', 'zeile__rechts', `${zahl(l.kcal)} kcal`));
      r.onclick = () => mengeWaehlen(l, fertig);
      k.append(r);
    });
    liste.append(k);
  };
  e.oninput = zeichnen;
  ziel.append(suche, liste);
  zeichnen();
}

function mengeWaehlen(l, fertig) {
  blattOeffnen(l.name, (inhalt, schliessen, blatt) => {
    let gramm = l.portion;
    const werte = el('div', 'werte');
    const zeichnen = () => {
      const n = naehrwerteFuer(l, gramm);
      werte.replaceChildren(wertKachel('Kalorien', zahl(n.kcal), 'kcal'), wertKachel('Eiweiß', zahl(n.e, 1), 'g'),
                            wertKachel('Kohlenhydrate', zahl(n.kh, 1), 'g'), wertKachel('Fett', zahl(n.f, 1), 'g'));
    };
    const st = stepper(gramm, { schritt: 10, min: 1, max: 5000, label: 'Menge in Gramm', beiAenderung: (n) => { gramm = n; zeichnen(); } });
    inhalt.append(el('div', 'feld__label', 'Menge in Gramm'), st);
    const schnell = el('div', 'schnell');
    [[`1 Portion (${l.portion} g)`, l.portion], ['100 g', 100], ['½ Portion', Math.round(l.portion / 2)], ['2 Portionen', l.portion * 2]].forEach(([t, g]) => {
      const c = el('button', 'chip', t); c.type = 'button';
      c.onclick = () => { gramm = g; st.querySelector('input').value = g; zeichnen(); };
      schnell.append(c);
    });
    inhalt.append(schnell);
    werte.style.marginTop = '16px';
    inhalt.append(werte);
    zeichnen();
    blattFuss(blatt, knopf('Eintragen', null, () => {
      schliessen();
      fertig({ name: l.name, menge: gramm, einheit: 'g', ...naehrwerteFuer(l, gramm) });
    }, 'plus'));
  });
}

function rezeptAuswahl(ziel, fertig) {
  const k = karte(null);
  App.rezepte.rezepte.forEach((r) => {
    const z = el('button', 'zeile'); z.type = 'button';
    const t = el('div', 'zeile__text');
    t.append(el('div', 'zeile__titel', r.name), el('div', 'zeile__meta', `1 Portion · E ${r.e} · KH ${r.kh} · F ${r.f}`));
    z.append(t, el('div', 'zeile__rechts', `${r.kcal} kcal`));
    z.onclick = () => fertig({ name: r.name, menge: 1, einheit: 'Portion', kcal: r.kcal, e: r.e, kh: r.kh, f: r.f });
    k.append(z);
  });
  ziel.append(k);
}

function schnellEintrag(ziel, fertig) {
  const name = eingabe('text', '', { platzhalter: 'z. B. Restaurant, Pasta' });
  const kcal = eingabe('text', '', { modus: 'decimal', platzhalter: '0' });
  const e = eingabe('text', '', { modus: 'decimal', platzhalter: '0' });
  const kh = eingabe('text', '', { modus: 'decimal', platzhalter: '0' });
  const f = eingabe('text', '', { modus: 'decimal', platzhalter: '0' });
  ziel.append(feld('Bezeichnung', name), feld('Kalorien (kcal)', kcal));
  const reihe = el('div', 'reihe');
  reihe.append(feld('Eiweiß (g)', e), feld('KH (g)', kh), feld('Fett (g)', f));
  ziel.append(reihe);
  ziel.append(el('p', 'leise', 'Keine Makros zur Hand? Kalorien reichen — lieber grob erfassen als gar nicht.'));
  ziel.append(knopf('Eintragen', null, () => {
    const k = leseZahl(kcal.value), ew = leseZahl(e.value) || 0, k2 = leseZahl(kh.value) || 0, fw = leseZahl(f.value) || 0;
    const kalorien = k != null ? k : Math.round(ew * 4 + k2 * 4 + fw * 9);
    if (!kalorien) { toast('Bitte Kalorien oder Makros eintragen'); return; }
    fertig({ name: name.value.trim() || 'Schnelleintrag', menge: null, einheit: '', kcal: Math.round(kalorien), e: ew, kh: k2, f: fw });
  }, 'plus'));
}

function eintragBearbeiten(datum, x) {
  blattOeffnen(x.name, (inhalt, schliessen, blatt) => {
    const t = Speicher.tag(datum);
    const lm = App.lebensmittel.lebensmittel.find((l) => l.name === x.name);
    const rezept = App.rezepte.rezepte.find((r) => r.name === x.name);
    let menge = x.menge;
    const werte = el('div', 'werte');
    const n = () => {
      if (lm && x.einheit === 'g') return naehrwerteFuer(lm, menge);
      if (rezept && x.einheit === 'Portion') return { kcal: Math.round(rezept.kcal * menge), e: rezept.e * menge, kh: rezept.kh * menge, f: rezept.f * menge };
      return { kcal: x.kcal, e: x.e, kh: x.kh, f: x.f };
    };
    const zeichnen = () => {
      const w = n();
      werte.replaceChildren(wertKachel('Kalorien', zahl(w.kcal), 'kcal'), wertKachel('Eiweiß', zahl(w.e, 1), 'g'),
                            wertKachel('Kohlenhydrate', zahl(w.kh, 1), 'g'), wertKachel('Fett', zahl(w.f, 1), 'g'));
    };
    if ((lm && x.einheit === 'g') || (rezept && x.einheit === 'Portion')) {
      inhalt.append(el('div', 'feld__label', x.einheit === 'g' ? 'Menge in Gramm' : 'Portionen'),
        stepper(menge, { schritt: x.einheit === 'g' ? 10 : 0.5, min: x.einheit === 'g' ? 1 : 0.5, label: 'Menge', beiAenderung: (v) => { menge = v; zeichnen(); } }));
      werte.style.marginTop = '16px';
    }
    const ms = el('div', 'feld'); ms.style.marginTop = '14px';
    ms.append(el('div', 'feld__label', 'Mahlzeit'));
    let mahlzeit = x.mahlzeit;
    ms.append(wahl(MAHLZEITEN.map((m) => ({ id: m.id, name: m.name })), mahlzeit, (id) => { mahlzeit = id; }, 2));
    inhalt.append(werte, ms);
    zeichnen();
    blattFuss(blatt,
      knopf('Löschen', 'knopf--gefahr', () => { t.essen = t.essen.filter((y) => y.id !== x.id); Speicher.sichern(); schliessen(); }),
      knopf('Speichern', null, () => { Object.assign(x, n(), { menge, mahlzeit }); Speicher.sichern(); schliessen(); }));
  }, { beimSchliessen: neuZeichnen });
}

/* --- Meal Prep ---------------------------------------------------------- */

function mealPrep(ziel) {
  const filter = el('div', 'filter');
  const optionen = [['alle', 'Alle'], ...App.rezepte.kategorien.map((k) => [k, k]), ['vegetarisch', 'Vegetarisch'], ['eiweißreich', 'Eiweißreich']];
  optionen.forEach(([id, name]) => {
    const c = el('button', 'chip', name); c.type = 'button';
    c.setAttribute('aria-pressed', String(App.rezeptFilter === id));
    c.onclick = () => { App.rezeptFilter = id; neuZeichnen(); };
    filter.append(c);
  });
  ziel.append(filter);
  const f = App.rezeptFilter;
  const liste = App.rezepte.rezepte.filter((r) => f === 'alle' || r.kat === f ||
    (f === 'vegetarisch' ? r.tags.includes('vegetarisch') || r.tags.includes('vegan') : r.tags.includes(f)));
  liste.forEach((r) => {
    const k = el('button', 'rezept'); k.type = 'button';
    const t = el('div', 'rezept__text');
    t.append(el('div', 'rezept__name', r.name),
             el('div', 'rezept__meta', `${r.kat} · ${r.zeit} Min. · ${r.portionen} Portionen · ${r.haltbar} Tage haltbar`));
    const m = el('div', 'makros'); m.style.marginTop = '5px';
    m.innerHTML = `<span><i class="makro-punkt" style="background:var(--c-eiweiss)"></i>E <b>${r.e} g</b></span>` +
      `<span><i class="makro-punkt" style="background:var(--c-kh)"></i>KH <b>${r.kh} g</b></span>` +
      `<span><i class="makro-punkt" style="background:var(--c-fett)"></i>F <b>${r.f} g</b></span>`;
    t.append(m);
    const kc = el('div', 'rezept__kcal', String(r.kcal)); kc.append(el('small', null, 'kcal/Port.'));
    k.append(t, kc);
    if (D().einkauf.rezepte[r.id]) k.style.borderColor = 'var(--accent)';
    k.onclick = () => rezeptBlatt(r);
    ziel.append(k);
  });
  ziel.append(el('p', 'fusstext', 'Nährwerte sind gerundete Richtwerte je Portion. Gekochtes im Kühlschrank bei höchstens 4 °C lagern und vor dem Essen vollständig durcherhitzen.'));
}

function mengeText(m, faktor) {
  if (m == null) return '';
  const wert = m * faktor;
  const gerundet = wert >= 50 ? Math.round(wert / 5) * 5 : Math.round(wert * 10) / 10;
  return zahl(gerundet, gerundet % 1 ? 1 : 0);
}

function rezeptBlatt(r) {
  blattOeffnen(r.name, (inhalt, schliessen, blatt) => {
    let portionen = D().einkauf.rezepte[r.id] || r.portionen;
    const marken = el('p');
    marken.append(el('span', 'marke marke--akzent', r.kat));
    r.tags.forEach((t) => marken.append(el('span', 'marke', t)));
    inhalt.append(marken);
    const werte = el('div', 'werte');
    werte.append(wertKachel('Kalorien', zahl(r.kcal), 'kcal'), wertKachel('Eiweiß', zahl(r.e), 'g'),
                 wertKachel('Kohlenhydrate', zahl(r.kh), 'g'), wertKachel('Fett', zahl(r.f), 'g'));
    inhalt.append(el('div', 'leise', 'Pro Portion'), werte);
    inhalt.append(el('p', 'leise', `⏱ ${r.zeit} Min. · 🧊 ${r.haltbar} Tage im Kühlschrank haltbar`));

    inhalt.append(abschnitt('Zutaten'));
    inhalt.append(el('div', 'feld__label', 'Portionen'));
    const zutaten = el('div');
    const zeichnen = () => {
      zutaten.replaceChildren();
      const faktor = portionen / r.portionen;
      r.zutaten.forEach((z) => {
        const zeile = el('div', 'zutat');
        zeile.append(el('span', 'zutat__menge', z.m == null ? '' : `${mengeText(z.m, faktor)} ${z.e}`), el('span', null, z.n));
        zutaten.append(zeile);
      });
    };
    inhalt.append(stepper(portionen, { min: 1, max: 30, label: 'Portionen', beiAenderung: (n) => { portionen = Math.round(n); zeichnen(); } }));
    zutaten.style.marginTop = '8px';
    inhalt.append(zutaten);
    zeichnen();
    inhalt.append(abschnitt('Zubereitung'));
    r.schritte.forEach((s, i) => {
      const z = el('div', 'schritt');
      z.append(el('div', 'schritt__nr', String(i + 1)), el('div', 'schritt__text', s));
      inhalt.append(z);
    });
    const drauf = !!D().einkauf.rezepte[r.id];
    blattFuss(blatt,
      knopf('Gegessen', 'knopf--zweit', () => {
        eintragSpeichern(App.essensDatum || heuteText(), { name: r.name, menge: 1, einheit: 'Portion', kcal: r.kcal, e: r.e, kh: r.kh, f: r.f, mahlzeit: mahlzeitJetzt() });
        toast('1 Portion eingetragen');
      }),
      knopf(drauf ? 'Aktualisieren' : 'Einkaufsliste', null, () => {
        D().einkauf.rezepte[r.id] = portionen;
        Speicher.sichern(); toast(`${r.name} auf der Einkaufsliste`); schliessen();
      }, 'liste'));
  }, { beimSchliessen: neuZeichnen });
}

function einkaufsZutaten() {
  const sammlung = new Map();
  Object.entries(D().einkauf.rezepte).forEach(([id, portionen]) => {
    const r = App.rezepte.rezepte.find((x) => x.id === id);
    if (!r) return;
    const faktor = portionen / r.portionen;
    r.zutaten.forEach((z) => {
      const schluessel = `${z.n.toLowerCase()}|${z.e}`;
      const vorhanden = sammlung.get(schluessel);
      if (vorhanden) {
        if (z.m != null) vorhanden.m = (vorhanden.m || 0) + z.m * faktor;
        vorhanden.rezepte.push(r.name);
      } else {
        sammlung.set(schluessel, { schluessel, n: z.n, e: z.e, m: z.m == null ? null : z.m * faktor, rezepte: [r.name] });
      }
    });
  });
  return [...sammlung.values()].sort((a, b) => a.n.localeCompare(b.n, 'de'));
}

function einkaufsliste(ziel) {
  const e = D().einkauf;
  const ids = Object.keys(e.rezepte);
  if (!ids.length) {
    ziel.append(leerzustand('Einkaufsliste leer', 'Öffne ein Rezept unter „Meal Prep" und tippe auf „Auf Einkaufsliste". Die Zutaten aller Rezepte werden hier zusammengerechnet.'));
    return;
  }
  const kr = karte('Rezepte', 'ernaehrung');
  ids.forEach((id) => {
    const r = App.rezepte.rezepte.find((x) => x.id === id);
    if (!r) return;
    const z = el('div', 'zeile'); z.style.cursor = 'default';
    const t = el('div', 'zeile__text');
    t.append(el('div', 'zeile__titel', r.name), el('div', 'zeile__meta', `${e.rezepte[id]} Portionen`));
    const weg = el('button', 'ikon-knopf ikon-knopf--plain'); weg.innerHTML = ikon('schliessen');
    weg.setAttribute('aria-label', `${r.name} entfernen`);
    weg.onclick = () => { delete e.rezepte[id]; Speicher.sichern(); neuZeichnen(); };
    z.append(t, weg);
    kr.append(z);
  });
  ziel.append(kr);

  const zutaten = einkaufsZutaten();
  const erledigt = zutaten.filter((z) => e.abgehakt[z.schluessel]).length;
  const kz = karte('Einkaufen', 'liste', `${erledigt}/${zutaten.length}`);
  zutaten.forEach((z) => {
    const menge = z.m == null ? 'nach Geschmack' : `${mengeText(z.m, 1)} ${z.e}`;
    kz.append(hakenReihe(z.n, menge, !!e.abgehakt[z.schluessel], (an) => {
      if (an) e.abgehakt[z.schluessel] = true; else delete e.abgehakt[z.schluessel];
      Speicher.sichern();
      kz.querySelector('.zaehler').textContent = `${zutaten.filter((x) => e.abgehakt[x.schluessel]).length}/${zutaten.length}`;
    }));
  });
  ziel.append(kz);

  const reihe = el('div', 'reihe');
  reihe.append(
    knopf('Teilen', 'knopf--zweit', () => {
      const text = 'Einkaufsliste\n\n' + zutaten.filter((z) => !e.abgehakt[z.schluessel])
        .map((z) => `• ${z.m == null ? '' : mengeText(z.m, 1) + ' ' + z.e + ' '}${z.n}`).join('\n');
      teilen(text, 'Einkaufsliste');
    }, 'senden'),
    knopf('Leeren', 'knopf--gefahr', () => {
      if (!confirm('Einkaufsliste komplett leeren?')) return;
      D().einkauf = { rezepte: {}, abgehakt: {} }; Speicher.sichern(); neuZeichnen();
    }));
  ziel.append(reihe);
}

/* --- Ansicht: Check-in -------------------------------------------------- */

function ansichtCheckin(ziel) {
  ziel.append(segment([['heute', 'Täglich'], ['woche', 'Wöchentlich'], ['gewohnheiten', 'Gewohnheiten']], App.checkin,
    (id) => { App.checkin = id; neuZeichnen(); }));
  if (App.checkin === 'heute') checkinTaeglich(ziel);
  if (App.checkin === 'woche') checkinWoche(ziel);
  if (App.checkin === 'gewohnheiten') gewohnheitenVerwalten(ziel);
}

function checkinTaeglich(ziel) {
  const p = D().profil;
  const datum = App.checkinDatum || heuteText();
  ziel.append(datumsleiste(datum, (neu) => { App.checkinDatum = neu; neuZeichnen(); }));
  const tag = Speicher.tag(datum);

  // Schritte
  const ks = karte('Schritte', 'schritte');
  const stand = el('div');
  stand.style.cssText = 'display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px';
  const zahlEl = el('div', 'gross-zahl');
  const zielEl = el('div', 'leise');
  const sb = el('div', 'balken'); const sbi = el('i'); sbi.style.background = 'var(--c-schritte)'; sb.append(sbi);
  const schritteZeigen = () => {
    zahlEl.textContent = zahl(tag.schritte || 0);
    zielEl.textContent = `Ziel ${zahl(p.schrittziel)}`;
    sbi.style.width = `${Math.min(100, ((tag.schritte || 0) / p.schrittziel) * 100)}%`;
  };
  stand.append(zahlEl, zielEl);
  ks.append(stand, sb);
  const se = eingabe('number', tag.schritte || '', { modus: 'numeric', platzhalter: 'Schritte laut Handy oder Uhr' });
  se.setAttribute('aria-label', 'Schritte');
  se.style.marginTop = '12px';
  se.addEventListener('change', () => { tag.schritte = Math.max(0, Math.round(leseZahl(se.value) || 0)); Speicher.sichern(); schritteZeigen(); });
  ks.append(se);
  const schnell = el('div', 'schnell');
  [1000, 2500, 5000].forEach((n) => {
    const c = el('button', 'chip', `+${zahl(n)}`); c.type = 'button';
    c.onclick = () => { tag.schritte = (tag.schritte || 0) + n; se.value = tag.schritte; Speicher.sichern(); schritteZeigen(); };
    schnell.append(c);
  });
  ks.append(schnell);
  ks.append(el('p', 'fusstext', 'Übernimm die Zahl abends aus der Health-App, Google Fit oder deiner Uhr. Eine Web-App darf diese Daten nicht selbst auslesen.'));
  schritteZeigen();
  ziel.append(ks);

  // Schlaf
  const kl = karte('Schlaf (letzte Nacht)', 'schlaf');
  const s = { von: '', bis: '', qualitaet: null, ...(tag.schlaf || {}) };
  const dauerEl = el('div', 'gross-zahl');
  const dauerZeigen = () => {
    const h = schlafDauer(s);
    dauerEl.textContent = h ? zahl(h, 1) : '–';
    dauerEl.append(el('small', null, `Std. · Ziel ${zahl(p.schlafziel, 1)}`));
  };
  const sichern = () => { tag.schlaf = { ...s }; Speicher.sichern(); dauerZeigen(); };
  const von = eingabe('time', s.von); von.addEventListener('change', () => { s.von = von.value; sichern(); });
  const bis = eingabe('time', s.bis); bis.addEventListener('change', () => { s.bis = bis.value; sichern(); });
  const reihe = el('div', 'reihe');
  reihe.append(feld('Ins Bett', von), feld('Aufgestanden', bis));
  kl.append(dauerEl);
  reihe.style.marginTop = '12px';
  kl.append(reihe);
  const q = el('div', 'feld');
  q.append(el('div', 'feld__label', 'Wie erholt fühlst du dich?'));
  q.append(skala(s.qualitaet, (n) => { s.qualitaet = n; sichern(); }, { links: 'gerädert', rechts: 'top fit', label: 'Schlafqualität' }));
  kl.append(q);
  dauerZeigen();
  ziel.append(kl);

  // Gewicht & Befinden
  const kg = karte('Gewicht & Befinden', 'fortschritt');
  const ge = eingabe('text', tag.gewicht != null ? String(tag.gewicht).replace('.', ',') : '', { modus: 'decimal', platzhalter: 'z. B. 78,4' });
  ge.addEventListener('change', () => {
    const w = leseZahl(ge.value);
    tag.gewicht = w && w > 30 && w < 350 ? Math.round(w * 10) / 10 : null;
    Speicher.sichern();
    if (tag.gewicht) toast('Gewicht gespeichert');
  });
  kg.append(feld('Gewicht (kg) — morgens nüchtern', ge));
  const en = el('div', 'feld');
  en.append(el('div', 'feld__label', 'Energie heute'));
  en.append(skala(tag.energie, (n) => { tag.energie = n; Speicher.sichern(); }, { links: 'leer', rechts: 'voller Energie', label: 'Energie' }));
  kg.append(en);
  ziel.append(kg);

  // Gewohnheiten
  const kh = karte('Gewohnheiten', 'haken');
  gewohnheitsListe(kh, datum);
  ziel.append(kh);
}

function gewohnheitenVerwalten(ziel) {
  ziel.append(el('p', 'leise', 'Kleine tägliche Handlungen, die dich deinem Ziel näherbringen. Weniger ist mehr: 3–5 Gewohnheiten, die du wirklich schaffst.'));
  const k = karte(null);
  D().gewohnheiten.forEach((g, i) => {
    const z = el('div', 'zeile'); z.style.cursor = 'default';
    const t = el('div', 'zeile__text');
    const s = serie(g.id);
    // Quote der letzten 30 Tage
    let n = 0;
    for (let j = 0; j < 30; j++) if (gewohnheitErledigt(g.id, tageVerschieben(heuteText(), -j))) n++;
    t.append(el('div', 'zeile__titel', g.name), el('div', 'zeile__meta', `Serie ${s} ${s === 1 ? 'Tag' : 'Tage'} · ${Math.round(n / 30 * 100)} % der letzten 30 Tage`));
    const weg = el('button', 'ikon-knopf ikon-knopf--plain'); weg.innerHTML = ikon('muell');
    weg.setAttribute('aria-label', `${g.name} löschen`);
    weg.onclick = () => {
      if (!confirm(`„${g.name}" löschen?`)) return;
      D().gewohnheiten.splice(i, 1); Speicher.sichern(); neuZeichnen();
    };
    z.append(t, weg);
    k.append(z);
  });
  if (!D().gewohnheiten.length) k.append(el('p', 'leise', 'Noch keine Gewohnheiten.'));
  ziel.append(k);
  const neu = eingabe('text', '', { platzhalter: 'Neue Gewohnheit, z. B. 2 l Wasser trinken' });
  neu.setAttribute('aria-label', 'Neue Gewohnheit');
  const hinzu = () => {
    const name = neu.value.trim();
    if (!name) return;
    D().gewohnheiten.push({ id: 'g' + neueId(), name }); Speicher.sichern(); neuZeichnen();
  };
  neu.addEventListener('keydown', (e) => { if (e.key === 'Enter') hinzu(); });
  ziel.append(neu);
  const kb = knopf('Hinzufügen', 'knopf--zweit', hinzu, 'plus');
  kb.style.marginTop = '8px';
  ziel.append(kb);
  ziel.append(abschnitt('Vorschläge'));
  const vorschlaege = ['Eiweiß zu jeder Mahlzeit', '2 Liter Wasser getrunken', '10 Minuten Spaziergang nach dem Essen',
    'Supplements genommen', 'Vor 23 Uhr im Bett', 'Kein Alkohol', 'Mahlzeiten vorbereitet', '5 Minuten Atemübung'];
  const box = el('div', 'schnell');
  vorschlaege.filter((v) => !D().gewohnheiten.some((g) => g.name === v)).forEach((v) => {
    const c = el('button', 'chip', `+ ${v}`); c.type = 'button';
    c.onclick = () => { D().gewohnheiten.push({ id: 'g' + neueId(), name: v }); Speicher.sichern(); neuZeichnen(); };
    box.append(c);
  });
  ziel.append(box);
}

/** Kennzahlen der 7 Tage bis einschließlich bis. */
function wochenStatistik(bis = heuteText()) {
  const von = tageVerschieben(bis, -6);
  const tage = Array.from({ length: 7 }, (_, i) => tageVerschieben(von, i));
  const mittel = (liste) => liste.length ? liste.reduce((a, b) => a + b, 0) / liste.length : null;
  const essensTage = tage.filter((d) => (Speicher.tagLesen(d) || { essen: [] }).essen.length);
  const schritte = tage.map((d) => (Speicher.tagLesen(d) || {}).schritte).filter((x) => x);
  const schlaf = tage.map((d) => schlafDauer((Speicher.tagLesen(d) || {}).schlaf)).filter((x) => x);
  const quali = tage.map((d) => ((Speicher.tagLesen(d) || {}).schlaf || {}).qualitaet).filter((x) => x);
  const gew = D().gewohnheiten.length;
  let gewErledigt = 0;
  tage.forEach((d) => D().gewohnheiten.forEach((g) => { if (gewohnheitErledigt(g.id, d)) gewErledigt++; }));
  const reihe = gewichtsreihe();
  return {
    von, bis,
    workouts: D().workouts.filter((w) => w.datum >= von && w.datum <= bis),
    kcal: mittel(essensTage.map((d) => tagesSumme(d).kcal)),
    eiweiss: mittel(essensTage.map((d) => tagesSumme(d).e)),
    essensTage: essensTage.length,
    schritte: mittel(schritte), schritteTage: schritte.length,
    schlaf: mittel(schlaf), schlafQuali: mittel(quali),
    gewohnheiten: gew ? gewErledigt / (gew * 7) : null,
    gewicht: gewichtMittel(bis, reihe),
    gewichtVorwoche: gewichtMittel(tageVerschieben(bis, -7), reihe),
    letztesGewicht: reihe.filter((r) => r.datum <= bis).pop()
  };
}

function checkinText(c, st) {
  const d = D();
  const p = d.profil;
  const z = [];
  const coachingWoche = Math.floor(tageZwischen(p.start, st.bis) / 7) + 1;
  z.push(`📋 Wöchentlicher Check-in — ${p.name}`);
  z.push(`${datumKurz(st.von)}–${datumKurz(st.bis)}${datumAusText(st.bis).getFullYear()} · Coaching-Woche ${coachingWoche}`);
  z.push('');
  if (st.gewicht != null) {
    let g = `⚖️ Gewicht: Ø ${zahl(st.gewicht, 1)} kg`;
    if (st.gewichtVorwoche != null) {
      const diff = st.gewicht - st.gewichtVorwoche;
      g += ` (${diff > 0 ? '+' : diff < 0 ? '−' : '±'}${zahl(Math.abs(diff), 1)} kg zur Vorwoche)`;
    }
    g += ` · Start ${zahl(p.gewicht, 1)} kg`;
    z.push(g);
  } else z.push('⚖️ Gewicht: diese Woche nicht gewogen');
  if (c.taille) z.push(`📏 Taille: ${zahl(c.taille, 1)} cm`);
  z.push(`🏋️ Training: ${st.workouts.length} von ${p.tage} Einheiten${st.workouts.length ? ' (' + st.workouts.map((w) => w.name).join(', ') + ')' : ''}`);
  if (st.essensTage) {
    z.push(`🍽 Ernährung: Ø ${zahl(st.kcal)} kcal (Ziel ${zahl(d.ziele.kcal)}) · Ø ${zahl(st.eiweiss)} g Eiweiß (Ziel ${zahl(d.ziele.e)}) · ${st.essensTage}/7 Tage erfasst`);
  } else z.push('🍽 Ernährung: nicht erfasst');
  z.push(st.schritte ? `👣 Schritte: Ø ${zahl(st.schritte)} (Ziel ${zahl(p.schrittziel)}) · ${st.schritteTage}/7 Tage` : '👣 Schritte: nicht erfasst');
  z.push(st.schlaf ? `😴 Schlaf: Ø ${zahl(st.schlaf, 1)} Std.${st.schlafQuali ? ` · Erholung ${zahl(st.schlafQuali, 1)}/5` : ''}` : '😴 Schlaf: nicht erfasst');
  if (st.gewohnheiten != null) z.push(`✅ Gewohnheiten: ${Math.round(st.gewohnheiten * 100)} % erledigt`);
  z.push('');
  const b = c.bewertung;
  z.push(`Selbsteinschätzung (1–5): Energie ${b.energie || '–'} · Schlaf ${b.schlaf || '–'} · Stress ${b.stress || '–'} · Hunger ${b.hunger || '–'} · Motivation ${b.motivation || '–'}`);
  z.push(`Plan eingehalten: Training ${c.treueTraining}% · Ernährung ${c.treueErnaehrung}%`);
  if (c.erfolge) z.push('', `🏆 Erfolge:\n${c.erfolge}`);
  if (c.probleme) z.push('', `🧱 Herausforderungen:\n${c.probleme}`);
  if (c.fragen) z.push('', `❓ Fragen an dich:\n${c.fragen}`);
  return z.join('\n');
}

function checkinWoche(ziel) {
  const d = D();
  const st = wochenStatistik();
  const letzter = letzterCheckin();
  const heuteErledigt = letzter && letzter.datum === heuteText();

  const held = el('div', 'held');
  held.append(el('div', 'held__label', 'Wöchentlicher Check-in'),
    el('div', 'held__titel', heuteErledigt ? 'Diese Woche erledigt ✓' : checkinFaellig() ? 'Zeit für dein Update' : 'Wochen-Check-in'),
    el('div', 'held__text', heuteErledigt ? 'Du kannst ihn unten erneut senden oder anpassen.'
      : `Fällig jeden ${WOCHENTAGE[d.coach.checkinTag]}. Die Zahlen der Woche trägt die App selbst ein — du ergänzt nur, was nur du weißt.`));
  ziel.append(held);

  // Automatische Zahlen
  const kz = karte('Deine Woche in Zahlen', 'fortschritt', `${datumKurz(st.von)}–${datumKurz(st.bis)}`);
  const w = el('div', 'werte');
  w.append(
    wertKachel('Gewicht Ø', st.gewicht != null ? zahl(st.gewicht, 1) : '–', 'kg',
      st.gewicht != null && st.gewichtVorwoche != null ? `${st.gewicht - st.gewichtVorwoche > 0 ? '+' : ''}${zahl(st.gewicht - st.gewichtVorwoche, 1)} kg zur Vorwoche` : null),
    wertKachel('Training', `${st.workouts.length}/${d.profil.tage}`, 'Einh.'),
    wertKachel('Kalorien Ø', st.kcal != null ? zahl(st.kcal) : '–', 'kcal', st.essensTage ? `${st.essensTage}/7 Tage erfasst` : 'nicht erfasst'),
    wertKachel('Schritte Ø', st.schritte != null ? zahl(st.schritte) : '–'),
    wertKachel('Schlaf Ø', st.schlaf != null ? zahl(st.schlaf, 1) : '–', 'Std.'),
    wertKachel('Gewohnheiten', st.gewohnheiten != null ? Math.round(st.gewohnheiten * 100) : '–', '%'));
  kz.append(w);
  ziel.append(kz);

  // Fragebogen — Entwurf überlebt das Wechseln der Ansicht.
  const c = App.checkinEntwurf || (App.checkinEntwurf = {
    taille: null, bewertung: {}, treueTraining: 80, treueErnaehrung: 80, erfolge: '', probleme: '', fragen: ''
  });
  const kf = karte('Deine Einschätzung', 'checkin');
  const ta = eingabe('text', c.taille ? String(c.taille).replace('.', ',') : '', { modus: 'decimal', platzhalter: 'optional' });
  ta.oninput = () => { c.taille = leseZahl(ta.value); };
  kf.append(feld('Taillenumfang (cm), auf Nabelhöhe', ta));
  [['energie', 'Energie', 'sehr niedrig', 'sehr hoch'], ['schlaf', 'Schlaf', 'schlecht', 'sehr gut'],
   ['stress', 'Stress', 'entspannt', 'sehr gestresst'], ['hunger', 'Hunger', 'kaum', 'ständig'],
   ['motivation', 'Motivation', 'niedrig', 'hoch']].forEach(([id, name, l, r]) => {
    const f = el('div', 'feld');
    f.append(el('div', 'feld__label', name));
    f.append(skala(c.bewertung[id] || null, (n) => { c.bewertung[id] = n; }, { links: l, rechts: r, label: name }));
    kf.append(f);
  });
  [['treueTraining', 'Training nach Plan'], ['treueErnaehrung', 'Ernährung nach Plan']].forEach(([id, name]) => {
    const f = el('div', 'feld');
    const lab = el('div', 'feld__label', `${name}: ${c[id]} %`);
    const r = el('input'); r.type = 'range'; r.min = 0; r.max = 100; r.step = 10; r.value = c[id];
    r.style.cssText = 'width:100%;accent-color:var(--accent)';
    r.setAttribute('aria-label', name);
    r.oninput = () => { c[id] = Number(r.value); lab.textContent = `${name}: ${c[id]} %`; };
    f.append(lab, r);
    kf.append(f);
  });
  [['erfolge', 'Was lief gut? Deine Erfolge der Woche'], ['probleme', 'Was war schwierig?'], ['fragen', 'Fragen an deinen Coach']].forEach(([id, name]) => {
    const t = el('textarea', 'eingabe'); t.value = c[id];
    t.oninput = () => { c[id] = t.value; };
    kf.append(feld(name, t));
  });
  ziel.append(kf);

  ziel.append(knopf('Vorschau & senden', null, () => checkinSendenBlatt(c, st), 'senden'));

  if (d.checkins.length) {
    ziel.append(abschnitt('Bisherige Check-ins'));
    const kv = karte(null);
    [...d.checkins].reverse().forEach((ci) => {
      const z = el('button', 'zeile'); z.type = 'button';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', datumLang(ci.datum)),
               el('div', 'zeile__meta', ci.gewicht != null ? `Ø ${zahl(ci.gewicht, 1)} kg · ${ci.workouts} Einheiten` : `${ci.workouts} Einheiten`));
      const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
      z.append(t, pf);
      z.onclick = () => blattOeffnen(`Check-in ${datumKurz(ci.datum)}`, (inhalt) => {
        inhalt.append(el('div', 'vorschau-text', ci.text));
        const k = knopf('Erneut teilen', 'knopf--zweit', () => teilen(ci.text, 'Check-in'), 'senden');
        k.style.marginTop = '14px';
        inhalt.append(k);
      });
      kv.append(z);
    });
    ziel.append(kv);
  }
}

function checkinSendenBlatt(c, st) {
  const d = D();
  const text = checkinText(c, st);
  blattOeffnen('Check-in senden', (inhalt, schliessen) => {
    inhalt.append(el('p', 'leise', 'So kommt dein Check-in bei deinem Coach an. Mit dem Senden wird er hier gespeichert.'));
    inhalt.append(el('div', 'vorschau-text', text));
    const speichern = () => {
      const heute = heuteText();
      d.checkins = d.checkins.filter((x) => x.datum !== heute);
      d.checkins.push({ datum: heute, text, gewicht: st.gewicht, workouts: st.workouts.length, taille: c.taille, bewertung: c.bewertung });
      if (c.taille) {
        const m = d.messungen.find((x) => x.datum === heute);
        if (m) m.taille = c.taille; else d.messungen.push({ datum: heute, taille: c.taille });
      }
      Speicher.sichern();
      App.checkinEntwurf = null;
    };
    const aktionen = el('div');
    aktionen.style.marginTop = '16px';
    if (d.coach.whatsapp) {
      aktionen.append(knopf('Per WhatsApp senden', null, () => {
        speichern();
        window.open(`https://wa.me/${d.coach.whatsapp}?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
        schliessen();
      }, 'senden'));
    }
    if (d.coach.email) {
      aktionen.append(knopf('Per E-Mail senden', 'knopf--zweit', () => {
        speichern();
        const betreff = `Check-in ${d.profil.name} · ${datumKurz(st.von)}–${datumKurz(st.bis)}`;
        location.href = `mailto:${d.coach.email}?subject=${encodeURIComponent(betreff)}&body=${encodeURIComponent(text)}`;
        schliessen();
      }));
    }
    if (!d.coach.whatsapp && !d.coach.email) {
      const h = el('div', 'hinweis');
      h.append(el('p', null, 'Hinterlege WhatsApp oder E-Mail deines Coachs unter Einstellungen — dann geht der Check-in mit einem Tipp raus. Bis dahin: teilen oder kopieren.'));
      aktionen.append(h);
      aktionen.append(knopf('Teilen', null, () => { speichern(); teilen(text, 'Check-in'); schliessen(); }, 'senden'));
    }
    aktionen.append(knopf('Text kopieren', 'knopf--zweit', () => { speichern(); kopieren(text); schliessen(); }));
    inhalt.append(aktionen);
    const extra = el('div');
    extra.style.marginTop = '20px';
    extra.append(el('p', 'leise', 'Soll dein Coach auch Diagramme, Trainings und Fotos sehen?'),
                 knopf('Fortschritt an Coach senden', 'knopf--zweit', fortschrittSendenBlatt, 'fortschritt'));
    inhalt.append(extra);
  }, { beimSchliessen: neuZeichnen });
}

function gewichtBlatt(datum) {
  blattOeffnen('Gewicht eintragen', (inhalt, schliessen, blatt) => {
    const t = Speicher.tag(datum);
    const vorschlag = t.gewicht != null ? t.gewicht : aktuellesGewicht();
    const e = eingabe('text', vorschlag != null ? String(vorschlag).replace('.', ',') : '', { modus: 'decimal' });
    e.className = 'eingabe eingabe--gross';
    e.setAttribute('aria-label', 'Gewicht in kg');
    inhalt.append(el('p', 'leise', `${datumLang(datum)} · am besten morgens nach dem Toilettengang, vor dem Frühstück.`), e);
    inhalt.append(el('p', 'fusstext', 'Das Gewicht schwankt täglich um 0,5–2 kg durch Wasser, Salz und Verdauung. Aussagekräftig ist der 7-Tage-Durchschnitt — den zeigt dir die App unter Fortschritt.'));
    setTimeout(() => e.focus(), 300);
    blattFuss(blatt, knopf('Speichern', null, () => {
      const w = leseZahl(e.value);
      if (!w || w < 30 || w > 350) { toast('Bitte ein gültiges Gewicht eingeben'); return; }
      t.gewicht = Math.round(w * 10) / 10;
      Speicher.sichern(); schliessen(); toast('Gewicht gespeichert');
    }));
  }, { beimSchliessen: neuZeichnen });
}

/* --- Ansicht: Fortschritt ----------------------------------------------- */

function ansichtFortschritt(ziel) {
  const d = D();
  const p = d.profil;
  const heute = heuteText();
  const reihe = gewichtsreihe();
  const mittel = gewichtMittel(heute, reihe);
  const start = p.gewicht;

  // Kennzahlen
  const werte = el('div', 'werte');
  werte.style.marginBottom = '14px';
  const diff = mittel != null ? mittel - start : null;
  const gutRichtung = diff != null && ((p.ziel === 'fett' && diff < 0) || (p.ziel === 'muskel' && diff > 0));
  werte.append(
    wertKachel('Gewicht (Ø 7 Tage)', mittel != null ? zahl(mittel, 1) : '–', 'kg',
      diff != null ? `${diff > 0 ? '+' : diff < 0 ? '−' : '±'}${zahl(Math.abs(diff), 1)} kg seit Start` : null, gutRichtung),
    wertKachel('Dabei seit', zahl(tageZwischen(p.start, heute) + 1), 'Tagen', `seit ${datumKurz(p.start)}${datumAusText(p.start).getFullYear()}`),
    wertKachel('Trainings', zahl(d.workouts.length), null, `${workoutsInWoche().length} diese Woche`),
    wertKachel('Check-ins', zahl(d.checkins.length), null, letzterCheckin() ? `zuletzt ${datumKurz(letzterCheckin().datum)}` : 'noch keiner'));
  ziel.append(werte);
  const senden = knopf('Fortschritt an Coach senden', 'knopf--zweit', fortschrittSendenBlatt, 'senden');
  senden.style.marginBottom = '14px';
  ziel.append(senden);

  // Gewicht
  const kg = karte('Gewicht', 'fortschritt');
  const filter = el('div', 'filter');
  [[30, '4 Wochen'], [90, '3 Monate'], [365, '1 Jahr'], [0, 'Alles']].forEach(([tage, name]) => {
    const c = el('button', 'chip', name); c.type = 'button';
    c.setAttribute('aria-pressed', String(App.gewichtZeitraum === tage));
    c.onclick = () => { App.gewichtZeitraum = tage; neuZeichnen(); };
    filter.append(c);
  });
  kg.append(filter);
  const ab = App.gewichtZeitraum ? tageVerschieben(heute, -App.gewichtZeitraum) : '0000';
  const sichtbar = reihe.filter((r) => r.datum >= ab);
  if (sichtbar.length >= 2) {
    const glatt = sichtbar.map((r) => ({ datum: r.datum, wert: gewichtMittel(r.datum, reihe) }));
    kg.append(liniendiagramm(sichtbar, { glatt, label: `Gewichtsverlauf, ${sichtbar.length} Messungen` }));
    const leg = el('div', 'legende');
    leg.innerHTML = '<span><i style="background:var(--accent-ink)"></i>7-Tage-Durchschnitt</span><span><i style="background:var(--ink-soft);opacity:.55"></i>Tageswerte</span>';
    kg.append(leg);
  } else {
    kg.append(el('p', 'leise', 'Ab zwei Messungen siehst du hier deinen Verlauf. Am besten wiegst du dich 3–7× pro Woche.'));
  }
  const gk = knopf('Gewicht eintragen', 'knopf--zweit knopf--klein', () => gewichtBlatt(heute), 'plus');
  gk.style.marginTop = '12px';
  kg.append(gk);
  ziel.append(kg);

  // Schritte & Schlaf der letzten 7 Tage
  const tage7 = Array.from({ length: 7 }, (_, i) => tageVerschieben(heute, i - 6));
  const ks = karte('Schritte · 7 Tage', 'schritte');
  ks.append(saeulendiagramm(tage7.map((t) => ({ label: WT_KURZ[datumAusText(t).getDay()], wert: (Speicher.tagLesen(t) || {}).schritte || 0 })),
    { ziel: p.schrittziel, label: 'Schritte der letzten 7 Tage', farbe: 'var(--c-schritte)' }));
  ziel.append(ks);
  const kl = karte('Schlaf · 7 Tage', 'schlaf');
  kl.append(saeulendiagramm(tage7.map((t) => ({ label: WT_KURZ[datumAusText(t).getDay()], wert: schlafDauer((Speicher.tagLesen(t) || {}).schlaf) || 0 })),
    { ziel: p.schlafziel, label: 'Schlafstunden der letzten 7 Tage', farbe: 'var(--c-schlaf)', stellen: 1 }));
  ziel.append(kl);

  // Trainingsvolumen pro Woche
  const kv = karte('Trainingsvolumen · 8 Wochen', 'training');
  const wochen = Array.from({ length: 8 }, (_, i) => wochenstart(tageVerschieben(heute, (i - 7) * 7)));
  kv.append(saeulendiagramm(wochen.map((w) => ({
    label: datumKurz(w),
    wert: Math.round(D().workouts.filter((x) => x.datum >= w && x.datum <= tageVerschieben(w, 6)).reduce((a, x) => a + volumen(x), 0))
  })), { label: 'Trainingsvolumen in kg pro Woche' }));
  kv.append(el('div', 'fusstext', 'Volumen = Gewicht × Wiederholungen aller Sätze. Steigt es über Wochen, wirst du stärker.'));
  ziel.append(kv);

  // Rekorde
  const rekorde = new Map();
  d.workouts.forEach((w) => w.uebungen.forEach((u) => {
    if (!uebung(u.uid).gewicht) return;
    u.saetze.forEach((s) => {
      if (!s.fertig || !s.kg) return;
      const wert = e1rm(s.kg, s.wdh);
      const alt = rekorde.get(u.uid);
      if (!alt || wert > alt.wert) rekorde.set(u.uid, { wert, kg: s.kg, wdh: s.wdh, datum: w.datum });
    });
  }));
  const kr = karte('Bestwerte', 'pokal');
  if (!rekorde.size) kr.append(el('p', 'leise', 'Nach deinen ersten Trainings stehen hier deine Bestleistungen.'));
  [...rekorde.entries()].sort((a, b) => b[1].wert - a[1].wert).slice(0, 10).forEach(([uid, r]) => {
    const z = el('button', 'zeile'); z.type = 'button';
    const t = el('div', 'zeile__text');
    t.append(el('div', 'zeile__titel', uebung(uid).name), el('div', 'zeile__meta', `${zahl(r.kg, r.kg % 1 ? 1 : 0)} kg × ${r.wdh} · ${datumKurz(r.datum)}`));
    z.append(t, el('div', 'zeile__rechts', `${zahl(r.wert, 1)} kg`));
    z.onclick = () => uebungBlatt(uid);
    kr.append(z);
  });
  ziel.append(kr);

  // Umfänge
  const ku = karte('Körpermaße', 'liste');
  umfaengeZeigen(ku);
  ziel.append(ku);

  // Fotos
  const kf = karte('Fortschrittsfotos', 'kamera');
  ziel.append(kf);
  fotosZeigen(kf);
}

function umfaengeZeigen(k) {
  const m = [...D().messungen].sort((a, b) => a.datum.localeCompare(b.datum));
  if (!m.length) {
    k.append(el('p', 'leise', 'Miss alle 2–4 Wochen nach, morgens und immer an derselben Stelle. Oft zeigt das Maßband Fortschritt, bevor die Waage es tut.'));
  } else {
    MASSE.forEach(([id, name]) => {
      const mit = m.filter((x) => x[id] != null);
      if (!mit.length) return;
      const erst = mit[0][id], letzt = mit[mit.length - 1][id];
      const z = el('div', 'zeile'); z.style.cursor = 'default';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', name),
               el('div', 'zeile__meta', mit.length > 1 ? `Start ${zahl(erst, 1)} cm · ${letzt - erst > 0 ? '+' : letzt - erst < 0 ? '−' : '±'}${zahl(Math.abs(letzt - erst), 1)} cm` : `gemessen ${datumKurz(mit[0].datum)}`));
      z.append(t, el('div', 'zeile__rechts', `${zahl(letzt, 1)} cm`));
      k.append(z);
    });
  }
  const b = knopf('Maße eintragen', 'knopf--zweit knopf--klein', messungBlatt, 'plus');
  b.style.marginTop = '12px';
  k.append(b);
}

function messungBlatt() {
  blattOeffnen('Körpermaße', (inhalt, schliessen, blatt) => {
    const heute = heuteText();
    const vorhanden = D().messungen.find((x) => x.datum === heute) || {};
    inhalt.append(el('p', 'leise', 'Alle Werte in Zentimetern. Leere Felder bleiben leer. Taille auf Nabelhöhe, Hüfte an der breitesten Stelle, Arm und Bein rechts an der dicksten Stelle.'));
    const felder = {};
    MASSE.forEach(([id, name]) => {
      felder[id] = eingabe('text', vorhanden[id] != null ? String(vorhanden[id]).replace('.', ',') : '', { modus: 'decimal' });
      inhalt.append(feld(name, felder[id]));
    });
    blattFuss(blatt, knopf('Speichern', null, () => {
      const eintrag = { datum: heute };
      MASSE.forEach(([id]) => { const v = leseZahl(felder[id].value); if (v) eintrag[id] = v; });
      D().messungen = D().messungen.filter((x) => x.datum !== heute);
      if (Object.keys(eintrag).length > 1) D().messungen.push(eintrag);
      Speicher.sichern(); schliessen(); toast('Maße gespeichert');
    }));
  }, { beimSchliessen: neuZeichnen });
}

const fotoUrls = [];

function fotoUrl(blob) {
  const u = URL.createObjectURL(blob);
  fotoUrls.push(u);
  return u;
}

async function fotosZeigen(k) {
  const liste = await Fotos.alle();
  const nachDatum = new Map();
  liste.forEach((f) => { if (!nachDatum.has(f.datum)) nachDatum.set(f.datum, []); nachDatum.get(f.datum).push(f); });
  const daten = [...nachDatum.keys()].sort();

  if (daten.length >= 2) {
    const erst = nachDatum.get(daten[0]), letzt = nachDatum.get(daten[daten.length - 1]);
    const pose = POSEN.map(([id]) => id).find((id) => erst.some((f) => f.pose === id) && letzt.some((f) => f.pose === id));
    if (pose) {
      const v = el('div', 'vergleich');
      [[erst, daten[0]], [letzt, daten[daten.length - 1]]].forEach(([fs, datum]) => {
        const fig = el('figure');
        const img = el('img'); img.alt = `${pose} am ${datumKurz(datum)}`;
        img.src = fotoUrl(fs.find((f) => f.pose === pose).blob);
        fig.append(img, el('figcaption', null, datumMittel(datum)));
        v.append(fig);
      });
      k.append(el('div', 'feld__label', 'Vorher – Nachher'), v, el('hr', 'trenner'));
    }
  }

  [...daten].reverse().forEach((datum) => {
    k.append(el('div', 'feld__label', datumLang(datum)));
    const g = el('div', 'fotos');
    g.style.marginBottom = '12px';
    nachDatum.get(datum).forEach((f) => {
      const b = el('button', 'foto'); b.type = 'button';
      const img = el('img'); img.alt = `${f.pose}, ${datumKurz(datum)}`; img.loading = 'lazy';
      img.src = fotoUrl(f.blob);
      b.append(img, el('span', 'foto__label', (POSEN.find((x) => x[0] === f.pose) || [0, f.pose])[1]));
      b.onclick = () => fotoBlatt(f);
      g.append(b);
    });
    k.append(g);
  });

  if (!daten.length) {
    k.append(el('p', 'leise', 'Fotos alle 2–4 Wochen machen: gleiches Licht, gleiche Kleidung, gleiche Uhrzeit. Sie bleiben nur auf diesem Gerät.'));
  }
  const b = knopf('Fotos aufnehmen', 'knopf--zweit knopf--klein', fotoAufnahmeBlatt, 'kamera');
  b.style.marginTop = '4px';
  k.append(b);
}

function fotoBlatt(f) {
  blattOeffnen(`${(POSEN.find((x) => x[0] === f.pose) || [0, 'Foto'])[1]} · ${datumKurz(f.datum)}`, (inhalt, schliessen) => {
    const img = el('img'); img.src = fotoUrl(f.blob); img.alt = '';
    img.style.cssText = 'width:100%;border-radius:var(--radius);display:block;margin-bottom:14px';
    inhalt.append(img, knopf('Foto löschen', 'knopf--gefahr', async () => {
      if (!confirm('Foto endgültig löschen?')) return;
      await Fotos.loeschen(f.id); schliessen();
    }));
  }, { beimSchliessen: neuZeichnen });
}

function fotoAufnahmeBlatt() {
  blattOeffnen('Fortschrittsfotos', (inhalt, schliessen) => {
    inhalt.append(el('p', 'leise', 'Wähle eine Ansicht und nimm das Foto auf oder wähle eins aus der Galerie. Die Fotos werden verkleinert und nur auf diesem Gerät gespeichert.'));
    const g = el('div', 'fotos');
    POSEN.forEach(([id, name]) => {
      const label = el('label', 'foto foto--neu');
      label.innerHTML = ikon('kamera');
      label.append(document.createTextNode(name));
      const input = el('input'); input.type = 'file'; input.accept = 'image/*'; input.className = 'versteckt';
      input.onchange = async () => {
        const datei = input.files && input.files[0];
        if (!datei) return;
        try {
          const blob = await fotoVerkleinern(datei);
          await Fotos.speichern({ id: neueId(), datum: heuteText(), pose: id, blob });
          label.replaceChildren();
          const img = el('img'); img.src = fotoUrl(blob); img.alt = name;
          label.append(img, el('span', 'foto__label', `${name} ✓`));
          toast(`${name} gespeichert`);
        } catch (e) {
          console.error(e);
          toast('Foto konnte nicht gespeichert werden');
        }
      };
      label.append(input);
      g.append(label);
    });
    inhalt.append(g);
    const fertig = knopf('Fertig', null, schliessen);
    fertig.style.marginTop = '16px';
    inhalt.append(fertig);
  }, { beimSchliessen: neuZeichnen });
}

/* --- Einstellungen ------------------------------------------------------ */

function einstellungenBlatt() {
  blattOeffnen('Einstellungen', (inhalt, schliessen) => {
    const d = D();
    const p = d.profil;

    inhalt.append(abschnitt('Profil & Ziel'));
    const kp = karte(null);
    const name = eingabe('text', p.name, { beiAenderung: (v) => { p.name = v.trim() || p.name; Speicher.sichern(); } });
    kp.append(feld('Vorname', name));
    const zf = el('div', 'feld');
    zf.append(el('div', 'feld__label', 'Ziel'));
    zf.append(wahl(Object.entries(ZIELE).map(([id, z]) => ({ id, name: z.name })), p.ziel, (id) => { p.ziel = id; neuBerechnen(); }, 3));
    kp.append(zf);
    const reihe = el('div', 'reihe');
    const alter = eingabe('number', p.alter, { modus: 'numeric', beiAenderung: (v) => { p.alter = leseZahl(v) || p.alter; neuBerechnen(); } });
    const groesse = eingabe('number', p.groesse, { modus: 'numeric', beiAenderung: (v) => { p.groesse = leseZahl(v) || p.groesse; neuBerechnen(); } });
    reihe.append(feld('Alter', alter), feld('Größe (cm)', groesse));
    kp.append(reihe);
    const af = el('div', 'feld');
    af.append(el('div', 'feld__label', 'Aktivität im Alltag'));
    af.append(wahl(AKTIVITAET.map((a) => ({ id: a.id, name: a.name })), p.aktivitaet, (id) => { p.aktivitaet = id; neuBerechnen(); }, 2));
    kp.append(af);
    inhalt.append(kp);

    inhalt.append(abschnitt('Tagesziele'));
    const kz = karte(null);
    const zielInfo = el('p', 'leise');
    const makroFelder = {};
    const zeigen = () => {
      zielInfo.textContent = d.ziele.manuell
        ? 'Vom Coach festgelegt. „Automatisch berechnen" stellt die Formel wieder her.'
        : `Automatisch berechnet aus Profil und aktuellem Gewicht (${zahl(aktuellesGewicht(), 1)} kg).`;
      ['kcal', 'e', 'kh', 'f'].forEach((k) => { makroFelder[k].value = d.ziele[k]; });
    };
    function neuBerechnen() {
      if (!d.ziele.manuell) d.ziele = zieleBerechnen({ ...p, gewicht: aktuellesGewicht() });
      Speicher.sichern();
      zeigen();
    }
    const r1 = el('div', 'reihe');
    const r2 = el('div', 'reihe');
    [['kcal', 'Kalorien', r1], ['e', 'Eiweiß (g)', r1], ['kh', 'Kohlenhydrate (g)', r2], ['f', 'Fett (g)', r2]].forEach(([k, label, r]) => {
      makroFelder[k] = eingabe('number', d.ziele[k], { modus: 'numeric', beiAenderung: (v) => {
        const n = leseZahl(v);
        if (n == null) return;
        d.ziele[k] = Math.round(n); d.ziele.manuell = true; Speicher.sichern(); zeigen();
      } });
      r.append(feld(label, makroFelder[k]));
    });
    kz.append(zielInfo, r1, r2);
    kz.append(linkKnopf('Automatisch berechnen', () => { d.ziele.manuell = false; neuBerechnen(); toast('Ziele neu berechnet'); }));
    const r3 = el('div', 'reihe');
    r3.style.marginTop = '12px';
    r3.append(
      feld('Schritte', eingabe('number', p.schrittziel, { modus: 'numeric', beiAenderung: (v) => { p.schrittziel = leseZahl(v) || p.schrittziel; Speicher.sichern(); } })),
      feld('Schlaf (Std.)', eingabe('text', String(p.schlafziel).replace('.', ','), { modus: 'decimal', beiAenderung: (v) => { p.schlafziel = leseZahl(v) || p.schlafziel; Speicher.sichern(); } })),
      feld('Wasser (Gläser)', eingabe('number', p.wasserziel || 8, { modus: 'numeric', beiAenderung: (v) => { p.wasserziel = leseZahl(v) || 8; Speicher.sichern(); } })));
    kz.append(r3);
    zeigen();
    inhalt.append(kz);

    inhalt.append(abschnitt('Dein Coach'));
    const kc = karte(null);
    // Bei jeder Eingabe speichern, nicht erst beim Verlassen des Felds — sonst
    // geht die Adresse verloren, wenn jemand das Blatt direkt schließt.
    const wa = eingabe('tel', d.coach.whatsapp, { platzhalter: 'z. B. 0170 1234567' });
    wa.addEventListener('input', () => { d.coach.whatsapp = whatsappNummer(wa.value); Speicher.sichern(); });
    kc.append(feld('WhatsApp-Nummer', wa, 'Wird automatisch ins internationale Format umgerechnet.'));
    const em = eingabe('email', d.coach.email, { platzhalter: 'coach@beispiel.de' });
    em.autocomplete = 'email';
    em.addEventListener('input', () => {
      const wert = em.value.trim();
      d.coach.email = wert.includes('@') ? wert : '';
      Speicher.sichern();
    });
    kc.append(feld('E-Mail', em));
    const ct = el('select', 'eingabe');
    [1, 2, 3, 4, 5, 6, 0].forEach((i) => { const o = el('option', null, WOCHENTAGE[i]); o.value = i; if (Number(d.coach.checkinTag) === i) o.selected = true; ct.append(o); });
    ct.onchange = () => { d.coach.checkinTag = Number(ct.value); Speicher.sichern(); };
    kc.append(feld('Check-in-Tag', ct));
    inhalt.append(kc);

    inhalt.append(abschnitt('Darstellung'));
    const modus = el('div', 'modus');
    [['hell', 'Hell', 'sonne'], ['dunkel', 'Dunkel', 'mond'], ['system', 'System', 'system']].forEach(([id, name, ik]) => {
      const b = el('button'); b.type = 'button';
      b.innerHTML = ikon(ik); b.append(document.createTextNode(name));
      b.setAttribute('aria-pressed', String(Modus.gewaehlt() === id));
      b.onclick = () => { Modus.setzen(id); modus.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); };
      modus.append(b);
    });
    inhalt.append(modus);

    inhalt.append(abschnitt('Deine Daten'));
    const h = el('div', 'hinweis');
    h.append(el('div', 'hinweis__titel', 'Alles bleibt auf diesem Gerät'));
    h.append(el('p', null, 'Kein Konto, kein Server. Nur was du im Check-in selbst abschickst, erreicht deinen Coach. Geht das Gerät verloren oder löschst du die Browserdaten, sind die Einträge weg — sichere sie deshalb regelmäßig.'));
    inhalt.append(h);
    const mitFotos = el('label');
    mitFotos.style.cssText = 'display:flex;gap:8px;align-items:center;font-size:14px;margin-bottom:10px';
    const cb = el('input'); cb.type = 'checkbox';
    mitFotos.append(cb, document.createTextNode('Fotos in die Sicherung aufnehmen (größere Datei)'));
    inhalt.append(mitFotos);
    inhalt.append(knopf('Sicherung exportieren', 'knopf--zweit', () => exportieren(cb.checked)));
    const datei = el('input'); datei.type = 'file'; datei.accept = 'application/json,.json'; datei.className = 'versteckt';
    datei.onchange = () => datei.files[0] && importieren(datei.files[0], schliessen);
    inhalt.append(datei, knopf('Sicherung einlesen', 'knopf--zweit', () => datei.click()));

    inhalt.append(abschnitt('Hinweis'));
    inhalt.append(el('p', 'leise', 'Diese App ersetzt keine ärztliche oder ernährungstherapeutische Beratung. Kalorien- und Makroziele sind Schätzungen auf Basis anerkannter Formeln. Bei Vorerkrankungen, Schmerzen, Essstörungen, in der Schwangerschaft oder bei Medikamenteneinnahme sprich bitte vorher mit deiner Ärztin oder deinem Arzt. Brich eine Übung bei Schmerzen sofort ab.'));

    inhalt.append(abschnitt('Rechtliches'));
    const kr = karte(null);
    [['recht/impressum.html', 'Impressum'], ['recht/datenschutz.html', 'Datenschutzerklärung'],
     ['recht/agb.html', 'Nutzungsbedingungen (AGB)']].forEach(([href, name]) => {
      const a = el('a', 'zeile');
      a.href = href;
      a.style.textDecoration = 'none';
      const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
      a.append(el('div', 'zeile__text', name), pf);
      kr.append(a);
    });
    inhalt.append(kr);

    const reset = knopf('Alle Daten löschen', 'knopf--gefahr', async () => {
      if (!confirm('Wirklich alle Daten auf diesem Gerät löschen? Das lässt sich nicht rückgängig machen.')) return;
      Speicher.zuruecksetzen();
      await Fotos.leeren();
      schliessen();
      neuZeichnen();
    });
    reset.style.marginTop = '20px';
    inhalt.append(reset);
    inhalt.append(el('p', 'fusstext mitte', 'Coaching · Version 1.1'));
  }, { beimSchliessen: neuZeichnen });
}

async function exportieren(mitFotos) {
  const paket = { app: 'coaching', version: 1, exportiert: new Date().toISOString(), daten: D() };
  if (mitFotos) {
    const liste = await Fotos.alle();
    paket.fotos = await Promise.all(liste.map(async (f) => ({ id: f.id, datum: f.datum, pose: f.pose, bild: await blobZuDataUrl(f.blob) })));
  }
  const blob = new Blob([JSON.stringify(paket)], { type: 'application/json' });
  const a = el('a');
  a.href = URL.createObjectURL(blob);
  a.download = `coaching-sicherung-${heuteText()}.json`;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  toast('Sicherung erstellt');
}

async function importieren(datei, schliessen) {
  try {
    const paket = JSON.parse(await datei.text());
    if (paket.app !== 'coaching' || !paket.daten || !paket.daten.profil) throw new Error('Keine Coaching-Sicherung');
    if (!confirm('Die Sicherung ersetzt alle Daten auf diesem Gerät. Fortfahren?')) return;
    Speicher.daten = Object.assign(Speicher.leer(), paket.daten);
    Speicher.sichern();
    if (paket.fotos) {
      await Fotos.leeren();
      for (const f of paket.fotos) {
        const blob = await (await fetch(f.bild)).blob();
        await Fotos.speichern({ id: f.id, datum: f.datum, pose: f.pose, blob });
      }
    }
    schliessen();
    toast('Sicherung eingelesen');
  } catch (e) {
    console.error(e);
    alert('Die Datei konnte nicht gelesen werden. Ist es eine Sicherung dieser App?');
  }
}

/* --- Fortschritt an den Coach ------------------------------------------- */
/** Alles, was der Coach zur Auswertung braucht — ohne Einkaufsliste,
 *  „zuletzt gegessen“ und ein gerade laufendes Training. */
async function fortschrittsBericht(mitFotos) {
  const d = D();
  const bericht = {
    app: 'coaching-bericht', version: 1, erstellt: new Date().toISOString(),
    profil: d.profil, ziele: d.ziele, plan: d.plan, workouts: d.workouts, tage: d.tage,
    messungen: d.messungen, checkins: d.checkins, gewohnheiten: d.gewohnheiten
  };
  if (mitFotos) {
    // Kleiner als im Gerät gespeichert, damit die Datei per WhatsApp durchgeht.
    const liste = await Fotos.alle();
    bericht.fotos = [];
    for (const f of liste) {
      const klein = await fotoVerkleinern(f.blob, 600).catch(() => f.blob);
      bericht.fotos.push({ id: f.id, datum: f.datum, pose: f.pose, bild: await blobZuDataUrl(klein) });
    }
  }
  return bericht;
}

async function fortschrittDatei(mitFotos) {
  const bericht = await fortschrittsBericht(mitFotos);
  const vorname = (D().profil.name || 'klient').toLowerCase().replace(/[^a-z0-9äöüß]+/g, '-');
  const name = `fortschritt-${vorname}-${heuteText()}.json`;
  return new File([JSON.stringify(bericht)], name, { type: 'application/json' });
}

function dateiLaden(datei) {
  const a = el('a');
  a.href = URL.createObjectURL(datei);
  a.download = datei.name;
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

const kannDateienTeilen = (datei) => !!(navigator.canShare && navigator.canShare({ files: [datei] }));

/** Muss direkt aus dem Tipp heraus laufen: Safari öffnet das Teilen-Menü
 *  nur innerhalb der Nutzeraktion. Deshalb liegt die Datei schon bereit. */
function dateiTeilen(datei) {
  if (kannDateienTeilen(datei)) {
    return navigator.share({ files: [datei], title: 'Mein Fortschritt' })
      .then(() => true)
      .catch((e) => { if (e.name !== 'AbortError') toast('Teilen nicht möglich'); return false; });
  }
  dateiLaden(datei);
  return Promise.resolve(true);
}

function fortschrittSendenBlatt() {
  const email = D().coach.email;
  blattOeffnen('Fortschritt an Coach', (inhalt, schliessen, blatt) => {
    inhalt.append(el('p', 'leise', 'Damit dein Coach deine Diagramme, Trainings und Rekorde sehen kann, schickst du ihm eine Fortschrittsdatei. Er öffnet sie in seiner Coach-Ansicht.'));
    const h = el('div', 'hinweis');
    h.append(el('div', 'hinweis__titel', 'Was drinsteht'));
    h.append(el('p', null, 'Profil und Ziele, Trainings, Gewicht, Ernährung, Schritte, Schlaf, Gewohnheiten, Körpermaße und deine Check-ins — auf Wunsch auch deine Fortschrittsfotos. Schick die Datei nur an deinen Coach.'));
    inhalt.append(h);
    const label = el('label');
    label.style.cssText = 'display:flex;gap:8px;align-items:center;font-size:14px;margin-bottom:12px';
    const cb = el('input'); cb.type = 'checkbox'; cb.checked = true;
    label.append(cb, document.createTextNode('Fortschrittsfotos mitsenden'));
    inhalt.append(label);

    if (email) {
      const k = karte('Empfänger', 'senden');
      const zeile = el('div', 'zeile'); zeile.style.cursor = 'default';
      zeile.append(el('div', 'zeile__text', email), linkKnopf('Kopieren', () => kopieren(email)));
      k.append(zeile);
      k.append(el('p', 'fusstext', 'Das Teilen-Menü des Handys kann keinen Empfänger vorgeben. Die App kopiert die Adresse deshalb beim Senden — in der Mail-App ins Feld „An“ tippen und „Einfügen“ wählen.'));
      inhalt.append(k);
    } else {
      inhalt.append(el('p', 'fusstext', 'Tipp: Trägst du unter Einstellungen die E-Mail deines Coachs ein, bereitet die App den Empfänger für dich vor.'));
    }

    const status = el('p', 'leise', 'Datei wird vorbereitet …');
    inhalt.append(status);

    // Die Datei entsteht vorab, damit der Tipp auf „Senden“ das Teilen-Menü
    // ohne Verzögerung öffnen kann.
    let datei = null;
    const knoepfe = [];
    const vorbereiten = async () => {
      datei = null;
      knoepfe.forEach((k) => { k.disabled = true; });
      status.textContent = 'Datei wird vorbereitet …';
      try {
        datei = await fortschrittDatei(cb.checked);
        status.textContent = `Bereit: ${datei.name} (${zahl(datei.size / 1024)} KB)`;
        knoepfe.forEach((k) => { k.disabled = false; });
      } catch (fehler) {
        console.error(fehler);
        status.textContent = 'Datei konnte nicht erstellt werden.';
      }
    };
    cb.onchange = vorbereiten;

    if (email) {
      knoepfe.push(knopf('Per E-Mail senden', null, () => {
        if (!datei) return;
        if (navigator.clipboard) navigator.clipboard.writeText(email).catch(() => {});
        if (kannDateienTeilen(datei)) {
          toast(`${email} kopiert — in der Mail bei „An“ einfügen`);
          dateiTeilen(datei).then((ok) => { if (ok) schliessen(); });
        } else {
          // Am Computer: Datei speichern, dann eine Mail mit Empfänger öffnen.
          dateiLaden(datei);
          const betreff = `Fortschritt ${D().profil.name} · ${datumKurz(heuteText())}`;
          const text = `Hallo,\n\nim Anhang meine Fortschrittsdatei (${datei.name}).\nBitte die eben gespeicherte Datei anhängen.\n`;
          location.href = `mailto:${email}?subject=${encodeURIComponent(betreff)}&body=${encodeURIComponent(text)}`;
          toast('Datei gespeichert — bitte an die Mail anhängen');
          schliessen();
        }
      }, 'senden'));
    }
    knoepfe.push(knopf(email ? 'Anders teilen (WhatsApp …)' : 'Datei senden', email ? 'knopf--zweit' : null, () => {
      if (!datei) return;
      dateiTeilen(datei).then((ok) => {
        if (!ok) return;
        if (!kannDateienTeilen(datei)) toast('Datei gespeichert — jetzt an deinen Coach schicken');
        schliessen();
      });
    }, email ? null : 'senden'));

    const fuss = el('div');
    fuss.append(...knoepfe);
    blattFuss(blatt, fuss);
    vorbereiten();
  });
}

/* --- Router ------------------------------------------------------------- */

const ANSICHTEN = {
  heute: { titel: 'Heute', bauen: ansichtHeute },
  training: { titel: 'Training', bauen: ansichtTraining },
  ernaehrung: { titel: 'Ernährung', bauen: ansichtErnaehrung },
  checkin: { titel: 'Check-in', bauen: ansichtCheckin },
  fortschritt: { titel: 'Fortschritt', bauen: ansichtFortschritt }
};

function untertitelFuer(name) {
  const d = D();
  if (name === 'heute') return datumLang(heuteText());
  if (name === 'training') {
    const t = d.plan.tage.length;
    return `${t} ${t === 1 ? 'Trainingstag' : 'Trainingstage'} · ${d.profil.ort === 'zuhause' ? 'Zuhause' : 'Studio'}`;
  }
  if (name === 'ernaehrung') return `Ziel ${zahl(d.ziele.kcal)} kcal · ${zahl(d.ziele.e)} g Eiweiß`;
  if (name === 'checkin') return `Wochen-Check-in jeden ${WOCHENTAGE[d.coach.checkinTag]}`;
  if (name === 'fortschritt') return `Coaching-Woche ${Math.floor(tageZwischen(d.profil.start, heuteText()) / 7) + 1}`;
  return '';
}

function wechseln(name) {
  if (!ANSICHTEN[name]) name = 'heute';
  App.ansicht = name;
  document.querySelectorAll('.tab').forEach((t) => t.setAttribute('aria-selected', String(t.dataset.ansicht === name)));
  if (location.hash !== '#' + name) history.replaceState(null, '', '#' + name);
  neuZeichnen();
  window.scrollTo({ top: 0 });
}

function neuZeichnen() {
  fotoUrls.splice(0).forEach((u) => URL.revokeObjectURL(u));
  const inhalt = document.getElementById('inhalt');
  inhalt.replaceChildren();
  if (!D().profil) { einrichtung(inhalt); return; }
  const ansicht = ANSICHTEN[App.ansicht];
  document.getElementById('titel').textContent = ansicht.titel;
  document.getElementById('untertitel').textContent = untertitelFuer(App.ansicht);
  // Hinweispunkt am Reiter, wenn der Check-in fällig ist.
  const tab = document.querySelector('.tab[data-ansicht="checkin"]');
  const punkt = tab.querySelector('.tab__punkt');
  if (checkinFaellig() && !punkt) tab.append(el('span', 'tab__punkt'));
  if (!checkinFaellig() && punkt) punkt.remove();
  ansicht.bauen(inhalt);
}

/* --- Start -------------------------------------------------------------- */

async function starten() {
  Modus.anwenden();
  Modus.beobachten();
  Speicher.laden();
  try {
    const [uebungen, lebensmittel, rezepte] = await Promise.all([
      fetch('daten/uebungen.json').then((r) => r.json()),
      fetch('daten/lebensmittel.json').then((r) => r.json()),
      fetch('daten/rezepte.json').then((r) => r.json())
    ]);
    Object.assign(App, { uebungen, lebensmittel, rezepte });
  } catch (e) {
    document.getElementById('inhalt').append(leerzustand('Daten konnten nicht geladen werden',
      'Bitte die Seite neu laden. Beim ersten Aufruf braucht die App kurz eine Internetverbindung.'));
    console.error(e);
    return;
  }

  document.querySelectorAll('.tab').forEach((tab) => { tab.onclick = () => wechseln(tab.dataset.ansicht); });
  document.getElementById('einstellungen-auf').onclick = einstellungenBlatt;

  // Nach Mitternacht soll „Heute" auch wirklich heute sein, wenn die App
  // aus dem Hintergrund zurückkommt.
  let zuletztGezeichnet = heuteText();
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && heuteText() !== zuletztGezeichnet && !document.querySelector('.blatt')) {
      zuletztGezeichnet = heuteText();
      App.essensDatum = null; App.checkinDatum = null;
      neuZeichnen();
    }
  });

  wechseln((location.hash || '#heute').slice(1));
  if (D().aktiv) toast('Dein Training läuft noch — unter Training fortsetzen.');

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch((e) => console.warn('Offline-Betrieb nicht verfügbar.', e));
  }
}

starten();
