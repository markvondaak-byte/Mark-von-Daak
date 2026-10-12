# Coaching mit Mark — Klienten-App

Eine **PWA**: läuft im Browser, lässt sich auf dem Homescreen installieren und
funktioniert nach dem ersten Aufruf offline. Kein Framework, kein Build-Schritt,
keine Abhängigkeiten zur Laufzeit — gebaut wie die beiden Apps daneben.

Abgrenzung: `app/` begleitet durch das Ernährungsprogramm aus den Büchern,
`business/` ist Marks eigenes Kontaktwerkzeug. **Diese App ist für Klienten im
Fitness-Coaching** und deckt alles ab, was zwischen zwei Coach-Kontakten passiert.

## Was die App kann

| Bereich | Inhalt |
|---|---|
| **Einrichtung** | Name, Ziel, Körperdaten, Aktivität, Trainingstage, Ort, Erfahrung. Daraus Kalorien- und Makroziele und ein fertiger Trainingsplan |
| **Heute** | Nächstes Training mit Start-Knopf, Ringe für Kalorien, Eiweiß, Schritte und Schlaf, Wasser, Gewohnheiten mit Serien, Check-in-Erinnerung, Tipp des Tages |
| **Training** | Plan (2–5 Tage, Studio oder Zuhause), Workout-Modus mit Satzprotokoll, Vorwerten vom letzten Mal, Pausentimer mit Vibration und Ton, Übung tauschen, Rekorde (geschätztes 1RM), Verlauf, Übungsbibliothek mit 45 Übungen und Anleitung, Planeditor |
| **Ernährung** | Tagebuch nach Mahlzeiten mit 83 Lebensmitteln, Rezeptportionen und Schnelleintrag, Makrobalken, Wasser, Tage blättern |
| **Meal Prep** | 18 Rezepte mit Nährwerten je Portion, Haltbarkeit, Portionsrechner. Ausgewählte Rezepte ergeben eine zusammengerechnete, abhakbare **Einkaufsliste** zum Teilen |
| **Check-in** | Täglich: Schritte, Schlaf (Uhrzeiten → Dauer, Erholung 1–5), Gewicht, Energie, Gewohnheiten. Wöchentlich: Fragebogen plus automatisch errechnete Wochenzahlen, als fertiger Text **per WhatsApp oder E-Mail an den Coach** |
| **Fortschritt** | Gewicht mit 7-Tage-Durchschnitt, Schritte und Schlaf der Woche, Trainingsvolumen über 8 Wochen, Bestwerte, Körpermaße, **Fortschrittsfotos** mit Vorher-Nachher-Vergleich |
| **Einstellungen** | Profil, Makros vom Coach überschreibbar, Coach-Kontakt, Check-in-Wochentag, Hell/Dunkel, Sicherung exportieren und einlesen |

## Berechnungen

- **Grundumsatz** nach Mifflin-St Jeor, mal Aktivitätsfaktor (1,3 bis 1,8).
- **Ziel:** Fett verlieren −20 %, Muskelaufbau +10 %, Fitness ±0 — nie unter
  den Grundumsatz.
- **Eiweiß** 2,0 / 1,8 / 1,6 g je kg, **Fett** 0,8 g je kg, Rest Kohlenhydrate.
  Ab BMI 30 rechnet die App mit dem Gewicht bei BMI 27, sonst würden die
  Mengen unrealistisch hoch.
- **1RM** nach Epley: Gewicht × (1 + Wiederholungen / 30).

Setzt der Coach unter Einstellungen eigene Werte, bleiben die stehen, bis
„Automatisch berechnen" gedrückt wird.

## Inhalte pflegen

```
daten/uebungen.json      Übungen: Gruppe, Studio/Zuhause, Ausführung, Tipp
daten/lebensmittel.json  Nährwerte je 100 g und übliche Portion
daten/rezepte.json       Meal-Prep-Rezepte, Zutaten mit Menge für den Portionsrechner
```

Die Trainingsplan-Vorlagen und der Ersatz von Studio-Übungen fürs Training
zuhause stehen oben in `app.js` (`T`, `PLAN_VORLAGEN`, `ERSATZ_ZUHAUSE`). Die
Coach-Kontaktdaten sind als Vorgabe in `Speicher.leer()` hinterlegt.

Nach jeder Änderung `VERSION` in `sw.js` erhöhen — sonst sehen bestehende
Nutzer das Update nicht.

## Icons

```bash
python3 coaching/build/build_icons.py
```

Hantel in Orange — bewusst anders als Pulslinie in Rot (`app/`) und Knoten in
Petrol (`business/`), damit alle drei auf einem Homescreen unterscheidbar sind.

## Lokal ausprobieren

```bash
cd coaching && python3 -m http.server 8899
```

## Daten der Klienten

Alles liegt auf dem Gerät: Einträge im `localStorage`, Fotos (auf 1000 px
verkleinert) in IndexedDB. Kein Server, kein Konto — und damit auch kein
Zugriff des Coachs auf die Rohdaten. Was der Coach bekommt, schickt der Klient
im Check-in selbst ab. Sicherung und Umzug aufs neue Gerät über
Einstellungen → Sicherung exportieren (Fotos optional).

## Grenzen

- **Schritte und Schlaf werden eingetippt.** Eine Web-App darf Apple Health
  oder Google Fit nicht auslesen; dafür bräuchte es eine native App.
- **Keine Push-Benachrichtigungen** — die Check-in-Erinnerung erscheint beim
  Öffnen der App und als Punkt am Reiter.
- **Kein Coach-Dashboard.** Wer alle Klienten live sehen will, braucht einen
  Server mit Konten und Auftragsverarbeitung nach DSGVO.
- **Kein medizinischer Ratgeber.** Der Gesundheitshinweis steht bei der
  Einrichtung und in den Einstellungen und darf nicht entfernt werden.
