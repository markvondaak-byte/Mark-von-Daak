# Coaching — Klienten-App

Eine **PWA**: läuft im Browser, lässt sich auf dem Homescreen installieren und
funktioniert nach dem ersten Aufruf offline. Kein Framework, kein Build-Schritt,
keine Abhängigkeiten zur Laufzeit.

**Für Klienten im Fitness-Coaching** — deckt alles ab, was zwischen zwei
Coach-Kontakten passiert. Die App ist bewusst neutral: kein Personen- oder
Markenname, keine voreingestellten Kontaktdaten. WhatsApp-Nummer und E-Mail
des Coachs trägt der Klient bei der Einrichtung oder unter Einstellungen ein.
Sie ist von keiner anderen Seite aus verlinkt und nur über ihre Adresse
(`/coaching/`) erreichbar.

## Was die App kann

| Bereich | Inhalt |
|---|---|
| **Einrichtung** | Name, Ziel, Körperdaten, Aktivität, Trainingstage, Ort, Erfahrung. Daraus Kalorien- und Makroziele und ein fertiger Trainingsplan |
| **Heute** | Nächstes Training mit Start-Knopf, Ringe für Kalorien, Eiweiß, Schritte und Schlaf, Wasser, Gewohnheiten mit Serien, Check-in-Erinnerung, Tipp des Tages |
| **Training** | Plan (2–5 Tage, Studio oder Zuhause), Workout-Modus mit Satzprotokoll und RIR (Wiederholungen in Reserve: Ziel im Plan, Eintrag pro Satz, Rückmeldung und Tipp fürs nächste Mal), Vorwerten vom letzten Mal, **Steigerungsvorschlag** pro Übung (doppelte Progression mit RIR), **Aufwärmsätze**, **Deload-Wochen**, Pausentimer mit Vibration und Ton, Übung tauschen, Rekorde (geschätztes 1RM), Verlauf, Übungsbibliothek mit 161 Übungen in 10 Gruppen (inkl. Cardio und Mobilität), Gerät, Anleitung und Übungsvideo, Planeditor. Cardio läuft auf Zeit: eine Einheit in Minuten, ohne Sätze und Pausentimer |
| **Ernährung** | Tagebuch nach Mahlzeiten mit 280 Lebensmitteln und **Barcode-Scanner** (Open Food Facts), Rezeptportionen und Schnelleintrag, Makrobalken, Wasser, Tage blättern |
| **Meal Prep** | 18 Rezepte mit Nährwerten je Portion, Haltbarkeit, Portionsrechner. Ausgewählte Rezepte ergeben eine zusammengerechnete, abhakbare **Einkaufsliste** zum Teilen |
| **Check-in** | Täglich: Schritte, Schlaf (Uhrzeiten → Dauer, Erholung 1–5), Gewicht, Energie, Gewohnheiten. Wöchentlich: Fragebogen plus automatisch errechnete Wochenzahlen, als fertiger Text **per WhatsApp oder E-Mail an den Coach** — ohne hinterlegten Kontakt zum Teilen oder Kopieren |
| **Fortschritt** | Gewicht mit 7-Tage-Durchschnitt, Schritte und Schlaf der Woche, Trainingsvolumen über 8 Wochen, Bestwerte, Körpermaße, **Fortschrittsfotos** mit Vorher-Nachher-Vergleich |
| **Einstellungen** | Profil, Makros vom Coach überschreibbar, Coach-Kontakt, Check-in-Wochentag, Hell/Dunkel, Sicherung exportieren und einlesen |

## Berechnungen

- **Grundumsatz** nach Mifflin-St Jeor, mal Aktivitätsfaktor (1,3 bis 1,8).
- **Ziel:** Fett verlieren −20 %, Muskelaufbau +10 %, Fitness ±0 — nie unter
  den Grundumsatz.
- **Eiweiß** 2,0 / 1,8 / 1,6 g je kg, **Fett** 0,8 g je kg, Rest Kohlenhydrate.
  Ab BMI 30 rechnet die App mit dem Gewicht bei BMI 27, sonst würden die
  Mengen unrealistisch hoch.
- **1RM** nach Epley: Gewicht × (1 + Wiederholungen / 30).

Setzt der Coach unter Einstellungen eigene Werte, bleiben die stehen, bis
„Automatisch berechnen" gedrückt wird.

## Inhalte pflegen

```
daten/uebungen.json      Übungen: Gruppe, Gerät, Studio/Zuhause, Ausführung, Tipp
daten/lebensmittel.json  Nährwerte je 100 g und übliche Portion
daten/rezepte.json       Meal-Prep-Rezepte, Zutaten mit Menge für den Portionsrechner
```

