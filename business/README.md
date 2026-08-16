# FitLine Business — Kontakte & Follow-up

Eine **PWA**: läuft im Browser, lässt sich auf dem Homescreen installieren und
funktioniert nach dem ersten Aufruf offline. Kein Framework, kein Build-Schritt,
keine Abhängigkeiten zur Laufzeit — genauso wartbar wie die Website und die
Programm-App daneben.

Das ist das Werkzeug für die Geschäftsseite: **wer sind meine Leute, und was
steht bei jedem als Nächstes an.** Die App unter `app/` ist etwas anderes — die
begleitet Kunden durch das Ernährungsprogramm.

## Was die App kann

| Bereich | Inhalt |
|---|---|
| **Heute** | Was heute dran ist: überfällige und fällige Follow-ups, Geburtstage, fällige Nachbestellungen, vernachlässigte Kunden und Partner, Kontakte ohne nächsten Schritt |
| **Kontakte** | Die Datenbank: Interessenten, Kunden, Teampartner, Ruhende. Suche über alle Felder, Filter, vier Sortierungen |
| **Follow-up** | Alle geplanten Schritte nach Überfällig, Heute, Morgen, Woche, Später. Abhaken, verschieben, neu planen |
| **Team** | Struktur über die Sponsorenkette, Ebenen, Betreuungsstand, Kundenübersicht mit Bestellrhythmus |
| **Zahlen** | Bestand, Aktivität der letzten acht Wochen, Trichter, Auswertung nach Quelle, Pflegezustand der Datenbank |

## Der eigentliche Kern: die Kadenz

Eine Kontaktdatenbank ohne Wiedervorlage ist eine Adressliste. Der Unterschied
steckt darin, dass **aus jeder Statusänderung automatisch der nächste Schritt
mit Datum wird**:

| Auslöser | Was die App anlegt | Vorgabe |
|---|---|---|
| Kontakt neu erfasst | Erstkontakt aufnehmen | +1 Tag |
| Erstkontakt geführt | Nachfassen, Termin vereinbaren | +3 Tage |
| Termin vereinbart | Termin durchführen | +2 Tage |
| Produkt oder Geschäft gezeigt | Offene Fragen klären | +2 Tage |
| Entscheidung offen | Entscheidung nachfassen | +4 Tage |
| Wurde Kunde | Nach den Produkten fragen | +10 Tage |
| Wurde Partner | Startgespräch | +7 Tage |
| Auf „ruhend" gesetzt | Locker wieder melden | +90 Tage |

Dasselbe passiert beim Abhaken: Eine erledigte Aufgabe wandert in den Verlauf
des Kontakts, und der nächste Schritt steht sofort wieder da. Angelegt wird
immer nur dann, wenn für den Kontakt nichts Offenes vorliegt — sonst würden
sich bei jedem Antippen Erinnerungen stapeln.

Alle Abstände sind unter **Einstellungen → Follow-up-Rhythmus** änderbar. Wer
enger nachfasst, stellt sie kleiner.

Zwei weitere Rhythmen laufen ohne Aufgabe im Hintergrund und melden sich unter
„Heute":

- **Nachbestellung**: 30 Tage nach der letzten Bestellung (außer bei Autoship).
- **Betreuung**: Partner nach 21 Tagen ohne Verlaufseintrag, Kunden nach 60.

## Was zu einem Kontakt gespeichert wird

Name, Telefon, E-Mail, Ort, Geburtstag, Quelle, Empfehlungsgeber, Schlagwörter
und eine freie Notiz. Dazu je nach Rolle:

