#!/usr/bin/env python3
"""Baut Band 3 — das Rezeptbuch.

    python3 rezepte/build/build_rezepte.py

Rezepte liegen strukturiert als YAML in rezepte/rezepte/*.yaml, nicht als
Fließtext. Das hat zwei Gründe: Das Layout bleibt über alle 72 Rezepte
identisch, und `zutaten_check.py` kann jede Zutat gegen die Regeln der Phase
prüfen, in der das Rezept stehen soll.

Rahmentexte (Titelei, Grundlagen, Anhang) sind Markdown in rezepte/rahmen/
und werden mit demselben Renderer gesetzt wie Band 1 und 2.
"""

import sys
from pathlib import Path

import yaml
from docx.shared import Mm, Pt

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import stile  # noqa: E402
from build_docx import Renderer, kapitel_laden, pdf_erzeugen  # noqa: E402

# Anzeige der Tagesfarbe im Rezeptkopf
FARBMARKE = {
    "weiss": ("WEISSER TAG", "9A9A9A"),
    "gruen": ("GRÜNER TAG", "6FA85E"),
    "stabilisierung": ("AB STABILISIERUNG", "C9A227"),
    "grundrezept": ("GRUNDREZEPT", "7A8A99"),
    "fruehstueck": ("FRÜHSTÜCK", "8FA85E"),
}


def rezept_stile(doc):
    """Absatzformate der Rezepte.

    Die Größen sind auf 8 × 10 Zoll ausgelegt. Bei 6 × 9 standen hier
    9,5 pt — auf der breiteren Seite ergab das 110 Zeichen je Zeile. Gut
    lesbar sind 60 bis 75; ab etwa 90 verliert das Auge beim Zeilenwechsel
    den Anschluss und springt in dieselbe Zeile zurück. In einem Kochbuch,
    das man im Stehen und aus einem Meter Entfernung liest, wiegt das
    doppelt.

    Korrigiert wird von zwei Seiten: 12,5 pt hier und 42 mm Außensteg in
    rezepte.yaml. Zusammen ergibt das 72 Zeichen im Mittel. Nur an der
    Schrift zu drehen hätte 14,5 pt gebraucht, nur am Rand einen Außensteg
    von 95 mm — beides für sich genommen zu viel.
    """
    stile._stil(doc, "RezeptName", schrift=stile.SANS, groesse=15, fett=True,
                farbe=stile.FARBEN["blatt"], vor=14, nach=1,
                zusammenhalten=True)
    stile._stil(doc, "RezeptMeta", schrift=stile.SANS, groesse=9,
                farbe=stile.FARBEN["gedaempft"], vor=0, nach=7,
                zusammenhalten=True)
    stile._stil(doc, "RezeptRubrik", schrift=stile.SANS, groesse=9.5,
                fett=True, farbe=stile.FARBEN["blatt_hell"], vor=6, nach=2,
                zusammenhalten=True)
    stile._stil(doc, "RezeptZutat", schrift=stile.SERIF, groesse=12.5,
                vor=0, nach=1.5, zeilen=1.10, einzug_links=4)
    stile._stil(doc, "RezeptSchritt", schrift=stile.SERIF, groesse=12.5,
                vor=0, nach=4, zeilen=1.15, einzug_links=6)
    stile._stil(doc, "RezeptTipp", schrift=stile.SERIF, groesse=10.5,
                kursiv=True, farbe=stile.FARBEN["gedaempft"],
                vor=4, nach=2, zeilen=1.12, einzug_links=4)


