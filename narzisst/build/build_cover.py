#!/usr/bin/env python3
"""Baut die KDP-Umschläge (Taschenbuch und Hardcover) für „Der Narzisst in
meinem Bett".

    python3 narzisst/build/build_cover.py

Der Innenteil muss vorher gebaut sein — die Rückenbreite ergibt sich aus der
Seitenzahl. Anschnitt, Rückenformel, Hardcover-Maße und Barcodefeld kommen aus
buch/build/build_cover.py, die Bild- und Textwerkzeuge aus
kopf/build/build_cover.py. Gesetzt wird wie dort direkt als Rasterbild bei
300 dpi und als einzelnes Bild in ein PDF exakter Größe gelegt: keine
Schriften, keine Transparenz, keine Ebenen.

Motiv: das Foto unter narzisst/cover/titelbild.png — ein dunkles
Schlafzimmer um 3:33 Uhr, eine Person allein unter der Decke. Ohne Foto
zeichnet das Skript einen gesprungenen Spiegel mit Krone.

Das Foto ist mit Higgsfield erzeugt; das Wasserzeichen unten rechts ist aus
der Vorlage herausgeschnitten (der Streifen war fast schwarz, vom Motiv fehlt
nichts). Die Vorlage hat 896 × 1110 px und wird beim Bauen hochgerechnet.
"""

import importlib.util
import io
import math
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFilter

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "narzisst"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM, BESCHNITT_MM,  # noqa: E402
                         BUCHDECKE_MM, HARDCOVER_MIN_SEITEN,
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN, WRAP_MM,
                         barcodefeld, klappentext_laden, seitenzahl)


def _kopf_umschlag():
    """kopf/build/build_cover.py unter eigenem Namen laden — unter
    „build_cover" fände Python das Skript der Reihe in buch/build/."""
    pfad = WURZEL / "kopf" / "build" / "build_cover.py"
    spec = importlib.util.spec_from_file_location("kopf_cover", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


K = _kopf_umschlag()
DPI, PX_JE_MM, PT_JE_MM, SS = K.DPI, K.PX_JE_MM, K.PT_JE_MM, K.SS
mm, schrift, verlauf, leuchten = K.mm, K.schrift, K.verlauf, K.leuchten
zentriert, passend, umbrechen, ebene = (K.zentriert, K.passend, K.umbrechen,
                                        K.ebene)

FARBE = {
    "grund_oben": (30, 14, 32),
    "grund_unten": (58, 24, 50),
    "text": (247, 238, 232),
    "text_leise": (214, 192, 204),
    "akzent": (240, 168, 150),
    "gold_hell": (246, 214, 150),
    "gold": (212, 164, 88),
    "gold_tief": (138, 92, 40),
    "glas_oben": (92, 70, 104),
    "glas_unten": (26, 18, 38),
    "linie": (110, 66, 104),
}

HINWEIS = ("Kein medizinischer oder psychotherapeutischer Ratgeber und kein "
           "Ersatz für Beratung oder Therapie. Bei Gewalt: Notruf 110 · "
           "Hilfetelefon 116 016.")

# Deckungsgleich mit der Kurzbiografie in kdp-metadaten.md.
AUTOR_KURZ = ("Mark von Daak lebt in Wolfsburg und schreibt Ratgeber über die "
              "Themen, an denen Menschen im Alltag scheitern. Er ist kein "
              "Psychologe — dieses Buch übersetzt Forschung und "
              "Beratungspraxis in klare Worte.")


# Farben, wenn das Foto den Umschlag trägt: kühles Blaugrau statt Aubergine,
# damit Rücken und Rückseite zum Foto passen. Rosé bleibt als Akzent — der
# einzige warme Ton auf dem Umschlag.
FOTO_FARBE = {
    "text_leise": (196, 206, 218),
    "linie": (72, 88, 106),
}

# Ab diesem Anteil der Höhe wird das Foto nach unten abgedunkelt, damit der
# Titel auf ruhigem Grund steht. Gerechnet ins Bild, nicht als transparente
# Ebene — die Druckdatei darf keine Transparenz enthalten.
ABDUNKELN_AB = 0.50


def titelbild_suchen():
    for endung in (".png", ".jpg", ".jpeg", ".webp"):
        pfad = BAND / "cover" / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


# Wo der Ausschnitt waagerecht sitzt, wenn das Foto breiter ist als die
# Vorderseite: 0 = linker Rand, 0,5 = Mitte. Etwas links der Mitte, damit
# Kopfteil und Kopf der schlafenden Person im Bild bleiben; das Fenster
# rechts bleibt trotzdem ganz sichtbar.
AUSSCHNITT_X = 0.3


def titelbild_einsetzen(bild, pfad, x0, breite, ueberblendung):
    """Wie kopf/build/build_cover.py, aber mit waagerechtem Anker."""
    foto = Image.open(pfad).convert("RGB")
    hoehe = bild.height
    faktor = max(breite / foto.width, hoehe / foto.height)
    if faktor > 1.05:
        print(f"  Titelbild wird um den Faktor {faktor:.2f} hochgerechnet "
              f"({foto.width} x {foto.height} px Vorlage).")
    foto = foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS)
    links = round((foto.width - breite) * AUSSCHNITT_X)
    oben = (foto.height - hoehe) // 2
    foto = foto.crop((links, oben, links + breite, oben + hoehe))
    maske = Image.new("L", (breite, hoehe), 255)
    z = ImageDraw.Draw(maske)
    for i in range(ueberblendung):
        z.line((i, 0, i, hoehe), fill=round(255 * i / ueberblendung))
    bild.paste(foto, (x0, 0), maske)


