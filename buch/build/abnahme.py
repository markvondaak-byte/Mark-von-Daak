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


# Quellen je Band: Ändert sich hier etwas, ist das PDF daneben veraltet.
# buch/build zählt überall mit, weil dort die gemeinsamen Absatzformate
# liegen — genau darüber ist das Workbook einmal unbemerkt von 88 auf 103
# Seiten gewachsen, während die Abnahme das alte PDF geprüft und
# durchgewinkt hat.
QUELLEN = {
    "buch": ["buch/buch.yaml", "buch/kapitel", "buch/build"],
    "workbook": ["workbook/workbook.yaml", "workbook/rahmen",
                 "workbook/build", "buch/build"],
    "rezepte": ["rezepte/rezepte.yaml", "rezepte/rezepte", "rezepte/rahmen",
                "rezepte/build", "buch/build"],
}

# Prüfer und Nachbearbeitung stehen zwar in denselben Verzeichnissen, gehen
# aber nicht in den Innenteil ein. Ohne diese Ausnahme meldet die Prüfung
# sich selbst als Grund, neu zu bauen.
KEINE_QUELLE = {"abnahme.py", "claim_check.py", "zutaten_check.py",
                "cover_flach.py", "innenteil_druck.py", "build_cover.py",
                "illustration.py", "build_epub.py", "kindle_cover.py"}


def aktueller_als_quellen(bezeichnung, pdf, band):
    """Meldet Quelldateien, die jünger sind als das gebaute PDF.

    Ohne diese Prüfung sagt die Abnahme nur, dass irgendein früher gebautes
    PDF in Ordnung war — nicht, dass das aktuelle es ist.
    """
    stand = pdf.stat().st_mtime
    juenger = []
    for eintrag in QUELLEN[band]:
        pfad = WURZEL / eintrag
        dateien = ([pfad] if pfad.is_file()
                   else [d for d in pfad.rglob("*") if d.is_file()])
        juenger += [d.relative_to(WURZEL) for d in dateien
                    if d.name not in KEINE_QUELLE
                    and "__pycache__" not in d.parts
                    and d.stat().st_mtime > stand]
    pruefe(f"{bezeichnung}: PDF ist auf dem Stand der Quellen", not juenger,
           f"neuer als das PDF: {', '.join(str(d) for d in sorted(juenger)[:3])}"
           if juenger else "")


def fast_leere_seiten(seiten, mindestzeichen=60):
    """Seiten, die außer Kolumnentitel und Seitenzahl nichts tragen.

    Im Workbook liefen die Wochenauftakte um zwei bis drei Schreiblinien über;
    die standen dann allein auf der Folgeseite. Dreizehn solcher Seiten waren
    im Heft, bevor das hier geprüft wurde — im PDF-Schnelldurchlauf fallen sie
    kaum auf, im gedruckten Buch sofort.

    Schreiblinien sind Tabellenränder und liefern keinen Text; eine Seite mit
    Linien zum Ausfüllen trägt trotzdem immer eine Überschrift darüber.

    Eine vollständig leere letzte Seite ist erlaubt: Das ist die Vakatseite,
    mit der die Seitenzahl auf gerade aufgeht. Sie trägt bewusst weder
    Kolumnentitel noch Seitenzahl — eine Seite mit nur diesen beiden sähe
    dagegen nach einem Satzfehler aus und wird deshalb gemeldet.
    """
    zu_leer = []
    for nummer, text in enumerate(seiten, 1):
        knapp = " ".join((text or "").split())
        if nummer == len(seiten) and not knapp:
            continue
        if len(knapp) < mindestzeichen:
            zu_leer.append(nummer)
    return zu_leer


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
    aktueller_als_quellen("Band 1", pdf, "buch")

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

    zu_leer = fast_leere_seiten(seiten)
    pruefe("Keine fast leeren Seiten", not zu_leer,
           f"Seiten {zu_leer}" if zu_leer else "")

    innenteil_druck_pruefen("Band 1", pdf.with_name(pdf.stem + "-druck.pdf"),
                            cfg["seitenformat"]["breite_mm"],
                            cfg["seitenformat"]["hoehe_mm"])
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

    aktueller_als_quellen("Band 2", pdf, "workbook")

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

    zu_leer = fast_leere_seiten(seiten)
    pruefe("Keine fast leeren Seiten", not zu_leer,
           f"Seiten {zu_leer}" if zu_leer else "")

    innenteil_druck_pruefen("Band 2", pdf.with_name(pdf.stem + "-druck.pdf"),
                            cfg["seitenformat"]["breite_mm"],
                            cfg["seitenformat"]["hoehe_mm"])
    cover_pruefen("Band 2", basis / "out" / "cover.pdf", cfg, len(seiten))


