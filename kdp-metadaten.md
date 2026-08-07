# KDP-Metadaten — alle drei Bände

Alles, was beim Anlegen eines Titels bei Amazon KDP abgefragt wird, an einer
Stelle zum Kopieren. Die langen Beschreibungstexte stehen in eigenen Dateien,
weil sie dort zusätzlich als KDP-taugliches HTML vorliegen:

- `buch/cover/amazon-beschreibung.md`
- `workbook/cover/amazon-beschreibung.md`
- `rezepte/cover/amazon-beschreibung.md`

Die Druckangaben stammen aus dem letzten Build. Ändert sich der Innenteil,
ändern sich Seitenzahl und Rückenbreite — dann hier nachziehen.

---

## Autorenbiografie

Ein eigenes Feld bei KDP, getrennt von der Buchbeschreibung. Sie erscheint
unter „Über den Autor" und im Autorenprofil. Zwei Längen, inhaltlich deckungs-
gleich mit dem Kapitel „Über den Autor" in Band 1 — nichts behaupten, was dort
nicht steht.

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
| Trimmgröße | 15,24 × 22,86 cm (6″ × 9″) |
| Seiten | 54 |
| Papier | weiß |
| Rückenbreite | 3,1 mm — kein Rückentext |

**Kategorien:**

1. Kochen & Genießen › Spezielle Ernährung › Low Carb
2. Kochen & Genießen › Gesunde Küche
3. Ratgeber › Gesundheit & Medizin › Ernährung

**Keywords:**

```
kochen ohne salz rezepte
low carb ohne zucker
eiweißreiche rezepte einfach
rezepte ernährungsumstellung
salzfrei kochen anleitung
gerichte ohne getreide
schnelle eiweißgerichte abends
```

---

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

Vor dem ersten Upload stehen außerdem zwei Dinge aus, die nicht aus diesem
Repository kommen können: eine juristische Durchsicht der Rechtstexte und die
Abstimmung mit PM-International zur Partner-Compliance.
