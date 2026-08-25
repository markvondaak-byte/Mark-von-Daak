# Chaos mit System — Band 4

**ADHS verstehen, annehmen und in den Griff bekommen**
Praxisbuch für Erwachsene · 6″ × 9″ · rund 29.700 Wörter · 134 Seiten

Thematisch eigenständig, unabhängig von der Stoffwechsel-Reihe. Geteilt wird
nur die Werkzeugkette: `buch/build/build_docx.py`, `buch/build/stile.py` und
die beiden Prüfskripte.

## Bauen

```bash
pip install -r buch/requirements.txt

python3 adhs/build/build_adhs.py            # Innenteil: .docx und .pdf
python3 buch/build/innenteil_druck.py       # Innenteil auf exakte Trimmgröße
python3 adhs/build/build_cover.py           # Umschlag, Taschenbuch + Hardcover
python3 buch/build/cover_flach.py adhs/out/cover.pdf
python3 buch/build/cover_flach.py adhs/out/cover-hardcover.pdf
python3 adhs/build/kindle_titelbild.py      # Titelbild für Kindle
python3 adhs/build/build_epub.py            # Kindle-Ausgabe

python3 buch/build/rechtschreibung.py       # Rechtschreibung und Typografie
python3 buch/build/claim_check.py           # HCVO, muss ohne Fehler laufen
```

**Der Umschlag muss nach dem Innenteil gebaut werden** — die Rückenbreite
errechnet sich aus dessen Seitenzahl. Bei 134 Seiten sind das 7,7 mm beim
Taschenbuch und 16,7 mm bei der Buchdecke des Hardcovers; beide liegen über
KDPs Schwelle, der Rücken trägt also Text.

**Zu KDP hochgeladen wird auch beim Innenteil die `-druck`-Fassung.**
LibreOffice exportiert 6 × 9 Zoll nicht maßhaltig: Im `.docx` steht die
Seitengröße korrekt, im erzeugten PDF sind daraus 152,4 × **229,01** mm
geworden — 0,41 mm zu hoch. KDP prüft gegen die im Formular gewählte
Trimmgröße und weist das zurück. `innenteil_druck.py` setzt die Seitenbox auf
das Sollmaß und schneidet den Überschuss unten ab, wo er gemessen sitzt; keine
Textzeile wandert dabei. Ergebnis: `adhs/out/chaos-mit-system-druck.pdf`.

**Zu KDP hochgeladen wird `cover-druck.pdf`, nicht `cover.pdf`.** Die
Vektorfassung enthält einen gestuften Verlauf; `cover_flach.py` rastert den
Umschlag bei 300 dpi und legt ihn als einzelnes Bild in ein PDF exakter
Größe — ohne Transparenz, Verläufe, Schriften und Ebenen. Die Vektorfassung
bleibt die Quelle für Korrekturen.

`build_adhs.py` ist ein dünner Aufruf um `build_docx.py` — dieselbe
Zwei-Durchlauf-Logik wie Band 1, nur mit `adhs.yaml` und `adhs/kapitel`.
Zusätzlich meldet er, wenn ein Kapitel im Inhaltsverzeichnis ohne Seitenzahl
geblieben ist; `seitenzahlen_ermitteln()` lässt einen Eintrag lieber aus, als
eine falsche Zahl zu drucken, und das darf nicht unbemerkt durchlaufen.

**In `stile.py` wird für diesen Band nichts gedreht.** Die Absatzformate
gelten für alle vier Bände; wer dort am Schriftgrad dreht, um eine Seitenzahl
zu treffen, verstellt die anderen mit (siehe `buch/README.md`).

### Was der Container braucht

Zwei Stolpersteine, beide schon einmal getroffen:

- **`libreoffice-writer` muss installiert sein.** `soffice` allein genügt
  nicht — die Konvertierung bricht dann mit „source file could not be loaded“
  ab, obwohl das `.docx` in Ordnung ist.
  `apt-get install -y libreoffice-writer`
- **`pypdf` kann mit `pyo3_runtime.PanicException` abbrechen.** Das ist der in
  `buch/requirements.txt` beschriebene Fall einer defekten
  `cryptography`-Installation: `pip install --force-reinstall cffi
  cryptography`. Die Meldung „RECORD file not found“ beim Deinstallieren der
  Debian-Version ist dabei folgenlos.

## Aufbau

