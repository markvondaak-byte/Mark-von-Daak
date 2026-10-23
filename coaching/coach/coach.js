/* =========================================================================
   Coaching — Coach-Ansicht
   Öffnet die Fortschrittsdateien, die Klienten aus ihrer App verschicken,
   und wertet sie aus. Kein Server: Die Berichte liegen in IndexedDB auf dem
   Gerät des Coachs. Ein neuer Bericht desselben Klienten ersetzt den alten.

   Die Rechnungen ähneln denen der Klienten-App, bekommen den Bericht aber
   als Parameter statt auf gespeicherte Daten zuzugreifen.
   ========================================================================= */
'use strict';

/* --- Speicher ----------------------------------------------------------- */
const Klienten = {
  db: null,

  oeffnen() {
    if (this.db) return Promise.resolve(this.db);
    return new Promise((ok, fehler) => {
      const anfrage = indexedDB.open('coaching-coach', 1);
      anfrage.onupgradeneeded = () => anfrage.result.createObjectStore('klienten', { keyPath: 'id' });
      anfrage.onsuccess = () => { this.db = anfrage.result; ok(this.db); };
      anfrage.onerror = () => fehler(anfrage.error);
    });
  },

  async _tx(modus, arbeit) {
    const db = await this.oeffnen();
    return new Promise((ok, fehler) => {
      const tx = db.transaction('klienten', modus);
      const ergebnis = arbeit(tx.objectStore('klienten'));
      tx.oncomplete = () => ok(ergebnis && 'result' in ergebnis ? ergebnis.result : undefined);
      tx.onerror = () => fehler(tx.error);
    });
  },

  alle() { return this._tx('readonly', (s) => s.getAll()).then((l) => l || []); },
  holen(id) { return this._tx('readonly', (s) => s.get(id)); },
  speichern(eintrag) { return this._tx('readwrite', (s) => s.put(eintrag)); },
  loeschen(id) { return this._tx('readwrite', (s) => s.delete(id)); },
  leeren() { return this._tx('readwrite', (s) => s.clear()); }
};