Die Trainingsplan-Vorlagen und der Ersatz von Studio-Übungen fürs Training
zuhause stehen oben in `app.js` (`T`, `PLAN_VORLAGEN`, `ERSATZ_ZUHAUSE`). Die
Coach-Kontaktdaten sind bewusst nicht vorbelegt (`Speicher.leer()`).

Nach jeder Änderung `VERSION` in `sw.js` erhöhen — sonst sehen bestehende
Nutzer das Update nicht. Ist die Version erhöht, kommt das Update von selbst an:
Die App fragt beim Öffnen und beim Zurückholen in den Vordergrund nach, lädt den
neuen Stand im Hintergrund und lädt sich dann neu. Ist gerade ein Blatt offen,
ein Feld in Bearbeitung oder ein Check-in angefangen, erscheint stattdessen
„Neue Version bereit — tippen zum Aktualisieren“ (`offlineUndUpdates()` in
`gemeinsam.js`).

## Rezeptbilder

Jedes Rezept kann ein Foto haben (Feld `bild` in `daten/rezepte.json`); ohne
Foto zeigt die App einen ruhigen Platzhalter. Die Fotos sind KI-Bilder aus
Canva in einheitlichem Stil (schräg von oben, Tageslicht, heller Stein, 4:3).

- `build/rezeptbilder.json` — je Rezept die Canva-Medien-ID (falls schon
  erzeugt) und die exakte Bildbeschreibung, damit neue Bilder gleich aussehen.
- Originale als `<rezept-id>.jpg|png|webp` nach `build/rezeptbilder/` legen und
  `python3 coaching/build/rezeptbilder.py` ausführen: schneidet auf 4:3, rechnet
  auf 960 × 720 herunter (ca. 60–90 KB), legt sie unter `bilder/rezepte/` ab
  und trägt `bild` in `rezepte.json` ein. Danach `VERSION` in `sw.js` erhöhen.

Die Bilder werden nicht vorab in den Offline-Speicher geladen, sondern beim
ersten Ansehen — so bleibt die Installation klein.

## Übungsvideos

Jedes Übungsblatt zeigt oben ein Video. Hat die Übung einen eigenen Clip (Feld
`video` in `daten/uebungen.json`), spielt die App ihn ohne Ton in Schleife ab.
Sonst erscheint der Knopf „Übungsvideo auf YouTube ansehen“, der die YouTube-Suche
zur Übung öffnet — YouTube wird nicht eingebettet, es lädt also nichts von Google,
solange niemand tippt. Lässt sich ein eigener Clip nicht laden (z. B. offline),
fällt die App ebenfalls auf den Knopf zurück.

- Eigene Clips (Handyvideo genügt, am besten quer, 5–15 Sekunden, eine saubere
  Wiederholung von der Seite) als `<übungs-id>.mp4|mov|m4v|webm` nach
  `build/uebungsvideos/` legen und `python3 coaching/build/uebungsvideos.py`
  ausführen (braucht ffmpeg): kürzt auf höchstens 20 Sekunden, entfernt den Ton,
  rechnet auf 720 px Breite als MP4 (H.264) herunter (meist 0,5–2 MB), legt sie
  unter `videos/` ab und trägt `video` ein. Danach `VERSION` in `sw.js` erhöhen.
- Videos laufen am Service Worker vorbei direkt vom Netz (Browser laden sie
  stückweise), sie sind also nicht offline verfügbar.

## Icons

```bash
python3 coaching/build/build_icons.py
```

Neutrale Hantel in Orange, ohne Logo oder Wortmarke.

## Lokal ausprobieren

```bash
cd coaching && python3 -m http.server 8899
```

## Daten der Klienten

Alles liegt auf dem Gerät: Einträge im `localStorage`, Fotos (auf 1000 px
verkleinert) in IndexedDB. Kein Server, kein Konto — und damit auch kein
Zugriff des Coachs auf die Rohdaten. Was der Coach bekommt, schickt der Klient
selbst ab: den Check-in-Text und auf Wunsch die Fortschrittsdatei (siehe unten).
Sicherung und Umzug aufs neue Gerät über Einstellungen → Sicherung exportieren
(Fotos optional).

## Fortschritt der Klienten sehen: Coach-Ansicht

Unter **`/coaching/coach/`** liegt eine eigene Ansicht für den Coach — ebenfalls
ohne Server, installierbar als „Coach“.

