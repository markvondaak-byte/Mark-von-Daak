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
| `cover_kennung` | `""` (leer) | **kein** Balken über dem Titel — der Band gehört zu keiner Reihe, die Kennung unterschiede also nichts |
| `barcode_weissflaeche` | beide `false` | keine Weißfläche unter dem Barcodefeld, auch nicht beim Taschenbuch |
| `markenhinweis` | eigener Text | ohne ihn stünde der cellRESET-Hinweis der Stoffwechsel-Reihe auf der Rückseite |

Ohne diese Felder erbt ein Band stillschweigend die Identität von Band 1. Das
ist genau einmal passiert und im Vorschaubild aufgefallen: „DAS BUCH ·
4 PHASEN" über einem Buch über Hirnforschung. **`cover_kennung` deshalb leer
lassen und nicht weglassen** — ein fehlendes Feld fällt auf genau diesen Wert
zurück.

**Zur abgeschalteten Weißfläche.** KDP druckt den Barcode in einer eigenen
weißen Box; die Fläche darunter ist deckungsgleich und damit unsichtbar. Sie
war eine Rückversicherung für den Fall, dass KDP ohne eigene Box druckt — dann
stünde schwarze Strichschrift auf dem Schiefergrund und wäre nicht zu scannen.
Dieser Band verzichtet bei **beiden** Bindearten darauf; die Bände 1 bis 3
behalten sie beim Taschenbuch. `abnahme.py` prüft entsprechend nicht mehr auf
Helligkeit, sondern darauf, dass der Grund dort ruhig ist (Kanalwerte 84 bis
85). Beim ersten Belegexemplar nachsehen.

**Wer am Akzent dreht, rechnet den Kontrast nach.** Die Farbe steht auf dem
gefüllten Balken und in der Autorenzeile, dafür sind 3:1 gefordert; Bernstein
liegt bei 3,30 bzw. 3,66 zu 1 gegen die beiden Schiefertöne. Jede Aufhellung
des Grundes kostet Kontrast.

### Das Titelbild

`reptilienhirn/cover/titelbild.jpg` — der Neandertaler betrachtet ein
Gehirn aus Stein auf einem Sockel. Beide Motive in einer Aufnahme, gleiches
Licht, gleicher Grund. Das Bild erzählt die These des Buches, ohne sie zu
behaupten: Der Umschlag setzt die Erwartung vom archaischen Vorfahren, die
Kapitel 2 dann abräumt.

**Das Bild ist KI-erzeugt** (Higgsfield, Nano Banana Pro; aus zwei früheren
Generierungen als Referenz zusammengesetzt). Bei KDP ist das anzugeben —
siehe `kdp-metadaten.md`, Abschnitt „KI-erzeugte Inhalte melden". Antwort auf
die Frage nach KI-generierten Inhalten: **ja**, Kategorie Bilder.

Als Alternative liegt `titelbild-alternative-portraet.jpg` daneben — dasselbe
Gesicht allein, ohne Gehirn. Bei sehr kleinen Vorschaubildern trägt ein
einzelnes Gesicht sicherer als zwei Motive; wer das ausprobieren will, tauscht
die Dateinamen.

#### Warum das Bild oben 275 px Zugabe hat

Die Originaldatei war 5504 x 3072 px. In dieser Fassung wurde der Hintergrund
oben um 275 px verlängert — die oberste Bildzeile nach oben gestreckt, deshalb
ohne sichtbare Naht. Grund: `titelbild_zeichnen()` zeichnet das Foto um den
Anschnitt über die Trimmkante hinaus, und dabei wurde dem Neandertaler das Haar
abgeschnitten.

