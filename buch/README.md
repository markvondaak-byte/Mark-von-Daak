# Der Stoffwechsel-Reset — Buchprojekt

Zwei eigenständige Bände, gemeinsame Build-Basis:

| Band | Quelle | Format | Ausgabe |
|---|---|---|---|
| 1 — Das Buch | `buch/kapitel/*.md` | 6″ × 9″ | `buch/out/stoffwechsel-reset.{docx,pdf}` |
| 2 — Das Workbook | `workbook/` | 8,27″ × 11,69″ | `workbook/out/workbook.{docx,pdf}` |
| 3 — Das Rezeptbuch | `rezepte/` | 6″ × 9″ | `rezepte/out/rezeptbuch.{docx,pdf}` |

## Bauen

```bash
pip install -r buch/requirements.txt

python3 buch/build/build_docx.py           # Band 1: .docx und .pdf
python3 buch/build/build_cover.py          # Umschlag Band 1

python3 workbook/build/build_workbook.py   # Band 2: .docx und .pdf
python3 workbook/build/build_cover.py      # Umschlag Band 2

python3 rezepte/build/build_rezepte.py     # Band 3: .docx und .pdf
python3 rezepte/build/build_cover.py       # Umschlag Band 3

python3 buch/build/claim_check.py          # HCVO-Prüfung, muss ohne Fehler laufen
python3 rezepte/build/zutaten_check.py     # Rezepte gegen die Phasenregeln
python3 buch/build/abnahme.py              # Endabnahme aller drei Bände
```

Die Umschläge müssen **nach** dem jeweiligen Innenteil gebaut werden — die
Rückenbreite errechnet sich aus der Seitenzahl des fertigen PDFs.

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

**Kein Farbdruck einplanen.** Jede Tagesfarbe trägt zusätzlich ihre
Beschriftung (WEISS / GRÜN / ROT), damit der Band auch in Schwarz-Weiß
funktioniert — KDP-Farbdruck verteuert das Buch erheblich.
