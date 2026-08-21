# Was uns die Maschine abnimmt — Buchprojekt

Ein eigenständiges Sachbuch über Künstliche Intelligenz. Es gehört **nicht**
zur Stoffwechsel-Reihe und hat eigene Metadaten, eigene Kategorien und einen
eigenen Umschlag — geteilt wird nur die Satz-Werkstatt unter `buch/build/`.

| | |
|---|---|
| Format | 6″ × 9″, 124 Seiten |
| Aufbau | 5 Teile, 34 Kapitel, rund 25 000 Wörter |
| Ausgaben | Taschenbuch, Hardcover und Kindle |

## Bauen

```bash
pip install -r buch/requirements.txt

python3 ki/build/build_ki.py            # Innenteil: .docx und .pdf
python3 ki/build/build_cover.py         # beide Umschläge und Kindle-Titelbild
python3 buch/build/cover_flach.py \
    ki/out/cover.pdf ki/out/cover-hardcover.pdf      # KDP-Druckfassungen
python3 ki/build/build_epub.py          # Kindle-Ausgabe

python3 buch/build/rechtschreibung.py   # prüft dieses Buch mit
```

Die Reihenfolge ist nicht beliebig: Die Rückenbreite des Umschlags errechnet
sich aus der Seitenzahl des fertigen Innenteils, und das EPUB braucht das
Titelbild, das `build_cover.py` erzeugt.

### Hardcover

`build_cover.py` baut **zwei** Umschläge: `cover.pdf` fürs Taschenbuch und
`cover-hardcover.pdf` fürs gebundene Buch. KDP rechnet dafür anders, und zwar
in zwei Punkten:

| | Taschenbuch | Hardcover |
|---|---|---|
| Rand ringsum | 3,175 mm Anschnitt (wird abgeschnitten) | 18,0 mm Umschlagrand (wird um die Decke geschlagen) |
| Rücken | Buchblock: Seiten × 0,0572 mm | Buchdecke: Seiten × 0,0572 mm **+ 9 mm** für Pappen und Falzrillen |
| Rückentext | erst ab 79 Seiten | immer — die Decke bringt allein 9 mm mit |

Bei 124 Seiten ergibt das **356,88 × 264,59 mm = 14,050 × 10,417 Zoll** mit
einem Rücken von 16,1 mm. Die Konstanten kommen aus
`buch/build/build_cover.py` und stehen dort in Zoll, nicht in Millimetern: KDP
rechnet in Zoll, und runde Millimeterwerte (18,0 / 9,0) treffen die Sollbreite
um 0,03 mm daneben.

KDP nimmt Hardcover erst **ab 75 Seiten** an; darunter überspringt das Skript
die Fassung mit einem Hinweis.

**Der Innenteil ist für beide derselbe.** Nur der Umschlag unterscheidet sich —
bei KDP sind Taschenbuch und Hardcover trotzdem zwei getrennte Titel.

**Zu KDP hochgeladen wird `cover-druck.pdf`, nicht `cover.pdf`** (beim
Hardcover entsprechend `cover-hardcover-druck.pdf`)**.** Die
Vektorfassung enthält transparente Kanten im Netzmotiv; die KDP-Prüfung
verlangt reduzierte Ebenen ohne Transparenz und lehnt sie ab. `cover_flach.py`
rastert den Umschlag bei 300 dpi und meldet anschließend, ob die Datei sauber
ist. Die Vektorfassung bleibt die Quelle für Korrekturen.

### Systemvoraussetzung

`libreoffice-writer` muss installiert sein — `libreoffice-core` allein genügt
nicht und führt zu „source file could not be loaded“:

```bash
apt-get update && apt-get install -y libreoffice-writer
```

## Was hier eigen ist und was geteilt wird

Renderer, Absatzformate, PDF-Erzeugung, EPUB-Gerüst und die Umschlaggeometrie
kommen aus `buch/build/`. Dieses Verzeichnis enthält nur die Abweichungen:

