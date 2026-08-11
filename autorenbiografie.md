---
verwendung: Autorenprofil bei Amazon (Author Central) und „Über den Autor"
grenze: Author-Central-Biografie 2500 Zeichen
---

# Autorenbiografie

Vier Längen derselben Biografie, von einer Zeile bis zur vollen Fassung. Alle
sagen dasselbe — sie unterscheiden sich nur darin, wie viel Platz zur Verfügung
steht.

Inhaltlich decken sie sich mit dem Kapitel „Ein Wort in eigener Sache" in
Band 1 (`buch/kapitel/62-in-eigener-sache.md`). Nichts steht hier, was dort
nicht steht — wer das Kapitel ändert, prüft diese Datei mit.

**Wohin welche Fassung gehört**

| Fassung | Ort |
|---|---|
| Eine Zeile | Umschlagrückseite, Beiträge, Signatur |
| Kurz | Ende der Amazon-Beschreibung, als Block „Über den Autor" |
| Mittel | Autorenprofil, wenn es knapp gehalten sein soll |
| Lang | Author Central — Biografie |

Das Feld für die Biografie liegt **nicht** im KDP-Formular, in dem der Titel
angelegt wird, sondern im Autorenkonto bei Author Central
(`author.amazon.de`). Von dort speist Amazon den Abschnitt „Über den Autor"
auf den Produktseiten aller verknüpften Titel. Das Feld nimmt reinen Text —
Auszeichnung wird verworfen, Absätze bleiben erhalten.

Auf der Produktseite selbst erscheint die Biografie erst, wenn Amazon Titel
und Autorenkonto verknüpft hat; das dauert nach der Veröffentlichung ein paar
Tage. Bis dahin ist die Kurzfassung am Ende der Buchbeschreibung die einzige
Stelle, an der ein Leser erfährt, wer da schreibt — deshalb steht sie dort
auch dauerhaft.

---

## Eine Zeile

> Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der Umstellung
> ihrer Ernährung.

---

## Kurz (rund 400 Zeichen)

> „Muss ich wirklich alle vier Mahlzeiten essen?" — Fragen wie diese bekommt
> Mark von Daak jede Woche gestellt. Er lebt in Wolfsburg und begleitet
> Menschen bei der Umstellung ihrer Ernährung: über Monate, durch die erste
> Woche, durch die Tage, an denen die Waage stillsteht. Daraus sind seine
> Bücher entstanden. Ohne Produktempfehlungen, ohne Marken und ohne eine Zahl,
> die jemandem versprochen wird.

---

## Mittel (rund 900 Zeichen)

> „Muss ich wirklich alle vier Mahlzeiten essen?" — Fragen wie diese bekommt
> Mark von Daak jede Woche gestellt. Er lebt in Wolfsburg und begleitet
> Menschen bei der Umstellung ihrer Ernährung: über Monate, durch die erste
> Woche, durch die Tage, an denen die Waage stillsteht.
>
> Er ist kein Arzt und kein Ernährungsberater mit Kammerzulassung. Was er
> mitbringt, ist die Praxis — und die Überzeugung, dass ein Konzept nur so viel
> wert ist, wie im Alltag davon übrig bleibt. Seine Bücher beantworten deshalb
> die Fragen, die wirklich gestellt werden, und beschreiben die Stolpersteine,
> über die Menschen tatsächlich stolpern.
>
> Als selbstständiger Vertriebspartner für Nahrungsergänzungsmittel hat er ein
> wirtschaftliches Interesse an diesem Themenfeld. Er schreibt das in seine
> Bücher hinein, statt es zu verschweigen — und empfiehlt darin kein einziges
> Produkt.

---

## Lang (rund 1900 Zeichen, für Author Central)

