# KDP-Metadaten — „Was uns die Maschine abnimmt“

Alles, was beim Anlegen des Titels bei Amazon KDP abgefragt wird, an einer
Stelle zum Kopieren. Der lange Beschreibungstext steht in
`ki/cover/amazon-beschreibung.md`, weil er dort zusätzlich als KDP-taugliches
HTML vorliegt.

Dieses Buch gehört **nicht** zur Stoffwechsel-Reihe. Es hat eine eigene
Zielgruppe, eigene Kategorien und eine eigene Autorenbiografie — die Angaben
aus `kdp-metadaten.md` im Wurzelverzeichnis passen hier nicht.

Die Druckangaben stammen aus dem letzten Build. Ändert sich der Innenteil,
ändern sich Seitenzahl und Rückenbreite — dann hier nachziehen.

---

## Taschenbuch

| Feld | Wert |
|---|---|
| Titel | Was uns die Maschine abnimmt |
| Untertitel | Künstliche Intelligenz — Nutzen, Kosten und was zu tun bleibt |
| Serie | keine |
| Autor | Mark von Daak |
| Sprache | Deutsch |
| Beschreibung | `ki/cover/amazon-beschreibung.md` |
| Altersfreigabe | keine jugendgefährdenden Inhalte |
| Trimmgröße | 15,24 × 22,86 cm (6″ × 9″) |
| Seiten | 124 |
| Papier / Druckfarbe | weiß / Schwarzweiß |
| Rückenbreite | 7,1 mm — **mit** Rückentext (KDP erlaubt ihn ab 79 Seiten) |
| Umschlag gesamt | 318,24 × 234,95 mm (12,529 × 9,250 Zoll), inkl. 3,175 mm Anschnitt |
| Innenteil | `ki/out/was-uns-die-maschine-abnimmt.pdf` |
| Umschlag | `ki/out/cover-druck.pdf` — **nicht** `cover.pdf` |

**Hardcover** wäre möglich: KDP nimmt es ab 75 Seiten an, der Band hat 124.
Gebaut wird derzeit keine Hardcover-Fassung — `ki/build/build_cover.py` kennt
die dafür nötige Umschlaggeometrie nicht. `buch/build/build_cover.py` kann es
für die Stoffwechsel-Reihe; wer es hier will, überträgt von dort die
Konstanten `WRAP_ZOLL` und `BUCHDECKE_ZOLL` und rechnet den Umschlag neu.

**Kategorien** — eine breite, zwei enge:

1. Computer & Internet › Künstliche Intelligenz
2. Politik & Geschichte › Politik › Technologiepolitik *(oder Sachbuch ›
   Gesellschaft & Politik)*
3. Wirtschaft › Arbeitswelt & Zukunft der Arbeit

Die dritte Kategorie ist die interessanteste: Dort steht das Buch neben
Zukunft-der-Arbeit-Titeln statt neben Programmierbüchern, und genau dort ist
seine Leserschaft.

**Keywords** — sieben Felder à 50 Zeichen. Wortgruppen statt Einzelwörter, und
kein Wort, das schon in Titel oder Untertitel steht: Amazon indexiert die
ohnehin, eine Wiederholung verschenkt ein Feld.

```
ki verstehen ohne vorkenntnisse
chancen und risiken neue technologie
zukunft der arbeit automatisierung
digitale ethik verantwortung
sachbuch technik gesellschaft
ki im unternehmen einführen
ki einfach erklärt für einsteiger
```

Zum Tauschen, falls ein Begriff nach ein paar Wochen nichts bringt:
`algorithmen entscheiden über menschen` · `desinformation deepfakes erkennen` ·
`ki regulierung europa` · `sprachmodelle verständlich erklärt` ·
`technikfolgen abschätzen ratgeber`

---

## Kindle-Ausgabe

| Feld | Wert |
|---|---|
| Datei | `ki/out/was-uns-die-maschine-abnimmt-kindle.epub` |
| Titelbild | `ki/out/kindle-cover.jpg` — 1600 × 2560 px |
| Bauart | fließender Text |
| DRM | keine |
| Preisgestaltung | 70-Prozent-Tantieme setzt einen Preis zwischen 2,99 und 9,99 Euro voraus |

Titel, Untertitel, Autor, Beschreibung, Kategorien und Keywords sind dieselben
wie beim Taschenbuch. Amazon verknüpft die Ausgaben anhand dieser Angaben; wer
beim Kindle-Titel eine andere Schreibweise einträgt, bekommt zwei getrennte
Produktseiten statt einer mit Formatauswahl.

---

## KI-erzeugte Inhalte melden

KDP fragt beim Anlegen ab, ob Text, Bilder oder Übersetzungen **KI-erzeugt**
sind. Die Angabe ist verpflichtend und erscheint nicht auf der Produktseite.

Der Unterschied, auf den es ankommt: *KI-erzeugt* ist Material, das ein
Werkzeug erstellt hat und das man anschließend höchstens bearbeitet hat.
*KI-unterstützt* ist eigenes Material, bei dem ein Werkzeug beim Überarbeiten
geholfen hat — das ist nicht meldepflichtig.

Für dieses Buch heißt das:

| Bestandteil | Angabe |
|---|---|
| Text | KI-**unterstützt**, nicht KI-erzeugt — siehe Kapitel „Wichtige Hinweise“ |
| Umschlag | keine KI-erzeugten Bilder; das Netzmotiv ist in `build_cover.py` gezeichnet |
| Übersetzung | entfällt |

Bei einem Buch über KI wird diese Frage genauer gelesen als bei anderen
Titeln. Die Offenlegung im Buch (Impressum und Kapitel „Wichtige Hinweise“)
und die Angabe bei KDP müssen deshalb übereinstimmen — und tun es.

Eine Falschangabe ist nach Amazons Bedingungen ein Grund, das Konto zu
sperren. Der Aufwand für die richtige Angabe ist ein Klick.

---

## Was beim Anlegen nicht hineingehört

**Keine Firmennamen in Titel, Untertitel oder Keywords.** Die Namen der
bekannten Chat-Anwendungen wären hervorragende Suchbegriffe und sind fremde
Marken. Im Listing wirken sie als Werbung mit fremdem Kennzeichen — der
klassische Anlass für eine Beanstandung, der Amazon ohne Prüfung nachkommt.

**Keine Prognose mit Jahreszahl in der Beschreibung.** „Bis 2030 fallen X
Prozent der Arbeitsplätze weg“ ist nicht belegbar, und das Buch sagt selbst,
warum. Eine Beschreibung, die verspricht, was der Text ausdrücklich ablehnt,
erzeugt schlechte Rezensionen.

**Keine erfundenen Rezensionen und keine Zitate**, die es nicht gibt.

---

## Was noch offen ist

Die Kategorienamen oben sind die üblichen. Amazon benennt seine Bäume
regelmäßig um, und die Auswahl unterscheidet sich zwischen amazon.de und
amazon.com — welche genau im Konto zur Wahl stehen, zeigt erst das
KDP-Formular. Nimm die Liste als Suchraster, nicht als Abschrift.

Vor dem ersten Upload steht außerdem eine Durchsicht der Rechtstexte aus. Das
Kapitel „Wichtige Hinweise“ deckt Stand der Angaben, fehlende Rechtsberatung
und Haftung ab; ob das für den Vertrieb genügt, sollte ein Anwalt bestätigen —
dieses Repository kann das nicht.
