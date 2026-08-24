#!/usr/bin/env python3
"""Baut Band 4 aus adhs/kapitel/*.md zu einem druckfertigen .docx samt PDF.

    python3 adhs/build/build_adhs.py

Der Band teilt sich die gesamte Satzlogik mit Band 1 — Markdown-Umsetzung,
Absatzformate, Seitenzahlen, Inhaltsverzeichnis. Hier steht deshalb nur, was
sich unterscheidet: das Quellverzeichnis und die YAML-Datei.

Absatzformate kommen unverändert aus buch/build/stile.py. Dort wird **nicht**
gedreht, um die Seitenzahl dieses Bandes zu treffen — das verstellt die
anderen drei mit (siehe buch/README.md).
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
ADHS = WURZEL / "adhs"

# build_docx.py liegt neben stile.py und erwartet dessen Verzeichnis im Pfad.
sys.path.insert(0, str(WURZEL / "buch" / "build"))
import build_docx  # noqa: E402


def main():
    cfg = yaml.safe_load((ADHS / "adhs.yaml").read_text(encoding="utf-8"))
    kapitel = build_docx.kapitel_laden(ADHS / "kapitel")
    ziel = ADHS / "out" / f"{cfg['slug']}.docx"

    # Durchlauf 1: ohne Verzeichnis, nur um die Seitenzahlen zu erfahren.
    build_docx.bauen(cfg, kapitel, ziel)
    pdf = build_docx.pdf_erzeugen(ziel)
    toc = build_docx.seitenzahlen_ermitteln(pdf, kapitel)

    # Durchlauf 2: mit fertigem Verzeichnis. Weil die Titelei römisch und der
    # Rumpf dezimal ab 1 zählt, verschiebt das längere Verzeichnis die
    # Rumpfseitenzahlen nicht — ein zweiter Durchlauf genügt.
    build_docx.bauen(cfg, kapitel, ziel, toc_daten=toc)
    pdf = build_docx.pdf_erzeugen(ziel)

    from pypdf import PdfReader
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        # Dritter Durchlauf mit Vakatseite am Ende. Erst jetzt möglich —
        # vorher ist die Seitenzahl unbekannt. Das Verzeichnis bleibt
        # gültig: Die Leerseite hängt hinten an und verschiebt nichts.
        build_docx.bauen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True)
        pdf = build_docx.pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)

    rumpf = [k for k in kapitel if k["meta"]["typ"] != "titelei"]
    fehlend = len(rumpf) - len(toc)

    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{seiten} Seiten")
    if fehlend:
        # seitenzahlen_ermitteln() lässt eine Überschrift lieber aus, als eine
        # falsche Seitenzahl zu drucken. Das darf nicht unbemerkt bleiben.
        print(f"  ACHTUNG: {fehlend} Kapitel ohne Seitenzahl im Verzeichnis")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
