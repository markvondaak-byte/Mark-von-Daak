/* =========================================================================
   Der Stoffwechsel-Reset — App
   Kein Framework, kein Build. Reines JavaScript, damit die App genauso
   wartbar bleibt wie die Website daneben und offline ohne Ballast läuft.

   Alle Inhalte kommen aus daten/*.json — erzeugt von
   app/build/build_app_daten.py aus den Quellen der drei Bände. Hier steht
   bewusst kein einziges Rezept und keine einzige Regel im Klartext.
   ========================================================================= */
'use strict';

/* --- Speicher ----------------------------------------------------------- */
const SCHLUESSEL = 'stoffwechsel-reset.v1';

const Speicher = {
  daten: null,

  laden() {
    try {
      this.daten = JSON.parse(localStorage.getItem(SCHLUESSEL)) || null;
    } catch (e) {
      console.warn('Gespeicherte Daten unlesbar, starte neu.', e);
      this.daten = null;
    }
    if (!this.daten) this.daten = { start: null, tage: {}, messungen: [] };
    if (!this.daten.tage) this.daten.tage = {};
    if (!this.daten.messungen) this.daten.messungen = [];
    return this.daten;
  },

  sichern() {
    try {
      localStorage.setItem(SCHLUESSEL, JSON.stringify(this.daten));
    } catch (e) {
      // Privates Surfen oder voller Speicher: nicht abstürzen, nur melden.
      console.warn('Speichern fehlgeschlagen.', e);
    }
  },

  tag(nummer) {
    if (!this.daten.tage[nummer]) {
      this.daten.tage[nummer] = {
        mahlzeiten: [false, false, false, false],
        wasser: 0,
        naehrstoffe: { morgens: false, mittags: false, abends: false, joghurt: false },
        bewegung: '',
        schlaf: '',
        befinden: null,
        notiz: '',
        farbe: null   // nur ab Woche 7, wenn selbst geplant wird
      };
    }
    return this.daten.tage[nummer];
  },

  zuruecksetzen() {
    localStorage.removeItem(SCHLUESSEL);
    this.daten = { start: null, tage: {}, messungen: [] };
  }
};

/* --- Zustand ------------------------------------------------------------ */
const App = {
  programm: null,
  rezepte: null,
  wissen: null,
  ansicht: 'heute',
  rezeptFilter: 'alle',
  rezeptSuche: ''
};

/* --- Hilfen ------------------------------------------------------------- */
const WOCHENTAGE = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
const MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
                'August', 'September', 'Oktober', 'November', 'Dezember'];

const FARBNAME = {
  weiss: 'Weißer Tag', gruen: 'Grüner Tag', rot: 'Roter Tag',
  vorbereitung: 'Vorbereitung', fruehstueck: 'Frühstück',
  stabilisierung: 'Ab Stabilisierung', grundrezept: 'Grundrezept'
};

const el = (tag, klasse, text) => {
  const k = document.createElement(tag);
  if (klasse) k.className = klasse;
  if (text != null) k.textContent = text;
  return k;
};

