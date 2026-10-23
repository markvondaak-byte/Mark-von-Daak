#!/usr/bin/env python3
"""Baut den KDP-Umschlag (Taschenbuch) für „Kopf schlägt Kalorien".

    python3 kopf/build/build_cover.py

Der Innenteil muss vorher gebaut sein — die Rückenbreite ergibt sich aus der
Seitenzahl. Anschnitt, Rückenformel und Barcodefeld kommen aus
buch/build/build_cover.py, damit alle Titel dieselben KDP-Regeln einhalten.

Anders als die Umschläge der Reihe wird dieser direkt als Rasterbild bei
300 dpi gesetzt (Pillow) und dann als einzelnes Bild in ein PDF exakter Größe
gelegt — genau die Form, die cover_flach.py für die anderen Bände erzeugt.
Grund: Die Titelschrift Inter Display liegt nur als OpenType/CFF vor, und die
kann reportlab nicht einbetten. Im Bild ist die Schrift einfach Pixel; die
Druckdatei enthält weder Schriften noch Transparenz noch Ebenen.

Motiv: eine Wippe, auf der ein Kopf einen glasierten Donut aufwiegt — der
Buchtitel als Bild.
"""

import math
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

WURZEL = Path(__file__).resolve().parents[2]
KOPF = WURZEL / "kopf"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM, BESCHNITT_MM,  # noqa: E402
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN,
                         barcodefeld, klappentext_laden, seitenzahl)

DPI = 300
PX_JE_MM = DPI / 25.4
PT_JE_MM = 72 / 25.4
SS = 2  # Überabtastung für die Illustration, gegen Treppenkanten

SCHRIFT = "/usr/share/fonts/opentype/inter/InterDisplay-{}.otf"

FARBE = {
    "grund_oben": (13, 24, 41),
    "grund_unten": (27, 45, 70),
    "text": (246, 242, 234),
    "text_leise": (184, 197, 212),
    "akzent": (247, 176, 62),
    "akzent_tief": (226, 128, 36),
    "balken": (238, 232, 220),
    "bock": (74, 94, 118),
}

HINWEIS = ("Kein medizinischer Ratgeber und kein Ersatz für ärztliche oder "
           "psychotherapeutische Beratung — bitte die Hinweise im Buch "
           "beachten.")

AUTOR_KURZ = ("Mark von Daak lebt in Wolfsburg und begleitet Menschen bei der "
              "Umstellung ihrer Ernährung. Er ist kein Arzt und kein "
              "Psychologe — was er mitbringt, ist die Praxis.")


def mm(wert):
    return round(wert * PX_JE_MM)


def schrift(schnitt, groesse):
    return ImageFont.truetype(SCHRIFT.format(schnitt), round(groesse))


# --- Grundflächen ------------------------------------------------------------
def verlauf(breite, hoehe, oben, unten):
    spalte = Image.new("RGB", (1, hoehe))
    for y in range(hoehe):
        t = y / max(1, hoehe - 1)
        spalte.putpixel((0, y), tuple(round(a + (b - a) * t)
                                      for a, b in zip(oben, unten)))
    return spalte.resize((breite, hoehe))


def leuchten(bild, mitte, radius, farbe, staerke):
    """Weiches Licht hinter der Illustration — als Pixel, nicht als Ebene."""
    maske = Image.new("L", bild.size, 0)
    d = ImageDraw.Draw(maske)
    x, y = mitte
    d.ellipse((x - radius, y - radius, x + radius, y + radius),
              fill=round(255 * staerke))
    maske = maske.filter(ImageFilter.GaussianBlur(radius * 0.45))
    bild.paste(Image.new("RGB", bild.size, farbe), (0, 0), maske)


