---
typ: kapitel
nummer: 20
titel: Wenn Systeme irren und niemand haftet
kopfzeile: Wenn niemand haftet
---

# Wenn Systeme irren und niemand haftet

Jede Technik erzeugt Schäden. Was eine Gesellschaft im Umgang damit ausmacht,
ist nicht, dass sie Schäden verhindert, sondern dass sie eine Ordnung hat, wer
sie trägt. Bei lernenden Systemen ist diese Ordnung unklar, und die Unklarheit
ist kein Zufall — sie folgt aus der Bauart.

## Die Kette der Beteiligten

An einem einzigen fehlerhaften Ergebnis sind typischerweise beteiligt:

- wer die Trainingsdaten zusammengestellt hat,
- wer das Modell trainiert hat,
- wer es für einen bestimmten Zweck angepasst hat,
- wer die Anwendung darum herum gebaut hat,
- wer sie eingekauft und eingeführt hat,
- wer sie im konkreten Fall bedient hat,
- und wer die Entscheidung formal verantwortet.

Jeder dieser Beteiligten kann mit einiger Berechtigung auf einen anderen
zeigen. Der Modellanbieter weist darauf hin, dass sein System nicht für diesen
Zweck bestimmt war. Der Anwendungshersteller verweist auf das Modell. Der
Betreiber verweist auf die Zusicherungen des Herstellers. Der Bediener
verweist darauf, dass er der Empfehlung folgen sollte. Am Ende steht der
Geschädigte vor einer Kette, in der jedes Glied auf das nächste zeigt.

Fachlich heißt das **Verantwortungslücke**. Sie ist der Grund, warum die
juristische Aufarbeitung solcher Fälle bislang Jahre dauert und selten
befriedigend endet.

## Warum die üblichen Werkzeuge nicht ganz greifen

Das Haftungsrecht kennt zwei bewährte Wege, und beide passen nur teilweise.

**Verschuldenshaftung** setzt voraus, dass jemand eine Sorgfaltspflicht
verletzt hat. Bei einem System, dessen Fehlerquote bekannt und unvermeidbar
ist, ist unklar, worin die Sorgfaltsverletzung liegen soll — der Hersteller hat
den Stand der Technik eingehalten, und der Anwender hat das Produkt bestimmungsgemäß
verwendet. Trotzdem ist ein Schaden entstanden.

**Produkthaftung** greift bei fehlerhaften Produkten unabhängig vom
Verschulden. Sie war jedoch auf körperliche Gegenstände zugeschnitten und
brauchte einen Fehlerbegriff, der bei einem lernenden System schwer zu fassen
ist: Ist es fehlerhaft, wenn es in einem von tausend Fällen irrt, obwohl genau
das seiner Spezifikation entspricht?

Die europäische Gesetzgebung hat auf diese Lücke reagiert. Die überarbeitete
Produkthaftungsrichtlinie erfasst Software und KI-Systeme ausdrücklich als
Produkte, schließt nachträgliche Aktualisierungen und selbstlernendes Verhalten
ein und erleichtert Geschädigten die Beweisführung — unter anderem durch
Offenlegungspflichten und durch Vermutungsregeln, wenn ein System technisch zu
komplex ist, um seinen Fehler nachzuweisen. Das ist ein Fortschritt. Aus der
Praxis wird sich in den nächsten Jahren zeigen, wie weit er reicht.

## Der Mensch als Blitzableiter

In vielen Anwendungen wird die Lücke durch eine Konstruktion geschlossen, die
auf dem Papier gut aussieht: **Der Mensch entscheidet, das System berät nur.**

Diese Konstruktion ist häufig eine Fiktion, und zwar aus drei nachweisbaren
Gründen.

**Zeit.** Wer dreihundert Vorgänge am Tag zu bearbeiten hat und für jeden eine
Empfehlung bekommt, kann nicht dreihundertmal selbständig prüfen. Die
Kontrollinstanz ist eingeplant, aber nicht ausgestattet.

**Autoritätsgefälle.** Von einer Empfehlung abzuweichen, verlangt Begründung;
ihr zu folgen, verlangt keine. Wer abweicht und danebenliegt, hat sich
angreifbar gemacht; wer folgt und danebenliegt, hat sich an die Vorgabe
gehalten. Diese Asymmetrie erzeugt zuverlässig Zustimmung.

**Fehlende Beurteilbarkeit.** Wer nicht weiß, worauf eine Empfehlung beruht,
kann sie nicht prüfen, sondern nur annehmen oder ablehnen — und ohne Grundlage
wird er annehmen.

Das Ergebnis ist eine Verantwortungsverschiebung nach unten: Der
Sachbearbeiter, die Pflegekraft, der Fahrer trägt die Haftung für Ergebnisse
eines Systems, das er weder gebaut noch ausgewählt hat noch versteht. Diese
Konstruktion ist in mehreren Branchen bereits Praxis und gehört zu den
unfairsten Nebenwirkungen der ganzen Entwicklung.

> Woran man erkennt, ob die menschliche Kontrolle echt ist:
>
> Wie viele Empfehlungen weicht die Kontrollinstanz im Betrieb tatsächlich ab?
> Liegt der Anteil dauerhaft nahe null, ist keine Kontrolle vorhanden, sondern
> eine Unterschrift. Diese Zahl sollte jede Organisation erheben — sie ist der
> einzige belastbare Prüfstein.

## Was funktionieren würde

**Gefährdungshaftung für Hochrisikoanwendungen.** Wer ein System betreibt, das
über Menschen entscheidet, haftet für dessen Schäden unabhängig vom
Verschulden — wie beim Halter eines Kraftfahrzeugs. Das ist einfach,
kalkulierbar und erzeugt genau die richtigen Anreize: Wer haftet, prüft.

**Pflicht zur Protokollierung.** Ohne Aufzeichnung von Eingaben, Ausgaben,
Modellstand und menschlicher Entscheidung lässt sich im Nachhinein nichts
klären. Die europäische KI-Verordnung sieht das für Hochrisikosysteme vor. Es
ist die Voraussetzung für alles Weitere.

**Beweislast beim Betreiber.** Der Geschädigte kann nicht nachweisen, was in
einem Modell geschehen ist, zu dem er keinen Zugang hat. Wer das System
einsetzt, muss belegen, dass es ordnungsgemäß gearbeitet hat.

**Versicherungspflicht.** Der stillste, wirksamste Hebel. Versicherer
verlangen Nachweise, messen Schadenshäufigkeiten und staffeln Prämien. Sie
erzeugen damit eine laufende Qualitätskontrolle, zu der kein Gesetzgeber die
Detailkenntnis hätte.

**Und der einfachste Grundsatz von allen:** Wer Ergebnisse eines Systems
verwendet, verantwortet sie — auch wenn das System sie erzeugt hat. „Das hat
die KI gemacht“ ist keine Entlastung. Es ist die Beschreibung einer
Entscheidung, ein solches System einzusetzen.
