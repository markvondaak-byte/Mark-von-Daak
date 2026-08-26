#!/usr/bin/env python3
"""Baut „Das Reptiliengehirn des Menschen" aus reptilienhirn/kapitel/*.md.

    python3 reptilienhirn/build/build_reptilienhirn.py

Der Satz kommt unverändert aus `buch/build/build_docx.py` — dieselbe
Markdown-Teilmenge, dieselben Absatzformate, dieselbe Behandlung von Titelei,
Teil-Trennseiten und Kopfzeilen. Hier stehen nur die abweichenden Pfade und
die eigene Metadatendatei. Wer am Satz etwas ändern will, ändert ihn dort;
alles andere lässt die Bände der Reihe auseinanderlaufen.
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "reptilienhirn"

sys.path.insert(0, str(WURZEL / "buch" / "build"))
import build_docx  # noqa: E402


def main():
    cfg = yaml.safe_load(
        (BAND / "reptilienhirn.yaml").read_text(encoding="utf-8"))
    kapitel = build_docx.kapitel_laden(BAND / "kapitel")
    ziel = BAND / "out" / f"{cfg['slug']}.docx"

    # Durchlauf 1: ohne Verzeichnis, nur um die Seitenzahlen zu erfahren.
    build_docx.bauen(cfg, kapitel, ziel)
    pdf = build_docx.pdf_erzeugen(ziel)
    toc = build_docx.seitenzahlen_ermitteln(pdf, kapitel)

    # Durchlauf 2: mit fertigem Verzeichnis.
    build_docx.bauen(cfg, kapitel, ziel, toc_daten=toc)
    pdf = build_docx.pdf_erzeugen(ziel)

    from pypdf import PdfReader
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        # Dritter Durchlauf mit Vakatseite — KDP verlangt eine gerade
        # Seitenzahl und schiebt sonst selbst ein unbeschriftetes Blatt ein.
        build_docx.bauen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True)
        pdf = build_docx.pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)

    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{seiten} Seiten")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
