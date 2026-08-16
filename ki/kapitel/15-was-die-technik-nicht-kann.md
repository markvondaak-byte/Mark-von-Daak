---
typ: kapitel
nummer: 5
titel: Was diese Systeme nicht können
kopfzeile: Die Grenzen
---

# Was diese Systeme nicht können

Eine ehrliche Bestandsaufnahme der Grenzen ist die Voraussetzung dafür, den
Nutzen richtig einzuschätzen. Nicht alle der folgenden Grenzen sind
grundsätzlicher Natur — einige verschieben sich, und wo das absehbar ist, wird
es gesagt. Aber es gibt eine Reihe von Schwächen, die nicht daran liegen, dass
die Systeme noch zu klein sind.

## Sie unterscheiden nicht zwischen Zusammenhang und Ursache

Statistische Modelle finden Zusammenhänge. Ob ein Zusammenhang eine Ursache
abbildet, sagt kein Modell aus sich heraus. Das klassische Beispiel: Ein
System, das aus Krankenhausdaten die Sterblichkeit von Lungenentzündungen
schätzt, kann lernen, dass Patienten mit Asthma bessere Verläufe haben — weil
sie in der Praxis sofort intensiv behandelt wurden. Als Prognose ist das
richtig. Als Entscheidungsgrundlage — diese Patienten brauchen weniger
Aufmerksamkeit — ist es lebensgefährlich.

Solche Umkehrungen sind der häufigste ernste Fehler beim Einsatz lernender
Systeme in Organisationen. Sie treten nicht auf, weil das Modell schlecht ist,
sondern weil es genau das tut, wofür es gebaut wurde, und die Anwender etwas
anderes hineinlesen.

## Sie sind unzuverlässig auf eine Weise, die schwer zu prüfen ist

Klassische Software versagt hart: Ein Programm stürzt ab, eine Berechnung
liefert einen Fehlercode. Lernende Systeme versagen weich. Sie geben eine
Antwort aus, die aussieht wie alle anderen, und nichts an der Form verrät, ob
sie richtig ist.

Damit fällt die übliche Qualitätssicherung aus. Man kann ein solches System
nicht durch Lesen des Quelltextes prüfen und nicht durch eine überschaubare
Zahl von Testfällen abnehmen. Man kann nur statistisch messen — an Stichproben,
im laufenden Betrieb, mit Vergleichswerten. Das ist möglich, aber es ist eine
andere Disziplin, und die meisten Organisationen haben sie nicht.

## Sie erklären ihre Ergebnisse nicht

Ein Modell mit Milliarden Gewichten lässt sich nicht in eine Begründung
übersetzen. Es gibt Verfahren, die nachträglich zeigen, welche Eingabeteile ein
Ergebnis am stärksten beeinflusst haben; sie liefern Hinweise, aber keine
Begründung im rechtlichen oder fachlichen Sinn.

Das kollidiert unmittelbar mit Anforderungen, die in vielen Bereichen
selbstverständlich sind: Ein Ablehnungsbescheid muss begründet sein, eine
medizinische Entscheidung nachvollziehbar, eine Kreditentscheidung erklärbar.
Wo ein System eine Begründung nicht liefern kann, muss ein Mensch sie liefern —
und das geht nur, wenn er die Sache selbst beurteilen kann. Ein Mensch, der
eine Systemausgabe abnickt, erzeugt keine Nachvollziehbarkeit, sondern nur
deren Anschein.

## Sie kennen die Welt nur durch Beschreibungen

Ein Sprachmodell hat über Wasser gelesen, aber nie eines verschüttet. Diese
Feststellung wirkt philosophisch und hat sehr praktische Folgen: Systeme
scheitern regelmäßig an Aufgaben, die ein Kind mühelos löst, sobald es um
Raum, Materialeigenschaften oder körperliche Erfahrung geht.

In der Robotik zeigt sich dieselbe Grenze noch deutlicher. Ein Modell, das
juristische Schriftsätze entwirft, ist verfügbar; ein Roboter, der eine fremde
Küche aufräumt, ist es nicht. Der Grund ist nicht mangelnde Rechenleistung,
sondern der Mangel an Trainingsmaterial: Für Sprache lagen Billionen Wörter
bereit, für körperliches Handeln muss jede Erfahrung mühsam erzeugt werden.
Diese Asymmetrie erklärt einen großen Teil dessen, welche Berufe unter Druck
geraten und welche nicht — Kapitel 13 kommt darauf zurück.

## Sie haben keine Ziele, aber sie verfolgen welche

Das klingt widersprüchlich und ist es nicht. Ein Modell hat kein Interesse.
Aber jedes trainierte System optimiert eine Zielgröße, und diese Zielgröße ist
immer eine Vereinfachung dessen, was eigentlich gemeint war.

Ein Empfehlungssystem, das auf Verweildauer optimiert, findet zuverlässig
heraus, dass Empörung länger bindet als Sachlichkeit. Niemand hat das gewollt;
das System hat sein Ziel erreicht. Der Fachausdruck dafür ist
**Zielverfehlung durch Stellvertretergrößen**: Man misst, was messbar ist, und
bekommt genau das — nicht das, was man meinte.

Diese Schwierigkeit ist nicht technisch zu lösen, weil sie vor der Technik
liegt. Sie ist der Grund, warum die Frage „Worauf ist dieses System eigentlich
optimiert?“ zu den wichtigsten gehört, die man einem Anbieter stellen kann.

## Was sich absehbar verschiebt — und was nicht

| Grenze | Aussicht |
|---|---|
| Erfundene Angaben | wird seltener durch Belegverfahren, verschwindet nicht |
| Rechnen und Logik | verbessert sich deutlich durch Werkzeuge und Prüfschritte |
| Erklärbarkeit | Teilfortschritte, kein grundsätzlicher Durchbruch in Sicht |
| Ursache und Wirkung | nur durch bewusste Modellierung, nicht durch Größe |
| Körperliches Handeln | langsamer Fortschritt, begrenzt durch Trainingsdaten |
| Zielverfehlung | keine technische Lösung — eine Frage der Gestaltung |

Die Zeile, auf die es ankommt, ist die letzte. Die meisten Schäden, von denen
Teil III handelt, entstehen nicht daran, dass Systeme zu schwach sind. Sie
entstehen daran, dass leistungsfähige Systeme auf Ziele optimiert werden, die
mit dem Interesse der Betroffenen nicht übereinstimmen.
