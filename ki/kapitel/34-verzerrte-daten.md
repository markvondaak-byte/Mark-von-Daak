---
typ: kapitel
nummer: 16
titel: Vorurteile in Zahlenform
kopfzeile: Vorurteile in Zahlenform
---

# Vorurteile in Zahlenform

Ein lernendes System hat keine Vorurteile. Es hat Trainingsdaten. Wenn in
diesen Daten die Ungleichbehandlung der Vergangenheit steckt, lernt es sie als
Muster — nicht als Missstand, sondern als Regelmäßigkeit der Welt. Und
anschließend wendet es sie mit einer Gleichmäßigkeit an, die kein Mensch
erreicht.

## Wie Diskriminierung in ein Modell kommt

**Über die Zielgröße.** Ein Personalsystem soll „erfolgreiche Mitarbeiter“
vorhersagen. Erfolg wird gemessen an Beförderungen der letzten zehn Jahre.
Wurden in diesen zehn Jahren Frauen seltener befördert, lernt das System, dass
Merkmale, die mit Frauen zusammenhängen, gegen Erfolg sprechen. Das ist kein
Programmfehler; es ist die korrekte Wiedergabe der Datenlage.

**Über die Stichprobe.** Ein Modell, das überwiegend an Daten einer Gruppe
trainiert wurde, arbeitet bei anderen Gruppen schlechter. Bei
Gesichtserkennung ist das gut vermessen, bei medizinischer Bildauswertung
ebenfalls; auch Spracherkennung versteht Dialekte und Akzente schlechter,
sofern sie in den Daten unterrepräsentiert waren.

**Über Stellvertretermerkmale.** Der wichtigste und am meisten unterschätzte
Weg. Man kann Herkunft, Geschlecht oder Religion aus den Eingabedaten
entfernen — und das System findet sie trotzdem, weil andere Merkmale sie
abbilden: Postleitzahl, Name, Schule, Vereinsmitgliedschaft, Kaufverhalten,
Uhrzeit der Antragstellung. Das bloße Weglassen des geschützten Merkmals
erzeugt keine Neutralität, sondern nur Unsichtbarkeit der Diskriminierung.

**Über die Rückkopplung.** Wenn ein System bestimmt, wo Streifen fahren, wird
dort mehr entdeckt. Diese Entdeckungen fließen in die nächsten Trainingsdaten.
Das System bestätigt sich selbst. Solche Kreisläufe sind besonders zäh, weil
sie Belege für ihre eigene Richtigkeit produzieren.

## Warum „gerecht“ keine eindeutige Vorgabe ist

An dieser Stelle wird es unbequem, und dieser Teil fehlt in den meisten
Darstellungen. Man kann Fairness mathematisch definieren — es gibt mehrere
sinnvolle Definitionen, und sie widersprechen einander.

Drei gebräuchliche:

- **Gleiche Trefferquote in allen Gruppen:** Das System soll in jeder Gruppe
  gleich oft richtig liegen.
- **Gleiche Fehlerarten in allen Gruppen:** Es soll in jeder Gruppe gleich oft
  fälschlich ablehnen und fälschlich annehmen.
- **Gleiche Ergebnisquote:** Der Anteil der Angenommenen soll in allen Gruppen
  gleich sein.

Es ist mathematisch bewiesen, dass diese Kriterien sich nicht gleichzeitig
erfüllen lassen, sobald sich die Gruppen in der zugrunde liegenden Häufigkeit
des Merkmals unterscheiden. Man muss sich entscheiden. Das ist keine
technische, sondern eine politische und rechtliche Entscheidung — und sie wird
in der Praxis meistens von einem Entwicklungsteam getroffen, das gar nicht
weiß, dass es sie trifft.

> Die Frage, die man in jedem Beschaffungsgespräch stellen sollte:
>
> „Nach welcher Definition von Fairness ist dieses System geprüft worden, und
> welche anderen Definitionen verletzt es dadurch?“ Wer darauf keine Antwort
> hat, hat nicht geprüft.

## Wo es wehtut

Die Bereiche, in denen automatisierte Bewertung von Menschen Schäden
verursacht, sind gut dokumentiert:

**Bewerbungsvorauswahl.** Systeme, die Lebensläufe sortieren, haben in
mehreren dokumentierten Fällen systematisch Frauen oder Bewerber bestimmter
Herkunft benachteiligt. Der Betroffene erfährt nie, dass er aussortiert wurde,
und schon gar nicht, warum.

**Kredit und Versicherung.** Bonitätsbewertung arbeitet mit Merkmalen, deren
Zusammenhang mit Zahlungsverhalten teils sachlich, teils zufällig, teils
diskriminierend ist. Die Wohngegend ist der klassische Fall: Sie hat
statistische Aussagekraft und bildet zugleich soziale Herkunft ab.

**Sozialverwaltung.** Mehrere europäische Staaten haben Systeme eingesetzt,
die Missbrauchsverdacht bei Sozialleistungen schätzen. In den bekanntesten
Fällen wurden vor allem Menschen mit Migrationshintergrund und Alleinerziehende
getroffen; Existenzen wurden zerstört, bevor die Systeme gerichtlich gestoppt
wurden. Diese Fälle sind die wichtigsten Lehrstücke, die es zu dem Thema gibt.

**Justiz.** Rückfallprognosen zur Unterstützung von Haft- und
Bewährungsentscheidungen. Die Untersuchungen dazu sind der Anlass für die oben
beschriebene Fairness-Debatte gewesen — das dortige System war je nach
gewähltem Kriterium gerecht oder eklatant ungerecht, und beide Seiten hatten
recht.

## Was hilft

**Messen, getrennt nach Gruppen.** Eine Gesamttrefferquote sagt nichts. Man
muss die Leistung für jede betroffene Gruppe einzeln ausweisen. Das ist der
erste und wirksamste Schritt, und er wird erstaunlich selten getan.

**Fehlerkosten benennen, bevor man baut.** Was ist schlimmer: einen Berechtigten
abzulehnen oder einen Unberechtigten anzunehmen? Diese Frage entscheidet über
den Schwellenwert, und sie gehört nicht in die Technik, sondern in die
Leitungsebene.

**Betroffene beteiligen.** Wer prüft, ob ein System gerecht ist, sollte nicht
nur die Gruppe sein, die es baut.

**Widerspruch ermöglichen.** Jede automatisierte Bewertung eines Menschen
braucht eine Stelle, die den Einzelfall ansieht — mit Zeit, Befugnis und
Kenntnis. Das europäische Recht sieht bei automatisierten Entscheidungen
Auskunfts- und Eingriffsrechte vor. Sie sind vorhanden und werden selten
genutzt, weil kaum jemand von ihnen weiß.

**Die Alternative ehrlich vergleichen.** Ein wichtiger Einwand zum Schluss:
Menschliche Entscheider sind ebenfalls voreingenommen — nachweislich, in
denselben Feldern, oft stärker. Der Unterschied ist, dass menschliche
Voreingenommenheit ungleichmäßig streut und maschinelle systematisch wirkt.
Ein Sachbearbeiter hat Vorurteile; ein System hat dasselbe Vorurteil in allen
zweihunderttausend Fällen. Dafür ist es messbar und korrigierbar, ein Mensch
kaum. Beides ernst zu nehmen, führt zur einzigen brauchbaren Antwort: nicht
Mensch oder Maschine, sondern messen — bei beiden.