| Datei | Was sie hinzufügt |
|---|---|
| `build/build_ki.py` | Typografie und Leitfarbe des Bandes |
| `build/build_cover.py` | das Netzmotiv, Vorder- und Rückseite, Kindle-Titelbild |
| `build/build_epub.py` | eigene Kennung, sonst dieselbe Bauart wie Band 1 |

**An `buch/build/stile.py` wird dafür nichts geändert.** Die Formate dort
gelten für alle Bände der Stoffwechsel-Reihe mit; wer sie verstellt, um dieses
Buch zu justieren, verschiebt drei andere Bücher gleich mit. `dokument_anlegen()`
nimmt deshalb einen zweiten Parameter mit Abweichungen — `TYPOGRAFIE` in
`build/build_ki.py` setzt sie.

Dasselbe gilt für die Farben: Das Blattgrün in `stile.py` ist die Leitfarbe der
Ernährungsbände. Dieses Buch überschreibt sie je Absatzformat mit einem tiefen
Schieferblau. Kontrast auf Papierweiß: 8,7:1 für die Leitfarbe, 4,6:1 für die
aufgehellte Variante — beide stehen auch in Normalgröße und müssen die 4,5:1
halten. Wer aufhellt, muss nachrechnen.

## Umschlaggestaltung

Das Motiv ist ein Netz aus Knoten und Kanten, das über Rückseite, Rücken und
Vorderseite durchläuft und nach unten ausläuft. Gezeichnet wird es aus einem
festen Zufallskeim (`NETZ_KEIM`): Der Umschlag sieht bei jedem Lauf gleich
aus — sonst ließe sich eine Textkorrektur nicht von einer Bildänderung
unterscheiden.

Verbunden wird jeder Knoten mit seinen **nächsten Nachbarn**, nicht mit allem
innerhalb eines Radius: Ein fester Radius ergibt in dichten Bereichen ein
Knäuel und in dünnen gar nichts. Über die nächsten Nachbarn entsteht ein
gleichmäßig trianguliertes Gitter. Gezeichnet wird es in zwei Ebenen — eine
ferne, kleinere und dunklere hinter einer nahen, kräftigen; ohne sie wirkt das
Netz wie eine flach aufgelegte Folie.

Die Knotenzahl ergibt sich aus der **Fläche** (`FLAECHE_JE_KNOTEN`), nicht als
feste Zahl. Das Kindle-Titelbild ist halb so breit wie der aufgeklappte
Umschlag; mit einer festen Knotenzahl zeigte es im ersten Versuch einzelne
Punkte ohne Verbindungen. Der Wert ist am Aussehen ausgemessen: Bei 520 las
sich das Gitter nicht als Gewebe, sondern als einzelne große Punkte mit
Strichen dazwischen. Wer daran dreht, sollte beide Ausgaben ansehen.

Der Untergrund ist ein Verlauf aus 140 Streifen, kein Shading-Objekt.
reportlab würde für einen echten Verlauf genau das anlegen, was `cover_flach.py`
anschließend als Beanstandung meldet.

**Titelbild statt Netz.** Liegt in `ki/cover/` eine Datei `titelbild.jpg`
(auch `.jpeg`, `.png`, `.webp`), tritt sie an die Stelle des gezeichneten
Netzes: Sie füllt den oberen Teil der **Vorderseite** samt Anschnitt oben und
außen, Rückseite und Rücken bleiben im Grundton. Nötig sind mindestens
**1838 × 1276 px**; `build_cover.py` rechnet das Maß aus der Seitengröße aus
und meldet beim Bauen, was vorliegt und was fehlt.

