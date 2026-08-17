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

# --- Hardcover ---------------------------------------------------------------
# Beim Hardcover wird der Umschlag nicht beschnitten, sondern um die Buchdecke
# geschlagen. Statt 3,175 mm Anschnitt braucht er 18 mm Umschlagrand ringsum,
# und der Rücken ist nicht der Buchblock, sondern die Decke: Buchblock plus
# zwei Deckelpappen und die Falzrillen, zusammen 9 mm.
#
# Gegenprobe an KDPs eigener Vorlage für 6 x 9 Zoll mit 76 Seiten:
#   Breite  2·152,4 + (76·0,0572 + 9) + 2·18 = 354,13 mm = 13,942 Zoll
#   Höhe                       228,6 + 2·18  = 264,59 mm = 10,417 Zoll
# In Zoll definiert und erst dann umgerechnet: KDP rechnet in Zoll, und runde
# Millimeterwerte (18,0 / 9,0) treffen die Sollbreite um 0,03 mm daneben.
WRAP_ZOLL = 0.7085
BUCHDECKE_ZOLL = 0.354
WRAP_MM = WRAP_ZOLL * 25.4
BUCHDECKE_MM = BUCHDECKE_ZOLL * 25.4
HARDCOVER_MIN_SEITEN = 75      # weniger nimmt KDP als Hardcover nicht an

# --- Barcodefeld -------------------------------------------------------------
# KDP druckt den Barcode selbst auf die Rückseite, unten rechts, ohne eigenen
# Hintergrund. Die Fläche muss deshalb zweierlei sein: frei von Text, Bild und
# Grafik — und hell, sonst steht schwarze Strichschrift auf dem Schiefergrund
# dieser Reihe und ist nicht mehr zu scannen.
#
# Gemessen wird ab der Trimmkante, nicht ab dem Anschnitt: Nach dem Beschneiden
# ist die Trimmkante die Papierkante, und von dort rechnet KDP.
BARCODE_B_MM, BARCODE_H_MM = 50.8, 30.5   # 2,0 x 1,2 Zoll — KDPs Mindestmaß
BARCODE_RAND_MM = 6.35                    # 0,25 Zoll zur Trimmkante
BARCODE_LUFT_MM = 4.0                     # Abstand, den Text zur Fläche hält
# Das helle Feld wird einen halben Millimeter größer angelegt als die
# geforderte Fläche. Sonst liegt die Kante zwischen Weiß und Schiefergrund
# genau auf der Feldgrenze, und was im Druck an Passertoleranz dazukommt,
# zieht einen dunklen Haarstrich an den Rand des Barcodes.
BARCODE_UEBERSTAND_MM = 0.5

MARKENHINWEIS = (
    "„cellRESET“ und „FitLine“ sind Marken der PM-International AG. "
    "Dieses Buch wird von diesem Unternehmen weder herausgegeben noch "
    "autorisiert. Kein medizinischer Ratgeber — bitte die Hinweise im "
    "Buch beachten."
)

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


def barcodefeld(x, y, breite):
    """Das Rechteck unten rechts auf der Rückseite, das frei bleibt.

    `x`, `y`, `breite` sind Ursprung und Breite der **Rückseite in
    Trimmgröße** — nicht des ganzen Umschlags. Zurück kommt (x, y, b, h) in
    Punkt, so wie reportlab rechnet.
    """
    b, h = BARCODE_B_MM * mm, BARCODE_H_MM * mm
    return (x + breite - BARCODE_RAND_MM * mm - b,
            y + BARCODE_RAND_MM * mm, b, h)