def abdunkeln(bild, x0, y0, b, h, grund):
    """Unterer Teil der Vorderseite läuft in den Grundton aus."""
    start = round(y0 + h * ABDUNKELN_AB)
    maske = Image.new("L", bild.size, 0)
    z = ImageDraw.Draw(maske)
    for y in range(start, bild.height):
        t = min(1.0, (y - start) / (h * 0.30))
        z.line((x0, y, x0 + b, y), fill=round(255 * 0.82 * t ** 1.3))
    bild.paste(grund, (0, 0), maske)


# --- Motiv -------------------------------------------------------------------
def oval_maske(groesse, kasten):
    m = Image.new("L", groesse, 0)
    ImageDraw.Draw(m).ellipse(kasten, fill=255)
    return m


def riss(zeichnen, start, winkel, laenge, staerke, tiefe, zufall):
    """Ein gezackter Sprung, der sich verzweigt — fest verteilt, damit jeder
    Lauf dasselbe Bild ergibt."""
    x, y = start
    punkte = [(x, y)]
    schritte = 7
    for i in range(schritte):
        abweichung = math.radians(((zufall * 37 + i * 53) % 41) - 20)
        w = winkel + abweichung
        s = laenge / schritte * (0.7 + ((zufall + i * 17) % 10) / 16)
        x, y = x + s * math.cos(w), y + s * math.sin(w)
        punkte.append((x, y))
        if tiefe > 0 and i in (2, 4):
            seite = 1 if (zufall + i) % 2 else -1
            riss(zeichnen, (x, y), w + seite * math.radians(38),
                 laenge * 0.42, max(1, staerke * 0.6), tiefe - 1,
                 zufall * 3 + i)
    zeichnen.line(punkte, fill=255, width=max(1, round(staerke)),
                  joint="curve")


