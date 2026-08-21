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
    BARCODE_B_MM, BARCODE_H_MM, BESCHNITT_MM, BUCHDECKE_MM,
    HARDCOVER_MIN_SEITEN, RUECKENTEXT_AB_SEITEN, RUECKEN_PRO_SEITE_MM,
    WRAP_MM, block_schreiben, groesse_einpassen, klappentext_laden,
    schriften_laden, seitenzahl, titelbild_zeichnen, umbrechen, vorschau,
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
    "akzent_hell": HexColor("#74CBF7"),   # die vordersten Knoten

    "akzent_tief": HexColor("#2E6E9E"),
    "gitter": HexColor("#4E8FC4"),   # Linien und matte Knoten
    "kante": HexColor("#2A4459"),
}

# Das Motiv — gezeichnetes Gitter wie Titelbild — steht auf der
# **Vorderseite**, nicht über den ganzen Umschlag. Anfangs lief das Gitter
# durchgehend über Rückseite, Rücken und Vorderseite; das sah als aufgeklappte
# Fläche gut aus und kostete Platz an der einzigen Stelle, an der er knapp ist:
# Der Klappentext musste sich auf 98 Prozent verkleinern. Auf die Vorderseite
# beschränkt darf das Motiv fast die halbe Seite nehmen, und die Rückseite
# behält ihren vollen Satzspiegel.
MOTIV_HOEHE = 0.46

# Was die Rückseite oben frei lässt: ein ruhiger Kopfsteg.
RUECKEN_KOPFSTEG = 0.10

# Barcodefeld. KDP setzt den Code selbst ein und richtet ihn an der Trimmkante
# der Rückseite aus — nicht am Textrand. Genau das war der Fehler: Das weiße
# Feld hing am Textrand und saß dadurch 17,5 statt 6,35 mm von der Kante
# entfernt; der Code ragte um die Differenz auf den dunklen Grund hinaus und
# war dort nicht scannbar.
BARCODE_KANTE_MM = 6.35     # 0,25 Zoll, KDPs Richtwert zur Trimmkante

# Zwei verschiedene Flächen, die man nicht verwechseln darf:
#
# BARCODE_B_MM x BARCODE_H_MM (50,8 x 30,5 mm, importiert) ist die Fläche, die
# KDP **freigehalten** haben will. Dort darf kein Gestaltungselement liegen.
#
# BARCODE_FELD_* ist das weiße Rechteck, das hier tatsächlich **gezeichnet**
# wird. Es ist kleiner, weil KDPs gedrucktes Symbol kleiner ist als die
# reservierte Fläche: Deckt das weiße Feld die volle Reservefläche ab, steht auf
# einem dunklen Umschlag ringsum sichtbar Weiß über, und das sieht nach Versehen
# aus statt nach Gestaltung.
#
# Das Feld wird in der Reservefläche zentriert — dort sitzt auch das Symbol.
BARCODE_FELD_B_MM = 46.0
BARCODE_FELD_H_MM = 26.0

