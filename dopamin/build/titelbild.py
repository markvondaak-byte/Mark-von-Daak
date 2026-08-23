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

# --- Knochen und Weichteile --------------------------------------------------
# Was eine Silhouette zur Röntgenansicht macht, sind wenige Andeutungen:
# Augenhöhle, Kieferlinie, Halswirbelsäule. Gezeichnet werden sie als
# **Linien** und nicht als Flächen, und sie bleiben dunkler als das Gehirn.
# Nase und Zahnreihe stehen als Konstanten bereit, werden aber nicht
# gezeichnet — warum, steht in _knochen().
AUGENHOEHLE = [
    (0.678, 0.624), (0.724, 0.612), (0.736, 0.584),
    (0.714, 0.562), (0.680, 0.568), (0.664, 0.596),
]

NASENHOEHLE = [(0.754, 0.548), (0.774, 0.508), (0.738, 0.514)]

# Nur der Unterkiefer als Linie. Ein zweiter Bogen für den Oberkiefer stand
# im ersten Versuch quer durch die Zahnreihe und machte daraus einen
# Reißverschluss — der Zahnbogen oben ergibt sich aus den Zähnen selbst.
UNTERKIEFER = [
    (0.558, 0.330), (0.578, 0.398), (0.620, 0.418),
    (0.700, 0.414), (0.760, 0.396),
]

# Zahnreihe: von, bis, Grundlinie, Höhe der Krone (negativ = nach unten).
ZAEHNE_OBEN = (0.650, 0.762, 0.462, -0.020)
ZAEHNE_UNTEN = (0.652, 0.756, 0.424, 0.018)
ZAHN_BREITE = 0.024

# Halswirbel, von oben nach unten. Die dritte Zahl ist die halbe Breite.
# Sie sitzen hinten im Hals und sind klein: Im ersten Versuch standen sie
# mittig und doppelt so breit — das las sich als Leiter, nicht als Wirbel.
WIRBEL = [
    (0.350, 0.268, 0.020), (0.354, 0.212, 0.021), (0.358, 0.156, 0.022),
    (0.362, 0.098, 0.023), (0.366, 0.038, 0.024), (0.370, -0.024, 0.025),
    (0.374, -0.088, 0.026),
]
WIRBEL_HOEHE = 0.019            # halbe Höhe eines Wirbels

# --- Farbwelt ----------------------------------------------------------------
# Nach der Vorlage: türkiser Bokeh-Grund, der nach rechts ins Violette
# kippt, ein fast schwarzer Kopf und alles Anatomische in Cyan. Der warme
# Ton bleibt den Synapsen vorbehalten — er ist im ganzen Bild die einzige
# Farbe, die nicht kalt ist, und deshalb sieht man ihn zuerst.
GRUND_LINKS = (16, 96, 116)
GRUND_RECHTS = (62, 46, 108)
GRUND_ABDUNKLUNG = 0.42          # wie stark der untere Rand abgedunkelt wird
BOKEH_TOENE = [(48, 176, 196), (36, 140, 176), (92, 78, 168), (28, 168, 158)]

KOPF_HINTEN = (7, 14, 30)        # der Kopf ist fast schwarz — erst dadurch
KOPF_VORN = (16, 30, 54)         # leuchten die Knochenlinien darin

RANDLICHT = (150, 236, 255)      # Cyan, die Profilkante
KNOCHEN = (118, 206, 242)
HIRN_GRUND = (30, 92, 126)
GYRI = (156, 228, 250)
SYNAPSE = (255, 132, 52)

# Die Gehirnwindungen: Zahl der Bahnen und wie stark sie mäandern. Sie
# liegen als leise Textur unter dem Netz — siehe rendern(), Schritt 5.
GYRI_BAHNEN = 13
GYRI_AUSSCHLAG = 0.030

# Das Nervennetz darüber: Knoten, Mindestabstand und Nachbarn je Knoten.
NETZ_KNOTEN = 74
NETZ_ABSTAND = 0.030
NETZ_NACHBARN = 3

SYNAPSEN = 20                    # Leuchtpunkte im Gehirn

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


