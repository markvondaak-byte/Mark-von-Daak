---
typ: kapitel
nummer: 4
titel: Warum es gerade jetzt passiert
kopfzeile: Warum jetzt
---

# Warum es gerade jetzt passiert

Die Frage stellt sich zu Recht: Wenn die Grundlagen jahrzehntealt sind, warum
steht die Welt dann erst in den letzten Jahren kopf? Die Antwort besteht aus
vier Entwicklungen, die einzeln unspektakulär sind und erst zusammen wirken.

## Erstens: Rechenleistung wurde billig genug

Grafikprozessoren wurden gebaut, um Bildpunkte zu berechnen — Millionen
einfacher Rechnungen gleichzeitig. Dass dieselbe Bauart genau das ist, was ein
neuronales Netz braucht, war zunächst ein Zufallsbefund. Er hat die Kosten je
Rechenoperation über zwei Jahrzehnte um Größenordnungen gedrückt.

Das Training eines großen Modells verlangt heute dennoch einen Aufwand, der
außerhalb der Reichweite fast aller Beteiligten liegt: Zehntausende
Spezialprozessoren, Wochen bis Monate Laufzeit, ein Rechenzentrum mit
entsprechender Strom- und Kühlleistung. Die Kosten für einen einzelnen
Trainingslauf der größten Modelle liegen im hohen zweistelligen bis
dreistelligen Millionenbereich. Diese Zahl ist keine Randnotiz — sie bestimmt,
wer überhaupt mitspielen kann, und ist damit die technische Wurzel eines
Machtproblems, das Kapitel 17 behandelt.

## Zweitens: Daten in nie gekannter Menge

Das Training großer Sprachmodelle beruht auf Textmengen, die es vor dem
Internet schlicht nicht gab: Webseiten, Bücher, Foren, Programmcode,
wissenschaftliche Aufsätze, Untertitel. Es ist ein Rohstoff, der von
Milliarden Menschen über drei Jahrzehnte hinweg angehäuft wurde, ohne dass
irgendjemand dabei an diesen Verwendungszweck gedacht hätte.

Daraus ergeben sich zwei Folgeprobleme. Das eine ist rechtlicher Natur: Ein
großer Teil dieser Texte ist urheberrechtlich geschützt, und ob und in welchem
Umfang das Training damit zulässig ist, wird derzeit in mehreren
Rechtsordnungen vor Gericht geklärt. Das andere ist ein Mengenproblem: Die
leicht zugänglichen, hochwertigen Textbestände sind weitgehend ausgeschöpft.
Neue Größensprünge müssen anders gewonnen werden — aus synthetisch erzeugten
Daten, aus Fachbeständen hinter Bezahlschranken, aus Video und Audio, oder aus
besserem Training statt mehr Material.

## Drittens: eine Architektur, die mit Größe skaliert

Der 2017 vorgestellte Transformer hat eine Eigenschaft, die vorherige
Bauformen nicht hatten: Er lässt sich fast beliebig vergrößern und wird dabei
zuverlässig besser. Dieser Zusammenhang zwischen Modellgröße, Datenmenge,
Rechenaufwand und Leistung ist so regelmäßig, dass man ihn in Kurven fassen
kann. Er hat die Investitionen der letzten Jahre begründet: Wenn mehr Geld
verlässlich mehr Leistung bedeutet, wird Geld investiert.

Interessant sind zwei Einschränkungen, die dabei gern übersehen werden.

Erstens verläuft der Zusammenhang nicht linear, sondern flacht ab. Wer die
Leistung um einen bestimmten Betrag steigern will, muss den Aufwand um ein
Vielfaches erhöhen. Irgendwann wird das unwirtschaftlich, und es ist eine
offene Frage, wie nah dieser Punkt ist.

Zweitens hat sich die Entwicklung inzwischen verlagert. Statt immer größerer
Trainingsläufe wird zunehmend in die Nutzungsphase investiert: Modelle
bekommen Rechenzeit, um vor der Antwort mehrere Lösungswege zu erzeugen und zu
prüfen. Bei Aufgaben mit klarem Richtig und Falsch — Mathematik, Programmieren,
Logik — bringt das erhebliche Zuwächse. Bei Fragen ohne prüfbare Lösung bringt
es weniger.

## Viertens: eine Bedienoberfläche, die jeder versteht

Der letzte Faktor wird am häufigsten übersehen. Sprachmodelle waren in
Fachkreisen bereits mehrere Jahre bekannt, bevor sie die Öffentlichkeit
erreichten. Was den Unterschied machte, war ein Eingabefeld, in das man in
normaler Sprache schreiben konnte.

Die Wirkung dieser Entscheidung ist kaum zu überschätzen. Jede vorherige
mächtige Software verlangte, ihre Sprache zu lernen — Tabellenformeln,
Abfragesprachen, Programmierung. Ein System, das die Sprache des Nutzers
spricht, hat keine Lernschwelle mehr. Deshalb hat sich diese Technik schneller
verbreitet als jede zuvor, und deshalb sitzt sie mitten in Berufen, die mit
Software bis dahin wenig zu tun hatten.

> Was daraus für die Zukunft folgt:
>
> Die Verbreitung hängt nicht mehr an der Technik, sondern an der Einbettung.
> Die nächsten Jahre entscheiden sich nicht daran, ob Modelle noch etwas besser
> werden, sondern daran, in welche Arbeitsabläufe, Geräte und Institutionen sie
> eingebaut werden — und mit welchen Sicherungen.

## Was das für die Einschätzung bedeutet

Wer wissen will, wie es weitergeht, sollte diese vier Faktoren einzeln
betrachten, statt auf eine Gesamtstimmung zu hören.

**Rechenleistung** wird weiter billiger, aber langsamer als früher; die
physikalischen Grenzen der Chipfertigung rücken näher, und der Energiebedarf
wird zum begrenzenden Faktor.

**Daten** sind der knappste Rohstoff geworden. Wer Zugang zu großen,
hochwertigen und rechtlich sauberen Beständen hat, hat einen Vorteil, den Geld
allein nicht ausgleicht.

**Architektur** entwickelt sich weiter, aber ein zweiter Sprung von der Größe
des Transformers ist nicht angekündigt und lässt sich nicht planen.

**Einbettung** ist der Bereich, in dem die kommenden Jahre tatsächlich
entschieden werden — und der einzige der vier, in dem Nutzer, Unternehmen und
Gesetzgeber unmittelbar mitreden.