**Das Motiv steht auf der Vorderseite, nicht über dem ganzen Umschlag.**
Anfangs lief das Gitter durchgehend über Rückseite, Rücken und Vorderseite. Als
aufgeklappte Fläche sah das gut aus und kostete Platz an der einzigen Stelle,
an der er knapp ist: Der Klappentext musste sich auf 98 Prozent verkleinern.
Auf die Vorderseite beschränkt (`MOTIV_HOEHE` 0,46) darf das Motiv fast die
halbe Seite nehmen, die Rückseite behält ihren vollen Satzspiegel und lässt
oben nur einen ruhigen Kopfsteg frei (`RUECKEN_KOPFSTEG`). Für ein Titelbild
gilt dieselbe Fläche — beide Motivarten sind austauschbar.

Der Titelblock richtet sich automatisch danach: Er wird im freien Feld unter
der Motivunterkante zentriert, und die wird übergeben — an `BILD_HOEHE` zu
drehen verschiebt ihn mit, ohne dass etwas nachzurechnen wäre.

Warum nur die Vorderseite: Ein Motiv, das am Rücken in ein anderes übergeht,
hat quer über den flach ausgelegten Umschlag eine sichtbare Kante. Ein Bild
über die volle Umschlagbreite wäre die Alternative, bräuchte aber ein
Seitenverhältnis von 4,5:1 — dafür gibt es kaum brauchbares Material. Die
Stoffwechsel-Reihe löst es genauso.

**Der Umschlaggrund richtet sich nach dem Bild, nicht umgekehrt.**
`grundton_aus_bild()` misst den Median des unteren Bildrandes — dort ist das
Motiv ausgelaufen, dort steht nur noch der Grund — und färbt Rückseite und
Rücken damit ein. Ohne das trennt eine Tonkante Vorder- und Rückseite quer über
den flach ausgelegten Umschlag; schon wenige Prozent Unterschied sind zu sehen.
Gemeldet wird der übernommene Ton bei jedem Lauf, und ist er zu hell für die
weiße Umschlagschrift, sagt das Skript das ebenfalls.

Die Unterkante des Bildes wird **ins Bild hinein** in genau diesen Ton
ausgeblendet, nicht als transparenter Verlauf darüber: Die KDP-Druckfassung
darf keine Transparenz enthalten.

