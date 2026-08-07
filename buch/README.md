# Der Stoffwechsel-Reset — Buchprojekt

Zwei eigenständige Bände, gemeinsame Build-Basis:

| Band | Quelle | Format | Ausgabe |
|---|---|---|---|
| 1 — Das Buch | `buch/kapitel/*.md` | 6″ × 9″ | `buch/out/stoffwechsel-reset.{docx,pdf}` |
| 2 — Das Workbook | `workbook/` | 8″ × 10″ | `workbook/out/workbook.{docx,pdf}` |
| 3 — Das Rezeptbuch | `rezepte/` | 8″ × 10″ | `rezepte/out/rezeptbuch.{docx,pdf}` |

## Bauen

```bash
pip install -r buch/requirements.txt

python3 buch/build/build_docx.py           # Band 1: .docx und .pdf
python3 buch/build/build_cover.py          # Umschlag Band 1

python3 workbook/build/build_workbook.py   # Band 2: .docx und .pdf
python3 workbook/build/build_cover.py      # Umschlag Band 2

python3 rezepte/build/build_rezepte.py     # Band 3: .docx und .pdf
python3 rezepte/build/build_cover.py       # Umschlag Band 3

python3 buch/build/cover_flach.py          # Umschläge in die KDP-Druckfassung

python3 buch/build/kindle_cover.py         # Titelbilder für die Kindle-Ausgaben
python3 buch/build/build_epub.py           # Kindle-Ausgaben Band 1 und 2

python3 buch/build/claim_check.py          # HCVO-Prüfung, muss ohne Fehler laufen
python3 rezepte/build/zutaten_check.py     # Rezepte gegen die Phasenregeln
python3 buch/build/abnahme.py              # Endabnahme aller drei Bände
```

Die Umschläge müssen **nach** dem jeweiligen Innenteil gebaut werden — die
Rückenbreite errechnet sich aus der Seitenzahl des fertigen PDFs.

**Typografie je Band festzurren, nicht in `stile.py` drehen.** Die
Absatzformate in `buch/build/stile.py` gelten für alle drei Bände. Wird dort
am Schriftgrad oder am Durchschuss gedreht, um die Seitenzahl eines Bandes zu
treffen, verstellt das die anderen mit — das Workbook ist auf diesem Weg
einmal unbemerkt von 88 auf 103 Seiten gewachsen und hatte wieder dreizehn
fast leere Seiten. `dokument_anlegen()` nimmt deshalb einen zweiten Parameter
mit Abweichungen je Format; Band 2 setzt seine Werte in `TYPOGRAFIE` in
`workbook/build/build_workbook.py`. `abnahme.py` prüft zusätzlich, dass kein
PDF älter ist als seine Quellen — sonst prüft die Abnahme einen alten Stand
und winkt ihn durch.

**Zu KDP hochgeladen wird `cover-druck.pdf`, nicht `cover.pdf`.** Die
Vektorfassung enthält Radialverläufe und transparente Schlagschatten; die
KDP-Prüfung verlangt reduzierte Ebenen ohne Transparenz und lehnt sie ab.
`cover_flach.py` rastert den Umschlag bei 300 dpi und legt ihn als einzelnes
Bild in ein PDF exakter Größe — ohne Transparenz, Verläufe, Schriften und
Ebenen. Die Vektorfassung bleibt die Quelle für Korrekturen.

## Kindle-Ausgaben

Ein Kindle-Buch ist nicht das Druck-PDF in anderer Verpackung. KDP verlangt
zwei eigene Dateien je Band: ein **EPUB** und ein **Titelbild** — ein reines
Vorderseitenbild, kein aufgeklappter Umschlag.

| | Band 1 | Band 2 |
|---|---|---|
| Bauart | fließender Text (reflowable) | feste Seiten (pre-paginated) |
| Quelle | `buch/kapitel/*.md` | `workbook/out/workbook.pdf` |
| Ausgabe | `buch/out/stoffwechsel-reset-kindle.epub` | `workbook/out/workbook-kindle.epub` |