def _gyri(groesse, wuerfel, hirn_maske, rahmen, figur_b):
    """Die Gehirnwindungen als mäandernde Bänder, am Gehirn beschnitten.

    Gezeichnet wird über die volle Breite und danach beschnitten — das ist
    erheblich einfacher, als jede Bahn an die Kontur anzupassen, und läuft
    an der Kante sauberer aus.

    Die Bahnen sind dick und stehen eng: Nicht die Linien sind die
    Windungen, sondern die Lücken dazwischen sind die Furchen. Mit dünnen
    Strichen in großem Abstand sah das Gehirn aus wie ein Drahtmodell.
    """
    x, y, b, h = rahmen
    ebene = Image.new("L", groesse, 0)
    zeichner = ImageDraw.Draw(ebene)
    staerke = max(2, round(figur_b * 0.017))

    # Jede Windung ist ein Lauf mit Trägheit: Die Richtung ändert sich in
    # kleinen Schritten, nie sprunghaft. Ein erster Versuch legte waagerechte
    # Sinusbahnen übereinander — das ergab ein Streifenmuster und sah aus wie
    # eine Petrischale, nicht wie ein Gehirn. Furchen laufen nicht parallel.
    for i in range(GYRI_BAHNEN):
        u = wuerfel.uniform(0.23, 0.68)
        v = wuerfel.uniform(0.67, 0.91)
        # Die Startrichtung ist waagerecht mit etwas Streuung. Furchen laufen
        # in weiten Bögen quer über die Hemisphäre, nicht in alle Richtungen:
        # Bei freier Startrichtung und starker Krümmung entstand ein
        # Wollknäuel, in dem sich die Bahnen ständig selbst kreuzten.
        winkel = (0.0 if i % 2 else math.pi) + wuerfel.uniform(-0.55, 0.55)
        drall = wuerfel.uniform(-0.08, 0.08)
        punkte = []
        for _ in range(46):
            punkte.append((x + u * b, y + (1 - v) * h))
            drall += wuerfel.uniform(-0.05, 0.05)
            drall = max(-0.16, min(0.16, drall))
            winkel += drall
            u += math.cos(winkel) * GYRI_AUSSCHLAG * 0.55
            v += math.sin(winkel) * GYRI_AUSSCHLAG * 0.55
            # Am Rand endet die Bahn. Umkehren wäre naheliegend und war der
            # zweite Grund für das Knäuel — die Bahnen sammelten sich dann
            # an der Kontur und verknoteten sich dort.
            if not (0.21 < u < 0.71 and 0.65 < v < 0.93):
                break
        if len(punkte) > 3:
            zeichner.line(punkte, fill=205,
                          width=max(2, round(staerke * wuerfel.uniform(0.8, 1.2))),
                          joint="curve")

    return ImageChops.multiply(ebene, hirn_maske)


def _nervennetz(groesse, wuerfel, hirn_polygon, rahmen, figur_b):
    """Knoten im Gehirn, mit ihren nächsten Nachbarn verbunden.

    Das Netz trägt das Gehirn, nicht die Windungen: Eine Strichgrafik kann
    Furchen nicht plastisch machen, ein Netz braucht keine Plastik. Es ist
    zugleich die passendere Aussage für dieses Buch — es geht um Signale
    zwischen Zellen, nicht um Faltung.

    Die Knoten werden verworfen und neu gezogen, bis sie weit genug
    auseinanderliegen. Ein reines Zufallsmuster ballt sich an einigen
    Stellen und lässt anderswo Löcher, und beides sieht man dem Bild an.
    """
    x, y, b, h = rahmen
    knoten = []
    versuche = 0
    while len(knoten) < NETZ_KNOTEN and versuche < NETZ_KNOTEN * 400:
        versuche += 1
        p = (wuerfel.uniform(0.21, 0.71), wuerfel.uniform(0.64, 0.94))
        if not _im_polygon(p, hirn_polygon):
            continue
        if any(math.dist(p, q) < NETZ_ABSTAND for q in knoten):
            continue
        knoten.append(p)

    def ab(p):
        return (x + p[0] * b, y + (1 - p[1]) * h)

    ebene = Image.new("L", groesse, 0)
    zeichner = ImageDraw.Draw(ebene)
    for i, p in enumerate(knoten):
        nah = sorted(range(len(knoten)),
                     key=lambda j: math.dist(p, knoten[j]))[1:NETZ_NACHBARN + 1]
        for j in nah:
            if math.dist(p, knoten[j]) < NETZ_ABSTAND * 3.0:
                zeichner.line([ab(p), ab(knoten[j])], fill=105,
                              width=max(1, round(figur_b * 0.0022)))
    for p in knoten:
        px, py = ab(p)
        r = figur_b * 0.0048
        zeichner.ellipse([px - r, py - r, px + r, py + r], fill=190)
    return ebene


