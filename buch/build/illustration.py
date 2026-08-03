"""Plastische Vektor-Illustrationen von Obst und Gemüse für die Umschläge.

Gezeichnet mit reportlab: rechtefrei, in jeder Größe scharf, ohne externe
Bilddateien. Fotos sind in dieser Umgebung nicht beschaffbar — der
Netzwerkzugang ist auf wenige Paketquellen beschränkt, und das Bildmaterial
der Website hat Web-Auflösung.

Um dem Eindruck echter Lebensmittel möglichst nahe zu kommen, arbeitet jedes
Motiv mit vier Lagen:

  1. weicher Schlagschatten darunter
  2. Grundkörper mit Radialverlauf (Lichtquelle oben links)
  3. Detailzeichnung — Segmente, Kerne, Maserung
  4. Glanzlicht

Wer ein echtes Foto einsetzen will: `build_cover.py` verwendet automatisch
`buch/cover/titelbild.jpg`, sobald die Datei existiert (mind. 1800 x 2700 px).

**Wichtig:** Abgebildet wird ausschließlich, was das Konzept auch erlaubt.
Banane, Weintraube, Ananas und Karotte stehen auf der Vermeiden-Liste.
"""

import math

from reportlab.lib.colors import HexColor

# --- Palette -----------------------------------------------------------------
PALETTE = {
    "papier": HexColor("#FBFAF5"),
    "blatt": HexColor("#2F7A3E"),
    "blatt_hell": HexColor("#6FA85E"),
    "blatt_tief": HexColor("#1F5A2C"),
    "erdbeere": HexColor("#C8382C"),
    "tinte": HexColor("#243021"),
    "schatten": HexColor("#B9BCAF"),
}

# Zweite Farbwelt: Lebensmittel auf hellem Anthrazit. Dieselben Motive, nur
# Grund, Schrift und Schlagschatten wechseln.
#
# Der Grund ist bewusst kein Schwarz. Anthrazit lässt die Lebensmittel warm
# wirken statt hart ausgeschnitten — kostet aber Kontrast: Jede Aufhellung des
# Grundes drückt die helleren Schriften und Akzente nach unten. Alle Werte
# unten sind auf mindestens 4,5:1 gegen den helleren der beiden Grundtöne
# gerechnet; wer am Grund dreht, muss sie nachrechnen.
SCHIEFER = {
    "grund": HexColor("#454B54"),
    "grund_tief": HexColor("#3E434B"),   # flacher Verlauf, damit der Fuß
                                         # des Umschlags nicht wieder absäuft
    "text": HexColor("#F5F7F2"),        # 8,2:1
    "text_leise": HexColor("#B4BCB3"),  # 4,5:1
    "akzent": HexColor("#9DD380"),      # wird je Band gesetzt
    "balkentext": HexColor("#23272D"),  # dunkle Schrift auf dem Akzentbalken
    "schatten": HexColor("#05070A"),
}

# Je Band eine eigene Akzentfarbe, damit sich die drei Umschläge im Regal und
# im Amazon-Vorschaubild unterscheiden — dort ist der Titel bei allen dreien
# derselbe. Alle drei stammen aus der Lebensmittelpalette, halten Abstand zum
# FitLine-Crimson #C8102E und erreichen rund 5:1 gegen den Grund.
AKZENTE = {
    "blatt": HexColor("#9DD380"),    # Band 1 — Blattgrün
    "zitrone": HexColor("#E9BF47"),  # Band 2 — Zitronengelb
    "beere": HexColor("#CDBEE8"),    # Band 3 — Heidelbeere, aufgehellt
}

# Steuert nur die Schlagschatten. Auf hellem Grund sind sie hellgrau, auf
# dunklem fast schwarz — ein heller Schatten auf Schiefer sähe aus wie ein
# Lichtkranz um jedes Motiv.
_GRUND = "hell"


def grund_setzen(art):
    """'hell' oder 'dunkel' — bestimmt die Schattenfarbe der Motive."""
    global _GRUND
    if art not in ("hell", "dunkel"):
        raise ValueError(f"Unbekannter Grund: {art}")
    _GRUND = art


def akzent_setzen(name):
    """Wählt die Akzentfarbe des Bandes aus AKZENTE."""
    if name not in AKZENTE:
        raise SystemExit(
            f"Unbekannter cover_akzent: {name} ({' | '.join(AKZENTE)})")
    SCHIEFER["akzent"] = AKZENTE[name]

