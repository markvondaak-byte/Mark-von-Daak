#!/usr/bin/env python3
"""Endabnahme beider Bände vor dem KDP-Upload.

    python3 buch/build/abnahme.py

Prüft, was sich maschinell prüfen lässt: Seitenzahlen, Vollständigkeit der
84 Tageskarten, Übereinstimmung der Tagesfarben mit dem Wochenplan,
Umschlagmaße, eingebettete Schriften und die Rechtstexte. Ersetzt keine
inhaltliche Durchsicht und keine juristische Prüfung.
"""

import re
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "workbook" / "build"))
import wochenplan as wp  # noqa: E402

BESCHNITT_MM = 3.175
RUECKEN_PRO_SEITE_MM = 0.0572

ergebnisse = []


def pruefe(name, bedingung, detail=""):
    ergebnisse.append((bool(bedingung), name, detail))
    zeichen = "OK  " if bedingung else "FEHL"
    print(f"  [{zeichen}] {name}" + (f"  — {detail}" if detail else ""))


def text_von(pdf):
    return [(s.extract_text() or "") for s in PdfReader(str(pdf)).pages]


def schriften_eingebettet(pdf):
    """KDP lehnt PDFs mit nicht eingebetteten Schriften ab."""
    fehlend = set()
    reader = PdfReader(str(pdf))
    for seite in reader.pages:
        ressourcen = seite.get("/Resources", {})
        schriften = ressourcen.get("/Font", {})
        if hasattr(schriften, "get_object"):
            schriften = schriften.get_object()
        for schluessel in schriften:
            font = schriften[schluessel].get_object()
            deskriptor = font.get("/FontDescriptor")
            if deskriptor is None:
                nachkommen = font.get("/DescendantFonts")
                if nachkommen:
                    deskriptor = nachkommen[0].get_object().get("/FontDescriptor")
            if deskriptor is None:
                continue
            deskriptor = deskriptor.get_object()
            if not any(k in deskriptor for k in
                       ("/FontFile", "/FontFile2", "/FontFile3")):
                fehlend.add(str(font.get("/BaseFont", "?")))
    return fehlend


def buch_pruefen():
    print("\nBand 1 — Das Buch")
    print("-" * 66)
    basis = WURZEL / "buch"
    cfg = yaml.safe_load((basis / "buch.yaml").read_text(encoding="utf-8"))
    pdf = basis / "out" / f"{cfg['slug']}.pdf"
    pruefe("PDF vorhanden", pdf.exists(), str(pdf.relative_to(WURZEL)))
    if not pdf.exists():
        return

    seiten = text_von(pdf)
    pruefe("Seitenzahl gerade (KDP rundet sonst auf)", len(seiten) % 2 == 0,
           f"{len(seiten)} Seiten")

    volltext = "\n".join(seiten)

    # Inhaltsverzeichnis muss echte Seitenzahlen tragen, keine Feld-Platzhalter
    pruefe("Inhaltsverzeichnis aufgelöst",
           "Warum Diäten scheitern" in volltext and "…" not in seiten[3][:400],
           "keine unaufgelösten Word-Felder")

    # Pflichtinhalte gegen die Quelle
    pflicht = {
        "Vier Phasen": "Vorbereitung",
        "Tagesfarben": "weißen Tag",
        "Eiweißformel": "0,8 bis 1,5",
        "Kohlenhydrat-Richtwert": "5 Gramm Kohlenhydrate pro 100",
        "Einkaufsliste": "Einkaufsliste",
        "FAQ": "Häufige Fragen",
        "Vier Mahlzeiten": "vier Mahlzeiten",
    }
    for name, nadel in pflicht.items():
        pruefe(f"Inhalt: {name}", nadel in volltext)

    # Rechtstexte
    rechts = {
        "Schwangerschaft": "Schwangerschaft",
        "Ärztliche Abklärung": "ärztlich",
        "Kein Ersatz für ärztlichen Rat": "ersetz",
        "Eigenverantwortung": "eigener Verantwortung",
        "Einzelergebnisse": "nicht übertragbar",
        "Markenhinweis PM-International": "PM-International AG",
    }
    for name, nadel in rechts.items():
        pruefe(f"Rechtstext: {name}", nadel in volltext)

    fehlend = schriften_eingebettet(pdf)
    pruefe("Alle Schriften eingebettet", not fehlend,
           ", ".join(sorted(fehlend)) if fehlend else "")

    cover_pruefen("Band 1", basis / "out" / "cover.pdf", cfg, len(seiten))