/* --- Farbmodus ---------------------------------------------------------- */
const MODUS_SCHLUESSEL = 'coaching.modus';
const Modus = {
  gewaehlt() {
    try { return localStorage.getItem(MODUS_SCHLUESSEL) || 'system'; } catch (e) { return 'system'; }
  },
  anwenden() {
    const wahl = this.gewaehlt();
    const dunkel = wahl === 'dunkel' || (wahl === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
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
  }
};

/* --- Zustand und Stammdaten --------------------------------------------- */
const Coach = { uebungen: {}, ausdauer: new Set(), liste: [], gruppen: [] };

const ZIELNAMEN = { fett: 'Fett verlieren', muskel: 'Muskeln aufbauen', fitness: 'Fitter & gesünder' };
const uebungsName = (id) => Coach.uebungen[id] || id;

/* --- Auswertung eines Berichts ------------------------------------------ */
/** Stichtag ist der Tag, an dem der Klient die Datei erstellt hat. */
const stichtag = (b) => textAusDatum(new Date(b.erstellt));
const tagVon = (b, datum) => (b.tage && b.tage[datum]) || null;

function gewichtsreihe(b) {
  return Object.keys(b.tage || {}).sort()
    .filter((d) => b.tage[d].gewicht != null)
    .map((d) => ({ datum: d, wert: b.tage[d].gewicht }));
}

function gewichtMittel(datum, reihe) {
  const von = tageVerschieben(datum, -6);
  const fenster = reihe.filter((r) => r.datum >= von && r.datum <= datum);
  return fenster.length ? fenster.reduce((a, r) => a + r.wert, 0) / fenster.length : null;
}

function tagesSumme(b, datum) {
  const s = { kcal: 0, e: 0 };
  const t = tagVon(b, datum);
  if (t && t.essen) t.essen.forEach((x) => { s.kcal += x.kcal; s.e += x.e; });
  return s;
}

function workoutsZwischen(b, von, bis) {
  return (b.workouts || []).filter((w) => w.datum >= von && w.datum <= bis);
}

function rekorde(b) {
  const best = new Map();
  (b.workouts || []).forEach((w) => w.uebungen.forEach((u) => u.saetze.forEach((s) => {
    if (!s.fertig || !s.kg) return;
    const wert = e1rm(s.kg, s.wdh);
    const alt = best.get(u.uid);
    if (!alt || wert > alt.wert) best.set(u.uid, { wert, kg: s.kg, wdh: s.wdh, datum: w.datum });
  })));
  return [...best.entries()].sort((a, c) => c[1].wert - a[1].wert);
}

function gewohnheitsquote(b, tage) {
  const anzahl = (b.gewohnheiten || []).length;
  if (!anzahl) return null;
  let erledigt = 0;
  for (let i = 0; i < tage; i++) {
    const t = tagVon(b, tageVerschieben(stichtag(b), -i));
    if (t && t.gewohnheiten) erledigt += Object.keys(t.gewohnheiten).length;
  }
  // Gelöschte Gewohnheiten können noch als erledigt in alten Tagen stehen.
  return Math.min(1, erledigt / (anzahl * tage));
}

function tageReihe(b, anzahl) {
  return Array.from({ length: anzahl }, (_, i) => tageVerschieben(stichtag(b), i - anzahl + 1));
}

function vorzeichen(n, stellen = 1) {
  return `${n > 0 ? '+' : n < 0 ? '−' : '±'}${zahl(Math.abs(n), stellen)}`;
}

function alterText(tage) {
  if (tage <= 0) return 'heute';
  if (tage === 1) return 'gestern';
  return `vor ${tage} Tagen`;
}

/* --- Handlungsbedarf ---------------------------------------------------- */
// Prüft einen Bericht auf Punkte, bei denen der Coach eingreifen sollte.
// Stufe 2 = dringend, Stufe 1 = beobachten. Bezugstag ist der Stichtag der
// Datei, nur die Aktualität der Datei selbst misst sich am heutigen Tag.
const kuerzen = (t, n = 80) => (t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t);

function handlungsbedarf(b) {
  const p = b.profil;
  const z = b.ziele || {};
  const tag = stichtag(b);
  const punkte = [];
  const add = (stufe, text) => punkte.push({ stufe, text });
  const dabei = p.start ? tageZwischen(p.start, tag) : 99;
  const letzte7 = tageReihe(b, 7);

  // Aktualität der Datei
  const alter = tageZwischen(tag, heuteText());
  if (alter > 10) add(2, `Seit ${alter} Tagen keine neue Datei — nachfragen, wie es läuft`);
  else if (alter >= 7) add(1, `Letzte Datei ${alterText(alter)}`);

  // Training
  const ws = b.workouts || [];
  const woche = workoutsZwischen(b, tageVerschieben(tag, -6), tag);
  const letztesTraining = ws.length ? ws.map((w) => w.datum).sort().pop() : null;
  if (!letztesTraining) { if (dabei >= 7) add(2, 'Noch kein Training eingetragen'); }
  else if (tageZwischen(letztesTraining, tag) >= 10) add(2, `Seit ${tageZwischen(letztesTraining, tag)} Tagen kein Training`);
  else if (p.tage && woche.length < p.tage * 0.5) add(1, `Nur ${woche.length} von ${p.tage} Trainings in den letzten 7 Tagen`);

  // RIR der letzten 14 Tage
  const rirWerte = [];
  workoutsZwischen(b, tageVerschieben(tag, -13), tag).forEach((w) => w.uebungen.forEach((u) =>
    u.saetze.forEach((s) => { if (s.rir != null) rirWerte.push(s.rir); })));
  if (rirWerte.length >= 6) {
    const anteilNull = rirWerte.filter((x) => x === 0).length / rirWerte.length;
    const schnitt = rirWerte.reduce((a, x) => a + x, 0) / rirWerte.length;
    if (anteilNull > 0.4) add(1, `Trainiert oft bis zum Muskelversagen (${Math.round(anteilNull * 100)} % der Sätze mit RIR 0)`);
    else if (schnitt >= 4) add(1, `Trainiert zu leicht (RIR Ø ${zahl(schnitt, 1)})`);
  }

  // Check-in
  const ci = (b.checkins || []).slice(-1)[0];
  if (!ci) { if (dabei >= 8) add(1, 'Noch kein Check-in gesendet'); }
  else {
    const seit = tageZwischen(ci.datum, tag);
    if (seit >= 10) add(1, `Letzter Check-in vor ${seit} Tagen`);
    if (seit <= 8) {
      if (ci.fragen) add(2, `Frage im Check-in: „${kuerzen(ci.fragen)}“`);
      if (ci.probleme) add(1, `Schwierigkeiten: „${kuerzen(ci.probleme)}“`);
      const bw = ci.bewertung || {};
      const warn = [];
      if (bw.stress >= 4) warn.push(`Stress ${bw.stress}/5`);
      if (bw.energie && bw.energie <= 2) warn.push(`Energie ${bw.energie}/5`);
      if (bw.motivation && bw.motivation <= 2) warn.push(`Motivation ${bw.motivation}/5`);
      if (bw.schlaf && bw.schlaf <= 2) warn.push(`Schlaf ${bw.schlaf}/5`);
      if (bw.hunger >= 4) warn.push(`Hunger ${bw.hunger}/5`);
      if (warn.length) add(warn.length >= 2 ? 2 : 1, `Check-in: ${warn.join(' · ')}`);
      const treue = [];
      if (ci.treueTraining != null && ci.treueTraining <= 50) treue.push(`Training ${ci.treueTraining} %`);
      if (ci.treueErnaehrung != null && ci.treueErnaehrung <= 50) treue.push(`Ernährung ${ci.treueErnaehrung} %`);
      if (treue.length) add(1, `Wenig nach Plan: ${treue.join(', ')}`);
    }
  }

  // Gewicht im Verhältnis zum Ziel
  const reihe = gewichtsreihe(b);
  const jetzt = gewichtMittel(tag, reihe);
  const vorwoche = gewichtMittel(tageVerschieben(tag, -7), reihe);
  const vor3 = gewichtMittel(tageVerschieben(tag, -21), reihe);
  if (jetzt == null && (p.ziel === 'fett' || p.ziel === 'muskel') && dabei >= 7) add(1, 'Kein Gewicht in den letzten 7 Tagen eingetragen');
  if (jetzt != null && vorwoche != null) {
    const d = jetzt - vorwoche;
    if (p.ziel === 'fett' && d > 0.3) add(1, `Gewicht steigt (${vorzeichen(d)} kg zur Vorwoche) — Ziel Fettabbau`);
    else if (p.ziel === 'fett' && d < -0.012 * vorwoche) add(1, `Verliert sehr schnell (${vorzeichen(d)} kg in einer Woche)`);
    else if (p.ziel === 'muskel' && d < -0.3) add(1, `Gewicht sinkt (${vorzeichen(d)} kg zur Vorwoche) — Ziel Muskelaufbau`);
  }
  if (p.ziel === 'fett' && jetzt != null && vor3 != null && jetzt - vor3 > -0.2) add(1, 'Gewicht seit 3 Wochen ohne Fortschritt');

  // Ernährung
  const essTage = letzte7.filter((d) => { const t = tagVon(b, d); return t && t.essen && t.essen.length; });
  if (essTage.length < 3) add(1, `Ernährung nur an ${essTage.length} von 7 Tagen erfasst`);
  else {
    const kcal = essTage.reduce((a, d) => a + tagesSumme(b, d).kcal, 0) / essTage.length;
    const e = essTage.reduce((a, d) => a + tagesSumme(b, d).e, 0) / essTage.length;
    if (z.kcal && Math.abs(kcal - z.kcal) / z.kcal > 0.15) {
      add(1, `Kalorien Ø ${zahl(kcal)} statt ${zahl(z.kcal)} (${vorzeichen(Math.round((kcal / z.kcal - 1) * 100), 0)} %)`);
    }
    if (z.e && e < z.e * 0.8) add(1, `Eiweiß Ø ${zahl(e)} g statt ${zahl(z.e)} g`);
  }

  // Schlaf, Schritte, Gewohnheiten
  const schlaf = letzte7.map((d) => schlafDauer((tagVon(b, d) || {}).schlaf)).filter((x) => x);
  if (schlaf.length >= 3) {
    const s = schlaf.reduce((a, x) => a + x, 0) / schlaf.length;
    if (s < 6) add(s < 5 ? 2 : 1, `Schlaf Ø ${zahl(s, 1)} Std. (Ziel ${zahl(p.schlafziel, 1)})`);
  }
  const schritte = letzte7.map((d) => (tagVon(b, d) || {}).schritte).filter((x) => x);
  if (schritte.length >= 3 && p.schrittziel) {
    const s = schritte.reduce((a, x) => a + x, 0) / schritte.length;
    if (s < p.schrittziel * 0.6) add(1, `Schritte Ø ${zahl(s)} (Ziel ${zahl(p.schrittziel)})`);
  }
  const quote = gewohnheitsquote(b, 7);
  if (quote != null && quote < 0.4) add(1, `Gewohnheiten nur zu ${Math.round(quote * 100)} % erledigt`);

  return punkte.sort((a, c) => c.stufe - a.stufe);
}

const bedarfStufe = (punkte) => punkte.reduce((m, x) => Math.max(m, x.stufe), 0);
const istErledigt = (eintrag) => eintrag.erledigt === eintrag.bericht.erstellt;

/* --- Import ------------------------------------------------------------- */
async function dateienEinlesen(dateien) {
  let neu = 0, ersetzt = 0, aelter = 0, fehler = 0;
  for (const datei of dateien) {
    try {
      const b = JSON.parse(await datei.text());
      if (b.app !== 'coaching-bericht' || !b.profil || !b.profil.id) throw new Error('Keine Fortschrittsdatei');
      const alt = await Klienten.holen(b.profil.id);
      // Eine ältere Datei darf einen neueren Stand nicht überschreiben.
      if (alt && alt.bericht.erstellt > b.erstellt) { aelter++; continue; }
      await Klienten.speichern({ id: b.profil.id, name: b.profil.name, empfangen: Date.now(), bericht: b });
      if (alt) ersetzt++; else neu++;
    } catch (e) {
      console.warn(datei.name, e);
      fehler++;
    }
  }
  const teile = [];
  if (neu) teile.push(`${neu} neu`);
  if (ersetzt) teile.push(`${ersetzt} aktualisiert`);
  if (aelter) teile.push(`${aelter} älter als vorhanden, übersprungen`);
  if (fehler) teile.push(`${fehler} keine Fortschrittsdatei`);
  toast(teile.join(' · ') || 'Nichts eingelesen');
  zeichnen();
}

/* --- Übersicht ---------------------------------------------------------- */
async function zeichnen() {
  const inhalt = document.getElementById('inhalt');
  const liste = (await Klienten.alle()).sort((a, c) => c.bericht.erstellt.localeCompare(a.bericht.erstellt));
  document.getElementById('untertitel').textContent =
    liste.length ? `${liste.length} ${liste.length === 1 ? 'Klient' : 'Klienten'}` : 'Coach-Ansicht';
  inhalt.replaceChildren();

  const oeffnen = knopf('Fortschrittsdatei öffnen', null, () => document.getElementById('datei').click(), 'plus');
  oeffnen.style.marginBottom = '16px';
  inhalt.append(oeffnen);

  if (!liste.length) {
    const k = karte('So funktioniert’s', 'checkin');
    [
      'Dein Klient tippt in seiner App unter Fortschritt oder beim Check-in auf „Fortschritt an Coach senden“.',
      'Die Datei kommt per WhatsApp oder Mail bei dir an. Speichere sie auf deinem Gerät.',
      'Hier auf „Fortschrittsdatei öffnen“ tippen und die Datei wählen — fertig. Eine neuere Datei desselben Klienten ersetzt die alte.'
    ].forEach((t, i) => {
      const z = el('div', 'schritt');
      z.append(el('div', 'schritt__nr', String(i + 1)), el('div', 'schritt__text', t));
      k.append(z);
    });
    inhalt.append(k);
  }

  if (liste.length) {
    inhalt.append(bedarfKarte(liste));
    inhalt.append(abschnitt('Alle Klienten'));
  }
  liste.forEach((eintrag) => inhalt.append(klientKarte(eintrag)));

  const h = el('div', 'hinweis');
  h.style.marginTop = '8px';
  h.append(el('div', 'hinweis__titel', 'Gesundheitsdaten'));
  h.append(el('p', null, 'Die Dateien enthalten Gesundheitsdaten deiner Klienten. Sie liegen nur auf diesem Gerät. Sperre es mit Code, gib es nicht weiter und lösche einen Klienten, sobald das Coaching endet.'));
  inhalt.append(h);
}

// Liste oben in der Übersicht: wer braucht jetzt Aufmerksamkeit? Dringendes
// zuerst, dann nach Anzahl der Punkte. Als erledigt markierte Klienten
// tauchen erst mit der nächsten Datei wieder auf.
function bedarfKarte(liste) {
  const k = karte('Handlungsbedarf', 'checkin');
  const offen = [];
  let erledigt = 0;
  liste.forEach((eintrag) => {
    const punkte = handlungsbedarf(eintrag.bericht);
    if (!punkte.length) return;
    if (istErledigt(eintrag)) { erledigt++; return; }
    offen.push({ eintrag, punkte, stufe: bedarfStufe(punkte) });
  });
  offen.sort((a, c) => c.stufe - a.stufe || c.punkte.length - a.punkte.length);
  if (!offen.length) {
    k.append(el('p', 'leise', 'Alles im grünen Bereich — gerade braucht niemand besondere Aufmerksamkeit. 👍'));
  }
  offen.forEach(({ eintrag, punkte, stufe }) => {
    const p = eintrag.bericht.profil;
    const z = el('button', 'zeile'); z.type = 'button';
    z.append(el('div', `zeile__ikon bedarf--${stufe}`, (p.name || '?').slice(0, 2).toUpperCase()));
    const t = el('div', 'zeile__text');
    const titel = el('div', 'zeile__titel', p.name || 'Ohne Namen');
    titel.append(el('span', `marke ${stufe === 2 ? 'marke--dringend' : 'marke--warn'}`, stufe === 2 ? 'Dringend' : 'Beobachten'));
    t.append(titel);
    punkte.slice(0, 3).forEach((x) => t.append(el('div', 'zeile__meta bedarf-punkt', x.text)));
    if (punkte.length > 3) t.append(el('div', 'zeile__meta', `+ ${punkte.length - 3} weitere`));
    const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
    z.append(t, pf);
    z.onclick = () => klientBlatt(eintrag);
    k.append(z);
  });
  if (erledigt) k.append(el('div', 'fusstext', `${erledigt} ${erledigt === 1 ? 'Klient' : 'Klienten'} als erledigt markiert — bis zur nächsten Datei ausgeblendet.`));
  return k;
}

function klientKarte(eintrag) {
  const b = eintrag.bericht;
  const p = b.profil;
  const tag = stichtag(b);
  const alter = tageZwischen(tag, heuteText());
  const reihe = gewichtsreihe(b);
  const mittel = gewichtMittel(tag, reihe);
  const woche = workoutsZwischen(b, tageVerschieben(tag, -6), tag);
  const letzter = (b.checkins || []).slice(-1)[0];

  const k = el('button', 'karte karte--klick klient');
  k.type = 'button';
  const kopf = el('div', 'klient__kopf');
  kopf.append(el('div', 'zeile__ikon', (p.name || '?').slice(0, 2).toUpperCase()));
  const text = el('div', 'zeile__text');
  text.append(el('div', 'klient__name', p.name || 'Ohne Namen'),
              el('div', 'zeile__meta', `${ZIELNAMEN[p.ziel] || ''} · Stand ${alterText(alter)}`));
  kopf.append(text);
  if (alter > 10) kopf.append(el('span', 'marke marke--warn', 'veraltet'));
  const pf = el('span', 'zeile__pfeil'); pf.innerHTML = ikon('weiter');
  kopf.append(pf);
  k.append(kopf);

  const werte = el('div', 'werte werte--3');
  const diff = mittel != null ? mittel - p.gewicht : null;
  const gut = diff != null && ((p.ziel === 'fett' && diff < 0) || (p.ziel === 'muskel' && diff > 0));
  werte.append(
    wertKachel('Gewicht Ø', mittel != null ? zahl(mittel, 1) : '–', 'kg', diff != null ? `${vorzeichen(diff)} kg` : null, gut),
    wertKachel('Training 7 T.', `${woche.length}/${p.tage}`),
    wertKachel('Check-in', letzter ? datumKurz(letzter.datum) : '–'));
  k.append(werte);
  k.onclick = () => klientBlatt(eintrag);
  return k;
}

/* --- Klienten-Detail ---------------------------------------------------- */
function klientBlatt(eintrag) {
  const b = eintrag.bericht;
  const p = b.profil;
  const tag = stichtag(b);
  blattOeffnen(p.name || 'Klient', (inhalt, schliessen) => {
    const reihe = gewichtsreihe(b);
    const mittel = gewichtMittel(tag, reihe);
    const z = b.ziele || {};

    inhalt.append(el('p', 'leise',
      `${ZIELNAMEN[p.ziel] || ''} · ${p.alter} J. · ${p.groesse} cm · ${p.tage}× Training/Woche (${p.ort === 'zuhause' ? 'zuhause' : 'Studio'}) · dabei seit ${datumKurz(p.start)}${datumAusText(p.start).getFullYear()} · Datei vom ${datumLang(tag)}`));

    // Handlungsbedarf
    const punkte = handlungsbedarf(b);
    const kb = karte('Handlungsbedarf', 'checkin');
    if (!punkte.length) kb.append(el('p', 'leise', 'Nichts Auffälliges — läuft nach Plan. 👍'));
    else {
      const ul = el('ul', 'bedarf-liste');
      punkte.forEach((x) => ul.append(el('li', `bedarf-liste__punkt bedarf-liste__punkt--${x.stufe}`, x.text)));
      kb.append(ul);
      const knopfErledigt = () => knopf(istErledigt(eintrag) ? 'Wieder als offen markieren' : 'Als erledigt markieren',
        'knopf--zweit knopf--klein', async () => {
          eintrag.erledigt = istErledigt(eintrag) ? null : b.erstellt;
          await Klienten.speichern(eintrag);
          toast(eintrag.erledigt ? 'Erledigt — bis zur nächsten Datei ausgeblendet' : 'Wieder offen');
          umschalter.replaceWith(umschalter = knopfErledigt());
        }, 'haken');
      let umschalter = knopfErledigt();
      kb.append(umschalter);
    }
    const antworten = knopf(`Antwort an ${p.name || 'Klient'} schreiben`, null, () => antwortBlatt(eintrag), 'senden');
    antworten.style.marginTop = '12px';
    kb.append(antworten);
    const gesendet = eintrag.antworten || [];
    if (gesendet.length) {
      const letzte = gesendet[gesendet.length - 1];
      kb.append(el('div', 'fusstext', `Zuletzt geantwortet am ${datumLang(textAusDatum(new Date(letzte.erstellt)))}${letzte.nachricht ? ` · „${kuerzen(letzte.nachricht, 60)}“` : ''}`));
    }
    inhalt.append(kb);

    // Kennzahlen
    const werte = el('div', 'werte');
    werte.style.marginBottom = '14px';
    const diff = mittel != null ? mittel - p.gewicht : null;
    const gut = diff != null && ((p.ziel === 'fett' && diff < 0) || (p.ziel === 'muskel' && diff > 0));
    const quote = gewohnheitsquote(b, 30);
    werte.append(
      wertKachel('Gewicht Ø 7 Tage', mittel != null ? zahl(mittel, 1) : '–', 'kg', diff != null ? `${vorzeichen(diff)} kg seit Start (${zahl(p.gewicht, 1)})` : null, gut),
      wertKachel('Trainings gesamt', zahl((b.workouts || []).length), null, `${workoutsZwischen(b, tageVerschieben(tag, -6), tag).length} in den letzten 7 Tagen`),
      wertKachel('Gewohnheiten', quote != null ? Math.round(quote * 100) : '–', '%', 'letzte 30 Tage'),
      wertKachel('Check-ins', zahl((b.checkins || []).length), null, (b.checkins || []).length ? `zuletzt ${datumKurz(b.checkins[b.checkins.length - 1].datum)}` : null));
    inhalt.append(werte);

    // Gewicht
    const kg = karte('Gewicht', 'fortschritt');
    if (reihe.length >= 2) {
      const glatt = reihe.map((r) => ({ datum: r.datum, wert: gewichtMittel(r.datum, reihe) }));
      kg.append(liniendiagramm(reihe, { glatt, label: `Gewichtsverlauf von ${p.name}` }));
      const leg = el('div', 'legende');
      leg.innerHTML = '<span><i style="background:var(--accent-ink)"></i>7-Tage-Durchschnitt</span><span><i style="background:var(--ink-soft);opacity:.55"></i>Tageswerte</span>';
      kg.append(leg);
    } else kg.append(el('p', 'leise', 'Noch zu wenige Messungen.'));
    inhalt.append(kg);

    // Ernährung, Schritte, Schlaf — 14 Tage
    const tage14 = tageReihe(b, 14);
    const etikett = (d) => String(datumAusText(d).getDate());
    const kk = karte('Kalorien · 14 Tage', 'ernaehrung', z.kcal ? `Ziel ${zahl(z.kcal)}` : null);
    kk.append(saeulendiagramm(tage14.map((d) => ({ label: etikett(d), wert: Math.round(tagesSumme(b, d).kcal) })),
      { ziel: z.kcal, label: 'Kalorien der letzten 14 Tage' }));
    inhalt.append(kk);
    const ke = karte('Eiweiß · 14 Tage', 'ernaehrung', z.e ? `Ziel ${zahl(z.e)} g` : null);
    ke.append(saeulendiagramm(tage14.map((d) => ({ label: etikett(d), wert: Math.round(tagesSumme(b, d).e) })),
      { ziel: z.e, label: 'Eiweiß der letzten 14 Tage', farbe: 'var(--c-eiweiss)' }));
    inhalt.append(ke);
    const ks = karte('Schritte · 14 Tage', 'schritte', `Ziel ${zahl(p.schrittziel)}`);
    ks.append(saeulendiagramm(tage14.map((d) => ({ label: etikett(d), wert: (tagVon(b, d) || {}).schritte || 0 })),
      { ziel: p.schrittziel, label: 'Schritte der letzten 14 Tage', farbe: 'var(--c-schritte)' }));
    inhalt.append(ks);
    const kl = karte('Schlaf · 14 Tage', 'schlaf', `Ziel ${zahl(p.schlafziel, 1)} Std.`);
    kl.append(saeulendiagramm(tage14.map((d) => ({ label: etikett(d), wert: schlafDauer((tagVon(b, d) || {}).schlaf) || 0 })),
      { ziel: p.schlafziel, label: 'Schlafstunden der letzten 14 Tage', farbe: 'var(--c-schlaf)', stellen: 1 }));
    inhalt.append(kl);

    // Training
    const kv = karte('Trainingsvolumen · 8 Wochen', 'training');
    const wochen = Array.from({ length: 8 }, (_, i) => wochenstart(tageVerschieben(tag, (i - 7) * 7)));
    kv.append(saeulendiagramm(wochen.map((w) => ({
      label: datumKurz(w),
      wert: Math.round(workoutsZwischen(b, w, tageVerschieben(w, 6)).reduce((a, x) => a + volumen(x), 0))
    })), { label: 'Trainingsvolumen in kg pro Woche' }));
    inhalt.append(kv);

    const kt = karte('Letzte Trainings', 'training');
    const ws = [...(b.workouts || [])].reverse().slice(0, 12);
    if (!ws.length) kt.append(el('p', 'leise', 'Noch kein Training eingetragen.'));
    ws.forEach((w) => {
      const det = el('details', 'aufklapp');
      const sum = el('summary');
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', w.deload ? `${w.name} · Deload` : w.name),
               el('div', 'zeile__meta', `${datumMittel(w.datum)} · ${dauerText(w.ende - w.start)} · ${zahl(volumen(w))} kg${w.rekorde && w.rekorde.length ? ` · ${w.rekorde.length} PR` : ''}`));
      sum.append(t);
      const body = el('div');
      w.uebungen.forEach((u) => {
        const zeile = el('div');
        zeile.append(el('b', null, uebungsName(u.uid) + ': '),
          document.createTextNode(Coach.ausdauer.has(u.uid) ? u.saetze.map((s) => `${zahl(s.wdh)} Min.`).join(' · ')
            : u.saetze.map((s) => `${s.kg ? zahl(s.kg, s.kg % 1 ? 1 : 0) + '×' : ''}${s.wdh}${s.rir != null ? ` @${zahl(s.rir)}` : ''}`).join(' · ')));
        body.append(zeile);
      });
      if (w.notiz) body.append(el('p', null, `Notiz: ${w.notiz}`));
      det.append(sum, body);
      kt.append(det);
    });
    if (ws.some((w) => w.uebungen.some((u) => u.saetze.some((s) => s.rir != null)))) {
      kt.append(el('div', 'fusstext', 'kg×Wdh. @RIR — RIR = Wiederholungen in Reserve (0 = Muskelversagen).'));
    }
    inhalt.append(kt);

    const kr = karte('Bestwerte', 'pokal');
    const best = rekorde(b);
    if (!best.length) kr.append(el('p', 'leise', 'Noch keine Bestwerte.'));
    best.slice(0, 10).forEach(([uid, r]) => {
      const zeile = el('div', 'zeile'); zeile.style.cursor = 'default';
      const t = el('div', 'zeile__text');
      t.append(el('div', 'zeile__titel', uebungsName(uid)), el('div', 'zeile__meta', `${zahl(r.kg, r.kg % 1 ? 1 : 0)} kg × ${r.wdh} · ${datumKurz(r.datum)}`));
      zeile.append(t, el('div', 'zeile__rechts', `${zahl(r.wert, 1)} kg`));
      kr.append(zeile);
    });
    inhalt.append(kr);

    // Körpermaße
    const m = [...(b.messungen || [])].sort((a, c) => a.datum.localeCompare(c.datum));
    if (m.length) {
      const km = karte('Körpermaße', 'liste');
      MASSE.forEach(([id, name]) => {
        const mit = m.filter((x) => x[id] != null);
        if (!mit.length) return;
        const erst = mit[0][id], letzt = mit[mit.length - 1][id];
        const zeile = el('div', 'zeile'); zeile.style.cursor = 'default';
        const t = el('div', 'zeile__text');
        t.append(el('div', 'zeile__titel', name),
                 el('div', 'zeile__meta', mit.length > 1 ? `Start ${zahl(erst, 1)} cm · ${vorzeichen(letzt - erst)} cm` : `gemessen ${datumKurz(mit[0].datum)}`));
        zeile.append(t, el('div', 'zeile__rechts', `${zahl(letzt, 1)} cm`));
        km.append(zeile);
      });
      inhalt.append(km);
    }

    // Check-ins
    const kc = karte('Check-ins', 'checkin');
    const cs = [...(b.checkins || [])].reverse();
    if (!cs.length) kc.append(el('p', 'leise', 'Noch kein Check-in gesendet.'));
    cs.forEach((c, i) => {
      const det = el('details', 'aufklapp');
      if (i === 0) det.open = true;
      const sum = el('summary');
      sum.append(el('div', 'zeile__titel', datumLang(c.datum)));
      const body = el('div');
      body.append(el('div', 'vorschau-text', c.text));
      det.append(sum, body);
      kc.append(det);
    });
    inhalt.append(kc);

    // Fotos
    const fotos = (b.fotos || []).slice().sort((a, c) => a.datum.localeCompare(c.datum));
    if (fotos.length) {
      const kf = karte('Fortschrittsfotos', 'kamera');
      const daten = [...new Set(fotos.map((f) => f.datum))];
      if (daten.length >= 2) {
        const erst = fotos.filter((f) => f.datum === daten[0]);
        const letzt = fotos.filter((f) => f.datum === daten[daten.length - 1]);
        const pose = POSEN.map(([id]) => id).find((id) => erst.some((f) => f.pose === id) && letzt.some((f) => f.pose === id));
        if (pose) {
          const v = el('div', 'vergleich');
          [[erst, daten[0]], [letzt, daten[daten.length - 1]]].forEach(([fs, datum]) => {
            const fig = el('figure');
            const img = el('img'); img.alt = `${pose}, ${datumKurz(datum)}`;
            img.src = fs.find((f) => f.pose === pose).bild;
            fig.append(img, el('figcaption', null, datumMittel(datum)));
            v.append(fig);
          });
          kf.append(el('div', 'feld__label', 'Vorher – Nachher'), v, el('hr', 'trenner'));
        }
      }
      [...daten].reverse().forEach((datum) => {
        kf.append(el('div', 'feld__label', datumLang(datum)));
        const g = el('div', 'fotos');
        g.style.marginBottom = '12px';
        fotos.filter((f) => f.datum === datum).forEach((f) => {
          const box = el('div', 'foto');
          const img = el('img'); img.src = f.bild; img.alt = `${f.pose}, ${datumKurz(datum)}`; img.loading = 'lazy';
          box.append(img, el('span', 'foto__label', (POSEN.find((x) => x[0] === f.pose) || [0, f.pose])[1]));
          g.append(box);
        });
        kf.append(g);
      });
      inhalt.append(kf);
    }

    // Ziele und Plan
    const kz = karte('Ziele & Plan', 'liste');
    kz.append(el('p', 'leise', `${zahl(z.kcal)} kcal · ${zahl(z.e)} g Eiweiß · ${zahl(z.kh)} g KH · ${zahl(z.f)} g Fett${z.manuell ? ' (manuell gesetzt)' : ''}`));
    ((b.plan && b.plan.tage) || []).forEach((t) => {
      const zeile = el('div', 'zeile'); zeile.style.cursor = 'default';
      const text = el('div', 'zeile__text');
      text.append(el('div', 'zeile__titel', t.name), el('div', 'zeile__meta', t.uebungen.map((u) => `${uebungsName(u.uid)} ${Coach.ausdauer.has(u.uid) ? `${u.wdh} Min.` : `${u.saetze}×${u.wdh}${u.rir ? ` RIR ${u.rir}` : ''}`}`).join(' · ')));
      zeile.append(text);
      kz.append(zeile);
    });
    inhalt.append(kz);

    const weg = knopf('Klient löschen', 'knopf--gefahr', async () => {
      if (!confirm(`Alle Daten von ${p.name} auf diesem Gerät löschen?`)) return;
      await Klienten.loeschen(eintrag.id);
      schliessen();
      toast('Klient gelöscht');
    });
    weg.style.marginTop = '8px';
    inhalt.append(weg);
  }, { beimSchliessen: zeichnen });
}