# Verlaufstripel je Motiv: (Glanz, Mitte, Tiefe)
TOENE = {
    "tomate": ("#F07A62", "#D6412C", "#8E2318"),
    "zitrone": ("#FBEBA6", "#F0C230", "#C68F12"),
    "zitrone_fleisch": ("#FDF6D2", "#F7DE86", "#E2C25C"),
    "avocado_schale": ("#4C7F3C", "#335D28", "#1D3A16"),
    "avocado_fleisch": ("#E4EEA6", "#C3D46A", "#95AB44"),
    "avocado_kern": ("#B08355", "#8A6034", "#5C3E1F"),
    "paprika": ("#7DC45E", "#4E9B3C", "#2E6B22"),
    "brokkoli": ("#63A24E", "#3B7A31", "#22521F"),
    "brokkoli_strunk": ("#CBDDA0", "#A8C47B", "#7C9955"),
    "gurke_schale": ("#79B04E", "#4C8A32", "#2C5C1D"),
    "gurke_fleisch": ("#F0F6DC", "#DAE9BE", "#BCD199"),
    "beere": ("#7A88B8", "#48568C", "#252F55"),
    "erdbeere": ("#EB6B55", "#C8382C", "#831C15"),
    "pilz_hut": ("#E3C69C", "#C09A6B", "#8E6C42"),
    "pilz_stiel": ("#F7EEDD", "#E3D5BC", "#BFAF92"),
    "spargel": ("#A8C97F", "#7BA453", "#4F7431"),
    "kraut": ("#7FB562", "#4E8C3C", "#2C5F24"),
}


def _farben(schluessel):
    return [HexColor(t) for t in TOENE[schluessel]]


def _schatten(c, x, y, rx, ry):
    """Weicher Schlagschatten aus mehreren transparenten Ellipsen."""
    dunkel = _GRUND == "dunkel"
    farbe = SCHIEFER["schatten"] if dunkel else PALETTE["schatten"]
    # Auf Schiefer darf der Schatten kräftiger sein, sonst schweben die
    # Motive über dem Grund, statt auf ihm zu liegen.
    stufen = (((1.06, 0.20), (0.88, 0.22), (0.70, 0.24), (0.52, 0.26))
              if dunkel else
              ((1.00, 0.05), (0.86, 0.06), (0.70, 0.07), (0.54, 0.08)))
    c.saveState()
    for faktor, alpha in stufen:
        c.setFillColor(farbe, alpha=alpha)
        c.ellipse(x - rx * faktor, y - ry * faktor,
                  x + rx * faktor, y + ry * faktor, stroke=0, fill=1)
    c.restoreState()


def _kugel(c, x, y, rx, ry, toene, *, licht=(-0.34, 0.34)):
    """Runder Körper mit Radialverlauf — erzeugt den Eindruck von Volumen."""
    hell, mitte, tief = _farben(toene)
    c.saveState()
    p = c.beginPath()
    p.ellipse(x - rx, y - ry, 2 * rx, 2 * ry)
    c.clipPath(p, stroke=0, fill=0)
    c.radialGradient(x + licht[0] * rx, y + licht[1] * ry,
                     max(rx, ry) * 1.55,
                     [hell, mitte, tief], [0.0, 0.45, 1.0])
    c.restoreState()


def _pfad_verlauf(c, pfad_bauen, toene, cx, cy, radius, *, licht=(-0.3, 0.3)):
    """Beliebige Form mit Radialverlauf füllen."""
    hell, mitte, tief = _farben(toene)
    c.saveState()
    p = c.beginPath()
    pfad_bauen(p)
    c.clipPath(p, stroke=0, fill=0)
    c.radialGradient(cx + licht[0] * radius, cy + licht[1] * radius,
                     radius * 1.6, [hell, mitte, tief], [0.0, 0.45, 1.0])
    c.restoreState()


def _glanz(c, x, y, rx, ry, *, alpha=0.42, drehung=-28):
    c.saveState()
    c.translate(x, y)
    c.rotate(drehung)
    c.setFillColor(HexColor("#FFFFFF"), alpha=alpha)
    c.ellipse(-rx, -ry, rx, ry, stroke=0, fill=1)
    c.restoreState()


