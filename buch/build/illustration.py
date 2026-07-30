"""Vektor-Illustrationen von Obst und Gemüse für die Umschläge beider Bände.

Alles wird direkt mit reportlab gezeichnet: rechtefrei, in jeder Größe scharf
und ohne externe Bilddateien. Im Container ist kein lizenziertes Bildmaterial
verfügbar, und die Web-Grafiken der Website haben keine Druckauflösung.

Jede Funktion zeichnet ein Motiv zentriert auf (x, y) in ein gedachtes Quadrat
der Kantenlänge `groesse`. Alle Maße in Punkt.

**Wichtig:** Abgebildet wird ausschließlich, was das Konzept auch erlaubt.
Banane, Weintraube, Ananas und Karotte stehen auf der Vermeiden-Liste und
haben auf dem Umschlag nichts zu suchen.
"""

import math

from reportlab.lib.colors import HexColor

# --- Palette -----------------------------------------------------------------
PALETTE = {
    "papier": HexColor("#FBFAF5"),
    "blatt": HexColor("#2F7A3E"),
    "blatt_hell": HexColor("#6FA85E"),
    "blatt_tief": HexColor("#1F5A2C"),
    "avocado_schale": HexColor("#3D6B33"),
    "avocado_fleisch": HexColor("#C7D96B"),
    "avocado_kern": HexColor("#8B6239"),
    "paprika_rot": HexColor("#D1483C"),
    "paprika_gruen": HexColor("#5BA34A"),
    "zitrone": HexColor("#F2C43D"),
    "zitrone_hell": HexColor("#F8E08A"),
    "gurke_schale": HexColor("#4E8A3C"),
    "gurke_fleisch": HexColor("#DCEBC4"),
    "beere": HexColor("#4A5B8C"),
    "beere_hell": HexColor("#6E7EAB"),
    "erdbeere": HexColor("#D1483C"),
    "erdbeere_kern": HexColor("#F5E3A0"),
    "tomate": HexColor("#D9533F"),
    "pilz_hut": HexColor("#C9A57B"),
    "pilz_stiel": HexColor("#EDE0CB"),
    "tinte": HexColor("#243021"),
}


def _ellipse(c, x, y, rx, ry, fuellung, kontur=None, strich=0):
    c.saveState()
    c.setFillColor(fuellung)
    if kontur is not None and strich:
        c.setStrokeColor(kontur)
        c.setLineWidth(strich)
    c.ellipse(x - rx, y - ry, x + rx, y + ry,
              stroke=1 if (kontur is not None and strich) else 0, fill=1)
    c.restoreState()


# --- Motive ------------------------------------------------------------------
def avocado(c, x, y, groesse):
    """Halbierte Avocado mit Kern — das Leitmotiv."""
    h = groesse / 2
    # Schale: birnenförmiger Umriss
    c.saveState()
    c.setFillColor(PALETTE["avocado_schale"])
    p = c.beginPath()
    p.moveTo(x, y + h)
    p.curveTo(x + h * 0.62, y + h * 0.80, x + h * 0.78, y + h * 0.05,
              x + h * 0.66, y - h * 0.45)
    p.curveTo(x + h * 0.56, y - h * 0.92, x - h * 0.56, y - h * 0.92,
              x - h * 0.66, y - h * 0.45)
    p.curveTo(x - h * 0.78, y + h * 0.05, x - h * 0.62, y + h * 0.80,
              x, y + h)
    p.close()
    c.drawPath(p, stroke=0, fill=1)

    # Fruchtfleisch, gleiche Form etwas kleiner
    c.setFillColor(PALETTE["avocado_fleisch"])
    f = 0.80
    p = c.beginPath()
    p.moveTo(x, y + h * f)
    p.curveTo(x + h * 0.62 * f, y + h * 0.80 * f, x + h * 0.78 * f, y + h * 0.05,
              x + h * 0.66 * f, y - h * 0.45 * f)
    p.curveTo(x + h * 0.56 * f, y - h * 0.92 * f, x - h * 0.56 * f, y - h * 0.92 * f,
              x - h * 0.66 * f, y - h * 0.45 * f)
    p.curveTo(x - h * 0.78 * f, y + h * 0.05, x - h * 0.62 * f, y + h * 0.80 * f,
              x, y + h * f)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()

    _ellipse(c, x, y - h * 0.28, h * 0.34, h * 0.34, PALETTE["avocado_kern"])