def spiegel_zeichnen(breite):
    """Ovaler Spiegel mit Goldrahmen, Krone und Sprung, als RGBA-Bild."""
    b = breite * SS
    rx, ry = b * 0.40, b * 0.50
    rahmen = b * 0.055
    h = round(2 * ry + rahmen * 2 + b * 0.26)
    mx, my = b / 2, h - ry - rahmen - b * 0.02
    bild = ebene((round(b), h))
    groesse = bild.size

    aussen = (mx - rx - rahmen, my - ry - rahmen, mx + rx + rahmen,
              my + ry + rahmen)
    innen = (mx - rx, my - ry, mx + rx, my + ry)

    # Goldrahmen: Verlauf von links oben hell nach rechts unten tief
    gold = verlauf(groesse[0], groesse[1], FARBE["gold_hell"],
                   FARBE["gold_tief"]).rotate(-25, resample=Image.BICUBIC,
                                              fillcolor=FARBE["gold_tief"],
                                              expand=False)
    ring = ImageChops.subtract(oval_maske(groesse, aussen),
                               oval_maske(groesse, innen))
    bild.paste(gold, (0, 0), ring)
    # feine Kehlung im Rahmen
    z = ImageDraw.Draw(bild)
    k = rahmen * 0.45
    z.ellipse((aussen[0] + k, aussen[1] + k, aussen[2] - k, aussen[3] - k),
              outline=FARBE["gold_tief"] + (255,), width=round(b * 0.004))
    z.ellipse((aussen[0] + 3, aussen[1] + 3, aussen[2] - 3, aussen[3] - 3),
              outline=FARBE["gold_hell"] + (255,), width=round(b * 0.003))
    # Perlen auf dem Rahmen
    for i in range(36):
        w = 2 * math.pi * i / 36
        px = mx + (rx + rahmen * 0.5) * math.cos(w)
        py = my + (ry + rahmen * 0.5) * math.sin(w)
        r = b * 0.0075
        z.ellipse((px - r, py - r, px + r, py + r),
                  fill=FARBE["gold_hell"] + (255,))

    # Glas
    glas = verlauf(groesse[0], groesse[1], FARBE["glas_oben"],
                   FARBE["glas_unten"])
    glasmaske = oval_maske(groesse, innen)
    bild.paste(glas, (0, 0), glasmaske)
    # schräger Glanz
    glanz = Image.new("L", groesse, 0)
    gz = ImageDraw.Draw(glanz)
    for versatz, deckung, dicke in ((-0.18, 70, 0.10), (0.02, 40, 0.05)):
        x0 = mx + rx * versatz
        gz.polygon([(x0 - rx * 0.5, my + ry), (x0 - rx * 0.5 + rx * dicke,
                                                my + ry),
                    (x0 + rx * 0.6 + rx * dicke, my - ry),
                    (x0 + rx * 0.6, my - ry)], fill=deckung)
    glanz = ImageChops.multiply(glanz.filter(ImageFilter.GaussianBlur(b * 0.01)),
                                glasmaske)
    bild.paste(Image.new("RGB", groesse, (255, 236, 244)), (0, 0), glanz)

    # Sprung: helle Linie mit dunklem Schatten, nur innerhalb des Glases
    sprung = Image.new("L", groesse, 0)
    sz = ImageDraw.Draw(sprung)
    zentrum = (mx + rx * 0.22, my - ry * 0.12)
    for i, w in enumerate((200, 255, 330, 20, 95, 140)):
        riss(sz, zentrum, math.radians(w), ry * (1.1 if i % 2 else 0.9),
             b * 0.0035, 1, i + 3)
    sprung = ImageChops.multiply(sprung, glasmaske)
    schatten = ImageChops.offset(sprung, round(b * 0.003), round(b * 0.003))
    bild.paste((8, 4, 14), (0, 0), schatten.point(lambda v: v * 0.8))
    bild.paste((236, 226, 240), (0, 0), sprung)
    # Aufschlagpunkt
    r = b * 0.012
    z.ellipse((zentrum[0] - r, zentrum[1] - r, zentrum[0] + r, zentrum[1] + r),
              fill=(240, 232, 244, 255))

    # Krone auf dem Rahmen, leicht schräg
    krone = ebene((round(b * 0.30), round(b * 0.22)))
    kb, kh = krone.size
    kz = ImageDraw.Draw(krone)
    zacken = [(0.0, 1.0), (0.0, 0.45), (0.2, 0.72), (0.33, 0.12),
              (0.5, 0.62), (0.67, 0.12), (0.8, 0.72), (1.0, 0.45),
              (1.0, 1.0)]
    kmaske = Image.new("L", krone.size, 0)
    ImageDraw.Draw(kmaske).polygon([(x * kb, y * kh * 0.82 + kh * 0.05)
                                    for x, y in zacken], fill=255)
    krone.paste(verlauf(kb, kh, FARBE["gold_hell"], FARBE["gold_tief"]),
                (0, 0), kmaske)
    kz.rectangle((0, kh * 0.80, kb, kh * 0.87), fill=FARBE["gold_tief"] + (255,))
    for x, y in ((0.0, 0.45), (0.33, 0.12), (0.67, 0.12), (1.0, 0.45)):
        r = kb * 0.045
        cx = min(max(x * kb, r), kb - r)
        cy = y * kh * 0.82 + kh * 0.05
        kz.ellipse((cx - r, cy - r, cx + r, cy + r),
                   fill=FARBE["gold_hell"] + (255,))
    for x in (0.25, 0.5, 0.75):
        r = kb * 0.03
        kz.ellipse((x * kb - r, kh * 0.835 - r, x * kb + r, kh * 0.835 + r),
                   fill=FARBE["akzent"] + (255,))
    krone = krone.rotate(12, expand=True, resample=Image.BICUBIC)
    kx = round(mx - krone.width / 2 + b * 0.06)
    ky = round(aussen[1] - krone.height * 0.78)
    bild.alpha_composite(krone, (kx, max(0, ky)))

    return bild.resize((breite, round(h / SS)), Image.LANCZOS)


