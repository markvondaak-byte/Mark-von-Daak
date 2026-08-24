#!/usr/bin/env python3
"""Erzeugt das Titelbild für die Kindle-Ausgabe von Band 4.

    python3 adhs/build/kindle_titelbild.py

Amazon verlangt für Kindle kein aufgeklapptes PDF, sondern ein einzelnes Bild
der Vorderseite: JPEG, mindestens 1000 Pixel an der langen Kante, empfohlen
1600 x 2560 — Seitenverhältnis 1,6.

Das ist nicht das Verhältnis des gedruckten Bandes (6 x 9 Zoll sind 1,5).
Deshalb wird die Vorderseite hier neu gesetzt statt aus dem Umschlag-PDF
ausgeschnitten — beim Ausschneiden müsste oben Fläche weg, und das Motiv
verlöre genau den Teil, in dem es sich ordnet.

Der Dateiname weicht bewusst von `buch/build/kindle_cover.py` ab: Beide
Verzeichnisse liegen beim Bauen gleichzeitig im Suchpfad, und zwei Module
gleichen Namens verdecken einander.
"""

import io
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
# Eigenes Verzeichnis zuerst, damit `build_cover` die Fassung dieses Bandes
# meint und nicht die der Reihe.
sys.path.insert(0, str(WURZEL / "buch" / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

BREITE_PX, HOEHE_PX = 1600, 2560     # Amazons Empfehlung
JPEG_QUALITAET = 92


def titelbild_bauen(cfg, ziel, breite_px=BREITE_PX, hoehe_px=HOEHE_PX):
    import fitz
    from PIL import Image
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    import gestaltung as umschlag       # adhs/build/gestaltung.py

    from build_cover import schriften_laden
    schriften_laden()

    # Die Leinwand bekommt die echte Buchbreite in Punkt, die Höhe ergibt sich
    # aus dem geforderten Verhältnis 1,6. Das ist wichtig, weil die Schrift-
    # größen absolute Punktwerte sind: Auf einer beliebig großen Leinwand
    # blieben Untertitel und Autorenzeile winzig, während nur der Titel
    # mitwüchse.
    breite_pt = cfg["seitenformat"]["breite_mm"] * mm
    hoehe_pt = breite_pt * (hoehe_px / breite_px)

    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(breite_pt, hoehe_pt),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Kindle")

    umschlag.tintengrund(c, 0, 0, breite_pt, hoehe_pt)
    # ueberstand=0: Ein Kindle-Titelbild wird nicht beschnitten, es gibt also
    # keinen Anschnitt, in den etwas hineinlaufen dürfte.
    umschlag.vorderseite(c, 0, 0, breite_pt, hoehe_pt, cfg, ueberstand=0)

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


def main():
    import yaml
    from kindle_cover import pruefen   # buch/build — reine Prüffunktion

    cfg = yaml.safe_load(
        (WURZEL / "adhs" / "adhs.yaml").read_text(encoding="utf-8"))
    ziel = WURZEL / "adhs" / "out" / "kindle-cover.jpg"
    ergebnis = titelbild_bauen(cfg, ziel)
    befunde = pruefen(ergebnis["ziel"])
    b, h = ergebnis["px"]
    print(f"Band 4: {b} x {h} px · {ergebnis['kb']:.0f} KB")
    print("  " + ("passt zu Amazons Vorgaben" if not befunde
                  else "ACHTUNG: " + "; ".join(befunde)))
    print(f"  → {ergebnis['ziel'].relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
