#!/usr/bin/env python3
"""Farbwelt, Motiv und Flächen des Umschlags von Band 4.

Eigenes Modul, weil zwei Skripte dieselbe Gestaltung brauchen — der gedruckte
Umschlag (`build_cover.py`) und das Kindle-Titelbild (`kindle_titelbild.py`).
Läge sie in einem der beiden, müsste das andere es importieren; da im
Suchpfad gleichzeitig `buch/build/build_cover.py` liegt, verdeckten sich zwei
Module gleichen Namens gegenseitig.

**Bewusst nicht die Bildsprache der Stoffwechsel-Reihe.** Band 4 gehört
thematisch nicht dazu, und im Regal soll niemand eine Reihe vermuten, die es
nicht gibt. Aus `buch/build` kommen nur bandneutrale Bausteine: Schriften,
Zeilenumbruch, Textblöcke und die Geometrie des Barcodefeldes.
"""

import io
import math
import random
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM,  # noqa: E402
                         barcodefeld_freistellen, block_schreiben,
                         groesse_einpassen, umbrechen, weissflaeche)

# --- Farbwelt ----------------------------------------------------------------
# Tiefes Tintenblau statt des Schiefergraus der Reihe, dazu ein warmer
# Bernstein als Akzent. Beide Töne stehen außerhalb der Palette der drei
# Ernährungsbände.
#
# Kontraste gegen den helleren der beiden Grundtöne (#1E2937), gerundet:
#   text  14,5:1     text_leise  9,8:1     akzent  7,1:1
# Alle drei liegen über 4,5:1 und damit auch für normalgroße Schrift im
# grünen Bereich. Wer am Grund dreht, rechnet sie nach.
FARBEN = {
    "grund": HexColor("#1E2937"),
    "grund_tief": HexColor("#161E29"),
    "text": HexColor("#F3F6F9"),
    "text_leise": HexColor("#C7D1DC"),
    "akzent": HexColor("#F2A65A"),
    "raster_chaos": HexColor("#5C6B7C"),
    "raster_ordnung": HexColor("#F2A65A"),
}

# Das Motiv: ein Strichraster, das von links nach rechts aus der Unordnung in
# die Ordnung kippt — die These des Buches als Bild. Feste Zufallszahl, damit
# jeder Build denselben Umschlag erzeugt; ohne sie sähe jede Auflage anders
# aus und Korrekturabzüge ließen sich nicht vergleichen.
MOTIV_SAAT = 20260824
MOTIV_FAEDEN = 21        # Fäden über die Breite
MOTIV_SEGMENTE = 44      # Teilstücke je Faden — je Stück eine eigene Farbe
MOTIV_AUFLOESUNG = 4     # Stützpunkte je Teilstück
MOTIV_AUSSCHLAG = 0.42   # größter Ausschlag links, Anteil der Motivhöhe

# Kein Markenhinweis: In diesem Band kommt keine fremde Marke vor. An seine
# Stelle tritt der Hinweis, der für ein Buch über ein medizinisches Thema
# tatsächlich nötig ist.
RECHTSHINWEIS = (
    "Kein medizinischer Ratgeber. Dieses Buch stellt keine Diagnose und "
    "ersetzt weder Diagnostik noch Beratung oder Behandlung — bitte die "
    "Hinweise im Buch beachten."
)

#: Grundgrößen des Rückseitentexts: (Schlagzeile, Fließtext, Stichpunkt).
RUECKEN_GROESSEN = (19.0, 12.0, 11.5)


# --- Grund und Motiv ---------------------------------------------------------
def tintengrund(c, x, y, breite, hoehe, stufen=48):
    """Flacher senkrechter Verlauf, gestuft aus Vollton-Rechtecken.

    Bewusst ohne reportlabs Verlaufsfunktion: Die Druckfassung wird ohnehin
    gerastert, und gestufte Volltonflächen bleiben auch in der Vektorfassung
    frei von Transparenz — genau das, woran KDPs Prüfung sonst hängenbleibt.
    """
    oben, unten = FARBEN["grund"], FARBEN["grund_tief"]
    for i in range(stufen):
        t = i / (stufen - 1)
        c.setFillColorRGB(
            oben.red + (unten.red - oben.red) * t,
            oben.green + (unten.green - oben.green) * t,
            oben.blue + (unten.blue - oben.blue) * t,
        )
        # Eine Haarlinie Überlappung, sonst blitzt zwischen den Stufen der
        # weiße Seitengrund durch.
        c.rect(x, y + hoehe * (1 - (i + 1) / stufen),
               breite, hoehe / stufen + 0.6, stroke=0, fill=1)