const ikon = (name) =>
  `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;

function heuteDatum() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d;
}

function datumAusText(text) {
  const [j, m, t] = text.split('-').map(Number);
  return new Date(j, m - 1, t);
}

function textAusDatum(d) {
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Tagesnummer 1..84 auf Basis des Startdatums, sonst null. */
function aktuelleTagesnummer() {
  if (!Speicher.daten.start) return null;
  const start = datumAusText(Speicher.daten.start);
  start.setHours(0, 0, 0, 0);
  const tage = Math.floor((heuteDatum() - start) / 86400000);
  return tage + 1;
}

function datumFuerTag(nummer) {
  if (!Speicher.daten.start) return null;
  const d = datumAusText(Speicher.daten.start);
  d.setDate(d.getDate() + nummer - 1);
  return d;
}

function datumLang(d) {
  return `${WOCHENTAGE[d.getDay()]}, ${d.getDate()}. ${MONATE[d.getMonth()]} ${d.getFullYear()}`;
}

/** Findet Woche und Tag zu einer Tagesnummer. */
function tagInfo(nummer) {
  for (const woche of App.programm.wochen) {
    const tag = woche.tage.find((t) => t.nummer === nummer);
    if (tag) return { woche, tag };
  }
  return null;
}

/** Ab Woche 7 legt der Nutzer die Farbe selbst fest. */
function farbeVonTag(nummer) {
  const info = tagInfo(nummer);
  if (!info) return null;
  if (info.woche.planbar) {
    const gespeichert = Speicher.daten.tage[nummer]?.farbe;
    return gespeichert || null;
  }
  return info.tag.farbe;
}

function tagIstFertig(nummer) {
  const t = Speicher.daten.tage[nummer];
  if (!t) return false;
  return t.mahlzeiten.some(Boolean) || t.wasser > 0 || t.befinden != null;
}

/* --- Blatt (Overlay) ---------------------------------------------------- */
function blattOeffnen(titel, aufbauen) {
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
  kopf.append(el('h2', null, titel), zu);

  const inhalt = el('div', 'blatt__inhalt');
  aufbauen(inhalt, () => blattSchliessen(blatt));

  blatt.append(kopf, inhalt);
  halter.append(blatt);
  document.body.style.overflow = 'hidden';

  blatt._escape = (e) => { if (e.key === 'Escape') blattSchliessen(blatt); };
  document.addEventListener('keydown', blatt._escape);
  zu.focus();
  return blatt;
}

function blattSchliessen(blatt) {
  document.removeEventListener('keydown', blatt._escape);
  blatt.remove();
  if (!document.querySelector('.blatt')) document.body.style.overflow = '';
}

/* --- Bausteine ---------------------------------------------------------- */
function plakette(farbe) {
  const p = el('span', `plakette plakette--${farbe}`, FARBNAME[farbe] || farbe);
  return p;
}

function hakenReihe(text, note, aktiv, beiKlick) {
  const reihe = el('div', 'haken-reihe');
  const knopf = el('button', 'haken');
  knopf.innerHTML = ikon('haken');
  knopf.setAttribute('aria-pressed', String(aktiv));
  const beschriftung = el('div', 'haken-reihe__text');
  beschriftung.append(document.createTextNode(text));
  if (note) beschriftung.append(el('span', 'haken-reihe__note', note));
  knopf.setAttribute('aria-label', text);
  knopf.onclick = () => {
    const neu = knopf.getAttribute('aria-pressed') !== 'true';
    knopf.setAttribute('aria-pressed', String(neu));
    beiKlick(neu);
  };
  reihe.append(knopf, beschriftung);
  return reihe;
}

function skala(wert, beiWahl) {
  const feld = el('div', 'skala');
  for (let i = 1; i <= 10; i++) {
    const k = el('button', null, String(i));
    k.setAttribute('aria-pressed', String(wert === i));
    k.setAttribute('aria-label', `Befinden ${i} von 10`);
    k.onclick = () => {
      feld.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', 'false'));
      k.setAttribute('aria-pressed', 'true');
      beiWahl(i);
    };
    feld.append(k);
  }
  return feld;
}

function leerzustand(titel, text) {
  const box = el('div', 'leer');
  box.innerHTML = ikon('leer');
  box.append(el('div', 'leer__titel', titel), el('p', null, text));
  return box;
}

/* --- Ansicht: Heute ----------------------------------------------------- */
function ansichtHeute(ziel) {
  if (!Speicher.daten.start) return einrichtung(ziel);

  const nummer = aktuelleTagesnummer();
  if (nummer < 1) {
    const d = datumAusText(Speicher.daten.start);
    ziel.append(leerzustand('Noch nicht gestartet',
      `Dein Programm beginnt am ${datumLang(d)}. Bis dahin kannst du dich im Wissensteil einlesen und den ersten Einkauf planen.`));
    return;
  }
  if (nummer > 84) {
    ziel.append(abschlussKarte(nummer));
    return;
  }
  tageskarte(ziel, nummer, true);
}

function abschlussKarte(nummer) {
  const box = el('div', 'karte');
  box.append(el('div', 'karte__titel', 'Die zwölf Wochen sind vorbei'));
  const p1 = el('p', null,
    `Heute ist Tag ${nummer} seit deinem Start. Das Programm dieser App endet nach 84 Tagen — die Stabilisierungsphase läuft aber noch rund sieben Wochen weiter.`);
  const p2 = el('p', null,
    'Es ändert sich nichts an dem, was du seit Woche 7 machst: grüne Tage als Basis, ein bis zwei rote Tage pro Woche, und auf jeden roten Tag folgt ein weißer. Der weiße Tag bleibt streng.');
  p1.style.fontSize = p2.style.fontSize = '14.5px';
  box.append(p1, p2);
  return box;
}

/** Die zentrale Tageskarte — auch aus der Programmübersicht heraus genutzt. */
function tageskarte(ziel, nummer, istHeute) {
  const info = tagInfo(nummer);
  const tag = Speicher.tag(nummer);
  const farbe = farbeVonTag(nummer);
  const datum = datumFuerTag(nummer);

  /* Kopfbereich */
  const held = el('div', 'heute');
  const oben = el('div', 'heute__oben');
  oben.append(el('span', 'heute__phase',
    `Woche ${info.woche.nummer} · ${info.woche.phaseName}`));
  const marke = el('span', 'heute__plakette',
    farbe ? FARBNAME[farbe] : 'Farbe wählen');
  oben.append(marke);
  held.append(oben);
  held.append(el('div', 'heute__tag', `Tag ${nummer} von 84`));
  if (datum) held.append(el('div', 'heute__datum', datumLang(datum)));

  const balkenAussen = el('div', 'heute__fortschritt');
  const balken = el('div', 'heute__balken');
  balken.style.width = `${Math.min(100, (nummer / 84) * 100)}%`;
  balkenAussen.append(balken);
  held.append(balkenAussen);
  const meta = el('div', 'heute__meta');
  meta.append(el('span', null, `${Math.round((nummer / 84) * 100)} % geschafft`),
              el('span', null, `noch ${Math.max(0, 84 - nummer)} Tage`));
  held.append(meta);
  ziel.append(held);

  /* Farbwahl ab Woche 7 */
  if (info.woche.planbar) {
    const box = el('div', 'karte');
    box.append(el('div', 'karte__titel', 'Tagesfarbe festlegen'));
    const hinweis = el('p', null,
      'Ab der Stabilisierungsphase planst du selbst: grün als Basis, ein bis zwei rote Tage pro Woche, und auf jeden roten Tag folgt ein weißer.');
    hinweis.style.cssText = 'font-size:13.5px;color:var(--ink-soft);margin:0 0 11px';
    box.append(hinweis);
    const reihe = el('div', 'reihe');
    ['weiss', 'gruen', 'rot'].forEach((f) => {
      const k = el('button', 'chip', FARBNAME[f]);
      k.style.width = '100%';
      k.setAttribute('aria-pressed', String(farbe === f));
      k.onclick = () => {
        tag.farbe = f;
        Speicher.sichern();
        neuZeichnen();
      };
      reihe.append(k);
    });
    box.append(reihe);
    ziel.append(box);
    if (!farbe) return;   // ohne Farbe kein sinnvolles Protokoll
  }

  /* Vorbereitungstage brauchen kein Mahlzeitenprotokoll */
  if (farbe === 'vorbereitung') {
    const box = el('div', 'karte');
    box.append(el('div', 'karte__titel', 'Heute'));
    const p = el('p', null,
      'In der Vorbereitungsphase änderst du an deiner Ernährung noch nichts. Was dazukommt, sind die Nährstoffe und der probiotische Joghurt.');
    p.style.cssText = 'font-size:14px;color:var(--ink-soft);margin:0 0 8px';
    box.append(p);
    box.append(hakenReihe('Wie gewohnt gegessen', null, tag.mahlzeiten[0], (v) => {
      tag.mahlzeiten[0] = v; Speicher.sichern();
    }));
    ziel.append(box);
  } else {
    const box = el('div', 'karte');
    const titel = el('div', 'karte__titel', 'Mahlzeiten');
    const zaehler = el('span', 'zaehler', `${tag.mahlzeiten.filter(Boolean).length} von 4`);
    titel.append(zaehler);
    box.append(titel);
    const noten = ['Joghurt mit Körnern, kalt', 'ca. 4 Stunden später',
                   'ca. 4 Stunden später', 'ca. 4 Stunden später'];
    tag.mahlzeiten.forEach((wert, i) => {
      box.append(hakenReihe(`${i + 1}. Mahlzeit`, noten[i], wert, (v) => {
        tag.mahlzeiten[i] = v;
        zaehler.textContent = `${tag.mahlzeiten.filter(Boolean).length} von 4`;
        Speicher.sichern();
      }));
    });
    ziel.append(box);
  }

  /* Wasser */
  const wasserBox = el('div', 'karte');
  const wTitel = el('div', 'karte__titel', 'Wasser');
  const wZaehler = el('span', 'zaehler', `${tag.wasser * 250} ml von 2000 ml`);
  wTitel.append(wZaehler);
  wasserBox.append(wTitel);
  const perlen = el('div', 'wasser');
  for (let i = 1; i <= 8; i++) {
    const p = el('button', 'perle', '💧');
    p.setAttribute('aria-pressed', String(tag.wasser >= i));
    p.setAttribute('aria-label', `${i * 250} Milliliter`);
    p.onclick = () => {
      tag.wasser = (tag.wasser === i) ? i - 1 : i;
      perlen.querySelectorAll('.perle').forEach((q, j) =>
        q.setAttribute('aria-pressed', String(tag.wasser >= j + 1)));
      wZaehler.textContent = `${tag.wasser * 250} ml von 2000 ml`;
      Speicher.sichern();
    };
    perlen.append(p);
  }
  wasserBox.append(perlen);
  const wHinweis = el('p', null, 'Immer 15 bis 20 Minuten Abstand zu den Mahlzeiten — nie dazu.');
  wHinweis.style.cssText = 'font-size:12px;color:var(--ink-soft);margin:10px 0 0';
  wasserBox.append(wHinweis);
  ziel.append(wasserBox);

  /* Nährstoffe */
  const nBox = el('div', 'karte');
  nBox.append(el('div', 'karte__titel', 'Nährstoffe'));
  [['morgens', 'Morgens'], ['mittags', 'Mittags'],
   ['abends', 'Abends'], ['joghurt', 'Probiotischer Joghurt']].forEach(([k, t]) => {
    nBox.append(hakenReihe(t, null, tag.naehrstoffe[k], (v) => {
      tag.naehrstoffe[k] = v; Speicher.sichern();
    }));
  });
  ziel.append(nBox);

  /* Befinden und Notiz */
  const bBox = el('div', 'karte');
  bBox.append(el('div', 'karte__titel', 'Wie war der Tag?'));

  const bFeld = el('div', 'feld');
  bFeld.append(el('label', null, 'Befinden'));
  bFeld.append(skala(tag.befinden, (v) => { tag.befinden = v; Speicher.sichern(); }));
  bBox.append(bFeld);

  const reihe = el('div', 'reihe');
  [['bewegung', 'Bewegung', 'z. B. 30 Min. Spaziergang'],
   ['schlaf', 'Schlaf', 'Stunden']].forEach(([k, label, platzhalter]) => {
    const f = el('div', 'feld');
    f.append(el('label', null, label));
    const i = el('input', 'eingabe');
    i.value = tag[k] || '';
    i.placeholder = platzhalter;
    if (k === 'schlaf') { i.type = 'number'; i.min = '0'; i.max = '24'; i.step = '0.5'; }
    i.oninput = () => { tag[k] = i.value; Speicher.sichern(); };
    f.append(i);
    reihe.append(f);
  });
  bBox.append(reihe);

  const nFeld = el('div', 'feld');
  nFeld.append(el('label', null, 'Notiz'));
  const nText = el('textarea', 'eingabe');
  nText.value = tag.notiz || '';
  nText.placeholder = 'Was ist dir heute aufgefallen?';
  nText.oninput = () => { tag.notiz = nText.value; Speicher.sichern(); };
  nFeld.append(nText);
  bBox.append(nFeld);
  ziel.append(bBox);

  /* Wochenfokus */
  const fBox = el('div', 'karte');
  fBox.append(el('div', 'karte__titel', `Diese Woche: ${info.woche.fokusTitel}`));
  const fText = el('p', null, info.woche.fokusText);
  fText.style.cssText = 'font-size:14px;margin:0;color:var(--ink-soft)';
  fBox.append(fText);
  ziel.append(fBox);

  /* Passende Rezepte */
  if (farbe && farbe !== 'vorbereitung') {
    const passend = App.rezepte.rezepte.filter((r) =>
      r.farbe === farbe || (farbe !== 'rot' && r.farbe === 'fruehstueck'));
    if (passend.length) {
      ziel.append(el('div', 'abschnitt-titel', `Rezepte für heute`));
      passend.slice(0, 4).forEach((r) => ziel.append(rezeptZeile(r)));
      const mehr = el('button', 'knopf knopf--zweit', `Alle ${passend.length} Rezepte ansehen`);
      mehr.onclick = () => { App.rezeptFilter = farbe; wechseln('rezepte'); };
      ziel.append(mehr);
    }
  }
}

/* --- Einrichtung -------------------------------------------------------- */
function einrichtung(ziel) {
  const box = el('div', 'karte');
  box.append(el('div', 'karte__titel', 'Willkommen'));
  const p = el('p', null,
    'Diese App begleitet dich zwölf Wochen lang durch das Ernährungskonzept: Tagesplan, Rezepte, Nachschlagewerk und deinen Verlauf. Trag zum Start dein Startdatum ein.');
  p.style.cssText = 'font-size:14.5px;margin:0 0 14px';
  box.append(p);

  const feld = el('div', 'feld');
  feld.append(el('label', null, 'Erster Tag der Vorbereitungsphase'));
  const eingabe = el('input', 'eingabe');
  eingabe.type = 'date';
  eingabe.value = textAusDatum(heuteDatum());
  feld.append(eingabe);
  box.append(feld);

  const start = el('button', 'knopf', 'Programm starten');
  start.onclick = () => {
    if (!eingabe.value) return;
    Speicher.daten.start = eingabe.value;
    Speicher.sichern();
    neuZeichnen();
  };
  box.append(start);
  ziel.append(box);

  const hinweis = el('div', 'karte');
  hinweis.append(el('div', 'karte__titel', 'Bevor du beginnst'));
  const h = el('p', null,
    'Diese App ist kein medizinischer Ratgeber. Lass deinen Gesundheitszustand vorher ärztlich abklären — zwingend bei Diabetes, Herz-Kreislauf- und Nierenerkrankungen sowie bei der Einnahme von Medikamenten. In Schwangerschaft und Stillzeit ist das Konzept nicht geeignet, für Kinder und Jugendliche ebenfalls nicht.');
  h.style.cssText = 'font-size:13.5px;margin:0;color:var(--ink-soft)';
  hinweis.append(h);
  ziel.append(hinweis);
}

/* --- Ansicht: Programm -------------------------------------------------- */
function ansichtProgramm(ziel) {
  if (!Speicher.daten.start) {
    ziel.append(leerzustand('Noch kein Startdatum',
      'Leg unter „Heute" dein Startdatum fest, dann erscheint hier dein Plan über zwölf Wochen.'));
    return;
  }
  const aktuell = aktuelleTagesnummer();
  const gitter = el('div', 'wochen');

  App.programm.wochen.forEach((woche) => {
    const karte = el('div', 'woche');
    const kopf = el('div', 'woche__kopf');
    kopf.append(el('span', 'woche__nr', `Woche ${woche.nummer}`));
    kopf.append(el('span', 'woche__phase', woche.phaseName));
    kopf.append(el('span', 'woche__fokus', woche.fokusTitel));
    karte.append(kopf);

    const tage = el('div', 'woche__tage');
    woche.tage.forEach((t) => {
      const farbe = farbeVonTag(t.nummer) || 'vorbereitung';
      const zelle = el('button', `tageszelle tageszelle--${farbe}`);
      if (t.nummer === aktuell) zelle.classList.add('tageszelle--heute');
      if (tagIstFertig(t.nummer)) zelle.classList.add('tageszelle--fertig');
      zelle.append(el('span', 'tageszelle__wt', t.wochentag.slice(0, 2)));
      zelle.append(el('span', 'tageszelle__nr', String(t.nummer)));
      const d = datumFuerTag(t.nummer);
      zelle.setAttribute('aria-label',
        `Tag ${t.nummer}, ${FARBNAME[farbe]}${d ? ', ' + datumLang(d) : ''}`);
      zelle.onclick = () => tagBlattOeffnen(t.nummer);
      tage.append(zelle);
    });
    karte.append(tage);
    gitter.append(karte);
  });
  ziel.append(gitter);

  const legende = el('div', 'fusstext');
  legende.textContent =
    'Ein Punkt markiert Tage, an denen du etwas eingetragen hast. Ab Woche 7 legst du die Tagesfarben selbst fest — tippe einen Tag an.';
  ziel.append(legende);
}

function tagBlattOeffnen(nummer) {
  blattOeffnen(`Tag ${nummer}`, (inhalt) => tageskarte(inhalt, nummer, false));
}

/* --- Ansicht: Rezepte --------------------------------------------------- */
function ansichtRezepte(ziel) {
  const suchfeld = el('div', 'feld');
  const suche = el('input', 'eingabe');
  suche.type = 'search';
  suche.placeholder = 'Rezept oder Zutat suchen …';
  suche.value = App.rezeptSuche;
  suche.oninput = () => {
    App.rezeptSuche = suche.value;
    liste.replaceChildren(...rezeptListe());
  };
  suchfeld.append(suche);
  ziel.append(suchfeld);

  const filter = el('div', 'filter');
  const gruppen = [['alle', 'Alle'], ['fruehstueck', 'Frühstück'],
                   ['weiss', 'Weiße Tage'], ['gruen', 'Grüne Tage'],
                   ['stabilisierung', 'Ab Stabilisierung'], ['grundrezept', 'Grundrezepte']];
  gruppen.forEach(([wert, beschriftung]) => {
    const chip = el('button', 'chip', beschriftung);
    chip.setAttribute('aria-pressed', String(App.rezeptFilter === wert));
    chip.onclick = () => {
      App.rezeptFilter = wert;
      filter.querySelectorAll('.chip').forEach((c) =>
        c.setAttribute('aria-pressed', String(c.textContent === beschriftung)));
      liste.replaceChildren(...rezeptListe());
    };
    filter.append(chip);
  });
  ziel.append(filter);

  const liste = el('div');
  liste.replaceChildren(...rezeptListe());
  ziel.append(liste);
}

function rezeptListe() {
  const suche = App.rezeptSuche.trim().toLowerCase();
  const treffer = App.rezepte.rezepte.filter((r) => {
    if (App.rezeptFilter !== 'alle' && r.farbe !== App.rezeptFilter) return false;
    if (!suche) return true;
    return r.name.toLowerCase().includes(suche) ||
           r.zutaten.some((z) => z.toLowerCase().includes(suche));
  });
  if (!treffer.length) {
    return [leerzustand('Nichts gefunden',
      'Versuch einen anderen Suchbegriff oder wähle einen anderen Filter.')];
  }
  return treffer.map(rezeptZeile);
}

function rezeptZeile(r) {
  const knopf = el('button', 'rezept');
  const text = el('div', 'rezept__text');
  text.append(el('div', 'rezept__name', r.name));
  const teile = [];
  if (r.zeit) teile.push(`${r.zeit} Min.`);
  if (r.eiweiss) teile.push(`${r.eiweiss} g Eiweiß`);
  teile.push(`${r.portionen} Portion${r.portionen > 1 ? 'en' : ''}`);
  text.append(el('div', 'rezept__meta', teile.join('  ·  ')));
  const pfeil = el('div', 'rezept__pfeil');
  pfeil.innerHTML = ikon('zurueck');
  pfeil.style.transform = 'rotate(180deg)';
  knopf.append(plakette(r.farbe), text, pfeil);
  knopf.onclick = () => rezeptBlatt(r);
  return knopf;
}

function rezeptBlatt(r) {
  blattOeffnen(r.name, (inhalt) => {
    const kopf = el('div');
    kopf.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px';
    kopf.append(plakette(r.farbe));
    const meta = [];
    if (r.zeit) meta.push(`${r.zeit} Min.`);
    if (r.eiweiss) meta.push(`ca. ${r.eiweiss} g Eiweiß`);
    meta.push(`${r.portionen} Portion${r.portionen > 1 ? 'en' : ''}`);
    meta.forEach((m) => {
      const s = el('span', 'plakette plakette--grundrezept', m);
      kopf.append(s);
    });
    inhalt.append(kopf);

    const zBox = el('div', 'karte');
    zBox.append(el('div', 'karte__titel', 'Zutaten'));
    r.zutaten.forEach((z) => {
      const zeile = el('div', 'zutat');
      zeile.append(el('span', 'zutat__punkt', '·'), el('span', null, z));
      zBox.append(zeile);
    });
    inhalt.append(zBox);

    const sBox = el('div', 'karte');
    sBox.append(el('div', 'karte__titel', 'Zubereitung'));
    r.schritte.forEach((s, i) => {
      const zeile = el('div', 'schritt');
      zeile.append(el('div', 'schritt__nr', String(i + 1)),
                   el('div', 'schritt__text', s));
      sBox.append(zeile);
    });
    inhalt.append(sBox);

    if (r.tipp) {
      const t = el('div', 'hinweis');
      t.append(el('div', 'hinweis__titel', 'Tipp'), el('p', null, r.tipp));
      inhalt.append(t);
    }

    const fuss = el('div', 'fusstext');
    fuss.textContent = `Aus dem Teil „${r.teil}“. Alle Mengen gelten für rund 80 kg Körpergewicht — rechne sie nach der Formel im Wissensteil auf dich um.`;
    inhalt.append(fuss);
  });
}

/* --- Ansicht: Wissen ---------------------------------------------------- */
function ansichtWissen(ziel) {
  App.wissen.kapitel.forEach((k) => {
    const knopf = el('button', 'rezept');
    const text = el('div', 'rezept__text');
    text.append(el('div', 'rezept__name', k.titel));
    const ersterAbsatz = k.bloecke.find((b) => b.typ === 'absatz');
    if (ersterAbsatz) {
      const kurz = ersterAbsatz.text.slice(0, 88);
      text.append(el('div', 'rezept__meta',
        kurz + (ersterAbsatz.text.length > 88 ? ' …' : '')));
    }
    const pfeil = el('div', 'rezept__pfeil');
    pfeil.innerHTML = ikon('zurueck');
    pfeil.style.transform = 'rotate(180deg)';
    knopf.append(text, pfeil);
    knopf.onclick = () => wissenBlatt(k);
    ziel.append(knopf);
  });

  const fuss = el('div', 'fusstext');
  fuss.textContent =
    'Auszug aus „Der Stoffwechsel-Reset — Das 4-Phasen-Ernährungskonzept in 28 Tagen". Kein medizinischer Ratgeber.';
  ziel.append(fuss);
}

function wissenBlatt(kapitel) {
  blattOeffnen(kapitel.titel, (inhalt) => {
    const block = el('div', 'wissen-block');
    kapitel.bloecke.forEach((b) => {
      if (b.typ === 'h1') return;   // Titel steht schon im Kopf
      if (b.typ === 'h2') block.append(el('h2', null, b.text));
      else if (b.typ === 'h3') block.append(el('h3', null, b.text));
      else if (b.typ === 'absatz') block.append(el('p', null, entfetten(b.text)));
      else if (b.typ === 'liste' || b.typ === 'nummern') {
        const l = el(b.typ === 'liste' ? 'ul' : 'ol');
        b.punkte.forEach((p) => l.append(el('li', null, entfetten(p))));
        block.append(l);
      } else if (b.typ === 'kasten') {
        const k = el('div', 'hinweis');
        if (b.titel) k.append(el('div', 'hinweis__titel', entfetten(b.titel)));
        k.append(el('p', null, entfetten(b.text)));
        block.append(k);
      } else if (b.typ === 'tabelle') {
        const wrap = el('div', 'tabelle-wrap');
        const t = el('table');
        const kopf = el('tr');
        b.kopf.forEach((z) => kopf.append(el('th', null, entfetten(z))));
        t.append(kopf);
        b.zeilen.forEach((zeile) => {
          const tr = el('tr');
          zeile.forEach((z) => tr.append(el('td', null, entfetten(z))));
          t.append(tr);
        });
        wrap.append(t);
        block.append(wrap);
      }
    });
    inhalt.append(block);
  });
}

/** Entfernt Markdown-Auszeichnung, die in den Textblöcken übrig ist. */
function entfetten(text) {
  return text.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1');
}

/* --- Ansicht: Fortschritt ----------------------------------------------- */
function ansichtFortschritt(ziel) {
  const messungen = Speicher.daten.messungen;

  const neu = el('button', 'knopf', 'Neue Messung eintragen');
  neu.onclick = () => messungBlatt();
  ziel.append(neu);

  if (!messungen.length) {
    ziel.append(leerzustand('Noch keine Messung',
      'Trag deine Startwerte ein, bevor du beginnst. Miss immer morgens, nüchtern und an derselben Stelle.'));
    return;
  }

  const sortiert = [...messungen].sort((a, b) => a.datum.localeCompare(b.datum));
  const erste = sortiert[0];
  const letzte = sortiert[sortiert.length - 1];

  ziel.append(el('div', 'abschnitt-titel', 'Seit dem Start'));
  const werte = el('div', 'werte');
  [['gewicht', 'Gewicht', 'kg'], ['taille', 'Taille', 'cm'],
   ['bauch', 'Bauch', 'cm'], ['huefte', 'Hüfte', 'cm']].forEach(([k, label, einheit]) => {
    if (letzte[k] == null || letzte[k] === '') return;
    const box = el('div', 'wert');
    box.append(el('div', 'wert__label', label));
    box.append(el('div', 'wert__zahl', `${letzte[k]} ${einheit}`));
    if (erste[k] != null && erste[k] !== '' && sortiert.length > 1) {
      const delta = Number(letzte[k]) - Number(erste[k]);
      const zeichen = delta > 0 ? '+' : '';
      const d = el('div',
        `wert__delta ${delta < 0 ? 'wert__delta--gut' : 'wert__delta--neutral'}`,
        `${zeichen}${delta.toFixed(1)} ${einheit}`);
      box.append(d);
    }
    werte.append(box);
  });
  ziel.append(werte);

  const mitGewicht = sortiert.filter((m) => m.gewicht !== '' && m.gewicht != null);
  if (mitGewicht.length > 1) {
    ziel.append(el('div', 'abschnitt-titel', 'Gewichtsverlauf'));
    const karte = el('div', 'karte');
    karte.append(diagramm(mitGewicht.map((m) => Number(m.gewicht))));
    const h = el('p', null,
      'Gewicht verläuft nicht gleichmäßig. Plateaus über ein bis zwei Wochen sind normal — der Umfang zeigt Veränderungen oft früher.');
    h.style.cssText = 'font-size:12px;color:var(--ink-soft);margin:8px 0 0';
    karte.append(h);
    ziel.append(karte);
  }

  ziel.append(el('div', 'abschnitt-titel', 'Alle Messungen'));
  [...sortiert].reverse().forEach((m, i) => {
    const knopf = el('button', 'rezept');
    const text = el('div', 'rezept__text');
    text.append(el('div', 'rezept__name', datumLang(datumAusText(m.datum))));
    const teile = [];
    if (m.gewicht) teile.push(`${m.gewicht} kg`);
    if (m.taille) teile.push(`Taille ${m.taille} cm`);
    if (m.bauch) teile.push(`Bauch ${m.bauch} cm`);
    text.append(el('div', 'rezept__meta', teile.join('  ·  ') || 'ohne Werte'));
    knopf.append(text);
    knopf.onclick = () => messungBlatt(sortiert.length - 1 - i, m);
    ziel.append(knopf);
  });
}

function diagramm(werte) {
  // Linker Rand großzügig, damit die Achsenbeschriftung nicht an den
  // ersten Messpunkt stößt.
  const b = 320, h = 170, rand = { o: 14, u: 24, l: 48, r: 12 };
  const min = Math.min(...werte), max = Math.max(...werte);
  const spanne = (max - min) || 1;
  const innenB = b - rand.l - rand.r, innenH = h - rand.o - rand.u;

  const x = (i) => rand.l + (werte.length === 1 ? innenB / 2 : (i / (werte.length - 1)) * innenB);
  const y = (v) => rand.o + innenH - ((v - min) / spanne) * innenH;

  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('class', 'diagramm');
  svg.setAttribute('viewBox', `0 0 ${b} ${h}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label',
    `Gewichtsverlauf über ${werte.length} Messungen, von ${werte[0]} auf ${werte[werte.length - 1]} Kilogramm`);

  const linie = werte.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');

  const flaeche = document.createElementNS(ns, 'path');
  flaeche.setAttribute('class', 'flaeche');
  flaeche.setAttribute('d',
    `${linie} L${x(werte.length - 1).toFixed(1)},${rand.o + innenH} L${x(0).toFixed(1)},${rand.o + innenH} Z`);
  svg.append(flaeche);

  const achse = document.createElementNS(ns, 'line');
  achse.setAttribute('class', 'achse');
  achse.setAttribute('x1', rand.l); achse.setAttribute('x2', b - rand.r);
  achse.setAttribute('y1', rand.o + innenH); achse.setAttribute('y2', rand.o + innenH);
  svg.append(achse);

  const pfad = document.createElementNS(ns, 'path');
  pfad.setAttribute('class', 'linie');
  pfad.setAttribute('d', linie);
  svg.append(pfad);

  werte.forEach((v, i) => {
    const p = document.createElementNS(ns, 'circle');
    p.setAttribute('class', 'punkt');
    p.setAttribute('cx', x(i)); p.setAttribute('cy', y(v)); p.setAttribute('r', 3);
    svg.append(p);
  });

  [[max, rand.o + 4], [min, rand.o + innenH - 2]].forEach(([wert, py]) => {
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('class', 'beschriftung');
    t.setAttribute('x', 4); t.setAttribute('y', py);
    t.textContent = `${wert} kg`;
    svg.append(t);
  });

  return svg;
}