# --- Grund -------------------------------------------------------------------
def grundton_aus_bild(pfad, anteil=0.10):
    """Mittlere Farbe des unteren Bildrandes.

    Der Umschlaggrund wird darauf gesetzt, wenn ein Titelbild verwendet wird.
    Ohne das steht am Rücken eine sichtbare Kante: Das Bild füllt nur die
    Vorderseite, und schon ein paar Prozent Unterschied im Grundton trennen
    Vorder- und Rückseite quer über den flach ausgelegten Umschlag.

    Gemessen wird der untere Rand, weil dort das Motiv ausgelaufen ist und nur
    noch der Grund steht — der Mittelwert über das ganze Bild wäre von den
    hellen Knoten nach oben gezogen.
    """
    from PIL import Image

    with Image.open(pfad) as bild:
        bild = bild.convert("RGB")
        streifen = bild.crop((0, int(bild.height * (1 - anteil)),
                              bild.width, bild.height))
        # Median statt Mittelwert: Ein einzelner heller Fleck im Randstreifen
        # zieht den Mittelwert spürbar hoch, den Median nicht.
        #
        # tobytes() statt getdata(): getdata() ist seit Pillow 11 als veraltet
        # markiert und fällt mit Pillow 14 weg. tobytes() liefert dasselbe und
        # ist stabil.
        roh = streifen.resize((64, 8)).tobytes()
        anzahl = len(roh) // 3
        kanaele = [sorted(roh[i::3])[anzahl // 2] for i in range(3)]
    return HexColor("#%02X%02X%02X" % tuple(kanaele))


def _helligkeit(farbe):
    """Relative Leuchtdichte nach WCAG — für die Kontrollfrage unten."""
    def kanal(k):
        return k / 12.92 if k <= 0.03928 else ((k + 0.055) / 1.055) ** 2.4
    r, g, b = farbe.rgb()
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def grund(c, breite, hoehe, oben=None, unten=None, streifen=140):
    """Vertikaler Verlauf, gezeichnet als Streifen statt als Shading-Objekt.

    reportlab würde für einen echten Verlauf ein Shading anlegen — genau das,
    was cover_flach.py später als Beanstandung meldet. Bei 140 Streifen ist
    der Übergang im Druck nicht als Stufe erkennbar.
    """
    o = oben or PALETTE["grund_oben"]
    u = unten or PALETTE["grund_unten"]
    for i in range(streifen):
        anteil = i / (streifen - 1)
        c.setFillColorRGB(
            u.red + (o.red - u.red) * anteil,
            u.green + (o.green - u.green) * anteil,
            u.blue + (o.blue - u.blue) * anteil,
        )
        c.rect(0, hoehe * i / streifen, breite,
               hoehe / streifen + 1, stroke=0, fill=1)


# --- Titelbild ---------------------------------------------------------------
def titelbild_suchen():
    """Sucht ein Titelbild in ki/cover/.

    Bewusst **ohne** den Rückgriff auf buch/cover/, den
    buch/build/build_cover.py macht: Dort liegt das Lebensmittelfoto der
    Stoffwechsel-Reihe, und das auf diesem Umschlag zu finden wäre kein
    Fundstück, sondern ein Unfall.
    """
    for endung in (".jpg", ".jpeg", ".png", ".webp"):
        pfad = KI / "cover" / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


def titelbild_sollmasse(cfg, dpi=300):
    """Mindestmaße des Titelbilds in Pixeln.

    Gerechnet, nicht geraten: Das Bild füllt nicht den Umschlag, sondern das
    obere Band der Vorderseite — MOTIV_HOEHE der Gesamthöhe, über die
    Seitenbreite plus Anschnitt oben und außen.
    """
    sf = cfg["seitenformat"]
    breite_mm = sf["breite_mm"] + BESCHNITT_MM
    hoehe_mm = (sf["hoehe_mm"] + 2 * BESCHNITT_MM) * MOTIV_HOEHE
    je_mm = dpi / 25.4
    return round(breite_mm * je_mm), round(hoehe_mm * je_mm)


def titelbild_melden(cfg, pfad):
    """Sagt beim Bauen, welches Motiv verwendet wird — und was daraus folgt."""
    soll_b, soll_h = titelbild_sollmasse(cfg)
    if not pfad:
        print(f"Motiv: gezeichnetes Netz. Für ein Bild stattdessen "
              f"ki/cover/titelbild.jpg ablegen (mindestens {soll_b} x {soll_h} px).")
        print("  KDP-Meldung „KI-erzeugte Bilder\": nein")
        return

    from PIL import Image
    with Image.open(pfad) as bild:
        breite, hoehe = bild.size
    print(f"Motiv: {Path(pfad).relative_to(WURZEL)} "
          f"({breite} x {hoehe} px, nötig {soll_b} x {soll_h})")
    if breite < soll_b or hoehe < soll_h:
        band = soll_b / soll_h
        nutz_b = round(hoehe * band) if breite / hoehe > band else breite
        print(f"  {nutz_b / (soll_b / 300):.0f} dpi statt 300 — wird auf "
              f"{soll_b} px hochgerechnet. Das erfindet keine Schärfe, es "
              "verhindert die KDP-Meldung „Auflösung zu niedrig\".")
    ton = grundton_aus_bild(pfad)
    print(f"  Umschlaggrund übernommen: {ton.hexval()[2:].upper()}")
    if _helligkeit(ton) > 0.18:
        print("  ACHTUNG: Dieser Grund ist zu hell für die weiße Schrift des "
              "Umschlags. Entweder ein dunkleres Motiv wählen oder die "
              "Textfarben in PALETTE nachziehen.")
    print("  Herkunft klären: Ist das Bild KI-erzeugt, ist bei KDP "
          "„KI-erzeugte Bilder\": ja anzugeben — und die Offenlegung in "
          "ki/kapitel/01-impressum.md und 63-hinweise.md zu ergänzen. "
          "Siehe ki/kdp-metadaten.md.")


# --- Motiv -------------------------------------------------------------------
# Ein Knoten je so viel Fläche in Punkt². Als Dichte formuliert und nicht als
# feste Knotenzahl: Das Kindle-Titelbild ist halb so breit wie der aufgeklappte
# Umschlag, und mit einer festen Zahl zeigte es im ersten Versuch einzelne
# Punkte ohne Verbindungen.
#
# Der Wert ist am Aussehen ausgemessen: Bei 520 las sich das Gitter nicht als
# Gewebe, sondern als einzelne große Punkte mit Strichen dazwischen. Diese
# Motive leben von vielen kleinen Knoten und feinen Linien.
FLAECHE_JE_KNOTEN = 120.0

# Jeder Knoten wird mit seinen nächsten Nachbarn verbunden. Nicht „alles
# innerhalb eines Radius": Das ergibt in dichten Bereichen ein Knäuel und in
# dünnen gar nichts. Über die nächsten Nachbarn entsteht ein gleichmäßig
# trianguliertes Gitter.
NACHBARN = 4

# Zwei Ebenen übereinander erzeugen Tiefe: eine ferne, kleinere und dunklere
# hinter einer nahen, kräftigen. Ohne sie wirkt das Gitter wie eine flach
# aufgelegte Folie.
EBENEN = (
    # (Anteil der Knoten, Größe, Deckkraft, Linienstärke)
    (0.58, 0.60, 0.40, 0.70),   # fern
    (0.42, 1.00, 1.00, 1.00),   # nah
)

NETZ_KEIM = 20260816    # fester Keim: gleicher Umschlag bei jedem Lauf


def _knoten_streuen(zufall, anzahl, x, y, breite, hoehe):
    """Punkte mit nach unten abnehmender Dichte.

    Das Quadrat der Zufallszahl schiebt die Punkte nach oben; unten läuft das
    Gitter dadurch aus, statt an einer Kante abzubrechen. Vorher stand hier
    die Wurzel — die ließ das untere Drittel noch deutlich bevölkert, und
    darunter steht der Titel.
    """
    punkte = []
    for _ in range(anzahl):
        px = zufall.uniform(x - breite * 0.02, x + breite * 1.02)
        py = y + hoehe * (1 - zufall.random() ** 2)
        punkte.append((px, py))
    return punkte


def _kanten(punkte, nachbarn=NACHBARN):
    """Kanten zu den nächsten Nachbarn, jede nur einmal.

    Bei den hier anfallenden Knotenzahlen (einige hundert) ist der einfache
    Vergleich aller Paare schnell genug; ein Suchbaum wäre mehr Code als
    Gewinn.
    """
    kanten = set()
    for i, (x1, y1) in enumerate(punkte):
        abstaende = sorted(
            ((math.hypot(x2 - x1, y2 - y1), j)
             for j, (x2, y2) in enumerate(punkte) if j != i),
            key=lambda e: e[0],
        )
        for _, j in abstaende[:nachbarn]:
            kanten.add((min(i, j), max(i, j)))
    return kanten


def netz(c, x, y, breite, hoehe):
    """Ein trianguliertes Gitter aus Knoten und Kanten.

    Oben dicht und hell, nach unten ausdünnend und dunkler, in zwei Ebenen für
    die Tiefe. Die Helligkeit jedes Elements hängt an seiner Höhe im Band —
    dadurch löst sich das Motiv nach unten auf, statt an der Ausblendkante
    abgeschnitten zu wirken.
    """
    gesamt = max(40, round(breite * hoehe / FLAECHE_JE_KNOTEN))
    zufall = random.Random(NETZ_KEIM)

    c.setLineCap(1)
    for anteil, groesse, deckkraft, strichstaerke in EBENEN:
        punkte = _knoten_streuen(zufall, max(12, round(gesamt * anteil)),
                                 x, y, breite, hoehe)

        for i, j in _kanten(punkte):
            x1, y1 = punkte[i]
            x2, y2 = punkte[j]
            # Höhe im Band, 0 unten bis 1 oben.
            hoch = max(0.0, min(1.0, ((y1 + y2) / 2 - y) / hoehe))
            c.setStrokeColor(PALETTE["gitter"],
                             alpha=deckkraft * (0.07 + 0.80 * hoch ** 1.5))
            c.setLineWidth(0.13 * mm * strichstaerke)
            c.line(x1, y1, x2, y2)

        for px, py in punkte:
            hoch = max(0.0, min(1.0, (py - y) / hoehe))
            hell = zufall.random() > 0.62
            c.setFillColor(PALETTE["akzent_hell"] if hell else PALETTE["akzent"],
                           alpha=deckkraft * (0.10 + 0.90 * hoch ** 1.2))
            radius = ((0.16 + 0.50 * zufall.random() ** 2) * mm * groesse
                      * (0.5 + 0.7 * hoch))
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
# Der Titelblock sitzt nicht genau in der Mitte des freien Feldes, sondern um
# diesen Anteil der Feldhöhe darüber. Zwei Gründe: Ein Block, der geometrisch
# mittig steht, wirkt in einem hohen Feld zu tief — das ist der alte Satz vom
# optischen gegenüber dem rechnerischen Mittelpunkt. Und hier kommt hinzu, dass
# das Motiv oben Gewicht hat; der Titel darf ihm entgegenkommen, statt am
# unteren Rand allein zu stehen.
BLOCK_HEBUNG = 0.12

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

    # Im freien Feld zwischen Motivunterkante und Seitenfuß ausrichten — um
    # BLOCK_HEBUNG über dessen Mitte, nicht genau darin.
    feldhoehe = motiv_unterkante - y
    feld_mitte = y + feldhoehe / 2 + feldhoehe * BLOCK_HEBUNG
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
    # dann muss der Titel kürzer oder MOTIV_HOEHE kleiner werden.
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


def barcode_feld(x, y, breite):
    """Lage und Größe des weißen Barcodefelds, in Punkt.

    Eigene Funktion, damit main() dieselbe Rechnung melden kann, die
    rueckseite() zeichnet — zwei getrennte Rechnungen laufen irgendwann
    auseinander, und dann meldet der Build etwas anderes, als im PDF steht.
    """
    # Reservefläche zuerst — sie bestimmt die Lage.
    reserve_x = x + breite - (BARCODE_KANTE_MM + BARCODE_B_MM) * mm
    reserve_y = y + BARCODE_KANTE_MM * mm

    # Das gezeichnete Feld darin zentrieren.
    feld_b, feld_h = BARCODE_FELD_B_MM * mm, BARCODE_FELD_H_MM * mm
    feld_x = reserve_x + ((BARCODE_B_MM * mm) - feld_b) / 2
    feld_y = reserve_y + ((BARCODE_H_MM * mm) - feld_h) / 2
    return feld_x, feld_y, feld_b, feld_h


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte, *,
               kopfsteg):
    """`kopfsteg` ist der oben frei bleibende Anteil der Seitenhöhe.

    Beim gezeichneten Netz ist das dessen Bandhöhe — es läuft über die
    Rückseite mit. Ein Titelbild steht dagegen nur auf der Vorderseite; dann
    genügt ein ruhiger Kopfsteg, und der Klappentext bekommt den Rest.
    """
    rand = breite * 0.115
    textbreite = breite - 2 * rand
    links = x + rand

    # Text beginnt unter dem Kopfsteg und endet über dem Barcodefeld.
    oben = y + hoehe - hoehe * kopfsteg - rand * 0.5
    # Lage und Größe kommen aus barcode_feld(), damit die Meldung beim Bauen
    # und das gezeichnete Rechteck nicht auseinanderlaufen können.
    feld_x, feld_y, feld_b, feld_h = barcode_feld(x, y, breite)
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
    c.rect(feld_x, feld_y, feld_b, feld_h, stroke=0, fill=1)

    c.setFillColor(PALETTE["leise"])
    c.setFont("Sans-Bold", 8.5)
    c.drawString(links, feld_y + feld_h - 10, cfg["autor"])
    c.setFont("Sans", 7.5)
    c.drawString(links, feld_y + feld_h - 22, f"Sachbuch · {cfg['jahr']}")


# --- Zusammenbau -------------------------------------------------------------
def cover_bauen(cfg, seiten, klappentext_pfad, ziel, *, hardcover=False):
    """Baut den Umschlag. `hardcover` schaltet auf KDPs andere Rechnung um.

    Beim Taschenbuch wird der Umschlag beschnitten: 3,175 mm Anschnitt ringsum
    fallen weg. Beim Hardcover wird er nicht beschnitten, sondern um die
    Buchdecke geschlagen — dafür braucht er 18 mm Umschlagrand, und der Rücken
    ist nicht der Buchblock, sondern die Decke: Buchblock plus zwei
    Deckelpappen und Falzrillen, zusammen 9 mm.

    Die Konstanten kommen aus buch/build/build_cover.py und stehen dort in
    Zoll, nicht in Millimetern: KDP rechnet in Zoll, und runde Millimeterwerte
    (18,0 / 9,0) treffen die Sollbreite um 0,03 mm daneben.
    """
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    anschnitt = (WRAP_MM if hardcover else BESCHNITT_MM) * mm
    ruecken_b = (seiten * RUECKEN_PRO_SEITE_MM
                 + (BUCHDECKE_MM if hardcover else 0)) * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")

    titelbild = titelbild_suchen()
    band_h = gesamt_h * MOTIV_HOEHE
    band_y = gesamt_h - band_h

    # Bei einem Titelbild richtet sich der Umschlaggrund nach dem Bild, nicht
    # umgekehrt. Sonst trennt eine Tonkante Vorder- und Rückseite.
    ton = grundton_aus_bild(titelbild) if titelbild else None
    grund(c, gesamt_b, gesamt_h, oben=ton, unten=ton)

    if titelbild:
        # Das Bild füllt das obere Band der **Vorderseite**, samt Anschnitt
        # oben und außen. Rückseite und Rücken bleiben im Grundton — genauso
        # macht es die Stoffwechsel-Reihe, und aus demselben Grund: Ein Motiv,
        # das am Rücken in ein anderes übergeht, hat quer über den flach
        # ausgelegten Umschlag eine Kante. Ein Bild über die volle Breite wäre
        # die Alternative, bräuchte aber ein Seitenverhältnis von 4,5:1.
        titelbild_zeichnen(c, titelbild,
                           anschnitt + trim_b + ruecken_b, band_y,
                           trim_b + anschnitt, band_h,
                           ausblenden=ton)
    else:
        netz(c, anschnitt + trim_b + ruecken_b, band_y,
             trim_b + anschnitt, band_h)

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    # Beim Hardcover ist der Rücken immer breit genug: Die Buchdecke bringt
    # allein 9 mm mit. Die 79-Seiten-Schwelle des Taschenbuchs greift dort
    # nicht.
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte,
               kopfsteg=RUECKEN_KOPFSTEG)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_ruecken_text)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg, motiv_unterkante=band_y)

    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm,
            "ruecken_text": mit_ruecken_text,
            "rand_mm": anschnitt / mm,
            "hardcover": hardcover}


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
    titelbild = titelbild_suchen()
    band_h = hoehe_pt * MOTIV_HOEHE
    ton = grundton_aus_bild(titelbild) if titelbild else None
    grund(c, breite_pt, hoehe_pt, oben=ton, unten=ton)
    if titelbild:
        titelbild_zeichnen(c, titelbild, 0, hoehe_pt - band_h,
                           breite_pt, band_h, ausblenden=ton)
    else:
        netz(c, 0, hoehe_pt - band_h, breite_pt, band_h)
    vorderseite(c, 0, 0, breite_pt, hoehe_pt, cfg,
                motiv_unterkante=hoehe_pt - band_h)
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


