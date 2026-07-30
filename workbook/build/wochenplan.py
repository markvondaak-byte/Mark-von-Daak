"""Die zentrale Wahrheitstabelle des Workbooks: welcher Tag welche Farbe hat.

Alles andere im Workbook wird daraus erzeugt — die 84 Tagesseiten, die
Wochenauftakte und die Prüfungen in der Endabnahme. Wer die Farbverteilung
ändern will, ändert sie hier und nirgendwo sonst.

Herleitung aus dem Phasenaufbau:

  Woche 1–2   Vorbereitung, 14 Tage, noch keine Tagesfarben
  Woche 3     Aktivierung beginnt mit sieben weißen Tagen
  Woche 4–6   überwiegend grün, zwei weiße Tage pro Woche im Abstand
              von vier Tagen (Montag und Freitag)
  Woche 7–12  Stabilisierung: grün als Basis, ein bis zwei rote Tage,
              jeder rote Tag wird durch einen weißen ausgeglichen

Nach Woche 12 ist die Stabilisierungsphase noch nicht vorbei — sie dauert
mindestens 90 Tage. Das Workbook endet deshalb mit einem Ausblick, nicht mit
einer Ziellinie.
"""

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
              "Freitag", "Samstag", "Sonntag"]

VORBEREITUNG = "vorbereitung"
WEISS = "weiss"
GRUEN = "gruen"
ROT = "rot"

# Woche 1–2: Ernährung bleibt unverändert, nur Nährstoffe und Joghurt.
_VORBEREITUNGSWOCHE = [VORBEREITUNG] * 7

# Woche 3: die weiße Woche.
_WEISSE_WOCHE = [WEISS] * 7

# Woche 4–6: Montag und Freitag weiß — vier Tage Abstand.
_AKTIVIERUNGSWOCHE = [WEISS, GRUEN, GRUEN, GRUEN, WEISS, GRUEN, GRUEN]

# Stabilisierung, ungerade Wochen: ein roter Tag, ein weißer danach.
_STABIL_EIN_ROT = [GRUEN, GRUEN, GRUEN, GRUEN, ROT, WEISS, GRUEN]

# Stabilisierung, gerade Wochen: zwei rote Tage, zwei weiße danach.
_STABIL_ZWEI_ROT = [GRUEN, GRUEN, GRUEN, ROT, ROT, WEISS, WEISS]


PHASEN = {
    "vorbereitung": {
        "name": "Vorbereitungsphase",
        "kurz": "Vorbereitung",
        "wochen": (1, 2),
    },
    "aktivierung": {
        "name": "Aktivierungsphase",
        "kurz": "Aktivierung",
        "wochen": (3, 6),
    },
    "stabilisierung": {
        "name": "Stabilisierungsphase",
        "kurz": "Stabilisierung",
        "wochen": (7, 12),
    },
}

