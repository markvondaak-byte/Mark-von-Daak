---
typ: kapitel
nummer: 2
titel: Wie Maschinen lernen
kopfzeile: Wie Maschinen lernen
---

# Wie Maschinen lernen

Die Grundidee des maschinellen Lernens lässt sich an einem Beispiel erklären,
für das man nichts weiter braucht als eine Vorstellung von Immobilienpreisen.

Angenommen, jemand will den Preis einer Wohnung schätzen. Er könnte sich Regeln
ausdenken: so viel Euro je Quadratmeter, ein Aufschlag für Balkon, ein Abschlag
für die Lage an der Durchgangsstraße. Diese Regeln müsste er selbst finden,
begründen und bei jeder Marktveränderung nachziehen.

Maschinelles Lernen geht anders vor. Man legt dem System zehntausend
tatsächliche Verkäufe vor — jeweils mit Größe, Lage, Baujahr, Zustand und dem
erzielten Preis. Das System sucht darin nach dem Zusammenhang zwischen den
Merkmalen und dem Preis. Es bekommt die Regel nicht gesagt; es leitet sie aus
den Beispielen ab. Legt man ihm anschließend eine unbekannte Wohnung vor, gibt
es eine Schätzung aus.

Das ist der ganze Kern. Alles Weitere ist eine Frage des Maßstabs und der
Bauform.

## Was beim Training geschieht

Ein neuronales Netz besteht aus vielen kleinen Recheneinheiten, die in
Schichten angeordnet sind. Jede Verbindung zwischen zwei Einheiten trägt ein
Gewicht: eine Zahl, die bestimmt, wie stark ein Signal weitergereicht wird.
Diese Gewichte sind der eigentliche Inhalt des Modells. Bei den großen Systemen
der Gegenwart geht ihre Zahl in die Hunderte von Milliarden.

Zu Beginn sind alle Gewichte zufällig. Das Netz produziert Unsinn. Nun beginnt
ein Vorgang, der millionenfach wiederholt wird:

1. Das Netz bekommt ein Beispiel und erzeugt eine Ausgabe.
2. Die Ausgabe wird mit der richtigen Antwort verglichen. Die Abweichung wird
   als Zahl ausgedrückt — der Fehler.
3. Ein Verfahren rechnet zurück, welche Gewichte wie stark zu diesem Fehler
   beigetragen haben, und verschiebt jedes ein winziges Stück in die Richtung,
   die den Fehler verringert hätte.

Dieses Rückrechnen ist der mathematische Kern des Deep Learning. Es ist im
Grunde Ableitungsrechnung, wie man sie in der Oberstufe kennenlernt, nur eben
über sehr viele Größen gleichzeitig und sehr oft.

Das Ergebnis nach Wochen oder Monaten Rechenzeit ist eine Zahlenkolonne, die
nichts weiter tut, als Eingaben in Ausgaben zu übersetzen. Niemand hat diese
Zahlen geschrieben. Niemand kann sie einzeln erklären. Sie sind das
Destillat der Trainingsdaten.

> Der wichtigste Satz dieses Kapitels:
>
> Ein trainiertes Modell enthält keine Regeln, die jemand aufgeschrieben hat.
> Es enthält Zahlen, die während des Trainings so lange verschoben wurden, bis
> die Ausgaben stimmten. Deshalb kann niemand vollständig sagen, warum es tut,
> was es tut.

## Drei Arten zu lernen

**Überwachtes Lernen** ist der Fall aus dem Wohnungsbeispiel: Zu jedem
Beispiel gibt es die richtige Antwort. So entstehen Systeme, die Tumore auf
Aufnahmen markieren, Schrift erkennen oder Kreditausfälle schätzen. Der Aufwand
liegt bei den Daten: Jemand muss die richtigen Antworten liefern, und das ist
teuer.