**Herkunft des Bildes klären, bevor es eingesetzt wird.** Ist es KI-erzeugt,
ist das bei KDP anzugeben (`ki/kdp-metadaten.md`, Abschnitt „KI-erzeugte
Inhalte melden"), und die Offenlegung in `ki/kapitel/01-impressum.md` und
`63-hinweise.md` ist zu ergänzen — ein Buch, das von anderen Transparenz über
KI-Einsatz verlangt, kann sie beim eigenen Umschlag nicht weglassen. Stammt es
von einem Bildanbieter, muss die Lizenz die kommerzielle Nutzung auf einem
Buchumschlag abdecken; viele Standardlizenzen schließen genau das aus.

**Vorderseite.** Titel, Trennstrich, Untertitel und Autorenzeile bilden einen
Block, der erst ausgemessen und dann in der Höhe ausgerichtet wird — nicht auf
der Seite, sondern im freien Feld zwischen der Unterkante des Motivs und der
unteren Trimmkante. Und nicht genau mittig darin, sondern um `BLOCK_HEBUNG`
(0,12 der Feldhöhe, rund 13 mm) darüber: Ein geometrisch zentrierter Block
wirkt in einem hohen Feld zu tief, und das Motiv hat oben Gewicht, dem der
Titel entgegenkommen darf. Auf die Seitenmitte bezogen säße er halb im Netz; an festen
Bruchteilen der Seitenhöhe aufgehängt sitzt er zu tief. Gemessen wird über die
Versalhöhe der obersten Titelzeile, nicht über die Oberkante des Schriftkastens
— optisch zentriert ist ein Titel an seinen Großbuchstaben, nicht an der
unsichtbaren Oberlänge darüber.

**Rückseite.** Der Klappentext sucht sich seine Schriftgröße selbst: Er muss
über dem freizuhaltenden Barcodefeld enden, und ein Umschlag, bei dem beides
übereinanderliegt, fällt am Bildschirm kaum auf und im Druck teuer. Fällt die
Größe unter etwa 90 Prozent, ist der Klappentext zu lang — dann kürzen, nicht
weiter verkleinern. Das Barcodefeld wird weiß angelegt; auf dunklem Grund wäre
der Code nicht scannbar.

**Kindle-Titelbild.** Amazon empfiehlt 1600 × 2560 Pixel, also das Verhältnis
1,6; der gedruckte Band hat 1,5. Das Bild wird deshalb neu gesetzt statt aus
dem Umschlag ausgeschnitten — beim Ausschneiden müsste oben Motiv weichen.

## Kapitel schreiben

Wie bei Band 1: Jede Datei in `ki/kapitel/` beginnt mit YAML-Front-Matter, die
Reihenfolge ergibt sich aus dem Dateinamen.

```markdown
---
typ: kapitel          # titelei | teil | kapitel
nummer: 3             # erscheint im Inhaltsverzeichnis
titel: Was ein Sprachmodell wirklich tut
kopfzeile: Was Sprachmodelle tun
---
```

Unterstützte Auszeichnung, Hinweiskästen und die drei Marker
(`{{INHALTSVERZEICHNIS}}`, `{{SEITENUMBRUCH}}`, `{{LEERZEILE}}`) sind in
`buch/README.md` beschrieben und gelten hier unverändert.

Die Nummernkreise der Dateinamen folgen den Teilen: `0x` Titelei, `1x` Teil I,
`2x` Teil II, `3x` Teil III, `4x` Teil IV, `5x` Teil V, `6x` Anhang. Innerhalb
von Teil III sind neun Kapitel untergebracht — wer einen zehnten braucht,
verschiebt die Grenze, statt eine Datei zwischen zwei Nummern zu quetschen.

`build_ki.py` läuft **zweimal** durch: Der erste Durchlauf ermittelt die
Seitenzahlen, der zweite setzt damit das Inhaltsverzeichnis. Fällt die
Seitenzahl ungerade aus, folgt ein dritter Durchlauf mit Vakatseite am Ende —
KDP verlangt eine gerade Seitenzahl und schiebt sonst selbst ein Blatt ein.

## Inhaltliche Leitplanken

- **Keine Prognose mit Jahreszahl.** Das Buch arbeitet mit Szenarien und
  Anzeichen. Wer eine Jahreszahl einfügt, widerspricht Teil IV.
- **Nutzen und Kosten getrennt nach Belegbarkeit**: was heute trägt, was sich
  abzeichnet, was Erzählung ist. Diese Dreiteilung zieht sich durch Teil II
  und III und sollte nicht aufgeweicht werden.
- **Keine Firmennamen als Beleg.** Sachverhalte werden beschrieben, nicht
  Unternehmen an den Pranger gestellt — Namen veralten schneller als der
  Sachverhalt, und ohne sie ist das Argument genauso stark.
- **Zahlen als Größenordnung.** Der Gegenstand verändert sich schnell; das
  Kapitel „Wichtige Hinweise“ sagt das ausdrücklich. Wer eine präzise Zahl
  einfügt, veraltet das Buch.
- **Die Offenlegung im Impressum und in „Wichtige Hinweise“ bleibt stehen.**
  Ein Buch, das von anderen Transparenz über KI-Einsatz verlangt, muss sie
  selbst leisten — und die Angabe muss mit der KDP-Meldung übereinstimmen
  (`ki/kdp-metadaten.md`).

## Metadaten für den Verkauf

`ki/kdp-metadaten.md` — Trimmgröße, Rückenbreite, Kategorien, Keywords,
KI-Meldung. `ki/cover/amazon-beschreibung.md` — Produktbeschreibung in zwei
Fassungen, zum Lesen und als KDP-taugliches HTML.

Beide enthalten Zahlen aus dem letzten Build. Wer den Innenteil ändert, zieht
sie nach.
