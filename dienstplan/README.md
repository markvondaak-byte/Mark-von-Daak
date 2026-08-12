# Dienstplan Fitnessstudio — 4-Wochen-Rotation

Rollierender Dienstplan für ein Team aus zwei Vollzeitkräften, zwei
Teilzeitkräften und einer Minijob-Kraft. Nach Woche 4 beginnt der Zyklus wieder
mit Woche 1.

- **Plan:** `Dienstplan_Fitnessstudio_4-Wochen.xlsx`
- **Quelle:** `generate_dienstplan.py` — erzeugt die Datei neu und prüft sie

## Öffnungszeiten

| Tag | Öffnung | Stunden |
|---|---|---|
| Montag | 06:00 – 22:00 | 16 |
| Dienstag | 08:00 – 24:00 | 16 |
| Mittwoch | 06:00 – 22:00 | 16 |
| Donnerstag | 08:00 – 24:00 | 16 |
| Freitag | 06:00 – 22:00 | 16 |
| Samstag | 09:00 – 20:00 | 11 |
| Sonntag | 09:00 – 20:00 | 11 |
| **Summe** | | **102** |

## Schichten

Die Zeiten hängen vom Tag ab, weil Montag/Mittwoch/Freitag früher öffnen und
Dienstag/Donnerstag später schließen.

| Code | Schicht | Mo / Mi / Fr | Di / Do | Sa / So | Arbeitszeit |
|---|---|---|---|---|---|
| F | Frühdienst | 06:00 – 14:30 | 08:00 – 16:30 | — | 8,0 h |
| S | Spätdienst | 13:30 – 22:00 | 15:30 – 24:00 | — | 8,0 h |
| Z | Zwischendienst | 16:30 – 21:00 | 17:30 – 22:00 | — | 4,5 h |
| T | Tagesdienst | — | — | 09:00 – 20:00 | 10,0 h |

Pausen sind unbezahlt und in den Arbeitszeiten bereits abgezogen: 30 Minuten bei
Früh- und Spätdienst, 60 Minuten beim Wochenend-Tagesdienst.

Dazu drei Blöcke ohne Thekenbindung:

| Code | Block | Lage | Dauer |
|---|---|---|---|
| B | Bürozeit | im Anschluss an den Frühdienst bzw. vor dem Spätdienst | 1,0 h |
| P | Studioaufgaben | vor dem Zwischendienst — Probetraining, Gerätecheck | 1,5 h |
| V | Verwaltung | großer Büroblock, danach 30 min Pause, dann Zwischendienst | 3,5 h |

## Besetzungslogik

- Während der gesamten Öffnungszeit ist mindestens eine Person im Studio.
- Früh- und Spätdienst überlappen sich eine Stunde — Zeit für die Übergabe.
- Abends kommt an allen fünf Werktagen ein Zwischendienst dazu, damit die
  Hauptlastzeit doppelt besetzt ist: 16:30 – 21:00 an Mo/Mi/Fr, 17:30 – 22:00 an
  Di/Do.
- Am Wochenende trägt eine Person den ganzen Tag. Der Bedarf rechtfertigt dort
  keine zweite Kraft.

## Stundenverteilung

| | Vertrag | Woche 1 | Woche 2 | Woche 3 | Woche 4 | 4 Wochen | Soll | Konto |
|---|---|---|---|---|---|---|---|---|
| VZ 1 | 40 h | 41,0 | 41,0 | 43,0 | 35,0 | 160,0 | 160,0 | ± 0 |
| VZ 2 | 40 h | 41,0 | 41,0 | 35,0 | 43,0 | 160,0 | 160,0 | ± 0 |
| TZ 1 | 20 h | 24,0 | 16,0 | 18,5 | 22,0 | 80,5 | 80,0 | + 0,5 |
| TZ 2 | 20 h | 16,0 | 24,0 | 22,0 | 18,5 | 80,5 | 80,0 | + 0,5 |
| MJ | 9 h | 9,0 | 9,0 | 9,0 | 9,0 | 36,0 | 36,0 | ± 0 |

Die Wochenstunden schwanken, die Vier-Wochen-Summe trifft den Vertrag. Bei den
Teilzeitkräften bleiben 0,5 Stunden je Zyklus übrig — die gehören ins
Gleitzeitkonto oder werden ausbezahlt.