def _knochen(groesse, rahmen, figur_b):
    """Augenhöhle, Nasenöffnung, Kiefer mit Zahnreihe und Halswirbelsäule.

    Alles auf einer Maske, damit es in einem Zug eingefärbt und mit einem
    Hof versehen werden kann.
    """
    x, y, b, h = rahmen

    def ab(px, py):
        return (x + px * b, y + (1 - py) * h)

    maske = Image.new("L", groesse, 0)
    zeichner = ImageDraw.Draw(maske)
    strich = max(2, round(figur_b * 0.007))

    # Augenhöhle und Nasenöffnung sind Öffnungen im Knochen — als Fläche
    # gezeichnet und nicht als Umriss, sonst verschwinden sie im Druck.
    # Die Augenhöhle als **Linie**, nicht als Fläche. Gefüllt war sie ein
    # heller Klecks im Gesicht; als Kontur liest sie sich als Knochen.
    zeichner.line([ab(*p) for p in polylinie(AUGENHOEHLE, schritte=10)]
                  + [ab(*AUGENHOEHLE[0])],
                  fill=120, width=strich, joint="curve")

    zeichner.line([ab(*p) for p in polylinie(UNTERKIEFER, geschlossen=False,
                                             schritte=12)],
                  fill=115, width=strich, joint="curve")

    # Nasenöffnung und Zahnreihe sind hier bewusst **nicht** gezeichnet.
    # Beides braucht auf 55 mm Kopfbreite mehr Auflösung, als der Druck
    # hergibt: Das Dreieck der Nase wurde zur Flosse, die Zahnreihe zum
    # Reißverschluss. Die Vorlage kann sich das leisten, weil sie ein
    # 3D-Rendering mit echten Volumen ist. Die Konstanten stehen oben —
    # wer es mit mehr Auflösung versuchen will, findet sie dort.

    for wx, wy, halb in WIRBEL:
        p1 = ab(wx - halb, wy + WIRBEL_HOEHE)
        p2 = ab(wx + halb, wy - WIRBEL_HOEHE)
        zeichner.rounded_rectangle(
            [min(p1[0], p2[0]), min(p1[1], p2[1]),
             max(p1[0], p2[0]), max(p1[1], p2[1])],
            radius=figur_b * 0.007, fill=122)

    return maske


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

    # 1 — Grund: waagerecht von Türkis nach Violett, nach unten abgedunkelt.
    #     Der Verlauf wird über eine Spalte gerechnet und gedreht; rotate(90)
    #     dreht gegen den Uhrzeigersinn, deshalb steht LINKS zuerst.
    grund = _verlaufsbild((hoehe, breite), GRUND_LINKS, GRUND_RECHTS)
    grund = grund.rotate(90, expand=True).resize(groesse, Image.BILINEAR)
    abdunklung = _verlaufsbild(groesse, (255, 255, 255),
                               tuple([round(255 * GRUND_ABDUNKLUNG)] * 3))
    bild = ImageChops.multiply(grund, abdunklung)
    bild = ImageChops.add(bild, _bokeh(groesse, wuerfel))

    # 2 — Rahmen der Figur. Sie steht mittig, hat oben Luft und läuft unten
    #     aus dem Bild. Die Höhe ist so gewählt, dass der Hals die Unterkante
    #     gerade erreicht: Bei 0,78 der Bildhöhe reicht der Umriss mit seinen
    #     1,14 Rastereinheiten knapp darüber hinaus. Die Luft oben ist
    #     großzügiger, als sie im Einzelbild aussieht — auf dem Umschlag
    #     liegen die oberen 3,175 mm im Anschnitt.
    figur_h = hoehe * 0.78
    figur_b = figur_h * 0.736          # x-Ausdehnung der Punktfolgen
    rahmen = ((breite - figur_b) / 2 - 0.152 * figur_h,
              hoehe * 0.10, figur_h, figur_h)
    x, y, b, h = rahmen

    def ab(px, py):
        return (x + px * b, y + (1 - py) * h)

    umriss = polylinie(KOPF_UMRISS, spannung=7.5)
    hirn = polylinie(KOPF_HIRN)
    klein = polylinie(KOPF_KLEINHIRN)

    kopf_maske = _maske(groesse, umriss, rahmen)

    # 3 — Der Kopf ist fast schwarz, mit einem leichten Verlauf von hinten
    #     nach vorn. Das ist der Punkt, an dem die Vorlage ihre Wirkung
    #     herholt: Erst auf einem dunklen Körper leuchten Knochen und Gehirn.
    volumen = _verlaufsbild((hoehe, breite), KOPF_HINTEN, KOPF_VORN)
    volumen = volumen.rotate(90, expand=True).resize(groesse, Image.BILINEAR)
    bild = Image.composite(volumen, bild,
                           kopf_maske.filter(ImageFilter.GaussianBlur(s * 0.8)))

    # 4 — Knochen: Augenhöhle, Nase, Kiefer, Zähne, Wirbelsäule. Erst der
    #     Hof, dann die Linien — sonst wirken sie flach aufgeklebt.
    knochen = _knochen(groesse, rahmen, figur_b)
    knochen = ImageChops.multiply(knochen, kopf_maske)
    bild = ImageChops.add(bild, _farbig(
        knochen.filter(ImageFilter.GaussianBlur(figur_b * 0.012)).point(
            lambda v: round(v * 0.55)), KNOCHEN))
    bild = ImageChops.add(bild, _farbig(knochen, KNOCHEN))

    # 5 — Gehirn: Fläche, dann Windungen, dann eine helle Kante.
    hirn_maske = ImageChops.lighter(_maske(groesse, hirn, rahmen),
                                    _maske(groesse, klein, rahmen))
    bild = Image.composite(
        Image.new("RGB", groesse, HIRN_GRUND), bild,
        hirn_maske.filter(ImageFilter.GaussianBlur(figur_b * 0.008)).point(
            lambda v: round(v * 0.78)))

    # Die Windungen liegen leise darunter — als Textur, nicht als Zeichnung.
    # Bei voller Helligkeit lasen sie sich als Gekritzel: Furchen brauchen
    # Volumen, um als Furchen zu wirken, und Volumen hat eine Strichgrafik
    # nicht. Was das Gehirn tatsächlich lesbar macht, ist das Netz darüber.
    windungen = _gyri(groesse, wuerfel, hirn_maske, rahmen, figur_b)
    bild = ImageChops.add(bild, _farbig(
        windungen.filter(ImageFilter.GaussianBlur(figur_b * 0.016)).point(
            lambda v: round(v * 0.34)), GYRI))
    bild = ImageChops.add(bild, _farbig(windungen.point(
        lambda v: round(v * 0.26)), GYRI))

    netz = _nervennetz(groesse, wuerfel, hirn, rahmen, figur_b)
    bild = ImageChops.add(bild, _farbig(
        netz.filter(ImageFilter.GaussianBlur(figur_b * 0.010)).point(
            lambda v: round(v * 0.55)), GYRI))
    bild = ImageChops.add(bild, _farbig(netz, GYRI))

    hirn_kante, _ = _randlicht(groesse, hirn, rahmen, figur_b * 0.0045)
    bild = ImageChops.add(bild, _farbig(hirn_kante.point(
        lambda v: round(v * 0.60)), GYRI))

    # 6 — Synapsen: heller Kern, weiter Hof. Der Hof ist der Grund, warum
    #     das Bild leuchtet und nicht nur bunte Punkte trägt. Die Punkte
    #     werden im Gehirn gestreut und verworfen, wenn sie danebenliegen.
    kerne = Image.new("L", groesse, 0)
    hoefe = Image.new("L", groesse, 0)
    k_zeichner, h_zeichner = ImageDraw.Draw(kerne), ImageDraw.Draw(hoefe)
    gesetzt, versuche = 0, 0
    while gesetzt < SYNAPSEN and versuche < SYNAPSEN * 200:
        versuche += 1
        p = (wuerfel.uniform(0.22, 0.70), wuerfel.uniform(0.60, 0.94))
        if not _im_polygon(p, hirn):
            continue
        gesetzt += 1
        px, py = ab(*p)
        r = figur_b * wuerfel.uniform(0.0055, 0.0110)
        k_zeichner.ellipse([px - r, py - r, px + r, py + r], fill=255)
        # Der Hof war zuerst fünfmal so groß wie der Kern. Daraus wurden
        # orange Flecken, die alles darunter überdeckten — ein Hof soll den
        # Punkt tragen, nicht ihn ersetzen.
        hr = r * 3.4
        h_zeichner.ellipse([px - hr, py - hr, px + hr, py + hr], fill=120)
    hoefe = hoefe.filter(ImageFilter.GaussianBlur(figur_b * 0.012))

    bild = ImageChops.add(bild, _farbig(hoefe, SYNAPSE))
    bild = ImageChops.add(bild, _farbig(
        kerne.filter(ImageFilter.GaussianBlur(figur_b * 0.0022)), SYNAPSE))
    bild = ImageChops.add(bild, _farbig(
        kerne.filter(ImageFilter.GaussianBlur(s * 0.6)), (255, 226, 190)))

    # 7 — Randlicht der Profillinie, zuletzt und über allem
    kern, hof = _randlicht(groesse, umriss, rahmen, figur_b * 0.0070)
    bild = ImageChops.add(bild, _farbig(hof, (26, 92, 118)))
    bild = ImageChops.add(bild, _farbig(kern, RANDLICHT))

    # 8 — Vignette und feines Korn. Das Korn ist kein Effekt, sondern gegen
    #     Streifenbildung: Ein glatter Verlauf über 30 cm zeigt im Druck
    #     sonst Stufen, und ein Prozent Rauschen bricht sie auf.
    bild = Image.composite(bild, Image.new("RGB", groesse, (0, 0, 0)),
                           _vignette(groesse).point(
                               lambda v: 145 + round(v * 110 / 255)))
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