def barcodefeld_freistellen(c, x, y, breite, farbe=None):
    """Legt die Barcodefläche als helles Feld an.

    Auf hellem Grund macht das Feld nichts sichtbar — der Umschlag ist dort
    ohnehin schon Papierweiß. Auf dem Schiefergrund ist es das, was den
    Barcode überhaupt lesbar macht.

    Gezeichnet wird ein volltonweißes Rechteck ohne Verlauf und ohne
    Transparenz: Die Druckfassung für KDP darf keine Transparenz enthalten,
    und ein Scanner braucht harten Kontrast, keinen weichen Rand.
    """
    fx, fy, fb, fh = barcodefeld(x, y, breite)
    u = BARCODE_UEBERSTAND_MM * mm
    c.setFillColor(farbe or HexColor("#FFFFFF"))
    c.rect(fx - u, fy - u, fb + 2 * u, fh + 2 * u, stroke=0, fill=1)
    return fx, fy, fb, fh


def markenhinweis_setzen(c, x, y, breite, textbreite, farbe, groesse=7,
                         zeilenhoehe=9):
    """Setzt den Markenhinweis so tief wie möglich, aber über dem Barcodefeld.

    Der Hinweis lief vorher mit den letzten beiden Zeilen quer durch die
    Barcodefläche — im PDF unauffällig, im Druck ein Barcode über Text. Die
    Grundlinie der **letzten** Zeile bestimmt deshalb die Position, nicht die
    der ersten: Der Block wächst nach unten, also muss von unten gerechnet
    werden.
    """
    _, fy, _, fh = barcodefeld(x, y, breite)
    zeilen = umbrechen(c, MARKENHINWEIS, "Serif", groesse, textbreite)
    # Unterlängen (g, p, ß) reichen unter die Grundlinie — sonst berührt der
    # Hinweis die Feldkante genau dort, wo er es nicht darf.
    unterlaenge = groesse * 0.25
    hinweis_y = (fy + fh + BARCODE_LUFT_MM * mm + unterlaenge
                 + (len(zeilen) - 1) * zeilenhoehe)
    block_schreiben(c, MARKENHINWEIS, x + (breite - textbreite) / 2, hinweis_y,
                    textbreite, "Serif", groesse, zeilenhoehe, farbe)
    return hinweis_y


# --- Zeichnen ----------------------------------------------------------------
def titelbild_suchen(cover_verzeichnis):
    """Sucht ein eigenes Titelfoto.

    Gesucht wird zuerst im Umschlagverzeichnis des Bandes, dann in
    buch/cover/. Damit reicht **eine** Datei für alle drei Bände — sie ist
    dasselbe Motiv, und drei Kopien im Repository würden nur auseinanderlaufen.
    Ein Band, der ein eigenes Motiv bekommen soll, legt seine Datei einfach
    daneben; die gewinnt.

    Wie groß das Bild sein muss, rechnet titelbild_sollmasse() aus.
    """
    orte = [Path(cover_verzeichnis)]
    gemeinsam = WURZEL / "buch" / "cover"
    if gemeinsam not in orte:
        orte.append(gemeinsam)
    for ort in orte:
        for endung in (".jpg", ".jpeg", ".png", ".webp"):
            pfad = ort / f"titelbild{endung}"
            if pfad.exists():
                return pfad
    return None


def titelbild_sollmasse(cfg, dpi=300):
    """Wie groß das Titelfoto mindestens sein muss.

    Gerechnet, nicht geraten: Das Foto füllt nicht den ganzen Umschlag,
    sondern das obere Band der Vorderseite — bei AUSLAGE_HOEHE von 0,30
    ergibt vorderseite_schiefer() daraus 40 Prozent der Trimmhöhe. Dazu der
    Anschnitt oben und außen.

    Vorher stand hier ein fester Wert von 1800 x 2700 px, abgeleitet aus dem
    ganzen Umschlag. Der war für dieses Band deutlich zu hoch gegriffen und
    hätte brauchbare Bilder als „zu klein" gemeldet.
    """
    sf = cfg["seitenformat"]
    breite_mm = sf["breite_mm"] + BESCHNITT_MM
    hoehe_mm = sf["hoehe_mm"] * 0.40 + BESCHNITT_MM
    je_mm = dpi / 25.4
    return round(breite_mm * je_mm), round(hoehe_mm * je_mm)