def innenteil_druck_pruefen(bezeichnung, pdf, breite_mm, hoehe_mm):
    """Die Innenteil-Datei, die tatsächlich zu KDP hochgeladen wird.

    LibreOffice exportiert 6x9 Zoll nicht maßhaltig: Aus 228,6 mm Höhe werden
    229,01 mm. Schon ein leeres Dokument mit derselben Seitengröße kommt so
    heraus, A4 dagegen stimmt. KDP prüft die Seitengröße gegen die gewählte
    Trimmgröße — deshalb setzt innenteil_druck.py die Seitenbox gerade.
    """
    if not pdf.exists():
        pruefe(f"{bezeichnung}: Druckfassung des Innenteils vorhanden", False,
               "innenteil_druck.py laufen lassen")
        return

    reader = PdfReader(str(pdf))
    masse = {(round(float(s.mediabox.width) / 72 * 25.4, 2),
              round(float(s.mediabox.height) / 72 * 25.4, 2))
             for s in reader.pages}
    stimmt = (len(masse) == 1
              and abs(list(masse)[0][0] - breite_mm) < 0.05
              and abs(list(masse)[0][1] - hoehe_mm) < 0.05)
    pruefe(f"{bezeichnung}: Innenteil hat exakt die Trimmgröße", stimmt,
           " / ".join(f"{b} x {h} mm" for b, h in sorted(masse)))

    fehlend = schriften_eingebettet(pdf)
    pruefe(f"{bezeichnung}: Druckfassung mit allen Schriften", not fehlend,
           ", ".join(sorted(fehlend)) if fehlend else "")


def druckfassung_pruefen(bezeichnung, pdf, soll_b, soll_h):
    """Die Datei, die tatsächlich zu KDP hochgeladen wird.

    Die Vektorfassung des Umschlags enthält Radialverläufe und transparente
    Schlagschatten. Am Bildschirm ist das die bessere Datei — beim Upload
    wurde sie abgelehnt: KDP verlangt reduzierte Ebenen ohne Transparenz.
    `cover_flach.py` rastert sie deshalb bei 300 dpi.

    Hier wird geprüft, dass in der Druckfassung wirklich nichts davon übrig
    ist. Der erste Versuch hatte noch eine nicht eingebettete Helvetica aus
    dem Seitenvorspann des PDF-Erzeugers darin — dieselbe Ursache, anderer
    Auslöser.
    """
    if not pdf.exists():
        pruefe(f"{bezeichnung}: Druckfassung des Umschlags vorhanden", False,
               "cover_flach.py laufen lassen")
        return

    reader = PdfReader(str(pdf))
    seite = reader.pages[0]
    kiste = seite.mediabox
    ist_b = float(kiste.width) / 72 * 25.4
    ist_h = float(kiste.height) / 72 * 25.4
    pruefe(f"{bezeichnung}: Druckfassung hat die Umschlagmaße",
           len(reader.pages) == 1
           and abs(ist_b - soll_b) < 0.5 and abs(ist_h - soll_h) < 0.5,
           f"{ist_b:.1f} x {ist_h:.1f} mm")

    res = seite.get("/Resources", {})
    if hasattr(res, "get_object"):
        res = res.get_object()

    befunde = []
    zustand = res.get("/ExtGState")
    if zustand:
        for schluessel in zustand.get_object():
            eintrag = zustand.get_object()[schluessel].get_object()
            if any(feld in eintrag and float(eintrag[feld]) < 1.0
                   for feld in ("/ca", "/CA")):
                befunde.append("Transparenz")
                break
    if res.get("/Shading"):
        befunde.append("Verläufe")
    if res.get("/Font"):
        befunde.append("Schriften")
    if res.get("/Pattern"):
        befunde.append("Muster")

    pruefe(f"{bezeichnung}: Druckfassung ohne Transparenz und Verläufe",
           not befunde, ", ".join(befunde) if befunde else "")


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

    druckfassung_pruefen(bezeichnung, pdf.with_name("cover-druck.pdf"),
                         soll_b, soll_h)

    # Auch der Umschlag muss alle Schriften mitbringen. reportlab schreibt
    # sonst einen Seitenvorspann mit Helvetica in die Ressourcen — er setzt
    # kein Zeichen, steht aber als nicht eingebettete Schrift in der Datei.
    fehlend = schriften_eingebettet(pdf)
    pruefe(f"{bezeichnung}: Umschlagschriften eingebettet", not fehlend,
           ", ".join(fehlend) if fehlend else "")