function messungBlatt(index, vorhanden) {
  const bearbeiten = index != null;
  blattOeffnen(bearbeiten ? 'Messung bearbeiten' : 'Neue Messung', (inhalt, schliessen) => {
    const daten = vorhanden
      ? { ...vorhanden }
      : { datum: textAusDatum(heuteDatum()), gewicht: '', taille: '', bauch: '', huefte: '', oberschenkel: '' };

    const felder = [
      ['datum', 'Datum', 'date'],
      ['gewicht', 'Gewicht (kg)', 'number'],
      ['taille', 'Taille (cm)', 'number'],
      ['bauch', 'Bauch auf Nabelhöhe (cm)', 'number'],
      ['huefte', 'Hüfte (cm)', 'number'],
      ['oberschenkel', 'Oberschenkel (cm)', 'number']
    ];
    felder.forEach(([k, label, typ]) => {
      const f = el('div', 'feld');
      f.append(el('label', null, label));
      const i = el('input', 'eingabe');
      i.type = typ;
      if (typ === 'number') { i.step = '0.1'; i.inputMode = 'decimal'; }
      i.value = daten[k] ?? '';
      i.oninput = () => { daten[k] = i.value; };
      f.append(i);
      inhalt.append(f);
    });

    const hinweis = el('div', 'hinweis');
    hinweis.append(el('div', 'hinweis__titel', 'So misst du vergleichbar'));
    hinweis.append(el('p', null,
      'Morgens, nüchtern, nach dem ersten Toilettengang. Maßband waagerecht anlegen, nicht straff ziehen, normal ausatmen. Einmal pro Woche genügt.'));
    inhalt.append(hinweis);

    const sichern = el('button', 'knopf', 'Speichern');
    sichern.onclick = () => {
      if (bearbeiten) Speicher.daten.messungen[index] = daten;
      else Speicher.daten.messungen.push(daten);
      Speicher.sichern();
      schliessen();
      neuZeichnen();
    };
    inhalt.append(sichern);

    if (bearbeiten) {
      const loeschen = el('button', 'knopf knopf--zweit', 'Diese Messung löschen');
      loeschen.style.marginTop = '10px';
      loeschen.onclick = () => {
        Speicher.daten.messungen.splice(index, 1);
        Speicher.sichern();
        schliessen();
        neuZeichnen();
      };
      inhalt.append(loeschen);
    }
  });
}