1. Der Klient tippt in seiner App unter **Fortschritt** oder beim Check-in auf
   **„Fortschritt an Coach senden“**. Auf dem Handy öffnet sich das Teilen-Menü
   (WhatsApp, Mail …), am Computer wird die Datei gespeichert.
2. Der Coach speichert die Datei und öffnet sie in der Coach-Ansicht über
   **„Fortschrittsdatei öffnen“** (mehrere auf einmal oder per Ziehen und Ablegen).
3. Die Übersicht zeigt alle Klienten mit Gewichtstrend, Trainings der letzten
   7 Tage und letztem Check-in. Dateien älter als 10 Tage sind als „veraltet“
   markiert. Ein Tipp öffnet das Detail: Gewichtsverlauf, Kalorien, Eiweiß,
   Schritte und Schlaf der letzten 14 Tage, Trainingsvolumen, alle Trainings mit
   Sätzen, Bestwerte, Körpermaße, Check-in-Texte, Fotos mit Vorher-Nachher,
   Ziele und Plan.

### Antwort an den Klienten

Im Klienten-Detail öffnet **„Antwort an … schreiben“** ein Blatt mit
Nachricht, Zielen (Kalorien, Makros, Schritte) und dem Trainingsplan des
Klienten (Sätze, Wdh., RIR, Pause, Notiz ändern, Übungen entfernen oder aus der
Bibliothek hinzufügen). **„Antwort senden“** erzeugt die Datei
`antwort-<name>-<datum>.json` (`app: 'coaching-antwort'`, nur geänderte Teile)
und öffnet das Teilen-Menü; am Computer wird sie gespeichert. Danach gilt der
Klient als erledigt, und die Antwort steht im Detail.

Der Klient öffnet sie unter **Check-in → Wöchentlich** oder **Einstellungen →
Dein Coach** mit „Antwort vom Coach öffnen“, sieht eine Vorschau (Nachricht,
Ziele alt → neu, Planänderungen) und tippt **Übernehmen**. Ziele gelten dann als
manuell gesetzt, der Plan wird ersetzt, die Nachricht erscheint auf **Heute**,
bis sie als gelesen markiert ist. Eine Datei für einen anderen Klienten
(`fuer` ≠ `profil.id`) oder eine schon übernommene wird abgelehnt.

### Handlungsbedarf

Oben in der Übersicht listet die Karte **Handlungsbedarf** alle Klienten, um die
sich der Coach jetzt kümmern sollte — **Dringend** zuerst, dann **Beobachten**,
jeweils mit den konkreten Gründen (`handlungsbedarf()` in `coach/coach.js`).
Bezugstag ist der Tag, an dem die Datei erstellt wurde.

| Dringend | Beobachten |
|---|---|
| Datei älter als 10 Tage | Datei 7–10 Tage alt |
| Seit 10+ Tagen kein Training, noch nie trainiert | Weniger als die Hälfte der geplanten Trainings in 7 Tagen |
| Frage an den Coach im letzten Check-in | Schwierigkeiten im Check-in, Plantreue ≤ 50 % |
| Zwei oder mehr Warnwerte im Check-in (Stress ≥ 4, Energie/Motivation/Schlaf ≤ 2, Hunger ≥ 4) | Ein Warnwert im Check-in, kein Check-in seit 10 Tagen |
| Schlaf Ø unter 5 Std. | Schlaf Ø unter 6 Std., Schritte unter 60 % vom Ziel, Gewohnheiten unter 40 % |
| | Gewicht entgegen dem Ziel, mehr als 1,2 % pro Woche Verlust, 3 Wochen Stillstand beim Abnehmen, kein Gewicht eingetragen |
| | Ernährung an weniger als 3 von 7 Tagen erfasst, Kalorien mehr als 15 % neben dem Ziel, Eiweiß unter 80 % |
| | Mehr als 40 % der Sätze mit RIR 0 oder RIR Ø ab 4 (letzte 14 Tage) |

Im Klienten-Detail stehen alle Punkte oben. **„Als erledigt markieren“** blendet
den Klienten aus der Liste aus, bis seine nächste Fortschrittsdatei kommt.
Frage, Schwierigkeiten und Plantreue speichert die Klienten-App dafür seit
`coaching-v15` als eigene Felder im Check-in.

Jeder Klient hat eine zufällige ID (`profil.id`). Eine neuere Datei desselben
Klienten ersetzt die alte, eine ältere wird übersprungen. Die Berichte liegen in
IndexedDB (`coaching-coach`) auf dem Gerät des Coachs — es sind
Gesundheitsdaten: Gerät sperren, nicht weitergeben, Klienten löschen, wenn das
Coaching endet.

