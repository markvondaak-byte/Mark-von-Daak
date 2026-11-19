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

ISBN_MARKER = "{{ISBN}}"

# Schriftgrad des Impressums. Es soll auf eine Seite passen; 8 pt ist in
# Verlagsbüchern für das Impressum üblich und im Druck gut lesbar.
IMPRESSUM_PT = 8.0
IMPRESSUM_ANFANG = "Der Narzisst in meinem Bett\n"
IMPRESSUM_ENDE = "Markenhinweis"


def isbn_einsetzen(kapitel, cfg, ebook=False):
    """Ersetzt {{ISBN}} im Impressum durch die Nummern aus narzisst.yaml.

    Taschenbuch und Hardcover teilen sich einen Innenteil, deshalb stehen
    beide Nummern darin. Ist keine eingetragen — oder ist es das E-Book, das
    statt einer ISBN eine ASIN bekommt —, fällt die Zeile weg.
    """
    isbn = cfg.get("isbn") or {}
    teile = [f"ISBN {isbn[art]} ({name})"
             for art, name in (("taschenbuch", "Taschenbuch"),
                               ("hardcover", "Hardcover"))
             if isbn.get(art)]
    zeile = "" if ebook or not teile else "\\\n".join(teile)
    treffer = 0
    for kap in kapitel:
        if ISBN_MARKER in kap["text"]:
            kap["text"] = kap["text"].replace(
                ISBN_MARKER + "\n\n", zeile + "\n\n" if zeile else "")
            treffer += 1
    if treffer != 1:
        raise SystemExit("{{ISBN}} im Impressum nicht gefunden.")
    return bool(zeile)


def impressum_verkleinern(docx_pfad):
    """Setzt das Impressum in kleinerer Schrift, damit es auf eine Seite passt.

    Bewusst hier und nicht in buch/build/stile.py: Die Absatzformate dort
    gelten für alle Bände.
    """
    from docx import Document
    from docx.shared import Pt

    doc = Document(str(docx_pfad))
    im_impressum = False
    for absatz in doc.paragraphs:
        if absatz.text.startswith(IMPRESSUM_ANFANG):
            im_impressum = True
        if not im_impressum:
            continue
        for lauf in absatz.runs:
            lauf.font.size = Pt(IMPRESSUM_PT)
        absatz.paragraph_format.space_after = Pt(3.5)
        absatz.paragraph_format.space_before = Pt(0)
        absatz.paragraph_format.line_spacing = 1.08
        if absatz.text.startswith(IMPRESSUM_ENDE):
            break
    else:
        raise SystemExit("Ende des Impressums nicht gefunden.")
    doc.save(str(docx_pfad))


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
    impressum_verkleinern(ziel)
    return pdf_erzeugen(ziel)


def main():
    from pypdf import PdfReader

    cfg = yaml.safe_load((BAND / "narzisst.yaml").read_text(encoding="utf-8"))
    kapitel = kapitel_laden(BAND / "kapitel")
    mit_isbn = isbn_einsetzen(kapitel, cfg)
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

    if not mit_isbn:
        print("Hinweis: keine ISBN in narzisst.yaml — Zeile im Impressum "
              "ausgelassen.")
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
