#!/usr/bin/env python3
"""Baut „Was uns die Maschine abnimmt“ aus ki/kapitel/*.md.

    python3 ki/build/build_ki.py

Das Buch gehört nicht zur Stoffwechsel-Reihe, nutzt aber dieselbe
Satz-Werkstatt: Renderer, Absatzformate und PDF-Erzeugung kommen aus
buch/build/. Eigen ist hier nur die Typografie — 6 × 9 Zoll wie Band 1, aber
ein Sachbuch mit langen Kapiteln statt kurzer Merksätze, deshalb etwas mehr
Durchschuss und ein größerer Abstand vor Zwischenüberschriften.

Der Ablauf ist derselbe wie bei Band 1 und aus demselben Grund dreistufig:

  1. Durchlauf ohne Inhaltsverzeichnis — er liefert die Seitenzahlen.
  2. Durchlauf mit gesetztem Verzeichnis.
  3. Nur bei ungerader Seitenzahl: Durchlauf mit Vakatseite am Ende, weil KDP
     sonst selbst ein unbeschriftetes Blatt einschiebt.
"""

import sys
from pathlib import Path

import yaml
from docx.shared import RGBColor

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import stile  # noqa: E402
from build_docx import (  # noqa: E402
    bauen, kapitel_laden, pdf_erzeugen, seitenzahlen_ermitteln,
)

KI = WURZEL / "ki"

# Eigene Leitfarbe. buch/build/stile.py ist auf das Blattgrün der
# Stoffwechsel-Reihe eingestellt; dieses Buch gehört nicht dazu und soll im
# Regal nicht danach aussehen. Geändert wird deshalb nichts an stile.py — die
# Farben werden über `stilwerte` je Absatzformat überschrieben.
#
# Kontrast auf Papierweiß: AKZENT 8,7:1, AKZENT_HELL 4,6:1. Beide stehen auch
# in Normalgröße (Unterabschnitt, Kapitelnummer) und müssen deshalb die 4,5:1
# halten — wer hier aufhellt, muss nachrechnen.
AKZENT = RGBColor(0x1F, 0x4E, 0x79)       # tiefes Schieferblau
AKZENT_HELL = RGBColor(0x4A, 0x76, 0x9C)  # dieselbe Farbe, aufgehellt
KASTEN = "ECF1F6"                          # Schattierung der Hinweiskästen

# Abweichungen von den Formaten in buch/build/stile.py. Nicht dort ändern —
# die Werte dort gelten für alle drei Bände der Stoffwechsel-Reihe mit.
#
# Zur Typografie: 1,30 statt 1,15 Durchschuss und ein größerer Abstand vor den
# Zwischenüberschriften. Band 1 ist in kurzen Merksätzen geschrieben, dieses
# Buch in Argumentationsketten über mehrere Absätze — die brauchen mehr Luft,
# sonst liest sich die Seite als Block.
TYPOGRAFIE = {
    "Fliesstext": {"zeilen": 1.30},
    "FliesstextEng": {"zeilen": 1.30},
    "Punkt": {"zeilen": 1.25},
    "Nummer": {"zeilen": 1.25},
    "Abschnitt": {"vor": 17},
    "BuchTitel": {"farbe": AKZENT},
    "Teilnummer": {"farbe": AKZENT_HELL},
    "Teiltitel": {"farbe": AKZENT},
    "KapitelNummer": {"farbe": AKZENT_HELL},
    "Kapitel": {"farbe": AKZENT},
    "KastenTitel": {"farbe": AKZENT},
    "InhaltTeil": {"farbe": AKZENT},
}


def main():
    cfg = yaml.safe_load((KI / "ki.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(KI / "kapitel")
    ziel = KI / "out" / f"{cfg['slug']}.docx"

    urspruenglich = stile.dokument_anlegen

    def mit_typografie(seitenformat, stilwerte=None):
        werte = dict(TYPOGRAFIE)
        werte.update(stilwerte or {})
        return urspruenglich(seitenformat, werte)

    # Die Kastenschattierung wird erst beim Rendern gelesen, nicht beim
    # Anlegen der Formate — sie lässt sich deshalb nur so umstellen.
    stile.dokument_anlegen = mit_typografie
    kasten_vorher = stile.FARBEN["kasten"]
    stile.FARBEN["kasten"] = KASTEN
    try:
        bauen(cfg, kapitel, ziel)
        pdf = pdf_erzeugen(ziel)
        toc = seitenzahlen_ermitteln(pdf, kapitel)

        bauen(cfg, kapitel, ziel, toc_daten=toc)
        pdf = pdf_erzeugen(ziel)

        from pypdf import PdfReader
        seiten = len(PdfReader(str(pdf)).pages)

        if seiten % 2:
            bauen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True)
            pdf = pdf_erzeugen(ziel)
            seiten = len(PdfReader(str(pdf)).pages)
    finally:
        stile.dokument_anlegen = urspruenglich
        stile.FARBEN["kasten"] = kasten_vorher

    fehlend = [k["meta"].get("titel") for k in kapitel
               if k["meta"]["typ"] != "titelei"
               and not any(e["titel"] == k["meta"].get("titel") for e in toc)]

    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{seiten} Seiten")
    if fehlend:
        print("  Ohne Seitenzahl im Verzeichnis: " + ", ".join(fehlend))
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
