#!/usr/bin/env python3
"""Baut den KDP-Umschlag (Taschenbuch) für „Kopf schlägt Kalorien".

    python3 kopf/build/build_cover.py

Der Innenteil muss vorher gebaut sein — die Rückenbreite ergibt sich aus der
Seitenzahl. Maße, Anschnitt und Barcodefeld kommen aus buch/build/build_cover.py,
damit alle Titel dieselben KDP-Regeln einhalten.

Kein Band der Stoffwechsel-Reset-Reihe, deshalb eigene Bildsprache: statt der
Lebensmittelauslage eine Wippe, auf der ein Kopf einen Kalorienblock aufwiegt.
Gezeichnet wird nur in Vollton — keine Verläufe, keine Transparenz. Die
Druckfassung entsteht trotzdem über cover_flach.py, wie bei den anderen Bänden.
"""

import math
import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
KOPF = WURZEL / "kopf"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM, BESCHNITT_MM,  # noqa: E402
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN,
                         barcodefeld_freistellen, block_schreiben,
                         groesse_einpassen, klappentext_laden, schriften_laden,
                         seitenzahl, umbrechen, vorschau)
from cover_flach import flach_rechnen  # noqa: E402

FARBEN = {
    "grund": HexColor("#1E2A38"),       # tiefes Nachtblau
    "text": HexColor("#F4F1EA"),        # warmes Papierweiß
    "text_leise": HexColor("#B9C2CC"),
    "akzent": HexColor("#F2A93B"),      # Bernstein
    "linie": HexColor("#5B6B7D"),
}

HINWEIS = ("Kein medizinischer Ratgeber und kein Ersatz für ärztliche oder "
           "psychotherapeutische Beratung — bitte die Hinweise im Buch "
           "beachten.")


def wippe(c, mitte_x, boden_y, breite):
    """Die Wippe: links der schwere Kopf unten, rechts der leichte Block oben."""
    neigung = math.radians(11)
    halb = breite * 0.42
    drehpunkt_y = boden_y + breite * 0.16

    # Dreieckiger Bock
    c.setFillColor(FARBEN["linie"])
    p = c.beginPath()
    p.moveTo(mitte_x - breite * 0.075, boden_y)
    p.lineTo(mitte_x + breite * 0.075, boden_y)
    p.lineTo(mitte_x, drehpunkt_y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(FARBEN["linie"])
    c.setLineWidth(1.4)
    c.line(mitte_x - breite * 0.30, boden_y, mitte_x + breite * 0.30, boden_y)

    # Balken, links abgesenkt
    dx, dy = halb * math.cos(neigung), halb * math.sin(neigung)
    links = (mitte_x - dx, drehpunkt_y - dy)
    rechts = (mitte_x + dx, drehpunkt_y + dy)
    c.setStrokeColor(FARBEN["text"])
    c.setLineWidth(5)
    c.setLineCap(1)
    c.line(*links, *rechts)

    # Lot auf den Balken, für Kopf und Block
    nx, ny = -math.sin(neigung), math.cos(neigung)

    # Kopf: Profil in Bernstein, Blick zur Waagenmitte, steht links auf dem
    # Balken. Gezeichnet in einer Einheit von Kopfhöhe 1, Halsansatz bei 0.
    s = breite * 0.30
    c.saveState()
    c.translate(links[0] + dx * 0.24 + nx * 2, links[1] + dy * 0.24 + ny * 2)
    c.rotate(math.degrees(neigung))
    c.scale(s, s)
    p = c.beginPath()
    p.moveTo(-0.12, 0.0)
    p.curveTo(-0.13, 0.12, -0.30, 0.22, -0.32, 0.46)
    p.curveTo(-0.35, 0.80, -0.10, 1.00, 0.10, 1.00)
    p.curveTo(0.30, 1.00, 0.40, 0.86, 0.40, 0.70)
    p.lineTo(0.47, 0.56)
    p.lineTo(0.41, 0.52)
    p.curveTo(0.43, 0.46, 0.40, 0.44, 0.41, 0.40)
    p.curveTo(0.42, 0.34, 0.38, 0.30, 0.30, 0.30)
    p.curveTo(0.24, 0.30, 0.20, 0.22, 0.18, 0.12)
    p.lineTo(0.18, 0.0)
    p.close()
    c.setFillColor(FARBEN["akzent"])
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()

    # Kalorienblock rechts, gedreht mit dem Balken
    bb, bh = breite * 0.17, breite * 0.11
    c.saveState()
    c.translate(rechts[0] - dx * 0.22 + nx * 3, rechts[1] - dy * 0.22 + ny * 3)
    c.rotate(math.degrees(neigung))
    c.setFillColor(FARBEN["text"])
    c.roundRect(-bb / 2, 0, bb, bh, 3, stroke=0, fill=1)
    c.setFillColor(FARBEN["grund"])
    c.setFont("Sans-Bold", bh * 0.42)
    c.drawCentredString(0, bh * 0.33, "kcal")
    c.restoreState()


def vorderseite(c, x, y, breite, hoehe, cfg):
    rand = breite * 0.10

    wippe(c, x + breite / 2, y + hoehe * 0.62, breite * 0.78)

    titel_groesse, titel_zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", breite - 2 * rand, maximal=44, minimal=24)
    zeilenhoehe = titel_groesse * 1.1
    titel_y = y + hoehe * 0.47
    c.setFillColor(FARBEN["text"])
    for i, zeile in enumerate(titel_zeilen):
        c.setFont("Sans-Bold", titel_groesse)
        c.drawCentredString(x + breite / 2, titel_y - i * zeilenhoehe, zeile)
    unten = titel_y - (len(titel_zeilen) - 1) * zeilenhoehe

    c.setStrokeColor(FARBEN["akzent"])
    c.setLineWidth(1.8)
    c.line(x + breite * 0.38, unten - 20, x + breite * 0.62, unten - 20)

    # Von Hand umbrochen: Automatisch bliebe „Plan" allein in der letzten Zeile.
    c.setFillColor(FARBEN["text_leise"])
    c.setFont("Sans", 15)
    for i, zeile in enumerate(("Warum Diäten am Mindset scheitern",
                               "und nicht am Plan")):
        c.drawCentredString(x + breite / 2, unten - 46 - i * 20, zeile)

    c.setFillColor(FARBEN["akzent"])
    c.setFont("Sans-Bold", 18)
    c.drawCentredString(x + breite / 2, y + hoehe * 0.09, cfg["autor"])


def rueckseite(c, x, y, breite, hoehe, kopf, absaetze, punkte):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    _, fy, _, fh = barcodefeld_freistellen(c, x, y, breite)
    hinweis_zeilen = umbrechen(c, HINWEIS, "Serif", 7.5, textbreite)
    hinweis_y = fy + fh + BARCODE_LUFT_MM * mm + 2 + (len(hinweis_zeilen) - 1) * 10
    block_schreiben(c, HINWEIS, x + rand, hinweis_y, textbreite, "Serif", 7.5,
                    10, FARBEN["text_leise"])

    cursor = y + hoehe - rand * 1.1
    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", 18, 23,
                                 FARBEN["akzent"])
        cursor -= 14
    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", 12, 16.5, FARBEN["text"])
        cursor -= 8
    cursor -= 4
    for punkt in punkte:
        c.setFillColor(FARBEN["akzent"])
        c.setFont("Sans-Bold", 11.5)
        c.drawString(x + rand, cursor, "•")
        for zeile in umbrechen(c, punkt, "Serif", 11.5, textbreite - 14):
            c.setFillColor(FARBEN["text"])
            c.setFont("Serif", 11.5)
            c.drawString(x + rand + 14, cursor, zeile)
            cursor -= 15.5
        cursor -= 3

    if cursor < hinweis_y + 24:
        raise SystemExit("Rückseitentext reicht bis an den Hinweis — "
                         "Klappentext kürzen.")