def barcode_melden(cfg):
    """Sagt beim Bauen, wo das weiße Barcodefeld sitzt.

    Ohne diese Zeile fällt ein falsch platziertes Feld erst beim Hochladen auf —
    genau so ist der Fehler entdeckt worden, den BARCODE_KANTE_MM behebt.
    Gemeldet wird, was auch gezeichnet wird: beides kommt aus barcode_feld().
    """
    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    anschnitt = BESCHNITT_MM * mm
    feld_x, feld_y, feld_b, feld_h = barcode_feld(anschnitt, anschnitt, trim_b)

    rechts = (anschnitt + trim_b - (feld_x + feld_b)) / mm
    unten = (feld_y - anschnitt) / mm

    print(f"Barcodefeld: {feld_b/mm:.1f} x {feld_h/mm:.1f} mm, "
          f"{rechts:.1f} mm von der rechten und {unten:.1f} mm von der "
          f"unteren Trimmkante")
    # Wie weit das gezeichnete Feld hinter KDPs Reservefläche zurückbleibt.
    schmaler = (BARCODE_B_MM - BARCODE_FELD_B_MM) / 2
    niedriger = (BARCODE_H_MM - BARCODE_FELD_H_MM) / 2
    print(f"  Zentriert in KDPs Reservefläche ({BARCODE_B_MM} x "
          f"{BARCODE_H_MM} mm), auf jeder Seite {schmaler:.1f} mm schmaler "
          f"und {niedriger:.1f} mm niedriger.")
    if schmaler > 0 or niedriger > 0:
        print("  Ist das gedruckte Symbol größer als das Feld, steht an den "
              "Rändern dunkler Grund unter dem Code — in der KDP-Vorschau "
              "gegenprüfen.")


def main():
    cfg = yaml.safe_load((KI / "ki.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(KI / "out" / f"{cfg['slug']}.pdf")
    klappentext = KI / "cover" / "klappentext.md"
    print(f"Innenteil: {seiten} Seiten\n")

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue

        ziel = KI / "out" / f"{name}.pdf"
        masse = cover_bauen(cfg, seiten, klappentext, ziel,
                            hardcover=hardcover)
        png = vorschau(ziel, KI / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        randname = ("Umschlagrand um die Buchdecke" if hardcover
                    else "Anschnitt")
        print(f"{art}")
        print(f"  Rücken: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"  Gesamt: {b:.2f} x {h:.2f} mm = {b/25.4:.3f} x "
              f"{h/25.4:.3f} Zoll, inkl. {masse['rand_mm']:.1f} mm {randname}")
        barcode_melden(cfg)
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}\n")

    titelbild_melden(cfg, titelbild_suchen())
    jpg, (px_b, px_h) = kindle_titelbild(cfg, KI / "out" / "kindle-cover.jpg")
    print(f"Kindle-Titelbild: {px_b} x {px_h} px "
          f"({jpg.stat().st_size / 1024:.0f} KB)")
    print(f"  → {jpg.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