def _farbmischung(c, a, b, t):
    """Setzt die Strichfarbe zwischen zwei Tönen."""
    c.setStrokeColorRGB(a.red + (b.red - a.red) * t,
                        a.green + (b.green - a.green) * t,
                        a.blue + (b.blue - a.blue) * t)


def fadenmotiv(c, x, y, breite, hoehe):
    """Fäden, die links verknotet liegen und sich nach rechts entwirren.

    Die These des Buches als Bild: Dieselben Fäden, dieselbe Zahl, dieselbe
    Länge — links unbrauchbar verschlungen, rechts in Ordnung. Nicht „vorher
    schlecht, nachher gut", sondern dasselbe Material, anders geführt.

    Jeder Faden ist die Summe dreier Sinuswellen mit eigener Frequenz und
    Phase. Ihre Amplitude fällt nach rechts auf null ab, deshalb läuft jeder
    Faden dort exakt waagerecht in seine Spur ein — ohne dass die Endlage
    eigens gesetzt werden müsste.

    Gezeichnet wird in Teilstücken statt als ein Pfad, weil ein Pfad nur eine
    Strichfarbe haben kann: Erst die stückweise Färbung ergibt den Übergang
    von Schiefer nach Bernstein. Ohne Transparenz — die Vektorfassung soll
    frei davon bleiben, daran hängt sonst KDPs Prüfung.
    """
    zufall = random.Random(MOTIV_SAAT)
    chaos_f, ordnung_f = FARBEN["raster_chaos"], FARBEN["raster_ordnung"]
    schritte = MOTIV_SEGMENTE * MOTIV_AUFLOESUNG

    c.setLineCap(1)
    c.setLineJoin(1)
    for i in range(MOTIV_FAEDEN):
        lage = (i + 0.5) / MOTIV_FAEDEN
        spur_y = y + hoehe * lage
        # Der Ausschlag läuft zu den Rändern des Feldes hin aus. Ohne das
        # schwingen die äußeren Fäden aus ihrem Rahmen — nach oben in den
        # Untertitel, nach unten quer durch die Autorenzeile. Nebenbei sieht
        # es richtiger aus: ein Bündel liegt außen enger als in der Mitte.
        randabfall = math.sin(math.pi * lage) ** 0.55
        # Drei Wellen je Faden: eine lange für den groben Schwung, zwei
        # kürzere für die Verschlingung. Ohne die kurzen sähe es nach Welle
        # aus, nicht nach Knoten.
        wellen = [(zufall.uniform(0.6, 1.4), zufall.uniform(0, 2 * math.pi), 1.00),
                  (zufall.uniform(2.2, 3.8), zufall.uniform(0, 2 * math.pi), 0.62),
                  (zufall.uniform(4.5, 7.0), zufall.uniform(0, 2 * math.pi), 0.38),
                  (zufall.uniform(8.0, 12.0), zufall.uniform(0, 2 * math.pi), 0.18)]
        gewicht = 1 / sum(a for _, _, a in wellen)

        def punkt(u):
            # Nach rechts fällt der Ausschlag auf null — der Faden läuft in
            # seine Spur ein. Hoch potenziert, damit die Auflösung erst im
            # letzten Drittel geschieht und nicht schon in der Mitte.
            unruhe = (1 - u) ** 1.9
            versatz = sum(a * math.sin(f * u * 2 * math.pi + ph)
                          for f, ph, a in wellen) * gewicht
            return (x + breite * u,
                    spur_y + versatz * hoehe * MOTIV_AUSSCHLAG
                    * randabfall * unruhe)

        for seg in range(MOTIV_SEGMENTE):
            u0 = seg / MOTIV_SEGMENTE
            t_farbe = u0 ** 1.5
            _farbmischung(c, chaos_f, ordnung_f, t_farbe)
            c.setLineWidth(0.9 + 1.3 * t_farbe)

            pfad = c.beginPath()
            px, py = punkt(u0)
            pfad.moveTo(px, py)
            for k in range(1, MOTIV_AUFLOESUNG + 1):
                px, py = punkt((seg * MOTIV_AUFLOESUNG + k) / schritte)
                pfad.lineTo(px, py)
            c.drawPath(pfad, stroke=1, fill=0)
    c.setLineCap(0)
    c.setLineJoin(0)