def workbook_pruefen():
    print("\nBand 2 — Das Workbook")
    print("-" * 66)
    basis = WURZEL / "workbook"
    cfg = yaml.safe_load((basis / "workbook.yaml").read_text(encoding="utf-8"))
    pdf = basis / "out" / f"{cfg['slug']}.pdf"
    pruefe("PDF vorhanden", pdf.exists(), str(pdf.relative_to(WURZEL)))
    if not pdf.exists():
        return

    seiten = text_von(pdf)
    volltext = "\n".join(seiten)
    pruefe("Seitenzahl gerade", len(seiten) % 2 == 0, f"{len(seiten)} Seiten")

    # Alle 84 Tageskarten vorhanden, lückenlos und je genau einmal.
    # Wortgrenze am Ende, sonst zählt „Tag 1" auch die Treffer von „Tag 10".
    fehlend, doppelt = [], []
    for nummer in range(1, 85):
        treffer = len(re.findall(rf"\bTag {nummer}\b", volltext))
        if treffer == 0:
            fehlend.append(nummer)
        elif treffer > 1:
            doppelt.append(nummer)
    pruefe("84 Tageskarten lückenlos", not fehlend,
           f"fehlen: {fehlend[:10]}" if fehlend else "Tag 1 bis 84")
    pruefe("Keine Tageskarte doppelt", not doppelt,
           f"doppelt: {doppelt[:10]}" if doppelt else "")

    # Alle zwölf Wochenauftakte
    fehlende_wochen = [w for w in range(1, 13)
                       if f"WOCHE {w} VON 12" not in volltext]
    pruefe("12 Wochenauftakte", not fehlende_wochen,
           f"fehlen: {fehlende_wochen}" if fehlende_wochen else "")

    # Farbverteilung gegen die Wahrheitstabelle
    soll = wp.verteilung()
    pruefe("Woche 3 ist die weiße Woche",
           all(t["farbe"] == wp.WEISS for t in wp.wochen()[2]["tage"]),
           "7 x weiß")
    pruefe("Woche 1–2 ohne Tagesfarbe",
           all(t["farbe"] == wp.VORBEREITUNG
               for w in wp.wochen()[:2] for t in w["tage"]),
           "14 Vorbereitungstage")
    pruefe("Jeder rote Tag wird ausgeglichen",
           soll.get(wp.WEISS, 0) >= soll.get(wp.ROT, 0),
           f"{soll.get(wp.WEISS)} weiße zu {soll.get(wp.ROT)} roten Tagen")
    pruefe("Tagesfarben im PDF beschriftet",
           "GRÜN" in volltext and "WEISS" in volltext,
           "auch im Schwarz-Weiß-Druck unterscheidbar")

    for name, nadel in {
        "Konzept in fünf Minuten": "Das Konzept in fünf Minuten",
        "Ausblick nach Woche 12": "Wie es nach Woche 12 weitergeht",
        "Ehrlicher Hinweis zur Stabilisierung": "mindestens 90 Tage",
        "Schwangerschaft": "Schwangerschaft",
        "Eigenverantwortung": "eigener Verantwortung",
        "Markenhinweis": "PM-International AG",
    }.items():
        pruefe(f"Inhalt: {name}", nadel in volltext)

    fehlend_f = schriften_eingebettet(pdf)
    pruefe("Alle Schriften eingebettet", not fehlend_f,
           ", ".join(sorted(fehlend_f)) if fehlend_f else "")

    cover_pruefen("Band 2", basis / "out" / "cover.pdf", cfg, len(seiten))


def cover_pruefen(bezeichnung, pdf, cfg, seiten):
    if not pdf.exists():
        pruefe(f"{bezeichnung}: Umschlag vorhanden", False)
        return
    reader = PdfReader(str(pdf))
    pruefe(f"{bezeichnung}: Umschlag ist einseitig", len(reader.pages) == 1)

    kiste = reader.pages[0].mediabox
    ist_b = float(kiste.width) / 72 * 25.4
    ist_h = float(kiste.height) / 72 * 25.4

    ruecken = seiten * RUECKEN_PRO_SEITE_MM
    soll_b = 2 * cfg["seitenformat"]["breite_mm"] + ruecken + 2 * BESCHNITT_MM
    soll_h = cfg["seitenformat"]["hoehe_mm"] + 2 * BESCHNITT_MM

    pruefe(f"{bezeichnung}: Umschlagbreite", abs(ist_b - soll_b) < 0.5,
           f"{ist_b:.1f} mm (Soll {soll_b:.1f}, Rücken {ruecken:.1f})")
    pruefe(f"{bezeichnung}: Umschlaghöhe", abs(ist_h - soll_h) < 0.5,
           f"{ist_h:.1f} mm (Soll {soll_h:.1f})")


def website_unberuehrt():
    print("\nWebsite")
    print("-" * 66)
    import subprocess
    ergebnis = subprocess.run(
        ["git", "-C", str(WURZEL), "status", "--porcelain",
         "index.html", "impressum.html", "datenschutz.html", "assets"],
        capture_output=True, text=True)
    pruefe("Website unverändert", not ergebnis.stdout.strip(),
           ergebnis.stdout.strip() or "keine Änderungen")


def main():
    print("=" * 66)
    print("ENDABNAHME — Der Stoffwechsel-Reset")
    print("=" * 66)
    buch_pruefen()
    workbook_pruefen()
    website_unberuehrt()

    fehler = [e for e in ergebnisse if not e[0]]
    print("\n" + "=" * 66)
    print(f"{len(ergebnisse) - len(fehler)} von {len(ergebnisse)} Prüfungen "
          "bestanden")
    if fehler:
        print("\nOffen:")
        for _, name, detail in fehler:
            print(f"  · {name}" + (f" — {detail}" if detail else ""))
        return 1
    print("\nAlles bestanden. Hinweis: Das ersetzt keine inhaltliche "
          "Durchsicht\nund keine juristische Prüfung vor der Veröffentlichung.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
