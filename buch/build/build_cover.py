#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für Band 1.

    python3 buch/build/build_cover.py

Das Skript liest die Seitenzahl aus dem fertigen Innenteil-PDF und rechnet die
Rückenbreite daraus aus. Der Innenteil muss also vorher gebaut sein:

    python3 buch/build/build_docx.py

Ergebnis: buch/out/cover.pdf (druckfertig) und buch/out/cover-vorschau.png.
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
import illustration as ill  # noqa: E402

WURZEL = Path(__file__).resolve().parents[2]

# --- KDP-Vorgaben ------------------------------------------------------------
BESCHNITT_MM = 3.175          # Anschnitt ringsum
RUECKEN_PRO_SEITE_MM = 0.0572  # weißes Papier
RUECKENTEXT_AB_SEITEN = 79     # darunter erlaubt KDP keinen Text auf dem Rücken
BARCODE_B_MM, BARCODE_H_MM = 50.8, 30.5  # 2,0 x 1,2 Zoll, bleibt frei

SCHRIFTEN = {
    "Sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "Sans-Bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "Serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "Serif-Bold": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "Serif-Italic": "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
}


def schriften_laden():
    for name, pfad in SCHRIFTEN.items():
        if not Path(pfad).exists():
            raise SystemExit(f"Schrift fehlt: {pfad}")
        pdfmetrics.registerFont(TTFont(name, pfad))


# --- Hilfen ------------------------------------------------------------------
def seitenzahl(pdf_pfad):
    from pypdf import PdfReader
    if not Path(pdf_pfad).exists():
        raise SystemExit(
            f"{pdf_pfad} fehlt. Bitte zuerst build_docx.py laufen lassen — "
            "die Rückenbreite ergibt sich aus der Seitenzahl."
        )
    return len(PdfReader(str(pdf_pfad)).pages)


def klappentext_laden(pfad):
    roh = pfad.read_text(encoding="utf-8")
    kopf, rumpf = {}, roh
    if roh.startswith("---"):
        teile = roh.split("---", 2)
        if len(teile) >= 3:
            kopf = yaml.safe_load(teile[1]) or {}
            rumpf = teile[2]
    bloecke = [b.strip() for b in rumpf.strip().split("\n\n") if b.strip()]
    absaetze, punkte = [], []
    for block in bloecke:
        if block.lstrip().startswith("- "):
            for zeile in block.splitlines():
                punkte.append(zeile.strip()[2:].replace("**", ""))
        else:
            absaetze.append(" ".join(block.split()).replace("**", ""))
    return kopf, absaetze, punkte


def umbrechen(c, text, schrift, groesse, breite):
    """Bricht Text auf eine Zeilenbreite um."""
    c.setFont(schrift, groesse)
    zeilen, aktuell = [], ""
    for wort in text.split():
        probe = f"{aktuell} {wort}".strip()
        if c.stringWidth(probe, schrift, groesse) <= breite:
            aktuell = probe
        else:
            if aktuell:
                zeilen.append(aktuell)
            aktuell = wort
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def groesse_einpassen(c, text, schrift, breite, *, maximal, minimal):
    """Größte Schriftgröße, bei der keine Zeile über `breite` hinausragt.

    Ohne das läuft ein langer Titel in den Anschnitt und wird beim
    Beschneiden abgesägt.
    """
    for groesse in range(int(maximal), int(minimal) - 1, -1):
        zeilen = umbrechen(c, text, schrift, groesse, breite)
        if all(c.stringWidth(z, schrift, groesse) <= breite for z in zeilen):
            return groesse, zeilen
    return minimal, umbrechen(c, text, schrift, minimal, breite)


def block_schreiben(c, text, x, y, breite, schrift, groesse, zeilenhoehe,
                    farbe, zentriert=False):
    c.setFillColor(farbe)
    for zeile in umbrechen(c, text, schrift, groesse, breite):
        c.setFont(schrift, groesse)
        if zentriert:
            c.drawCentredString(x + breite / 2, y, zeile)
        else:
            c.drawString(x, y, zeile)
        y -= zeilenhoehe
    return y


