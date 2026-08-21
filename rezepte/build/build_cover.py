#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für Band 3 (Rezeptbuch).

    python3 rezepte/build/build_cover.py

Gleiche Illustrationssprache und Palette wie Band 1 und 2, eigene Komposition
und ein Aufdruck „REZEPTBUCH", damit die drei Bände unterscheidbar bleiben.

Der Innenteil muss vorher gebaut sein — die Rückenbreite ergibt sich aus der
Seitenzahl.
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import illustration as ill  # noqa: E402
from build_cover import (AUSLAGE_HOEHE, BESCHNITT_MM,  # noqa: E402
                         BUCHDECKE_MM, HARDCOVER_MIN_SEITEN, WRAP_MM,
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN,
                         auslage_oben, block_schreiben, groesse_einpassen,
                         klappentext_laden, rueckseite, rueckseite_schiefer,
                         ruecken_schiefer, schriften_laden, seitenzahl,
                         titelbild_melden, titelbild_suchen, titelbild_zeichnen,
                         vorderseite_schiefer, vorschau)

# Dritte Komposition — Kräuter und Gewürzträger stehen im Vordergrund,
# passend zum Thema Kochen ohne Salz.
BAND_OBEN_REZEPTE = [
    (ill.kraeuterzweig, 0.07, 0.50, 0.17, -14),
    (ill.paprika, 0.22, 0.62, 0.20, 5),
    (ill.zitrone, 0.38, 0.38, 0.17, 0),
    (ill.brokkoli, 0.54, 0.62, 0.22, 0),
    (ill.tomate, 0.71, 0.38, 0.18, 0),
    (ill.kraeuterzweig, 0.86, 0.60, 0.17, 10),
    (ill.heidelbeeren, 0.96, 0.36, 0.14, 0),
]

BAND_UNTEN_REZEPTE = [
    (ill.pilz, 0.10, 0.34, 0.16, 0),
    (ill.spargel, 0.25, 0.54, 0.18, -5),
    (ill.gurkenscheibe, 0.42, 0.32, 0.15, 0),
    (ill.avocado, 0.58, 0.56, 0.19, 7),
    (ill.erdbeere, 0.75, 0.30, 0.15, -6),
    (ill.kraeuterzweig, 0.90, 0.50, 0.16, 12),
]


def rezeptzahl():
    """Zählt die Rezepte in den Quelldateien.

    Nicht fest eintragen: Die Zahl steht auch im Untertitel und auf dem
    Cover, und genau da ist sie schon einmal auseinandergelaufen.
    """
    return sum(
        len(yaml.safe_load(p.read_text(encoding="utf-8")).get("rezepte", []))
        for p in sorted((WURZEL / "rezepte" / "rezepte").glob("*.yaml")))


def vorderseite(c, x, y, breite, hoehe, cfg, titelbild=None):
    rand = breite * 0.09

    if titelbild:
        titelbild_zeichnen(c, titelbild, x, y + hoehe * 0.62,
                           breite, hoehe * 0.38)
    else:
        ill.komposition_zeichnen(c, BAND_OBEN_REZEPTE,
                                 x, y + hoehe * 0.70, breite, hoehe * 0.24)

    # Kennzeichnung des Bandes
    kennung_h = 22
    kennung_y = y + hoehe * 0.655
    c.setFillColor(ill.PALETTE["blatt"])
    c.rect(x + rand, kennung_y, breite - 2 * rand, kennung_h, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Sans-Bold", 11)
    c.drawCentredString(x + breite / 2, kennung_y + kennung_h * 0.32,
                        "REZEPTBUCH   ·   73 GERICHTE")

    titel_groesse, titel_zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", breite - 2 * rand,
        maximal=42, minimal=20)
    zeilenhoehe = titel_groesse * 1.13
    mitte_y = y + hoehe * 0.545
    c.setFillColor(ill.PALETTE["blatt"])
    for i, zeile in enumerate(titel_zeilen):
        c.setFont("Sans-Bold", titel_groesse)
        c.drawCentredString(x + breite / 2, mitte_y - i * zeilenhoehe, zeile)
    unten = mitte_y - len(titel_zeilen) * zeilenhoehe

    block_schreiben(c, cfg["untertitel"], x + rand, unten - 22,
                    breite - 2 * rand, "Sans", 13, 18,
                    HexColor("#3E4A3A"), zentriert=True)

    c.setFillColor(ill.PALETTE["blatt_tief"])
    c.setFont("Sans-Bold", 17)
    c.drawCentredString(x + breite / 2, y + hoehe * 0.295, cfg["autor"])

    if not titelbild:
        ill.komposition_zeichnen(c, BAND_UNTEN_REZEPTE,
                                 x, y + hoehe * 0.075, breite, hoehe * 0.18)


def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    c.saveState()
    c.setFillColor(ill.PALETTE["blatt"])
    c.rect(x, y, breite, hoehe, stroke=0, fill=1)
    if mit_text:
        c.translate(x + breite / 2, y + hoehe / 2)
        c.rotate(-90)
        groesse = min(11, breite * 0.5)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Sans-Bold", groesse)
        c.drawCentredString(
            0, -groesse * 0.35,
            f"{cfg['titel']} — REZEPTBUCH   ·   {cfg['autor']}")
    c.restoreState()