def titelbild_melden(cfg, pfad):
    """Sagt beim Bauen, welches Titelfoto benutzt wird und wie es dasteht."""
    soll_b, soll_h = titelbild_sollmasse(cfg)
    if not pfad:
        print("Titelbild: keins — es werden die Illustrationen verwendet. "
              f"Für ein Foto: buch/cover/titelbild.jpg ablegen "
              f"(mindestens {soll_b} x {soll_h} px).")
        return

    from PIL import Image
    with Image.open(pfad) as bild:
        breite, hoehe = bild.size
    print(f"Titelbild: {Path(pfad).relative_to(WURZEL)} "
          f"({breite} x {hoehe} px, nötig {soll_b} x {soll_h})")
    if breite < soll_b or hoehe < soll_h:
        # Der Beschnitt bestimmt, was übrig bleibt — deshalb hier dieselbe
        # Rechnung wie in titelbild_zeichnen und nicht nur ein Größenvergleich.
        band = soll_b / soll_h
        nutz_b = round(hoehe * band) if breite / hoehe > band else breite
        print(f"  {nutz_b / (soll_b / 300):.0f} dpi statt 300 — wird auf "
              f"{soll_b} px hochgerechnet. Das erfindet keine Schärfe, es "
              "verhindert die KDP-Meldung „Auflösung zu niedrig\".")


def titelbild_zeichnen(c, pfad, x, y, breite, hoehe, dpi=300,
                       ausblenden=None):
    """Zeichnet das Foto formatfüllend in den Rahmen, mittig beschnitten.

    Bleibt nach dem Beschnitt weniger als `dpi` übrig, wird hochgerechnet.
    Dazu offen gesagt: Das erfindet keine Bildinformation. Es verhindert nur,
    dass die KDP-Prüfung eine zu niedrige Auflösung meldet, und bei den hier
    anfallenden Faktoren (rund 1,2) ist der Unterschied im Druck nicht zu
    sehen. Wird der Faktor deutlich größer, ist das ein Zeichen dafür, dass
    das Motiv für dieses Format zu klein ist — dann hilft nur ein größeres
    Original.
    """
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

        ziel_b = round(breite / 72 * dpi)
        hochgerechnet = None
        if bild.width < ziel_b:
            ziel_h = round(hoehe / 72 * dpi)
            hochgerechnet = (bild.width, ziel_b)
            bild = bild.resize((ziel_b, ziel_h), Image.LANCZOS)

        if ausblenden:
            bild = _unterkante_ausblenden(bild, ausblenden)

        c.drawImage(ImageReader(bild), x, y, breite, hoehe,
                    preserveAspectRatio=False, mask=None)
    return hochgerechnet