Die 275 px sind keine runde Zahl, sondern die Obergrenze. Beschnitten wird
mittig auf das Verhältnis 1838:1118 = 1,6440. Solange das Bild **breiter** als
dieses Verhältnis ist, beschneidet die Routine die Seiten und lässt die Höhe
unangetastet; kippt es darunter, beginnt sie die Höhe zu beschneiden und nimmt
die Zugabe gleich wieder weg. Bei 5504 px Breite liegt die Grenze also bei
5504 / 1,6440 = 3348 px Höhe, und 3348 − 3072 = 276. Die Datei liegt mit
5504 x 3347 knapp darunter.

Wer das Motiv tauscht, prüft dasselbe: Verhältnis über 1,6440 halten, sonst
verschwindet oben genau das, was man dazugegeben hat.

| | |
|---|---|
| Ablage | `reptilienhirn/cover/titelbild.jpg` (auch `.png`, `.jpeg`, `.webp`) |
| Mindestgröße | **1838 x 1118 px** — gerechnet von `titelbild_sollmasse()`, nicht geraten |
| Verhältnis | über 1,6440 halten, sonst wird die Höhe beschnitten |
| Motiv | oben Luft lassen (Anschnitt), unten wird in den Schieferton ausgeblendet |

Ohne Titelbild bricht `build_cover.py` mit einem Hinweis ab, statt auf das Foto
der Stoffwechsel-Reihe oder die gezeichnete Lebensmittelauslage
zurückzufallen — beides fiele erst am fertigen Umschlag auf.

**Herkunft klären, bevor ein anderes Bild eingesetzt wird.** Stammt es von
einem Bildanbieter, muss die Lizenz die kommerzielle Nutzung auf einem
Buchumschlag abdecken; viele Standardlizenzen schließen genau das aus.
Erkennbare reale Personen brauchen eine Einwilligung.

## Endabnahme

```bash
python3 buch/build/innenteil_druck.py     # Innenteil auf Trimmgröße
python3 buch/build/cover_flach.py         # Umschläge in die KDP-Druckfassung
python3 buch/build/abnahme.py             # 43 Prüfungen für diesen Band
```

`abnahme.py` kennt den Band als eigenen Abschnitt. Geprüft wird dasselbe wie
bei den anderen Bänden, mit zwei Abweichungen:

**Andere Pflichttexte.** Dieser Band macht keine Ernährungsaussagen und
braucht weder Schwangerschaftshinweis noch HCVO-Prüfung. Er berührt dafür
Panik, Angst und Suizidgedanken und muss die Grenze zur fachlichen Hilfe samt
Notrufnummern führen — die Abnahme prüft Telefonseelsorge, 116 117 und 112
einzeln. Zusätzlich prüft sie, dass **kein** cellRESET- oder FitLine-Bezug im
Innenteil steht.

**Suchbegriffe über Zeilenumbrüche.** Die Prüfung zieht den Text vor dem
Suchen zusammen. Ohne das prüft ein mehrwortiger Suchbegriff den Umbruch statt
den Inhalt und meldet Text als fehlend, der auf der Seite steht — das ist beim
ersten Lauf dreimal passiert.

Die Reihenfolge ist nicht beliebig: Innenteil, dann Umschlag (die Rückenbreite
hängt an der Seitenzahl), dann die Druckfassungen, dann die Abnahme. Sie prüft
unter anderem, dass kein PDF älter ist als seine Quellen — sonst winkt sie
einen alten Stand durch.

## Was noch offen ist

- **E-Book.** `buch/build/build_epub.py` und `kindle_cover.py` kennen den Band
  noch nicht. Der Band ist fließender Text wie Band 1, der Pfad wäre derselbe.
- **KI-Angabe bei KDP.** Beim Einstellen ist das Titelbild als KI-erzeugt zu
  melden. Das ist keine Formalie — eine falsche Angabe kann das Konto kosten.
- **Belegexemplar ansehen.** Unter dem Barcodefeld liegt bei **beiden**
  Bindearten bewusst keine Weißfläche, weil KDP seine eigene Box mitbringt.
  Gesehen hat das im gedruckten Buch noch niemand; der Blick aufs erste
  Exemplar lohnt und entscheidet, ob die Fläche zurückkommen muss.