def rezeptbuch_pruefen():
    print("\nBand 3 — Das Rezeptbuch")
    print("-" * 66)
    basis = WURZEL / "rezepte"
    cfg = yaml.safe_load((basis / "rezepte.yaml").read_text(encoding="utf-8"))
    pdf = basis / "out" / f"{cfg['slug']}.pdf"
    pruefe("PDF vorhanden", pdf.exists(), str(pdf.relative_to(WURZEL)))
    if not pdf.exists():
        return

    aktueller_als_quellen("Band 3", pdf, "rezepte")

    seiten = text_von(pdf)
    volltext = "\n".join(seiten)
    pruefe("Seitenzahl gerade", len(seiten) % 2 == 0, f"{len(seiten)} Seiten")

    # Rezepte zählen und mit der Zahl im Untertitel abgleichen
    rezepte, namen = [], []
    for quelle in sorted((basis / "rezepte").glob("*.yaml")):
        daten = yaml.safe_load(quelle.read_text(encoding="utf-8"))
        for rezept in daten.get("rezepte", []):
            rezepte.append(rezept)
            namen.append(rezept["name"])

    behauptet = re.search(r"(\d+)\s+Gerichte", cfg["untertitel"])
    pruefe("Rezeptzahl im Untertitel stimmt",
           behauptet and int(behauptet.group(1)) == len(rezepte),
           f"Untertitel nennt {behauptet.group(1) if behauptet else '?'}, "
           f"tatsächlich {len(rezepte)}")

    doppelt = {n for n in namen if namen.count(n) > 1}
    pruefe("Keine doppelten Rezeptnamen", not doppelt,
           ", ".join(sorted(doppelt)) if doppelt else f"{len(namen)} Rezepte")

    fehlend = [n for n in namen if n.split(" mit ")[0][:28] not in volltext]
    pruefe("Alle Rezepte im PDF gesetzt", not fehlend,
           f"fehlen: {fehlend[:5]}" if fehlend else "")

    pruefe("Rezeptregister vorhanden", "Rezeptregister" in volltext)
    pruefe("Kapitel „Kochen im Konzept“", "Kochen im Konzept" in volltext)

    for name, nadel in {
        "Schwangerschaft": "Schwangerschaft",
        "Eigenverantwortung": "eigener Verantwortung",
        "Allergiehinweis": "Allergie",
        "Lebensmittelsicherheit": "durchgaren",
        "Markenhinweis": "PM-International AG",
    }.items():
        pruefe(f"Rechtstext: {name}", nadel in volltext)

    fehlend_f = schriften_eingebettet(pdf)
    pruefe("Alle Schriften eingebettet", not fehlend_f,
           ", ".join(sorted(fehlend_f)) if fehlend_f else "")

    zu_leer = fast_leere_seiten(seiten)
    pruefe("Keine fast leeren Seiten", not zu_leer,
           f"Seiten {zu_leer}" if zu_leer else "")

    innenteil_druck_pruefen("Band 3", pdf.with_name(pdf.stem + "-druck.pdf"),
                            cfg["seitenformat"]["breite_mm"],
                            cfg["seitenformat"]["hoehe_mm"])
    cover_pruefen("Band 3", basis / "out" / "cover.pdf", cfg, len(seiten))