def _unterkante_ausblenden(bild, farbe, anteil=0.14):
    """Blendet die unteren Bildzeilen in die Grundfarbe des Umschlags aus.

    Ohne das steht zwischen Foto und Grund eine harte Kante quer über den
    Umschlag. Sie fällt umso mehr auf, je näher sich die beiden Töne sind —
    und das Schiefergrau des Fotos liegt dicht am Grundton.

    Gerechnet wird im Bild, nicht als transparenter Verlauf darüber: Die
    KDP-Druckfassung darf keine Transparenz enthalten, und was hier schon
    fertig verrechnet ist, kann in der Rasterfassung keine mehr erzeugen.
    """
    from PIL import Image

    hoehe = max(1, int(bild.height * anteil))
    ziel = Image.new("RGB", (bild.width, hoehe),
                     tuple(round(k * 255) for k in farbe.rgb()))
    maske = Image.linear_gradient("L").resize((bild.width, hoehe))
    unten = bild.crop((0, bild.height - hoehe, bild.width, bild.height))
    bild.paste(Image.composite(ziel, unten, maske),
               (0, bild.height - hoehe))
    return bild


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

    # Untertitel
    c.setFillColor(HexColor("#3E4A3A"))
    block_schreiben(c, cfg["untertitel"], x + rand, unten - 22,
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


#: Anteil der Umschlaghöhe, den die Auslage am oberen Rand einnimmt.
AUSLAGE_HOEHE = 0.30


def kennungsbalken(c, text, mitte_x, y, schrift, groesse, sperrung):
    """Bandkennung als gefüllter Balken in der Akzentfarbe."""
    breite = c.stringWidth(text, schrift, groesse) + sperrung * (len(text) - 1)
    polster_x, polster_y = groesse * 1.4, groesse * 0.62
    c.setFillColor(ill.SCHIEFER["akzent"])
    c.roundRect(mitte_x - breite / 2 - polster_x, y - polster_y,
                breite + 2 * polster_x, groesse + 2 * polster_y,
                (groesse + 2 * polster_y) / 2, stroke=0, fill=1)
    gesperrt_zentriert(c, text, mitte_x, y + groesse * 0.12,
                       schrift, groesse, sperrung, ill.SCHIEFER["balkentext"])


def gesperrt_zentriert(c, text, mitte_x, y, schrift, groesse, sperrung, farbe):
    """Zentrierter Text mit erweiterter Laufweite.

    Die Sperrung sitzt im Textobjekt, nicht in eingefügten Leerzeichen — die
    würden aus dem Wortabstand eine Lücke von drei Zeichen machen. Die
    Gesamtbreite wächst um die Sperrung und muss beim Zentrieren mitzählen.
    """
    breite = c.stringWidth(text, schrift, groesse) + sperrung * (len(text) - 1)
    t = c.beginText(mitte_x - breite / 2, y)
    t.setFont(schrift, groesse)
    t.setCharSpace(sperrung)
    t.setFillColor(farbe)
    t.textOut(text)
    # Zurücksetzen, solange das Textobjekt noch offen ist: Die Laufweite ist
    # Teil des PDF-Textzustands und gälte sonst für jeden weiteren Text auf
    # der Seite — Untertitel und Autorenzeile kamen gesperrt heraus.
    t.setCharSpace(0)
    c.drawText(t)


def auslage_oben(c, x, y, breite, hoehe, *, bezug, wiederholungen):
    """Durchlaufender Streifen mit Lebensmitteln am oberen Rand.

    Läuft über Rückseite, Rücken und Vorderseite in einem Zug — wie eine
    ausgebreitete Auslage, die am Bildrand einfach weitergeht.
    """
    motive = ill.band_ueber_breite(ill.BAND_DICHT, wiederholungen)
    ill.komposition_zeichnen(c, motive, x, y, breite, hoehe, bezug=bezug)


def vorderseite_schiefer(c, x, y, breite, hoehe, cfg, titelbild=None,
                         *, kennung=None, titel_maximal=46, ueberstand=0):
    """Titelseite im Schieferstil: Titel im freien Grund unter der Auslage.

    Die Auslage selbst zeichnet cover_bauen über den ganzen Umschlag.
    `kennung` ist die Bandkennzeichnung über dem Titel („REZEPTBUCH · …"),
    die Band 2 und 3 voneinander und von Band 1 unterscheidbar macht.

    `ueberstand` ist der Anschnitt beim Taschenbuch und der Umschlagrand beim
    Hardcover. Das Titelfoto läuft um diesen Betrag über die Trimmkante nach
    oben und nach außen hinaus — sonst bliebe dort ein Streifen Grundton
    stehen: beim Taschenbuch 3,2 mm, beim Hardcover 18 mm.
    """
    rand = breite * 0.09

    if titelbild:
        titelbild_zeichnen(c, titelbild, x, y + hoehe * 0.60,
                           breite + ueberstand, hoehe * 0.40 + ueberstand,
                           ausblenden=ill.SCHIEFER["grund"])

    if kennung:
        # Als gefüllter Balken, nicht als feine Schrift auf dem Grund: Im
        # Amazon-Vorschaubild ist der Umschlag rund 100 px breit, und alle
        # drei Bände tragen denselben Titel. Die Bandkennung ist dort das
        # Einzige, was sie unterscheidet — sie muss bei dieser Größe stehen.
        kennungsbalken(c, kennung, x + breite / 2, y + hoehe * 0.545,
                       "Sans-Bold", 10.5, 2.4)

    titel_groesse, titel_zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", breite - 2 * rand,
        maximal=titel_maximal, minimal=20)
    zeilenhoehe = titel_groesse * 1.13

    mitte_y = y + hoehe * 0.455
    c.setFillColor(ill.SCHIEFER["text"])
    for i, zeile in enumerate(titel_zeilen):
        c.setFont("Sans-Bold", titel_groesse)
        c.drawCentredString(x + breite / 2, mitte_y - i * zeilenhoehe, zeile)

    unten = mitte_y - len(titel_zeilen) * zeilenhoehe

    # Feiner Strich in Blattgrün als Trenner statt eines Farbbalkens — auf
    # dunklem Grund reicht das, ein Balken würde das Bild zerschneiden.
    c.setStrokeColor(ill.SCHIEFER["akzent"])
    c.setLineWidth(1.6)
    c.line(x + breite * 0.36, unten - 12, x + breite * 0.64, unten - 12)

    block_schreiben(c, cfg["untertitel"], x + rand, unten - 36,
                    breite - 2 * rand, "Sans", 15.5, 20.5,
                    ill.SCHIEFER["text_leise"], zentriert=True)

    c.setFillColor(ill.SCHIEFER["akzent"])
    c.setFont("Sans-Bold", 18)
    c.drawCentredString(x + breite / 2, y + hoehe * 0.135, cfg["autor"])