# --- Motive ------------------------------------------------------------------
def tomate(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.80, h * 0.72, h * 0.15)
    _kugel(c, x, y - h * 0.05, h * 0.84, h * 0.76, "tomate")

    # Wölbungsrillen
    c.saveState()
    c.setStrokeColor(HexColor("#A62C1E"), alpha=0.30)
    c.setLineWidth(max(0.5, h * 0.045))
    for versatz in (-0.42, 0.0, 0.42):
        c.bezier(x + versatz * h, y + h * 0.62,
                 x + versatz * h * 1.5, y + h * 0.10,
                 x + versatz * h * 1.5, y - h * 0.30,
                 x + versatz * h * 0.75, y - h * 0.72)
    c.restoreState()

    _glanz(c, x - h * 0.34, y + h * 0.34, h * 0.24, h * 0.14)

    # Kelchblätter
    c.saveState()
    for i in range(6):
        c.saveState()
        c.translate(x, y + h * 0.62)
        c.rotate(i * 60 + 12)
        gruen = _farben("blatt" if False else "kraut")
        c.setFillColor(gruen[1])
        p = c.beginPath()
        p.moveTo(0, 0)
        p.curveTo(h * 0.10, h * 0.12, h * 0.16, h * 0.26, h * 0.05, h * 0.40)
        p.curveTo(h * 0.00, h * 0.26, -h * 0.06, h * 0.14, 0, 0)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.restoreState()
    c.setFillColor(_farben("kraut")[2])
    c.circle(x, y + h * 0.64, h * 0.09, stroke=0, fill=1)
    c.restoreState()


def zitrone(c, x, y, groesse):
    """Aufgeschnittene Zitrone mit Segmenten."""
    h = groesse / 2
    _schatten(c, x, y - h * 0.86, h * 0.72, h * 0.14)
    _kugel(c, x, y, h * 0.86, h * 0.86, "zitrone")
    _kugel(c, x, y, h * 0.74, h * 0.74, "zitrone_fleisch")

    # Segmente als Tortenstücke mit weißen Trennhäuten
    c.saveState()
    for i in range(8):
        a0 = i * math.pi / 4 + 0.10
        a1 = (i + 1) * math.pi / 4 - 0.10
        c.setFillColor(HexColor("#F6D96A"), alpha=0.85)
        p = c.beginPath()
        p.moveTo(x, y)
        p.lineTo(x + math.cos(a0) * h * 0.70, y + math.sin(a0) * h * 0.70)
        schritte = 6
        for s in range(1, schritte + 1):
            a = a0 + (a1 - a0) * s / schritte
            p.lineTo(x + math.cos(a) * h * 0.70, y + math.sin(a) * h * 0.70)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
    # Mittelachse
    c.setFillColor(HexColor("#FDF8E0"))
    c.circle(x, y, h * 0.09, stroke=0, fill=1)
    c.restoreState()
    _glanz(c, x - h * 0.30, y + h * 0.42, h * 0.20, h * 0.09, alpha=0.30)


def avocado(c, x, y, groesse):
    """Halbierte Avocado mit Kern — das Leitmotiv."""
    h = groesse / 2
    _schatten(c, x, y - h * 0.92, h * 0.60, h * 0.13)

    def umriss(p, f=1.0):
        # Birnenform: schmaler Hals oben, runder Bauch unten. Der Hals darf
        # nicht spitz zulaufen, sonst sieht die Frucht aus wie ein Tropfen.
        p.moveTo(x, y + h * 0.92 * f)
        p.curveTo(x + h * 0.24 * f, y + h * 0.91 * f,
                  x + h * 0.38 * f, y + h * 0.66 * f,
                  x + h * 0.44 * f, y + h * 0.30 * f)
        p.curveTo(x + h * 0.50 * f, y - h * 0.06 * f,
                  x + h * 0.74 * f, y - h * 0.20 * f,
                  x + h * 0.74 * f, y - h * 0.50 * f)
        p.curveTo(x + h * 0.74 * f, y - h * 0.86 * f,
                  x + h * 0.40 * f, y - h * 0.99 * f,
                  x, y - h * 0.99 * f)
        p.curveTo(x - h * 0.40 * f, y - h * 0.99 * f,
                  x - h * 0.74 * f, y - h * 0.86 * f,
                  x - h * 0.74 * f, y - h * 0.50 * f)
        p.curveTo(x - h * 0.74 * f, y - h * 0.20 * f,
                  x - h * 0.50 * f, y - h * 0.06 * f,
                  x - h * 0.44 * f, y + h * 0.30 * f)
        p.curveTo(x - h * 0.38 * f, y + h * 0.66 * f,
                  x - h * 0.24 * f, y + h * 0.91 * f,
                  x, y + h * 0.92 * f)
        p.close()

    _pfad_verlauf(c, umriss, "avocado_schale", x, y, h)
    _pfad_verlauf(c, lambda p: umriss(p, 0.82), "avocado_fleisch", x, y, h * 0.82)

    # Übergang Fleisch zu Schale etwas heller absetzen
    c.saveState()
    c.setStrokeColor(HexColor("#D8E88F"), alpha=0.55)
    c.setLineWidth(max(0.6, h * 0.05))
    p = c.beginPath()
    umriss(p, 0.82)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()

    _kugel(c, x, y - h * 0.28, h * 0.35, h * 0.35, "avocado_kern")
    _glanz(c, x - h * 0.14, y - h * 0.18, h * 0.09, h * 0.05, alpha=0.30)


