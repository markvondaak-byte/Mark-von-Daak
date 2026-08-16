---
typ: kapitel
nummer: 3
titel: Was ein Sprachmodell wirklich tut
kopfzeile: Was Sprachmodelle tun
---

# Was ein Sprachmodell wirklich tut

Wer zum ersten Mal mit einem modernen Sprachmodell schreibt, macht eine
merkwürdige Erfahrung. Die Antworten sind formuliert wie von einem
aufmerksamen Gegenüber. Sie greifen den Ton auf, gehen auf Zwischenfragen ein,
räumen Fehler ein. Der Eindruck eines Gesprächs stellt sich unwillkürlich ein,
und er hält sich auch dann, wenn man weiß, dass keiner da ist.

Deshalb lohnt es sich, einmal genau hinzusehen, was tatsächlich passiert.

## Die Grundoperation: das nächste Stück Text

Ein Sprachmodell zerlegt Text in kleine Einheiten, sogenannte **Token** — etwa
Wortteile. „Unwahrscheinlich“ kann in drei Token zerfallen, „und“ ist eines.
Das Modell tut im Kern genau eine Sache: Es bekommt eine Folge von Token und
berechnet, welches Token als nächstes kommt. Genauer: Es berechnet für jedes
mögliche Token eine Wahrscheinlichkeit. Dann wird eines ausgewählt, angehängt,
und die Rechnung beginnt von vorn.

Das ist alles. Ein ganzer Aufsatz entsteht Stück für Stück, jedes auf Basis
alles Vorangegangenen.

Man kann diese Beschreibung auf zwei Weisen missverstehen. Die eine
unterschätzt sie: „Nur Autovervollständigung“ — als wäre das Erzeugen eines
juristisch brauchbaren Vertragsentwurfs dasselbe wie die Wortvorschläge auf
dem Telefon. Um vorherzusagen, wie ein Text weitergeht, muss ein System sehr
viel über den Aufbau von Argumenten, über Fachsprachen und über die
beschriebene Welt in seinen Gewichten abgelegt haben. Diese abgelegte Struktur
ist real und leistungsfähig.

Die andere überschätzt sie: Weil die Ausgabe wie Denken aussieht, wird
angenommen, dass gedacht wird. Aber es gibt kein Modell der Welt, an dem
Aussagen geprüft würden, keine Absicht, keine Erfahrung, kein Interesse am
Ausgang. Es gibt eine außerordentlich gute Statistik über Sprache — und Sprache
ist nun einmal der Stoff, in dem Menschen ihr Wissen abgelegt haben.

## Warum Sprachmodelle erfinden

Aus dieser Bauweise folgt unmittelbar die bekannteste Schwäche. Ein
Sprachmodell erzeugt die plausibelste Fortsetzung — nicht die wahre. In den
allermeisten Fällen fällt beides zusammen, weil wahre Aussagen in den
Trainingsdaten häufiger vorkommen als falsche. Aber wo das Wissen dünn ist,
erzeugt das Modell trotzdem etwas. Es kennt keinen Zustand „ich weiß es
nicht“, den es von selbst erreichen würde; es hat gelernt, dass auf eine Frage
eine Antwort folgt.

Das Ergebnis sind erfundene Quellenangaben, erfundene Paragraphen, erfundene
Studien — im Fachjargon **Halluzinationen**, ein beschönigender Ausdruck für
einen Systemfehler. Er wird durch bessere Modelle seltener, verschwindet aber
nicht, weil er kein Bedienfehler ist, sondern in der Bauart liegt.

Praktisch heißt das: Ein Sprachmodell ist stark bei Aufgaben, bei denen der
Nutzer das Ergebnis beurteilen kann, und riskant bei Aufgaben, bei denen er es
nicht kann. Wer einen Text umformuliert bekommt, sieht sofort, ob es taugt. Wer
nach einer Rechtsnorm fragt, die er nicht kennt, sieht es nicht.

> Faustregel für den Alltag:
>
> Fragen Sie ein Sprachmodell nach Form, Struktur und Varianten — dort ist es
> stark. Bei Tatsachen, Zahlen, Zitaten und Rechtsfragen behandeln Sie jede
> Ausgabe als unbelegte Behauptung, bis Sie sie geprüft haben.

## Was nach dem Training geschieht

Ein frisch trainiertes Modell ist noch nicht das, was Nutzer zu sehen bekommen.
Es folgen zwei weitere Schritte, die den Charakter des Systems prägen.

**Instruktionstraining.** Das Modell wird mit Beispielen nachtrainiert, in
denen auf eine Anweisung eine gute Antwort folgt. Erst dadurch wird aus einem
Textfortsetzer ein Assistent, der Aufforderungen befolgt.

**Rückmeldung durch Menschen.** Menschen bewerten Antwortpaare — welche ist
besser? Aus diesen Bewertungen entsteht ein zweites Modell, das menschliche
Vorlieben nachbildet, und mit dessen Hilfe wird das Sprachmodell weiter
justiert. So werden Höflichkeit, Ausführlichkeit, Vorsicht und die Weigerung
bei bestimmten Themen eingestellt.

Dieser zweite Schritt ist der Ort, an dem Werturteile in das System kommen.
Wer die Bewerter auswählt, wer ihre Richtlinien schreibt, wer festlegt, was als
schädlich gilt — der prägt das Verhalten des Systems für Millionen Nutzer.
Diese Entscheidungen sind selten öffentlich einsehbar. Sie sind einer der
Gründe, warum Kapitel 17 die Frage der Anbieterkonzentration ernst nimmt.

## Kontextfenster, Gedächtnis, Werkzeuge

Ein Sprachmodell hat kein Gedächtnis im menschlichen Sinn. Was es
berücksichtigen kann, steht in seinem **Kontextfenster** — der Textmenge, die
bei einer Anfrage mitgegeben wird. Alles darüber hinaus existiert für das
Modell nicht. Wirkt ein System, als erinnere es sich an frühere Gespräche,
wurde ein Auszug davon technisch wieder mitgeschickt.

Diese Grenze hat man auf zwei Wegen erweitert. Der eine ist das **Nachschlagen
in Dokumenten**: Vor der Antwort durchsucht ein Zusatzsystem eine Datenbank
und legt die passenden Ausschnitte in den Kontext. So arbeiten die meisten
firmeninternen Anwendungen, und so lässt sich das Erfinden deutlich eindämmen —
das Modell kann sich auf Belege stützen statt auf Erinnerung.

Der andere ist die **Werkzeugnutzung**: Das Modell darf Programme aufrufen —
eine Suchmaschine, einen Taschenrechner, eine Datenbankabfrage, eine
Schnittstelle zu anderer Software. Aus dem Textgenerator wird damit ein System,
das in der Welt etwas auslöst. Genau an dieser Stelle wechselt das Thema von der
Frage „Ist die Antwort richtig?“ zur Frage „Was hat es getan?“ — mit allen
Haftungsfragen, die daran hängen.

## Der Kern in vier Sätzen

Ein Sprachmodell sagt Text voraus. Es tut das auf der Grundlage von Mustern,
die es aus riesigen Textmengen gezogen hat. Es hat kein Weltbild, keine
Absicht und keinen Zugang zur Wahrheit, sondern eine Statistik über Sprache.
Und es ist trotzdem eines der nützlichsten Werkzeuge, die je gebaut wurden —
für jeden, der weiß, wofür es taugt.
