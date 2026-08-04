#!/usr/bin/env python3
"""Baut Band 2 — das 12-Wochen-Workbook.

    python3 workbook/build/build_workbook.py

Die 84 Tagesseiten werden aus wochenplan.py erzeugt, nicht von Hand gepflegt.
Rahmentexte (Titelei, Anleitung, Anhang) liegen als Markdown in
workbook/rahmen/ und werden mit demselben Renderer gesetzt wie Band 1.

Aufbau je Woche: ein Wochenauftakt, vier Seiten mit je zwei Tageskarten und
ein Wochenrückblick — also sechs Seiten, zwölfmal.
"""

import sys
from pathlib import Path

import yaml
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import stile  # noqa: E402
import wochenplan as wp  # noqa: E402
from build_docx import Renderer, kapitel_laden, pdf_erzeugen  # noqa: E402

KAESTCHEN = "❑"


# --- zusätzliche Formate für das Workbook ------------------------------------
def workbook_stile(doc):
    mitte = WD_ALIGN_PARAGRAPH.CENTER
    stile._stil(doc, "WocheNummer", schrift=stile.SANS, groesse=11, fett=True,
                farbe=stile.FARBEN["blatt_hell"], vor=0, nach=2)
    stile._stil(doc, "WocheTitel", schrift=stile.SANS, groesse=24, fett=True,
                farbe=stile.FARBEN["blatt"], vor=0, nach=10, zeilen=1.05)
    stile._stil(doc, "TagKopf", schrift=stile.SANS, groesse=12, fett=True,
                farbe=stile.FARBEN["blatt"], vor=0, nach=0)
    stile._stil(doc, "TagFarbe", schrift=stile.SANS, groesse=8, fett=True,
                vor=0, nach=0, ausrichtung=WD_ALIGN_PARAGRAPH.RIGHT)
    stile._stil(doc, "FeldLabel", schrift=stile.SANS, groesse=8,
                farbe=stile.FARBEN["gedaempft"], vor=1, nach=1)
    stile._stil(doc, "FeldZeile", schrift=stile.SERIF, groesse=9,
                vor=3, nach=3)
    stile._stil(doc, "Kaestchen", schrift=stile.SERIF, groesse=11,
                farbe=stile.FARBEN["gedaempft"], vor=1, nach=1)
    stile._stil(doc, "WocheHinweis", schrift=stile.SERIF, groesse=9.5,
                farbe=stile.FARBEN["gedaempft"], vor=0, nach=6, zeilen=1.15)
    stile._stil(doc, "AuftaktMitte", schrift=stile.SANS, groesse=9, fett=True,
                vor=0, nach=0, ausrichtung=mitte)


# --- Bausteine ---------------------------------------------------------------
def _linie(absatz, farbe="C8C8C8"):
    """Unterstrich als Schreiblinie."""
    stile.rahmen(absatz, farbe, staerke=4, seiten=("bottom",))
    return absatz


def _zelle_leeren(zelle):
    absatz = zelle.paragraphs[0]
    for lauf in list(absatz.runs):
        lauf._r.getparent().remove(lauf._r)
    return absatz


def schreibzeilen(doc, anzahl, breite_mm, *, praefix=None, hoehe_pt=11):
    """Mehrere leere Schreiblinien untereinander.

    Als Tabelle und nicht als Absätze mit Unterstrich: Word fasst
    aufeinanderfolgende Absätze mit identischem Rahmen zu einer einzigen Linie
    zusammen — aus acht Zeilen würde sonst ein einziger Strich am Ende.
    """
    tabelle = doc.add_table(rows=anzahl, cols=1)
    tabelle.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabelle.autofit = False
    stile.spaltenbreiten(tabelle, [breite_mm])
    stile.zellenrand(tabelle, oben=0.5, unten=0.5, links=0, rechts=0)
    stile.tabellenraender(tabelle, hexfarbe="FFFFFF", staerke=0)

    for zeile in tabelle.rows:
        stile.zeile_zusammenhalten(zeile)
        zeile.height = Pt(hoehe_pt)
        absatz = _zelle_leeren(zeile.cells[0])
        absatz.style = doc.styles["FeldZeile"]
        if praefix:
            absatz.add_run(praefix)
        _linie(absatz)

    abstand = doc.add_paragraph(style="FliesstextEng")
    abstand.paragraph_format.space_after = Pt(6)
    return tabelle