**Warum zwei Bauarten.** Band 1 ist ein Lesebuch: Der Leser stellt Schriftgröße
und Rand selbst ein, der Text läuft neu um. Seitenzahlen, Kopfzeilen und ein
Inhaltsverzeichnis mit Seitenangaben gibt es dort nicht. Band 2 besteht aus
Tageskarten und Schreiblinien — umflossener Text macht daraus eine Liste von
Beschriftungen ohne die Felder, zu denen sie gehören. Deshalb wird jede
Druckseite als Bild eingelegt.

**Band 2 als E-Book ist ein Kompromiss**, und das sollte man wissen, bevor man
es einstellt: Man kann darin nicht schreiben. Sinnvoll ist die Ausgabe als
Leseprobe und als Nachschlagefassung neben dem gedruckten Heft, nicht als
Ersatz dafür. Band 3 hat aus demselben Grund keine Kindle-Ausgabe — dort wäre
sie sinnvoll, aber sie ist bisher nicht gebaut.

Die Titelbilder werden **neu gesetzt**, nicht aus dem Umschlag-PDF
ausgeschnitten: Amazon empfiehlt das Seitenverhältnis 1,6, die gedruckten
Bände haben 1,5 (6 × 9 Zoll) und 1,25 (8 × 10 Zoll). Beim Ausschneiden müsste
man oben und unten Fläche wegnehmen und würde die Lebensmittelauslage
anschneiden. `kindle_cover.py` zeichnet stattdessen mit denselben Funktionen
wie der gedruckte Umschlag auf eine Leinwand mit Buchbreite und 1,6-Höhe.

Erzeugt wird EPUB, nicht MOBI oder KPF. KDP nimmt EPUB für Kindle-Bücher
entgegen und wandelt selbst; ein Konverter ist in dieser Bauumgebung weder
vorhanden noch nötig.

## Umschlaggestaltung

Obst und Gemüse sind als Vektorgrafik in `buch/build/illustration.py`
gezeichnet — mit Radialverläufen, Glanzlichtern und Schlagschatten, damit die
Motive plastisch wirken. Der Grund für Zeichnungen statt Fotos: In der
Bauumgebung ist kein lizenziertes Bildmaterial beschaffbar, und die Grafiken
der Website haben nur Web-Auflösung.

**Farbwelt.** Zwei Varianten, umgeschaltet über `cover_stil` in der jeweiligen
YAML-Datei des Bandes:

| Wert | Aussehen |
|---|---|
| `schiefer` | helles Anthrazit (`#5A616B` oben nach `#545A64` unten), Lebensmittel als durchlaufender Streifen am oberen Rand, Titel im freien Grund darunter (aktuell eingestellt) |
| `hell` | Papierweiß, Illustrationsbänder oben und unten, Titel in der Mitte |

Dazu bestimmt `cover_akzent` die Akzentfarbe des Bandes — `blatt` (Band 1),
`zitrone` (Band 2) oder `beere` (Band 3). Die drei Bände tragen denselben
Titel; im Amazon-Vorschaubild ist der farbige Balken mit der Bandkennung das
Einzige, was sie auf den ersten Blick unterscheidet. Alle Akzentfarben halten
Abstand zum FitLine-Crimson `#C8102E`.

Wer am Grundton dreht, muss die Schriftfarben nachrechnen — jede Aufhellung
des Grundes kostet Kontrast. Maßstab: `text_leise` steht in Normalgröße und
braucht 4,5:1, die Akzentfarben stehen nur auf gefüllten Balken und in großer
Fettschrift und brauchen 3:1. Sie über diesen Wert hinaus aufzuhellen macht
sie pastellig und gleicht die Bände im Vorschaubild wieder an.

Der Untergrund ist ein Vektorverlauf, kein Bild. Ein Rasterhintergrund über
den ganzen Umschlag bräuchte für 300 dpi rund zehn Megapixel — und unterhalb
davon meldet KDP beim Hochladen eine zu niedrige Auflösung.

**Ein eigenes Titelfoto einsetzen:** Leg die Datei unter
`buch/cover/titelbild.jpg` ab (auch `.png` und `.webp` werden erkannt) und bau
den Umschlag neu. Sie ersetzt dann das obere Illustrationsband und wird mittig
auf das Format beschnitten. Für den Druck sind mindestens **1800 × 2700 px**
nötig; darunter warnt das Skript.

