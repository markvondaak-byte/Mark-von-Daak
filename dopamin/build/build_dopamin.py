#!/usr/bin/env python3
"""Baut Band 4 aus dopamin/kapitel/*.md zu einem druckfertigen .docx und PDF.

    python3 dopamin/build/build_dopamin.py

Der Band nutzt denselben Markdown-Renderer wie Band 1 — dieselbe
Auszeichnungs-Teilmenge, dieselben Marker. Eigen sind ihm drei Dinge:

* **Format 5 x 8 Zoll** statt 6 x 9. Ein reines Lesebuch gehört in die Hand.
* **Eigene Typografie.** Der schmalere Satzspiegel (97 mm) braucht einen
  kleineren Grad, sonst stehen keine 60 Zeichen in der Zeile. Die Werte
  stehen in TYPOGRAFIE und werden `dokument_anlegen()` als Abweichung
  mitgegeben — nicht in `stile.py` gedreht, sonst verstellen sie die Bände
  1 bis 3 mit. Siehe buch/README.md.
* **Eigene Farbwelt.** Indigo statt Blattgrün: Der Band gehört nicht zur
  Stoffwechsel-Reihe und soll im Regal auch nicht so aussehen.
"""

import sys
from pathlib import Path

import yaml
from docx.shared import RGBColor

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import build_docx  # noqa: E402
import stile  # noqa: E402
from build_cover import HARDCOVER_MIN_SEITEN  # noqa: E402
from build_docx import (bauen, kapitel_laden, pdf_erzeugen,  # noqa: E402
                        seitenzahlen_ermitteln)

BAND = WURZEL / "dopamin"

# --- Farbwelt ----------------------------------------------------------------
# Indigo als Leitfarbe. Beide Töne sind gegen Papierweiß auf Kontrast geprüft:
# INDIGO liegt bei rund 9:1, INDIGO_HELL bei rund 4,7:1 — der hellere Ton
# steht nur in kleinen Auszeichnungen und Trennern, nie im Fließtext.
INDIGO = RGBColor(0x2E, 0x2B, 0x6E)
INDIGO_HELL = RGBColor(0x5F, 0x5B, 0xA6)
KASTEN_GRUND = "EDECF5"
KASTEN_RAHMEN = "CFCDE6"

# --- Typografie --------------------------------------------------------------
# Nur die Abweichungen von stile.STILE. Grundsatz: ein Grad kleiner als Band 1
# im Fließtext, deutlich kleinere Überschriften — auf 127 mm Seitenbreite
# wirkt eine 19-pt-Kapitelzeile wie ein Plakat.
TYPOGRAFIE = {
    "BuchTitel": {"groesse": 22, "farbe": INDIGO},
    "BuchUntertitel": {"groesse": 11.5},
    "BuchAutor": {"groesse": 11.5},

    "ImpressumTitel": {"groesse": 15, "farbe": INDIGO},
    "ImpressumKopf": {"groesse": 9.5},
    "ImpressumZeile": {"groesse": 9.5},

    "Teilnummer": {"groesse": 10, "farbe": INDIGO_HELL},
    "Teiltitel": {"groesse": 18, "farbe": INDIGO},
    "KapitelNummer": {"groesse": 9.5, "farbe": INDIGO_HELL},
    "Kapitel": {"groesse": 16, "farbe": INDIGO},
    "Abschnitt": {"groesse": 11.5},
    "Unterabschnitt": {"groesse": 10},

    "Fliesstext": {"groesse": 10.5, "nach": 5},
    "FliesstextEng": {"groesse": 10.5},
    "Einzug": {"groesse": 10.5},
    "Klein": {"groesse": 8.5},
    "KleinMitte": {"groesse": 8.5},
    "Zitat": {"groesse": 10.5},

    "Punkt": {"groesse": 10.5},
    "Nummer": {"groesse": 10.5},

    "KastenTitel": {"groesse": 9.5, "farbe": INDIGO},
    "KastenText": {"groesse": 9},
    "TabellenKopf": {"groesse": 8.5},
    "TabellenZelle": {"groesse": 8.5},

    "InhaltTeil": {"groesse": 9.5, "farbe": INDIGO},
    "InhaltKapitel": {"groesse": 9.5},
}


