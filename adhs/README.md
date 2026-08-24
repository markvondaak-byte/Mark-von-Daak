# Chaos mit System — Band 4

**ADHS verstehen, annehmen und in den Griff bekommen**
Praxisbuch für Erwachsene · 6″ × 9″ · rund 29.700 Wörter · 134 Seiten

Thematisch eigenständig, unabhängig von der Stoffwechsel-Reihe. Geteilt wird
nur die Werkzeugkette: `buch/build/build_docx.py`, `buch/build/stile.py` und
die beiden Prüfskripte.

## Bauen

```bash
pip install -r buch/requirements.txt
python3 adhs/build/build_adhs.py        # → adhs/out/chaos-mit-system.{docx,pdf}

python3 buch/build/rechtschreibung.py   # Rechtschreibung und Typografie
python3 buch/build/claim_check.py       # HCVO, muss ohne Fehler laufen
```

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

## Noch nicht gebaut

- **Umschlag.** `build_cover.py` ist für diesen Band nicht angelegt. Der
  Aufruf wäre derselbe wie bei Band 1; die Rückenbreite errechnet sich aus den
  134 Seiten des fertigen Innenteils, `cover_stil` und `cover_akzent` stehen
  bereits in `adhs.yaml`.
- **Kindle-Ausgabe.** `build_epub.py` ist auf die drei bestehenden Bände
  verdrahtet und wurde nicht angefasst.
- **Abnahme.** `abnahme.py` prüft die drei alten Bände samt Umschlägen. Ohne
  Umschlag gibt es für Band 4 nichts abzunehmen, was das Skript prüfen würde.