Auf dem Umschlag dürfen nur Lebensmittel erscheinen, die das Konzept auch
erlaubt — keine Banane, Weintraube, Ananas oder Karotte. Fremde Marken
(Produktfotos, Verbandslogos, Prüfsiegel) gehören nicht darauf.

`build_docx.py` läuft **zweimal** durch: Der erste Durchlauf ermittelt die
Seitenzahlen, der zweite setzt damit das Inhaltsverzeichnis. Grund: LibreOffice
löst Word-TOC-Felder beim PDF-Export nicht auf, deshalb wird das Verzeichnis
selbst gesetzt.

Fällt die Seitenzahl dabei ungerade aus, folgt ein dritter Durchlauf mit einer
Vakatseite am Buchende — KDP verlangt eine gerade Seitenzahl und schiebt sonst
selbst ein Blatt ein. Die Vakatseite ist ein eigener Abschnitt ohne Kopfzeile
und ohne Seitenzahl; mit beidem sähe sie nach einem Satzfehler aus. Band 3
macht das genauso.

### Systemvoraussetzung

`libreoffice-writer` muss installiert sein — `libreoffice-core` allein genügt
nicht und führt zu „source file could not be loaded":

```bash
apt-get update && apt-get install -y libreoffice-writer
```

## Kapitel schreiben

Jede Datei in `buch/kapitel/` beginnt mit YAML-Front-Matter:

```markdown
---
typ: kapitel          # titelei | teil | kapitel
nummer: 3             # Kapitelnummer, erscheint im Inhaltsverzeichnis
titel: Die Idee dahinter
kopfzeile: Die Idee   # steht in der Kopfzeile der rechten Seiten
---

# Die Idee dahinter

Fließtext …
```

Die Reihenfolge ergibt sich aus dem Dateinamen (`01-…`, `02-…`).

### Unterstützte Auszeichnung

Überschriften `#`, `##`, `###` · Absätze · `- ` Aufzählung · `1. ` Nummerierung ·
GFM-Tabellen · `**fett**` · `*kursiv*` · `---` Trenner · `> ` Hinweiskasten.

Ein Hinweiskasten bekommt eine Titelzeile, wenn dessen erster Absatz auf einen
Doppelpunkt endet — dazwischen muss eine leere `>`-Zeile stehen:

```markdown
> Kurz gefasst:
>
> Der eigentliche Kastentext.
```

Drei Marker, jeweils allein in einer Zeile:

| Marker | Wirkung |
|---|---|
| `{{INHALTSVERZEICHNIS}}` | setzt das Inhaltsverzeichnis ein |
| `{{SEITENUMBRUCH}}` | harter Seitenumbruch |
| `{{LEERZEILE}}` | vertikaler Abstand |

## Band 3 — Rezeptbuch

Rezepte liegen **strukturiert als YAML** in `rezepte/rezepte/*.yaml`, nicht als
Fließtext. Zwei Gründe: Das Layout bleibt über alle Rezepte gleich, und
`zutaten_check.py` kann jede Zutat gegen die Regeln der Phase prüfen, in der
das Rezept stehen soll.

```yaml
rezepte:
  - name: Kräuteromelett
    tagesfarbe: weiss        # weiss | gruen | stabilisierung |
                             #   fruehstueck | grundrezept
    portionen: 1
    zeit_min: 10
    eiweiss_g: 13
    zutaten: ["2 Eier", "1 TL Kokosöl"]
    schritte: ["Eier verquirlen …"]
    tipp: optional
```

Der Prüfer kennt drei Verbotsstufen: immer verboten (Salz, Zucker, Zwiebeln,
Getreide …), an weißen Tagen zusätzlich verboten (jedes Gemüse, jedes Obst)
und erst ab der Stabilisierungsphase erlaubt (Milchprodukte, Nüsse,
Wurzelgemüse, kleine Mengen Kohlenhydrate). Er läuft ohne Treffer durch —
neue Rezepte müssen das ebenfalls.

Ein Rezept bricht nie über zwei Seiten: Alle Absätze außer dem letzten
tragen `keep_with_next`.