def brokkoli(c, x, y, groesse):
    h = groesse / 2
    c.saveState()
    # Strunk
    c.setFillColor(PALETTE["blatt_hell"])
    c.roundRect(x - h * 0.16, y - h, h * 0.32, h * 0.85,
                h * 0.12, stroke=0, fill=1)
    # Röschen als überlappende Kreise
    c.setFillColor(PALETTE["blatt"])
    roeschen = [
        (0.00, 0.52, 0.40), (-0.42, 0.30, 0.34), (0.42, 0.30, 0.34),
        (-0.22, 0.02, 0.32), (0.22, 0.02, 0.32), (0.00, 0.22, 0.34),
        (-0.58, 0.00, 0.24), (0.58, 0.00, 0.24),
    ]
    for dx, dy, r in roeschen:
        c.circle(x + dx * h, y + dy * h, r * h, stroke=0, fill=1)
    # Aufhellungen für Tiefe
    c.setFillColor(PALETTE["blatt_hell"])
    for dx, dy, r in [(-0.30, 0.44, 0.13), (0.16, 0.38, 0.10), (0.44, 0.14, 0.09)]:
        c.circle(x + dx * h, y + dy * h, r * h, stroke=0, fill=1)
    c.restoreState()


def paprika(c, x, y, groesse, farbe="paprika_gruen"):
    h = groesse / 2
    c.saveState()
    c.setFillColor(PALETTE[farbe])
    p = c.beginPath()
    p.moveTo(x - h * 0.70, y + h * 0.30)
    p.curveTo(x - h * 0.92, y - h * 0.30, x - h * 0.60, y - h * 0.95,
              x - h * 0.16, y - h * 0.86)
    p.curveTo(x, y - h * 0.82, x, y - h * 0.82, x + h * 0.16, y - h * 0.86)
    p.curveTo(x + h * 0.60, y - h * 0.95, x + h * 0.92, y - h * 0.30,
              x + h * 0.70, y + h * 0.30)
    p.curveTo(x + h * 0.56, y + h * 0.68, x - h * 0.56, y + h * 0.68,
              x - h * 0.70, y + h * 0.30)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # Stiel
    c.setFillColor(PALETTE["blatt_tief"])
    c.roundRect(x - h * 0.09, y + h * 0.52, h * 0.18, h * 0.42,
                h * 0.07, stroke=0, fill=1)
    _ellipse(c, x, y + h * 0.56, h * 0.30, h * 0.11, PALETTE["blatt"])
    c.restoreState()


def zitrone(c, x, y, groesse):
    """Zitronenhälfte mit Segmenten."""
    h = groesse / 2
    _ellipse(c, x, y, h * 0.86, h * 0.86, PALETTE["zitrone"])
    _ellipse(c, x, y, h * 0.72, h * 0.72, PALETTE["zitrone_hell"])
    c.saveState()
    c.setStrokeColor(PALETTE["zitrone"])
    c.setLineWidth(max(0.6, h * 0.055))
    for i in range(8):
        winkel = i * math.pi / 4
        c.line(x, y,
               x + math.cos(winkel) * h * 0.70,
               y + math.sin(winkel) * h * 0.70)
    c.restoreState()


def gurkenscheibe(c, x, y, groesse):
    h = groesse / 2
    _ellipse(c, x, y, h * 0.85, h * 0.85, PALETTE["gurke_schale"])
    _ellipse(c, x, y, h * 0.70, h * 0.70, PALETTE["gurke_fleisch"])
    c.saveState()
    c.setFillColor(PALETTE["blatt_hell"])
    for i in range(6):
        winkel = i * math.pi / 3 + 0.4
        c.circle(x + math.cos(winkel) * h * 0.34,
                 y + math.sin(winkel) * h * 0.34,
                 h * 0.10, stroke=0, fill=1)
    c.restoreState()


