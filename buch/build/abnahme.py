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
WRAP_MM = 0.7085 * 25.4        # Hardcover: Umschlagrand statt Anschnitt
BUCHDECKE_MM = 0.354 * 25.4    # Hardcover: Pappen und Falzrillen im Rücken

# Barcodefeld unten rechts auf der Rückseite. Die Werte stehen hier noch
# einmal und werden bewusst nicht aus build_cover importiert: Ein Prüfer, der
# die Zahlen des Erzeugers übernimmt, prüft nur, ob der Erzeuger mit sich
# selbst übereinstimmt. Diese Zahlen kommen aus KDPs Vorgabe.
BARCODE_B_MM, BARCODE_H_MM = 50.8, 30.5
BARCODE_RAND_MM = 6.35
# Hardcover: 0,25 Zoll Abstand gelten dort nicht zum Rücken, sondern zum
# Scharnier — und das ist 0,4 Zoll breit. Das Feld rückt also 10,2 mm weiter
# nach innen als beim Taschenbuch, abzüglich der 4 mm, um die es nach
# Sichtprüfung in KDPs Vorschau wieder zum Rücken hin gerückt wurde.
BARCODE_SCHARNIER_MM = 0.4 * 25.4
BARCODE_HARDCOVER_KORREKTUR_MM = 4.0
# Nach unten misst KDP nicht ab der Trimmkante, sondern ab der Unterkante der
# Datei: mindestens 0,76 Zoll. Beim Taschenbuch liegen darunter nur 3,175 mm
# Anschnitt, das Feld muss also 16,1 mm über der Trimmkante sitzen; beim
# Hardcover bringen 18 mm Umschlagrand die Vorgabe schon mit.
BARCODE_UNTEN_AB_DATEIKANTE_MM = 0.76 * 25.4
# Gezeichnet wird exakt KDPs Zone — ohne Rand. KDP bringt seine eigene weiße
# Box mit; alles, was darüber hinausgeht, steht als weißer Rand um den Barcode.
FELD_B_MM, FELD_H_MM = BARCODE_B_MM, BARCODE_H_MM
# Beim Hardcover liegt gar keine eigene Weißfläche mehr unter KDPs Box.
BARCODE_WEISSFLAECHE = {"taschenbuch": True, "hardcover": False}

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
    # „Der Darm im Gleichgewicht" hat kein eigenes build-Verzeichnis — der
    # Band wird mit den Skripten aus buch/build gebaut.
    "darm": ["darm/darm.yaml", "darm/kapitel", "buch/build"],
}