def brokkoli(c, x, y, groesse):
    h = groesse / 2

    def strunk(p):
        # Kurz und kräftig mit abzweigenden Nebenstielen — ein dünner,
        # langer Stiel lässt den Brokkoli wie ein Bäumchen aussehen.
        p.moveTo(x - h * 0.26, y - h * 0.92)
        p.curveTo(x - h * 0.30, y - h * 0.55, x - h * 0.26, y - h * 0.40,
                  x - h * 0.34, y - h * 0.16)
        p.lineTo(x - h * 0.16, y - h * 0.08)
        p.lineTo(x + h * 0.02, y - h * 0.22)
        p.lineTo(x + h * 0.20, y - h * 0.06)
        p.lineTo(x + h * 0.36, y - h * 0.18)
        p.curveTo(x + h * 0.28, y - h * 0.42, x + h * 0.30, y - h * 0.58,
                  x + h * 0.26, y - h * 0.92)
        p.close()

    _schatten(c, x, y - h * 0.92, h * 0.58, h * 0.13)
    _pfad_verlauf(c, strunk, "brokkoli_strunk", x, y - h * 0.5, h * 0.55)

    # Röschen: breite, flache Krone aus vielen Kugeln. Hintere Reihe zuerst
    # und dunkler, damit Tiefe entsteht.
    hinten = [(-0.72, 0.26, 0.28), (0.72, 0.26, 0.28), (-0.40, 0.62, 0.28),
              (0.40, 0.62, 0.28), (0.00, 0.70, 0.30), (-0.60, 0.50, 0.24),
              (0.60, 0.50, 0.24)]
    vorne = [(-0.58, 0.22, 0.34), (0.58, 0.22, 0.34), (-0.28, 0.40, 0.38),
             (0.28, 0.40, 0.38), (0.00, 0.24, 0.36), (-0.20, 0.06, 0.28),
             (0.22, 0.06, 0.28)]

    c.saveState()
    for dx, dy, r in hinten:
        _kugel(c, x + dx * h, y + dy * h, r * h, r * h * 0.92, "brokkoli",
               licht=(-0.2, 0.2))
    for dx, dy, r in vorne:
        _kugel(c, x + dx * h, y + dy * h, r * h, r * h * 0.92, "brokkoli")
    c.restoreState()

    # Feine Krümel für die typische Textur
    c.saveState()
    c.setFillColor(HexColor("#8CBE6E"), alpha=0.55)
    for dx, dy, r in vorne:
        for k in range(7):
            winkel = k * 2 * math.pi / 7 + dx
            c.circle(x + dx * h + math.cos(winkel) * r * h * 0.55,
                     y + dy * h + math.sin(winkel) * r * h * 0.55,
                     r * h * 0.11, stroke=0, fill=1)
    c.restoreState()
    _glanz(c, x - h * 0.30, y + h * 0.46, h * 0.14, h * 0.07, alpha=0.25)