# --- Titelbild ------------------------------------------------------------
#: Liegt hier eine Datei, füllt sie die Vorderseite und ersetzt das gezeichnete
#: Fadenmotiv. Gesucht wird **nur** in adhs/cover — anders als bei der Reihe
#: gibt es bewusst keinen Rückgriff auf buch/cover/titelbild.jpg: Das ist das
#: Lebensmittelfoto der Ernährungsbände und hätte hier nichts zu suchen.
TITELBILD_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp")

#: Anteil der Bildhöhe, über den das Bild oben in den Grund übergeht. Darüber
#: stehen Titel und Untertitel, und die brauchen ruhigen Grund.
TITELBILD_UEBERBLENDUNG = 0.46


def titelbild_suchen(verzeichnis=None):
    verzeichnis = Path(verzeichnis or WURZEL / "adhs" / "cover")
    for endung in TITELBILD_ENDUNGEN:
        pfad = verzeichnis / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


def titelbild_sollmasse(breite_mm, hoehe_mm, dpi=300):
    """Wie groß das Titelbild mindestens sein sollte, in Pixeln."""
    je_mm = dpi / 25.4
    return round(breite_mm * je_mm), round(hoehe_mm * je_mm)


def titelbild_melden(pfad, breite_mm, hoehe_mm):
    """Sagt beim Bauen, ob das Titelbild für den Druck reicht.

    KDP verlangt 300 dpi über die belichtete Fläche. Ein zu kleines Bild wird
    nicht abgelehnt, aber es wird im Druck weich — und das sieht man auf einem
    dunklen Umschlag sofort.
    """
    if not pfad:
        return "kein Titelbild — gezeichnetes Fadenmotiv"

    from PIL import Image
    with Image.open(pfad) as bild:
        ist_b, ist_h = bild.size
    soll_b, soll_h = titelbild_sollmasse(breite_mm, hoehe_mm)
    dpi = min(ist_b / breite_mm, ist_h / hoehe_mm) * 25.4
    zustand = "reicht" if ist_b >= soll_b and ist_h >= soll_h else \
        f"ZU KLEIN, empfohlen {soll_b} x {soll_h} px"
    return (f"{pfad.name}: {ist_b} x {ist_h} px "
            f"= rund {dpi:.0f} dpi auf dieser Fläche — {zustand}")


def titelbild_aufbereiten(pfad, seitenverhaeltnis, breite_px=1800):
    """Beschneidet das Bild und blendet es oben in den Grundton über.

    Das Abdunkeln geschieht **im Bild**, nicht als Fläche darüber: Ein Schleier
    im PDF wäre Transparenz, und die Vektorfassung soll frei davon bleiben.
    Nebenbei ist es das bessere Ergebnis — der Übergang lässt sich pixelgenau
    steuern statt über eine Deckkraft.

    `seitenverhaeltnis` ist Höhe geteilt durch Breite der Zielfläche. Das Bild
    wird mittig auf dieses Verhältnis beschnitten, nicht verzerrt.
    """
    from PIL import Image

    bild = Image.open(pfad).convert("RGB")
    b, h = bild.size
    soll_h = b * seitenverhaeltnis
    if soll_h <= h:
        # zu hoch — oben und unten beschneiden, dabei die untere Hälfte
        # bevorzugen: dort liegt bei diesem Motiv die Auflösung ins Geordnete.
        rest = h - soll_h
        oben = rest * 0.35
        bild = bild.crop((0, round(oben), b, round(oben + soll_h)))
    else:
        # zu breit — links und rechts gleichmäßig beschneiden
        soll_b = h / seitenverhaeltnis
        rand = (b - soll_b) / 2
        bild = bild.crop((round(rand), 0, round(b - rand), h))

    hoehe_px = round(breite_px * seitenverhaeltnis)
    bild = bild.resize((breite_px, hoehe_px), Image.LANCZOS)

    grund = FARBEN["grund"]
    gr = (round(grund.red * 255), round(grund.green * 255),
          round(grund.blue * 255))
    pixel = bild.load()
    blende = max(1, round(hoehe_px * TITELBILD_UEBERBLENDUNG))
    for zeile in range(blende):
        # 1 ganz oben (voller Grundton) bis 0 am Ende der Überblendung
        anteil = (1 - zeile / blende) ** 1.35
        for spalte in range(breite_px):
            r, g, b_ = pixel[spalte, zeile]
            pixel[spalte, zeile] = (
                round(r + (gr[0] - r) * anteil),
                round(g + (gr[1] - g) * anteil),
                round(b_ + (gr[2] - b_) * anteil),
            )

    puffer = io.BytesIO()
    bild.save(puffer, format="JPEG", quality=94, optimize=True)
    puffer.seek(0)
    return ImageReader(puffer)