# --- Zeichnen ----------------------------------------------------------------
def titelbild_suchen(cover_verzeichnis):
    """Sucht ein eigenes Titelfoto.

    Liegt in buch/cover/ eine Datei namens `titelbild.jpg` (oder .png/.webp),
    wird sie anstelle des oberen Illustrationsbands eingesetzt. Für den Druck
    sollte sie mindestens 1800 x 2700 px haben — darunter warnt das Skript.
    """
    for endung in (".jpg", ".jpeg", ".png", ".webp"):
        pfad = cover_verzeichnis / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


def titelbild_zeichnen(c, pfad, x, y, breite, hoehe):
    """Zeichnet das Foto formatfüllend in den Rahmen, mittig beschnitten."""
    from PIL import Image
    from reportlab.lib.utils import ImageReader

    with Image.open(pfad) as bild:
        bild = bild.convert("RGB")
        soll = breite / hoehe
        ist = bild.width / bild.height
        if ist > soll:  # zu breit — links und rechts beschneiden
            neu = int(bild.height * soll)
            links = (bild.width - neu) // 2
            bild = bild.crop((links, 0, links + neu, bild.height))
        else:           # zu hoch — oben und unten beschneiden
            neu = int(bild.width / soll)
            oben = (bild.height - neu) // 2
            bild = bild.crop((0, oben, bild.width, oben + neu))
        c.drawImage(ImageReader(bild), x, y, breite, hoehe,
                    preserveAspectRatio=False, mask=None)


def vorderseite(c, x, y, breite, hoehe, cfg, titelbild=None):
    """Titelseite: Illustrationsbänder oben und unten, Titel in der Mitte."""
    rand = breite * 0.10

    if titelbild:
        titelbild_zeichnen(c, titelbild, x, y + hoehe * 0.62,
                           breite, hoehe * 0.38)
    else:
        ill.komposition_zeichnen(c, ill.BAND_OBEN,
                                 x, y + hoehe * 0.70, breite, hoehe * 0.24)

    # Titelblock — Größe so wählen, dass keine Zeile in den Anschnitt läuft
    titel_groesse, titel_zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", breite - 2 * rand,
        maximal=46, minimal=22)
    zeilenhoehe = titel_groesse * 1.13

    mitte_y = y + hoehe * 0.545
    c.setFillColor(ill.PALETTE["blatt"])
    for i, zeile in enumerate(titel_zeilen):
        c.setFont("Sans-Bold", titel_groesse)
        c.drawCentredString(x + breite / 2, mitte_y - i * zeilenhoehe, zeile)

    unten = mitte_y - len(titel_zeilen) * zeilenhoehe

    # Tagesfarben-Streifen
    streifen_b = breite * 0.36
    ill.streifen_tagesfarben(c, x + (breite - streifen_b) / 2,
                             unten - 4, streifen_b, 7)

    # Untertitel
    c.setFillColor(HexColor("#3E4A3A"))
    block_schreiben(c, cfg["untertitel"], x + rand, unten - 34,
                    breite - 2 * rand, "Sans", 16, 21,
                    HexColor("#3E4A3A"), zentriert=True)

    # Autor
    c.setFillColor(ill.PALETTE["blatt_tief"])
    c.setFont("Sans-Bold", 18)
    c.drawCentredString(x + breite / 2, y + hoehe * 0.30, cfg["autor"])

    # Illustrationsband unten — beim Fotocover bleibt es weg, sonst
    # konkurrieren Foto und Zeichnung miteinander.
    if not titelbild:
        ill.komposition_zeichnen(c, ill.BAND_UNTEN,
                                 x, y + hoehe * 0.075, breite, hoehe * 0.18)