def kindle_pruefen():
    """Die E-Book-Ausgaben — andere Dateien, andere Vorgaben als der Druck."""
    import zipfile

    print("\nKindle-Ausgaben")
    print("-" * 66)

    sys.path.insert(0, str(WURZEL / "buch" / "build"))
    import build_epub
    import kindle_cover

    baende = [
        ("Band 1", "buch/out/stoffwechsel-reset-kindle.epub",
         "buch/out/kindle-cover.jpg", None),
        ("Band 2", "workbook/out/workbook-kindle.epub",
         "workbook/out/kindle-cover.jpg", "workbook/out/workbook.pdf"),
    ]

    for name, epub_pfad, bild_pfad, druck_pfad in baende:
        epub = WURZEL / epub_pfad
        bild = WURZEL / bild_pfad
        pruefe(f"{name}: EPUB vorhanden", epub.exists(), epub_pfad)
        pruefe(f"{name}: Titelbild vorhanden", bild.exists(), bild_pfad)
        if not (epub.exists() and bild.exists()):
            continue

        befunde = build_epub.pruefen(epub)
        pruefe(f"{name}: EPUB-Struktur", not befunde, "; ".join(befunde))

        befunde = kindle_cover.pruefen(bild)
        pruefe(f"{name}: Titelbild nach Amazons Vorgaben", not befunde,
               "; ".join(befunde))

        with zipfile.ZipFile(epub) as archiv:
            namen = archiv.namelist()
            opf = archiv.read("OEBPS/inhalt.opf").decode("utf-8")
            volltext = "\n".join(
                archiv.read(n).decode("utf-8") for n in namen
                if n.endswith(".xhtml"))

        # Ein Kindle-Buch ohne Navigation ist bei KDP ein Ablehnungsgrund.
        punkte = len(re.findall(r"<navPoint ", archiv_lesen(epub, "OEBPS/toc.ncx")))
        pruefe(f"{name}: Navigationspunkte vorhanden", punkte >= 5,
               f"{punkte} Punkte")

        if druck_pfad:
            # Feste Seiten: Jede Druckseite muss als Bild drin sein.
            gedruckt = len(PdfReader(str(WURZEL / druck_pfad)).pages)
            gesetzt = len([n for n in namen
                           if re.fullmatch(r"OEBPS/s\d+\.xhtml", n)])
            pruefe(f"{name}: alle Druckseiten im E-Book",
                   gesetzt == gedruckt, f"{gesetzt} von {gedruckt}")
            pruefe(f"{name}: als feste Seiten deklariert",
                   "pre-paginated" in opf)
        else:
            # Fließender Text: keine Marker, keine Rechtstexte verloren.
            offen = re.findall(r"\{\{[A-ZÄÖÜ]+\}\}", volltext)
            pruefe(f"{name}: keine offenen Marker", not offen,
                   ", ".join(sorted(set(offen))))
            for bezeichnung, nadel in (
                    ("Schwangerschaft", "Schwangerschaft"),
                    ("Eigenverantwortung", "eigener Verantwortung"),
                    ("Markenhinweis", "PM-International AG")):
                pruefe(f"{name}: Rechtstext {bezeichnung}", nadel in volltext)

        pruefe(f"{name}: Titelbild im Paket verzeichnet",
               'properties="cover-image"' in opf)


def archiv_lesen(epub, name):
    import zipfile

    with zipfile.ZipFile(epub) as archiv:
        return archiv.read(name).decode("utf-8")


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
    print("ENDABNAHME — Der Stoffwechsel-Reset (drei Bände)")
    print("=" * 66)
    buch_pruefen()
    workbook_pruefen()
    rezeptbuch_pruefen()
    kindle_pruefen()
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
