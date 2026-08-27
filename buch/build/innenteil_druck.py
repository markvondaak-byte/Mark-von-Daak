#!/usr/bin/env python3
"""Bringt die Innenteile auf die exakte Trimmgröße für KDP.

    python3 buch/build/innenteil_druck.py

Hintergrund: LibreOffice exportiert 6″ × 9″ nicht maßhaltig. Im .docx steht
die Seitengröße korrekt als 8640 × 12960 Twips (152,4 × 228,6 mm), im
erzeugten PDF sind daraus 152,4 × 229,01 mm geworden — 0,41 mm zu hoch. Das
ist kein Fehler dieses Projekts: Schon ein leeres Dokument mit derselben
Seitengröße kommt so heraus. A4 ist davon nicht betroffen.

KDP prüft die Seitengröße gegen die im Formular gewählte Trimmgröße und weist
Abweichungen zurück. Hier wird die Seitenbox deshalb auf das Sollmaß gesetzt.

Beschnitten wird unten. Gemessen sitzt der Überschuss dort: Die Kopfzeile
steht 10,09 mm unter der Oberkante (Soll 10,0), die Fußzeile 10,55 mm über
der Unterkante. Nach dem Beschnitt sind es 10,09 oben und 10,14 unten — der
Satzspiegel steht damit symmetrischer als vorher, und keine Zeile wandert.
"""

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
PT_JE_MM = 72 / 25.4

# Sollmaße als KDP-Trimmgrößen in Zoll gerechnet, nicht als runde Millimeter:
# 6 × 9 Zoll und 8,27 × 11,69 Zoll. KDP prüft gegen diese Werte.
BAENDE = [
    ("Band 1", "buch/out/stoffwechsel-reset.pdf", 152.4, 228.6),
    ("Band 2", "workbook/out/workbook.pdf", 203.2, 254.0),
    ("Band 3", "rezepte/out/rezeptbuch.pdf", 203.2, 254.0),
    # Eigener Innenteil fürs Hardcover: KDP führt 8 x 10 Zoll nur als
    # Taschenbuch, das Hardcover läuft auf 8,25 x 11 Zoll.
    ("Band 3 Hardcover", "rezepte/out/rezeptbuch-hardcover.pdf", 209.55, 279.4),
    # Eigenständiger Band, nicht Teil der Stoffwechsel-Reihe. 6 x 9 Zoll wie
    # Band 1, deshalb genügt ein Innenteil für Taschenbuch und Hardcover.
    ("Reptiliengehirn", "reptilienhirn/out/reptiliengehirn.pdf", 152.4, 228.6),
]


def auf_trimmgroesse(quelle, breite_mm, hoehe_mm, ziel=None):
    from pypdf import PdfReader, PdfWriter

    quelle = Path(quelle)
    ziel = Path(ziel) if ziel else quelle.with_name(quelle.stem + "-druck.pdf")

    soll_b = breite_mm * PT_JE_MM
    soll_h = hoehe_mm * PT_JE_MM

    reader = PdfReader(str(quelle))
    writer = PdfWriter()
    groesster_versatz = 0.0

    for seite in reader.pages:
        kiste = seite.mediabox
        ist_h = float(kiste.height)
        # Überschuss unten abschneiden, damit der Abstand zur Oberkante — und
        # damit jede Zeile Text — unverändert bleibt.
        unten = float(kiste.bottom) + (ist_h - soll_h)
        links = float(kiste.left)
        groesster_versatz = max(groesster_versatz, abs(ist_h - soll_h))

        for kasten in (seite.mediabox, seite.cropbox):
            kasten.lower_left = (links, unten)
            kasten.upper_right = (links + soll_b, unten + soll_h)
        writer.add_page(seite)

    with open(ziel, "wb") as datei:
        writer.write(datei)

    return {"ziel": ziel, "seiten": len(reader.pages),
            "versatz_mm": groesster_versatz / PT_JE_MM,
            "kb": ziel.stat().st_size / 1024}


def pruefen(pdf, breite_mm, hoehe_mm):
    """Gegenprobe an der geschriebenen Datei, nicht an den Rechenwerten."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    befunde = []

    masse = {(round(float(s.mediabox.width) / PT_JE_MM, 3),
              round(float(s.mediabox.height) / PT_JE_MM, 3))
             for s in reader.pages}
    if len(masse) != 1:
        befunde.append(f"uneinheitliche Seitengrößen: {sorted(masse)}")
    else:
        b, h = masse.pop()
        if abs(b - breite_mm) > 0.05 or abs(h - hoehe_mm) > 0.05:
            befunde.append(f"{b} x {h} mm statt {breite_mm} x {hoehe_mm}")

    if len(reader.pages) % 2:
        befunde.append(f"ungerade Seitenzahl ({len(reader.pages)})")

    fehlende = set()
    for seite in reader.pages:
        res = seite.get("/Resources", {})
        if hasattr(res, "get_object"):
            res = res.get_object()
        schriften = res.get("/Font")
        if not schriften:
            continue
        for schluessel in schriften.get_object():
            font = schriften.get_object()[schluessel].get_object()
            deskriptor = font.get("/FontDescriptor")
            if deskriptor is None:
                nachkommen = font.get("/DescendantFonts")
                if nachkommen:
                    deskriptor = nachkommen[0].get_object().get("/FontDescriptor")
            if deskriptor is None:
                continue
            if not any(k in deskriptor.get_object()
                       for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                fehlende.add(str(font.get("/BaseFont", "?")))
    if fehlende:
        befunde.append("Schriften nicht eingebettet: " + ", ".join(sorted(fehlende)))

    return befunde


def main():
    for name, pfad, breite, hoehe in BAENDE:
        quelle = WURZEL / pfad
        if not quelle.exists():
            print(f"{name}: {pfad} fehlt — erst den Innenteil bauen.")
            continue
        ergebnis = auf_trimmgroesse(quelle, breite, hoehe)
        befunde = pruefen(ergebnis["ziel"], breite, hoehe)
        print(f"{name}: {ergebnis['seiten']} Seiten, {breite} x {hoehe} mm, "
              f"{ergebnis['kb']:.0f} KB")
        if ergebnis["versatz_mm"] > 0.001:
            print(f"  korrigiert um {ergebnis['versatz_mm']:.3f} mm in der Höhe")
        print("  " + ("druckfertig" if not befunde else "ACHTUNG: " + "; ".join(befunde)))
        print(f"  → {ergebnis['ziel'].relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
