# Der Stoffwechsel-Reset — App

Eine **PWA**: läuft im Browser, lässt sich auf dem Homescreen installieren und
funktioniert nach dem ersten Aufruf offline. Kein Framework, kein Build-Schritt,
keine Abhängigkeiten zur Laufzeit — genauso wartbar wie die Website daneben.

## Was die App kann

| Bereich | Inhalt |
|---|---|
| **Heute** | Tageskarte: Mahlzeiten, Wasser, Nährstoffe, Bewegung, Schlaf, Befinden, Notiz. Dazu der Wochenfokus und passende Rezepte zur Tagesfarbe |
| **Programm** | Alle 12 Wochen auf einen Blick, Tagesfarben, heutiger Tag markiert, erledigte Tage mit Punkt |
| **Rezepte** | Alle 73 Gerichte, Filter nach Tagesfarbe, Suche über Namen und Zutaten |
| **Wissen** | 12 Kapitel aus Band 1 zum Nachschlagen |
| **Verlauf** | Gewicht und Umfänge, Veränderung seit Start, Diagramm |

Ab Woche 7 legt der Nutzer die Tagesfarben selbst fest — so wie es die
Stabilisierungsphase vorsieht.

## Wo die Inhalte herkommen

Die App hat **keine eigene Kopie** der Inhalte. Alles wird aus den Quellen der
drei Bände erzeugt:

```
workbook/build/wochenplan.py   →  app/daten/programm.json
rezepte/rezepte/*.yaml         →  app/daten/rezepte.json
buch/kapitel/*.md              →  app/daten/wissen.json
```

Nach jeder Änderung an einem Band:

```bash
python3 app/build/build_app_daten.py
```

Ein geändertes Rezept im Buch ist damit auch in der App geändert. Welche
Buchkapitel in den Wissensteil wandern, steht in `WISSENSKAPITEL` in
`build_app_daten.py`.

## Icons

```bash
python3 app/build/build_icons.py
```

Erzeugt die drei PNG-Größen, die Android und iOS erwarten. Bewusst ohne
FitLine-Logo oder -Wortmarke: Die App ist Marks eigenes Werkzeug und soll
nicht wie eine Publikation von PM-International aussehen. Übernommen ist nur
die **Farbwelt der eigenen Website** (`--accent: #C8102E`, Poppins,
Instrument Sans, heller und dunkler Modus).

## Lokal ausprobieren

```bash
cd app && python3 -m http.server 8899
```

Dann `http://127.0.0.1:8899` öffnen. Ein Server ist nötig — die App lädt ihre
Daten per `fetch`, und das funktioniert bei `file://` nicht.

## Veröffentlichen

Der Ordner `app/` ist ein statisches Verzeichnis und kann direkt neben die
Website gelegt werden, etwa unter `/app/`. Zwei Bedingungen:

- **HTTPS ist Pflicht.** Ohne gesicherte Verbindung registriert kein Browser
  einen Service Worker, und ohne den gibt es weder Offline-Betrieb noch die
  Installation auf dem Homescreen.
- **Nach einem Update** die Konstante `VERSION` in `sw.js` erhöhen. Sonst
  liefert der Cache bei bestehenden Nutzern weiter die alten Dateien aus.

## Daten der Nutzer

Alles liegt im `localStorage` des Geräts. Kein Server, kein Konto, keine
Übertragung — entsprechend auch keine Synchronisierung zwischen Geräten und
kein Zugriff für dich als Betreuer.

Unter Einstellungen gibt es Export und Import als JSON-Datei. Das ist der
einzige Weg, Daten auf ein neues Gerät zu bringen, und der Hinweis darauf
steht auch in der App.

## Grenzen

- **Keine native App.** Für App Store und Play Store bräuchte es Xcode
  beziehungsweise Android Studio. Eine PWA lässt sich auf iOS über „Zum
  Home-Bildschirm" und auf Android über „App installieren" ablegen und
  verhält sich danach weitgehend wie eine installierte App.
- **Keine Push-Benachrichtigungen.** Technisch möglich, bräuchte aber einen
  Server für den Versand.
- **Kein medizinischer Ratgeber.** Die Hinweise aus den Büchern erscheinen bei
  der Einrichtung und unter Einstellungen und dürfen nicht entfernt werden.