# --- Formen ------------------------------------------------------------------
def bezier(p0, p1, p2, p3, schritte=24):
    punkte = []
    for i in range(1, schritte + 1):
        t = i / schritte
        u = 1 - t
        punkte.append((u**3 * p0[0] + 3 * u * u * t * p1[0]
                       + 3 * u * t * t * p2[0] + t**3 * p3[0],
                       u**3 * p0[1] + 3 * u * u * t * p1[1]
                       + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return punkte


def kopfprofil():
    """Profil mit Blick nach rechts, Höhe 1, Halsansatz bei y = 0 (y nach oben)."""
    p = [(-0.12, 0.0)]
    p += bezier(p[-1], (-0.13, 0.12), (-0.30, 0.22), (-0.32, 0.46))
    p += bezier(p[-1], (-0.35, 0.80), (-0.10, 1.00), (0.10, 1.00))
    p += bezier(p[-1], (0.30, 1.00), (0.40, 0.86), (0.40, 0.70))
    p += [(0.47, 0.56), (0.41, 0.52)]
    p += bezier(p[-1], (0.43, 0.46), (0.40, 0.44), (0.41, 0.40))
    p += bezier(p[-1], (0.42, 0.34), (0.38, 0.30), (0.30, 0.30))
    p += bezier(p[-1], (0.24, 0.30), (0.20, 0.22), (0.18, 0.12))
    p += [(0.18, 0.0)]
    return p


def ebene(groesse):
    return Image.new("RGBA", groesse, (0, 0, 0, 0))


def kopf_zeichnen(groesse_px):
    """Kopf als eigenes Bild: Verlauf in Bernstein, Lichtkante an der Stirn."""
    h = groesse_px * SS
    b = round(h * 0.95)
    maske = Image.new("L", (b, h), 0)
    pts = [((x + 0.37) * h, (1 - y) * h) for x, y in kopfprofil()]
    ImageDraw.Draw(maske).polygon(pts, fill=255)

    farbe = verlauf(b, h, FARBE["akzent"], FARBE["akzent_tief"])
    # Lichtkante: die Maske leicht nach links versetzt, die Differenz hell
    versatz = ImageChops.offset(maske, round(-h * 0.025), round(h * 0.015))
    kante = ImageChops.subtract(maske, versatz).filter(
        ImageFilter.GaussianBlur(h * 0.012))
    hell = Image.new("RGB", (b, h), (255, 222, 160))
    farbe.paste(hell, (0, 0), kante.point(lambda v: v * 0.55))

    bild = ebene((b, h))
    bild.paste(farbe, (0, 0), maske)
    return bild.resize((b // SS, h // SS), Image.LANCZOS)


def donut_zeichnen(durchmesser_px):
    d = durchmesser_px * SS
    bild = ebene((d, d))
    zeichnen = ImageDraw.Draw(bild)
    r = d / 2
    c = (r, r)

    # Teig mit Bräunung zum Rand
    for i in range(40, 0, -1):
        t = i / 40
        farbe = (round(196 + 34 * (1 - t)), round(134 + 40 * (1 - t)),
                 round(72 + 30 * (1 - t)), 255)
        rr = r * (0.55 + 0.45 * t)
        zeichnen.ellipse((c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr),
                         fill=farbe)

    # Glasur mit welligem Rand
    glasur = []
    for i in range(360):
        w = math.radians(i)
        rr = r * (0.86 + 0.035 * math.sin(7 * w) + 0.02 * math.sin(13 * w + 1))
        glasur.append((c[0] + rr * math.cos(w), c[1] + rr * math.sin(w)))
    gl = Image.new("L", (d, d), 0)
    ImageDraw.Draw(gl).polygon(glasur, fill=255)
    rosa = verlauf(d, d, (250, 150, 188), (226, 92, 144))
    bild.paste(rosa, (0, 0), gl)

    # Glanzlicht oben links
    glanz = Image.new("L", (d, d), 0)
    ImageDraw.Draw(glanz).ellipse((r * 0.35, r * 0.25, r * 1.05, r * 0.75),
                                  fill=110)
    glanz = ImageChops.multiply(glanz.filter(ImageFilter.GaussianBlur(r * 0.12)),
                                gl)
    bild.paste(Image.new("RGB", (d, d), (255, 255, 255)), (0, 0), glanz)

    # Streusel, fest verteilt — gleiches Bild bei jedem Lauf
    farben = [(255, 255, 255), (255, 214, 92), (120, 200, 255),
              (140, 220, 150), (255, 140, 90), (200, 150, 255)]
    for i in range(46):
        w = i * 2.399963
        abstand = r * (0.42 + 0.38 * ((i * 37) % 100) / 100)
        x, y = c[0] + abstand * math.cos(w), c[1] + abstand * math.sin(w)
        lang, dick = r * 0.085, r * 0.028
        winkel = (i * 53) % 180
        dx = lang / 2 * math.cos(math.radians(winkel))
        dy = lang / 2 * math.sin(math.radians(winkel))
        zeichnen.line((x - dx, y - dy, x + dx, y + dy),
                      fill=farben[i % len(farben)] + (255,), width=round(dick))

    # Loch
    loch = r * 0.30
    zeichnen.ellipse((c[0] - loch, c[1] - loch, c[0] + loch, c[1] + loch),
                     fill=(0, 0, 0, 0))
    return bild.resize((durchmesser_px, durchmesser_px), Image.LANCZOS)


def schatten(bild, ebene_rgba, versatz, weich, deckung):
    alpha = ebene_rgba.split()[3].point(lambda v: v * deckung)
    alpha = alpha.filter(ImageFilter.GaussianBlur(weich))
    bild.paste((5, 10, 20), (versatz[0], versatz[1]), alpha)


def wippe(bild, ox, oy, breite):
    """Wippe mit Kopf links (schwer, unten) und Donut rechts (leicht, oben)."""
    boden_y = oy + round(breite * 0.50)
    dreh_y = boden_y - round(breite * 0.17)
    mitte_x = ox + breite // 2
    neigung = math.radians(10)
    halb = breite * 0.45

    z = ImageDraw.Draw(bild)
    # Bodenlinie und Bodenschatten
    boden = Image.new("L", bild.size, 0)
    ImageDraw.Draw(boden).ellipse((mitte_x - breite * 0.30, boden_y - 14,
                                   mitte_x + breite * 0.30, boden_y + 22),
                                  fill=150)
    bild.paste((6, 12, 24), (0, 0), boden.filter(ImageFilter.GaussianBlur(14)))
    z.line((mitte_x - breite * 0.34, boden_y, mitte_x + breite * 0.34, boden_y),
           fill=FARBE["bock"], width=4)
    # Bock
    z.polygon([(mitte_x - breite * 0.085, boden_y),
               (mitte_x + breite * 0.085, boden_y), (mitte_x, dreh_y)],
              fill=FARBE["bock"])

    dx, dy = halb * math.cos(neigung), halb * math.sin(neigung)
    links = (mitte_x - dx, dreh_y + dy)
    rechts = (mitte_x + dx, dreh_y - dy)

    # Kopf: steht auf dem linken Balkenende
    kopf = kopf_zeichnen(round(breite * 0.40)).rotate(
        -math.degrees(neigung), expand=True, resample=Image.BICUBIC)
    kx = round(links[0] + dx * 0.30 - kopf.width * 0.40)
    ky = round(links[1] - dy * 0.30 - kopf.height + breite * 0.012)
    schatten(bild, kopf, (kx + 14, ky + 22), 26, 0.55)
    bild.paste(kopf, (kx, ky), kopf)

    # Donut: liegt auf dem rechten, angehobenen Ende
    donut = donut_zeichnen(round(breite * 0.25))
    nx = round(rechts[0] - dx * 0.30 - donut.width / 2)
    ny = round(rechts[1] + dy * 0.30 - donut.height * 0.96)
    schatten(bild, donut, (nx + 12, ny + 20), 22, 0.5)
    bild.paste(donut, (nx, ny), donut)

    # Balken zuletzt, damit Kopf und Donut darauf stehen
    z.line((*links, *rechts), fill=FARBE["balken"], width=round(breite * 0.016))
    for ende in (links, rechts):
        r = breite * 0.008
        z.ellipse((ende[0] - r, ende[1] - r, ende[0] + r, ende[1] + r),
                  fill=FARBE["balken"])


# --- Text --------------------------------------------------------------------
def zentriert(z, text, mitte_x, y, font, farbe, sperrung=0):
    if sperrung:
        breite = sum(z.textlength(ch, font=font) for ch in text) \
            + sperrung * (len(text) - 1)
        x = mitte_x - breite / 2
        for ch in text:
            z.text((x, y), ch, font=font, fill=farbe)
            x += z.textlength(ch, font=font) + sperrung
        return
    breite = z.textlength(text, font=font)
    z.text((mitte_x - breite / 2, y), text, font=font, fill=farbe)


def passend(z, texte, schnitt, maximal, breite):
    """Größte Schrift, bei der jede Zeile in `breite` passt."""
    groesse = maximal
    while groesse > 20:
        font = schrift(schnitt, groesse)
        if all(z.textlength(t, font=font) <= breite for t in texte):
            return font
        groesse -= 2
    return schrift(schnitt, groesse)


def umbrechen(z, text, font, breite):
    zeilen, aktuell = [], ""
    for wort in text.split():
        probe = f"{aktuell} {wort}".strip()
        if z.textlength(probe, font=font) <= breite:
            aktuell = probe
        else:
            zeilen.append(aktuell)
            aktuell = wort
    if aktuell:
        zeilen.append(aktuell)
    return zeilen


def titelbild_suchen():
    """Eigenes Titelbild nur aus kopf/cover/ — bewusst ohne Rückgriff auf
    buch/cover/: Das Lebensmittelfoto der Reihe passt nicht zu diesem Titel."""
    for endung in (".png", ".jpg", ".jpeg", ".webp"):
        pfad = KOPF / "cover" / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


def randfarbe(bild, seite):
    """Mittlere Farbe eines schmalen Randstreifens — für nahtlose Übergänge."""
    b, h = bild.size
    kiste = {"oben": (0, 0, b, max(1, h // 40)),
             "unten": (0, h - max(1, h // 40), b, h),
             "links": (0, 0, max(1, b // 40), h)}[seite]
    return bild.crop(kiste).convert("RGB").resize((1, 1), Image.LANCZOS) \
        .getpixel((0, 0))


def titelbild_einsetzen(bild, pfad, x0, breite, ueberblendung):
    """Titelbild randabfallend über die Vorderseite, links weich in den Rücken.

    Füllt Vorderseite samt Anschnitt oben, rechts und unten; das Bild wird
    mittig auf das Format beschnitten. Die linke Kante läuft über
    `ueberblendung` Pixel in den Grund aus — sonst stünde am Rücken eine
    harte Kante, sobald Bild- und Grundton auch nur leicht abweichen.
    """
    foto = Image.open(pfad).convert("RGB")
    hoehe = bild.height
    faktor = max(breite / foto.width, hoehe / foto.height)
    if faktor > 1.05:
        print(f"  Titelbild wird um den Faktor {faktor:.2f} hochgerechnet "
              f"({foto.width} x {foto.height} px Vorlage).")
    foto = foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS)
    links = (foto.width - breite) // 2
    oben = (foto.height - hoehe) // 2
    foto = foto.crop((links, oben, links + breite, oben + hoehe))

    maske = Image.new("L", (breite, hoehe), 255)
    z = ImageDraw.Draw(maske)
    for i in range(ueberblendung):
        z.line((i, 0, i, hoehe), fill=round(255 * i / ueberblendung))
    bild.paste(foto, (x0, 0), maske)


def vorderseite(bild, x0, y0, b, h, cfg, titelbild=None):
    titel_max = 260
    if titelbild:
        # Das Bild trägt das Motiv oben; wie weit es nach unten reicht, hängt
        # vom Motiv ab. Deshalb stehen die Positionen in kopf.yaml unter
        # `cover:`, als Anteil der Seitenhöhe von der Trimmkante oben.
        lage = cfg.get("cover", {})
        titel_y = lage.get("titel_y", 0.495)
        kapsel_y = lage.get("kapsel_y", 0.85)
        autor_y = lage.get("autor_y", 0.928)
        titel_max = lage.get("titel_max_px", titel_max)
    else:
        leuchten(bild, (x0 + b // 2, y0 + round(h * 0.24)), round(b * 0.48),
                 (48, 74, 112), 0.6)
        wippe(bild, x0 + round(b * 0.06), y0 + round(h * 0.075),
              round(b * 0.88))
        titel_y, kapsel_y, autor_y = 0.475, 0.80, 0.905

    z = ImageDraw.Draw(bild)
    mitte = x0 + b / 2
    rand = b * 0.10

    zeile1, zeile2 = "Kopf schlägt", "Kalorien"
    titel = passend(z, [zeile1], "Black", titel_max, b - 2 * rand)
    groesse = titel.size
    y = y0 + h * titel_y
    zentriert(z, zeile1, mitte, y, titel, FARBE["text"])
    titel2 = schrift("Black", groesse * 1.16)
    zentriert(z, zeile2, mitte, y + groesse * 1.02, titel2, FARBE["akzent"])

    unten = y + groesse * 1.02 + titel2.size * 1.18
    z.rounded_rectangle((mitte - b * 0.07, unten, mitte + b * 0.07, unten + 9),
                        radius=4, fill=FARBE["akzent"])

    unter = schrift("Medium", b * 0.035)
    zeilen = ("Warum Diäten am Mindset scheitern", "und nicht am Plan")
    for i, zeile in enumerate(zeilen):
        zentriert(z, zeile, mitte, unten + 56 + i * unter.size * 1.32, unter,
                  FARBE["text_leise"])
    unter_ende = unten + 56 + (len(zeilen) - 1) * unter.size * 1.32 + unter.size

    # Hinweis auf den Arbeitsteil als Kapsel. Die Positionen aus kopf.yaml
    # sind Mindestwerte: Rückt der Titel tiefer, rücken Kapsel und Autor mit,
    # statt sich mit dem Untertitel zu überlagern.
    block_ende = unter_ende
    if cfg.get("cover", {}).get("kapsel", True):
        kapsel = schrift("SemiBold", b * 0.024)
        text = "MIT 12-WOCHEN-PROGRAMM UND ARBEITSTEIL"
        sperr = kapsel.size * 0.12
        breite = sum(z.textlength(ch, font=kapsel) for ch in text) \
            + sperr * (len(text) - 1)
        ky = max(y0 + h * kapsel_y, unter_ende + 76)
        z.rounded_rectangle((mitte - breite / 2 - 44, ky - 26,
                             mitte + breite / 2 + 44, ky + kapsel.size + 30),
                            radius=(kapsel.size + 56) / 2,
                            outline=FARBE["akzent"], width=4)
        zentriert(z, text, mitte, ky - kapsel.size * 0.06, kapsel,
                  FARBE["akzent"], sperrung=sperr)
        block_ende = ky + kapsel.size + 30

    autor = schrift("SemiBold", b * 0.036)
    ay = max(y0 + h * autor_y, block_ende + 90)
    # KDP: Text mindestens 0,125 Zoll innerhalb der Trimmkante
    if ay + autor.size > y0 + h - mm(3.2) - 10:
        raise SystemExit("Titelblock reicht zu tief — in kopf.yaml unter "
                         "cover: titel_y oder titel_max_px verkleinern.")
    zentriert(z, cfg["autor"].upper(), mitte, ay, autor,
              FARBE["text"], sperrung=autor.size * 0.22)


def rueckseite(bild, x0, y0, b, h, feld, kopf_meta, absaetze, punkte):
    z = ImageDraw.Draw(bild)
    rand = b * 0.11
    textbreite = b - 2 * rand
    links = x0 + rand

    # Barcodefeld: bleibt frei von Text, aber ohne eigene Weißfläche — KDP
    # druckt den Barcode in einer eigenen weißen Box darüber. Wie beim
    # Hardcover der Reihe (BARCODE_WEISSFLAECHE in buch/build/build_cover.py).
    fx, fy, fb, fh = feld

    # Hinweis über dem Barcodefeld, von unten gerechnet
    klein = schrift("Regular", 24)
    hinweis = umbrechen(z, HINWEIS, klein, textbreite)
    hy = fy - mm(BARCODE_LUFT_MM) - len(hinweis) * 32
    for i, zeile in enumerate(hinweis):
        z.text((links, hy + i * 32), zeile, font=klein, fill=FARBE["text_leise"])

    y = y0 + rand * 1.1
    # Schlagzeile satzweise umbrechen: Ein Satz pro Zeile liest sich ruhiger
    # als ein automatischer Umbruch mitten in der Frage.
    kopfzeile = schrift("ExtraBold", 74)
    saetze = [s.strip() + "." if not s.strip().endswith(("?", "!", "."))
              else s.strip()
              for s in kopf_meta.get("schlagzeile", "").replace("? ", "?|")
              .replace(". ", ".|").split("|") if s.strip()]
    for satz in saetze:
        for zeile in umbrechen(z, satz, kopfzeile, textbreite):
            z.text((links, y), zeile, font=kopfzeile, fill=FARBE["akzent"])
            y += kopfzeile.size * 1.18
    y += 54

    fliess = schrift("Regular", 45)
    for absatz in absaetze:
        for zeile in umbrechen(z, absatz, fliess, textbreite):
            z.text((links, y), zeile, font=fliess, fill=FARBE["text"])
            y += fliess.size * 1.42
        y += 30

    y += 20
    punkt = schrift("Medium", 43)
    for eintrag in punkte:
        r = 9
        z.ellipse((links, y + punkt.size * 0.45 - r, links + 2 * r,
                   y + punkt.size * 0.45 + r), fill=FARBE["akzent"])
        for zeile in umbrechen(z, eintrag, punkt, textbreite - 48):
            z.text((links + 48, y), zeile, font=punkt, fill=FARBE["text"])
            y += punkt.size * 1.36
        y += 16

    # Autorenblock über dem Hinweis, links neben dem Barcodefeld endend.
    # Inhalt deckungsgleich mit der Kurzbiografie in kdp-metadaten.md.
    titelzeile = schrift("SemiBold", 34)
    bio = schrift("Regular", 34)
    bio_zeilen = umbrechen(z, AUTOR_KURZ, bio, textbreite)
    ay = hy - 70 - titelzeile.size * 1.6 - len(bio_zeilen) * bio.size * 1.4
    z.line((links, ay - 44, links + textbreite, ay - 44),
           fill=(70, 92, 120), width=2)
    z.text((links, ay), "ÜBER DEN AUTOR", font=titelzeile,
           fill=FARBE["akzent"])
    for i, zeile in enumerate(bio_zeilen):
        z.text((links, ay + titelzeile.size * 1.6 + i * bio.size * 1.4),
               zeile, font=bio, fill=FARBE["text_leise"])

    if y > ay - 90:
        raise SystemExit("Rückseitentext reicht bis an den Autorenblock — "
                         "Klappentext kürzen.")


def cover_bauen(cfg, seiten, ziel_pdf, ziel_png):
    import fitz

    sf = cfg["seitenformat"]
    trim_b, trim_h = mm(sf["breite_mm"]), mm(sf["hoehe_mm"])
    anschnitt = mm(BESCHNITT_MM)
    ruecken_mm = seiten * RUECKEN_PRO_SEITE_MM
    ruecken = mm(ruecken_mm)
    gesamt_mm = (2 * sf["breite_mm"] + ruecken_mm + 2 * BESCHNITT_MM,
                 sf["hoehe_mm"] + 2 * BESCHNITT_MM)
    gesamt = (round(gesamt_mm[0] * PX_JE_MM), round(gesamt_mm[1] * PX_JE_MM))

    titelbild = titelbild_suchen()
    oben, unten = FARBE["grund_oben"], FARBE["grund_unten"]
    if titelbild:
        # Rückseite und Rücken nehmen die Randtöne des Bildes auf, damit der
        # Umschlag wie aus einem Guss wirkt.
        foto = Image.open(titelbild)
        oben, unten = randfarbe(foto, "oben"), randfarbe(foto, "unten")
        # Helles Bild (etwa Food-Fotografie auf weißem Grund): Schrift dunkel,
        # sonst stünde Papierweiß auf Papierweiß.
        r, g, b = unten
        if 0.299 * r + 0.587 * g + 0.114 * b > 150:
            FARBE.update({"text": (22, 32, 48), "text_leise": (70, 82, 98),
                          "akzent": (196, 104, 18)})
    bild = verlauf(*gesamt, oben, unten)

    # Barcodefeld in reportlab-Koordinaten (Punkt, Ursprung unten links)
    # berechnen und in Pixel von oben umrechnen — dieselbe Geometrie wie bei
    # allen anderen Umschlägen des Projekts.
    pt = 72 / DPI
    fx, fy, fb, fh = barcodefeld(anschnitt * pt, anschnitt * pt, trim_b * pt)
    feld = (round(fx / pt), round(gesamt[1] - (fy + fh) / pt),
            round(fb / pt), round(fh / pt))

    kopf_meta, absaetze, punkte = klappentext_laden(
        KOPF / "cover" / "klappentext.md")
    rueckseite(bild, anschnitt, anschnitt, trim_b, trim_h, feld,
               kopf_meta, absaetze, punkte)

    mit_ruecken_text = seiten >= RUECKENTEXT_AB_SEITEN
    if mit_ruecken_text:
        streifen = ebene((trim_h, ruecken))
        zs = ImageDraw.Draw(streifen)
        f = schrift("SemiBold", ruecken * 0.5)
        zentriert(zs, f"{cfg['titel']}  ·  {cfg['autor']}", trim_h / 2,
                  ruecken * 0.2, f, FARBE["text"])
        streifen = streifen.rotate(-90, expand=True)
        bild.paste(streifen, (anschnitt + trim_b, anschnitt), streifen)

    if titelbild:
        titelbild_einsetzen(bild, titelbild, anschnitt + trim_b + ruecken,
                            gesamt[0] - (anschnitt + trim_b + ruecken),
                            ueberblendung=mm(6))
    vorderseite(bild, anschnitt + trim_b + ruecken, anschnitt, trim_b, trim_h,
                cfg, titelbild)

    bild.save(ziel_png.with_name("cover.png"))
    bild.resize((gesamt[0] // 4, gesamt[1] // 4), Image.LANCZOS).save(ziel_png)

    # Druckdatei: ein Bild, exakte Größe, keine Schriften, keine Transparenz.
    import io
    puffer = io.BytesIO()
    bild.save(puffer, format="JPEG", quality=95, dpi=(DPI, DPI))
    breite_pt, hoehe_pt = gesamt_mm[0] * PT_JE_MM, gesamt_mm[1] * PT_JE_MM
    pdf = fitz.open()
    seite = pdf.new_page(width=breite_pt, height=hoehe_pt)
    seite.insert_image(fitz.Rect(0, 0, breite_pt, hoehe_pt),
                       stream=puffer.getvalue())
    pdf.set_metadata({"title": f"{cfg['titel']} — Umschlag",
                      "producer": "", "creator": ""})
    pdf.save(str(ziel_pdf), garbage=4, deflate=True)

    return {"gesamt_mm": gesamt_mm, "ruecken_mm": ruecken_mm,
            "ruecken_text": mit_ruecken_text, "px": gesamt,
            "titelbild": titelbild}


def main():
    cfg = yaml.safe_load((KOPF / "kopf.yaml").read_text(encoding="utf-8"))
    out = KOPF / "out"
    seiten = seitenzahl(out / f"{cfg['slug']}-druck.pdf")
    ziel = out / "cover-druck.pdf"
    masse = cover_bauen(cfg, seiten, ziel, out / "cover-vorschau.png")

    b, h = masse["gesamt_mm"]
    print(f"Taschenbuch — Innenteil: {seiten} Seiten")
    print(f"Rückenbreite: {masse['ruecken_mm']:.2f} mm"
          f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
    print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
          f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {BESCHNITT_MM} mm Anschnitt"
          f", {masse['px'][0]} x {masse['px'][1]} px bei {DPI} dpi")
    print("Titelbild: " + (str(masse["titelbild"].relative_to(WURZEL))
                           if masse["titelbild"] else "keins, Wippe gezeichnet"))
    print(f"  → {ziel.relative_to(WURZEL)}  (zu KDP hochladen)")
    print(f"  → {(out / 'cover-vorschau.png').relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
