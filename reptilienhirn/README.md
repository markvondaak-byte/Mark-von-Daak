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

## Umschlag

```bash
python3 reptilienhirn/build/build_cover.py     # nach dem Innenteil!
python3 buch/build/cover_flach.py              # KDP-Druckfassung
```

Die Rückenbreite errechnet sich aus der Seitenzahl des fertigen PDFs — der
Umschlag muss deshalb **nach** dem Innenteil gebaut werden. Erzeugt werden
`cover.pdf` (Taschenbuch) und `cover-hardcover.pdf`; bei 114 Seiten liegt der
Band über KDPs Hardcover-Grenze von 75 Seiten.

Gezeichnet wird von `buch/build/build_cover.py`. Dieser Band setzt dort drei
Felder aus `reptilienhirn.yaml` ein, die es vorher nicht gab:

| Feld | Wert | wozu |
|---|---|---|
| `cover_akzent` | `bernstein` | warmes `#E8B27A`, als einziger Akzent der Sammlung warm — der Band trägt ein kühles Graumotiv statt der bunten Lebensmittelauslage |
| `cover_kennung` | `SACHBUCH · GEHIRN` | der gefüllte Balken über dem Titel |
| `markenhinweis` | eigener Text | ohne ihn stünde der cellRESET-Hinweis der Stoffwechsel-Reihe auf der Rückseite |

Ohne diese Felder erbt ein Band stillschweigend die Identität von Band 1. Das
ist genau einmal passiert und im Vorschaubild aufgefallen: „DAS BUCH ·
4 PHASEN" über einem Buch über Hirnforschung.

**Wer am Akzent dreht, rechnet den Kontrast nach.** Die Farbe steht auf dem
gefüllten Balken und in der Autorenzeile, dafür sind 3:1 gefordert; Bernstein
liegt bei 3,30 bzw. 3,66 zu 1 gegen die beiden Schiefertöne. Jede Aufhellung
des Grundes kostet Kontrast.

### Das Titelbild

`reptilienhirn/cover/titelbild.jpg` — Porträt eines Neandertalers, 5504 x 3072
px, deutlich über den nötigen 1838 x 1118. Der dunkle Grund des Fotos liegt
farblich nah am Schieferton, deshalb geht die Ausblendung an der Unterkante
sauber auf.

**Das Bild ist KI-erzeugt** (Higgsfield, Modell Nano Banana Pro). Das ist bei
KDP anzugeben — siehe `kdp-metadaten.md`, Abschnitt „KI-erzeugte Inhalte
melden". Für das Titelbild lautet die Antwort auf KDPs Frage nach
KI-generierten Inhalten also **ja**, Kategorie Bilder.

Ein Motiv, das den Titel bestätigt statt ihn zu bebildern: Das Buch nimmt die
Erzählung vom archaischen Vorfahren im Kopf auseinander, und der Umschlag setzt
genau diese Erwartung — Kapitel 2 räumt sie dann ab. Bewusst kein
Höhlenmensch-Klischee: kein Keulenschwingen, kein gefletschtes Gebiss, ruhiger
Blick.

Wird das Motiv getauscht, gelten die Anforderungen aus der Tabelle unten. Ohne
Datei bricht `build_cover.py` mit einem Hinweis ab, statt auf das Foto der
Stoffwechsel-Reihe oder die gezeichnete Lebensmittelauslage zurückzufallen —
beides fiele erst am fertigen Umschlag auf.

| | |
|---|---|
| Ablage | `reptilienhirn/cover/titelbild.jpg` (auch `.png`, `.jpeg`, `.webp`) |
| Mindestgröße | **1838 x 1118 px** — gerechnet von `titelbild_sollmasse()` aus der Seitengröße, nicht geraten |
| Seitenverhältnis | egal, es wird mittig auf das Format beschnitten |
| Motiv | Bildmitte freihalten; die Unterkante wird in den Schieferton ausgeblendet |

Das Foto füllt nur das obere Band der Vorderseite, nicht den ganzen Umschlag.
Reicht die Auflösung nach dem Beschnitt nicht für 300 dpi, rechnet das Skript
hoch und meldet das.

**Herkunft klären, bevor ein anderes Bild eingesetzt wird.** Stammt es von
einem Bildanbieter, muss die Lizenz die kommerzielle Nutzung auf einem
Buchumschlag abdecken; viele Standardlizenzen schließen genau das aus.
Erkennbare reale Personen brauchen eine Einwilligung.

## Was noch offen ist

- **Endabnahme.** `buch/build/abnahme.py` prüft bisher nur die drei Bände der
  Stoffwechsel-Reihe. Die Prüfungen zum Barcodefeld — Wörter im Feld,
  Helligkeit, Abstand zur Unterkante — gelten für diesen Umschlag genauso und
  sollten auf ihn ausgeweitet werden, bevor er zu KDP geht.
- **E-Book.** `buch/build/build_epub.py` und `kindle_cover.py` kennen den Band
  noch nicht. Der Band ist fließender Text wie Band 1, der Pfad wäre derselbe.
- **KI-Angabe bei KDP.** Beim Einstellen ist das Titelbild als KI-erzeugt zu
  melden. Das ist keine Formalie — eine falsche Angabe kann das Konto kosten.