def paprika(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.90, h * 0.62, h * 0.13)

    def koerper(p):
        # Blockpaprika: breite Schultern oben, unten drei deutliche Lappen.
        # Ohne die Lappen wirkt die Form wie ein Apfel.
        p.moveTo(x - h * 0.78, y + h * 0.34)
        p.curveTo(x - h * 0.96, y - h * 0.10, x - h * 0.90, y - h * 0.52,
                  x - h * 0.62, y - h * 0.78)
        # linker Lappen
        p.curveTo(x - h * 0.50, y - h * 0.92, x - h * 0.36, y - h * 0.88,
                  x - h * 0.30, y - h * 0.70)
        # mittlerer Lappen, sitzt etwas tiefer
        p.curveTo(x - h * 0.22, y - h * 0.94, x - h * 0.06, y - h * 1.00,
                  x + h * 0.02, y - h * 0.96)
        p.curveTo(x + h * 0.12, y - h * 0.92, x + h * 0.20, y - h * 0.80,
                  x + h * 0.26, y - h * 0.68)
        # rechter Lappen
        p.curveTo(x + h * 0.34, y - h * 0.90, x + h * 0.52, y - h * 0.90,
                  x + h * 0.64, y - h * 0.76)
        p.curveTo(x + h * 0.90, y - h * 0.50, x + h * 0.96, y - h * 0.10,
                  x + h * 0.78, y + h * 0.34)
        p.curveTo(x + h * 0.66, y + h * 0.70, x - h * 0.66, y + h * 0.70,
                  x - h * 0.78, y + h * 0.34)
        p.close()

    _pfad_verlauf(c, koerper, "paprika", x, y, h)

    # Längsfurchen
    c.saveState()
    c.setStrokeColor(HexColor("#2E6B22"), alpha=0.28)
    c.setLineWidth(max(0.5, h * 0.05))
    for versatz in (-0.36, 0.36):
        c.bezier(x + versatz * h, y + h * 0.46,
                 x + versatz * h * 1.5, y + h * 0.00,
                 x + versatz * h * 1.4, y - h * 0.40,
                 x + versatz * h * 0.55, y - h * 0.80)
    c.restoreState()

    _glanz(c, x - h * 0.34, y + h * 0.18, h * 0.16, h * 0.34, alpha=0.34, drehung=-8)

    # Stiel
    c.saveState()
    gruen = _farben("kraut")
    c.setFillColor(gruen[1])
    c.roundRect(x - h * 0.09, y + h * 0.52, h * 0.18, h * 0.44,
                h * 0.07, stroke=0, fill=1)
    c.setFillColor(gruen[0])
    p = c.beginPath()
    p.moveTo(x - h * 0.30, y + h * 0.54)
    p.curveTo(x - h * 0.12, y + h * 0.68, x + h * 0.12, y + h * 0.68,
              x + h * 0.30, y + h * 0.54)
    p.curveTo(x + h * 0.12, y + h * 0.44, x - h * 0.12, y + h * 0.44,
              x - h * 0.30, y + h * 0.54)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def gurkenscheibe(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.88, h * 0.66, h * 0.12)
    _kugel(c, x, y, h * 0.86, h * 0.86, "gurke_schale")
    _kugel(c, x, y, h * 0.72, h * 0.72, "gurke_fleisch")

    # Kerne in zwei Ringen, leicht oval und unterschiedlich groß
    c.saveState()
    c.setFillColor(HexColor("#C3D89A"))
    for i in range(6):
        winkel = i * math.pi / 3 + 0.35
        c.saveState()
        c.translate(x + math.cos(winkel) * h * 0.34,
                    y + math.sin(winkel) * h * 0.34)
        c.rotate(math.degrees(winkel))
        c.ellipse(-h * 0.11, -h * 0.07, h * 0.11, h * 0.07, stroke=0, fill=1)
        c.restoreState()
    c.setFillColor(HexColor("#D6E7B4"))
    for i in range(3):
        winkel = i * 2 * math.pi / 3
        c.circle(x + math.cos(winkel) * h * 0.13,
                 y + math.sin(winkel) * h * 0.13, h * 0.05, stroke=0, fill=1)
    c.restoreState()
    _glanz(c, x - h * 0.32, y + h * 0.36, h * 0.18, h * 0.09, alpha=0.30)


def heidelbeeren(c, x, y, groesse):
    h = groesse / 2
    for dx, dy, r in ((-0.44, -0.20, 0.40), (0.02, -0.50, 0.34),
                      (0.36, 0.10, 0.46)):
        _schatten(c, x + dx * h, y + dy * h - r * h, r * h * 0.7, r * h * 0.16)
        _kugel(c, x + dx * h, y + dy * h, r * h, r * h * 0.94, "beere")
        # Blütenkranz auf der Oberseite
        c.saveState()
        c.setStrokeColor(HexColor("#9AA6CB"), alpha=0.65)
        c.setLineWidth(max(0.4, r * h * 0.10))
        for i in range(5):
            w = i * 2 * math.pi / 5 + 0.4
            c.line(x + dx * h, y + dy * h,
                   x + dx * h + math.cos(w) * r * h * 0.34,
                   y + dy * h + math.sin(w) * r * h * 0.34)
        c.setFillColor(HexColor("#B9C2DD"), alpha=0.55)
        c.circle(x + dx * h, y + dy * h, r * h * 0.10, stroke=0, fill=1)
        c.restoreState()
        _glanz(c, x + dx * h - r * h * 0.36, y + dy * h + r * h * 0.36,
               r * h * 0.20, r * h * 0.11, alpha=0.34)