def tageskarte(doc, tag, breite_mm):
    """Eine Tageskarte — zwei davon passen auf eine A4-Seite."""
    farbe = stile.TAGESFARBEN[tag["farbe"]]
    ist_vorbereitung = tag["farbe"] == wp.VORBEREITUNG
    label_mm = 32
    feld_mm = breite_mm - label_mm

    tabelle = doc.add_table(rows=0, cols=2)
    tabelle.alignment = WD_TABLE_ALIGNMENT.LEFT
    tabelle.autofit = False

    def zeile(label, *, linie=True, stil_inhalt="FeldZeile"):
        r = tabelle.add_row()
        stile.zeile_zusammenhalten(r)
        z1, z2 = r.cells
        a1 = _zelle_leeren(z1)
        a1.style = doc.styles["FeldLabel"]
        a1.add_run(label)
        a2 = _zelle_leeren(z2)
        a2.style = doc.styles[stil_inhalt]
        if linie:
            _linie(a2)
        return a2

    # Kopfzeile: Tagesnummer links, Tagesfarbe rechts
    kopf = tabelle.add_row()
    stile.zeile_zusammenhalten(kopf)
    z1, z2 = kopf.cells
    a1 = _zelle_leeren(z1)
    a1.style = doc.styles["TagKopf"]
    a1.add_run(f"Tag {tag['nummer']}")

    a2 = _zelle_leeren(z2)
    a2.style = doc.styles["TagFarbe"]
    a2.add_run(f"{tag['wochentag']}          ")
    marke = a2.add_run(
        "VORBEREITUNGSTAG" if ist_vorbereitung
        else f"{KAESTCHEN} WEISS    {KAESTCHEN} GRÜN    {KAESTCHEN} ROT"
        if tag["vorschlag"] else farbe["label"])
    marke.bold = True
    if not tag["vorschlag"]:
        stile.schattierung(z2, farbe["fuellung"])

    zeile("Datum")

    if ist_vorbereitung:
        a = zeile("Heute", linie=False, stil_inhalt="Kaestchen")
        a.add_run(f"{KAESTCHEN} gegessen wie gewohnt — noch nichts umgestellt")
    else:
        for nummer in range(1, 5):
            zeile(f"{nummer}. Mahlzeit")

    a = zeile("Wasser  je 250 ml", linie=False, stil_inhalt="Kaestchen")
    a.add_run("    ".join([KAESTCHEN] * 8))

    a = zeile("Nährstoffe", linie=False, stil_inhalt="Kaestchen")
    a.add_run(f"{KAESTCHEN} morgens     {KAESTCHEN} mittags     "
              f"{KAESTCHEN} abends     {KAESTCHEN} Joghurt")

    a = zeile("Bewegung", linie=True)
    a = zeile("Schlaf / Befinden", linie=True)
    a.add_run("Stunden:                    Befinden 1–10:")

    zeile("Notiz")

    stile.spaltenbreiten(tabelle, [label_mm, feld_mm])
    stile.zellenrand(tabelle, oben=0.8, unten=0.8, links=1.2, rechts=1.2)
    stile.tabellenraender(tabelle, hexfarbe="FFFFFF", staerke=0)
    _kartenrahmen(tabelle, farbe["rahmen"])

    abstand = doc.add_paragraph(style="FliesstextEng")
    abstand.paragraph_format.space_after = Pt(12)
    return tabelle