#: Grundgrößen des Rückseitentexts: (Schlagzeile, Fließtext, Stichpunkt).
#: Werden gemeinsam verkleinert, wenn der Platz nicht reicht. Betrifft nur die
#: Rückseite — Titel, Untertitel und Rücken haben eigene Größen.
#:
#: Der Platz für die größeren Werte kommt daher, dass die Autorenzeile
#: („… begleitet Menschen bei der Umstellung ihrer Ernährung.") entfallen ist.
RUECKEN_GROESSEN = (19.0, 12.0, 11.5)


def _rueckseite_hoehe(c, kopf, absaetze, punkte, textbreite, faktor):
    """Höhe, die der Rückseitentext bei diesem Verkleinerungsfaktor braucht.

    Wird vor dem Zeichnen ausgerechnet: Der Text muss über dem Markenhinweis
    enden, und ein Umschlag, bei dem beides übereinanderliegt, fällt in der
    PDF-Vorschau leicht durch, im Druck aber teuer auf.
    """
    g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
    hoehe = 0.0
    if kopf.get("schlagzeile"):
        hoehe += len(umbrechen(c, kopf["schlagzeile"], "Sans-Bold", g_kopf,
                               textbreite)) * g_kopf * 1.3 + 14
    for absatz in absaetze:
        hoehe += len(umbrechen(c, absatz, "Serif", g_text,
                               textbreite)) * g_text * 1.38 + 8
    hoehe += 4
    for punkt in punkte:
        hoehe += len(umbrechen(c, punkt, "Serif", g_punkt,
                               textbreite - 14)) * g_punkt * 1.35 + 3
    return hoehe