# --- Die drei Flächen --------------------------------------------------------
def vorderseite(c, x, y, breite, hoehe, cfg, *, ueberstand=0):
    """Titelseite: Titel oben, Untertitel darunter, Motiv, Autor unten.

    Der Titel steht am Kopf statt in der Mitte — im Amazon-Vorschaubild ist
    der Umschlag rund 100 Pixel breit, und dort entscheidet die oberste Zeile,
    ob ein Buch erkannt wird. Das Motiv rückt dafür in die untere Hälfte und
    trägt die Fläche zwischen Untertitel und Autorenzeile.
    """
    rand = breite * 0.10
    textbreite = breite - 2 * rand

    # --- Titelbild, wenn eines hinterliegt ---
    bild = titelbild_suchen()
    if bild:
        # Volle Fläche inklusive Anschnitt nach rechts, oben und unten. Nach
        # links **nicht**: dort liegt der Rücken.
        bild_b = breite + ueberstand
        bild_h = hoehe + 2 * ueberstand
        c.drawImage(titelbild_aufbereiten(bild, bild_h / bild_b),
                    x, y - ueberstand, width=bild_b, height=bild_h,
                    preserveAspectRatio=False, mask=None)

    # --- Titel, von oben gesetzt ---
    titel_groesse, titel_zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", textbreite, maximal=52, minimal=20)
    zeilenhoehe = titel_groesse * 1.13

    cursor = y + hoehe - rand * 1.15 - titel_groesse
    c.setFillColor(FARBEN["text"])
    for zeile in titel_zeilen:
        c.setFont("Sans-Bold", titel_groesse)
        c.drawCentredString(x + breite / 2, cursor, zeile)
        cursor -= zeilenhoehe
    cursor += zeilenhoehe - titel_groesse * 0.30

    # --- Trennstrich ---
    cursor -= 20
    c.setStrokeColor(FARBEN["akzent"])
    c.setLineWidth(1.8)
    c.line(x + breite * 0.34, cursor, x + breite * 0.66, cursor)

    # --- Untertitel, deutlich größer als zuvor ---
    unter_groesse = 20.0
    cursor -= 34
    cursor = block_schreiben(c, cfg["untertitel"], x + rand, cursor,
                             textbreite, "Sans", unter_groesse,
                             unter_groesse * 1.32, FARBEN["text_leise"],
                             zentriert=True)

    # --- Motiv: füllt, was zwischen Untertitel und Autorenzeile bleibt ---
    autor_y = y + hoehe * 0.105
    motiv_oben = cursor - 20
    motiv_unten = autor_y + 28
    if not bild and motiv_oben - motiv_unten > 24:
        fadenmotiv(c, x, motiv_unten,
                       breite + ueberstand, motiv_oben - motiv_unten)

    c.setFillColor(FARBEN["akzent"])
    c.setFont("Sans-Bold", 18)
    c.drawCentredString(x + breite / 2, autor_y, cfg["autor"])