def rezept_setzen(doc, rezept, textbreite_mm):
    """Setzt ein Rezept. Alle Absätze außer dem letzten bekommen
    keep_with_next, damit Word das Rezept nicht über zwei Seiten reißt."""
    absaetze = []

    kopf = doc.add_paragraph(style="RezeptName")
    kopf.add_run(rezept["name"])
    absaetze.append(kopf)

    marke, farbe = FARBMARKE[rezept["tagesfarbe"]]
    teile = [marke, f"{rezept['portionen']} Portion"
             + ("en" if rezept["portionen"] > 1 else "")]
    if rezept.get("zeit_min"):
        teile.append(f"{rezept['zeit_min']} Min.")
    if rezept.get("eiweiss_g"):
        teile.append(f"ca. {rezept['eiweiss_g']} g Eiweiß")
    meta = doc.add_paragraph(style="RezeptMeta")
    meta.add_run("   ·   ".join(teile))
    stile.rahmen(meta, farbe, staerke=4, seiten=("bottom",))
    absaetze.append(meta)

    rubrik = doc.add_paragraph(style="RezeptRubrik")
    rubrik.add_run("ZUTATEN")
    absaetze.append(rubrik)
    for zutat in rezept["zutaten"]:
        absatz = doc.add_paragraph(style="RezeptZutat")
        absatz.add_run("·  " + zutat)
        absaetze.append(absatz)

    rubrik = doc.add_paragraph(style="RezeptRubrik")
    rubrik.add_run("ZUBEREITUNG")
    absaetze.append(rubrik)
    for nummer, schritt in enumerate(rezept["schritte"], 1):
        absatz = doc.add_paragraph(style="RezeptSchritt")
        absatz.add_run(f"{nummer}.  ").bold = True
        absatz.add_run(schritt)
        absaetze.append(absatz)

    if rezept.get("tipp"):
        absatz = doc.add_paragraph(style="RezeptTipp")
        absatz.add_run("Tipp: ").bold = True
        absatz.add_run(rezept["tipp"])
        absaetze.append(absatz)

    for absatz in absaetze[:-1]:
        absatz.paragraph_format.keep_with_next = True
    absaetze[-1].paragraph_format.keep_with_next = False
    absaetze[-1].paragraph_format.space_after = Pt(11)
    return absaetze


def rezeptdateien_laden(verzeichnis):
    abschnitte = []
    for pfad in sorted(verzeichnis.glob("*.yaml")):
        daten = yaml.safe_load(pfad.read_text(encoding="utf-8"))
        daten["pfad"] = pfad
        abschnitte.append(daten)
    if not abschnitte:
        raise SystemExit(f"Keine Rezeptdateien in {verzeichnis}.")
    return abschnitte


# Eigene Werte statt der Vorgaben aus stile.py, die auf Band 1 ausgemessen
# sind. Zwei Gründe: Auf der breiteren Seite von 8 × 10 Zoll wären 11 pt
# Fließtext zu klein für die Zeilenlänge, und ein Rahmentext in 11 pt neben
# Rezepten in 12,5 pt sieht nach zwei verschiedenen Büchern aus.
TYPOGRAFIE = {
    "Fliesstext": {"groesse": 12, "nach": 7},
    "FliesstextEng": {"groesse": 12},
    "Einzug": {"groesse": 12},
    "Punkt": {"groesse": 12},
    "Nummer": {"groesse": 12},
    "Zitat": {"groesse": 12},
    "KastenText": {"groesse": 10.5},
    "KastenTitel": {"groesse": 11},
    "Abschnitt": {"groesse": 14},
    "TabellenZelle": {"groesse": 10},
    "TabellenKopf": {"groesse": 10},
}


