#!/usr/bin/env python3
"""Rechnet einen Umschlag in eine flache Druckdatei für KDP um.

    python3 buch/build/cover_flach.py buch/out/cover.pdf

Warum das nötig ist: Die Umschläge werden als Vektorgrafik gesetzt — mit
Radialverläufen für die Lebensmittel und mit transparenten Schlagschatten.
Am Bildschirm ist das die bessere Datei. Beim Hochladen bei KDP ist es die
schlechtere: Die Vorgaben verlangen reduzierte Ebenen ohne Transparenz, und
die Prüfung lehnt Dateien mit Transparenzgruppen und Smooth-Shading ab.

Hier wird der Umschlag deshalb einmal bei 300 dpi gerastert und als einzelnes
Bild in ein PDF exakter Größe gelegt. Danach enthält die Datei keine
Transparenz, keine Verläufe, keine Schriften und keine Ebenen mehr — nur noch
Pixel. Genau das erwartet die Druckvorstufe.

Die Vektorfassung bleibt daneben liegen; sie ist die Quelle für Korrekturen.
"""

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
DPI = 300          # KDP-Mindestauflösung für Umschläge
JPEG_QUALITAET = 95


def flach_rechnen(quelle, ziel=None, dpi=DPI):
    import io

    import fitz
    from PIL import Image

    quelle = Path(quelle)
    ziel = Path(ziel) if ziel else quelle.with_name(quelle.stem + "-druck.pdf")

    dokument = fitz.open(str(quelle))
    if dokument.page_count != 1:
        raise SystemExit(f"{quelle.name} hat {dokument.page_count} Seiten — "
                         "ein Umschlag muss einseitig sein.")

    seite = dokument[0]
    breite_pt, hoehe_pt = seite.rect.width, seite.rect.height

    # alpha=False: Ein Alphakanal wäre genau die Transparenz, die weg soll.
    pix = seite.get_pixmap(dpi=dpi, alpha=False)
    bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    puffer = io.BytesIO()
    bild.save(puffer, format="JPEG", quality=JPEG_QUALITAET, optimize=True)

    # Bewusst nicht mit reportlab geschrieben: Das legt in jede Seite einen
    # Vorspann „BT /F1 12 Tf ET" und damit eine nicht eingebettete Helvetica
    # in die Ressourcen. Sie setzt kein Zeichen, ist aber genau das, was die
    # KDP-Prüfung als nicht eingebettete Schrift beanstandet. Über PyMuPDF
    # entsteht eine Seite, die nichts außer dem Bild enthält.
    neu = fitz.open()
    ziel_seite = neu.new_page(width=breite_pt, height=hoehe_pt)
    ziel_seite.insert_image(fitz.Rect(0, 0, breite_pt, hoehe_pt),
                            stream=puffer.getvalue())
    neu.set_metadata({"title": quelle.stem, "producer": "", "creator": ""})
    neu.save(str(ziel), garbage=4, deflate=True)
    neu.close()

    mm = 25.4 / 72
    return {
        "ziel": ziel,
        "mm": (breite_pt * mm, hoehe_pt * mm),
        "px": (pix.width, pix.height),
        "dpi": dpi,
        "kb": ziel.stat().st_size / 1024,
    }


def pruefen(pdf):
    """Gegenprobe: Was KDP beanstanden könnte, darf nicht mehr drin sein."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    befunde = []
    if len(reader.pages) != 1:
        befunde.append(f"{len(reader.pages)} Seiten statt einer")

    seite = reader.pages[0]
    res = seite.get("/Resources", {})
    if hasattr(res, "get_object"):
        res = res.get_object()

    zustand = res.get("/ExtGState")
    if zustand:
        zustand = zustand.get_object()
        for schluessel in zustand:
            eintrag = zustand[schluessel].get_object()
            for feld in ("/ca", "/CA"):
                if feld in eintrag and float(eintrag[feld]) < 1.0:
                    befunde.append(f"Transparenz {feld}={eintrag[feld]}")

    if res.get("/Shading"):
        befunde.append("Verlaufsobjekte (Shading) vorhanden")
    if res.get("/Font"):
        befunde.append("Schriften vorhanden — bei einer Rasterdatei unerwartet")
    if res.get("/Pattern"):
        befunde.append("Muster (Pattern) vorhanden")

    return befunde


def main():
    quellen = sys.argv[1:] or [
        WURZEL / "buch" / "out" / "cover.pdf",
        WURZEL / "buch" / "out" / "cover-hardcover.pdf",
        WURZEL / "workbook" / "out" / "cover.pdf",
        WURZEL / "rezepte" / "out" / "cover.pdf",
        WURZEL / "rezepte" / "out" / "cover-hardcover.pdf",
        WURZEL / "reptilienhirn" / "out" / "cover.pdf",
        WURZEL / "reptilienhirn" / "out" / "cover-hardcover.pdf",
    ]
    for quelle in quellen:
        # resolve(): Wird das Skript mit einem relativen Pfad aufgerufen,
        # scheitert sonst am Ende das relative_to(WURZEL) der Ausgabe.
        quelle = Path(quelle).resolve()
        if not quelle.exists():
            print(f"  fehlt: {quelle}")
            continue
        ergebnis = flach_rechnen(quelle)
        b, h = ergebnis["mm"]
        px_b, px_h = ergebnis["px"]
        print(f"{quelle.parent.parent.name}:")
        print(f"  {b:.2f} x {h:.2f} mm · {px_b} x {px_h} px bei {ergebnis['dpi']} dpi"
              f" · {ergebnis['kb']:.0f} KB")
        befunde = pruefen(ergebnis["ziel"])
        print(f"  {'sauber — keine Transparenz, keine Verläufe, keine Schriften' if not befunde else 'ACHTUNG: ' + '; '.join(befunde)}")
        print(f"  → {ergebnis['ziel'].relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
