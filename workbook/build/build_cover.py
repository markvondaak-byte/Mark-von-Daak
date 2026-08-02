#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für Band 2 (Workbook).

    python3 workbook/build/build_cover.py

Nutzt dieselbe Illustrationssprache und Palette wie Band 1, aber eine andere
Komposition und einen deutlichen Aufdruck „WORKBOOK · 12 WOCHEN", damit sich
die beiden Bände im Regal und im Amazon-Vorschaubild nicht verwechseln lassen.

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
from build_cover import (BESCHNITT_MM, BARCODE_H_MM,  # noqa: E402
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN,
                         block_schreiben, groesse_einpassen,
                         klappentext_laden, schriften_laden, seitenzahl,
                         umbrechen, vorschau)

# Komposition für Band 2 — bewusst anders angeordnet als beim Buch.
BAND_OBEN_WORKBOOK = [
    (ill.gurkenscheibe, 0.08, 0.60, 0.15, 0),
    (ill.tomate, 0.24, 0.38, 0.17, 0),
    (ill.brokkoli, 0.40, 0.64, 0.20, 0),
    (ill.zitrone, 0.57, 0.36, 0.16, 0),
    (ill.avocado, 0.73, 0.62, 0.19, -10),
    (ill.spargel, 0.90, 0.40, 0.17, 8),
]

BAND_UNTEN_WORKBOOK = [
    (ill.kraeuterzweig, 0.10, 0.48, 0.16, -10),
    (ill.paprika, 0.27, 0.56, 0.18, 4),
    (ill.heidelbeeren, 0.44, 0.30, 0.14, 0),
    (ill.erdbeere, 0.60, 0.56, 0.15, 6),
    (ill.pilz, 0.76, 0.30, 0.14, 0),
    (ill.kraeuterzweig, 0.91, 0.50, 0.15, 12),
]


def vorderseite(c, x, y, breite, hoehe, cfg):
    rand = breite * 0.09

    ill.komposition_zeichnen(c, BAND_OBEN_WORKBOOK,
                             x, y + hoehe * 0.71, breite, hoehe * 0.22)

    # Kennzeichnung, die Band 2 vom Buch unterscheidet
    kennung_h = 26
    kennung_y = y + hoehe * 0.655
    c.setFillColor(ill.PALETTE["blatt"])
    c.rect(x + rand, kennung_y, breite - 2 * rand, kennung_h, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Sans-Bold", 14)
    c.drawCentredString(x + breite / 2, kennung_y + kennung_h * 0.32,
                        "WORKBOOK   ·   12 WOCHEN   ·   84 TAGE")

    # Titel
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
                    breite - 2 * rand, "Sans", 17, 22,
                    HexColor("#3E4A3A"), zentriert=True)

    c.setFillColor(ill.PALETTE["blatt_tief"])
    c.setFont("Sans-Bold", 17)
    c.drawCentredString(x + breite / 2, y + hoehe * 0.305, cfg["autor"])

    ill.komposition_zeichnen(c, BAND_UNTEN_WORKBOOK,
                             x, y + hoehe * 0.08, breite, hoehe * 0.18)


def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    c.saveState()
    c.setFillColor(ill.PALETTE["blatt"])
    c.rect(x, y, breite, hoehe, stroke=0, fill=1)
    if mit_text:
        c.translate(x + breite / 2, y + hoehe / 2)
        c.rotate(-90)
        groesse = min(12, breite * 0.5)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Sans-Bold", groesse)
        c.drawCentredString(
            0, -groesse * 0.35,
            f"{cfg['titel']} — WORKBOOK   ·   {cfg['autor']}")
    c.restoreState()


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte):
    rand = breite * 0.10
    textbreite = breite - 2 * rand
    cursor = y + hoehe - rand * 1.4

    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", 19, 24,
                                 ill.PALETTE["blatt"])
        cursor -= 16

    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", 11.5, 16, HexColor("#26301F"))
        cursor -= 10

    cursor -= 6
    for punkt in punkte:
        c.setFillColor(ill.PALETTE["blatt_hell"])
        c.setFont("Sans-Bold", 11.5)
        c.drawString(x + rand, cursor, "•")
        c.setFillColor(HexColor("#26301F"))
        for zeile in umbrechen(c, punkt, "Serif", 11, textbreite - 16):
            c.setFont("Serif", 11)
            c.drawString(x + rand + 16, cursor, zeile)
            cursor -= 15
        cursor -= 4

    hinweis_y = y + BARCODE_H_MM * mm + rand * 0.6
    block_schreiben(
        c,
        "„cellRESET“ und „FitLine“ sind Marken der PM-International AG. "
        "Dieses Workbook wird von diesem Unternehmen weder herausgegeben noch "
        "autorisiert. Kein medizinischer Ratgeber — bitte die Hinweise im "
        "Heft beachten.",
        x + rand, hinweis_y, textbreite, "Serif", 7.5, 10, HexColor("#6B7566"))


def cover_bauen(cfg, seiten, klappentext_pfad, ziel):
    schriften_laden()
    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    anschnitt = BESCHNITT_MM * mm
    ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h))
    c.setTitle(f"{cfg['titel']} — {cfg['untertitel']} — Umschlag")
    c.setFillColor(ill.PALETTE["papier"])
    c.rect(0, 0, gesamt_b, gesamt_h, stroke=0, fill=1)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_text=seiten >= RUECKENTEXT_AB_SEITEN)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg)

    c.showPage()
    c.save()
    return {
        "gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
        "ruecken_mm": ruecken_b / mm,
        "ruecken_text": seiten >= RUECKENTEXT_AB_SEITEN,
    }


def main():
    basis = WURZEL / "workbook"
    cfg = yaml.safe_load((basis / "workbook.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(basis / "out" / f"{cfg['slug']}.pdf")

    ziel = basis / "out" / "cover.pdf"
    masse = cover_bauen(cfg, seiten, basis / "cover" / "klappentext.md", ziel)
    png = vorschau(ziel, basis / "out" / "cover-vorschau.png")

    b, h = masse["gesamt_mm"]
    print(f"Innenteil: {seiten} Seiten")
    print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
          f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
    print(f"Umschlag gesamt: {b:.1f} x {h:.1f} mm inkl. {BESCHNITT_MM} mm Anschnitt")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
