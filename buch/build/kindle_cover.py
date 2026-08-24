#!/usr/bin/env python3
"""Erzeugt die Titelbilder für die Kindle-Ausgaben.

    python3 buch/build/kindle_cover.py

Ein Kindle-Buch braucht etwas anderes als ein Taschenbuch: kein aufgeklapptes
PDF mit Rückseite, Rücken und Anschnitt, sondern ein einzelnes Bild der
Vorderseite. Amazon verlangt JPEG oder TIFF, mindestens 1000 Pixel an der
langen Kante, und empfiehlt 1600 x 2560 Pixel — Seitenverhältnis 1,6.

Das ist nicht das Verhältnis der gedruckten Bände (6 x 9 Zoll sind 1,5,
8 x 10 Zoll sind 1,25). Deshalb wird die Vorderseite hier neu gesetzt statt
aus dem Umschlag-PDF ausgeschnitten: Beim Ausschneiden müsste man oben und
unten Fläche wegnehmen und würde die Lebensmittelauslage anschneiden.

Gezeichnet wird mit denselben Funktionen wie der gedruckte Umschlag, nur auf
eine andere Leinwand. Damit bleiben Farbwelt, Bandkennung und Schriftbild
identisch — im Amazon-Katalog stehen Taschenbuch und Kindle-Ausgabe
nebeneinander und müssen als dasselbe Buch erkennbar sein.
"""

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

BREITE_PX, HOEHE_PX = 1600, 2560     # Amazons Empfehlung
JPEG_QUALITAET = 92

BAENDE = [
    ("Band 1", "buch/buch.yaml", "buch/out/kindle-cover.jpg",
     "DAS BUCH · 4 PHASEN", "buch/cover"),
    ("Band 2", "workbook/workbook.yaml", "workbook/out/kindle-cover.jpg",
     "WORKBOOK · 12 WOCHEN", "workbook/cover"),
    ("Band 3", "rezepte/rezepte.yaml", "rezepte/out/kindle-cover.jpg",
     "REZEPTBUCH · 73 GERICHTE", "rezepte/cover"),
    ("Darm", "darm/darm.yaml", "darm/out/kindle-cover.jpg",
     "DARMGESUNDHEIT · 8 WOCHEN", "darm/cover"),
]


def titelbild_bauen(cfg, ziel, kennung, cover_verzeichnis,
                    breite_px=BREITE_PX, hoehe_px=HOEHE_PX):
    import io

    import fitz
    import yaml  # noqa: F401  (nur damit der Import früh scheitert)
    from PIL import Image
    from reportlab.pdfgen import canvas

    import build_cover as bc
    import illustration as ill

    bc.schriften_laden()
    ill.grund_setzen("dunkel" if cfg.get("cover_stil") == "schiefer" else "hell")
    ill.akzent_setzen(cfg.get("cover_akzent", "blatt"))

    # Die Leinwand bekommt die echte Buchbreite in Punkt, die Höhe ergibt sich
    # aus dem geforderten Verhältnis 1,6. Das ist wichtig, weil die Schrift-
    # größen in build_cover.py absolute Punktwerte sind: Auf einer beliebig
    # großen Leinwand blieben Bandkennung, Untertitel und Autorenzeile winzig,
    # während nur der Titel mitwächst.
    from reportlab.lib.units import mm

    breite_pt = cfg["seitenformat"]["breite_mm"] * mm
    hoehe_pt = breite_pt * (hoehe_px / breite_px)
    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(breite_pt, hoehe_pt),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Kindle")

    # Dasselbe Titelfoto wie beim Taschenbuch. Im Amazon-Katalog stehen
    # Taschenbuch und Kindle-Ausgabe nebeneinander; unterschiedliche Motive
    # sähen nach zwei verschiedenen Büchern aus.
    titelbild = bc.titelbild_suchen(cover_verzeichnis)

    if cfg.get("cover_stil") == "schiefer":
        ill.schiefergrund(c, 0, 0, breite_pt, hoehe_pt)
        if not titelbild:
            # bezug=breite_pt statt der Trimmbreite: Die Auslage soll über die
            # Bildbreite dieselbe Dichte haben wie auf dem gedruckten Umschlag
            # über eine Buchbreite.
            bc.auslage_oben(c, 0, hoehe_pt * (1 - bc.AUSLAGE_HOEHE),
                            breite_pt, hoehe_pt * bc.AUSLAGE_HOEHE,
                            bezug=breite_pt, wiederholungen=1)
        bc.vorderseite_schiefer(c, 0, 0, breite_pt, hoehe_pt, cfg, titelbild,
                                kennung=kennung)
    else:
        c.setFillColor(ill.PALETTE["papier"])
        c.rect(0, 0, breite_pt, hoehe_pt, stroke=0, fill=1)
        bc.vorderseite(c, 0, 0, breite_pt, hoehe_pt, cfg, titelbild)

    c.showPage()
    c.save()

    dokument = fitz.open(stream=puffer.getvalue(), filetype="pdf")
    pix = dokument[0].get_pixmap(
        matrix=fitz.Matrix(breite_px / breite_pt, hoehe_px / hoehe_pt),
        alpha=False)
    bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ziel, format="JPEG", quality=JPEG_QUALITAET, optimize=True)
    return {"ziel": ziel, "px": bild.size, "kb": ziel.stat().st_size / 1024}


def pruefen(pfad):
    """Gegen Amazons Vorgaben für Kindle-Titelbilder."""
    from PIL import Image

    befunde = []
    with Image.open(pfad) as bild:
        breite, hoehe = bild.size
        if bild.format != "JPEG":
            befunde.append(f"Format {bild.format} statt JPEG")
        if bild.mode != "RGB":
            befunde.append(f"Farbmodus {bild.mode} statt RGB")
    if max(breite, hoehe) < 1000:
        befunde.append(f"lange Kante nur {max(breite, hoehe)} px (mindestens 1000)")
    if max(breite, hoehe) > 10000:
        befunde.append(f"lange Kante {max(breite, hoehe)} px (höchstens 10000)")
    verhaeltnis = hoehe / breite
    if abs(verhaeltnis - 1.6) > 0.01:
        befunde.append(f"Seitenverhältnis {verhaeltnis:.2f} statt 1,60")
    if Path(pfad).stat().st_size > 50 * 1024 * 1024:
        befunde.append("größer als 50 MB")
    return befunde


def main():
    import yaml

    for name, yaml_pfad, ziel, kennung, cover in BAENDE:
        cfg = yaml.safe_load((WURZEL / yaml_pfad).read_text(encoding="utf-8"))
        ergebnis = titelbild_bauen(cfg, WURZEL / ziel, kennung, WURZEL / cover)
        befunde = pruefen(ergebnis["ziel"])
        b, h = ergebnis["px"]
        print(f"{name}: {b} x {h} px · {ergebnis['kb']:.0f} KB")
        print("  " + ("passt zu Amazons Vorgaben" if not befunde
                      else "ACHTUNG: " + "; ".join(befunde)))
        print(f"  → {ergebnis['ziel'].relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