def erdbeere(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.94, h * 0.44, h * 0.11)

    def koerper(p):
        p.moveTo(x, y - h * 0.94)
        p.curveTo(x + h * 0.44, y - h * 0.62, x + h * 0.76, y - h * 0.12,
                  x + h * 0.70, y + h * 0.26)
        p.curveTo(x + h * 0.64, y + h * 0.58, x - h * 0.64, y + h * 0.58,
                  x - h * 0.70, y + h * 0.26)
        p.curveTo(x - h * 0.76, y - h * 0.12, x - h * 0.44, y - h * 0.62,
                  x, y - h * 0.94)
        p.close()

    _pfad_verlauf(c, koerper, "erdbeere", x, y, h)

    # Nüsschen in versetzten Reihen, jeweils mit Schattenkante
    c.saveState()
    reihen = [(-0.44, 4, 0.44), (-0.16, 5, 0.52), (0.14, 4, 0.44),
              (0.40, 3, 0.30)]
    for dy, anzahl, spanne in reihen:
        for i in range(anzahl):
            dx = (i - (anzahl - 1) / 2) * (2 * spanne / max(1, anzahl - 1))
            c.setFillColor(HexColor("#8F2418"), alpha=0.55)
            c.circle(x + dx * h, y + dy * h - h * 0.018, h * 0.048,
                     stroke=0, fill=1)
            c.setFillColor(HexColor("#F7E4A8"))
            c.circle(x + dx * h, y + dy * h, h * 0.042, stroke=0, fill=1)
    c.restoreState()

    _glanz(c, x - h * 0.30, y + h * 0.14, h * 0.13, h * 0.22, alpha=0.28, drehung=-14)

    # Kelch
    c.saveState()
    gruen = _farben("kraut")
    for i, winkel in enumerate((-72, -36, 0, 36, 72)):
        c.saveState()
        c.translate(x, y + h * 0.46)
        c.rotate(winkel)
        c.setFillColor(gruen[0] if i % 2 else gruen[1])
        p = c.beginPath()
        p.moveTo(0, 0)
        p.curveTo(h * 0.13, h * 0.12, h * 0.16, h * 0.30, h * 0.02, h * 0.50)
        p.curveTo(-h * 0.08, h * 0.30, -h * 0.12, h * 0.12, 0, 0)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.restoreState()
    c.restoreState()


def spargel(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.95, h * 0.44, h * 0.10)
    hell, mitte, tief = _farben("spargel")
    for dx, neigung, laenge in ((-0.34, -7, 0.92), (0.02, 2, 1.00),
                                (0.36, 9, 0.88)):
        c.saveState()
        c.translate(x + dx * h, y)
        c.rotate(neigung)

        def stange(p, laenge=laenge):
            p.moveTo(-h * 0.11, -h * 0.95)
            p.lineTo(h * 0.11, -h * 0.95)
            p.lineTo(h * 0.085, h * 0.48 * laenge)
            p.curveTo(h * 0.06, h * 0.72 * laenge, -h * 0.06, h * 0.72 * laenge,
                      -h * 0.085, h * 0.48 * laenge)
            p.close()

        _pfad_verlauf(c, stange, "spargel", 0, 0, h * 0.5)

        # Kopf aus überlappenden Schuppen
        c.setFillColor(tief)
        p = c.beginPath()
        p.moveTo(0, h * 0.98 * laenge)
        p.curveTo(-h * 0.14, h * 0.72 * laenge, -h * 0.10, h * 0.58 * laenge,
                  0, h * 0.54 * laenge)
        p.curveTo(h * 0.10, h * 0.58 * laenge, h * 0.14, h * 0.72 * laenge,
                  0, h * 0.98 * laenge)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.setFillColor(mitte, alpha=0.8)
        for stufe in (0.62, 0.74, 0.86):
            c.circle(0, h * stufe * laenge, h * 0.055, stroke=0, fill=1)
        c.restoreState()


