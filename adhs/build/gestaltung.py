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

import random
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

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
RASTER_SAAT = 20260824
RASTER_SPALTEN = 26
RASTER_ZEILEN = 7

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


def ordnungsraster(c, x, y, breite, hoehe):
    """Striche, die links wild stehen und sich nach rechts ausrichten.

    Je weiter rechts eine Spalte liegt, desto kleiner sind Streuung und
    Drehung und desto mehr nähert sich die Farbe dem Akzent. Ganz rechts
    stehen die Striche im Raster — sichtbar geordnet, ohne steril zu wirken.
    """
    zufall = random.Random(RASTER_SAAT)
    spalte_b = breite / RASTER_SPALTEN
    zeile_h = hoehe / RASTER_ZEILEN
    strich = spalte_b * 0.62
    chaos_f, ordnung_f = FARBEN["raster_chaos"], FARBEN["raster_ordnung"]

    c.setLineCap(1)
    for sp in range(RASTER_SPALTEN):
        # 0 ganz links (Chaos) bis 1 ganz rechts (Ordnung), leicht beschleunigt
        # damit die Auflösung nicht schon in der Mitte fertig ist.
        t = (sp / (RASTER_SPALTEN - 1)) ** 1.6
        unruhe = 1.0 - t
        for ze in range(RASTER_ZEILEN):
            mx = x + (sp + 0.5) * spalte_b
            my = y + (ze + 0.5) * zeile_h
            mx += zufall.uniform(-1, 1) * spalte_b * 0.55 * unruhe
            my += zufall.uniform(-1, 1) * zeile_h * 0.55 * unruhe
            winkel = zufall.uniform(-90, 90) * unruhe

            c.setStrokeColorRGB(
                chaos_f.red + (ordnung_f.red - chaos_f.red) * t,
                chaos_f.green + (ordnung_f.green - chaos_f.green) * t,
                chaos_f.blue + (ordnung_f.blue - chaos_f.blue) * t,
            )
            c.setLineWidth(1.1 + 1.5 * t)
            c.saveState()
            c.translate(mx, my)
            c.rotate(winkel)
            c.line(-strich / 2, 0, strich / 2, 0)
            c.restoreState()
    c.setLineCap(0)


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
    motiv_oben = cursor - 26
    motiv_unten = autor_y + 34
    if motiv_oben - motiv_unten > 24:
        ordnungsraster(c, x, motiv_unten,
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