# Prüfer und Nachbearbeitung stehen zwar in denselben Verzeichnissen, gehen
# aber nicht in den Innenteil ein. Ohne diese Ausnahme meldet die Prüfung
# sich selbst als Grund, neu zu bauen.
KEINE_QUELLE = {"abnahme.py", "claim_check.py", "zutaten_check.py",
                "rechtschreibung.py",
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
    cover_pruefen("Band 1 Hardcover", basis / "out" / "cover-hardcover.pdf",
                  cfg, len(seiten), hardcover=True)


def darm_pruefen():
    print("\nDer Darm im Gleichgewicht")
    print("-" * 66)
    basis = WURZEL / "darm"
    cfg = yaml.safe_load((basis / "darm.yaml").read_text(encoding="utf-8"))
    pdf = basis / "out" / f"{cfg['slug']}.pdf"
    pruefe("PDF vorhanden", pdf.exists(), str(pdf.relative_to(WURZEL)))
    if not pdf.exists():
        return
    aktueller_als_quellen("Darm", pdf, "darm")

    seiten = text_von(pdf)
    pruefe("Seitenzahl gerade (KDP rundet sonst auf)", len(seiten) % 2 == 0,
           f"{len(seiten)} Seiten")
    # KDP nimmt Hardcover erst ab 75 Seiten. Der Band liegt weit darüber;
    # die Prüfung steht hier, damit ein Kürzen nicht unbemerkt darunter fällt.
    pruefe("Umfang für Hardcover ausreichend", len(seiten) >= 75,
           f"{len(seiten)} Seiten, KDP verlangt 75")

    volltext = "\n".join(seiten)

    pruefe("Inhaltsverzeichnis aufgelöst",
           "Die Reise einer Mahlzeit" in volltext,
           "keine unaufgelösten Word-Felder")

    # Pflichtinhalte — das Buch verspricht sie auf dem Umschlag.
    pflicht = {
        "Ballaststoff-Richtwert": "30 Gramm",
        "Bristol-Skala": "Bristol",
        "Acht Wochen": "Woche 7",
        "Rezeptteil": "Zubereitung",
        "Ballaststofftabelle": "je 100 Gramm",
        "Glossar": "Glossar",
        "Quellen": "Weiterlesen",
        "Rote Flaggen": "Blut im Stuhl",
    }
    for name, nadel in pflicht.items():
        pruefe(f"Inhalt: {name}", nadel in volltext)

    rechts = {
        "Schwangerschaft": "Schwangerschaft",
        "Ärztliche Abklärung": "ärztlich",
        "Kein Ersatz für ärztlichen Rat": "ersetz",
        "Eigenverantwortung": "eigener Verantwortung",
        "Einzelergebnisse": "nicht übertragbar",
    }
    for name, nadel in rechts.items():
        pruefe(f"Rechtstext: {name}", nadel in volltext)

    # Gegenprobe: Dieser Titel steht ausdrücklich für sich. Taucht die Reihe
    # oder das Konzept, auf dem sie fußt, doch wieder im Text auf, ist das
    # ein Fehler und kein Detail.
    fremd = [w for w in ("Stoffwechsel-Reset", "cellRESET", "FitLine",
                         "PM-International") if w in volltext]
    pruefe("Keine Verbindung zur Stoffwechsel-Reset-Reihe", not fremd,
           ", ".join(fremd) if fremd else "eigenständiger Titel")

    fehlend = schriften_eingebettet(pdf)
    pruefe("Alle Schriften eingebettet", not fehlend,
           ", ".join(sorted(fehlend)) if fehlend else "")

    zu_leer = fast_leere_seiten(seiten)
    pruefe("Keine fast leeren Seiten", not zu_leer,
           f"Seiten {zu_leer}" if zu_leer else "")

    innenteil_druck_pruefen("Darm", pdf.with_name(pdf.stem + "-druck.pdf"),
                            cfg["seitenformat"]["breite_mm"],
                            cfg["seitenformat"]["hoehe_mm"])
    cover_pruefen("Darm", basis / "out" / "cover.pdf", cfg, len(seiten))
    cover_pruefen("Darm Hardcover", basis / "out" / "cover-hardcover.pdf",
                  cfg, len(seiten), hardcover=True)


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


def barcodefeld_pruefen(bezeichnung, pdf, rand_mm, trim_b_mm, hardcover):
    """Die Fläche, auf die KDP den Barcode druckt, muss leer und hell sein.

    `rand_mm` ist der Anschnitt beziehungsweise der Umschlagrand beim
    Hardcover, `trim_b_mm` die Trimmbreite einer Umschlagseite. Zusammen
    ergeben sie die Trimmkanten der Rückseite, und von denen misst KDP.

    Geprüft wird zweierlei, weil beides schiefgehen kann und nur eines davon
    im Text steht:

    1. Kein Wort ragt in die Fläche. Der Markenhinweis tat genau das mit
       seinen letzten beiden Zeilen — in der PDF-Vorschau kaum zu sehen, im
       gedruckten Buch ein Barcode über Text.
    2. Die Fläche ist gleichmäßig hell. Ein Verlauf oder der Schiefergrund
       wäre textfrei und trotzdem unbrauchbar: KDP druckt den Barcode
       schwarz und ohne eigenen Hintergrund.
    """
    import fitz

    seite = fitz.open(str(pdf))[0]
    pt = 72 / 25.4
    breite, hoehe = BARCODE_B_MM * pt, BARCODE_H_MM * pt
    # Rückseite liegt links; das Feld sitzt an ihrer rechten unteren
    # Trimmecke. fitz zählt y von oben, reportlab von unten.
    seitlich = BARCODE_RAND_MM
    if hardcover:
        seitlich += BARCODE_SCHARNIER_MM - BARCODE_HARDCOVER_KORREKTUR_MM
    unten_mm = max(BARCODE_RAND_MM, BARCODE_UNTEN_AB_DATEIKANTE_MM - rand_mm)
    rechts = (rand_mm + trim_b_mm - seitlich) * pt
    unten = seite.rect.height - (rand_mm + unten_mm) * pt
    # Geprüft wird die **gezeichnete** Fläche, nicht KDPs Mindestzone: Wenn
    # dort Text oder Schiefergrund liegt, nützt eine saubere Mindestzone
    # nichts. Die Fläche liegt mittig um die Zone, ragt also ringsum um
    # FELD_LUFT_MM darüber hinaus.
    feld = fitz.Rect(rechts - FELD_B_MM * pt, unten - FELD_H_MM * pt,
                     rechts, unten)

    stoerer = sorted({w[4] for w in seite.get_text("words")
                      if fitz.Rect(w[:4]).intersects(feld)})
    pruefe(f"{bezeichnung}: Barcodefeld textfrei", not stoerer,
           f"{FELD_B_MM:.1f} x {FELD_H_MM:.1f} mm, {seitlich:.2f} mm von der "
           f"Rückenkante{' (inkl. Scharnier)' if hardcover else ''}"
           if not stoerer
           else f"{len(stoerer)} Wörter darin: {' '.join(stoerer[:6])}")

    # Innen messen, nicht auf der Kante: Beim Rastern mischt die Randreihe die
    # Fläche mit dem Grund dahinter. Ein Artefakt der Messung, kein Fehler im
    # Umschlag — 0,6 mm Einzug misst die Fläche und nicht ihren Rand.
    feld_innen = feld + (0.6 * pt, 0.6 * pt, -0.6 * pt, -0.6 * pt)
    bild = seite.get_pixmap(clip=feld_innen, dpi=120)
    proben = [bild.pixel(sx, sy)
              for sy in range(0, bild.height, max(1, bild.height // 40))
              for sx in range(0, bild.width, max(1, bild.width // 40))]
    kanaele = [min(p) for p in proben]
    dunkelste, hellste = min(kanaele), max(kanaele)

    if BARCODE_WEISSFLAECHE["hardcover" if hardcover else "taschenbuch"]:
        pruefe(f"{bezeichnung}: Barcodefeld hell und einfarbig",
               dunkelste >= 235 and hellste - dunkelste <= 6,
               f"dunkelster Kanalwert {dunkelste}, hellster {hellste} von 255")
    else:
        # Ohne eigene Weißfläche liegt dort der Umschlaggrund. Hell muss er
        # nicht sein — KDP bringt die weiße Box mit. Ruhig muss er sein:
        # Liefe eine Illustration oder eine harte Kante hindurch, stünde sie
        # rings um KDPs Box und sähe nach Versehen aus.
        pruefe(f"{bezeichnung}: Barcodefeld ohne eigene Weißfläche, "
               "Grund ruhig", hellste - dunkelste <= 40,
               f"Kanalwerte {dunkelste} bis {hellste} — KDP legt seine "
               "weiße Box darauf")

    # Die Vorgabe selbst, nicht nur die eigene Rechnung: KDPs Vorschau
    # markiert alles unterhalb von 0,76 Zoll ab der Dateikante rot. Genau
    # dort saß das Feld beim Taschenbuch, bis es jemand in der Vorschau sah.
    ab_dateikante = rand_mm + unten_mm
    pruefe(f"{bezeichnung}: Barcodefeld weit genug von der Unterkante",
           ab_dateikante >= BARCODE_UNTEN_AB_DATEIKANTE_MM - 0.01,
           f"{ab_dateikante:.2f} mm = {ab_dateikante / 25.4:.3f} Zoll "
           f"(gefordert {BARCODE_UNTEN_AB_DATEIKANTE_MM / 25.4:.2f})")


def cover_pruefen(bezeichnung, pdf, cfg, seiten, *, hardcover=False):
    if not pdf.exists():
        pruefe(f"{bezeichnung}: Umschlag vorhanden", False)
        return
    reader = PdfReader(str(pdf))
    pruefe(f"{bezeichnung}: Umschlag ist einseitig", len(reader.pages) == 1)

    kiste = reader.pages[0].mediabox
    ist_b = float(kiste.width) / 72 * 25.4
    ist_h = float(kiste.height) / 72 * 25.4

    # Hardcover rechnet anders: Umschlagrand statt Anschnitt, und der Rücken
    # ist die Buchdecke, nicht der Buchblock.
    if hardcover:
        rand = WRAP_MM
        ruecken = seiten * RUECKEN_PRO_SEITE_MM + BUCHDECKE_MM
    else:
        rand = BESCHNITT_MM
        ruecken = seiten * RUECKEN_PRO_SEITE_MM
    soll_b = 2 * cfg["seitenformat"]["breite_mm"] + ruecken + 2 * rand
    soll_h = cfg["seitenformat"]["hoehe_mm"] + 2 * rand

    pruefe(f"{bezeichnung}: Umschlagbreite", abs(ist_b - soll_b) < 0.5,
           f"{ist_b:.1f} mm (Soll {soll_b:.1f}, Rücken {ruecken:.1f})")
    pruefe(f"{bezeichnung}: Umschlaghöhe", abs(ist_h - soll_h) < 0.5,
           f"{ist_h:.1f} mm (Soll {soll_h:.1f})")

    barcodefeld_pruefen(bezeichnung, pdf, rand,
                        cfg["seitenformat"]["breite_mm"], hardcover)

    druckfassung_pruefen(bezeichnung,
                         pdf.with_name(pdf.stem + "-druck.pdf"),
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
    # Hardcover läuft in eigenem Format und mit eigenem Innenteil.
    hc = cfg.get("hardcover_seitenformat")
    if hc:
        hc_pdf = basis / "out" / f"{cfg['slug']}-hardcover.pdf"
        hc_seiten = len(text_von(hc_pdf)) if hc_pdf.exists() else 0
        pruefe("Band 3 Hardcover: Innenteil vorhanden", hc_pdf.exists(),
               f"{hc_seiten} Seiten" if hc_pdf.exists() else "fehlt")
        pruefe("Band 3 Hardcover: gleiche Seitenzahl wie Taschenbuch",
               hc_seiten == len(seiten),
               f"{hc_seiten} gegen {len(seiten)} — bei gleichem Satzspiegel "
               "müssen beide übereinstimmen")
        pruefe("Band 3 Hardcover: über KDPs Mindestseitenzahl",
               hc_seiten >= 75, f"{hc_seiten} Seiten, gefordert 75")
        innenteil_druck_pruefen(
            "Band 3 Hardcover",
            hc_pdf.with_name(hc_pdf.stem + "-druck.pdf"),
            hc["breite_mm"], hc["hoehe_mm"])
        cover_pruefen("Band 3 Hardcover",
                      basis / "out" / "cover-hardcover.pdf",
                      dict(cfg, seitenformat=hc), hc_seiten, hardcover=True)


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
        ("Band 3", "rezepte/out/rezeptbuch-kindle.epub",
         "rezepte/out/kindle-cover.jpg", None),
        ("Darm", "darm/out/darm-im-gleichgewicht-kindle.epub",
         "darm/out/kindle-cover.jpg", None),
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
            rechtstexte = [("Schwangerschaft", "Schwangerschaft"),
                           ("Eigenverantwortung", "eigener Verantwortung")]
            # Den Markenhinweis tragen nur die Bände der Reihe.
            if name != "Darm":
                rechtstexte.append(("Markenhinweis", "PM-International AG"))
            for bezeichnung, nadel in rechtstexte:
                pruefe(f"{name}: Rechtstext {bezeichnung}", nadel in volltext)

        pruefe(f"{name}: Titelbild im Paket verzeichnet",
               'properties="cover-image"' in opf)

        # Verweise innerhalb des Buchs müssen ein Ziel haben. Bei Band 3
        # verlinken drei Register auf 73 Rezepte — ein einziger toter Anker
        # fällt beim Durchblättern nicht auf, beim Antippen sofort.
        anker = set(re.findall(r'id="([^"]+)"', volltext))
        tot = sorted({f"{d}#{a}" for d, a in
                      re.findall(r'href="([^"#]+)#([^"]+)"', volltext)
                      if a not in anker})
        if tot or "#" in volltext:
            pruefe(f"{name}: keine toten Verweise", not tot,
                   ", ".join(tot[:3]) if tot else "")


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
    print("ENDABNAHME — Stoffwechsel-Reset (3 Bände) + Darm im Gleichgewicht")
    print("=" * 66)
    buch_pruefen()
    workbook_pruefen()
    rezeptbuch_pruefen()
    darm_pruefen()
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