def kraeuterzweig(c, x, y, groesse, blaetter=5):
    h = groesse / 2
    hell, mitte, tief = _farben("kraut")
    c.saveState()
    c.setStrokeColor(tief)
    c.setLineWidth(max(0.8, h * 0.06))
    c.line(x, y - h * 0.92, x, y + h * 0.82)

    for i in range(blaetter):
        anteil = i / max(1, blaetter - 1)
        hoehe = y - h * 0.64 + anteil * h * 1.34
        laenge = h * (0.62 - anteil * 0.26)
        breite = h * 0.19
        for seite in (-1, 1):
            c.saveState()
            c.translate(x, hoehe)
            c.rotate(seite * 36)
            c.setFillColor(mitte if i % 2 else hell)
            p = c.beginPath()
            p.moveTo(0, 0)
            p.curveTo(seite * laenge * 0.30, breite,
                      seite * laenge * 0.72, breite * 0.68,
                      seite * laenge, 0)
            p.curveTo(seite * laenge * 0.72, -breite * 0.68,
                      seite * laenge * 0.30, -breite,
                      0, 0)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            # Mittelrippe
            c.setStrokeColor(tief, alpha=0.45)
            c.setLineWidth(max(0.3, h * 0.025))
            c.line(0, 0, seite * laenge * 0.92, 0)
            c.restoreState()

    c.setFillColor(mitte)
    p = c.beginPath()
    p.moveTo(x, y + h * 0.94)
    p.curveTo(x - h * 0.17, y + h * 0.62, x - h * 0.10, y + h * 0.52,
              x, y + h * 0.48)
    p.curveTo(x + h * 0.10, y + h * 0.52, x + h * 0.17, y + h * 0.62,
              x, y + h * 0.94)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def pilz(c, x, y, groesse):
    h = groesse / 2
    _schatten(c, x, y - h * 0.88, h * 0.52, h * 0.12)

    def stiel(p):
        p.moveTo(-h * 0.24 + x, y - h * 0.86)
        p.curveTo(x - h * 0.20, y - h * 0.30, x - h * 0.22, y - h * 0.10,
                  x - h * 0.20, y + h * 0.08)
        p.lineTo(x + h * 0.20, y + h * 0.08)
        p.curveTo(x + h * 0.22, y - h * 0.10, x + h * 0.20, y - h * 0.30,
                  x + h * 0.24, y - h * 0.86)
        p.close()

    _pfad_verlauf(c, stiel, "pilz_stiel", x, y - h * 0.4, h * 0.6)

    def hut(p):
        p.moveTo(x - h * 0.84, y + h * 0.06)
        p.curveTo(x - h * 0.82, y + h * 0.88, x + h * 0.82, y + h * 0.88,
                  x + h * 0.84, y + h * 0.06)
        p.curveTo(x + h * 0.50, y - h * 0.10, x - h * 0.50, y - h * 0.10,
                  x - h * 0.84, y + h * 0.06)
        p.close()

    _pfad_verlauf(c, hut, "pilz_hut", x, y + h * 0.3, h * 0.9)
    _glanz(c, x - h * 0.30, y + h * 0.48, h * 0.20, h * 0.10, alpha=0.30)

    # Lamellenandeutung unter dem Hutrand
    c.saveState()
    c.setStrokeColor(HexColor("#8E6C42"), alpha=0.40)
    c.setLineWidth(max(0.4, h * 0.035))
    for i in range(9):
        anteil = i / 8
        px = x - h * 0.70 + anteil * h * 1.40
        c.line(px, y + h * 0.02, px, y - h * 0.05)
    c.restoreState()


# --- Kompositionen -----------------------------------------------------------
#  (Motivfunktion, x-Anteil, y-Anteil, Größe als Anteil der Breite, Drehung)
BAND_OBEN = [
    (kraeuterzweig, 0.08, 0.52, 0.16, -12),
    (zitrone, 0.22, 0.74, 0.18, 0),
    (brokkoli, 0.38, 0.46, 0.23, 0),
    (avocado, 0.54, 0.76, 0.21, 8),
    (paprika, 0.71, 0.48, 0.21, -6),
    (gurkenscheibe, 0.86, 0.74, 0.17, 0),
    (heidelbeeren, 0.95, 0.42, 0.16, 0),
]

BAND_UNTEN = [
    (spargel, 0.09, 0.52, 0.19, 6),
    (erdbeere, 0.26, 0.30, 0.16, -8),
    (tomate, 0.42, 0.58, 0.18, 0),
    (pilz, 0.58, 0.30, 0.16, 0),
    (gurkenscheibe, 0.73, 0.60, 0.15, 0),
    (kraeuterzweig, 0.89, 0.42, 0.17, 14),
]


# Dichte Anordnung für den Schieferstil: zwei versetzte Reihen, die sich
# überlappen und an beiden Seiten über den Rand hinauslaufen. Das ergibt das
# Bild einer ausgebreiteten Auslage statt einer Reihe einzelner Symbole.
# Reihenfolge = Zeichenreihenfolge: hinten liegende Motive zuerst.
BAND_DICHT = [
    # hintere Reihe
    (brokkoli,      -0.02, 0.74, 0.26, -4),
    (paprika,        0.15, 0.80, 0.23, 6),
    (avocado,        0.33, 0.76, 0.24, -8),
    (zitrone,        0.50, 0.82, 0.20, 0),
    (brokkoli,       0.66, 0.75, 0.24, 5),
    (paprika,        0.84, 0.81, 0.22, -7),
    (avocado,        1.01, 0.74, 0.23, 10),
    # vordere Reihe, tiefer und etwas kleiner
    (kraeuterzweig,  0.04, 0.44, 0.19, -16),
    (tomate,         0.21, 0.38, 0.19, 0),
    (gurkenscheibe,  0.36, 0.42, 0.17, 0),
    (erdbeere,       0.48, 0.34, 0.16, -9),
    (spargel,        0.60, 0.46, 0.19, 8),
    (tomate,         0.74, 0.36, 0.18, 0),
    (heidelbeeren,   0.87, 0.40, 0.16, 0),
    (pilz,           0.97, 0.35, 0.16, 0),
]