- **Interessent** — Stand im Gespräch (fünf Stufen von „neu erfasst" bis
  „Entscheidung offen")
- **Kunde** — Kundennummer, Produkte, letzte Bestellung, Autoship
- **Teampartner** — Partner seit, Rang, Sponsor (leer heißt Erstlinie)

Jeder Kontakt führt außerdem einen **Verlauf**: jedes Gespräch, jede Nachricht,
jeder Statuswechsel mit Datum. Das ist die Grundlage für die Betreuungswarnungen
und für die Aktivitätszahlen — und der Grund, warum man nach einem halben Jahr
noch weiß, worüber zuletzt gesprochen wurde.

## Anrufen, schreiben, mailen

Aus jedem Kontakt und aus jeder Aufgabe heraus direkt: `tel:`, `wa.me` und
`mailto:`. Für WhatsApp rechnet die App die Nummer ins internationale Format um
(aus `0170 …` wird `49170 …`); die Ländervorwahl steht in den Einstellungen.

Nach einem Anruf aus der Kontaktakte heraus öffnet sich der Dialog zum
Festhalten von selbst — samt Vorschlag für die Wiedervorlage.

## Daten der Nutzer

Alles liegt im `localStorage` des Geräts. Kein Server, kein Konto, keine
Übertragung — entsprechend auch keine Synchronisierung zwischen Geräten.

Unter Einstellungen gibt es:

- **Sicherung exportieren (JSON)** — vollständig, auch der einzige Weg auf ein
  neues Gerät. Regelmäßig machen: Geht das Gerät verloren, sind die Daten weg.
- **Kontakte als CSV** — für Tabellenkalkulation, mit BOM, damit Excel unter
  Windows die Umlaute richtig anzeigt.
- **Sicherung einlesen** — ersetzt den vorhandenen Bestand nach Rückfrage.

### Verantwortung

In dieser Datenbank stehen personenbezogene Daten anderer Menschen. Die App
weist bei der Einrichtung und in den Einstellungen darauf hin, und der Hinweis
darf nicht entfernt werden: nur erfassen, was für die Betreuung nötig ist,
niemandem sonst Zugriff auf das Gerät geben, und Kontakte **vollständig
löschen** — nicht nur archivieren —, sobald jemand nicht mehr kontaktiert
werden möchte.

## Beispieldaten

Beim ersten Start und unter Einstellungen lässt sich ein kleiner erfundener
Bestand laden, um die App durchzuspielen. Nur solange die Datenbank leer ist —
echte Kontakte sollen nie mit erfundenen durcheinandergeraten.

## Icons

```bash
python3 business/build/build_icons.py
```

Motiv sind drei verbundene Knoten in Petrol. Bewusst anders als die Pulslinie
in Rot bei der Programm-App: Beide liegen am Ende auf demselben Homescreen und
müssen auf einen Blick unterscheidbar sein. Kein FitLine-Logo und keine
Wortmarke — die App ist Marks eigenes Arbeitsmittel und keine Anwendung von
PM-International.

## Lokal ausprobieren

```bash
cd business && python3 -m http.server 8899
```

Dann `http://127.0.0.1:8899` öffnen. Ein Server ist nötig, weil ein Service
Worker unter `file://` nicht registriert wird.

## Veröffentlichen

Der Ordner wird von `tools/build_site.py` nach `dist/business/` kopiert und ist
unter `/business/` erreichbar. Ausgeschlossen bleiben `build/` und diese Datei.
Zwei Bedingungen:

- **HTTPS ist Pflicht.** Ohne gesicherte Verbindung registriert kein Browser
  einen Service Worker, und ohne den gibt es weder Offline-Betrieb noch die
  Installation auf dem Homescreen.
- **Nach einem Update** die Konstante `VERSION` in `sw.js` erhöhen. Sonst
  liefert der Cache weiter die alten Dateien aus.

`robots.txt` und der Kopf `X-Robots-Tag` schließen das Verzeichnis aus
Suchmaschinen aus. Ein Zugriffsschutz ist das nicht — wer die Adresse kennt,
sieht die leere App. Die Daten sieht er nicht, die liegen nur im Browser des
jeweiligen Geräts.

## Grenzen

- **Keine native App.** Für App Store und Play Store bräuchte es Xcode
  beziehungsweise Android Studio. Eine PWA lässt sich auf iOS über „Zum
  Home-Bildschirm" und auf Android über „App installieren" ablegen und verhält
  sich danach weitgehend wie eine installierte App.
- **Keine Push-Benachrichtigungen.** Fällige Follow-ups stehen als Zahl auf dem
  Reiter, aber das Gerät meldet sich nicht von selbst — dafür bräuchte es einen
  Server für den Versand.
- **Keine Synchronisierung, kein Mehrbenutzerbetrieb.** Ein Gerät, ein Bestand,
  Austausch nur über Export und Import.
- **Keine Anbindung an PM-International.** Kundennummern und Bestelldaten sind
  von Hand gepflegt; die App liest nichts aus deren Systemen.
