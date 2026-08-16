#!/usr/bin/env python3
"""Baut die Kindle-Ausgabe als EPUB 3.

    python3 ki/build/build_cover.py    # zuerst — liefert das Titelbild
    python3 ki/build/build_epub.py

Ein Lesebuch gehört auf dem Kindle mit fließendem Text gesetzt: Der Leser
stellt Schriftgröße und Rand selbst ein, der Text läuft neu um. Seitenzahlen,
Kopfzeilen und ein Inhaltsverzeichnis mit Seitenangaben gibt es dort nicht —
an ihre Stelle tritt die Navigation, die der Reader selbst anzeigt. Gebaut
wird deshalb direkt aus ki/kapitel/*.md, nicht aus dem Druck-PDF.

Gerüst, Absatzformate und Prüfung kommen aus buch/build/build_epub.py; dieses
Buch nutzt dieselbe Bauart wie Band 1 der Stoffwechsel-Reihe. Eigen ist hier
nur die Kennung — sie muss über Bücher und Auflagen hinweg eindeutig bleiben.

Erzeugt wird EPUB, nicht MOBI oder KPF: KDP nimmt EPUB entgegen und wandelt
selbst.
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import build_epub as be  # noqa: E402
from build_docx import kapitel_laden  # noqa: E402

KI = WURZEL / "ki"


def main():
    cfg = yaml.safe_load((KI / "ki.yaml").read_text(encoding="utf-8"))
    umschlag = KI / "out" / "kindle-cover.jpg"
    if not umschlag.exists():
        raise SystemExit(
            f"{umschlag.relative_to(WURZEL)} fehlt — erst "
            "python3 ki/build/build_cover.py laufen lassen."
        )

    kapitel = kapitel_laden(KI / "kapitel")
    ziel = KI / "out" / f"{cfg['slug']}-kindle.epub"

    # Eigene Kennung. band1_bauen setzt „b001" fest ein — mit der Vorlage aus
    # build_epub.py bekäme dieses Buch deshalb dieselbe Kennung wie Band 1 der
    # Stoffwechsel-Reihe. Unterschieden wird daher an der Vorlage selbst, nicht
    # am Bandkürzel. Die Kennung muss über Auflagen hinweg stabil bleiben:
    # Amazon erkennt daran, dass eine neue Datei dasselbe Buch ist.
    kennung_vorher = be.KENNUNG
    be.KENNUNG = "urn:uuid:3d7e5c42-{band}-4f18-9c30-mvd{jahr}"
    try:
        ziel, eintraege = be.band1_bauen(cfg, kapitel, umschlag, ziel)
    finally:
        be.KENNUNG = kennung_vorher

    navigation = sum(1 for e in eintraege if e["im_verzeichnis"])
    be.bericht("Kindle-Ausgabe — fließender Text", ziel,
               f"{len(kapitel)} Kapitel, {navigation} Navigationspunkte")


if __name__ == "__main__":
    main()
