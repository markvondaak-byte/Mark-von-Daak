#!/usr/bin/env python3
"""Erzeugt den 4-Wochen-Rotationsdienstplan des Fitnessstudios als XLSX.

Aufruf:  python3 dienstplan/generate_dienstplan.py
Ausgabe: dienstplan/Dienstplan_Fitnessstudio_4-Wochen.xlsx

Alle Eingabewerte stehen in den Blöcken OEFFNUNG, TEAM und PLAN. Wer den Plan
ändern will, ändert dort und lässt das Skript erneut laufen — die Summen im
Blatt "Stundenkonto" sind Excel-Formeln und rechnen sich beim Öffnen neu.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --------------------------------------------------------------------------
# Eingaben
# --------------------------------------------------------------------------

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# Öffnungszeiten laut Vorgabe des Studios
OEFFNUNG = {
    "Mo": ("06:00", "22:00"),
    "Di": ("08:00", "24:00"),
    "Mi": ("06:00", "22:00"),
    "Do": ("08:00", "24:00"),
    "Fr": ("06:00", "22:00"),
    "Sa": ("09:00", "20:00"),
    "So": ("09:00", "20:00"),
}

# Tagestypen: A = 06-22, B = 08-24, C = 09-20
TYP = {"Mo": "A", "Di": "B", "Mi": "A", "Do": "B", "Fr": "A", "Sa": "C", "So": "C"}

MINDESTLOHN = 13.90      # EUR/Std., gesetzlicher Mindestlohn ab 01.01.2026
MINIJOB_GRENZE = 603.00  # EUR/Monat, Geringfügigkeitsgrenze 2026
WOCHEN_JE_MONAT = 13 / 3  # 4,333 — gesetzlicher Umrechnungsfaktor Woche -> Monat

TEAM = [
    # Kürzel, Anzeigename, Vertragsart, Wochenstunden
    ("VZ 1", "VZ 1 — Studioleitung", "Vollzeit", 40.0),
    ("VZ 2", "VZ 2 — Trainer/in", "Vollzeit", 40.0),
    ("TZ 1", "TZ 1 — Trainer/in", "Teilzeit", 20.0),
    ("TZ 2", "TZ 2 — Trainer/in", "Teilzeit", 20.0),
    ("MJ", "MJ — Aushilfe Theke", "Minijob", 9.0),
]
KUERZEL = [k for k, _, _, _ in TEAM]

# Schichtkatalog: (Code, Tagestyp) -> (Beginn, Ende, Pause h, Arbeitszeit h)
SCHICHT = {
    ("F", "A"): ("06:00", "14:30", 0.5, 8.0),
    ("F", "B"): ("08:00", "16:30", 0.5, 8.0),
    ("S", "A"): ("13:30", "22:00", 0.5, 8.0),
    ("S", "B"): ("15:30", "24:00", 0.5, 8.0),
    ("Z", "A"): ("16:30", "21:00", 0.0, 4.5),
    ("Z", "B"): ("17:30", "22:00", 0.0, 4.5),
    ("T", "C"): ("09:00", "20:00", 1.0, 10.0),
}

# Zusatzblöcke ohne Thekenbindung. Lage wird aus der Schicht des Tages abgeleitet.
ZUSATZ = {
    "B": ("Büro", 1.0),    # Verwaltung / Trainingsplanung (Vollzeit)
    "P": ("Aufgaben", 1.5),  # Probetraining, Gerätecheck, Studioaufgaben (Teilzeit)
    "V": ("Verwaltung", 3.5),  # großer Büroblock vor dem Zwischendienst (Vollzeit)
}

NAME = {"F": "Frühdienst", "S": "Spätdienst", "Z": "Zwischendienst",
        "T": "Tagesdienst", "B": "Bürozeit", "P": "Studioaufgaben",
        "V": "Verwaltung"}

# 4-Wochen-Rotation. Woche 3/4 spiegeln Woche 1/2 mit Wochenenddienst der
# Vollzeitkräfte, damit jede Person planbar freie Wochenenden hat.
PLAN = {
    1: {
        "VZ 1": {"Mo": ["F"], "Di": ["F"], "Mi": ["F", "B"], "Do": ["F"], "Fr": ["F"]},
        "VZ 2": {"Mo": ["B", "S"], "Di": ["S"], "Mi": ["S"], "Do": ["S"], "Fr": ["V", "Z"]},
        "TZ 1": {"Mo": ["P", "Z"], "Fr": ["S"], "Sa": ["T"]},
        "TZ 2": {"Di": ["P", "Z"], "So": ["T"]},
        "MJ":   {"Mi": ["Z"], "Do": ["Z"]},
    },
    2: {
        "VZ 2": {"Mo": ["F"], "Di": ["F"], "Mi": ["F", "B"], "Do": ["F"], "Fr": ["F"]},
        "VZ 1": {"Mo": ["B", "S"], "Di": ["S"], "Mi": ["S"], "Do": ["S"], "Fr": ["V", "Z"]},
        "TZ 2": {"Mo": ["P", "Z"], "Fr": ["S"], "Sa": ["T"]},
        "TZ 1": {"Di": ["P", "Z"], "So": ["T"]},
        "MJ":   {"Mi": ["Z"], "Do": ["Z"]},
    },
    # In Woche 3 und 4 übernehmen die Vollzeitkräfte das Wochenende. Wer den
    # Sonntag arbeitet, hat am folgenden Montag frei — sonst blieben nach dem
    # Tagesdienst bis 20:00 nur 10 Stunden bis zum Frühdienst um 06:00.
    3: {
        "VZ 1": {"Di": ["B", "S"], "Mi": ["S"], "Do": ["S"], "Fr": ["S"], "So": ["T"]},
        "VZ 2": {"Di": ["F"], "Mi": ["F", "B"], "Do": ["F"], "Sa": ["T"]},
        "TZ 1": {"Mo": ["S"], "Do": ["Z"], "Fr": ["P", "Z"]},
        "TZ 2": {"Mo": ["F"], "Di": ["P", "Z"], "Fr": ["F"]},
        "MJ":   {"Mo": ["Z"], "Mi": ["Z"]},
    },
    4: {
        "VZ 2": {"Di": ["B", "S"], "Mi": ["S"], "Do": ["S"], "Fr": ["S"], "So": ["T"]},
        "VZ 1": {"Di": ["F"], "Mi": ["F", "B"], "Do": ["F"], "Sa": ["T"]},
        "TZ 2": {"Mo": ["S"], "Do": ["Z"], "Fr": ["P", "Z"]},
        "TZ 1": {"Mo": ["F"], "Di": ["P", "Z"], "Fr": ["F"]},
        "MJ":   {"Mo": ["Z"], "Mi": ["Z"]},
    },
}

WOCHEN_TITEL = {
    1: "Woche 1 — VZ 1 Frühwoche · VZ 2 Spätwoche · Wochenende TZ 1 / TZ 2",
    2: "Woche 2 — VZ 2 Frühwoche · VZ 1 Spätwoche · Wochenende TZ 2 / TZ 1",
    3: "Woche 3 — Wochenenddienst der Vollzeitkräfte (VZ 2 Sa / VZ 1 So)",
    4: "Woche 4 — Wochenenddienst der Vollzeitkräfte (VZ 1 Sa / VZ 2 So)",
}

# --------------------------------------------------------------------------
# Zeitrechnung
# --------------------------------------------------------------------------


def m(hhmm):
    h, mi = hhmm.split(":")
    return int(h) * 60 + int(mi)


def hhmm(minuten):
    return f"{minuten // 60:02d}:{minuten % 60:02d}"


def bloecke(tag, codes):
    """Löst die Codes eines Tages in konkrete Zeitblöcke auf.

    Rückgabe: Liste aus (Code, Beginn, Ende, Arbeitszeit h).
    """
    typ = TYP[tag]
    haupt = [c for c in codes if c in ("F", "S", "Z", "T")]
    out = []
    for code in codes:
        if code in ("F", "S", "Z", "T"):
            beginn, ende, _pause, az = SCHICHT[(code, typ)]
            out.append((code, m(beginn), m(ende), az))
        else:
            _label, dauer = ZUSATZ[code]
            d = int(dauer * 60)
            if not haupt:
                raise ValueError(f"Zusatzblock {code} ohne Schicht an {tag}")
            anker = haupt[0]
            a_beginn, a_ende, _p, _az = SCHICHT[(anker, typ)]
            if anker == "F":
                # Büro schließt direkt an den Frühdienst an
                out.append((code, m(a_ende), m(a_ende) + d, dauer))
            elif code == "V":
                # großer Verwaltungsblock, danach 30 min Pause, dann Zwischendienst
                ende = m(a_beginn) - 30
                out.append((code, ende - d, ende, dauer))
            else:
                # Block liegt unmittelbar vor Spät- oder Zwischendienst
                out.append((code, m(a_beginn) - d, m(a_beginn), dauer))
    return sorted(out, key=lambda b: b[1])


def tag_stunden(tag, codes):
    return round(sum(b[3] for b in bloecke(tag, codes)), 2)


def tag_text(tag, codes):
    if not codes:
        return "frei"
    zeilen = []
    for code, b, e, _az in bloecke(tag, codes):
        zeilen.append(f"{hhmm(b)}–{hhmm(e)}  {code}")
    return "\n".join(zeilen)


def plan_von(woche, person):
    return {tag: PLAN[woche].get(person, {}).get(tag, []) for tag in TAGE}


# --------------------------------------------------------------------------
# Prüfungen — laufen bei jedem Erzeugen des Plans
# --------------------------------------------------------------------------


def pruefe():
    fehler = []
    # 1. Besetzung: jede Öffnungsstunde mindestens eine Person
    for woche in PLAN:
        for tag in TAGE:
            besetzt = []
            for person in KUERZEL:
                for code, b, e, _az in bloecke(tag, plan_von(woche, person)[tag]):
                    if code in ("F", "S", "Z", "T"):
                        besetzt.append((b, e))
            oeffnung = (m(OEFFNUNG[tag][0]), m(OEFFNUNG[tag][1]))
            for minute in range(oeffnung[0], oeffnung[1], 15):
                if not any(b <= minute < e for b, e in besetzt):
                    fehler.append(f"W{woche} {tag} {hhmm(minute)}: keine Besetzung")
                    break
    # 2. Ruhezeit von 11 Stunden zwischen zwei Diensten (§ 5 ArbZG)
    for person in KUERZEL:
        folge = []
        for woche in (1, 2, 3, 4, 1):  # Rundlauf: Übergang W4 -> W1 mitprüfen
            for i, tag in enumerate(TAGE):
                codes = plan_von(woche, person)[tag]
                if codes:
                    bl = bloecke(tag, codes)
                    folge.append((woche, tag, i, bl[0][1], bl[-1][2]))
        for a, b in zip(folge, folge[1:]):
            tage_dazwischen = (b[2] - a[2]) % 7
            if tage_dazwischen == 0:
                continue
            ruhe = tage_dazwischen * 24 * 60 - a[4] + b[3]
            if ruhe < 11 * 60:
                fehler.append(
                    f"{person}: nur {ruhe/60:.1f} h Ruhe zwischen "
                    f"W{a[0]} {a[1]} und W{b[0]} {b[1]}")
    # 3. Höchstarbeitszeit 10 Stunden am Tag (§ 3 ArbZG)
    for woche in PLAN:
        for person in KUERZEL:
            for tag in TAGE:
                std = tag_stunden(tag, plan_von(woche, person)[tag])
                if std > 10:
                    fehler.append(f"W{woche} {person} {tag}: {std} h > 10 h")
    # 4. Minijob-Grenze
    mj_woche = sum(tag_stunden(t, plan_von(w, "MJ")[t])
                   for w in PLAN for t in TAGE) / 4
    entgelt = mj_woche * WOCHEN_JE_MONAT * MINDESTLOHN
    if entgelt > MINIJOB_GRENZE:
        fehler.append(f"Minijob: {entgelt:.2f} EUR/Monat > {MINIJOB_GRENZE} EUR")
    return fehler


# --------------------------------------------------------------------------
# Formatierung
# --------------------------------------------------------------------------

ARIAL = "Arial"
F_TITEL = Font(name=ARIAL, size=14, bold=True)
F_KOPF = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
F_NORMAL = Font(name=ARIAL, size=10)
F_FETT = Font(name=ARIAL, size=10, bold=True)
F_KLEIN = Font(name=ARIAL, size=9, color="595959")
F_ZELLE = Font(name=ARIAL, size=9)

BLAU = PatternFill("solid", fgColor="1F3864")
GRAU = PatternFill("solid", fgColor="F2F2F2")
FARBE = {
    "F": PatternFill("solid", fgColor="DCE9F7"),   # Frühdienst
    "S": PatternFill("solid", fgColor="FDE4D0"),   # Spätdienst
    "Z": PatternFill("solid", fgColor="E2F0D9"),   # Zwischendienst
    "T": PatternFill("solid", fgColor="EADCF5"),   # Wochenend-Tagesdienst
    "B": PatternFill("solid", fgColor="EDEDED"),
    "P": PatternFill("solid", fgColor="EDEDED"),
    "V": PatternFill("solid", fgColor="EDEDED"),
}
FREI = PatternFill("solid", fgColor="FFFFFF")

duenn = Side(style="thin", color="BFBFBF")
RAHMEN = Border(left=duenn, right=duenn, top=duenn, bottom=duenn)
MITTE = Alignment(horizontal="center", vertical="center", wrap_text=True)
LINKS = Alignment(horizontal="left", vertical="center", wrap_text=True)


def setze(ws, zelle, wert, font=F_NORMAL, fill=None, align=None,
          border=RAHMEN, fmt=None):
    c = ws[zelle]
    c.value = wert
    c.font = font
    if fill:
        c.fill = fill
    c.alignment = align or LINKS
    if border:
        c.border = border
    if fmt:
        c.number_format = fmt
    return c


# --------------------------------------------------------------------------
# Blätter
# --------------------------------------------------------------------------


def blatt_uebersicht(wb):
    ws = wb.create_sheet("Übersicht")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 46

    setze(ws, "A1", "Dienstplan Fitnessstudio — 4-Wochen-Rotation", F_TITEL, border=None)
    setze(ws, "A2", "Rollierender Plan. Nach Woche 4 beginnt wieder Woche 1.",
          F_KLEIN, border=None)

    r = 4
    setze(ws, f"A{r}", "Öffnungszeiten", F_KOPF, BLAU, MITTE)
    setze(ws, f"B{r}", "von", F_KOPF, BLAU, MITTE)
    setze(ws, f"C{r}", "bis", F_KOPF, BLAU, MITTE)
    setze(ws, f"D{r}", "Öffnungsstunden", F_KOPF, BLAU, MITTE)
    r += 1
    erste_oeffnung = r
    for tag in TAGE:
        von, bis = OEFFNUNG[tag]
        setze(ws, f"A{r}", tag, F_FETT)
        setze(ws, f"B{r}", von, F_NORMAL, align=MITTE)
        setze(ws, f"C{r}", bis, F_NORMAL, align=MITTE)
        setze(ws, f"D{r}", (m(bis) - m(von)) / 60, F_NORMAL, align=MITTE,
              fmt='0.0" h"')
        r += 1
    setze(ws, f"A{r}", "Summe Öffnung je Woche", F_FETT, GRAU)
    setze(ws, f"B{r}", "", F_NORMAL, GRAU)
    setze(ws, f"C{r}", "", F_NORMAL, GRAU)
    setze(ws, f"D{r}", f"=SUM(D{erste_oeffnung}:D{r-1})", F_FETT, GRAU, MITTE,
          fmt='0.0" h"')
    r += 2

    setze(ws, f"A{r}", "Team", F_KOPF, BLAU, MITTE)
    setze(ws, f"B{r}", "Vertrag", F_KOPF, BLAU, MITTE)
    setze(ws, f"C{r}", "Std./Woche", F_KOPF, BLAU, MITTE)
    setze(ws, f"D{r}", "Rolle im Plan", F_KOPF, BLAU, MITTE)
    r += 1
    rollen = {
        "VZ 1": "Trägt Früh- bzw. Spätwoche, Bürozeit, Wochenende alle 4 Wochen",
        "VZ 2": "Trägt Früh- bzw. Spätwoche, Bürozeit, Wochenende alle 4 Wochen",
        "TZ 1": "Zwischendienste, eine volle Schicht, Wochenende jede 2. Woche",
        "TZ 2": "Zwischendienste, eine volle Schicht, Wochenende jede 2. Woche",
        "MJ": "Zwei feste Abenddienste je Woche, kein Wochenenddienst",
    }
    for kuerzel, anzeige, vertrag, std in TEAM:
        setze(ws, f"A{r}", anzeige, F_FETT)
        setze(ws, f"B{r}", vertrag, F_NORMAL, align=MITTE)
        setze(ws, f"C{r}", std, F_NORMAL, align=MITTE, fmt='0.0" h"')
        setze(ws, f"D{r}", rollen[kuerzel], F_ZELLE)
        r += 1
    r += 1

    setze(ws, f"A{r}", "Kennzahlen", F_KOPF, BLAU, MITTE)
    setze(ws, f"B{r}", "Wert", F_KOPF, BLAU, MITTE)
    setze(ws, f"C{r}", "", F_KOPF, BLAU, MITTE)
    setze(ws, f"D{r}", "Erläuterung", F_KOPF, BLAU, MITTE)
    r += 1

    schichtstunden = sum(
        tag_stunden(t, plan_von(w, p)[t])
        for w in PLAN for p in KUERZEL for t in TAGE) / 4
    kennzahlen = [
        ("Öffnungsstunden je Woche", 102.0, '0.0" h"',
         "Mo/Mi/Fr 16 h, Di/Do 16 h, Sa/So 11 h"),
        ("Geplante Arbeitsstunden je Woche", round(schichtstunden, 2), '0.00" h"',
         "Durchschnitt über die vier Wochen, inkl. Büro- und Aufgabenblöcken"),
        ("Vertragsstunden je Woche", sum(s for _, _, _, s in TEAM), '0.0" h"',
         "2 × 40 h + 2 × 20 h + 9 h Minijob"),
        ("Doppelbesetzung abends", 4.5 * 5, '0.0" h"',
         "Zwischendienst an fünf Werktagen zur Hauptlastzeit"),
        ("Minijob-Stunden je Monat", round(9.0 * WOCHEN_JE_MONAT, 2), '0.00" h"',
         "9,0 h/Woche × 13/3 — gesetzlicher Umrechnungsfaktor"),
        ("Minijob-Entgelt je Monat", round(9.0 * WOCHEN_JE_MONAT * MINDESTLOHN, 2),
         '#,##0.00" €"',
         f"bei {MINDESTLOHN:.2f} €/h; Geringfügigkeitsgrenze 2026: "
         f"{MINIJOB_GRENZE:.0f} €"),
    ]
    for label, wert, fmt, erl in kennzahlen:
        setze(ws, f"A{r}", label, F_FETT)
        setze(ws, f"B{r}", wert, F_NORMAL, align=MITTE, fmt=fmt)
        setze(ws, f"C{r}", "", F_NORMAL)
        setze(ws, f"D{r}", erl, F_ZELLE)
        r += 1
    r += 1

    setze(ws, f"A{r}", "Annahmen — bitte prüfen und bei Bedarf anpassen",
          Font(name=ARIAL, size=11, bold=True), border=None)
    r += 1
    annahmen = [
        "Wochenstunden Teilzeit mit je 20 h angesetzt (nicht vorgegeben).",
        "Minijob mit 9,0 h/Woche angesetzt, damit die Geringfügigkeitsgrenze "
        "auch in Monaten mit fünf Abrechnungswochen sicher eingehalten wird.",
        "Mindestbesetzung: eine Person während der gesamten Öffnungszeit, "
        "abends zusätzlich ein Zwischendienst.",
        "Pausen: 30 min ab mehr als 6 h, 60 min beim Wochenend-Tagesdienst. "
        "Pausen sind unbezahlt und in den Stunden bereits abgezogen.",
        "Urlaub, Krankheit und Feiertage sind nicht eingerechnet — dafür ist "
        "der Puffer im Blatt Stundenkonto vorgesehen.",
        "Kurse, Reinigung durch Dienstleister und Buchhaltung sind nicht "
        "abgebildet.",
    ]
    for a in annahmen:
        setze(ws, f"A{r}", "•", F_NORMAL, border=None, align=MITTE)
        ws.merge_cells(f"B{r}:D{r}")
        setze(ws, f"B{r}", a, F_ZELLE, border=None)
        ws.row_dimensions[r].height = 26
        r += 1
    return ws


def blatt_legende(wb):
    ws = wb.create_sheet("Schichtlegende")
    ws.sheet_view.showGridLines = False
    for spalte, breite in zip("ABCDEF", (10, 22, 18, 18, 18, 12)):
        ws.column_dimensions[spalte].width = breite

    setze(ws, "A1", "Schichtlegende", F_TITEL, border=None)
    setze(ws, "A2", "Die Zeiten hängen vom Tag ab, weil das Studio "
                    "unterschiedlich lange geöffnet hat.", F_KLEIN, border=None)

    kopf = ["Code", "Schicht", "Mo / Mi / Fr", "Di / Do", "Sa / So", "Arbeitszeit"]
    for i, k in enumerate(kopf):
        setze(ws, f"{get_column_letter(i+1)}4", k, F_KOPF, BLAU, MITTE)

    zeilen = [
        ("F", "Frühdienst", ("F", "A"), ("F", "B"), None, 8.0),
        ("S", "Spätdienst", ("S", "A"), ("S", "B"), None, 8.0),
        ("Z", "Zwischendienst", ("Z", "A"), ("Z", "B"), None, 4.5),
        ("T", "Tagesdienst", None, None, ("T", "C"), 10.0),
    ]
    r = 5
    for code, name, a, b, c, az in zeilen:
        setze(ws, f"A{r}", code, F_FETT, FARBE[code], MITTE)
        setze(ws, f"B{r}", name, F_NORMAL)
        for spalte, schl in zip("CDE", (a, b, c)):
            if schl:
                beginn, ende, pause, _ = SCHICHT[schl]
                txt = f"{beginn}–{ende}  ({pause:.1f} h Pause)".replace(".", ",")
            else:
                txt = "—"
            setze(ws, f"{spalte}{r}", txt, F_ZELLE, align=MITTE)
        setze(ws, f"F{r}", az, F_FETT, align=MITTE, fmt='0.0" h"')
        r += 1

    r += 1
    setze(ws, f"A{r}", "Zusatzblöcke ohne Thekendienst", F_FETT, border=None)
    r += 1
    for i, k in enumerate(["Code", "Block", "Lage", "", "", "Dauer"]):
        setze(ws, f"{get_column_letter(i+1)}{r}", k, F_KOPF, BLAU, MITTE)
    r += 1
    zusatz = [
        ("B", "Bürozeit", "direkt im Anschluss an den Frühdienst bzw. vor dem "
                          "Spätdienst", 1.0),
        ("P", "Studioaufgaben", "unmittelbar vor dem Zwischendienst — "
                                "Probetraining, Gerätecheck", 1.5),
        ("V", "Verwaltung", "großer Büroblock, danach 30 min Pause, dann "
                            "Zwischendienst", 3.5),
    ]
    for code, name, lage, dauer in zusatz:
        setze(ws, f"A{r}", code, F_FETT, FARBE[code], MITTE)
        setze(ws, f"B{r}", name, F_NORMAL)
        ws.merge_cells(f"C{r}:E{r}")
        setze(ws, f"C{r}", lage, F_ZELLE)
        setze(ws, f"F{r}", dauer, F_FETT, align=MITTE, fmt='0.0" h"')
        ws.row_dimensions[r].height = 28
        r += 1

    r += 2
    setze(ws, f"A{r}", "Regeln, die der Plan einhält",
          Font(name=ARIAL, size=11, bold=True), border=None)
    r += 1
    regeln = [
        "Ruhezeit: mindestens 11 Stunden zwischen zwei Diensten (§ 5 ArbZG). "
        "Deshalb folgt auf einen Spätdienst nie ein Frühdienst am nächsten Tag.",
        "Höchstarbeitszeit: höchstens 10 Stunden am Tag (§ 3 ArbZG); der "
        "Wochenend-Tagesdienst nutzt diesen Rahmen aus und wird über den "
        "Sechs-Monats-Schnitt auf 8 Stunden ausgeglichen.",
        "Pausen: 30 Minuten bei mehr als 6 Stunden, 45 Minuten bei mehr als "
        "9 Stunden (§ 4 ArbZG).",
        "Nachtarbeit: der Spätdienst an Di/Do endet um 24:00 und liegt damit "
        "nur eine Stunde in der Nachtzeit — keine Nachtarbeit im Sinne des "
        "§ 2 Abs. 4 ArbZG.",
        "Sonntagsarbeit ist im Sportbetrieb zulässig (§ 10 Abs. 1 Nr. 4 ArbZG); "
        "der Ersatzruhetag liegt in derselben oder der folgenden Woche.",
        "Jede Person hat in vier Wochen mindestens zwei vollständig freie "
        "Wochenenden.",
    ]
    for reg in regeln:
        setze(ws, f"A{r}", "•", F_NORMAL, border=None, align=MITTE)
        ws.merge_cells(f"B{r}:F{r}")
        setze(ws, f"B{r}", reg, F_ZELLE, border=None)
        ws.row_dimensions[r].height = 30
        r += 1
    return ws


def blatt_woche(wb, woche):
    ws = wb.create_sheet(f"Woche {woche}")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 11
    for i in range(len(TAGE)):
        ws.column_dimensions[get_column_letter(3 + i)].width = 16
    ws.column_dimensions[get_column_letter(3 + len(TAGE))].width = 12

    setze(ws, "A1", WOCHEN_TITEL[woche], F_TITEL, border=None)
    setze(ws, "A2", "Zeiten sind Anwesenheitszeiten; die Pause ist in den "
                    "Stunden bereits abgezogen.", F_KLEIN, border=None)

    kopf_zeile = 4
    setze(ws, f"A{kopf_zeile}", "Mitarbeiter/in", F_KOPF, BLAU, MITTE)
    setze(ws, f"B{kopf_zeile}", "Vertrag", F_KOPF, BLAU, MITTE)
    for i, tag in enumerate(TAGE):
        von, bis = OEFFNUNG[tag]
        setze(ws, f"{get_column_letter(3+i)}{kopf_zeile}",
              f"{tag}\n{von}–{bis}", F_KOPF, BLAU, MITTE)
    summe_spalte = get_column_letter(3 + len(TAGE))
    setze(ws, f"{summe_spalte}{kopf_zeile}", "Ist-Std.", F_KOPF, BLAU, MITTE)
    ws.row_dimensions[kopf_zeile].height = 32

    erste = kopf_zeile + 1
    for j, (kuerzel, anzeige, vertrag, _std) in enumerate(TEAM):
        r = erste + j
        setze(ws, f"A{r}", anzeige, F_FETT, GRAU)
        setze(ws, f"B{r}", vertrag, F_ZELLE, GRAU, MITTE)
        for i, tag in enumerate(TAGE):
            codes = plan_von(woche, kuerzel)[tag]
            zelle = f"{get_column_letter(3+i)}{r}"
            if codes:
                leit = next((c for c in codes if c in ("F", "S", "Z", "T")), codes[0])
                setze(ws, zelle, tag_text(tag, codes), F_ZELLE, FARBE[leit], MITTE)
            else:
                setze(ws, zelle, "frei", Font(name=ARIAL, size=9, color="A6A6A6"),
                      FREI, MITTE)
        # Ist-Stunden aus der Stundentabelle weiter unten
        ws.row_dimensions[r].height = 40
    letzte = erste + len(TEAM) - 1

    # Stundentabelle — Zahlen, auf die sich alle Summenformeln beziehen
    st_kopf = letzte + 2
    setze(ws, f"A{st_kopf}", "Arbeitsstunden je Tag", F_KOPF, BLAU, MITTE)
    setze(ws, f"B{st_kopf}", "Soll", F_KOPF, BLAU, MITTE)
    for i, tag in enumerate(TAGE):
        setze(ws, f"{get_column_letter(3+i)}{st_kopf}", tag, F_KOPF, BLAU, MITTE)
    setze(ws, f"{summe_spalte}{st_kopf}", "Summe", F_KOPF, BLAU, MITTE)

    st_erste = st_kopf + 1
    for j, (kuerzel, anzeige, _vertrag, soll) in enumerate(TEAM):
        r = st_erste + j
        setze(ws, f"A{r}", anzeige, F_FETT, GRAU)
        setze(ws, f"B{r}", soll, F_ZELLE, GRAU, MITTE, fmt='0.0" h"')
        for i, tag in enumerate(TAGE):
            std = tag_stunden(tag, plan_von(woche, kuerzel)[tag])
            setze(ws, f"{get_column_letter(3+i)}{r}", std if std else None,
                  F_NORMAL, align=MITTE, fmt='0.00;;"–"')
        setze(ws, f"{summe_spalte}{r}",
              f"=SUM(C{r}:{get_column_letter(2+len(TAGE))}{r})",
              F_FETT, align=MITTE, fmt='0.00')
        # Verweis aus der Plantabelle nach oben
        setze(ws, f"{summe_spalte}{erste + j}", f"={summe_spalte}{r}",
              F_FETT, GRAU, MITTE, fmt='0.00')
    st_letzte = st_erste + len(TEAM) - 1

    r = st_letzte + 1
    setze(ws, f"A{r}", "Summe Studio", F_FETT, GRAU)
    setze(ws, f"B{r}", "", F_NORMAL, GRAU)
    for i in range(len(TAGE)):
        sp = get_column_letter(3 + i)
        setze(ws, f"{sp}{r}", f"=SUM({sp}{st_erste}:{sp}{st_letzte})",
              F_FETT, GRAU, MITTE, fmt='0.00')
    setze(ws, f"{summe_spalte}{r}",
          f"=SUM({summe_spalte}{st_erste}:{summe_spalte}{st_letzte})",
          F_FETT, GRAU, MITTE, fmt='0.00')

    r += 1
    setze(ws, f"A{r}", "Besetzte Personen je Tag", F_FETT)
    setze(ws, f"B{r}", "", F_NORMAL)
    for i, tag in enumerate(TAGE):
        anzahl = sum(
            1 for kuerzel in KUERZEL
            if any(c in ("F", "S", "Z", "T")
                   for c in plan_von(woche, kuerzel)[tag]))
        setze(ws, f"{get_column_letter(3+i)}{r}", anzahl, F_NORMAL, align=MITTE)
    setze(ws, f"{summe_spalte}{r}", "", F_NORMAL)

    ws.freeze_panes = f"C{kopf_zeile+1}"
    return ws


def blatt_stundenkonto(wb):
    ws = wb.create_sheet("Stundenkonto")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 26
    for spalte in "BCDEFGHI":
        ws.column_dimensions[spalte].width = 14
    ws.column_dimensions["I"].width = 40

    setze(ws, "A1", "Stundenkonto — vier Wochen", F_TITEL, border=None)
    setze(ws, "A2", "Alle Werte holen sich die Zahlen aus den Wochenblättern. "
                    "Ändert sich dort eine Schicht, ändert sich hier die Summe.",
          F_KLEIN, border=None)

    kopf = ["Mitarbeiter/in", "Woche 1", "Woche 2", "Woche 3", "Woche 4",
            "Ist gesamt", "Soll gesamt", "Konto", "Hinweis"]
    for i, k in enumerate(kopf):
        setze(ws, f"{get_column_letter(i+1)}4", k, F_KOPF, BLAU, MITTE)

    # Zeilenlage der Stundentabelle auf den Wochenblättern
    st_erste = 4 + len(TEAM) + 2 + 1
    summe_spalte = get_column_letter(3 + len(TAGE))

    hinweise = {
        "VZ 1": "Vier Wochen genau auf Vertragssoll.",
        "VZ 2": "Vier Wochen genau auf Vertragssoll.",
        "TZ 1": "+0,5 h wandern ins Gleitzeitkonto.",
        "TZ 2": "+0,5 h wandern ins Gleitzeitkonto.",
        "MJ": "36 h je vier Wochen; 39,0 h im Monatsschnitt.",
    }

    r = 5
    for j, (kuerzel, anzeige, _vertrag, soll) in enumerate(TEAM):
        setze(ws, f"A{r}", anzeige, F_FETT, GRAU)
        for w in (1, 2, 3, 4):
            sp = get_column_letter(1 + w)
            setze(ws, f"{sp}{r}", f"='Woche {w}'!{summe_spalte}{st_erste + j}",
                  F_NORMAL, align=MITTE, fmt='0.00')
        setze(ws, f"F{r}", f"=SUM(B{r}:E{r})", F_FETT, align=MITTE, fmt='0.00')
        setze(ws, f"G{r}", soll * 4, F_NORMAL, align=MITTE, fmt='0.00')
        setze(ws, f"H{r}", f"=F{r}-G{r}", F_FETT, align=MITTE,
              fmt='+0.00;-0.00;0.00')
        setze(ws, f"I{r}", hinweise[kuerzel], F_ZELLE)
        r += 1

    setze(ws, f"A{r}", "Summe", F_FETT, GRAU)
    for sp in "BCDEFGH":
        setze(ws, f"{sp}{r}", f"=SUM({sp}5:{sp}{r-1})", F_FETT, GRAU, MITTE,
              fmt='0.00')
    setze(ws, f"I{r}", "", F_NORMAL, GRAU)

    r += 2
    setze(ws, f"A{r}", "Minijob-Kontrolle", Font(name=ARIAL, size=11, bold=True),
          border=None)
    r += 1
    mj_zeile = 5 + KUERZEL.index("MJ")
    kontrolle = [
        ("Stunden je Woche (Schnitt)", f"=F{mj_zeile}/4", '0.00" h"',
         "Ist gesamt geteilt durch vier Wochen"),
        ("Umrechnungsfaktor Woche → Monat", WOCHEN_JE_MONAT, "0.000",
         "13/3, gesetzlicher Faktor"),
        ("Stunden je Monat", f"=B{r}*B{r+1}", '0.00" h"',
         "Grundlage der Entgeltrechnung"),
        ("Stundenlohn", MINDESTLOHN, '#,##0.00" €"',
         "gesetzlicher Mindestlohn ab 01.01.2026"),
        ("Entgelt je Monat", f"=B{r+2}*B{r+3}", '#,##0.00" €"',
         "muss unter der Geringfügigkeitsgrenze bleiben"),
        ("Geringfügigkeitsgrenze 2026", MINIJOB_GRENZE, '#,##0.00" €"',
         "603 € entsprechen 43,38 h bei 13,90 €/h"),
        ("Abstand zur Grenze", f"=B{r+5}-B{r+4}", '#,##0.00" €"',
         "positiver Wert = Puffer"),
    ]
    for label, wert, fmt, erl in kontrolle:
        setze(ws, f"A{r}", label, F_FETT)
        setze(ws, f"B{r}", wert, F_NORMAL, align=MITTE, fmt=fmt)
        ws.merge_cells(f"C{r}:I{r}")
        setze(ws, f"C{r}", erl, F_ZELLE)
        r += 1
    return ws


def blatt_besetzung(wb):
    ws = wb.create_sheet("Besetzung")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 12
    for i in range(len(TAGE)):
        ws.column_dimensions[get_column_letter(2 + i)].width = 9

    setze(ws, "A1", "Besetzungsstärke im Tagesverlauf", F_TITEL, border=None)
    setze(ws, "A2", "Anzahl Personen im Thekendienst je halber Stunde. "
                    "Das Raster ist in allen vier Wochen identisch — die "
                    "Rotation tauscht nur, wer die Schicht übernimmt.",
          F_KLEIN, border=None)

    setze(ws, "A4", "Uhrzeit", F_KOPF, BLAU, MITTE)
    for i, tag in enumerate(TAGE):
        setze(ws, f"{get_column_letter(2+i)}4", tag, F_KOPF, BLAU, MITTE)

    stufen = {
        0: (PatternFill("solid", fgColor="FFFFFF"), "A6A6A6"),
        1: (PatternFill("solid", fgColor="DCE9F7"), "1F3864"),
        2: (PatternFill("solid", fgColor="9DC3E6"), "1F3864"),
        3: (PatternFill("solid", fgColor="5B9BD5"), "FFFFFF"),
    }

    r = 5
    for minute in range(m("06:00"), m("24:00"), 30):
        setze(ws, f"A{r}", f"{hhmm(minute)}–{hhmm(minute+30)}", F_ZELLE,
              GRAU, MITTE)
        for i, tag in enumerate(TAGE):
            anzahl = 0
            for kuerzel in KUERZEL:
                for code, b, e, _az in bloecke(tag, plan_von(1, kuerzel)[tag]):
                    if code in ("F", "S", "Z", "T") and b <= minute < e:
                        anzahl += 1
            fill, farbe = stufen[min(anzahl, 3)]
            setze(ws, f"{get_column_letter(2+i)}{r}",
                  anzahl if anzahl else None,
                  Font(name=ARIAL, size=9, bold=True, color=farbe),
                  fill, MITTE, fmt='0;;""')
        r += 1

    r += 1
    setze(ws, f"A{r}", "Leer = geschlossen · 1 = Grundbesetzung · "
                       "2 = Doppelbesetzung zur Hauptlastzeit", F_KLEIN,
          border=None)
    ws.freeze_panes = "B5"
    return ws


# --------------------------------------------------------------------------


def main():
    fehler = pruefe()
    if fehler:
        print("PRÜFUNG FEHLGESCHLAGEN:")
        for f in fehler:
            print("  -", f)
        raise SystemExit(1)
    print("Prüfung bestanden: Besetzung, Ruhezeiten, Höchstarbeitszeit, "
          "Minijob-Grenze.")

    wb = Workbook()
    wb.remove(wb.active)
    blatt_uebersicht(wb)
    for woche in (1, 2, 3, 4):
        blatt_woche(wb, woche)
    blatt_stundenkonto(wb)
    blatt_besetzung(wb)
    blatt_legende(wb)

    ziel = "dienstplan/Dienstplan_Fitnessstudio_4-Wochen.xlsx"
    wb.save(ziel)
    print("Geschrieben:", ziel)

    for woche in PLAN:
        gesamt = sum(tag_stunden(t, plan_von(woche, p)[t])
                     for p in KUERZEL for t in TAGE)
        print(f"  Woche {woche}: {gesamt:.2f} h")
    for p in KUERZEL:
        gesamt = sum(tag_stunden(t, plan_von(w, p)[t])
                     for w in PLAN for t in TAGE)
        print(f"  {p}: {gesamt:.2f} h in vier Wochen")


if __name__ == "__main__":
    main()