def heidelbeeren(c, x, y, groesse):
    h = groesse / 2
    for dx, dy, r in [(-0.42, -0.18, 0.40), (0.34, 0.10, 0.46), (0.02, -0.48, 0.34)]:
        _ellipse(c, x + dx * h, y + dy * h, r * h, r * h, PALETTE["beere"])
        c.saveState()
        c.setStrokeColor(PALETTE["beere_hell"])
        c.setLineWidth(max(0.5, h * 0.05))
        for i in range(5):
            w = i * 2 * math.pi / 5
            c.line(x + dx * h, y + dy * h,
                   x + dx * h + math.cos(w) * r * h * 0.42,
                   y + dy * h + math.sin(w) * r * h * 0.42)
        c.restoreState()


def erdbeere(c, x, y, groesse):
    h = groesse / 2
    c.saveState()
    c.setFillColor(PALETTE["erdbeere"])
    p = c.beginPath()
    p.moveTo(x, y - h * 0.92)
    p.curveTo(x + h * 0.78, y - h * 0.20, x + h * 0.70, y + h * 0.52,
              x, y + h * 0.52)
    p.curveTo(x - h * 0.70, y + h * 0.52, x - h * 0.78, y - h * 0.20,
              x, y - h * 0.92)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    # Kerne
    c.setFillColor(PALETTE["erdbeere_kern"])
    for dx, dy in [(-0.34, 0.16), (0.00, 0.28), (0.34, 0.16), (-0.20, -0.14),
                   (0.20, -0.14), (0.00, -0.44)]:
        c.circle(x + dx * h, y + dy * h, h * 0.055, stroke=0, fill=1)
    # Blätter
    c.setFillColor(PALETTE["blatt"])
    for winkel in (-0.9, -0.3, 0.3, 0.9):
        c.saveState()
        c.translate(x, y + h * 0.52)
        c.rotate(math.degrees(winkel))
        c.ellipse(-h * 0.09, 0, h * 0.09, h * 0.42, stroke=0, fill=1)
        c.restoreState()
    c.restoreState()


def tomate(c, x, y, groesse):
    h = groesse / 2
    _ellipse(c, x, y - h * 0.06, h * 0.82, h * 0.74, PALETTE["tomate"])
    c.saveState()
    c.setFillColor(PALETTE["blatt"])
    for i in range(5):
        winkel = i * 2 * math.pi / 5 + 0.3
        c.saveState()
        c.translate(x, y + h * 0.60)
        c.rotate(math.degrees(winkel))
        c.ellipse(-h * 0.07, 0, h * 0.07, h * 0.34, stroke=0, fill=1)
        c.restoreState()
    c.circle(x, y + h * 0.62, h * 0.10, stroke=0, fill=1)
    c.restoreState()


def spargel(c, x, y, groesse):
    h = groesse / 2
    c.saveState()
    c.setFillColor(PALETTE["blatt_hell"])
    for i, dx in enumerate((-0.34, 0.0, 0.34)):
        neigung = dx * 0.30
        c.saveState()
        c.translate(x + dx * h, y)
        c.rotate(math.degrees(-neigung))
        c.roundRect(-h * 0.10, -h * 0.90, h * 0.20, h * 1.55,
                    h * 0.09, stroke=0, fill=1)
        c.setFillColor(PALETTE["blatt"])
        p = c.beginPath()
        p.moveTo(0, h * 0.95)
        p.lineTo(-h * 0.13, h * 0.52)
        p.lineTo(h * 0.13, h * 0.52)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.setFillColor(PALETTE["blatt_hell"])
        c.restoreState()
    c.restoreState()