/* --- Antwort an den Klienten ------------------------------------------- */
// Der Coach schreibt eine Nachricht und passt Ziele und Plan an. Daraus wird
// eine Antwortdatei, die der Klient in seiner App öffnet und übernimmt.
const kopie = (x) => JSON.parse(JSON.stringify(x));

function planUebungNeu(id) {
  const u = Coach.liste.find((x) => x.id === id) || {};
  if (u.ausdauer) return { uid: id, saetze: 1, wdh: '20', pause: 0, notiz: '' };
  return { uid: id, saetze: 3, wdh: u.zeit ? '30–45' : '8–12', pause: 90, notiz: '', ...(u.zeit ? {} : { rir: '2–3' }) };
}

function uebungAuswahl(beiWahl) {
  const sel = el('select', 'eingabe');
  sel.setAttribute('aria-label', 'Übung hinzufügen');
  sel.append(new Option('+ Übung hinzufügen …', ''));
  Coach.gruppen.forEach((g) => {
    const og = el('optgroup'); og.label = g;
    Coach.liste.filter((u) => u.gruppe === g).forEach((u) => og.append(new Option(u.name, u.id)));
    sel.append(og);
  });
  sel.onchange = () => { if (sel.value) beiWahl(sel.value); sel.value = ''; };
  return sel;
}