def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    c.saveState()
    c.setFillColor(ill.PALETTE["blatt"])
    c.rect(x, y, breite, hoehe, stroke=0, fill=1)
    if mit_text:
        c.translate(x + breite / 2, y + hoehe / 2)
        c.rotate(-90)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Sans-Bold", min(11, breite * 0.55))
        c.drawCentredString(0, -min(11, breite * 0.55) * 0.35,
                            f"{cfg['titel']}   ·   {cfg['autor']}")
    c.restoreState()


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte):
    rand = breite * 0.11
    textbreite = breite - 2 * rand
    cursor = y + hoehe - rand * 1.5

    # Schlagzeile
    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", 17, 22,
                                 ill.PALETTE["blatt"])
        cursor -= 14

    # Fließtext
    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", 10.5, 14.5, HexColor("#26301F"))
        cursor -= 8

    # Stichpunkte
    cursor -= 4
    for punkt in punkte:
        c.setFillColor(ill.PALETTE["blatt_hell"])
        c.setFont("Sans-Bold", 10.5)
        c.drawString(x + rand, cursor, "•")
        zeilen = umbrechen(c, punkt, "Serif", 10, textbreite - 14)
        c.setFillColor(HexColor("#26301F"))
        for zeile in zeilen:
            c.setFont("Serif", 10)
            c.drawString(x + rand + 14, cursor, zeile)
            cursor -= 13.5
        cursor -= 3

    # Autorenzeile
    cursor -= 10
    c.setFillColor(HexColor("#5A6455"))
    c.setFont("Serif-Italic", 9.5)
    c.drawString(x + rand, cursor,
                 f"{cfg['autor']} begleitet Menschen bei der")
    c.drawString(x + rand, cursor - 12, "Umstellung ihrer Ernährung.")

    # Markenhinweis über dem Barcode-Feld
    hinweis_y = y + BARCODE_H_MM * mm + rand * 0.5
    c.setFillColor(HexColor("#6B7566"))
    block_schreiben(
        c,
        "„cellRESET“ und „FitLine“ sind Marken der PM-International AG. "
        "Dieses Buch wird von diesem Unternehmen weder herausgegeben noch "
        "autorisiert. Kein medizinischer Ratgeber — bitte die Hinweise im "
        "Buch beachten.",
        x + rand, hinweis_y, textbreite, "Serif", 7, 9, HexColor("#6B7566"))

    # Freifläche für den KDP-Barcode markieren (nur als Kontrolle im Layout)
    return x + breite - rand - BARCODE_B_MM * mm, y + rand


def cover_bauen(cfg, seiten, klappentext_pfad, ziel):
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    anschnitt = BESCHNITT_MM * mm
    ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h))
    c.setTitle(f"{cfg['titel']} — Umschlag")

    # Grundfläche inklusive Anschnitt
    c.setFillColor(ill.PALETTE["papier"])
    c.rect(0, 0, gesamt_b, gesamt_h, stroke=0, fill=1)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    titelbild = titelbild_suchen(Path(klappentext_pfad).parent)

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_text=seiten >= RUECKENTEXT_AB_SEITEN)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg, titelbild)

    c.showPage()
    c.save()
    return {
        "gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
        "ruecken_mm": ruecken_b / mm,
        "ruecken_text": seiten >= RUECKENTEXT_AB_SEITEN,
        "titelbild": titelbild,
    }


def vorschau(pdf_pfad, png_pfad, dpi=90):
    import fitz
    seite = fitz.open(str(pdf_pfad))[0]
    seite.get_pixmap(dpi=dpi).save(str(png_pfad))
    return png_pfad


def main():
    buch = WURZEL / "buch"
    cfg = yaml.safe_load((buch / "buch.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(buch / "out" / f"{cfg['slug']}.pdf")

    ziel = buch / "out" / "cover.pdf"
    masse = cover_bauen(cfg, seiten, buch / "cover" / "klappentext.md", ziel)
    png = vorschau(ziel, buch / "out" / "cover-vorschau.png")

    b, h = masse["gesamt_mm"]
    print(f"Innenteil: {seiten} Seiten")
    print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
          f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
    print(f"Umschlag gesamt: {b:.1f} x {h:.1f} mm inkl. {BESCHNITT_MM} mm Anschnitt")
    if masse["titelbild"]:
        from PIL import Image
        with Image.open(masse["titelbild"]) as bild:
            gross_genug = bild.width >= 1800 and bild.height >= 2700
        print(f"Titelbild: {masse['titelbild'].name} "
              f"({bild.width} x {bild.height} px)"
              + ("" if gross_genug else "  — ACHTUNG: unter 1800 x 2700 px, "
                                        "für den Druck zu klein"))
    else:
        print("Titelbild: keins — es werden die Illustrationen verwendet. "
              "Für ein Foto: buch/cover/titelbild.jpg ablegen.")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