> „Muss ich wirklich alle vier Mahlzeiten essen?" — Fragen wie diese bekommt
> Mark von Daak jede Woche gestellt. Sie stehen in keinem Konzeptpapier, aber
> sie entscheiden darüber, ob jemand nach drei Wochen weitermacht oder aufgibt.
>
> Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der Umstellung
> ihrer Ernährung. Nicht in der Theorie, sondern über Monate: durch die erste
> Woche, durch die Tage, an denen die Waage stillsteht, und durch die Phase
> danach, die fast alle weglassen.
>
> Er ist kein Arzt, kein Ökotrophologe und kein Ernährungsberater mit
> Kammerzulassung. Was er mitbringt, ist die Praxis — und die Überzeugung, dass
> ein Konzept nur so viel wert ist, wie im Alltag davon übrig bleibt.
>
> Genau daraus sind seine Bücher entstanden. Sie beantworten die Fragen, die in
> der Begleitung wirklich gestellt werden, und beschreiben die Stolpersteine,
> über die Menschen tatsächlich stolpern — nicht die, die sich am Schreibtisch
> ausdenken lassen. Die Regeln stehen vollständig darin, mit Mengen, Listen und
> Übergängen, damit niemand raten muss.
>
> Was in seinen Büchern nicht steht, ist ihm dabei genauso wichtig: keine
> Produktempfehlung, keine Marke, keine Zahl, die jemandem versprochen wird.
> Wie ein Körper reagiert, hängt von zu vielen Dingen ab, die weder Leser noch
> Autor kennen.
>
> Als selbstständiger Vertriebspartner für Nahrungsergänzungsmittel hat er ein
> wirtschaftliches Interesse an diesem Themenfeld. Er schreibt das offen in
> seine Bücher hinein, statt darauf zu warten, dass es jemand herausfindet —
> und das Kapitel über Nährstoffe nennt deshalb Qualitätskriterien statt
> Präparate. Damit lässt sich jedes Produkt prüfen, auch eines, mit dem er
> nichts zu tun hat.
>
> Wo ein Ratgeber an seine Grenze kommt, sagt er das. Bei Beschwerden,
> Medikamenten und Diagnosen ist die Ärztin oder der Arzt die richtige Adresse
> — nicht ein Buch.
>
> Fragen zu den Büchern beantwortet er, so gut er kann: markvondaak@icloud.com

---

## Kurzfassung als HTML

Für den Block „Über den Autor" am Ende der Amazon-Beschreibung. Es gelten
dieselben Tags wie dort: `<b>`, `<i>`, `<br>`, `<p>`, `<h4>` bis `<h6>`,
`<ul>`, `<li>` — alles andere verwirft KDP.

Der Block zählt auf die 4000 Zeichen der Beschreibung mit: er ist 692 Zeichen
lang, die Beschreibung von Band 1 ist 3199 Zeichen lang, zusammen 3891. Das
passt, lässt aber nur gut hundert Zeichen Luft — wächst die Beschreibung, hat
sie Vorrang, und die Biografie steht dann nur im Autorenprofil. Bei Band 2 und
Band 3 vorher nachmessen.

```html
<h5>&Uuml;ber den Autor</h5>
<p><b>Mark von Daak</b> lebt in Wolfsburg und begleitet Menschen bei der Umstellung ihrer Ern&auml;hrung &mdash; &uuml;ber Monate, durch die erste Woche und durch die Tage, an denen die Waage stillsteht. Daraus sind seine B&uuml;cher entstanden: die Antworten auf die Fragen, die in der Praxis wirklich gestellt werden.</p>
<p>Er ist kein Arzt und kein Ern&auml;hrungsberater mit Kammerzulassung. Als selbstst&auml;ndiger Vertriebspartner f&uuml;r Nahrungserg&auml;nzungsmittel hat er ein wirtschaftliches Interesse an diesem Themenfeld &mdash; er schreibt das in seine B&uuml;cher hinein, statt es zu verschweigen, und empfiehlt darin kein einziges Produkt.</p>
```

---

## Was nicht hineingehört

**Keine Titel und keine Ausbildung, die es nicht gibt.** „Ernährungsexperte",
„Coach" oder „Spezialist" klingen gut und sind genau die Wörter, an denen sich
eine wettbewerbsrechtliche Abmahnung festmacht. Die Biografie sagt deshalb
zuerst, was er *nicht* ist.

**Keine fremde Marke.** „cellRESET" und „FitLine" gehören der
PM-International AG. Im Buch steht die Bezeichnung beschreibend mit
Markenhinweis; in einem Verkaufstext wirkt sie als Werbung mit fremdem
Kennzeichen — dasselbe Problem wie bei den Keywords.

**Keine Zahl über Kilogramm, Konfektionsgrößen oder Zeiträume**, weder über
Leser noch über den Autor selbst. Eine Erfolgsgeschichte in der Biografie ist
eine Werbeaussage wie jede andere.

**Keine Erfindung von Reichweite.** Keine Teilnehmerzahlen, keine „Hunderte
begleitet", solange sich das nicht belegen lässt. „Über Monate begleitet" ist
richtig und reicht.

**Die Postanschrift gehört ins Impressum, nicht in die Biografie.** Im Buch
steht sie, weil sie dort hingehört. Im Autorenprofil steht sie ohne Anlass
öffentlich; die E-Mail-Adresse genügt.
