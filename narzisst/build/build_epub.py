#!/usr/bin/env python3
"""Baut die Kindle-Ausgabe von „Der Narzisst in meinem Bett" als EPUB 3.

    python3 narzisst/build/build_epub.py

Fließender Text wie bei „Kopf schlägt Kalorien": gebaut direkt aus
narzisst/kapitel/*.md, ohne Seitenzahlen und Kopfzeilen — die Navigation
übernimmt der Reader. Die Bausteine kommen aus buch/build/build_epub.py.
Eigen sind:

- **Kennung:** eine eigene UUID, damit Amazon den Titel nicht mit einem
  anderen verwechselt.
- **Farben:** Aubergine und Rosé wie auf dem Umschlag statt des Grüns der
  Reihe. Auf Graustufendisplays bleiben alle Töne unterscheidbar.

Dazu das Kindle-Titelbild: 1600 × 2560 Pixel (Seitenverhältnis 1,6, Amazons
Empfehlung), mit denselben Funktionen gesetzt wie der gedruckte Umschlag.
"""

import importlib.util
import sys
from pathlib import Path

import yaml
from PIL import Image

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "narzisst"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import build_epub as reihe  # noqa: E402
from build_docx import kapitel_laden  # noqa: E402

KINDLE_PX = (1600, 2560)

# Fest vergeben und über Auflagen hinweg stabil halten.
reihe.KENNUNG = "urn:uuid:8fef748e-11c8-44e7-9d3e-a82a24a9162d"

reihe.STIL_FLIESSEND = (reihe.STIL_FLIESSEND
                        .replace("#2F7A3E", "#4A1F45")
                        .replace("#6FA85E", "#B5656B")
                        .replace("#EEF4EA", "#F5EEF3"))


def umschlag_modul():
    """narzisst/build/build_cover.py unter eigenem Namen laden."""
    pfad = BAND / "build" / "build_cover.py"
    spec = importlib.util.spec_from_file_location("narzisst_cover", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def kindle_cover_bauen(cfg, ziel):
    uc = umschlag_modul()
    breite, hoehe = KINDLE_PX
    bild = uc.verlauf(breite, hoehe, uc.FARBE["grund_oben"],
                      uc.FARBE["grund_unten"])
    # Die Vorderseite ist für 1800 × 2700 px (6 × 9 Zoll bei 300 dpi) gesetzt;
    # auf dieser Leinwand mit Seitenverhältnis 1,6 gewinnt sie oben und unten
    # etwas Luft.
    uc.vorderseite(bild, 0, 0, breite, hoehe, cfg)
    bild.save(ziel, "JPEG", quality=92, optimize=True)
    return ziel


def main():
    cfg = yaml.safe_load((BAND / "narzisst.yaml").read_text(encoding="utf-8"))
    out = BAND / "out"
    out.mkdir(exist_ok=True)

    umschlag = kindle_cover_bauen(cfg, out / "kindle-cover.jpg")

    kapitel = kapitel_laden(BAND / "kapitel")
    ziel = out / f"{cfg['slug']}-kindle.epub"
    ziel, eintraege = reihe.band1_bauen(cfg, kapitel, umschlag, ziel)
    verzeichnis = sum(1 for e in eintraege if e["im_verzeichnis"])
    reihe.bericht("Kindle-Ausgabe — fließender Text", ziel,
                  f"{len(kapitel)} Kapitel, {verzeichnis} Navigationspunkte")
    groesse = Image.open(umschlag).size
    print(f"  → {umschlag.relative_to(WURZEL)}  ({groesse[0]} x {groesse[1]} px, "
          "Titelbild für KDP)")


if __name__ == "__main__":
    main()