# Schmalere Fassung für den Fuß der Rückseite.
BAND_DICHT_SCHMAL = [
    (paprika,        0.06, 0.66, 0.20, 6),
    (zitrone,        0.24, 0.70, 0.17, 0),
    (brokkoli,       0.42, 0.64, 0.21, -5),
    (avocado,        0.62, 0.68, 0.20, 8),
    (gurkenscheibe,  0.80, 0.66, 0.16, 0),
    (kraeuterzweig,  0.94, 0.60, 0.17, 12),
    (tomate,         0.14, 0.30, 0.16, 0),
    (erdbeere,       0.34, 0.28, 0.14, -8),
    (heidelbeeren,   0.53, 0.30, 0.14, 0),
    (spargel,        0.72, 0.32, 0.16, 6),
]


def schiefergrund(c, x, y, breite, hoehe):
    """Dunkler Grund mit leichter Abdunklung nach unten.

    Bewusst als Vektorverlauf und nicht als Bild: Ein Rasterhintergrund über
    einen ganzen Umschlag bräuchte für 300 dpi rund 10 Megapixel — sieben
    Megabyte je Umschlag, und darunter meldet KDP beim Hochladen eine zu
    niedrige Auflösung. Der Verlauf bleibt in jeder Größe scharf.
    """
    c.saveState()
    # Ohne gesetzten Beschneidungspfad füllt der Verlauf die ganze Seite.
    p = c.beginPath()
    p.rect(x, y, breite, hoehe)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y + hoehe, x, y,
                     [SCHIEFER["grund"], SCHIEFER["grund_tief"]],
                     [0.0, 1.0], extend=True)
    c.restoreState()


def komposition_zeichnen(c, motive, x, y, breite, hoehe, *, bezug=None):
    """Zeichnet eine Motivliste in den Rahmen (x, y, breite, hoehe).

    `bezug` ist die Breite, auf die sich die Größenangaben beziehen. Ohne
    Angabe ist das die Rahmenbreite. Läuft ein Band über den ganzen Umschlag,
    muss der Bezug eine einzelne Buchseite bleiben — sonst wächst jede Tomate
    mit der Rahmenbreite mit und wird doppelt so groß wie gedacht.
    """
    bezugsbreite = breite if bezug is None else bezug
    for zeichnen, ax, ay, agroesse, drehung in motive:
        c.saveState()
        c.translate(x + ax * breite, y + ay * hoehe)
        c.rotate(drehung)
        zeichnen(c, 0, 0, agroesse * bezugsbreite)
        c.restoreState()


def band_ueber_breite(motive, wiederholungen):
    """Reiht eine Komposition mehrfach nebeneinander.

    Für den durchlaufenden Streifen über Rückseite, Rücken und Vorderseite.
    Jede Wiederholung wird leicht versetzt und gespiegelt angeordnet, damit
    kein sichtbares Muster entsteht.
    """
    lang = []
    for i in range(wiederholungen):
        # Jede Wiederholung startet an einer anderen Stelle der Liste, läuft
        # abwechselnd rückwärts und kippt die Drehungen. Ohne das sieht man
        # dieselbe Kette mehrfach hintereinander — bei vier Durchgängen über
        # ein A4-Format fällt das sofort auf.
        gedreht = motive[i * 3 % len(motive):] + motive[:i * 3 % len(motive)]
        for k, (zeichnen, ax, ay, agroesse, drehung) in enumerate(gedreht):
            anteil = (1.0 - ax) if i % 2 else ax
            versatz = (0.04, -0.03, 0.015, -0.045)[i % 4]
            skala = (1.0, 0.93, 1.06, 0.97)[(i + k) % 4]
            lang.append((zeichnen, (i + anteil) / wiederholungen,
                         min(0.95, max(0.05, ay + versatz)),
                         agroesse * skala,
                         -drehung if i % 2 else drehung))
    return lang