def bauen(cfg, rahmen, abschnitte, ziel, leerseite=False):
    sf = cfg["seitenformat"]
    doc = stile.dokument_anlegen(sf, TYPOGRAFIE)
    rezept_stile(doc)
    breite = sf["breite_mm"] - sf["rand_innen_mm"] - sf["rand_aussen_mm"]
    renderer = Renderer(doc, breite)

    vorne = [k for k in rahmen if k["meta"].get("position", "vorne") == "vorne"]
    hinten = [k for k in rahmen if k["meta"].get("position") == "hinten"]

    # Titelei in römischen Ziffern
    stile.seitenzahlen_format(doc.sections[0], "lowerRoman", neustart_bei=1)
    for nummer, kap in enumerate(vorne):
        if nummer:
            stile.seitenumbruch(doc)
        renderer.rendern(kap["text"],
                         Renderer.LAYOUTS.get(kap["meta"].get("layout")))

    # Rezeptteile
    register = []
    for nummer, abschnitt in enumerate(abschnitte):
        section = stile.neuer_abschnitt(doc, sf)
        if nummer == 0:
            stile.seitenzahlen_format(section, "decimal", neustart_bei=1)
        stile.kopf_und_fusszeile(doc, section, links_text=cfg["titel"],
                                 rechts_text=abschnitt["teil"])

        doc.add_paragraph(style="Kapitel").add_run(abschnitt["teil"])
        if abschnitt.get("einleitung"):
            renderer.rendern(abschnitt["einleitung"])

        for rezept in abschnitt["rezepte"]:
            rezept_setzen(doc, rezept, breite)
            register.append((rezept["name"], abschnitt["teil"]))

    # Anhang
    for kap in hinten:
        section = stile.neuer_abschnitt(doc, sf)
        stile.kopf_und_fusszeile(doc, section, links_text=cfg["titel"],
                                 rechts_text=kap["meta"]["kopfzeile"])
        text = kap["text"]
        if "{{REZEPTREGISTER}}" in text:
            vor, nach = text.split("{{REZEPTREGISTER}}", 1)
            renderer.rendern(vor)
            register_setzen(doc, register, breite)
            renderer.rendern(nach)
        else:
            renderer.rendern(text)

    if leerseite:
        # KDP verlangt eine gerade Seitenzahl und schiebt sonst selbst ein
        # unbeschriftetes Blatt ein. Besser, wir setzen es kontrolliert — und
        # zwar wirklich leer: Ein eigener Abschnitt ohne Kopf- und Fußzeile.
        # Mit Kolumnentitel und Seitenzahl sähe die Seite nach einem Fehler
        # aus statt nach der üblichen Vakatseite am Buchende.
        abschluss = stile.neuer_abschnitt(doc, sf)
        stile.kopf_und_fusszeile(doc, abschluss, links_text="", rechts_text="",
                                 mit_seitenzahl=False)
        doc.add_paragraph(style="Fliesstext")

    ziel.parent.mkdir(parents=True, exist_ok=True)
    doc.save(ziel)
    return ziel, register


def register_setzen(doc, register, breite_mm):
    """Alphabetisches Rezeptregister mit Angabe des Teils."""
    tabelle = doc.add_table(rows=0, cols=2)
    tabelle.autofit = False
    stile.spaltenbreiten(tabelle, [breite_mm * 0.62, breite_mm * 0.38])
    stile.zellenrand(tabelle, oben=0.6, unten=0.6, links=0, rechts=1)
    stile.tabellenraender(tabelle, hexfarbe="E4E4E4", staerke=2)

    for name, teil in sorted(register, key=lambda e: e[0].lower()):
        zeile = tabelle.add_row()
        stile.zeile_zusammenhalten(zeile)
        for zelle, text, stil in ((zeile.cells[0], name, "RezeptZutat"),
                                  (zeile.cells[1], teil, "Klein")):
            absatz = zelle.paragraphs[0]
            for lauf in list(absatz.runs):
                lauf._r.getparent().remove(lauf._r)
            absatz.style = doc.styles[stil]
            absatz.paragraph_format.left_indent = Mm(0)
            absatz.add_run(text)
    doc.add_paragraph(style="FliesstextEng")
    return tabelle


def main():
    basis = WURZEL / "rezepte"
    cfg = yaml.safe_load((basis / "rezepte.yaml").read_text(encoding="utf-8"))
    rahmen = kapitel_laden(basis / "rahmen")
    abschnitte = rezeptdateien_laden(basis / "rezepte")
    ziel = basis / "out" / f"{cfg['slug']}.docx"

    from pypdf import PdfReader

    _, register = bauen(cfg, rahmen, abschnitte, ziel)
    pdf = pdf_erzeugen(ziel)
    seiten = len(PdfReader(str(pdf)).pages)

    if seiten % 2:
        # Zweiter Durchlauf mit Leerseite am Ende, damit die Seitenzahl
        # gerade wird. Erst jetzt möglich — vorher ist sie unbekannt.
        bauen(cfg, rahmen, abschnitte, ziel, leerseite=True)
        pdf = pdf_erzeugen(ziel)
        seiten = len(PdfReader(str(pdf)).pages)

    print(f"{len(abschnitte)} Teile, {len(register)} Rezepte, "
          f"{len(rahmen)} Rahmenkapitel, {seiten} Seiten")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {pdf.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