def cover_bauen(cfg, seiten, ziel):
    schriften_laden()
    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    anschnitt = BESCHNITT_MM * mm
    ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm
    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")
    c.setFillColor(FARBEN["grund"])
    c.rect(0, 0, gesamt_b, gesamt_h, stroke=0, fill=1)

    kopf, absaetze, punkte = klappentext_laden(KOPF / "cover" / "klappentext.md")
    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, kopf, absaetze, punkte)

    mit_ruecken_text = seiten >= RUECKENTEXT_AB_SEITEN
    if mit_ruecken_text:
        c.saveState()
        c.translate(anschnitt + trim_b + ruecken_b / 2, gesamt_h / 2)
        c.rotate(-90)
        groesse = min(11, ruecken_b / mm * 0.55 * mm)
        c.setFillColor(FARBEN["text"])
        c.setFont("Sans-Bold", groesse)
        c.drawCentredString(0, -groesse * 0.35,
                            f"{cfg['titel']}   ·   {cfg['autor']}")
        c.restoreState()

    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt, trim_b, trim_h, cfg)
    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm, "ruecken_text": mit_ruecken_text}


def main():
    cfg = yaml.safe_load((KOPF / "kopf.yaml").read_text(encoding="utf-8"))
    out = KOPF / "out"
    seiten = seitenzahl(out / f"{cfg['slug']}-druck.pdf")
    ziel = out / "cover.pdf"
    masse = cover_bauen(cfg, seiten, ziel)
    druck = flach_rechnen(ziel)
    png = vorschau(ziel, out / "cover-vorschau.png")

    b, h = masse["gesamt_mm"]
    print(f"Taschenbuch — Innenteil: {seiten} Seiten")
    print(f"Rückenbreite: {masse['ruecken_mm']:.2f} mm"
          f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
    print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
          f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {BESCHNITT_MM} mm Anschnitt")
    print(f"  → {druck['ziel'].relative_to(WURZEL)}  (zu KDP hochladen)")
    print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