| Teil | Kapitel | |
|---|---|---|
| Titelei | — | Titelseite, Impressum, „Bitte zuerst lesen“, Inhalt |
| I — Verstehen | 1–5 | Was ADHS ist · Das Gehirn dahinter · Drei Ausprägungen · Vier Grundmuster · Versagensbiografie |
| II — Klarheit | 6–8 | Weg zur Diagnose · Was oft mitkommt · Standortbestimmung |
| III — Fundament | 9–12 | Schlaf · Bewegung · Essen und Energie · Umgebung |
| IV — Das System | 13–18 | Weniger Reibung · Externes Gehirn · Zeit · Anfangen · Dranbleiben · Ordnung, Papier, Geld |
| V — Behandlung | 19–21 | Medikamente · Therapie und Coaching · Emotionen |
| VI — Leben | 22–26 | Arbeit · Partnerschaft · Angehörige · Schlechte Wochen · Eigene Regeln |
| VII — Anhang | 27–34 | 30-Tage-Start · Vorlagen · Fragen · Anlaufstellen · Glossar · In eigener Sache · Haftung · Über den Autor |

Die Dateinamen bestimmen die Reihenfolge (`sorted(glob("*.md"))`), das Feld
`nummer:` im Front Matter die Kapitelnummer im Verzeichnis. Wer ein Kapitel
einschiebt, muss die folgenden `nummer:`-Angaben mitziehen — und die
Querverweise im Text, die auf Kapitelnummern zeigen.

## Inhaltliche Leitplanken

Das Thema ist medizinisch, der Autor ist es nicht. Der Band trägt das offen:

- **Keine Diagnose.** Auch die Standortbestimmung in Kapitel 8 ist
  ausdrücklich kein Test.
- **Keine Dosierungen, keine Einzelfallempfehlung** in Kapitel 19.
- **Kein Nahrungsergänzungsmittel gegen ADHS**, keine Produkte, keine Marken,
  kein Verweis auf ein Angebot des Autors. Die wirtschaftliche Interessenlage
  ist in „In eigener Sache“ offengelegt.
- **Kein Erfolgsversprechen.** ADHS verschwindet nicht; was sich ändern lässt,
  ist der Umgang damit.

`claim_check.py` prüft die Formulierungsverbote mit. Vier Kapitel dieses
Bandes stehen auf der Freigabeliste, weil sie Krankheitsbegriffe im
Sachkontext brauchen: `02-bitte-zuerst-lesen`, `22-was-oft-mitkommt`,
`51-medikamente`, `76-in-eigener-sache`, `77-hinweise-haftung`.

## Offene Punkte vor der Veröffentlichung

Drei Dinge kann nur der Autor entscheiden oder bestätigen.

**1. Die Autorenposition.** Der Band ist durchgehend aus der Position
*Angehöriger und Begleiter* geschrieben — kein eigenes ADHS, Außensicht,
verallgemeinerte Beobachtungen statt Fallberichte. Das steht so in
`78-ueber-den-autor.md`, in `76-in-eigener-sache.md` und im Klappentext.
**Bitte gegenlesen und bestätigen.** Stimmt die Position nicht, müssen diese
drei Stellen geändert werden — der übrige Text ist davon nicht betroffen, weil
er keine Ich-Erzählung enthält.

**2. Die Autorenbiografie.** `78-ueber-den-autor.md` ist bewusst knapp und
enthält nur, was aus dem Repository belegbar war: Wohnort, die Offenlegung zum
Vertrieb von Nahrungsergänzungsmitteln, der Hinweis auf die
Ernährungs-Bände. Es wurde **nichts erfunden** — keine Ausbildung, keine
Berufserfahrung mit ADHS, keine Zahlen zu begleiteten Menschen. Wenn es dazu
Belegbares gibt, gehört es dort hinein.

**3. Die Anlaufstellen.** `74-anlaufstellen.md` nennt Telefonnummern,
Verbände und Internetadressen. Sie waren nach bestem Wissen zum Zeitpunkt des
Schreibens richtig, und im Kapitel steht der Vorbehalt „Stand bei
Drucklegung“. **Vor dem Druck bitte einzeln prüfen** — eine tote Notrufnummer
in einem Buch über psychische Gesundheit ist der schlimmste denkbare Fehler.
Besonders zu prüfen: die Angaben zu Österreich und zur Schweiz, die dünner
sind als die deutschen.

## Der Umschlag