**Unüberwachtes Lernen** kommt ohne vorgegebene Antworten aus. Das System sucht
Strukturen — Gruppen ähnlicher Kunden, ungewöhnliche Zahlungsvorgänge,
wiederkehrende Formen in Messdaten. Es findet, was auffällt, ohne zu wissen,
was es bedeutet.

**Bestärkendes Lernen** arbeitet mit Belohnung. Das System handelt, bekommt
Rückmeldung über den Erfolg und passt sein Verhalten an. So sind die
Spielsysteme entstanden, die Menschen im Go und in Videospielen geschlagen
haben; so werden Roboterbewegungen und Steuerungsaufgaben trainiert. Und so
werden Sprachmodelle nachjustiert, damit ihre Antworten menschlichen
Erwartungen entsprechen — dazu gleich mehr im nächsten Kapitel.

## Warum Daten alles entscheiden

Ein Modell kann nur wiedergeben, was in seinen Daten steckt. Dieser Satz
klingt banal und wird trotzdem ständig übergangen. Er hat drei Konsequenzen,
die im ganzen Buch wiederkehren.

**Lücken werden nicht gemeldet.** Ein System, das nur mit Aufnahmen heller
Haut trainiert wurde, erkennt Hautveränderungen auf dunkler Haut schlechter.
Es sagt das aber nicht. Es liefert ein Ergebnis, ebenso zuversichtlich wie
sonst. Kapitel 16 handelt davon.

**Verzerrungen werden verstärkt, nicht ausgeglichen.** Wenn in den historischen
Daten einer Personalabteilung Frauen seltener befördert wurden, lernt das
System diesen Zusammenhang als Muster — nicht als Missstand.

**Die Welt bewegt sich, das Modell nicht.** Ein Modell friert einen Zustand
ein. Ändern sich die Verhältnisse, verliert es an Genauigkeit, ohne dass etwas
kaputtgeht. Man nennt das Modellalterung, und sie ist die häufigste Ursache
dafür, dass ein System nach zwei Jahren im Betrieb schlechtere Ergebnisse
liefert als bei der Abnahme.

## Was daran neu ist und was nicht

Die mathematischen Grundlagen sind alt. Die Idee des künstlichen Neurons
stammt aus den 1940er Jahren, das Rückrechnungsverfahren wurde in den 1980er
Jahren populär, die Bausteine für die Bildverarbeitung sind seit den 1990ern
bekannt. Was fehlte, waren Daten und Rechenleistung.

Beides kam in den 2010er Jahren zusammen. Die Digitalisierung des Alltags
lieferte die Datenmengen, und Grafikprozessoren — ursprünglich für
Computerspiele gebaut — lieferten die Rechenleistung: Sie können sehr viele
einfache Rechnungen gleichzeitig ausführen, und genau das braucht ein
neuronales Netz.

Der eigentliche Bruch kam 2017 mit einer Architektur namens **Transformer**.
Sie erlaubt es, große Textmengen parallel statt nacheinander zu verarbeiten,
und sie kann dabei gewichten, welche Teile einer Eingabe für welchen anderen
Teil bedeutsam sind. Damit wurde das Training auf einem Maßstab möglich, der
vorher an der Rechenzeit gescheitert wäre. Alle bekannten Sprachmodelle der
Gegenwart gehen auf diese Bauform zurück.

Von da an geschah etwas, das die Beteiligten selbst überrascht hat: Größere
Modelle mit mehr Daten wurden nicht bloß etwas besser, sondern zeigten
Fähigkeiten, für die sie nicht eigens trainiert worden waren — Übersetzen,
Zusammenfassen, einfaches Schlussfolgern. Diese Beobachtung, dass Leistung
verlässlich mit Größe wächst, ist der wirtschaftliche Motor der letzten Jahre.
Sie ist auch der Grund für den Ressourcenverbrauch, um den es in Kapitel 18
geht. Und sie gilt nicht ewig — auch dazu später mehr.