def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    if not mit_text:
        return
    groesse = min(11, breite * 0.55)
    c.saveState()
    c.translate(x + breite / 2, y + hoehe / 2)
    c.rotate(-90)
    c.setFillColor(FARBEN["text"])
    c.setFont("Sans-Bold", groesse)
    c.drawString(-hoehe / 2 + hoehe * 0.08, -groesse * 0.35, cfg["titel"])
    c.setFillColor(FARBEN["text_leise"])
    c.setFont("Sans", groesse * 0.86)
    c.drawRightString(hoehe / 2 - hoehe * 0.08, -groesse * 0.35, cfg["autor"])
    c.restoreState()


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte,
               *, hardcover=False):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    # Das Barcodefeld zuerst — es ist der einzige Bereich, dessen Lage nicht
    # verhandelbar ist. Auf diesem dunklen Grund muss es weiß hinterlegt sein,
    # sonst steht schwarze Strichschrift auf Tintenblau und ist nicht scanbar.
    barcodefeld_freistellen(c, x, y, breite, hardcover=hardcover)

    hinweis_zeilen = umbrechen(c, RECHTSHINWEIS, "Serif", 7, textbreite)
    _, fy, _, fh = weissflaeche(x, y, breite, hardcover=hardcover)
    unterlaenge = 7 * 0.25
    hinweis_y = (fy + fh + BARCODE_LUFT_MM * mm + unterlaenge
                 + (len(hinweis_zeilen) - 1) * 9)

    oben = y + hoehe - rand * 0.85
    platz = oben - (hinweis_y + 16)

    def hoehe_bei(faktor):
        g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
        h = 0.0
        if kopf.get("schlagzeile"):
            h += len(umbrechen(c, kopf["schlagzeile"], "Sans-Bold", g_kopf,
                               textbreite)) * g_kopf * 1.3 + 14
        for a in absaetze:
            h += len(umbrechen(c, a, "Serif", g_text, textbreite)) \
                 * g_text * 1.38 + 8
        h += 4
        for p in punkte:
            h += len(umbrechen(c, p, "Serif", g_punkt, textbreite - 14)) \
                 * g_punkt * 1.35 + 3
        return h

    # Der Text sucht sich seine Größe selbst — nach unten, damit ein langer
    # Klappentext nicht in den Rechtshinweis läuft, nach oben, damit die
    # Rückseite nicht halb leer bleibt.
    faktor = 1.0
    if hoehe_bei(faktor) <= platz:
        while faktor < 1.30 and hoehe_bei(faktor + 0.02) <= platz:
            faktor += 0.02
    else:
        while faktor > 0.72 and hoehe_bei(faktor) > platz:
            faktor -= 0.02
    g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
    if abs(faktor - 1.0) > 1e-9:
        wort = "vergrößert" if faktor > 1 else "verkleinert"
        print(f"  Rückseitentext auf {faktor:.0%} {wort} "
              f"(Fließtext {g_text:.1f} pt)")

    # Was übrig bleibt, wird oben und unten gleich verteilt.
    rest = platz - hoehe_bei(faktor)
    cursor = oben - max(0.0, rest) / 2

    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", g_kopf,
                                 g_kopf * 1.3, FARBEN["akzent"])
        cursor -= 14

    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", g_text, g_text * 1.38,
                                 FARBEN["text"])
        cursor -= 8

    cursor -= 4
    for punkt in punkte:
        c.setFillColor(FARBEN["akzent"])
        c.setFont("Sans-Bold", g_punkt)
        c.drawString(x + rand, cursor, "•")
        c.setFillColor(FARBEN["text"])
        for zeile in umbrechen(c, punkt, "Serif", g_punkt, textbreite - 14):
            c.setFont("Serif", g_punkt)
            c.drawString(x + rand + 14, cursor, zeile)
            cursor -= g_punkt * 1.35
        cursor -= 3

    if cursor < hinweis_y + 12:
        print("  ACHTUNG: Rückseitentext reicht bis an den Rechtshinweis — "
              "Klappentext kürzen.")

    block_schreiben(c, RECHTSHINWEIS, x + rand, hinweis_y, textbreite,
                    "Serif", 7, 9, FARBEN["text_leise"])
