# KDP-Metadaten — alle vier Titel

Alles, was beim Anlegen eines Titels bei Amazon KDP abgefragt wird, an einer
Stelle zum Kopieren. Die langen Beschreibungstexte stehen in eigenen Dateien,
weil sie dort zusätzlich als KDP-taugliches HTML vorliegen:

- `buch/cover/amazon-beschreibung.md`
- `workbook/cover/amazon-beschreibung.md`
- `rezepte/cover/amazon-beschreibung.md`
- `darm/cover/amazon-beschreibung.md`

Die ersten drei Titel bilden die Reihe „Der Stoffwechsel-Reset“. **„Der Darm
im Gleichgewicht“ hat damit nichts zu tun.** Er wird ohne Serieneintrag
angelegt, nennt weder das Konzept noch die Reihe noch PM-International, und
sein Umschlag trägt nicht den Markenhinweis der Reihe. Gemeinsam sind nur die
Bauskripte — und die stehen auf keinem Buchdeckel.

Das betrifft auch die Autorenbiografie: Für diesen Titel gilt die eigene
Fassung weiter unten, **nicht** die der Reihe.

Die Druckangaben stammen aus dem letzten Build. Ändert sich der Innenteil,
ändern sich Seitenzahl und Rückenbreite — dann hier nachziehen.

---

## Autorenbiografie

Ein eigenes Feld bei KDP, getrennt von der Buchbeschreibung. Sie erscheint
unter „Über den Autor" und im Autorenprofil. Zwei Längen, inhaltlich deckungs-
gleich mit dem Kapitel „Über den Autor" in Band 1 — nichts behaupten, was dort
nicht steht.

**Diese Fassung gilt für Band 1 bis 3.** „Der Darm im Gleichgewicht" hat eine
eigene, in seinem eigenen Abschnitt.

**Kurz (für das KDP-Feld, rund 400 Zeichen)**

> Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der Umstellung
> ihrer Ernährung. Er ist kein Arzt und kein Ernährungsberater mit
> Kammerzulassung — was er mitbringt, ist die Praxis: die Erfahrung aus der
> Begleitung derer, die dieses Konzept tatsächlich umgesetzt haben. Daraus sind
> seine Bücher entstanden. Wo sie an ihre Grenzen kommen, sagen sie das und
> verweisen dorthin, wo es hingehört.

**Lang (für Author Central, rund 900 Zeichen)**

> Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der Umstellung
> ihrer Ernährung.
>
> Er ist kein Arzt, kein Ökotrophologe und kein Ernährungsberater mit
> Kammerzulassung. Was er mitbringt, ist die Praxis: die Erfahrung aus der
> Begleitung von Menschen, die ein Ernährungskonzept über Monate umgesetzt
> haben — mit allem, was dabei schiefgehen kann, und mit den Fragen, die immer
> wieder auftauchen.
>
> Genau daraus sind seine Bücher entstanden. Sie beantworten die Fragen, die in
> der Praxis wirklich gestellt werden, und beschreiben die Stolpersteine, über
> die Menschen tatsächlich stolpern — nicht die, die sich theoretisch denken
> lassen. Sie enthalten keine Produktempfehlungen und kein Versprechen über
> Kilogramm.
>
> Als selbstständiger Vertriebspartner für Nahrungsergänzungsmittel hat er ein
> wirtschaftliches Interesse an diesem Themenfeld. Er schreibt das in seine
> Bücher hinein, statt es zu verschweigen.
>
> Kontakt: markvondaak@icloud.com

---

## Band 1 — Das Buch

| Feld | Wert |
|---|---|
| Titel | Der Stoffwechsel-Reset |
| Untertitel | Das 4-Phasen-Ernährungskonzept in 90 Tagen |
| Serie | Der Stoffwechsel-Reset, Band 1 |
| Autor | Mark von Daak |
| Sprache | Deutsch |
| Beschreibung | `buch/cover/amazon-beschreibung.md` |
| Altersfreigabe | keine jugendgefährdenden Inhalte |
| Trimmgröße | 15,24 × 22,86 cm (6″ × 9″) |
| Seiten | 76 (letzte Seite ist eine Vakatseite) |
| Papier | weiß |
| Rückenbreite | 4,3 mm — **kein Rückentext**, KDP erlaubt ihn erst ab 79 Seiten |