# Ein Schwerpunktthema pro Woche — gibt dem Wochenauftakt einen Fokus.
FOKUS = {
    1: ("Ankommen",
        "Ändere noch nichts an deinem Essen. Nimm nur die Nährstoffe und den "
        "Joghurt dazu und beobachte, was sich verändert."),
    2: ("Der Einkauf",
        "Diese Woche wird eingekauft und vorbereitet. Geh die Einkaufsliste "
        "durch und prüfe deine Gewürze auf Salz und Zucker."),
    3: ("Durchhalten",
        "Die weiße Woche ist die anstrengendste. Trink viel, iss genug Fett "
        "und leg keinen Sport ein. Die Umstellung dauert drei bis zehn Tage."),
    4: ("Kauen",
        "Nimm dir diese Woche das Kauen vor — rund 32-mal pro Bissen. Zähl "
        "an zwei, drei Mahlzeiten bewusst mit."),
    5: ("Trinken",
        "Zwei Liter stilles Wasser, immer mit 15 bis 20 Minuten Abstand zu "
        "den Mahlzeiten. Kontrolle: Der Urin sollte fast farblos sein."),
    6: ("Das Ende der Aktivierung",
        "Letzte Woche der strengen Phase. Miss am Ende deine Werte und "
        "vergleiche sie mit dem Start."),
    7: ("Der Übergang",
        "Die Stabilisierung beginnt. Salz kehrt zurück — sparsam, 2 bis 5 g "
        "am Tag, und nie an weißen Tagen."),
    8: ("Der erste rote Tag",
        "Geh ihn langsam an. Ein bis zwei Mahlzeiten mit dem, worauf du Lust "
        "hast, reichen. Beobachte, wie dein Körper reagiert."),
    9: ("Auswärts essen",
        "Diese Woche übst du das Essen außer Haus. Gemüse und Eiweiß wählen, "
        "Beilage klein halten — das geht auf fast jeder Speisekarte."),
    10: ("Der weiße Tag als Werkzeug",
         "Der weiße Tag bleibt streng, auch jetzt. Genau darauf beruht seine "
         "Ausgleichswirkung."),
    11: ("Gewohnheiten prüfen",
         "Was ist selbstverständlich geworden, was kostet noch Überwindung? "
         "Notiere beides."),
    12: ("Der Blick nach vorn",
         "Letzte Woche in diesem Buch — aber nicht das Ende der "
         "Stabilisierung. Die läuft noch rund sieben Wochen weiter."),
}


def _wochenmuster(woche):
    if woche <= 2:
        return _VORBEREITUNGSWOCHE
    if woche == 3:
        return _WEISSE_WOCHE
    if woche <= 6:
        return _AKTIVIERUNGSWOCHE
    return _STABIL_EIN_ROT if woche % 2 else _STABIL_ZWEI_ROT


def phase_der_woche(woche):
    for schluessel, daten in PHASEN.items():
        von, bis = daten["wochen"]
        if von <= woche <= bis:
            return schluessel, daten
    raise ValueError(f"Woche {woche} liegt außerhalb des Plans.")


def ist_vorschlag(woche):
    """Ab der Stabilisierung sind die Farben Vorschläge, keine Vorgabe.

    Das Konzept will hier ausdrücklich Anpassung an den Alltag — deshalb
    werden die Farben ab Woche 7 zum Ankreuzen gedruckt statt fest vorgegeben.
    """
    return woche >= 7


def wochen():
    """Liefert alle zwölf Wochen mit ihren Tagen."""
    ergebnis = []
    tagesnummer = 1
    for woche in range(1, 13):
        schluessel, phase = phase_der_woche(woche)
        muster = _wochenmuster(woche)
        tage = []
        for index, farbe in enumerate(muster):
            tage.append({
                "nummer": tagesnummer,
                "wochentag": WOCHENTAGE[index],
                "farbe": farbe,
                "vorschlag": ist_vorschlag(woche),
            })
            tagesnummer += 1
        fokus_titel, fokus_text = FOKUS[woche]
        ergebnis.append({
            "nummer": woche,
            "phase": schluessel,
            "phase_name": phase["name"],
            "phase_kurz": phase["kurz"],
            "tage": tage,
            "fokus_titel": fokus_titel,
            "fokus_text": fokus_text,
            "vorschlag": ist_vorschlag(woche),
        })
    return ergebnis


def verteilung():
    """Zählt die Tagesfarben — dient der Abnahmeprüfung."""
    summe = {}
    for woche in wochen():
        for tag in woche["tage"]:
            summe[tag["farbe"]] = summe.get(tag["farbe"], 0) + 1
    return summe


if __name__ == "__main__":
    alle = wochen()
    print(f"{len(alle)} Wochen, {sum(len(w['tage']) for w in alle)} Tage\n")
    kurz = {VORBEREITUNG: "–", WEISS: "W", GRUEN: "G", ROT: "R"}
    for woche in alle:
        farben = " ".join(kurz[t["farbe"]] for t in woche["tage"])
        marke = "(Vorschlag)" if woche["vorschlag"] else ""
        print(f"  Woche {woche['nummer']:2d}  {woche['phase_kurz']:15s} "
              f"{farben}  {marke}")
    print(f"\nVerteilung: {verteilung()}")