**Format 8″ × 10″ und ein breiter Außensteg.** Beim Kochen liegt das Buch
flach auf der Arbeitsfläche, und man liest im Stehen aus einem Meter
Entfernung — dafür ist das Großformat das nützlichere Maß.

Es bringt aber ein Problem mit: Über die volle Seitenbreite gesetzt kämen
110 Zeichen in die Zeile. Gut lesbar sind 60 bis 75; ab etwa 90 verliert das
Auge beim Zeilenwechsel den Anschluss und springt in dieselbe Zeile zurück.
Korrigiert ist das von zwei Seiten: **12,5 pt** in `rezept_stile()` und
**42 mm Außensteg** in `rezepte.yaml`. Zusammen ergibt das 72 Zeichen im
Mittel. Nur an der Schrift zu drehen hätte 14,5 pt gebraucht, nur am Rand
einen Außensteg von 95 mm.

Wer am Format oder an den Rändern dreht, sollte die Zeilenlänge nachmessen —
sie ist die Kennzahl, an der dieses Layout hängt.

Die Seitenzahl wird automatisch gerade gemacht — bei ungerader Zahl baut das
Skript einen zweiten Durchlauf mit Leerseite am Ende, weil KDP sonst selbst
ein unbeschriftetes Blatt einschiebt.

## Rechtliche Leitplanken

- **Eigenständigkeit:** Fakten, Mengen und Listen stammen aus dem
  cellRESET-Ernährungskonzept, jede Formulierung ist neu. Keine Textpassagen
  und keine Grafiken übernehmen.
- **HCVO:** keine krankheitsbezogenen Aussagen, keine Wirkversprechen.
  `claim_check.py` prüft das automatisch und muss ohne Treffer durchlaufen.
- **Marke:** „cellRESET" und „FitLine" sind Marken der PM-International AG und
  werden nur beschreibend genannt, nie im Titel.
- Pflichthinweise (Schwangerschaft, ärztliche Abklärung, Eigenverantwortung)
  stehen in `buch/kapitel/64-hinweise-haftung.md` und
  `workbook/rahmen/90-rechtliches.md` und dürfen nicht gekürzt werden.
  `abnahme.py` prüft ihr Vorhandensein im fertigen PDF.

## Band 2 — Workbook

Die 84 Tageskarten werden **nicht** von Hand gepflegt. Welcher Tag welche
Farbe hat, steht ausschließlich in `workbook/build/wochenplan.py`; das Layout
erzeugt daraus alles Weitere. Ein Blick auf den Plan:

```bash
python3 workbook/build/wochenplan.py
```

Rahmentexte (Titelei, Anleitung, Anhang) liegen als Markdown in
`workbook/rahmen/`. Die Reihenfolge steuert der Dateiname, die Platzierung das
Feld `position: vorne` oder `position: hinten` im Front Matter.

**Schreiblinien** werden über `schreibzeilen()` als Tabelle gesetzt, nicht als
Absätze mit Unterstrich: Word fasst aufeinanderfolgende Absätze mit gleichem
Rahmen sonst zu einer einzigen Linie zusammen.

**Format 8″ × 10″, nicht A4.** A4 (8,27″ × 11,69″) wäre für ein Heft zum
Ausfüllen minimal besser, steht bei KDP aber nicht in der Auswahlliste der
Trimmgrößen und muss von Hand als benutzerdefinierte Größe eingetragen werden.
Wird stattdessen eine Größe aus der Liste gewählt, prüft KDP Innenteil und
Umschlag gegen die falschen Sollmaße und weist beides zurück. 8″ × 10″ kommt
aus der Liste und kostet gegenüber A4 nur 17 Prozent Fläche.

Wer das Format wieder ändert, muss zwei Zahlen nachmessen: die Schreiblinien im
Wochenauftakt und im Wochenrückblick. Beide Seiten sind auf die Seitenhöhe
ausgemessen, und schon eine Zeile zu viel schickt jede der zwölf Wochen auf
eine zweite Seite.

**Kein Farbdruck einplanen.** Jede Tagesfarbe trägt zusätzlich ihre
Beschriftung (WEISS / GRÜN / ROT), damit der Band auch in Schwarz-Weiß
funktioniert — KDP-Farbdruck verteuert das Buch erheblich.