def kraeuterzweig(c, x, y, groesse, blaetter=5):
    """Kräuterzweig mit paarweise angesetzten Blättern."""
    h = groesse / 2
    c.saveState()
    c.setStrokeColor(PALETTE["blatt"])
    c.setLineWidth(max(0.8, h * 0.06))
    c.line(x, y - h * 0.9, x, y + h * 0.85)

    c.setFillColor(PALETTE["blatt_hell"])
    for i in range(blaetter):
        anteil = i / max(1, blaetter - 1)
        hoehe = y - h * 0.62 + anteil * h * 1.35
        laenge = h * (0.60 - anteil * 0.26)
        breite = h * 0.17
        for seite in (-1, 1):
            c.saveState()
            c.translate(x, hoehe)
            c.rotate(seite * 38)
            # Blattform als zwei gespiegelte Bögen statt gefüllter Ellipse:
            # ergibt eine Spitze und wirkt weniger klobig.
            p = c.beginPath()
            p.moveTo(0, 0)
            p.curveTo(seite * laenge * 0.35, breite,
                      seite * laenge * 0.75, breite * 0.7,
                      seite * laenge, 0)
            p.curveTo(seite * laenge * 0.75, -breite * 0.7,
                      seite * laenge * 0.35, -breite,
                      0, 0)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.restoreState()
    # Triebspitze
    c.setFillColor(PALETTE["blatt"])
    p = c.beginPath()
    p.moveTo(x, y + h * 0.95)
    p.curveTo(x - h * 0.16, y + h * 0.62, x - h * 0.10, y + h * 0.55,
              x, y + h * 0.52)
    p.curveTo(x + h * 0.10, y + h * 0.55, x + h * 0.16, y + h * 0.62,
              x, y + h * 0.95)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def pilz(c, x, y, groesse):
    h = groesse / 2
    c.saveState()
    c.setFillColor(PALETTE["pilz_stiel"])
    c.roundRect(x - h * 0.22, y - h * 0.85, h * 0.44, h * 0.90,
                h * 0.10, stroke=0, fill=1)
    c.setFillColor(PALETTE["pilz_hut"])
    p = c.beginPath()
    p.moveTo(x - h * 0.82, y + h * 0.05)
    p.curveTo(x - h * 0.80, y + h * 0.85, x + h * 0.80, y + h * 0.85,
              x + h * 0.82, y + h * 0.05)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


# --- Kompositionen -----------------------------------------------------------
#  (Motivfunktion, x-Anteil, y-Anteil, Größe als Anteil der Breite, Drehung)
BAND_OBEN = [
    (kraeuterzweig, 0.09, 0.52, 0.15, -12),
    (zitrone, 0.22, 0.74, 0.17, 0),
    (brokkoli, 0.37, 0.46, 0.22, 0),
    (avocado, 0.53, 0.76, 0.20, 8),
    (paprika, 0.70, 0.48, 0.20, -6),
    (gurkenscheibe, 0.85, 0.74, 0.16, 0),
    (heidelbeeren, 0.94, 0.44, 0.15, 0),
]

BAND_UNTEN = [
    (spargel, 0.10, 0.52, 0.18, 6),
    (erdbeere, 0.26, 0.30, 0.15, -8),
    (tomate, 0.42, 0.58, 0.17, 0),
    (pilz, 0.58, 0.30, 0.15, 0),
    (gurkenscheibe, 0.72, 0.60, 0.14, 0),
    (kraeuterzweig, 0.88, 0.42, 0.16, 14),
]


def komposition_zeichnen(c, motive, x, y, breite, hoehe):
    """Zeichnet eine Motivliste in den Rahmen (x, y, breite, hoehe)."""
    for zeichnen, ax, ay, agroesse, drehung in motive:
        mx = x + ax * breite
        my = y + ay * hoehe
        groesse = agroesse * breite
        c.saveState()
        c.translate(mx, my)
        c.rotate(drehung)
        zeichnen(c, 0, 0, groesse)
        c.restoreState()


def streifen_tagesfarben(c, x, y, breite, hoehe):
    """Schmaler Balken in Weiß, Grün und Rot — das Tagesfarbensystem."""
    farben = [HexColor("#FFFFFF"), PALETTE["blatt_hell"], PALETTE["erdbeere"]]
    teil = breite / len(farben)
    c.saveState()
    for i, farbe in enumerate(farben):
        c.setFillColor(farbe)
        c.setStrokeColor(PALETTE["blatt"])
        c.setLineWidth(0.5)
        c.rect(x + i * teil, y, teil, hoehe, stroke=1, fill=1)
    c.restoreState()
