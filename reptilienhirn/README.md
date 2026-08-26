# Das Reptiliengehirn des Menschen — Buchprojekt

Eigenständiger Band, gleiche Build-Basis wie die Stoffwechsel-Reihe.

| | |
|---|---|
| Quelle | `reptilienhirn/kapitel/*.md` |
| Format | 6″ × 9″ (wie Band 1) |
| Ausgabe | `reptilienhirn/out/reptiliengehirn.{docx,pdf}` |

## Bauen

```bash
pip install -r buch/requirements.txt
python3 reptilienhirn/build/build_reptilienhirn.py
```

Das Skript läuft zwei- bis dreimal durch: Der erste Durchlauf ermittelt die
Seitenzahlen, der zweite setzt damit das Inhaltsverzeichnis, ein dritter folgt
nur, wenn die Seitenzahl ungerade ausfällt — KDP verlangt eine gerade
Seitenzahl und schöbe sonst selbst ein unbeschriftetes Blatt ein.

**Systemvoraussetzung:** `libreoffice-writer` muss installiert sein —
`libreoffice-core` allein genügt nicht und führt zu „source file could not be
loaded“:

```bash
apt-get update && apt-get install -y libreoffice-writer
```

## Der Satz kommt aus Band 1

`build/build_reptilienhirn.py` importiert `buch/build/build_docx.py` und setzt
nur die eigenen Pfade und die eigene Metadatendatei. Absatzformate, Kopfzeilen,
Titelei-Behandlung und Teil-Trennseiten sind dieselben wie in der
Stoffwechsel-Reihe.

**Wer am Satz etwas ändern will, ändert es dort — nicht hier.** Eine Kopie der
Satzlogik in diesem Verzeichnis würde die Bände auseinanderlaufen lassen; genau
davor warnt auch `buch/README.md` im Abschnitt zur Typografie.

## Kapitel schreiben

Jede Datei in `kapitel/` beginnt mit YAML-Front-Matter:

```markdown
---
typ: kapitel          # titelei | teil | kapitel
nummer: 7             # Kapitelnummer; im Anhang weggelassen
titel: Was der Körper dazu sagt
kopfzeile: Der Körper # steht in der Kopfzeile der rechten Seiten
---

# Was der Körper dazu sagt

Fließtext …
```

Die Reihenfolge ergibt sich aus dem Dateinamen. Das Nummernschema hält die
Teile auseinander:

| Bereich | Dateien |
|---|---|
| Titelei | `00`–`03` |
| Teil I — Das schnelle Ich | `10`–`13` |
| Teil II — Der Maschinenraum | `20`–`26` |
| Teil III — Die Auslöser | `30`–`35` |
| Teil IV — Die Schauplätze | `40`–`47` |
| Teil V — Die Werkzeuge | `50`–`57` |
| Teil VI — Das Bild und die Verkäufer | `60`–`62` |
| Anhang | `70`–`73` |

Unterstützte Auszeichnung und die Marker `{{INHALTSVERZEICHNIS}}`,
`{{SEITENUMBRUCH}}`, `{{LEERZEILE}}` sind in `buch/README.md` beschrieben.

## Aufbau des Buches

Sechs Teile, 30 Kapitel. Der Aufbau ist situationsgetrieben, nicht
wissenschaftsgeschichtlich: Die Richtigstellung des dreieinigen Modells steht
kompakt in Kapitel 2 und nicht in einem eigenen Teil, damit der Rest des Buches
von der Sache handeln kann.

Zwei Bauentscheidungen, die man kennen sollte, bevor man daran dreht:

**Kapitel 21 („Wo du Hilfe brauchst“) steht vor dem Praxisteil, nicht
dahinter.** Ein Buch, das Techniken beschreibt, erweckt sonst den Eindruck,
alles sei eine Frage der richtigen Technik. Die Grenze gehört davor.

**Teil V endet mit vier Wochen zum Durcharbeiten, eine Sache pro Woche.** Das
ist die Konsequenz aus Kapitel 26: Mehrere Änderungen gleichzeitig
vervielfachen die Gelegenheiten zu scheitern. Wer den Plan erweitert, hebt
seine Wirkung auf.

## Querverweise

Die Kapitel verweisen wechselseitig aufeinander („nach Kapitel 9 …“). Die
Verweise nennen **Kapitelnummern**, nicht Seitenzahlen — Seitenzahlen wären
bei jedem Satzlauf neu zu pflegen.

Wird ein Kapitel eingefügt, verschoben oder entfernt, verschieben sich alle
folgenden Nummern und die Verweise stimmen nicht mehr. Vor jeder solchen
Änderung:

```bash
grep -rn "Kapitel [0-9]" reptilienhirn/kapitel/
```

## Rechtliche Leitplanken

- **Keine Heilversprechen, keine Diagnosen.** Das Buch ist ein Sachbuch. Die
  Pflichthinweise stehen in `kapitel/72-hinweise-haftung.md` und dürfen nicht
  gekürzt werden.
- **Notrufnummern** stehen in `kapitel/47-wo-du-hilfe-brauchst.md` und in den
  Pflichthinweisen. Vor jeder Auflage prüfen, ob sie noch gelten.
- **Belegpflicht.** Jede fachliche Aussage im Text muss sich auf eine der in
  `kapitel/71-quellen.md` genannten Arbeiten zurückführen lassen. Wo die
  Fachwelt uneins ist, sagt der Text das ausdrücklich — diese Einschränkungen
  sind Teil der Aussage und nicht redaktioneller Ballast.
- `claim_check.py` prüft die HCVO-Vorgaben der Ernährungsbände und ist für
  diesen Band ohne Belang.

## Offener Punkt: der Umschlag

**Dieser Band hat noch keinen Umschlag.** `buch/build/build_cover.py` zeichnet
über `buch/build/illustration.py` Obst und Gemüse — das passt motivisch nicht.
Ein Umschlag für diesen Band ist ein eigener Arbeitsgang und braucht:

1. ein eigenes Motiv oder eine eigene Illustrationsroutine,
2. ein Umschlagskript nach dem Muster von `buch/build/build_cover.py`
   (Rückenbreite aus der Seitenzahl des fertigen PDFs, Barcodefeld nach den in
   `buch/README.md` dokumentierten Maßen),
3. `buch/build/cover_flach.py` für die KDP-Druckfassung.

Die Umschlagtexte liegen bereits unter `cover/klappentext.md` und
`cover/amazon-beschreibung.md`.