# Die Rückseite im hellen Stil kommt aus buch/build/build_cover.py. Hier stand
# lange eine Kopie — mit der alten Hinweisformel und ohne die Weißfläche fürs
# Barcodefeld. Band 3 setzt zwar auf „schiefer", die Kopie wäre also nie
# gelaufen; genau deshalb wäre sie beim nächsten Stilwechsel als stiller
# Rückschritt aufgetaucht.


def cover_bauen(cfg, seiten, klappentext_pfad, ziel, *, hardcover=False):
    """Umschlag Band 3, Taschenbuch oder Hardcover.

    Die Hardcover-Geometrie ist dieselbe wie bei Band 1 und wird von dort
    importiert: Umschlagrand statt Anschnitt, Buchdecke statt Buchblock im
    Rücken. Die Trimmgröße dagegen ist eine andere als beim Taschenbuch —
    8,25 x 11 statt 8 x 10 Zoll, weil KDP 8 x 10 nicht als Hardcover führt.
    """
    schriften_laden()
    # Hardcover hat ein eigenes Trimmformat: KDP führt 8 x 10 Zoll nur als
    # Taschenbuch. Ohne diese Unterscheidung meldet der Upload „erwartete
    # Covergröße 18.442 x 12.417" gegen eine Datei mit 17.942 x 11.417.
    sf = cfg["hardcover_seitenformat"] if hardcover else cfg["seitenformat"]
    trim_b = sf["breite_mm"] * mm
    trim_h = sf["hoehe_mm"] * mm
    if hardcover:
        anschnitt = WRAP_MM * mm
        ruecken_b = (seiten * RUECKEN_PRO_SEITE_MM + BUCHDECKE_MM) * mm
    else:
        anschnitt = BESCHNITT_MM * mm
        ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    # initialFontName: reportlab schreibt sonst einen Seitenvorspann mit
    # Helvetica in die Ressourcen — eine Schrift ohne Einbettung, die
    # kein Zeichen setzt, aber bei der KDP-Prüfung auffallen kann.
    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Rezeptbuch — Umschlag"
               + (" (Hardcover)" if hardcover else ""))

    stil = cfg.get("cover_stil", "hell")
    ill.grund_setzen("dunkel" if stil == "schiefer" else "hell")
    ill.akzent_setzen(cfg.get("cover_akzent", "blatt"))
    if stil == "schiefer":
        ill.schiefergrund(c, 0, 0, gesamt_b, gesamt_h)
    else:
        c.setFillColor(ill.PALETTE["papier"])
        c.rect(0, 0, gesamt_b, gesamt_h, stroke=0, fill=1)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    titelbild = titelbild_suchen(Path(klappentext_pfad).parent)
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN
    anzahl = rezeptzahl()

    if stil == "schiefer":
        if not titelbild:
            # Andere Wiederholungszahl als Band 1: Dasselbe Bild auf drei
            # Umschlägen wäre im Regal nicht auseinanderzuhalten.
            auslage_oben(c, 0, gesamt_h * (1 - AUSLAGE_HOEHE),
                         gesamt_b, gesamt_h * AUSLAGE_HOEHE,
                         bezug=trim_b, wiederholungen=3)
        rueckseite_schiefer(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
                            kopf, absaetze, punkte,
                            auslage=not titelbild, hardcover=hardcover)
        ruecken_schiefer(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h,
                         cfg, mit_ruecken_text,
                         f"{cfg['titel']} — REZEPTBUCH   ·   {cfg['autor']}")
        vorderseite_schiefer(c, anschnitt + trim_b + ruecken_b, anschnitt,
                             trim_b, trim_h, cfg, titelbild,
                             kennung=f"REZEPTBUCH · {anzahl} GERICHTE",
                             titel_maximal=42, ueberstand=anschnitt)
    else:
        rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
                   kopf, absaetze, punkte, hardcover=hardcover)
        ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
                mit_text=mit_ruecken_text)
        vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                    trim_b, trim_h, cfg, titelbild)

    c.showPage()
    c.save()
    return {
        "gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
        "ruecken_mm": ruecken_b / mm,
        "ruecken_text": mit_ruecken_text,
        "stil": stil,
    }


def main():
    basis = WURZEL / "rezepte"
    cfg = yaml.safe_load((basis / "rezepte.yaml").read_text(encoding="utf-8"))
    klappentext = basis / "cover" / "klappentext.md"

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"

        # Jede Bindeart liest ihre eigene Seitenzahl: Die Innenteile haben
        # verschiedene Formate, und aus der Seitenzahl folgt der Rücken.
        innenteil = (f"{cfg['slug']}-hardcover.pdf" if hardcover
                     else f"{cfg['slug']}.pdf")
        seiten = seitenzahl(basis / "out" / innenteil)

        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue

        ziel = basis / "out" / f"{name}.pdf"
        masse = cover_bauen(cfg, seiten, klappentext, ziel,
                            hardcover=hardcover)
        png = vorschau(ziel, basis / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        rand = WRAP_MM if hardcover else BESCHNITT_MM
        randname = "Umschlagrand um die Buchdecke" if hardcover else "Anschnitt"
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        if not masse["ruecken_text"]:
            print(f"  Hinweis: KDP erlaubt Rückentext erst ab "
                  f"{RUECKENTEXT_AB_SEITEN} Seiten — der Rücken bleibt einfarbig.")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {rand} mm {randname}")
        titelbild_melden(cfg, titelbild_suchen(basis / "cover"))
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