def farbwelt_setzen():
    """Stellt die Kasten- und Trennerfarben des Renderers auf Indigo um.

    Beides sind Modulwerte und keine Argumente — sie wirken global, solange
    dieser Prozess läuft. Das ist unkritisch, weil je Prozess genau ein Band
    gebaut wird; wer beide Bände in einem Lauf baut, muss sie zurücksetzen.
    """
    stile.FARBEN["kasten"] = KASTEN_GRUND
    stile.FARBEN["blatt_hell"] = INDIGO_HELL
    build_docx.KASTEN_RAHMEN = KASTEN_RAHMEN


def main():
    cfg = yaml.safe_load((BAND / "dopamin.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(BAND / "kapitel")
    ziel = BAND / "out" / f"{cfg['slug']}.docx"

    farbwelt_setzen()

    # Durchlauf 1: ohne Verzeichnis, nur um die Seitenzahlen zu erfahren.
    bauen(cfg, kapitel, ziel, stilwerte=TYPOGRAFIE)
    pdf = pdf_erzeugen(ziel)
    toc = seitenzahlen_ermitteln(pdf, kapitel)

    # Durchlauf 2: mit fertigem Verzeichnis.
    bauen(cfg, kapitel, ziel, toc_daten=toc, stilwerte=TYPOGRAFIE)
    pdf = pdf_erzeugen(ziel)

    from pypdf import PdfReader
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        # Dritter Durchlauf mit Vakatseite: KDP verlangt eine gerade
        # Seitenzahl und schöbe sonst selbst ein Blatt ein.
        bauen(cfg, kapitel, ziel, toc_daten=toc, leerseite=True,
              stilwerte=TYPOGRAFIE)
        pdf = pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)

    woerter = sum(len(k["text"].split()) for k in kapitel)
    print(f"{len(kapitel)} Kapitel, {len(toc)} Verzeichniseinträge, "
          f"{woerter} Wörter, {seiten} Seiten")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")

    hardcover_bauen(cfg, kapitel, toc, seiten)


def hardcover_bauen(cfg, kapitel, toc, seiten_taschenbuch):
    """Zweiter Innenteil im Hardcover-Format — 5,5 x 8,5 statt 5 x 8 Zoll.

    KDP führt 5 x 8 Zoll nur als Taschenbuch. Der Satzspiegel ist in beiden
    Fassungen derselbe, die ganze Formatdifferenz liegt in den Rändern
    (siehe dopamin.yaml). Deshalb **muss** die Seitenzahl gleich bleiben —
    weicht sie ab, stimmen die Ränder nicht, und aus der Seitenzahl folgt
    die Rückenbreite des Umschlags.
    """
    hc_format = cfg.get("hardcover_seitenformat")
    if not hc_format:
        return

    from pypdf import PdfReader

    cfg_hc = dict(cfg, seitenformat=hc_format)
    ziel = BAND / "out" / f"{cfg['slug']}-hardcover.docx"
    for leerseite in (False, True):
        bauen(cfg_hc, kapitel, ziel, toc_daten=toc, leerseite=leerseite,
              stilwerte=TYPOGRAFIE)
        pdf = pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)
        if seiten % 2 == 0:
            break

    print(f"\nHardcover-Innenteil: {hc_format['breite_mm']} x "
          f"{hc_format['hoehe_mm']} mm, {seiten} Seiten")
    if seiten != seiten_taschenbuch:
        print(f"  ACHTUNG: {seiten} statt {seiten_taschenbuch} Seiten — der "
              "Satzspiegel weicht ab, Ränder in dopamin.yaml prüfen.")
    if seiten < HARDCOVER_MIN_SEITEN:
        print(f"  ACHTUNG: KDP verlangt für Hardcover mindestens "
              f"{HARDCOVER_MIN_SEITEN} Seiten, es sind {seiten}.")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