def rueckseite_schiefer(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte,
                        *, auslage=True):
    rand = breite * 0.11
    textbreite = breite - 2 * rand
    if auslage:
        # Text beginnt unter der Auslage, nicht am Seitenkopf.
        oben = y + hoehe * (1 - AUSLAGE_HOEHE) - rand * 0.6
    else:
        # Beim Fotocover steht das Titelbild nur auf der Vorderseite, die
        # Auslage entfällt — und damit auch der Grund, das obere Drittel der
        # Rückseite freizulassen. Ohne diese Unterscheidung blieben dort
        # 70 mm leerer Grund stehen, während sich der Klappentext darunter
        # zusammenquetscht.
        oben = y + hoehe - rand * 0.85

    # Barcodefeld zuerst: Es ist der einzige Bereich der Rückseite, dessen
    # Lage nicht verhandelbar ist. Alles andere ordnet sich darüber an.
    barcodefeld_freistellen(c, x, y, breite)
    hinweis_hoehe = (len(umbrechen(c, MARKENHINWEIS, "Serif", 7, textbreite))
                     * 9)
    _, fy, _, fh = barcodefeld(x, y, breite)
    hinweis_y = fy + fh + BARCODE_LUFT_MM * mm + hinweis_hoehe
    platz = oben - (hinweis_y + 16)

    def passt(faktor):
        return _rueckseite_hoehe(c, kopf, absaetze, punkte, textbreite,
                                 faktor) <= platz

    # Der Text sucht sich seine Größe selbst. Nach unten, damit ein langer
    # Klappentext nicht in den Markenhinweis läuft; nach oben, weil die
    # Rückseite von Band 2 im A4-Format sonst zu zwei Dritteln leer bleibt —
    # bei gleicher Textmenge auf deutlich mehr Fläche. Die Grenzen halten den
    # Abstand zwischen den Bänden klein: Die drei sollen als Reihe erkennbar
    # bleiben, nicht wie drei verschiedene Bücher aussehen.
    faktor = 1.0
    if passt(faktor):
        while faktor < 1.30 and passt(faktor + 0.02):
            faktor += 0.02
    else:
        while faktor > 0.72 and not passt(faktor):
            faktor -= 0.02
    g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
    if faktor != 1.0:
        wort = "vergrößert" if faktor > 1 else "verkleinert"
        print(f"  Rückseitentext auf {faktor:.0%} {wort} "
              f"(Fließtext {g_text:.1f} pt)")

    # Was nach dem Wachsen übrig bleibt, wird oben und unten gleich verteilt.
    # Sonst klebt der Text am oberen Rand und lässt über dem Markenhinweis
    # eine Lücke — bei gedeckelter Schriftgröße der Normalfall, nicht die
    # Ausnahme.
    rest = platz - _rueckseite_hoehe(c, kopf, absaetze, punkte, textbreite,
                                     faktor)
    cursor = oben - max(0.0, rest) / 2
    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", g_kopf,
                                 g_kopf * 1.3, ill.SCHIEFER["akzent"])
        cursor -= 14

    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", g_text, g_text * 1.38,
                                 ill.SCHIEFER["text"])
        cursor -= 8

    cursor -= 4
    for punkt in punkte:
        c.setFillColor(ill.SCHIEFER["akzent"])
        c.setFont("Sans-Bold", g_punkt)
        c.drawString(x + rand, cursor, "•")
        zeilen = umbrechen(c, punkt, "Serif", g_punkt, textbreite - 14)
        c.setFillColor(ill.SCHIEFER["text"])
        for zeile in zeilen:
            c.setFont("Serif", g_punkt)
            c.drawString(x + rand + 14, cursor, zeile)
            cursor -= g_punkt * 1.35
        cursor -= 3

    if cursor < hinweis_y + 12:
        print("  ACHTUNG: Rückseitentext reicht bis an den Markenhinweis — "
              "Klappentext kürzen.")

    markenhinweis_setzen(c, x, y, breite, textbreite,
                         ill.SCHIEFER["text_leise"])


def ruecken_schiefer(c, x, y, breite, hoehe, cfg, mit_text, text=None):
    """Der Rücken bleibt im Schiefergrund, der schon flächig liegt."""
    if not mit_text:
        return
    groesse = min(11, breite * 0.55)
    c.saveState()
    c.translate(x + breite / 2, y + hoehe / 2)
    c.rotate(-90)
    c.setFillColor(ill.SCHIEFER["text"])
    c.setFont("Sans-Bold", groesse)
    c.drawCentredString(0, -groesse * 0.35,
                        text or f"{cfg['titel']}   ·   {cfg['autor']}")
    c.restoreState()


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

    # Markenhinweis über dem Barcodefeld — die Fläche selbst ist auf dem
    # hellen Grund schon Papierweiß und muss nur freigehalten werden.
    markenhinweis_setzen(c, x, y, breite, textbreite, HexColor("#6B7566"))
    return barcodefeld(x, y, breite)