**Eigene Bildsprache, bewusst nicht die der Stoffwechsel-Reihe.** Band 4
gehört thematisch nicht dazu; im Regal und im Amazon-Vorschaubild soll
niemand eine Reihe vermuten, die es nicht gibt. Konkret heißt das:

| | Reihe (Band 1–3) | Band 4 |
|---|---|---|
| Grund | Schiefergrau `#5A616B` | Tintenblau `#1E2937` |
| Akzent | Blatt / Zitrone / Beere | Bernstein `#F2A65A` |
| Motiv | Lebensmittel-Illustrationen | Titelbild: Fadenknoten, der sich auskämmt |
| Titelfoto | gemeinsames `buch/cover/titelbild.jpg` | keines |
| Bandkennung | „DAS BUCH · 4 PHASEN" u. ä. | keine |
| Fußhinweis | Marken der PM-International AG | „Kein medizinischer Ratgeber" |
| Barcodefeld | Weißfläche beim Taschenbuch | keine — KDPs Box genügt |

Der letzte Punkt ist kein Kosmetikthema: In diesem Band kommt keine fremde
Marke vor, ein Markenhinweis wäre also sachlich falsch — und auf einem Buch
über psychische Gesundheit sähe der Verweis auf einen
Nahrungsergänzungs-Vertrieb nach Produktwerbung aus.

Farbwelt, Motiv und die drei Flächen stehen in `build/gestaltung.py`, geteilt
von Druckumschlag und Kindle-Titelbild.

**Das Motiv** (`fadenmotiv()`) zeigt die These des Buches als Bild:
einundzwanzig Fäden, links unbrauchbar verschlungen, rechts in Ordnung —
dasselbe Material, anders geführt, nicht „vorher schlecht, nachher gut". Jeder
Faden ist die Summe von vier Sinuswellen mit eigener Frequenz und Phase; ihre
Amplitude fällt nach rechts auf null, deshalb läuft jeder Faden dort exakt
waagerecht in seine Spur ein, ohne dass die Endlage eigens gesetzt werden
müsste.

Zwei Dinge daran sind nicht Geschmack, sondern nötig:

- **Feste Zufallszahl** (`MOTIV_SAAT`), damit jeder Build denselben Umschlag
  erzeugt — sonst ließen sich Korrekturabzüge nicht vergleichen.
- **Randabfall** (`randabfall`): Der Ausschlag läuft zu den Rändern des
  Motivfeldes hin aus. Ohne ihn schwingen die äußeren Fäden aus dem Rahmen —
  nach oben in den Untertitel, nach unten quer durch die Autorenzeile.

Gezeichnet wird in Teilstücken statt als ein Pfad je Faden, weil ein Pfad nur
eine Strichfarbe haben kann: Erst die stückweise Färbung ergibt den Übergang
von Schiefer nach Bernstein. Ohne Transparenz — daran hängt sonst KDPs
Prüfung.

Aus `buch/build` kommen nur bandneutrale Bausteine: Schriften, Zeilenumbruch,
Textblöcke und vor allem die **Geometrie des Barcodefeldes**, in der viel
mühsam erarbeitetes Wissen über KDPs Vorgaben steckt (siehe `buch/README.md`).
An den Skripten der Reihe wurde nichts geändert.

**Warum die Dateinamen abweichen.** `kindle_titelbild.py` heißt nicht
`kindle_cover.py`, und die Gestaltung liegt in `gestaltung.py` statt in
`build_cover.py`: Beim Bauen liegen `adhs/build` und `buch/build` gleichzeitig
im Suchpfad, und zwei Module gleichen Namens verdecken einander.

## Ein Titelbild einlegen

**Aktuell liegt eines:** `adhs/cover/titelbild.png`, 2751 × 4096 px — ein
Fadenknoten, der sich nach rechts in geordnete Linien auskämmt. Das ergibt
443 dpi über die Taschenbuchfläche und 393 dpi über die des Hardcovers, beides
über KDPs 300. Das gezeichnete Fadenmotiv (`fadenmotiv()`) ist der Rückfall,
falls die Datei entfernt wird oder unlesbar ist.

Leg eine Datei ab, und sie füllt die Vorderseite:

```
adhs/cover/titelbild.jpg     (auch .jpeg, .png, .webp)
```

Danach `python3 adhs/build/build_cover.py` und
`python3 adhs/build/kindle_titelbild.py` erneut laufen lassen — das Skript
meldet dann, ob die Auflösung reicht.