function antwortBlatt(eintrag) {
  const b = eintrag.bericht;
  const p = b.profil;
  const zAlt = b.ziele || {};
  const plan = kopie(b.plan || { tage: [] });
  const planVorher = JSON.stringify(plan);
  const ziele = { kcal: zAlt.kcal, e: zAlt.e, kh: zAlt.kh, f: zAlt.f };
  let schrittziel = p.schrittziel;
  let nachricht = '';

  blattOeffnen(`Antwort an ${p.name || 'Klient'}`, (inhalt, schliessen, blatt) => {
    inhalt.append(el('p', 'leise', `Die Antwort geht als Datei an ${p.name || 'deinen Klienten'} — per WhatsApp oder Mail. In der App öffnet er sie unter Check-in → „Antwort vom Coach öffnen“ und übernimmt sie mit einem Tipp.`));

    const ci = (b.checkins || []).slice(-1)[0];
    if (ci && (ci.fragen || ci.probleme)) {
      const h = el('div', 'hinweis');
      h.append(el('div', 'hinweis__titel', `Aus dem Check-in vom ${datumKurz(ci.datum)}`));
      if (ci.fragen) h.append(el('p', null, `Frage: ${ci.fragen}`));
      if (ci.probleme) h.append(el('p', null, `Schwierig: ${ci.probleme}`));
      h.style.marginBottom = '14px';
      inhalt.append(h);
    }

    const kn = karte('Nachricht', 'senden');
    const t = el('textarea', 'eingabe');
    t.rows = 5;
    t.placeholder = 'Feedback zur Woche, Antwort auf Fragen, Fokus für die nächsten Tage …';
    t.oninput = () => { nachricht = t.value; };
    kn.append(t);
    inhalt.append(kn);

    // Ziele
    const kz = karte('Ziele', 'ernaehrung');
    const reihe1 = el('div', 'reihe');
    const reihe2 = el('div', 'reihe');
    [['kcal', 'Kalorien'], ['e', 'Eiweiß (g)'], ['kh', 'Kohlenh. (g)'], ['f', 'Fett (g)']].forEach(([id, name], i) => {
      const e = eingabe('text', ziele[id] != null ? String(ziele[id]) : '', { modus: 'numeric', beiAenderung: (v) => { const n = leseZahl(v); if (n != null && n >= 0) ziele[id] = Math.round(n); } });
      (i < 2 ? reihe1 : reihe2).append(feld(name, e));
    });
    const sz = eingabe('text', schrittziel != null ? String(schrittziel) : '', { modus: 'numeric', beiAenderung: (v) => { const n = leseZahl(v); if (n) schrittziel = Math.round(n); } });
    kz.append(reihe1, reihe2, feld('Schrittziel pro Tag', sz));
    inhalt.append(kz);

    // Plan
    const kp = karte('Trainingsplan', 'training');
    const planBox = el('div');
    const planZeichnen = () => {
      planBox.replaceChildren();
      if (!plan.tage.length) planBox.append(el('p', 'leise', 'Der Klient hat noch keinen Plan.'));
      plan.tage.forEach((tag) => {
        const kopf = el('div', 'feld__label', tag.name);
        kopf.style.marginTop = '10px';
        planBox.append(kopf);
        tag.uebungen.forEach((pu, i) => {
          const u = Coach.liste.find((x) => x.id === pu.uid) || {};
          const k = el('div', 'karte uebung-karte');
          const kk = el('div', 'uebung-karte__kopf');
          kk.append(el('div', 'uebung-karte__name', uebungsName(pu.uid)));
          const weg = el('button', 'ikon-knopf ikon-knopf--plain'); weg.type = 'button'; weg.innerHTML = ikon('muell');
          weg.setAttribute('aria-label', `${uebungsName(pu.uid)} entfernen`);
          weg.onclick = () => { tag.uebungen.splice(i, 1); planZeichnen(); };
          kk.append(weg);
          k.append(kk);
          const r = el('div', 'reihe');
          const w = eingabe('text', pu.wdh, { beiAenderung: (v) => { pu.wdh = v.trim() || pu.wdh; } });
          if (u.ausdauer) r.append(feld('Minuten', w));
          else {
            const sa = eingabe('text', String(pu.saetze), { modus: 'numeric', beiAenderung: (v) => { pu.saetze = Math.max(1, Math.min(10, leseZahl(v) || pu.saetze)); } });
            const pa = eingabe('text', String(pu.pause), { modus: 'numeric', beiAenderung: (v) => { const n = leseZahl(v); if (n != null) pu.pause = Math.max(0, n); } });
            r.append(feld('Sätze', sa), feld(u.zeit ? 'Sek.' : 'Wdh.', w));
            if (!u.zeit) r.append(feld('RIR', eingabe('text', pu.rir || '', { beiAenderung: (v) => { pu.rir = v.trim(); } })));
            r.append(feld('Pause', pa));
          }
          k.append(r);
          const n = eingabe('text', pu.notiz || '', { platzhalter: 'Notiz, z. B. „Tempo 3-1-1“', beiAenderung: (v) => { pu.notiz = v; } });
          n.setAttribute('aria-label', 'Notiz');
          k.append(n);
          planBox.append(k);
        });
        planBox.append(uebungAuswahl((id) => { tag.uebungen.push(planUebungNeu(id)); planZeichnen(); }));
      });
    };
    planZeichnen();
    kp.append(planBox);
    inhalt.append(kp);

    blattFuss(blatt, knopf('Antwort senden', null, () => {
      // Felder mit offener Eingabe zuerst übernehmen (beiAenderung feuert bei change)
      if (document.activeElement && document.activeElement.blur) document.activeElement.blur();
      const zieleGeaendert = ['kcal', 'e', 'kh', 'f'].some((k) => ziele[k] !== zAlt[k]);
      const planGeaendert = JSON.stringify(plan) !== planVorher;
      const schritteGeaendert = schrittziel !== p.schrittziel;
      const text = nachricht.trim();
      if (!text && !zieleGeaendert && !planGeaendert && !schritteGeaendert) { toast('Noch nichts geändert oder geschrieben'); return; }
      const antwort = {
        app: 'coaching-antwort', version: 1, erstellt: new Date().toISOString(),
        fuer: p.id, name: p.name, bezug: b.erstellt, nachricht: text,
        ...(zieleGeaendert ? { ziele } : {}),
        ...(schritteGeaendert ? { schrittziel } : {}),
        ...(planGeaendert ? { plan } : {})
      };
      const name = `antwort-${(p.name || 'klient').toLowerCase().replace(/[^a-z0-9äöüß]+/g, '-')}-${heuteText()}.json`;
      const datei = new File([JSON.stringify(antwort)], name, { type: 'application/json' });
      dateiTeilen(datei, 'Antwort vom Coach').then(async (ok) => {
        if (!ok) return;
        eintrag.antworten = [...(eintrag.antworten || []), { erstellt: antwort.erstellt, nachricht: text,
          ziele: zieleGeaendert, plan: planGeaendert }];
        eintrag.erledigt = b.erstellt;
        await Klienten.speichern(eintrag);
        toast(kannDateienTeilen(datei) ? 'Antwort gesendet' : 'Datei gespeichert — jetzt an den Klienten schicken');
        schliessen();
      });
    }, 'senden'));
  }, { beimSchliessen: zeichnen });
}

