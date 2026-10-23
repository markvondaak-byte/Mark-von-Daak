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
const Coach = { uebungen: {}, ausdauer: new Set() };

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

  liste.forEach((eintrag) => inhalt.append(klientKarte(eintrag)));

  const h = el('div', 'hinweis');
  h.style.marginTop = '8px';
  h.append(el('div', 'hinweis__titel', 'Gesundheitsdaten'));
  h.append(el('p', null, 'Die Dateien enthalten Gesundheitsdaten deiner Klienten. Sie liegen nur auf diesem Gerät. Sperre es mit Code, gib es nicht weiter und lösche einen Klienten, sobald das Coaching endet.'));
  inhalt.append(h);
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
      t.append(el('div', 'zeile__titel', w.name),
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
