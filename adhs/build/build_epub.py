#!/usr/bin/env python3
"""Baut die Kindle-Ausgabe von Band 4 als EPUB 3.

    python3 adhs/build/build_epub.py

Voraussetzung ist das Titelbild:

    python3 adhs/build/kindle_titelbild.py

Ein Lesebuch gehört auf dem Kindle **reflowable** gesetzt: Der Leser stellt
Schriftgröße und Rand selbst ein, der Text läuft neu um. Feste Seitenzahlen,
Kopfzeilen und ein Inhaltsverzeichnis mit Seitenangaben gibt es hier nicht —
an ihre Stelle tritt die Navigation, die der Reader selbst anzeigt.

Gebaut wird deshalb direkt aus `adhs/kapitel/*.md`, nicht aus dem Druck-PDF.
Die eigentliche Arbeit macht `band1_bauen()` aus `buch/build/build_epub.py`:
Sie ist nicht an Band 1 gebunden, sondern nimmt Konfiguration, Kapitelliste
und Titelbild entgegen — genau das, was ein Fließtextband braucht.

Erzeugt wird EPUB, nicht MOBI oder KPF: KDP nimmt EPUB für Kindle-Bücher
entgegen und wandelt selbst.
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_docx import kapitel_laden  # noqa: E402
from build_epub import band1_bauen, bericht  # noqa: E402

ADHS = WURZEL / "adhs"


def main():
    cfg = yaml.safe_load((ADHS / "adhs.yaml").read_text(encoding="utf-8"))

    umschlag = ADHS / "out" / "kindle-cover.jpg"
    if not umschlag.exists():
        raise SystemExit(
            "Titelbild fehlt — erst `python3 adhs/build/kindle_titelbild.py` "
            "laufen lassen."
        )

    kapitel = kapitel_laden(ADHS / "kapitel")
    ziel = ADHS / "out" / f"{cfg['slug']}-kindle.epub"
    ziel, eintraege = band1_bauen(cfg, kapitel, umschlag, ziel)

    im_verzeichnis = sum(1 for e in eintraege if e["im_verzeichnis"])
    bericht("Band 4 — fließender Text", ziel,
            f"{len(kapitel)} Kapitel, {im_verzeichnis} Navigationspunkte")


if __name__ == "__main__":
    main()