/* --- Einstellungen ------------------------------------------------------ */
function einstellungenBlatt() {
  blattOeffnen('Einstellungen', (inhalt, schliessen) => {
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
    inhalt.append(abschnitt('Daten'));
    inhalt.append(el('p', 'leise', 'Alle Klientendaten liegen nur in diesem Browser auf diesem Gerät. Es gibt keine Sicherung — die Originaldateien in WhatsApp oder Mail bleiben aber erhalten und lassen sich jederzeit erneut öffnen.'));
    inhalt.append(knopf('Alle Klienten löschen', 'knopf--gefahr', async () => {
      if (!confirm('Alle Klientendaten auf diesem Gerät löschen?')) return;
      await Klienten.leeren();
      schliessen();
      toast('Alle Klienten gelöscht');
    }));
    inhalt.append(el('p', 'fusstext mitte', 'Coach-Ansicht · Version 1.0'));
  }, { beimSchliessen: zeichnen });
}

/* --- Start -------------------------------------------------------------- */
async function starten() {
  Modus.anwenden();
  window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', () => { if (Modus.gewaehlt() === 'system') Modus.anwenden(); });

  try {
    const daten = await fetch('../daten/uebungen.json').then((r) => r.json());
    daten.uebungen.forEach((u) => { Coach.uebungen[u.id] = u.name; if (u.ausdauer) Coach.ausdauer.add(u.id); });
    Object.assign(Coach, { liste: daten.uebungen, gruppen: daten.gruppen });
  } catch (e) {
    console.warn('Übungsnamen nicht geladen — es erscheinen die Kennungen.', e);
  }

  const eingabeDatei = document.getElementById('datei');
  eingabeDatei.onchange = async () => {
    const dateien = [...eingabeDatei.files];
    eingabeDatei.value = '';
    if (dateien.length) await dateienEinlesen(dateien);
  };
  document.getElementById('einstellungen-auf').onclick = einstellungenBlatt;

  // Dateien auch per Ziehen und Ablegen annehmen — praktisch am Computer.
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => {
    e.preventDefault();
    const dateien = [...(e.dataTransfer && e.dataTransfer.files || [])];
    if (dateien.length) dateienEinlesen(dateien);
  });

  if (!('indexedDB' in window)) {
    document.getElementById('inhalt').append(leerzustand('Nicht unterstützt',
      'Dieser Browser kann keine Daten speichern. Bitte einen aktuellen Browser ohne privates Fenster verwenden.'));
    return;
  }
  await zeichnen();

  offlineUndUpdates('../sw.js');
}

starten();