**Was das Skript mit dem Bild macht.** Es beschneidet mittig auf das
Seitenverhältnis der Vorderseite (nicht verzerrt, die untere Bildhälfte wird
bevorzugt) und lässt es dort zurücktreten, wo Text steht:

| Zone | Regel |
|---|---|
| oben bis 44 % | voller Grundton — dort stehen Titel und Untertitel |
| 44 → 63 % | linear auf null, das Bild kommt hervor |
| ab 74 % nach unten | auf 88 % abgedunkelt — dort steht die Autorenzeile |
| überall | 14 % Grundschleier, damit helle Schrift trägt |

Das Abdunkeln geschieht **im Bild**, nicht als Fläche darüber: Ein Schleier im
PDF wäre Transparenz, und die Vektorfassung soll frei davon bleiben. Gebaut
wird es als zeilenweise Maske über einen schmalen Streifen, der in die Breite
gezogen wird — eine Schleife über alle Bildpunkte brauchte Minuten, das hier
drei Sekunden.

Die **Autorenzeile steht über einem Titelbild in Weiß** statt in Bernstein:
Das Motiv ist selbst warm, und Bernstein auf Bernstein trägt keinen Kontrast.
Über dem gezeichneten Fadenmotiv bleibt sie farbig.

Eingebettet wird mit **300 dpi über die belichtete Fläche**, nicht mit fester
Pixelbreite — sonst hinge die Druckauflösung daran, wie groß die Fläche
zufällig ist, und beim Hardcover ist sie deutlich größer.

**Mindestgrößen** für 300 dpi über die belichtete Fläche:

| Bindeart | belichtete Fläche | Bild mindestens |
|---|---|---|
| Taschenbuch | 155,6 × 235,0 mm | **1837 × 2775 px** |
| Hardcover | 170,4 × 264,6 mm | **2013 × 3125 px** |

Wer beide Bindearten bedient, richtet sich nach der Hardcover-Zeile. Ein
2K-Bild (rund 1700 × 2530 px) liegt darunter — es wird angenommen, im Druck
aber weich, und das sieht man auf dunklem Grund sofort. Vor dem Einlegen also
auf 4K hochrechnen lassen.

**Wichtig zum Motiv:** Nach links darf nichts überstehen, dort liegt der
Rücken. Das Skript setzt den Anschnitt deshalb nur nach rechts, oben und
unten — im Bild selbst muss links nichts freigehalten werden.

## Das Barcodefeld

KDP druckt den Barcode selbst auf die Rückseite, unten rechts, **in einer
eigenen weißen Box** von 2 × 1,2 Zoll. Band 4 zeichnet dort deshalb keine
eigene Fläche (`BARCODE_WEISSFLAECHE = False` in `gestaltung.py`): Eine Fläche
darunter wäre bestenfalls unsichtbar und schlechtestenfalls ein weißer Rand,
der unter KDPs Box hervorschaut. Band 1 ist beim Hardcover denselben Weg
gegangen.

**Reserviert bleibt das Feld trotzdem.** Der Rechtshinweis endet darüber, und
es liegt nichts darin. Nachgemessen an beiden fertigen Umschlägen:

| | Taschenbuch | Hardcover |
|---|---|---|
| Feldgröße | 50,8 × 30,5 mm | 50,8 × 30,5 mm |
| Abstand zur Dateikante unten | 19,3 mm | 24,3 mm |
| Wörter im Feld | 0 | 0 |
| Helligkeitsspanne | 2 von 255 | 1 von 255 |

**Das Restrisiko gehört dazugesagt:** Druckte KDP den Barcode wider Erwarten
ohne eigene Box, stünde schwarze Strichschrift auf Tintenblau und wäre nicht
zu scannen. Vorschau und Dokumentation zeigen die Box, im gedruckten Buch
gesehen hat sie hier aber noch niemand — ein Blick aufs erste Belegexemplar
lohnt. Wer die Fläche zurückwill, setzt die Konstante auf `True`.

## Noch offen

- **Abnahme.** `abnahme.py` prüft die drei alten Bände samt Umschlägen und
  wurde nicht erweitert. Die dort automatisierten Barcode-Prüfungen greifen
  für Band 4 also noch nicht — vor dem Upload lohnt ein Blick in KDPs eigene
  Vorschau, besonders auf das Barcodefeld unten rechts.