Die Datei enthält Profil, Ziele, Plan, Trainings, Tagesdaten, Körpermaße,
Gewohnheiten und Check-ins, auf Wunsch Fotos (auf 600 px verkleinert) — nicht
aber Einkaufsliste, „zuletzt gegessen“ oder ein laufendes Training.

Code: `coach/coach.js`. Helfer, die beide Seiten nutzen (DOM, Datum,
Diagramme, Blätter), stehen in `gemeinsam.js`.

## Rechtstexte

`recht/impressum.html`, `recht/datenschutz.html` und `recht/agb.html`
(Nutzungsbedingungen der kostenlosen App), verlinkt unter Einstellungen →
Rechtliches und offline verfügbar. Die Anbieterangaben stehen nur dort, nicht in
der App-Oberfläche. Bei Änderungen an Anschrift, Kontakt, Hosting oder neuen
Funktionen, die Daten übertragen, die Texte anpassen und das „Stand“-Datum
aktualisieren. Es sind Vorlagen — vor dem Einsatz rechtlich prüfen lassen.

## Steigerung, Aufwärmen, Deload

- **Steigerung** (`steigerung()` in `app.js`): Ausgangspunkt ist das schwerste
  Gewicht vom letzten Mal. Alle Sätze am oberen Ende des Wdh.-Bereichs (und RIR
  nicht unter dem Ziel) oder RIR Ø mindestens 2 über dem Ziel → mehr Gewicht:
  Kurzhantel/Kettlebell +2 kg, Langhantel bei Beinen/Po/Kreuzheben +5 kg, sonst
  +2,5 kg. Mehr als die Hälfte der Sätze unter dem Bereich → weniger, berechnet
  über das 1RM (Epley) für das untere Ende samt RIR-Ziel, höchstens −5 %. Sonst
  gleiches Gewicht, eine Wdh. mehr. Der Vorschlag steht über der Übung und ist
  der Platzhalter im ersten Satz.
- **Aufwärmsätze** vor der ersten Übung jeder Muskelgruppe: Langhantel ab 40 kg
  leere Stange × 10, 50 % × 5, 70 % × 3 (ab 60 kg zusätzlich 85 % × 1);
  Kurzhantel, Maschine, SZ-Stange 50 % × 8 und 75 % × 4. Nur als Hinweis, nicht
  im Protokoll.
- **Deload**: Nach 7 (Einsteiger) bzw. 5 (Fortgeschrittene) Trainingswochen am
  Stück schlägt die App auf *Heute* und unter *Training* eine leichtere Woche vor
  („Diese Woche“ oder „Nächste Woche“); unter *Training* lässt sie sich auch von
  Hand einlegen. In der Deload-Woche: halbe Sätze, ca. 10 % weniger Gewicht,
  RIR 3–4. Deload-Trainings tragen `deload: true`, zählen nicht für die nächste
  Steigerung und erscheinen in der Coach-Ansicht mit „· Deload“.

## Barcode-Scanner

Unter *Ernährung → Eintrag hinzufügen → Barcode scannen*. Die Erkennung läuft
im Browser: `BarcodeDetector`, wo vorhanden, sonst die mitgelieferte
ZXing-Bibliothek (`vendor/zxing.min.js`, @zxing/library 0.21.3, Apache 2.0),
die erst beim ersten Scan geladen wird. Alternativ lässt sich die Nummer
eintippen. Die Nährwerte kommen von **Open Food Facts**
(`world.openfoodfacts.org/api/v2/product/<code>.json`); übertragen wird nur die
Nummer. Gefundene Produkte speichert die App in `gescannt` — sie erscheinen in der
Suche und funktionieren danach offline. Für die Kamera erlaubt `netlify.toml`
`camera=(self)`. Datenschutz: Abschnitt 7 der Datenschutzerklärung.

## Grenzen

- **Schritte und Schlaf werden eingetippt.** Eine Web-App darf Apple Health
  oder Google Fit nicht auslesen; dafür bräuchte es eine native App.
- **Keine Push-Benachrichtigungen** — die Check-in-Erinnerung erscheint beim
  Öffnen der App und als Punkt am Reiter.
- **Coach-Ansicht nicht live.** Sie ist so aktuell wie die letzte
  Fortschrittsdatei. Echtzeit bräuchte einen Server mit Konten und
  Auftragsverarbeitung nach DSGVO.
- **Kein medizinischer Ratgeber.** Der Gesundheitshinweis steht bei der
  Einrichtung und in den Einstellungen und darf nicht entfernt werden.