/* --- Einstellungen ------------------------------------------------------ */
function einstellungenBlatt() {
  blattOeffnen('Einstellungen', (inhalt, schliessen) => {
    const sBox = el('div', 'karte');
    sBox.append(el('div', 'karte__titel', 'Startdatum'));
    const f = el('div', 'feld');
    const i = el('input', 'eingabe');
    i.type = 'date';
    i.value = Speicher.daten.start || textAusDatum(heuteDatum());
    i.onchange = () => {
      Speicher.daten.start = i.value;
      Speicher.sichern();
      neuZeichnen();
    };
    f.append(i);
    sBox.append(f);
    const h = el('p', null, 'Der erste Tag deiner Vorbereitungsphase. Alle Tagesnummern richten sich danach.');
    h.style.cssText = 'font-size:12.5px;color:var(--ink-soft);margin:0';
    sBox.append(h);
    inhalt.append(sBox);

    const dBox = el('div', 'karte');
    dBox.append(el('div', 'karte__titel', 'Deine Daten'));
    const info = el('p', null,
      'Alles bleibt auf diesem Gerät — es gibt keinen Server und kein Konto. Wenn du den Browserspeicher löschst oder das Gerät wechselst, sind die Einträge weg. Sicher sie deshalb gelegentlich.');
    info.style.cssText = 'font-size:13.5px;color:var(--ink-soft);margin:0 0 12px';
    dBox.append(info);

    const exportieren = el('button', 'knopf knopf--zweit', 'Daten sichern');
    exportieren.onclick = () => {
      const blob = new Blob([JSON.stringify(Speicher.daten, null, 2)],
                           { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `stoffwechsel-reset-${textAusDatum(heuteDatum())}.json`;
      a.click();
      URL.revokeObjectURL(url);
    };
    dBox.append(exportieren);

    const importieren = el('button', 'knopf knopf--zweit', 'Sicherung einlesen');
    importieren.style.marginTop = '10px';
    importieren.onclick = () => {
      const eingabe = document.createElement('input');
      eingabe.type = 'file';
      eingabe.accept = 'application/json';
      eingabe.onchange = async () => {
        const datei = eingabe.files[0];
        if (!datei) return;
        try {
          const gelesen = JSON.parse(await datei.text());
          if (typeof gelesen !== 'object' || gelesen === null) throw new Error('Kein Objekt');
          Speicher.daten = {
            start: gelesen.start ?? null,
            tage: gelesen.tage ?? {},
            messungen: Array.isArray(gelesen.messungen) ? gelesen.messungen : []
          };
          Speicher.sichern();
          schliessen();
          neuZeichnen();
        } catch (e) {
          alert('Die Datei konnte nicht gelesen werden. Bitte wähle eine Sicherung, die diese App erzeugt hat.');
        }
      };
      eingabe.click();
    };
    dBox.append(importieren);
    inhalt.append(dBox);

    const rBox = el('div', 'karte');
    rBox.append(el('div', 'karte__titel', 'Neu beginnen'));
    const rHinweis = el('p', null,
      'Löscht Startdatum, alle Tageseinträge und alle Messungen. Das lässt sich nicht rückgängig machen.');
    rHinweis.style.cssText = 'font-size:13.5px;color:var(--ink-soft);margin:0 0 12px';
    rBox.append(rHinweis);
    const zuruecksetzen = el('button', 'knopf knopf--zweit', 'Alle Daten löschen');
    zuruecksetzen.onclick = () => {
      if (!confirm('Wirklich alle Daten löschen? Das lässt sich nicht rückgängig machen.')) return;
      Speicher.zuruecksetzen();
      schliessen();
      neuZeichnen();
    };
    rBox.append(zuruecksetzen);
    inhalt.append(rBox);

    const fuss = el('div', 'fusstext');
    fuss.textContent =
      'Der Stoffwechsel-Reset · Mark von Daak · markvondaak@icloud.com — Diese App ist kein medizinischer Ratgeber und ersetzt keine ärztliche Beratung. „cellRESET" und „FitLine" sind Marken der PM-International AG; diese App wird von diesem Unternehmen weder herausgegeben noch autorisiert.';
    inhalt.append(fuss);
  });
}

/* --- Router ------------------------------------------------------------- */
const ANSICHTEN = {
  heute: { titel: 'Heute', bauen: ansichtHeute },
  programm: { titel: 'Programm', bauen: ansichtProgramm },
  rezepte: { titel: 'Rezepte', bauen: ansichtRezepte },
  wissen: { titel: 'Wissen', bauen: ansichtWissen },
  fortschritt: { titel: 'Verlauf', bauen: ansichtFortschritt }
};

function untertitelFuer(name) {
  const nummer = aktuelleTagesnummer();
  if (name === 'heute' && nummer != null && nummer >= 1 && nummer <= 84) {
    const info = tagInfo(nummer);
    return `Woche ${info.woche.nummer} von 12 · ${info.woche.phaseName}`;
  }
  if (name === 'rezepte') return `${App.rezepte.rezepte.length} Gerichte im Konzept`;
  if (name === 'programm') return '12 Wochen · 84 Tage';
  if (name === 'wissen') return 'Zum Nachschlagen';
  if (name === 'fortschritt') return `${Speicher.daten.messungen.length} Messungen`;
  return '';
}

function wechseln(name) {
  App.ansicht = name;
  document.querySelectorAll('.tab').forEach((t) =>
    t.setAttribute('aria-selected', String(t.dataset.ansicht === name)));
  neuZeichnen();
  document.getElementById('inhalt').scrollTo?.({ top: 0 });
  window.scrollTo({ top: 0 });
}

function neuZeichnen() {
  const ansicht = ANSICHTEN[App.ansicht];
  document.getElementById('titel').textContent = ansicht.titel;
  document.getElementById('untertitel').textContent = untertitelFuer(App.ansicht);
  const inhalt = document.getElementById('inhalt');
  inhalt.replaceChildren();
  ansicht.bauen(inhalt);
}

/* --- Start -------------------------------------------------------------- */
async function starten() {
  Speicher.laden();
  try {
    const [programm, rezepte, wissen] = await Promise.all([
      fetch('daten/programm.json').then((r) => r.json()),
      fetch('daten/rezepte.json').then((r) => r.json()),
      fetch('daten/wissen.json').then((r) => r.json())
    ]);
    App.programm = programm;
    App.rezepte = rezepte;
    App.wissen = wissen;
  } catch (e) {
    document.getElementById('inhalt').append(leerzustand(
      'Daten konnten nicht geladen werden',
      'Bitte die Seite neu laden. Beim ersten Aufruf braucht die App kurz eine Internetverbindung.'));
    console.error(e);
    return;
  }

  document.querySelectorAll('.tab').forEach((tab) => {
    tab.onclick = () => wechseln(tab.dataset.ansicht);
  });
  document.getElementById('einstellungen-auf').onclick = einstellungenBlatt;

  neuZeichnen();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch((e) =>
      console.warn('Offline-Betrieb nicht verfügbar.', e));
  }
}

starten();