def motiv(bild, x0, y0, b, h):
    leuchten(bild, (x0 + b // 2, y0 + round(h * 0.25)), round(b * 0.46),
             (112, 44, 92), 0.55)
    sp = spiegel_zeichnen(round(b * 0.42))
    sx = round(x0 + (b - sp.width) / 2)
    sy = round(y0 + h * 0.035)
    alpha = sp.split()[3].filter(ImageFilter.GaussianBlur(24))
    bild.paste((6, 2, 10), (sx + 16, sy + 26), alpha.point(lambda v: v * 0.6))
    bild.paste(sp, (sx, sy), sp)
    return sy + sp.height


# --- Seiten ------------------------------------------------------------------
def vorderseite(bild, x0, y0, b, h, cfg, foto=False, titel_y=None):
    lage = cfg.get("cover", {})
    if foto:
        titel_max = lage.get("titel_max_px", 200)
        y = y0 + h * (titel_y or lage.get("titel_y", 0.585))
    else:
        motiv_ende = motiv(bild, x0, y0, b, h)
        titel_max = 230
        y = max(motiv_ende + h * 0.035, y0 + h * 0.47)
    z = ImageDraw.Draw(bild)
    mitte = x0 + b / 2
    rand = b * 0.10

    zeilen = lage.get("titelzeilen") or [cfg["titel"]]
    font = passend(z, zeilen[:-1] or zeilen, "Black", titel_max, b - 2 * rand)
    letzte = schrift("Black", font.size * 1.22)
    for zeile in zeilen[:-1]:
        zentriert(z, zeile, mitte, y, font, FARBE["text"])
        y += font.size * 1.04
    zentriert(z, zeilen[-1], mitte, y - font.size * 0.02, letzte,
              FARBE["akzent"])
    y += letzte.size * 1.18

    z.rounded_rectangle((mitte - b * 0.07, y, mitte + b * 0.07, y + 9),
                        radius=4, fill=FARBE["akzent"])
    unter = schrift("Medium", b * 0.034)
    untertitel = lage.get("untertitelzeilen") or [cfg["untertitel"]]
    for i, zeile in enumerate(untertitel):
        zentriert(z, zeile, mitte, y + 52 + i * unter.size * 1.32, unter,
                  FARBE["text_leise"])
    unter_ende = y + 52 + (len(untertitel) - 1) * unter.size * 1.32 + unter.size

    autor = schrift("SemiBold", b * 0.036)
    ay = max(y0 + h * 0.915, unter_ende + 80)
    # KDP: Text mindestens 0,125 Zoll innerhalb der Trimmkante
    if ay + autor.size > y0 + h - mm(3.2) - 10:
        raise SystemExit("Titelblock reicht zu tief — Spiegel verkleinern "
                         "oder Titelschrift (titel_max) reduzieren.")
    zentriert(z, cfg["autor"].upper(), mitte, ay, autor, FARBE["text"],
              sperrung=autor.size * 0.22)


def rueckseite(bild, x0, y0, b, h, feld, kopf_meta, absaetze, punkte):
    z = ImageDraw.Draw(bild)
    rand = b * 0.11
    textbreite = b - 2 * rand
    links = x0 + rand
    fx, fy, fb, fh = feld   # Barcodefeld bleibt frei, ohne eigene Weißfläche

    klein = schrift("Regular", 26)
    hinweis = umbrechen(z, HINWEIS, klein, textbreite)
    hy = fy - mm(BARCODE_LUFT_MM) - len(hinweis) * 34
    for i, zeile in enumerate(hinweis):
        z.text((links, hy + i * 34), zeile, font=klein,
               fill=FARBE["text_leise"])

    y = y0 + rand * 1.1
    kopfzeile = schrift("ExtraBold", 74)
    saetze = [s.strip() for s in kopf_meta.get("schlagzeile", "")
              .replace("? ", "?|").replace(". ", ".|").split("|") if s.strip()]
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
    fett, normal = schrift("Bold", 43), schrift("Regular", 43)
    for eintrag in punkte:
        r = 9
        z.ellipse((links, y + fett.size * 0.45 - r, links + 2 * r,
                   y + fett.size * 0.45 + r), fill=FARBE["akzent"])
        kopf, _, rest = eintrag.partition(": ")
        z.text((links + 48, y), kopf + ":", font=fett, fill=FARBE["text"])
        einzug = z.textlength(kopf + ": ", font=fett)
        zeilen = umbrechen(z, rest, normal, textbreite - 48 - einzug)
        for i, zeile in enumerate(zeilen):
            z.text((links + 48 + einzug, y), zeile, font=normal,
                   fill=FARBE["text_leise"])
            y += normal.size * 1.36
        y += 16

    titelzeile = schrift("SemiBold", 34)
    bio = schrift("Regular", 34)
    bio_zeilen = umbrechen(z, AUTOR_KURZ, bio, textbreite)
    ay = hy - 70 - titelzeile.size * 1.6 - len(bio_zeilen) * bio.size * 1.4
    z.line((links, ay - 44, links + textbreite, ay - 44),
           fill=FARBE["linie"], width=2)
    z.text((links, ay), "ÜBER DEN AUTOR", font=titelzeile,
           fill=FARBE["akzent"])
    for i, zeile in enumerate(bio_zeilen):
        z.text((links, ay + titelzeile.size * 1.6 + i * bio.size * 1.4),
               zeile, font=bio, fill=FARBE["text_leise"])

    if y > ay - 90:
        raise SystemExit("Rückseitentext reicht bis an den Autorenblock — "
                         "Klappentext kürzen.")


def cover_bauen(cfg, seiten, ziel_pdf, ziel_png, *, hardcover=False):
    """Taschenbuch oder Hardcover — die Unterschiede stehen in buch/README.md:
    18 mm Umschlagrand statt 3,175 mm Anschnitt, 9 mm mehr Rücken, Barcodefeld
    um das Scharnier nach innen, Rückentext unabhängig von der Seitenzahl."""
    import fitz

    sf = cfg["seitenformat"]
    trim_b, trim_h = mm(sf["breite_mm"]), mm(sf["hoehe_mm"])
    rand_mm = WRAP_MM if hardcover else BESCHNITT_MM
    anschnitt = mm(rand_mm)
    ruecken_mm = seiten * RUECKEN_PRO_SEITE_MM + (BUCHDECKE_MM if hardcover
                                                  else 0)
    ruecken = mm(ruecken_mm)
    gesamt_mm = (2 * sf["breite_mm"] + ruecken_mm + 2 * rand_mm,
                 sf["hoehe_mm"] + 2 * rand_mm)
    gesamt = (round(gesamt_mm[0] * PX_JE_MM), round(gesamt_mm[1] * PX_JE_MM))

    titelbild = titelbild_suchen()
    oben, unten = FARBE["grund_oben"], FARBE["grund_unten"]
    if titelbild:
        foto = Image.open(titelbild)
        oben, unten = K.randfarbe(foto, "oben"), K.randfarbe(foto, "unten")
        # Rückseite etwas aufhellen: Das Foto läuft unten in fast reines
        # Schwarz aus, und auf Schwarz wirkt der Klappentext hart.
        unten = tuple(max(c, w) for c, w in zip(unten, (14, 18, 24)))
        FARBE.update(FOTO_FARBE)
    bild = verlauf(*gesamt, oben, unten)

    pt = 72 / DPI
    fx, fy, fb, fh = barcodefeld(anschnitt * pt, anschnitt * pt, trim_b * pt,
                                 hardcover=hardcover)
    feld = (round(fx / pt), round(gesamt[1] - (fy + fh) / pt),
            round(fb / pt), round(fh / pt))

    kopf_meta, absaetze, punkte = klappentext_laden(
        BAND / "cover" / "klappentext.md")
    rueckseite(bild, anschnitt, anschnitt, trim_b, trim_h, feld,
               kopf_meta, absaetze, punkte)

    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN
    if mit_ruecken_text:
        streifen = ebene((trim_h, ruecken))
        zs = ImageDraw.Draw(streifen)
        f = schrift("SemiBold", min(ruecken * 0.38, mm(5)))
        oberkante, _, _, unterkante = zs.textbbox((0, 0), cfg["titel"], font=f)
        zentriert(zs, f"{cfg['titel']}  ·  {cfg['autor']}", trim_h / 2,
                  (ruecken - (unterkante - oberkante)) / 2 - oberkante, f,
                  FARBE["text"])
        streifen = streifen.rotate(-90, expand=True)
        bild.paste(streifen, (anschnitt + trim_b, anschnitt), streifen)

    vorne = anschnitt + trim_b + ruecken
    if titelbild:
        titelbild_einsetzen(bild, titelbild, vorne, gesamt[0] - vorne,
                              ueberblendung=mm(6))
        abdunkeln(bild, vorne, anschnitt, gesamt[0] - vorne, trim_h, unten)
    vorderseite(bild, vorne, anschnitt, trim_b, trim_h, cfg,
                foto=bool(titelbild))

    bild.save(ziel_png.with_name(ziel_pdf.stem.replace("-druck", "") + ".png"))
    bild.resize((gesamt[0] // 4, gesamt[1] // 4), Image.LANCZOS).save(ziel_png)

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
            "rand_mm": rand_mm, "ruecken_text": mit_ruecken_text,
            "px": gesamt, "titelbild": titelbild}


def main():
    cfg = yaml.safe_load((BAND / "narzisst.yaml").read_text(encoding="utf-8"))
    out = BAND / "out"
    seiten = seitenzahl(out / f"{cfg['slug']}-druck.pdf")

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue
        ziel = out / f"{name}-druck.pdf"
        vorschau_png = out / f"{name}-vorschau.png"
        masse = cover_bauen(cfg, seiten, ziel, vorschau_png,
                            hardcover=hardcover)
        b, h = masse["gesamt_mm"]
        randname = ("Umschlagrand um die Buchdecke" if hardcover
                    else "Anschnitt")
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.2f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. "
              f"{masse['rand_mm']:.3f} mm {randname}"
              f", {masse['px'][0]} x {masse['px'][1]} px bei {DPI} dpi")
        print("Titelbild: " + (str(masse["titelbild"].relative_to(WURZEL))
                               if masse["titelbild"]
                               else "keins, Spiegel gezeichnet"))
        print(f"  → {ziel.relative_to(WURZEL)}  (zu KDP hochladen)")
        print(f"  → {vorschau_png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
