#!/usr/bin/env python3
"""Baut die Kindle-Ausgabe von „Der Narzisst in meinem Bett" als EPUB 3.

    python3 narzisst/build/build_epub.py

Fließender Text wie bei „Kopf schlägt Kalorien": gebaut direkt aus
narzisst/kapitel/*.md, ohne Seitenzahlen und Kopfzeilen — die Navigation
übernimmt der Reader. Die Bausteine kommen aus buch/build/build_epub.py.
Eigen sind:

- **Kennung:** eine eigene UUID, damit Amazon den Titel nicht mit einem
  anderen verwechselt.
- **Farben:** Aubergine und Rosé statt des Grüns der Reihe. Auf
  Graustufendisplays bleiben alle Töne unterscheidbar.

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

sys.path.insert(0, str(BAND / "build"))
from build_narzisst import isbn_einsetzen  # noqa: E402

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
    titelbild = uc.titelbild_suchen()
    oben, unten = uc.FARBE["grund_oben"], uc.FARBE["grund_unten"]
    if titelbild:
        foto = Image.open(titelbild)
        oben, unten = uc.K.randfarbe(foto, "oben"), uc.K.randfarbe(foto, "unten")
    bild = uc.verlauf(breite, hoehe, oben, unten)
    if titelbild:
        uc.titelbild_einsetzen(bild, titelbild, 0, breite, ueberblendung=0)
        uc.abdunkeln(bild, 0, 0, breite, hoehe, unten)
    # Schmaler und höher als 6 × 9 Zoll: Der Titel beginnt etwas weiter oben.
    uc.vorderseite(bild, 0, 0, breite, hoehe, cfg, foto=bool(titelbild),
                   titel_y=0.56)
    bild.save(ziel, "JPEG", quality=92, optimize=True)
    return ziel


def main():
    cfg = yaml.safe_load((BAND / "narzisst.yaml").read_text(encoding="utf-8"))
    out = BAND / "out"
    out.mkdir(exist_ok=True)

    umschlag = kindle_cover_bauen(cfg, out / "kindle-cover.jpg")

    kapitel = kapitel_laden(BAND / "kapitel")
    isbn_einsetzen(kapitel, cfg, ebook=True)   # E-Book: ASIN statt ISBN
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