def cover_bauen(cfg, seiten, klappentext_pfad, ziel, *, hardcover=False):
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    if hardcover:
        anschnitt = WRAP_MM * mm
        ruecken_b = (seiten * RUECKEN_PRO_SEITE_MM + BUCHDECKE_MM) * mm
    else:
        anschnitt = BESCHNITT_MM * mm
        ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    # initialFontName: reportlab schreibt sonst einen Seitenvorspann mit
    # Helvetica in die Ressourcen — eine Schrift ohne Einbettung, die
    # kein Zeichen setzt, aber bei der KDP-Prüfung auffallen kann.
    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")

    stil = cfg.get("cover_stil", "hell")
    if stil not in ("hell", "schiefer"):
        raise SystemExit(f"Unbekannter cover_stil: {stil} (hell | schiefer)")
    ill.grund_setzen("dunkel" if stil == "schiefer" else "hell")
    ill.akzent_setzen(cfg.get("cover_akzent", "blatt"))

    # Grundfläche inklusive Anschnitt
    if stil == "schiefer":
        ill.schiefergrund(c, 0, 0, gesamt_b, gesamt_h)
    else:
        c.setFillColor(ill.PALETTE["papier"])
        c.rect(0, 0, gesamt_b, gesamt_h, stroke=0, fill=1)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    titelbild = titelbild_suchen(Path(klappentext_pfad).parent)
    # Beim Hardcover ist der Rücken immer breit genug: Die Buchdecke bringt
    # allein 9 mm mit, die 79-Seiten-Schwelle des Taschenbuchs greift hier
    # nicht. Bei 76 Seiten sind es 13,3 mm — reichlich Platz für Schrift.
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    if stil == "schiefer":
        # Die Auslage zuerst und über den ganzen Umschlag — Rückseite, Rücken
        # und Vorderseite bekommen denselben durchlaufenden Streifen.
        if not titelbild:
            auslage_oben(c, 0, gesamt_h * (1 - AUSLAGE_HOEHE),
                         gesamt_b, gesamt_h * AUSLAGE_HOEHE,
                         bezug=trim_b, wiederholungen=2)
        rueckseite_schiefer(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
                            kopf, absaetze, punkte,
                            auslage=not titelbild)
        ruecken_schiefer(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h,
                         cfg, mit_ruecken_text)
        vorderseite_schiefer(c, anschnitt + trim_b + ruecken_b, anschnitt,
                             trim_b, trim_h, cfg, titelbild,
                             kennung="DAS BUCH · 4 PHASEN",
                             ueberstand=anschnitt)
    else:
        rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
                   kopf, absaetze, punkte)
        ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
                mit_text=mit_ruecken_text)
        vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                    trim_b, trim_h, cfg, titelbild)

    c.showPage()
    c.save()
    return {
        "gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
        "ruecken_mm": ruecken_b / mm,
        "ruecken_text": mit_ruecken_text,
        "titelbild": titelbild,
        "stil": stil,
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
    klappentext = buch / "cover" / "klappentext.md"

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue

        ziel = buch / "out" / f"{name}.pdf"
        masse = cover_bauen(cfg, seiten, klappentext, ziel, hardcover=hardcover)
        png = vorschau(ziel, buch / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        rand = WRAP_MM if hardcover else BESCHNITT_MM
        randname = "Umschlagrand um die Buchdecke" if hardcover else "Anschnitt"
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {rand} mm {randname}")
        titelbild_melden(cfg, masse["titelbild"])
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