## Wochenendverteilung

Über den Zyklus arbeitet jede Person zwei Wochenendtage; kein Mensch hat zwei
Wochenenden hintereinander voll besetzt.

| Woche | Samstag | Sonntag |
|---|---|---|
| 1 | TZ 1 | TZ 2 |
| 2 | TZ 2 | TZ 1 |
| 3 | VZ 2 | VZ 1 |
| 4 | VZ 1 | VZ 2 |

Die Minijob-Kraft hat keinen Wochenenddienst — zwei feste Abenddienste pro Woche
passen besser zu neun Stunden.

## Arbeitsrechtliche Grundlagen

Das Skript prüft diese Punkte bei jedem Erzeugen und bricht bei Verstoß ab.

- **Ruhezeit** — mindestens 11 Stunden zwischen zwei Diensten (§ 5 ArbZG). Auf
  einen Spätdienst folgt deshalb nie ein Frühdienst am nächsten Tag, und wer
  sonntags den Tagesdienst hat, hat am Montag frei.
- **Höchstarbeitszeit** — höchstens 10 Stunden am Tag (§ 3 ArbZG). Der
  Wochenend-Tagesdienst nutzt diesen Rahmen aus; der Ausgleich auf 8 Stunden im
  Sechs-Monats-Schnitt ist durch die übrigen Wochen gedeckt.
- **Pausen** — 30 Minuten bei mehr als 6 Stunden, 45 Minuten bei mehr als
  9 Stunden (§ 4 ArbZG).
- **Nachtarbeit** — der Spätdienst an Di/Do endet um 24:00 und liegt damit nur
  eine Stunde in der Nachtzeit. Das ist keine Nachtarbeit im Sinne des § 2
  Abs. 4 ArbZG, es entsteht also kein Anspruch auf Nachtzuschlag oder
  arbeitsmedizinische Untersuchung.
- **Sonntagsarbeit** — in Sportbetrieben zulässig (§ 10 Abs. 1 Nr. 4 ArbZG). Der
  Ersatzruhetag liegt jeweils in derselben Woche. Bei 13 Sonntagsdiensten pro
  Person und Jahr bleiben weit mehr als die geforderten 15 beschäftigungsfreien
  Sonntage (§ 11 Abs. 1 ArbZG).
- **Minijob** — 9,0 h/Woche entsprechen 39,0 h im Monat (Faktor 13/3). Bei
  13,90 €/h sind das 542,10 € gegenüber der Geringfügigkeitsgrenze von 603 €.
  Der Abstand von rund 61 € trägt auch Monate mit fünf Abrechnungswochen und
  eine gelegentliche Vertretungsschicht.

Das ersetzt keine arbeitsrechtliche Beratung. Tarifverträge, Betriebsvereinba-
rungen und individuelle Arbeitsverträge können strengere Regeln enthalten.

## Annahmen

Diese Werte waren nicht vorgegeben und sind gesetzt — bitte prüfen:

1. Teilzeit mit je 20 Wochenstunden.
2. Minijob mit 9,0 Wochenstunden statt der rechnerisch möglichen 10,0, damit die
   Geringfügigkeitsgrenze auch in langen Monaten sicher hält.
3. Mindestbesetzung eine Person, abends zwei.
4. Urlaub, Krankheit und Feiertage sind nicht eingerechnet. Fällt jemand aus,
   ist der Zwischendienst der erste Posten, den man streicht — die Öffnung
   bleibt dann trotzdem besetzt.
5. Kurse, Reinigung durch Dienstleister und Buchhaltung sind nicht abgebildet.

## Plan ändern

Alle Eingaben stehen oben in `generate_dienstplan.py` in den Blöcken
`OEFFNUNG`, `TEAM`, `SCHICHT` und `PLAN`. Nach der Änderung:

```bash
python3 dienstplan/generate_dienstplan.py
```

Das Skript prüft Besetzung, Ruhezeiten, Höchstarbeitszeit und Minijob-Grenze und
schreibt die XLSX-Datei nur, wenn alles hält. Die Summen in der Datei sind
Excel-Formeln — wer direkt in der Tabelle eine Schicht umträgt, sieht die
Auswirkung sofort im Blatt „Stundenkonto".
