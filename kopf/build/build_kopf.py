#!/usr/bin/env python3
"""Baut den Innenteil von „Kopf schlägt Kalorien" aus kopf/kapitel/*.md.

    python3 kopf/build/build_kopf.py

Gleiche Toolchain wie Band 1 der Reihe (buch/build/build_docx.py): .docx über
LibreOffice nach .pdf, zwei Durchläufe fürs Inhaltsverzeichnis, bei ungerader
Seitenzahl ein dritter mit Vakatseite. Danach wird das PDF auf die exakte
Trimmgröße gebracht — hochgeladen wird `out/<slug>-druck.pdf`.
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
KOPF = WURZEL / "kopf"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_docx import (bauen, kapitel_laden, pdf_erzeugen,  # noqa: E402
                        seitenzahlen_ermitteln)
from innenteil_druck import auf_trimmgroesse, pruefen  # noqa: E402

LEER = " "          # &nbsp; — so stehen Schreibfelder in den Vorlagen
SCHREIBZEILE_MM = 9.0    # Mindesthöhe einer Zeile zum Ausfüllen
FRAGEZEILE_MM = 20.0     # Zeile mit einer langen Frage und leerem Antwortfeld


def schreibzeilen_erhoehen(docx_pfad):
    """Gibt den Schreibfeldern der Vorlagen Platz zum Ausfüllen.

    Eine leere Tabellenzeile ist sonst nur eine Textzeile hoch — darin kann
    niemand schreiben. Erkannt werden Schreibfelder an der Zelle, die nur ein
    geschütztes Leerzeichen enthält; im Fließtext kommt das nicht vor. Bewusst
    hier und nicht in buch/build/stile.py: Die Absatzformate dort gelten für
    alle Bände der Reihe.
    """
    from docx import Document
    from docx.enum.table import WD_ROW_HEIGHT_RULE
    from docx.shared import Mm

    doc = Document(str(docx_pfad))
    for tabelle in doc.tables:
        for zeile in tabelle.rows:
            texte = [zelle.text for zelle in zeile.cells]
            if not any(t.strip(" ") == LEER for t in texte):
                continue
            lang = any(len(t) > 40 for t in texte)
            zeile.height = Mm(FRAGEZEILE_MM if lang else SCHREIBZEILE_MM)
            zeile.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    doc.save(str(docx_pfad))


def setzen(cfg, kapitel, ziel, **optionen):
    bauen(cfg, kapitel, ziel, **optionen)
    schreibzeilen_erhoehen(ziel)
    return pdf_erzeugen(ziel)


# Untergrenze für diesen Titel. KDP selbst nimmt Taschenbücher ab 24 Seiten an,
# der Band ist aber bewusst auf mindestens 70 ausgelegt.
MIN_SEITEN = 70


def ursprung_nullen(pdf_pfad, breite_mm, hoehe_mm):
    """Setzt jede Seite auf ein Blatt, dessen Seitenbox bei (0, 0) beginnt.

    auf_trimmgroesse() schneidet den Überschuss unten ab, indem es die
    Unterkante der Seitenbox um 0,41 mm anhebt. Das Maß stimmt danach, die
    Box beginnt aber nicht im Ursprung — einige Prüfprogramme werten das als
    abweichendes Seitenformat. Hier wird jede Seite als Vektor (Schriften
    bleiben eingebettet) auf ein neues Blatt exakt in Trimmgröße gelegt.
    """
    import fitz

    pt = 72 / 25.4
    quelle = fitz.open(str(pdf_pfad))
    neu = fitz.open()
    for nummer, seite in enumerate(quelle):
        blatt = neu.new_page(width=breite_mm * pt, height=hoehe_mm * pt)
        blatt.show_pdf_page(blatt.rect, quelle, nummer, clip=seite.cropbox)
    neu.set_metadata({"title": quelle.metadata.get("title") or "",
                      "producer": "", "creator": ""})
    zwischen = Path(pdf_pfad).with_suffix(".tmp.pdf")
    neu.save(str(zwischen), garbage=4, deflate=True)
    neu.close()
    quelle.close()
    zwischen.replace(pdf_pfad)


def main():
    from pypdf import PdfReader

    cfg = yaml.safe_load((KOPF / "kopf.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(KOPF / "kapitel")
    ziel = KOPF / "out" / f"{cfg['slug']}.docx"

    pdf = setzen(cfg, kapitel, ziel)
    toc = seitenzahlen_ermitteln(pdf, kapitel)

    pdf = setzen(cfg, kapitel, ziel, toc_daten=toc)
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        pdf = setzen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True)
        seiten = len(PdfReader(str(pdf)).pages)

    sf = cfg["seitenformat"]
    druck = auf_trimmgroesse(pdf, sf["breite_mm"], sf["hoehe_mm"])
    ursprung_nullen(druck["ziel"], sf["breite_mm"], sf["hoehe_mm"])
    befunde = pruefen(druck["ziel"], sf["breite_mm"], sf["hoehe_mm"])
    if seiten < MIN_SEITEN:
        befunde.append(f"weniger als {MIN_SEITEN} Seiten")

    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{seiten} Seiten")
    print("  " + ("druckfertig" if not befunde
                  else "ACHTUNG: " + "; ".join(befunde)))
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {druck['ziel'].relative_to(WURZEL)}  (zu KDP hochladen)")
    if befunde:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
