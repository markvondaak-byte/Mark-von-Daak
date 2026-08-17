#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für „Was uns die Maschine abnimmt“.

    python3 ki/build/build_ki.py       # zuerst — liefert die Seitenzahl
    python3 ki/build/build_cover.py

Ergebnis: ki/out/cover.pdf (Vektorfassung) und ki/out/cover-vorschau.png.
Zu KDP hochgeladen wird nicht diese Datei, sondern die flache Fassung:

    python3 buch/build/cover_flach.py ki/out/cover.pdf

Warum ein eigenes Skript und nicht buch/build/build_cover.py: Das dortige
Motiv ist eine Auslage aus Obst und Gemüse — richtig für ein Ernährungsbuch
und sinnlos für dieses. Die Geometrie (Anschnitt, Rückenbreite, Sollmaße) ist
dieselbe und wird von dort importiert, damit sie nur an einer Stelle gepflegt
wird. Neu ist allein, was gezeichnet wird.

Das Motiv ist ein Netz aus Knoten und Kanten, das über Rückseite, Rücken und
Vorderseite durchläuft. Es wird aus einem festen Zufallskeim erzeugt: Der
Umschlag sieht bei jedem Lauf gleich aus, sonst ließe sich eine Korrektur am
Text nicht von einer Änderung am Bild unterscheiden.
"""

import math
import random
import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (  # noqa: E402
    BARCODE_B_MM, BARCODE_H_MM, BESCHNITT_MM, RUECKENTEXT_AB_SEITEN,
    RUECKEN_PRO_SEITE_MM, block_schreiben, groesse_einpassen,
    klappentext_laden, schriften_laden, seitenzahl, umbrechen, vorschau,
)

KI = WURZEL / "ki"

# --- Farbwelt ----------------------------------------------------------------
# Dieselbe Leitfarbe wie der Innenteil (siehe build_ki.py), nur als
# Umschlagpalette ausgebaut. Der Grund ist bewusst dunkel: Der Titel steht im
# freien Feld darunter, und heller Text auf dunklem Grund hält im
# Amazon-Vorschaubild mehr Kontrast als umgekehrt.
PALETTE = {
    "grund_oben": HexColor("#16232F"),
    "grund_unten": HexColor("#101A24"),
    "titel": HexColor("#FFFFFF"),
    "untertitel": HexColor("#AFC2D2"),
    "leise": HexColor("#8FA3B5"),
    "akzent": HexColor("#4A9BD4"),
    "akzent_tief": HexColor("#2E6E9E"),
    "kante": HexColor("#2A4459"),
}

NETZ_HOEHE = 0.30       # Anteil der Umschlaghöhe, den das Motiv einnimmt
#   0,30 wie das Illustrationsband der Stoffwechsel-Reihe. Wer den Wert
#   erhöht, nimmt ihn dem Klappentext weg: Die Rückseite verkleinert dann
#   ihre Schrift, bis der Text unter 8 pt fällt und niemand ihn mehr liest.
NETZ_KEIM = 20260816    # fester Keim: gleicher Umschlag bei jedem Lauf


# --- Grund -------------------------------------------------------------------
def grund(c, breite, hoehe, streifen=140):
    """Vertikaler Verlauf, gezeichnet als Streifen statt als Shading-Objekt.

    reportlab würde für einen echten Verlauf ein Shading anlegen — genau das,
    was cover_flach.py später als Beanstandung meldet. Bei 140 Streifen ist
    der Übergang im Druck nicht als Stufe erkennbar.
    """
    o, u = PALETTE["grund_oben"], PALETTE["grund_unten"]
    for i in range(streifen):
        anteil = i / (streifen - 1)
        c.setFillColorRGB(
            u.red + (o.red - u.red) * anteil,
            u.green + (o.green - u.green) * anteil,
            u.blue + (o.blue - u.blue) * anteil,
        )
        c.rect(0, hoehe * i / streifen, breite,
               hoehe / streifen + 1, stroke=0, fill=1)


# --- Motiv -------------------------------------------------------------------
# Ein Knoten je so viel Fläche in Punkt². Der Wert ist an der Umschlagbreite
# eines 6-x-9-Bandes ausgemessen und bewusst als Dichte formuliert, nicht als
# feste Knotenzahl: Das Kindle-Titelbild ist halb so breit, und mit einer
# festen Zahl hätte es entweder ein Gewimmel oder — wie im ersten Versuch —
# einzelne Punkte ohne Verbindungen gezeigt.
FLAECHE_JE_KNOTEN = 950.0
NACHBARSCHAFT = 1.8      # Reichweite einer Kante, in mittleren Knotenabständen


def netz(c, x, y, breite, hoehe):
    """Ein Netz aus Knoten und Kanten über die volle Umschlagbreite.

    Die Knotendichte nimmt nach oben zu und nach unten ab, damit das Motiv
    unten ausläuft statt an einer Kante abzubrechen. Verbunden wird nur, was
    nahe beieinander liegt — sonst entsteht ein Wollknäuel statt einer
    Struktur.
    """
    knoten = max(24, round(breite * hoehe / FLAECHE_JE_KNOTEN))
    nachbarschaft = NACHBARSCHAFT * math.sqrt(breite * hoehe / knoten)

    zufall = random.Random(NETZ_KEIM)
    punkte = []
    for _ in range(knoten):
        px = zufall.uniform(x, x + breite)
        # Wurzel der Zufallszahl schiebt die Punkte nach oben.
        py = y + hoehe * (1 - math.sqrt(zufall.random()))
        punkte.append((px, py, zufall.random()))

    # Kanten zuerst, damit die Knoten darauf liegen.
    c.setLineCap(1)
    for i, (x1, y1, _) in enumerate(punkte):
        for x2, y2, _ in punkte[i + 1:]:
            abstand = math.hypot(x2 - x1, y2 - y1)
            if abstand > nachbarschaft:
                continue
            # Je kürzer die Kante, desto kräftiger — das gibt dem Netz Tiefe.
            staerke = 1 - abstand / nachbarschaft
            c.setStrokeColor(PALETTE["kante"], alpha=0.30 + 0.55 * staerke)
            c.setLineWidth(0.25 * mm * (0.4 + 0.9 * staerke))
            c.line(x1, y1, x2, y2)

    for px, py, gewicht in punkte:
        hoch = (py - y) / hoehe
        c.setFillColor(PALETTE["akzent"] if gewicht > 0.82
                       else PALETTE["akzent_tief"],
                       alpha=0.35 + 0.6 * hoch)
        radius = (0.5 + 1.5 * gewicht) * mm * (0.5 + 0.7 * hoch)
        c.circle(px, py, radius, stroke=0, fill=1)


# --- Bausteine ---------------------------------------------------------------
def linie(c, x, y, breite, farbe=None, staerke=0.6):
    c.setStrokeColor(farbe or PALETTE["akzent"])
    c.setLineWidth(staerke * mm)
    c.line(x, y, x + breite, y)


# --- Vorderseite -------------------------------------------------------------
# Abstände im Titelblock, von oben nach unten. Als Konstanten und nicht als
# Zahlen im Satzcode, weil der Block als Ganzes ausgemessen und dann zentriert
# wird — wer einen Wert ändert, verschiebt nicht den Blocksatz, sondern nur
# den Abstand.
# Der Abstand des Trennstrichs wird über die **Versalhöhe** gemessen, nicht
# über die Grundlinie: Der Strich steht unter Großbuchstaben, und deren Höhe
# ist die Schriftgröße. Aus demselben Grund zählt die Versalhöhe der obersten
# Titelzeile in die Blockhöhe hinein — sie ist die Oberkante des Blocks.
ABSTAND_UEBER_VERSALHOEHE = 20.0
ABSTAND_TITEL_STRICH = 26.0
ABSTAND_UNTERTITEL_AUTOR = 34.0
UNTERTITEL_GROESSE = 14.0
UNTERTITEL_ZEILE = 19.0
AUTOR_UNTER_GRUNDLINIE = 4.0     # Unterlänge der Autorenzeile


def vorderseite(c, x, y, breite, hoehe, cfg, *, motiv_unterkante):
    """Titelseite: Titel, Trennstrich, Untertitel, Autor.

    Der Block wird zuerst ausgemessen und dann **in der Höhe zentriert** — und
    zwar nicht auf der Seite, sondern im freien Feld unter dem Netzmotiv. Auf
    die Seitenmitte bezogen säße er halb im Motiv; an festen Bruchteilen der
    Seitenhöhe aufgehängt (so war es vorher) sitzt er zu tief, und über dem
    Titel bleibt ein leeres Drittel stehen.

    `motiv_unterkante` ist die Unterkante des Netzes in denselben Koordinaten
    wie `y`. Sie wird übergeben und nicht hier ausgerechnet: Beim gedruckten
    Umschlag ist das Netz auf die Gesamthöhe samt Anschnitt bezogen, beim
    Kindle-Titelbild auf eine Leinwand mit anderem Seitenverhältnis. Aus der
    Seitenhöhe allein ließe sie sich nicht bestimmen.
    """
    rand = breite * 0.11
    textbreite = breite - 2 * rand
    mitte = x + breite / 2

    untertitel = umbrechen(c, cfg["untertitel"], "Sans", UNTERTITEL_GROESSE,
                           textbreite)
    # 34 pt ist die Obergrenze: Darüber wird ein dreizeiliger Titel höher als
    # das freie Feld unter dem Motiv.
    groesse, zeilen = groesse_einpassen(
        c, cfg["titel"], "Sans-Bold", textbreite, maximal=34, minimal=20)
    zeilenhoehe = groesse * 1.16

    strich_ueber_untertitel = UNTERTITEL_GROESSE + ABSTAND_UEBER_VERSALHOEHE

    # Höhe des Blocks von der Versalhöhe der obersten Titelzeile bis zur
    # Unterlänge des Autors.
    blockhoehe = (
        groesse + (len(zeilen) - 1) * zeilenhoehe
        + ABSTAND_TITEL_STRICH
        + strich_ueber_untertitel + (len(untertitel) - 1) * UNTERTITEL_ZEILE
        + ABSTAND_UNTERTITEL_AUTOR
        + AUTOR_UNTER_GRUNDLINIE
    )

    # Im freien Feld zwischen Motivunterkante und Seitenfuß zentrieren.
    feld_mitte = (motiv_unterkante + y) / 2
    autor_y = feld_mitte - blockhoehe / 2 + AUTOR_UNTER_GRUNDLINIE

    c.setFillColor(PALETTE["titel"])
    c.setFont("Sans-Bold", 17)
    c.drawCentredString(mitte, autor_y, cfg["autor"])

    cursor = autor_y + ABSTAND_UNTERTITEL_AUTOR \
        + (len(untertitel) - 1) * UNTERTITEL_ZEILE
    oberste_untertitelzeile = cursor
    c.setFillColor(PALETTE["untertitel"])
    for zeile in untertitel:
        c.setFont("Sans", UNTERTITEL_GROESSE)
        c.drawCentredString(mitte, cursor, zeile)
        cursor -= UNTERTITEL_ZEILE

    strich_y = oberste_untertitelzeile + strich_ueber_untertitel
    linie(c, mitte - textbreite * 0.16, strich_y, textbreite * 0.32)

    cursor = strich_y + ABSTAND_TITEL_STRICH + (len(zeilen) - 1) * zeilenhoehe
    oberste_titelzeile = cursor
    c.setFillColor(PALETTE["titel"])
    for zeile in zeilen:
        c.setFont("Sans-Bold", groesse)
        c.drawCentredString(mitte, cursor, zeile)
        cursor -= zeilenhoehe

    # Läuft der Titel ins Motiv, ist er nicht mehr freigestellt. Bei zentriertem
    # Block kann das nur passieren, wenn der Block höher ist als das freie Feld —
    # dann muss der Titel kürzer oder NETZ_HOEHE kleiner werden.
    if oberste_titelzeile + groesse > motiv_unterkante:
        print("  ACHTUNG: Titelblock reicht ins Netzmotiv hinein.")


# --- Rücken ------------------------------------------------------------------
def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    """Rückentext, von unten nach oben gelesen — die Konvention im Buchhandel.

    KDP verlangt beidseitig 1,6 mm Abstand zur Falz. Die Schriftgröße folgt
    deshalb der Rückenbreite: Was übrig bleibt, mal 2,4 — und nie über 10 pt,
    damit der Rücken bei einem dickeren Band nicht plump wirkt.
    """
    if not mit_text:
        return
    nutzbar_mm = breite / mm - 2 * 1.6
    groesse = max(6.0, min(10.0, nutzbar_mm * 2.4))

    c.saveState()
    c.translate(x + breite / 2, y + hoehe / 2)
    c.rotate(90)

    c.setFillColor(PALETTE["titel"])
    c.setFont("Sans-Bold", groesse)
    c.drawCentredString(0, -groesse * 0.35, cfg["titel"])

    c.setFillColor(PALETTE["leise"])
    c.setFont("Sans", groesse * 0.85)
    c.drawRightString(hoehe / 2 - 16 * mm, -groesse * 0.35, cfg["autor"])
    c.restoreState()


# --- Rückseite ---------------------------------------------------------------
# Grundgrößen für Schlagzeile, Fließtext und Aufzählung. Der Text sucht sich
# davon ausgehend selbst die Größe, die in den freien Raum passt.
RUECKEN_GROESSEN = (16.0, 10.5, 10.0)


def _rueckseite_hoehe(c, kopf, absaetze, punkte, textbreite, faktor):
    """Höhe, die der Rückseitentext bei diesem Verkleinerungsfaktor braucht.

    Wird vor dem Zeichnen ausgerechnet: Unten steht das freizuhaltende
    Barcodefeld, und ein Klappentext, der hineinläuft, fällt am Bildschirm
    kaum auf und im Druck teuer.
    """
    g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
    hoehe = len(umbrechen(c, kopf["schlagzeile"], "Sans-Bold", g_kopf,
                          textbreite)) * g_kopf * 1.28 + 22 \
        if kopf.get("schlagzeile") else 0.0
    for absatz in absaetze:
        hoehe += len(umbrechen(c, absatz, "Serif", g_text,
                               textbreite)) * g_text * 1.36 + 7
    hoehe += 4
    for punkt in punkte:
        hoehe += len(umbrechen(c, punkt, "Serif", g_punkt,
                               textbreite - 16)) * g_punkt * 1.33 + 4
    return hoehe


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte):
    rand = breite * 0.115
    textbreite = breite - 2 * rand
    links = x + rand

    # Text beginnt unter dem Netz und endet über dem Barcodefeld.
    oben = y + hoehe - hoehe * NETZ_HOEHE * 1.02 - rand * 0.5
    feld_b, feld_h = BARCODE_B_MM * mm, BARCODE_H_MM * mm
    feld_y = y + hoehe * 0.035
    unten = feld_y + feld_h + 14
    platz = oben - unten

    def passt(faktor):
        return _rueckseite_hoehe(c, kopf, absaetze, punkte, textbreite,
                                 faktor) <= platz

    faktor = 1.0
    if passt(faktor):
        while faktor < 1.25 and passt(faktor + 0.02):
            faktor += 0.02
    else:
        while faktor > 0.70 and not passt(faktor):
            faktor -= 0.02
    g_kopf, g_text, g_punkt = (g * faktor for g in RUECKEN_GROESSEN)
    if abs(faktor - 1.0) > 0.001:
        wort = "vergrößert" if faktor > 1 else "verkleinert"
        print(f"  Rückseitentext auf {faktor:.0%} {wort} "
              f"(Fließtext {g_text:.1f} pt)")

    cursor = oben
    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], links, cursor,
                                 textbreite, "Sans-Bold", g_kopf,
                                 g_kopf * 1.28, PALETTE["titel"])
        cursor -= 8
        linie(c, links, cursor, textbreite * 0.22, staerke=0.5)
        cursor -= 14

    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, links, cursor, textbreite,
                                 "Serif", g_text, g_text * 1.36,
                                 PALETTE["untertitel"])
        cursor -= 7

    cursor -= 4
    for punkt in punkte:
        c.setFillColor(PALETTE["akzent"])
        c.circle(links + 1.3 * mm, cursor + g_punkt * 0.32, 1.0 * mm,
                 stroke=0, fill=1)
        cursor = block_schreiben(c, punkt, links + 16, cursor,
                                 textbreite - 16, "Serif", g_punkt,
                                 g_punkt * 1.33, PALETTE["leise"])
        cursor -= 4

    if cursor < unten:
        print("  ACHTUNG: Rückseitentext reicht ins Barcodefeld — "
              "Klappentext kürzen.")

    # Barcodefeld freihalten: KDP legt dort selbst den Code hinein, und zwar
    # auf weißem Grund. Wird das Feld nicht weiß angelegt, druckt der Code auf
    # den dunklen Grund und ist nicht scannbar.
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(x + breite - rand - feld_b, feld_y, feld_b, feld_h,
           stroke=0, fill=1)

    c.setFillColor(PALETTE["leise"])
    c.setFont("Sans-Bold", 8.5)
    c.drawString(links, feld_y + feld_h - 10, cfg["autor"])
    c.setFont("Sans", 7.5)
    c.drawString(links, feld_y + feld_h - 22, f"Sachbuch · {cfg['jahr']}")


# --- Zusammenbau -------------------------------------------------------------
def cover_bauen(cfg, seiten, klappentext_pfad, ziel):
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    anschnitt = BESCHNITT_MM * mm
    ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")

    grund(c, gesamt_b, gesamt_h)
    netz(c, 0, gesamt_h * (1 - NETZ_HOEHE), gesamt_b, gesamt_h * NETZ_HOEHE)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    mit_ruecken_text = seiten >= RUECKENTEXT_AB_SEITEN

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_ruecken_text)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg,
                motiv_unterkante=gesamt_h * (1 - NETZ_HOEHE))

    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm,
            "ruecken_text": mit_ruecken_text}


# --- Titelbild für die Kindle-Ausgabe ----------------------------------------
# Amazon verlangt ein einzelnes Bild der Vorderseite — kein aufgeklapptes PDF —
# und empfiehlt 1600 x 2560 Pixel, also das Verhältnis 1,6. Der gedruckte Band
# hat 1,5 (6 x 9 Zoll). Ausgeschnitten würde man deshalb oben Motiv wegnehmen;
# stattdessen wird die Vorderseite auf die andere Leinwand neu gesetzt.
KINDLE_PX = (1600, 2560)
KINDLE_QUALITAET = 92


def kindle_titelbild(cfg, ziel):
    """Zeichnet die Vorderseite auf eine Leinwand im Verhältnis 1,6."""
    import io

    import pymupdf
    from PIL import Image

    schriften_laden()

    # Echte Buchbreite in Punkt, Höhe aus dem geforderten Verhältnis. Die
    # Schriftgrößen in diesem Modul sind absolute Punktwerte — auf einer
    # beliebig großen Leinwand blieben Kennung, Untertitel und Autorenzeile
    # winzig, während nur der Titel mitwüchse.
    breite_pt = cfg["seitenformat"]["breite_mm"] * mm
    hoehe_pt = breite_pt * (KINDLE_PX[1] / KINDLE_PX[0])

    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(breite_pt, hoehe_pt),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Kindle")
    grund(c, breite_pt, hoehe_pt)
    netz(c, 0, hoehe_pt * (1 - NETZ_HOEHE), breite_pt, hoehe_pt * NETZ_HOEHE)
    vorderseite(c, 0, 0, breite_pt, hoehe_pt, cfg,
                motiv_unterkante=hoehe_pt * (1 - NETZ_HOEHE))
    c.showPage()
    c.save()

    seite = pymupdf.open(stream=puffer.getvalue(), filetype="pdf")[0]
    pix = seite.get_pixmap(
        matrix=pymupdf.Matrix(KINDLE_PX[0] / breite_pt,
                              KINDLE_PX[1] / hoehe_pt), alpha=False)
    bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ziel, format="JPEG", quality=KINDLE_QUALITAET, optimize=True)
    return ziel, bild.size


def main():
    cfg = yaml.safe_load((KI / "ki.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(KI / "out" / f"{cfg['slug']}.pdf")
    ziel = KI / "out" / "cover.pdf"
    masse = cover_bauen(cfg, seiten, KI / "cover" / "klappentext.md", ziel)
    png = vorschau(ziel, KI / "out" / "cover-vorschau.png")

    b, h = masse["gesamt_mm"]
    print(f"Innenteil: {seiten} Seiten")
    print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
          f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
    print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
          f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {BESCHNITT_MM} mm Anschnitt")
    print(f"  → {ziel.relative_to(WURZEL)}")
    print(f"  → {png.relative_to(WURZEL)}")

    jpg, (px_b, px_h) = kindle_titelbild(cfg, KI / "out" / "kindle-cover.jpg")
    print(f"Kindle-Titelbild: {px_b} x {px_h} px "
          f"({jpg.stat().st_size / 1024:.0f} KB)")
    print(f"  → {jpg.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