**Hardcover-Fassung** — bei KDP ein eigener Titel neben dem Taschenbuch,
gleiche Beschreibung, gleiche Kategorien, gleiche Stichwörter:

| Feld | Wert |
|---|---|
| Trimmgröße | 6 × 9 Zoll (15,24 × 22,86 cm) |
| Seiten | 76 |
| Papier / Druckfarbe | weiß / Schwarzweiß |
| Rücken der Buchdecke | 13,3 mm — **mit** Rückentext |
| Umschlag gesamt | **13,942 × 10,417 Zoll** (354,13 × 264,59 mm) |
| Datei | `buch/out/cover-hardcover-druck.pdf` |

Der Umschlag ist deutlich größer als beim Taschenbuch, weil er nicht
beschnitten, sondern um die Buchdecke geschlagen wird: 18 mm Umschlagrand
ringsum statt 3,175 mm Anschnitt. Der Rücken enthält zusätzlich 9 mm für die
Deckelpappen und die Falzrillen.

KDP nimmt Hardcover **erst ab 75 Seiten** an — mit 76 liegt Band 1 knapp
darüber, und 6 × 9 Zoll steht in KDPs Hardcover-Liste. Band 3 brauchte zwei
Eingriffe: vier Seiten mehr und ein anderes Trimmformat — Näheres im Abschnitt
zu Band 3. Band 2 (92 Seiten) hätte die Seitenzahl, hat aber noch keinen
Hardcover-Umschlag und stünde vor demselben Formatproblem wie Band 3.

**Kategorien** — eine breite, zwei enge:

1. Ratgeber › Gesundheit & Medizin › Ernährung
2. Ratgeber › Gesundheit & Medizin › Diäten & Gewichtsreduktion
3. Ratgeber › Gesundheit & Medizin › Stoffwechsel *(oder eine vergleichbar
   enge Nische — dort ist eine Platzierung realistisch)*

**Keywords** — sieben Felder à 50 Zeichen. Wortgruppen statt Einzelwörter, und
kein Wort, das schon in Titel oder Untertitel steht: Amazon indexiert die
ohnehin, eine Wiederholung verschenkt ein Feld.

```
ernährungsumstellung dauerhaft durchhalten
abnehmen ohne hungern ohne diät
eiweißreiche ernährung plan anleitung
kohlenhydratarm essen alltagstauglich
kochen ohne salz und zucker
jojo effekt vermeiden ernährung
ratgeber gesunde ernährung einsteiger
```

Zum Tauschen, falls ein Begriff nach ein paar Wochen nichts bringt:
`vier mahlzeiten am tag konzept` · `ernährungsplan zum nachmachen` ·
`gesund abnehmen ratgeber` · `fettstoffwechsel ernährung buch` ·
`ernährungskonzept selbstständig umsetzen`

---

## Band 2 — Das Workbook

| Feld | Wert |
|---|---|
| Titel | Der Stoffwechsel-Reset |
| Untertitel | Das 12-Wochen-Workbook |
| Serie | Der Stoffwechsel-Reset, Band 2 |
| Beschreibung | `workbook/cover/amazon-beschreibung.md` |
| Trimmgröße | **8 × 10 Zoll** (20,32 × 25,4 cm) — steht in der Auswahlliste |
| Seiten | 92 |
| Papier | weiß |
| Druckfarbe | Schwarzweiß |
| Rückenbreite | 5,3 mm — Rückentext gesetzt |
| Umschlag gesamt | 418,01 × 260,35 mm (16,457 × 10,250 Zoll) |

Vorher war dieser Band A4 (8,27 × 11,69 Zoll). Das steht bei KDP **nicht** in
der Auswahlliste und muss als benutzerdefinierte Trimmgröße eingetragen
werden; wird stattdessen eine Größe aus der Liste gewählt, prüft KDP Innenteil
und Umschlag gegen die falschen Sollmaße und weist beides zurück. 8 × 10 kommt
aus der Liste und hat das Problem nicht.

**Schwarzweiß und weißes Papier** sind keine Nebensache: Jede andere Papier-
oder Farbwahl ändert die Rückenbreite und damit die Sollbreite des Umschlags.

Zur Kontrolle — was KDP bei 92 Seiten erwartet, je nach Auswahl:

| Trimmgröße | Papier | Umschlag gesamt |
|---|---|---|
| 8 × 10 Zoll | weiß | **418,0 × 260,4 mm** ← unsere Datei |
| 8 × 10 Zoll | creme | 418,6 × 260,4 mm |
| 8,5 × 11 Zoll | weiß | 443,4 × 285,8 mm |
| 8,27 × 11,69 Zoll | weiß | 431,7 × 303,3 mm |

Nennt KDP eine Sollgröße, die hier in einer anderen Zeile steht, ist im
Formular die falsche Trimmgröße oder das falsche Papier eingestellt.

**Kategorien:** dieselben wie Band 1.

Nicht unter „Kalender, Notizbücher & Planer" einordnen. Dort wird Blankoware
gekauft, und ein Begleitheft zu einem Konzept geht in dieser Umgebung unter.

**Keywords** — sieben Felder à 50 Zeichen, nach denselben Regeln wie bei
Band 1: Wortgruppen statt Einzelwörter, kein Wort aus Titel oder Untertitel.

Band 2 zielt bewusst auf andere Suchen als Band 1. Band 1 wird von Leuten
gesucht, die ein Konzept verstehen wollen („ratgeber", „anleitung"); Band 2 von
Leuten, die schon entschieden haben und etwas zum Ausfüllen suchen
(„tagebuch", „planer", „journal"). Nur so stehen die beiden Bände nicht in
denselben Trefferlisten gegeneinander.

```
ernährungstagebuch zum ausfüllen a4
abnehmtagebuch erfolgsjournal zum eintragen
gewichtstagebuch umfänge messen protokoll
diät tagebuch ernährungsumstellung begleiter
wochenplaner gesunde ernährung ausfüllbuch
begleitheft ernährungskonzept low carb
eiweißreich essen plan zum abhaken
```

Zum Tauschen, falls ein Begriff nach ein paar Wochen nichts bringt:
`habit tracker ernährung gesundheit` · `essenstagebuch selbst führen` ·
`ausfüllbuch abnehmen ohne diät` · `ernährungsjournal großformat` ·
`fortschritt dokumentieren ernährung`

---

## Band 3 — Das Rezeptbuch

| Feld | Wert |
|---|---|
| Titel | Der Stoffwechsel-Reset |
| Untertitel | Das Rezeptbuch — 73 Gerichte ohne Salz und Zucker |
| Serie | Der Stoffwechsel-Reset, Band 3 |
| Beschreibung | `rezepte/cover/amazon-beschreibung.md` |
| Trimmgröße | **8 × 10 Zoll** (20,32 × 25,4 cm) — steht in der Auswahlliste |
| Seiten | 76 |
| Papier | weiß |
| Druckfarbe | Schwarzweiß |
| Rückenbreite | 4,3 mm — kein Rückentext (KDP erlaubt ihn ab 79 Seiten) |
| Umschlag gesamt | 417,10 × 260,35 mm (16,421 × 10,250 Zoll) |
| Datei | `rezepte/out/cover-druck.pdf` |

**Hardcover-Fassung** — eigener Titel neben dem Taschenbuch, gleiche
Beschreibung, gleiche Kategorien, gleiche Stichwörter:

| Feld | Wert |
|---|---|
| Trimmgröße | **8,25 × 11 Zoll** (20,955 × 27,94 cm) — **nicht** 8 × 10 |
| Seiten | 76 |
| Papier / Druckfarbe | weiß / Schwarzweiß |
| Rücken der Buchdecke | 13,3 mm — **mit** Rückentext |
| Umschlag gesamt | **18,442 × 12,417 Zoll** (468,43 × 315,39 mm) |
| Innenteil | `rezepte/out/rezeptbuch-hardcover-druck.pdf` — **eigene Datei** |
| Umschlag | `rezepte/out/cover-hardcover-druck.pdf` |

**Achtung, hier weicht Band 3 von Band 1 ab:** KDP führt 8 × 10 Zoll nur als
Taschenbuch. Für Hardcover gibt es 5,5×8,5 · 6×9 · 6,14×9,21 · 7×10 ·
8,25×11 Zoll und sonst nichts. Band 3 läuft als Hardcover deshalb auf
**8,25 × 11 Zoll** — mit einem eigenen Innenteil, nicht demselben wie das
Taschenbuch. Band 1 (6 × 9) ist in der Liste enthalten und braucht nur eine
Datei für beide Bindearten.

Der Satzspiegel ist in beiden Fassungen identisch; die Formatdifferenz geht
vollständig in die Ränder. Nur dadurch bleibt die Seitenzahl bei 76 — mit
gleichen Rändern hätte die größere Fläche den Band auf rund 67 Seiten
gedrückt und damit wieder unter KDPs Hardcover-Grenze von 75.

Mit den ursprünglichen 72 Seiten war Band 3 ohnehin ausgeschlossen. Das
Kapitel „Vorkochen, aufbewahren, mitnehmen" bringt ihn auf 76 — und schließt
zugleich die Lücke, an der das Konzept im Alltag am häufigsten scheitert: die
dritte Mahlzeit am Nachmittag, die selten in der eigenen Küche stattfindet.

Gleiches Format wie Band 2. Beim Kochen liegt das Buch flach auf der
Arbeitsfläche — dafür ist das Großformat das nützlichere Maß. Band 1 bleibt
bei 6 × 9 Zoll; es ist ein Lesebuch und soll in die Hand passen.

**Kategorien:**

1. Kochen & Genießen › Spezielle Ernährung › Low Carb
2. Kochen & Genießen › Gesunde Küche
3. Ratgeber › Gesundheit & Medizin › Ernährung

**Keywords** — sieben Felder à 50 Zeichen, nach denselben Regeln wie bei
Band 1 und 2: Wortgruppen statt Einzelwörter, kein Wort aus Titel oder
Untertitel.

Band 3 zielt auf Kochsuchen, nicht auf Konzeptsuchen. Band 1 wird von Leuten
gesucht, die verstehen wollen, Band 2 von Leuten, die etwas zum Ausfüllen
suchen, Band 3 von Leuten, die heute Abend etwas kochen wollen. Nur so stehen
die drei Bände nicht in denselben Trefferlisten gegeneinander.

```
low carb kochbuch wenig kohlenhydrate
high protein rezepte eiweißreich kochen
salzfrei kochen würzen mit kräutern
zuckerfrei kochbuch alltagstauglich
abnehmen mit eiweiß alltagsrezepte
getreidefrei kochen reis nudeln ersetzen
schnelle abendessen wenige zutaten
```

**„glutenfrei" gehört nicht hinein**, so naheliegend es bei einem Buch ohne
Getreide wirkt: Acht Rezepte arbeiten mit Seitan aus Dinkelkleber, und der ist
reines Gluten. Ein Käufer mit Zöliakie, der über dieses Stichwort kommt, hat
einen berechtigten Grund für eine Rezension und für eine Beschwerde bei Amazon.
Dasselbe gilt für „vegan" — es gibt vegane Rezepte im Buch, aber es ist kein
veganes Kochbuch.

Zum Tauschen, falls ein Begriff nach ein paar Wochen nichts bringt:
`kohlenhydratarm kochen abendessen` · `eiweißbrot ersatz rezepte` ·
`gewürzmischung selber machen ohne salz` · `meal prep eiweißreich` ·
`kochbuch stoffwechselkur alternative`

---

## Der Darm im Gleichgewicht

Kein Band der Reihe — ein eigenständiger Titel auf derselben Bau- und
Gestaltungsbasis. **Serienfeld bei KDP leer lassen.**

| Feld | Wert |
|---|---|
| Titel | Der Darm im Gleichgewicht |
| Untertitel | Wie Verdauung wirklich funktioniert — mit 8-Wochen-Programm und 40 Rezepten |
| Serie | *keine* |
| Autor | Mark von Daak |
| Sprache | Deutsch |
| Beschreibung | `darm/cover/amazon-beschreibung.md` |
| Altersfreigabe | keine jugendgefährdenden Inhalte |
| Trimmgröße | 15,24 × 22,86 cm (6″ × 9″) |
| Seiten | 204 |
| Papier / Druckfarbe | weiß / Schwarzweiß |
| Rückenbreite | 11,7 mm — **mit** Rückentext (KDP erlaubt ihn ab 79 Seiten) |
| Umschlag gesamt | **12,709 × 9,250 Zoll** (322,82 × 234,95 mm), inkl. 3,175 mm Anschnitt |
| Innenteil | `darm/out/darm-im-gleichgewicht-druck.pdf` |
| Umschlag | `darm/out/cover-druck.pdf` |

**Hardcover-Fassung** — eigener Titel neben dem Taschenbuch, gleiche
Beschreibung, gleiche Kategorien, gleiche Stichwörter. 6 × 9 Zoll steht in
KDPs Hardcover-Liste, deshalb genügt **ein** Innenteil für beide Bindearten:

| Feld | Wert |
|---|---|
| Trimmgröße | 6 × 9 Zoll (15,24 × 22,86 cm) |
| Seiten | 204 |
| Rücken der Buchdecke | 20,7 mm — **mit** Rückentext |
| Umschlag gesamt | **14,230 × 10,417 Zoll** (361,45 × 264,59 mm) |
| Innenteil | `darm/out/darm-im-gleichgewicht-druck.pdf` (derselbe wie beim Taschenbuch) |
| Umschlag | `darm/out/cover-hardcover-druck.pdf` |

**Kategorien** — eine breite, zwei enge:

1. Ratgeber › Gesundheit & Medizin › Ernährung
2. Ratgeber › Gesundheit & Medizin › Krankheiten & Beschwerden › Verdauung
3. Sachbuch › Medizin › Ernährungsmedizin

**Sieben Stichwörter:**

`Darmgesundheit` · `Ballaststoffe` · `Mikrobiom` · `Verdauung` ·
`Ernährungsumstellung` · `Darmflora aufbauen` · `gesunde Ernährung Ratgeber`

Zum Tauschen, falls ein Begriff nichts bringt: `darm sanieren buch` ·
`reizdarm ernährung ratgeber` · `ballaststoffreiche rezepte` ·
`fermentieren anleitung` · `mikrobiom ernährung`

**Autorenbiografie für diesen Titel** — nicht die der Reihe verwenden. KDP
führt die Biografie am Buch, nicht am Konto; für diesen Titel ist sie so zu
hinterlegen:

> Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der Umstellung
> ihrer Ernährung. Er ist kein Arzt und kein Ernährungsberater mit
> Kammerzulassung — was er mitbringt, ist die Praxis: die Erfahrung aus der
> Begleitung von Menschen, die eine Umstellung über Monate durchgehalten
> haben. Sein Buch empfiehlt kein Produkt, nennt keine Marke und verspricht
> nichts, was sich nicht halten lässt. Wo es an seine Grenzen kommt, sagt es
> das und verweist dorthin, wo es hingehört.

> **Vor dem Hochladen gegenlesen.** Dieser Titel enthält
> Gesundheitsinformationen und ein Kapitel mit ärztlichen Warnzeichen.
> `claim_check.py` prüft nur auf verbotene Formulierungen — nicht auf
> inhaltliche Richtigkeit. Ein fachliches Gegenlesen vor der
> Veröffentlichung ist bei diesem Titel dringender angeraten als bei den
> anderen dreien.

---

## Kindle-Ausgaben

Bei KDP ein **eigener Titel** je Buch, nicht dieselbe Produktseite: Taschenbuch
und E-Book werden getrennt angelegt und von Amazon anschließend verknüpft.
Titel, Untertitel, Serie, Beschreibung, Kategorien und Stichwörter sind
dieselben wie beim Taschenbuch.

| Feld | Band 1 | Band 2 | Band 3 | Darm |
|---|---|---|---|---|
| Manuskript | `buch/out/stoffwechsel-reset-kindle.epub` | `workbook/out/workbook-kindle.epub` | `rezepte/out/rezeptbuch-kindle.epub` | `darm/out/darm-im-gleichgewicht-kindle.epub` |
| Titelbild | `buch/out/kindle-cover.jpg` | `workbook/out/kindle-cover.jpg` | `rezepte/out/kindle-cover.jpg` | `darm/out/kindle-cover.jpg` |
| Bauart | fließender Text | feste Seiten | fließender Text | fließender Text |
| Dateigröße | rund 0,5 MB | rund 5 MB | rund 0,5 MB | rund 0,6 MB |

Alle Titelbilder sind 1600 × 2560 Pixel im JPEG-Format — Amazons empfohlenes
Maß. Es wird **nicht** der Taschenbuchumschlag hochgeladen: Der enthält
Rückseite, Buchrücken und Anschnitt, die beim E-Book nichts zu suchen haben.

**Keine ISBN eintragen.** Für Kindle-Bücher vergibt Amazon eine ASIN; eine
ISBN ist weder nötig noch erwünscht.

**DRM:** eine Entscheidung, die sich nicht rückgängig machen lässt — sie wird
beim Anlegen getroffen und bleibt für die Lebensdauer des Titels bestehen.

**Zum Preis:** Die 70-Prozent-Tantieme gilt bei Amazon.de nur zwischen 2,99 €
und 9,99 €; außerhalb dieser Spanne sind es 35 Prozent. Bei Band 2 kommt die
Übertragungsgebühr hinzu, weil die Datei mit rund 5 MB deutlich größer ist als
die von Band 1 — das ist der Preis der festen Seiten.

**Band 2 ist als E-Book ein Kompromiss.** Ein Heft zum Ausfüllen, in dem man
nicht schreiben kann, verkauft sich als Ergänzung zum gedruckten Heft, nicht
als Ersatz. Wenn du es einstellst, sollte die Beschreibung das sagen — sonst
kommen Rezensionen, die genau das bemängeln.

**Band 3 profitiert von der E-Book-Fassung mehr als die anderen beiden.** Die
drei Register sind dort keine Listen zum Nachschlagen, sondern Verweise zum
Antippen: Wer im Register „nach Zeit" auf ein Gericht tippt, landet direkt beim
Rezept. Das ist ein Argument, das in die Produktbeschreibung der Kindle-Ausgabe
gehört.

## KI-erzeugte Inhalte melden

KDP fragt beim Anlegen eines Titels ab, ob Text, Bilder oder Übersetzungen
**KI-erzeugt** sind. Die Angabe ist verpflichtend und erscheint nicht auf der
Produktseite — sie geht nur an Amazon.

Der Unterschied, auf den es ankommt: *KI-erzeugt* ist Material, das ein
Werkzeug erstellt hat und das man anschließend höchstens bearbeitet hat.
*KI-unterstützt* ist eigenes Material, bei dem ein Werkzeug beim Überarbeiten
geholfen hat — das ist nicht meldepflichtig.

Für dieses Projekt heißt das: Wird ein mit Higgsfield erzeugtes Titelfoto
eingesetzt, ist beim Umschlag **„KI-erzeugte Bilder: ja"** anzugeben. Der
Text der Bücher ist selbst geschrieben und fällt nicht darunter. Ohne
Titelfoto sind die Umschläge Vektorzeichnungen aus `illustration.py` und
ebenfalls nicht meldepflichtig.

Eine Falschangabe ist nach Amazons Bedingungen ein Grund, das Konto zu
sperren. Der Aufwand für die richtige Angabe ist ein Klick.

## Was beim Anlegen nicht hineingehört

**Keine fremde Marke in Titel, Untertitel oder Keywords.** „cellRESET" und
„FitLine" gehören der PM-International AG. In den Büchern steht die
Bezeichnung beschreibend mit Markenhinweis — das ist etwas anderes als ein
Suchbegriff in einer Verkaufsanzeige. Beschwerden führen bei Amazon zur
Abschaltung des Listings, meist ohne vorherige Prüfung.

**Keine Angaben zu Kilogramm, Konfektionsgrößen oder Zeiträumen bis zu einem
Ergebnis** und keine Aussagen über Krankheiten. Das ist nach der
Health-Claims-Verordnung angreifbar und verstößt zusätzlich gegen die
Amazon-Richtlinien für Produktangaben.

**Keine erfundenen Rezensionen und keine Zitate**, die es nicht gibt.

## Was noch offen ist

Die Kategorienamen oben sind die üblichen. Amazon benennt seine Bäume
regelmäßig um, und die Auswahl unterscheidet sich zwischen amazon.de und
amazon.com — welche genau in deinem Konto zur Wahl stehen, siehst du erst im
KDP-Formular. Nimm die Liste als Suchraster, nicht als Abschrift.

Vor dem ersten Upload stehen außerdem drei Dinge aus, die nicht aus diesem
Repository kommen können:

1. eine **juristische Durchsicht** der Rechtstexte,
2. für Band 1 bis 3 die **Abstimmung mit PM-International** zur
   Partner-Compliance — bei „Der Darm im Gleichgewicht“ entfällt sie, weil der
   Titel weder das Unternehmen noch sein Konzept erwähnt,
3. bei „Der Darm im Gleichgewicht“ eine **fachliche Durchsicht** der
   Gesundheitsaussagen. Der Titel nennt Richtwerte, beschreibt ärztliche
   Warnzeichen und bewertet Testverfahren. `claim_check.py` prüft nur
   Formulierungen, nicht Inhalte — und bei einem Gesundheitsratgeber ist das
   der Unterschied, auf den es ankommt.