def _kartenrahmen(tabelle, hexfarbe):
    """Dünner Rahmen außen um die Karte, innen keine Linien."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tbl_pr = tabelle._tbl.tblPr
    for alt in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(alt)
    borders = OxmlElement("w:tblBorders")
    for kante, farbe, staerke in (
            ("top", hexfarbe, 8), ("left", hexfarbe, 8),
            ("bottom", hexfarbe, 8), ("right", hexfarbe, 8),
            ("insideH", "FFFFFF", 0), ("insideV", "FFFFFF", 0)):
        linie = OxmlElement(f"w:{kante}")
        linie.set(qn("w:val"), "single" if staerke else "none")
        linie.set(qn("w:sz"), str(staerke))
        linie.set(qn("w:space"), "0")
        linie.set(qn("w:color"), farbe)
        borders.append(linie)
    tbl_pr.append(borders)


def wochenauftakt(doc, woche, breite_mm):
    doc.add_paragraph(style="WocheNummer").add_run(
        f"WOCHE {woche['nummer']} VON 12   ·   {woche['phase_name'].upper()}")
    doc.add_paragraph(style="WocheTitel").add_run(woche["fokus_titel"])
    doc.add_paragraph(style="WocheHinweis").add_run(woche["fokus_text"])

    # Farbverteilung der Woche
    doc.add_paragraph(style="Abschnitt").add_run("Deine Woche")
    tabelle = doc.add_table(rows=2, cols=7)
    tabelle.autofit = False
    stile.tabellenraender(tabelle)
    stile.spaltenbreiten(tabelle, [breite_mm / 7] * 7)
    for spalte, tag in enumerate(woche["tage"]):
        farbe = stile.TAGESFARBEN[tag["farbe"]]
        oben = tabelle.rows[0].cells[spalte]
        unten = tabelle.rows[1].cells[spalte]

        a = _zelle_leeren(oben)
        a.style = doc.styles["AuftaktMitte"]
        a.add_run(tag["wochentag"][:2])

        a = _zelle_leeren(unten)
        a.style = doc.styles["AuftaktMitte"]
        a.add_run("?" if tag["vorschlag"] else farbe["label"][:1]
                  if tag["farbe"] != wp.VORBEREITUNG else "–")
        stile.schattierung(unten, farbe["fuellung"])

    doc.add_paragraph(style="FliesstextEng")
    if woche["vorschlag"]:
        doc.add_paragraph(style="WocheHinweis").add_run(
            "Ab der Stabilisierungsphase legst du die Tagesfarben selbst fest. "
            "Die Regel: grün als Basis, ein bis zwei rote Tage, und auf jeden "
            "roten Tag folgt ein weißer. Trag deine Planung oben ein.")

    # Die Zeilenzahlen sind so bemessen, dass der Wochenauftakt auf eine Seite
    # passt — auch in den Wochen ab 7, in denen der Hinweis zur eigenen
    # Farbwahl darübersteht. Vorher liefen zwei bis drei Schreiblinien über und
    # standen allein auf der Folgeseite: dreizehn Seiten im Heft, die nichts
    # trugen als eine übrig gebliebene Linie.
    einkaufszeilen = 9 if woche["vorschlag"] else 11

    doc.add_paragraph(style="Abschnitt").add_run("Einkauf für diese Woche")
    schreibzeilen(doc, einkaufszeilen, breite_mm, praefix=f"{KAESTCHEN}   ")

    doc.add_paragraph(style="Abschnitt").add_run("Mein Vorsatz für diese Woche")
    schreibzeilen(doc, 2, breite_mm)

    doc.add_paragraph(style="Abschnitt").add_run("Notizen")
    schreibzeilen(doc, 2, breite_mm)
    stile.seitenumbruch(doc)


def wochenrueckblick(doc, woche, breite_mm):
    doc.add_paragraph(style="WocheNummer").add_run(
        f"RÜCKBLICK AUF WOCHE {woche['nummer']}")
    doc.add_paragraph(style="WocheTitel").add_run("Was diese Woche gebracht hat")

    doc.add_paragraph(style="Abschnitt").add_run("Deine Werte")
    tabelle = doc.add_table(rows=6, cols=2)
    tabelle.autofit = False
    stile.tabellenraender(tabelle)
    stile.spaltenbreiten(tabelle, [55, 105])
    felder = ["Datum", "Gewicht (kg)", "Taille (cm)", "Bauch (cm)",
              "Hüfte (cm)", "Befinden 1–10"]
    for nummer, feld in enumerate(felder):
        zeile = tabelle.rows[nummer]
        stile.zeile_zusammenhalten(zeile)
        z1, z2 = zeile.cells
        a = _zelle_leeren(z1)
        a.style = doc.styles["FeldLabel"]
        a.add_run(feld)
        a = _zelle_leeren(z2)
        a.style = doc.styles["FeldZeile"]

    for titel, anzahl in [
        ("Was gut lief", 5),
        ("Was schwerfiel", 5),
        ("Das nehme ich in die nächste Woche mit", 4),
    ]:
        doc.add_paragraph(style="Abschnitt").add_run(titel)
        schreibzeilen(doc, anzahl, breite_mm)

    stile.seitenumbruch(doc)


def woche_bauen(doc, woche, breite_mm):
    wochenauftakt(doc, woche, breite_mm)
    for index, tag in enumerate(woche["tage"]):
        tageskarte(doc, tag, breite_mm)
        # Nach jeder zweiten Karte eine neue Seite.
        if index % 2 == 1 and index < len(woche["tage"]) - 1:
            stile.seitenumbruch(doc)
    stile.seitenumbruch(doc)
    wochenrueckblick(doc, woche, breite_mm)


# --- Zusammenbau -------------------------------------------------------------
def bauen(cfg, rahmen, ziel):
    sf = cfg["seitenformat"]
    doc = stile.dokument_anlegen(sf)
    workbook_stile(doc)
    breite = sf["breite_mm"] - sf["rand_innen_mm"] - sf["rand_aussen_mm"]
    renderer = Renderer(doc, breite)

    vorne = [k for k in rahmen if k["meta"].get("position", "vorne") == "vorne"]
    hinten = [k for k in rahmen if k["meta"].get("position") == "hinten"]

    # Titelei
    stile.seitenzahlen_format(doc.sections[0], "lowerRoman", neustart_bei=1)
    for nummer, kap in enumerate(vorne):
        if nummer:
            stile.seitenumbruch(doc)
        layout = Renderer.LAYOUTS.get(kap["meta"].get("layout"))
        renderer.rendern(kap["text"], layout)

    # Zwölf Wochen
    section = stile.neuer_abschnitt(doc, sf)
    stile.seitenzahlen_format(section, "decimal", neustart_bei=1)
    stile.kopf_und_fusszeile(doc, section, links_text=cfg["titel"],
                             rechts_text=cfg["untertitel"])
    for woche in wp.wochen():
        woche_bauen(doc, woche, breite)

    # Anhang
    for kap in hinten:
        section = stile.neuer_abschnitt(doc, sf)
        stile.kopf_und_fusszeile(doc, section, links_text=cfg["titel"],
                                 rechts_text=kap["meta"]["kopfzeile"])
        renderer.rendern(kap["text"],
                         Renderer.LAYOUTS.get(kap["meta"].get("layout")))

    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc.save(ziel)
    return ziel


def main():
    basis = WURZEL / "workbook"
    cfg = yaml.safe_load((basis / "workbook.yaml").read_text(encoding="utf-8"))
    rahmen = kapitel_laden(basis / "rahmen")
    ziel = basis / "out" / f"{cfg['slug']}.docx"

    bauen(cfg, rahmen, ziel)
    pdf = pdf_erzeugen(ziel)

    from pypdf import PdfReader
    seiten = len(PdfReader(str(pdf)).pages)
    print(f"12 Wochen, 84 Tageskarten, {len(rahmen)} Rahmenkapitel, "
          f"{seiten} Seiten")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
