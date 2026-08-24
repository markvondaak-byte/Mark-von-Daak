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
| Motiv | Lebensmittel-Illustrationen | Strichraster Chaos → Ordnung |
| Titelfoto | gemeinsames `buch/cover/titelbild.jpg` | keines |
| Bandkennung | „DAS BUCH · 4 PHASEN" u. ä. | keine |
| Fußhinweis | Marken der PM-International AG | „Kein medizinischer Ratgeber" |

Der letzte Punkt ist kein Kosmetikthema: In diesem Band kommt keine fremde
Marke vor, ein Markenhinweis wäre also sachlich falsch — und auf einem Buch
über psychische Gesundheit sähe der Verweis auf einen
Nahrungsergänzungs-Vertrieb nach Produktwerbung aus.

Farbwelt, Motiv und die drei Flächen stehen in `build/gestaltung.py`, geteilt
von Druckumschlag und Kindle-Titelbild. Das Motiv benutzt eine feste
Zufallszahl (`RASTER_SAAT`), damit jeder Build denselben Umschlag erzeugt —
sonst ließen sich Korrekturabzüge nicht vergleichen.

Aus `buch/build` kommen nur bandneutrale Bausteine: Schriften, Zeilenumbruch,
Textblöcke und vor allem die **Geometrie des Barcodefeldes**, in der viel
mühsam erarbeitetes Wissen über KDPs Vorgaben steckt (siehe `buch/README.md`).
An den Skripten der Reihe wurde nichts geändert.

**Warum die Dateinamen abweichen.** `kindle_titelbild.py` heißt nicht
`kindle_cover.py`, und die Gestaltung liegt in `gestaltung.py` statt in
`build_cover.py`: Beim Bauen liegen `adhs/build` und `buch/build` gleichzeitig
im Suchpfad, und zwei Module gleichen Namens verdecken einander.

## Noch offen

- **Abnahme.** `abnahme.py` prüft die drei alten Bände samt Umschlägen und
  wurde nicht erweitert. Die dort automatisierten Barcode-Prüfungen greifen
  für Band 4 also noch nicht — vor dem Upload lohnt ein Blick in KDPs eigene
  Vorschau, besonders auf das Barcodefeld unten rechts.
