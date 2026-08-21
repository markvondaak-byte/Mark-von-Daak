#!/usr/bin/env python3
"""Rendert das Titelmotiv für die Vorderseite von Band 4.

    python3 dopamin/build/titelbild.py        # Probeansicht nach out/

Warum ein gerendertes Bild und keine Vektorgrafik:

Eine erste Fassung zeichnete den Kopf mit reportlab — Umriss, Gehirn und
Windungen als Striche. Das war sauber und sah nach Piktogramm aus. Ein
Sachbuchumschlag lebt aber von Licht: von einer Kante, die glüht, von einem
Grund, der in die Tiefe geht, von Punkten mit einem Hof. Nichts davon lässt
sich mit Strichen erzeugen, und Verläufe mit Transparenz sind in der
KDP-Druckfassung ohnehin verboten.

Hier wird deshalb ein **Bild** gerechnet und nicht gezeichnet: Alle Effekte
entstehen als Pixel, bevor irgendetwas ins PDF kommt. Was am Ende im Umschlag
liegt, ist eine flache Rasterfläche — genau das, was die Druckvorstufe will.

Die Geometrie bleibt dieselbe wie vorher: Punktfolgen in einem
Einheitsraster, aus denen ein Catmull-Rom-Spline glatte Kurven macht. Ein
Profil lebt von wenigen Stellen — Nasenwurzel, Nasenspitze, Kinn —, und die
kann man als Koordinaten lesen und um zwei Hundertstel verschieben.
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

WURZEL = Path(__file__).resolve().parents[2]

# --- Geometrie ---------------------------------------------------------------
# x von 0 bis 1 über die Breite der Figur, y von 0 (Halsansatz) bis 1
# (Scheitel). Nach rechts gewandt.
#
# Der Mund ist eine flache Mulde und kein Lippenpaar: Vier Punkte mit großem
# Ausschlag auf engem Raum ergaben beim Glätten keine Lippen, sondern eine
# Zickzacklinie. Ecken entstehen über eng gesetzte Nachbarpunkte, nicht über
# doppelt aufgeführte Punkte — die erzeugten Knoten.
KOPF_UMRISS = [
    (0.452, 1.000),                      # Scheitel
    (0.614, 0.970),
    (0.722, 0.896),                      # Stirn
    (0.770, 0.804),                      # Haaransatz
    (0.784, 0.694),                      # Braue
    (0.752, 0.622),                      # Nasenwurzel
    (0.796, 0.556),                      # Nasenrücken
    (0.852, 0.512),
    (0.880, 0.492),                      # Nasenspitze
    (0.844, 0.476),
    (0.796, 0.466),                      # Nasenbasis
    (0.786, 0.428),                      # Mund
    (0.792, 0.392),
    (0.774, 0.356),                      # Kinnfalte
    (0.790, 0.318),                      # Kinn
    (0.748, 0.296),                      # Kinnunterkante
    (0.672, 0.280),                      # Kieferunterkante
    (0.620, 0.236),                      # Kieferwinkel
    (0.610, 0.150),                      # Hals vorn
    (0.616, 0.060),
    (0.620, -0.140),                     # läuft unten aus dem Bild
    (0.258, -0.140),
    (0.276, 0.120),
    (0.302, 0.240),                      # Nacken
    (0.292, 0.352),
    (0.246, 0.452),                      # hinter dem Kiefer
    (0.190, 0.586),
    (0.152, 0.732),                      # Hinterkopf
    (0.176, 0.858),
    (0.286, 0.958),
]

KOPF_HIRN = [
    (0.300, 0.900),
    (0.430, 0.938),
    (0.570, 0.925),
    (0.665, 0.868),
    (0.700, 0.790),
    (0.672, 0.716),
    (0.590, 0.668),
    (0.470, 0.648),
    (0.352, 0.652),
    (0.262, 0.700),
    (0.232, 0.790),
    (0.248, 0.858),
]

KOPF_KLEINHIRN = [
    (0.268, 0.678),
    (0.348, 0.666),
    (0.386, 0.628),
    (0.362, 0.588),
    (0.292, 0.580),
    (0.248, 0.616),
]

# --- Farbwelt ----------------------------------------------------------------
GRUND_OBEN = (27, 26, 58)
GRUND_UNTEN = (12, 11, 30)
BOKEH_TOENE = [(24, 86, 120), (38, 60, 150), (18, 108, 118), (72, 48, 140)]
KOPF_VORN = (54, 52, 104)        # Fleischton der Figur, vorderer Rand
KOPF_HINTEN = (28, 27, 62)       # hinterer Rand — daraus wird das Volumen
RANDLICHT = (176, 194, 255)
HIRN_GRUND = (74, 68, 148)
NETZ = (150, 142, 240)
SYNAPSE = (255, 186, 108)

# Wie viele Knoten das Nervennetz hat und wie eng sie stehen dürfen.
NETZ_KNOTEN = 78
NETZ_ABSTAND = 0.030            # Mindestabstand im Einheitsraster
NETZ_NACHBARN = 3
SYNAPSEN_ANTEIL = 0.17          # welcher Teil der Knoten hell leuchtet

ZUFALL = 20260821               # fester Startwert: gleicher Bau, gleiches Bild


# --- Kurven ------------------------------------------------------------------
def _bezier_aus_punkten(punkte, geschlossen=True, spannung=6.0):
    """Catmull-Rom durch die Punkte, ausgegeben als Bezier-Stützpunkte."""
    n = len(punkte)
    stuecke = []
    grenze = n if geschlossen else n - 1
    for i in range(grenze):
        p_vor = punkte[(i - 1) % n] if geschlossen else punkte[max(i - 1, 0)]
        p0 = punkte[i]
        p1 = punkte[(i + 1) % n]
        p_nach = (punkte[(i + 2) % n] if geschlossen
                  else punkte[min(i + 2, n - 1)])
        c1 = (p0[0] + (p1[0] - p_vor[0]) / spannung,
              p0[1] + (p1[1] - p_vor[1]) / spannung)
        c2 = (p1[0] - (p_nach[0] - p0[0]) / spannung,
              p1[1] - (p_nach[1] - p0[1]) / spannung)
        stuecke.append((p0, c1, c2, p1))
    return stuecke


def polylinie(punkte, geschlossen=True, spannung=6.0, schritte=28):
    """Die geglättete Kurve als Streckenzug — so kann PIL sie füllen."""
    aus = []
    for p0, c1, c2, p1 in _bezier_aus_punkten(punkte, geschlossen, spannung):
        for s in range(schritte):
            t = s / schritte
            u = 1 - t
            aus.append((
                u ** 3 * p0[0] + 3 * u * u * t * c1[0]
                + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                u ** 3 * p0[1] + 3 * u * u * t * c1[1]
                + 3 * u * t * t * c2[1] + t ** 3 * p1[1],
            ))
    return aus


def _im_polygon(punkt, polygon):
    """Punkt-in-Polygon nach dem Strahlverfahren."""
    x, y = punkt
    drin = False
    j = len(polygon) - 1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            drin = not drin
        j = i
    return drin


# --- Bausteine ---------------------------------------------------------------
def _verlaufsbild(groesse, oben, unten):
    """Senkrechter Verlauf, über eine schmale Spalte hochgerechnet."""
    breite, hoehe = groesse
    spalte = Image.new("RGB", (1, hoehe))
    for y in range(hoehe):
        t = y / max(1, hoehe - 1)
        spalte.putpixel((0, y), tuple(
            round(o + (u - o) * t) for o, u in zip(oben, unten)))
    return spalte.resize(groesse, Image.BILINEAR)


def _farbig(maske, farbe):
    """Färbt eine Graustufenmaske ein — Schwarz bleibt schwarz."""
    voll = Image.new("RGB", maske.size, farbe)
    return Image.composite(voll, Image.new("RGB", maske.size, (0, 0, 0)),
                           maske)


def _bokeh(groesse, wuerfel, anzahl=52):
    """Unscharfe Lichtkreise als Tiefe hinter der Figur.

    Kein Zierrat: Ohne sie ist der Grund eine leere Fläche, und die Figur
    steht darauf wie ein Aufkleber. Die Kreise geben ihr einen Raum, in dem
    sie stehen kann.
    """
    breite, hoehe = groesse
    ebene = Image.new("RGB", groesse, (0, 0, 0))
    zeichner = ImageDraw.Draw(ebene)
    for _ in range(anzahl):
        r = wuerfel.randint(int(breite * 0.025), int(breite * 0.095))
        cx = wuerfel.randint(-r, breite + r)
        cy = wuerfel.randint(-r, hoehe + r)
        ton = wuerfel.choice(BOKEH_TOENE)
        staerke = wuerfel.uniform(0.25, 0.85)
        zeichner.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=tuple(round(k * staerke) for k in ton))
    return ebene.filter(ImageFilter.GaussianBlur(breite * 0.016))


def _maske(groesse, streckenzug, rahmen):
    """Füllt einen Streckenzug des Einheitsrasters als Maske."""
    x, y, b, h = rahmen
    maske = Image.new("L", groesse, 0)
    ImageDraw.Draw(maske).polygon(
        [(x + px * b, y + (1 - py) * h) for px, py in streckenzug], fill=255)
    return maske


def _randlicht(groesse, streckenzug, rahmen, staerke_px):
    """Die glühende Kante der Figur: scharfer Kern plus weiter Hof.

    Zwei Ebenen, weil eine nicht reicht — nur mit Hof wird die Kante matschig,
    nur mit Kern bleibt sie eine Strichzeichnung.
    """
    x, y, b, h = rahmen
    punkte = [(x + px * b, y + (1 - py) * h) for px, py in streckenzug]
    punkte.append(punkte[0])

    kern = Image.new("L", groesse, 0)
    ImageDraw.Draw(kern).line(punkte, fill=255,
                              width=max(2, round(staerke_px)), joint="curve")
    kern = kern.filter(ImageFilter.GaussianBlur(staerke_px * 0.55))

    hof = Image.new("L", groesse, 0)
    ImageDraw.Draw(hof).line(punkte, fill=190,
                             width=max(2, round(staerke_px * 1.6)),
                             joint="curve")
    hof = hof.filter(ImageFilter.GaussianBlur(staerke_px * 5.5))

    return kern, hof


def _nervennetz(wuerfel, hirn_polygon, klein_polygon):
    """Knoten und Kanten des Netzes, im Einheitsraster.

    Die Knoten werden verworfen und neu gezogen, bis sie weit genug
    auseinanderliegen — ein reines Zufallsmuster ballt sich an einigen
    Stellen und lässt anderswo Löcher, und beides sieht man dem fertigen
    Bild an.
    """
    knoten = []
    versuche = 0
    while len(knoten) < NETZ_KNOTEN and versuche < NETZ_KNOTEN * 400:
        versuche += 1
        p = (wuerfel.uniform(0.20, 0.72), wuerfel.uniform(0.55, 0.95))
        if not (_im_polygon(p, hirn_polygon) or _im_polygon(p, klein_polygon)):
            continue
        if any(math.dist(p, q) < NETZ_ABSTAND for q in knoten):
            continue
        knoten.append(p)

    kanten = set()
    for i, p in enumerate(knoten):
        nah = sorted(range(len(knoten)),
                     key=lambda j: math.dist(p, knoten[j]))[1:NETZ_NACHBARN + 1]
        for j in nah:
            if math.dist(p, knoten[j]) < NETZ_ABSTAND * 3.2:
                kanten.add((min(i, j), max(i, j)))
    return knoten, sorted(kanten)


def _vignette(groesse):
    """Randabdunklung — hält den Blick in der Mitte."""
    breite, hoehe = groesse
    klein = (max(8, breite // 24), max(8, hoehe // 24))
    maske = Image.new("L", klein, 0)
    zeichner = ImageDraw.Draw(maske)
    stufen = 28
    for i in range(stufen):
        t = i / stufen
        rand_x = klein[0] * 0.5 * (1 - t) * 0.9
        rand_y = klein[1] * 0.5 * (1 - t) * 0.9
        zeichner.ellipse([rand_x, rand_y, klein[0] - rand_x, klein[1] - rand_y],
                         fill=round(255 * (1 - t) ** 1.4))
    return maske.resize(groesse, Image.BILINEAR)


# --- Zusammenbau -------------------------------------------------------------
def rendern(breite_px, hoehe_px, ueberabtastung=2):
    """Rechnet das Titelmotiv und gibt es als RGB-Bild zurück.

    Gerendert wird in doppelter Auflösung und danach verkleinert. Ohne das
    sind die Kanten der Figur getreppt — PIL zeichnet Polygone ohne
    Kantenglättung, und bei einer Profillinie fällt das sofort auf.
    """
    s = ueberabtastung
    groesse = (breite_px * s, hoehe_px * s)
    breite, hoehe = groesse
    wuerfel = random.Random(ZUFALL)

    # 1 — Grund mit Tiefe
    bild = _verlaufsbild(groesse, GRUND_OBEN, GRUND_UNTEN)
    bild = ImageChops.add(bild, _bokeh(groesse, wuerfel))

    # 2 — Rahmen der Figur. Sie steht mittig, hat oben Luft und läuft unten
    #     aus dem Bild. Die Höhe ist so gewählt, dass der Hals die Unterkante
    #     gerade erreicht: Bei 0,84 der Bildhöhe reicht der Umriss mit seinen
    #     1,14 Rastereinheiten knapp darüber hinaus. Ein erster Ansatz hatte
    #     0,97 und einen negativen Ursprung — da war der Scheitel abgesägt.
    # Die Luft oben ist großzügiger, als sie im Einzelbild aussieht: Auf dem
    # Umschlag liegen die oberen 3,175 mm des Bandes im Anschnitt und werden
    # weggeschnitten. Bei 0,05 Rand stand der Scheitel danach 1,7 mm unter
    # der Papierkante und wirkte angeschnitten.
    figur_h = hoehe * 0.78
    figur_b = figur_h * 0.736          # x-Ausdehnung der Punktfolgen
    rahmen = ((breite - figur_b) / 2 - 0.152 * figur_h,
              hoehe * 0.10, figur_h, figur_h)

    umriss = polylinie(KOPF_UMRISS, spannung=7.5)
    hirn = polylinie(KOPF_HIRN)
    klein = polylinie(KOPF_KLEINHIRN)

    kopf_maske = _maske(groesse, umriss, rahmen)

    # 3 — Volumen: waagerechter Verlauf von hinten nach vorn, durch die
    #     Kopfmaske gelegt. Ein flacher Ton machte aus der Figur eine
    #     Schablone; erst der Verlauf gibt ihr eine Vorder- und Rückseite.
    # rotate(90) dreht gegen den Uhrzeigersinn: Der obere Rand des Verlaufs
    # landet links. Deshalb steht hier HINTEN vor VORN — sonst wäre der
    # Hinterkopf beleuchtet und das Gesicht läge im Schatten.
    volumen = _verlaufsbild((hoehe, breite), KOPF_HINTEN, KOPF_VORN)
    volumen = volumen.rotate(90, expand=True).resize(groesse, Image.BILINEAR)
    bild = Image.composite(volumen, bild,
                           kopf_maske.filter(ImageFilter.GaussianBlur(s * 0.8)))

    # 4 — Gehirn, weich eingeblendet
    hirn_maske = _maske(groesse, hirn, rahmen)
    klein_maske = _maske(groesse, klein, rahmen)
    hirn_gesamt = ImageChops.lighter(hirn_maske, klein_maske)
    weich = hirn_gesamt.filter(ImageFilter.GaussianBlur(figur_b * 0.012))
    bild = Image.composite(
        Image.new("RGB", groesse, HIRN_GRUND), bild,
        weich.point(lambda v: round(v * 0.80)))

    # 5 — Nervennetz
    knoten, kanten = _nervennetz(wuerfel, hirn, klein)
    x, y, b, h = rahmen

    def ab(p):
        return (x + p[0] * b, y + (1 - p[1]) * h)

    netz = Image.new("L", groesse, 0)
    zeichner = ImageDraw.Draw(netz)
    for i, j in kanten:
        zeichner.line([ab(knoten[i]), ab(knoten[j])], fill=120,
                      width=max(1, round(figur_b * 0.0022)))
    for p in knoten:
        px, py = ab(p)
        r = figur_b * 0.0045
        zeichner.ellipse([px - r, py - r, px + r, py + r], fill=200)

    bild = ImageChops.add(bild, _farbig(netz, NETZ))
    bild = ImageChops.add(bild, _farbig(
        netz.filter(ImageFilter.GaussianBlur(figur_b * 0.010)).point(
            lambda v: round(v * 0.55)), NETZ))

    # 6 — Synapsen: heller Kern, weiter Hof. Der Hof ist der Grund, warum
    #     das Bild leuchtet und nicht nur bunte Punkte trägt.
    hell = wuerfel.sample(knoten, round(len(knoten) * SYNAPSEN_ANTEIL))
    kerne = Image.new("L", groesse, 0)
    hoefe = Image.new("L", groesse, 0)
    k_zeichner, h_zeichner = ImageDraw.Draw(kerne), ImageDraw.Draw(hoefe)
    for p in hell:
        px, py = ab(p)
        r = figur_b * wuerfel.uniform(0.0060, 0.0105)
        k_zeichner.ellipse([px - r, py - r, px + r, py + r], fill=255)
        # Der Hof war zuerst fünfmal so groß wie der Kern und mit 150
        # gefüllt. Daraus wurden orange Flecken, die das Netz überdeckten —
        # ein Hof soll den Punkt tragen, nicht ihn ersetzen.
        hr = r * 3.2
        h_zeichner.ellipse([px - hr, py - hr, px + hr, py + hr], fill=105)
    hoefe = hoefe.filter(ImageFilter.GaussianBlur(figur_b * 0.011))
    kerne_weich = kerne.filter(ImageFilter.GaussianBlur(figur_b * 0.0025))

    bild = ImageChops.add(bild, _farbig(hoefe, SYNAPSE))
    bild = ImageChops.add(bild, _farbig(kerne_weich, SYNAPSE))
    bild = ImageChops.add(bild, _farbig(
        kerne.filter(ImageFilter.GaussianBlur(s * 0.6)), (255, 240, 220)))

    # 7 — Randlicht der Profillinie, zuletzt und über allem
    kern, hof = _randlicht(groesse, umriss, rahmen, figur_b * 0.0075)
    bild = ImageChops.add(bild, _farbig(hof, (60, 74, 150)))
    bild = ImageChops.add(bild, _farbig(kern, RANDLICHT))

    # 8 — Vignette und feines Korn. Das Korn ist kein Effekt, sondern gegen
    #     Streifenbildung: Ein glatter Verlauf über 30 cm zeigt im Druck
    #     sonst Stufen, und ein Prozent Rauschen bricht sie auf.
    bild = Image.composite(bild, Image.new("RGB", groesse, (0, 0, 0)),
                           _vignette(groesse).point(
                               lambda v: 150 + round(v * 105 / 255)))
    korn = Image.effect_noise(groesse, 5).convert("L")
    bild = ImageChops.add(ImageChops.subtract(bild, _farbig(korn, (3, 3, 3))),
                          _farbig(korn.point(lambda v: 255 - v), (3, 3, 4)))

    return bild.resize((breite_px, hoehe_px), Image.LANCZOS)


def main():
    ziel = WURZEL / "dopamin" / "out" / "titelbild-probe.png"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild = rendern(1538, 1166)
    bild.save(ziel)
    print(f"{bild.width} x {bild.height} px")
    print(f"  → {ziel.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
