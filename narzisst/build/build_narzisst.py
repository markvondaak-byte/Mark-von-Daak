#!/usr/bin/env python3
"""Baut den Innenteil von „Der Narzisst in meinem Bett" aus narzisst/kapitel/*.md.

    python3 narzisst/build/build_narzisst.py

Gleiche Toolchain wie „Kopf schlägt Kalorien" (kopf/build/build_kopf.py) und
Band 1 der Reihe: .docx über LibreOffice nach .pdf, zwei Durchläufe fürs
Inhaltsverzeichnis, bei ungerader Seitenzahl ein dritter mit Vakatseite.
Danach wird das PDF auf die exakte Trimmgröße gebracht und jede Seitenbox in
den Ursprung gelegt — hochgeladen wird `out/<slug>-druck.pdf`.

Anders als „Kopf schlägt Kalorien" hat dieser Titel keinen Arbeitsteil und
keine Übungen; Schreibfelder gibt es deshalb nicht.
"""

import importlib.util
import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "narzisst"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_docx import (bauen, kapitel_laden, pdf_erzeugen,  # noqa: E402
                        seitenzahlen_ermitteln)
from innenteil_druck import auf_trimmgroesse, pruefen  # noqa: E402

# KDP nimmt Hardcover erst ab 75 Seiten an, und Taschenbuch und Hardcover
# teilen sich einen Innenteil — deshalb ist der Band auf 76 Seiten ausgelegt.
MIN_SEITEN = 76


def ursprung_nullen(pdf_pfad, breite_mm, hoehe_mm):
    """Aus kopf/build/build_kopf.py — dort steht, warum."""
    pfad = WURZEL / "kopf" / "build" / "build_kopf.py"
    spec = importlib.util.spec_from_file_location("kopf_innenteil", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    modul.ursprung_nullen(pdf_pfad, breite_mm, hoehe_mm)


def setzen(cfg, kapitel, ziel, **optionen):
    bauen(cfg, kapitel, ziel, **optionen)
    return pdf_erzeugen(ziel)


def main():
    from pypdf import PdfReader

    cfg = yaml.safe_load((BAND / "narzisst.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(BAND / "kapitel")
    ziel = BAND / "out" / f"{cfg['slug']}.docx"

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
