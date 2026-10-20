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

# KDP nimmt Taschenbücher erst ab 24 Seiten an.
MIN_SEITEN = 24


def main():
    from pypdf import PdfReader

    cfg = yaml.safe_load((KOPF / "kopf.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(KOPF / "kapitel")
    ziel = KOPF / "out" / f"{cfg['slug']}.docx"

    bauen(cfg, kapitel, ziel)
    pdf = pdf_erzeugen(ziel)
    toc = seitenzahlen_ermitteln(pdf, kapitel)

    bauen(cfg, kapitel, ziel, toc_daten=toc)
    pdf = pdf_erzeugen(ziel)
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        bauen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True)
        pdf = pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)

    sf = cfg["seitenformat"]
    druck = auf_trimmgroesse(pdf, sf["breite_mm"], sf["hoehe_mm"])
    befunde = pruefen(druck["ziel"], sf["breite_mm"], sf["hoehe_mm"])
    if seiten < MIN_SEITEN:
        befunde.append(f"KDP verlangt mindestens {MIN_SEITEN} Seiten")

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
