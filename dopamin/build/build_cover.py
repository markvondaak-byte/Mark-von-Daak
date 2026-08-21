#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für Band 4 (Die Dopamin-Lüge).

    python3 dopamin/build/build_cover.py

Der Innenteil muss vorher gebaut sein — die Rückenbreite ergibt sich aus der
Seitenzahl.

Warum dieser Band einen eigenen Umschlag bekommt und nicht den der Reihe:
Die Umschläge der Bände 1 bis 3 tragen eine Lebensmittelauslage und die
Leitfarbe Blattgrün. Beides gehört zum Stoffwechsel-Konzept und wäre hier
irreführend — ein Buch über einen Botenstoff, das aussieht wie ein
Ernährungsratgeber, wird im Vorschaubild dem falschen Regal zugeordnet.

Übernommen wird deshalb nur die **Geometrie**: Anschnitt, Rückenbreite,
Barcodefeld. Das sind KDP-Vorgaben und keine Gestaltungsfragen, und sie
stehen in buch/build/build_cover.py samt der Begründung, wie sie zustande
gekommen sind. Alles Sichtbare — Grund, Motiv, Schrift — ist hier eigen.

Zwei Motive, beide als Vektorgrafik gezeichnet:

* **Vorderseite: ein Kopf im Profil** mit sichtbarem Gehirn und leuchtenden
  Punkten an den Synapsen. Umriss, Gehirn und Kleinhirn liegen als
  Punktfolgen vor, aus denen _bezier_aus_punkten() glatte Kurven rechnet.
* **Rückseite: die Strukturformel des Dopamins** — ein Benzolring mit zwei
  Hydroxylgruppen und einer Aminoethyl-Seitenkette, also
  4-(2-Aminoethyl)benzol-1,2-diol.

Zusammen sagen sie, worum es im Buch geht: ein sehr kleines Molekül, dem man
nichts von Glück ansieht, und was es in einem Kopf anrichtet.

Liegt unter dopamin/cover/ ein Titelfoto, tritt es an die Stelle des Kopfes;
die Formel bleibt davon unberührt.
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM, BESCHNITT_MM,  # noqa: E402
                         BUCHDECKE_MM, HARDCOVER_MIN_SEITEN,
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN, WRAP_MM,
                         barcodefeld_freistellen, block_schreiben,
                         klappentext_laden, schriften_laden, seitenzahl,
                         titelbild_zeichnen,
                         umbrechen, vorschau, weissflaeche)

BAND = WURZEL / "dopamin"

# --- Farbwelt ----------------------------------------------------------------
# Tiefes Indigo statt des Schiefergraus der Reihe. Die Werte sind gegen den
# Grund auf Kontrast geprüft: TEXT liegt bei rund 14:1, TEXT_LEISE bei 5,4:1
# (Normalgröße, Mindestwert 4,5), AKZENT bei 6,8:1.
FARBEN = {
    "grund_oben": HexColor("#1B1A3A"),
    "grund_unten": HexColor("#0E0D22"),
    "text": HexColor("#F2F1F8"),
    "text_leise": HexColor("#A6A3C4"),
    "akzent": HexColor("#8F86E8"),
    "molekuel": HexColor("#3B3868"),
    "molekuel_hell": HexColor("#6E67B8"),

    # Der Kopf auf der Vorderseite. Kühle Struktur, ein warmer Ton für das
    # Signal — mehr Farben verträgt der Umschlag nicht, und die beiden
    # sagen zusammen genau das, worum es im Buch geht.
    "kopf_fuell": HexColor("#232149"),
    "kopf_linie": HexColor("#8C9BEF"),
    "hirn_fuell": HexColor("#3A3676"),
    "hirn_linie": HexColor("#8F86E8"),
    "synapse": HexColor("#F2A65A"),
}

VERLAUF_STUFEN = 220   # so fein, dass keine Bänder sichtbar bleiben

# Anteil der Vorderseitenhöhe, den ein Titelfoto einnimmt — von der Oberkante
# nach unten. Darunter beginnt der freie Grund mit Akzentlinie und Titel.
TITELBILD_BAND = 0.47

# Der gezeichnete Kopf: Höhe als Anteil der Vorderseitenhöhe, und auf welcher
# Höhe seine Unterkante steht. Die Akzentlinie liegt bei 0,395 — zwischen ihr
# und dem Halsansatz bleibt damit knapp ein Zentimeter Luft.
KOPF_ANTEIL = 0.50
KOPF_FUSS = 0.44

MARKENHINWEIS = (
    "Kein medizinischer Ratgeber. Dieses Buch ersetzt keine ärztliche oder "
    "psychotherapeutische Behandlung — bitte die Hinweise im Buch beachten. "
    "Alle genannten Marken sind Eigentum ihrer jeweiligen Inhaber."
)


# --- Grund -------------------------------------------------------------------
def verlauf(c, x, y, breite, hoehe, oben, unten, stufen=VERLAUF_STUFEN):
    """Senkrechter Verlauf aus vollflächigen Streifen.

    Bewusst kein reportlab-Shading: Das erzeugt ein Smooth-Shading-Objekt,
    und genau die lehnt die KDP-Prüfung ab. Gerasterte Streifen sind nach
    dem Flachrechnen ohnehin nicht zu unterscheiden — und die Vektorfassung
    lässt sich so auch ohne den Umweg über cover_flach.py ansehen.
    """
    schritt = hoehe / stufen
    for i in range(stufen):
        t = i / (stufen - 1)
        c.setFillColorRGB(
            oben.red + (unten.red - oben.red) * t,
            oben.green + (unten.green - oben.green) * t,
            oben.blue + (unten.blue - oben.blue) * t,
        )
        # Halber Streifen Überlappung, sonst stehen bei manchen Betrachtern
        # Haarlinien zwischen den Rechtecken.
        c.rect(x, y + hoehe - (i + 1) * schritt, breite, schritt * 1.5,
               stroke=0, fill=1)


# --- Strukturformel ----------------------------------------------------------
def _ecken(cx, cy, r):
    """Die sechs Ringecken, beginnend unten links, gegen den Uhrzeigersinn.

    Nummeriert wie in der Nomenklatur: C1 und C2 tragen die
    Hydroxylgruppen, C4 die Seitenkette. C4 liegt C1 gegenüber.
    """
    import math
    winkel = [210, 270, 330, 30, 90, 150]
    return [(cx + r * math.cos(math.radians(w)),
             cy + r * math.sin(math.radians(w))) for w in winkel]


def _strich(c, p, q, staerke):
    c.setLineWidth(staerke)
    c.line(p[0], p[1], q[0], q[1])


def _innenlinie(c, p, q, cx, cy, staerke, abstand):
    """Die zweite Linie einer Doppelbindung, nach innen versetzt."""
    import math
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = cx - mx, cy - my
    laenge = math.hypot(dx, dy) or 1
    dx, dy = dx / laenge * abstand, dy / laenge * abstand
    # Etwas kürzer als die Außenlinie, sonst berührt sie die Nachbarbindung.
    kx, ky = (q[0] - p[0]) * 0.16, (q[1] - p[1]) * 0.16
    _strich(c, (p[0] + dx + kx, p[1] + dy + ky),
            (q[0] + dx - kx, q[1] + dy - ky), staerke)


def molekuel(c, cx, cy, r, farbe, staerke, *, beschriftung=None,
             schriftgroesse=None):
    """Zeichnet die Strukturformel des Dopamins um (cx, cy).

    `r` ist der Ringradius; alles Weitere ist daraus abgeleitet, damit sich
    die Formel in einem Zug skalieren lässt.
    """
    import math

    c.saveState()
    c.setStrokeColor(farbe)
    c.setLineCap(1)
    c.setLineJoin(1)

    e = _ecken(cx, cy, r)
    for i in range(6):
        _strich(c, e[i], e[(i + 1) % 6], staerke)
    # Aromatischer Ring: jede zweite Bindung doppelt.
    for i in (0, 2, 4):
        _innenlinie(c, e[i], e[(i + 1) % 6], cx, cy, staerke, r * 0.17)

    bindung = r * 0.72

    def nach_aussen(punkt, winkel_grad, laenge=bindung):
        w = math.radians(winkel_grad)
        return (punkt[0] + laenge * math.cos(w),
                punkt[1] + laenge * math.sin(w))

    # Die beiden Hydroxylgruppen an C1 (unten links) und C2 (unten).
    oh1 = nach_aussen(e[0], 210)
    oh2 = nach_aussen(e[1], 270)
    _strich(c, e[0], oh1, staerke)
    _strich(c, e[1], oh2, staerke)

    # Die Aminoethyl-Seitenkette an C4 (oben rechts), im Zickzack.
    k1 = nach_aussen(e[3], 30)
    k2 = nach_aussen(k1, -30)
    k3 = nach_aussen(k2, 30)
    _strich(c, e[3], k1, staerke)
    _strich(c, k1, k2, staerke)
    _strich(c, k2, k3, staerke)

    if beschriftung:
        c.setFillColor(beschriftung)
        groesse = schriftgroesse or r * 0.42
        c.setFont("Sans-Bold", groesse)
        # Die Beschriftungen sitzen an den Kettenenden und werden so
        # ausgerichtet, dass die Bindung auf den Text zuläuft.
        c.drawRightString(oh1[0] - groesse * 0.18,
                          oh1[1] - groesse * 0.36, "HO")
        c.drawCentredString(oh2[0], oh2[1] - groesse * 1.05, "OH")
        c.drawString(k3[0] + groesse * 0.18, k3[1] - groesse * 0.36, "NH₂")

    c.restoreState()


# --- Kopf im Profil ----------------------------------------------------------
# Umriss, Gehirn und Kleinhirn liegen als Punktfolgen in einem Einheitsraster:
# x von 0 bis 1 über die Breite der Figur, y von 0 (Halsansatz unten) bis 1
# (Scheitel). Skaliert wird erst beim Zeichnen.
#
# Warum Punktfolgen und keine von Hand gesetzten Bezierkurven: Ein Profil
# lebt von wenigen Stellen — Nasenwurzel, Nasenspitze, Lippen, Kinn. Als
# Koordinaten kann man sie lesen und um zwei Hundertstel verschieben; als
# Kontrollpunkte einer Bezierkette könnte das niemand mehr nachvollziehen.
# _bezier_aus_punkten() rechnet die Folge in Bezierstücke um. Ein doppelt
# aufgeführter Punkt erzeugt dort eine Ecke, wo eine hingehört — an der
# Nasenspitze und an der unteren Schnittkante des Halses.
# Die Höhen der Gesichtspunkte folgen den üblichen Proportionen: Von der
# Kinnunterkante (0,296) bis zum Scheitel (1,000) liegen Mundspalt bei einem
# Siebtel, Nasenbasis bei einem Viertel, Nasenwurzel bei knapp der Hälfte und
# der Haaransatz bei knapp drei Vierteln dieser Strecke.
#
# Die x-Ausschläge an Lippen und Kinn sind bewusst klein (rund 0,016). Ein
# erster Entwurf hatte dort 0,03 auf engem Raum — daraus wurde beim Glätten
# kein Mund, sondern eine Zickzacklinie.
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
    (0.786, 0.428),                      # Mund — eine flache Mulde, keine
    (0.792, 0.392),                      # zwei Lippen: Auf dieser Größe wird
    (0.774, 0.356),                      # Kinnfalte     aus jedem Lippenpaar
    (0.790, 0.318),                      # Kinn          eine Zickzacklinie
    (0.748, 0.296),                      # Kinnunterkante
    (0.672, 0.280),                      # Kieferunterkante
    (0.620, 0.236),                      # Kieferwinkel
    (0.610, 0.150),                      # Hals vorn
    (0.616, 0.060),
    # Der Hals läuft unter die Unterkante des Rasters und wird dort
    # abgeschnitten — siehe kopf_zeichnen(). Eine gezeichnete Schnittkante
    # wurde beim Glätten wellig, weil die Kurve an den Ecken ausschert.
    (0.620, -0.090),
    (0.258, -0.090),
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

# Kleinhirn: unten hinten, an der Unterkante des Großhirns anliegend, und
# deutlich hinter dem Ohr. Im ersten Entwurf stand es frei darunter und
# überschnitt sich mit dem Ohr — zwei gleich große Ovale nebeneinander, die
# beide nach Ohr aussahen.
KOPF_KLEINHIRN = [
    (0.268, 0.678),
    (0.348, 0.666),
    (0.386, 0.628),
    (0.362, 0.588),
    (0.292, 0.580),
    (0.248, 0.616),
]

# Leuchtpunkte im Gehirn, im selben Raster. Von Hand gesetzt und nicht
# gewürfelt: Ein Zufallsmuster trifft regelmäßig die Kontur und sieht dann
# nach Fehler aus. Die dritte Zahl ist der Radius als Anteil der Figurbreite.
KOPF_SYNAPSEN = [
    (0.360, 0.845, 0.019), (0.440, 0.885, 0.012), (0.512, 0.860, 0.023),
    (0.582, 0.880, 0.011), (0.618, 0.806, 0.017), (0.478, 0.796, 0.015),
    (0.392, 0.756, 0.013), (0.552, 0.742, 0.020), (0.640, 0.752, 0.010),
    (0.306, 0.788, 0.011), (0.462, 0.702, 0.014), (0.664, 0.826, 0.009),
]


def _bezier_aus_punkten(punkte, geschlossen=True, spannung=6.0):
    """Legt eine glatte Kurve durch die Punkte (Catmull-Rom als Bezier).

    Gibt Stücke (p0, c1, c2, p1) zurück, wie reportlab sie für curveTo
    braucht. `spannung` steuert, wie weit die Kontrollpunkte ausgreifen —
    6,0 ist der klassische Wert; größere Zahlen ziehen die Kurve enger an
    die Punkte und machen sie kantiger.
    """
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


def _figurpfad(c, punkte, x, y, breite, hoehe, geschlossen=True,
               spannung=6.0):
    """Baut aus einer Punktfolge im Einheitsraster einen reportlab-Pfad."""
    def ab(p):
        return (x + p[0] * breite, y + p[1] * hoehe)

    pfad = c.beginPath()
    stuecke = _bezier_aus_punkten(punkte, geschlossen, spannung)
    pfad.moveTo(*ab(stuecke[0][0]))
    for p0, c1, c2, p1 in stuecke:
        pfad.curveTo(*ab(c1), *ab(c2), *ab(p1))
    if geschlossen:
        pfad.close()
    return pfad


def _mischen(a, b, t):
    """Farbe zwischen a und b; t = 0 ergibt a, t = 1 ergibt b."""
    return Color(a.red + (b.red - a.red) * t,
                 a.green + (b.green - a.green) * t,
                 a.blue + (b.blue - a.blue) * t)


def _glimmpunkt(c, x, y, r, kern, grund, ringe=9):
    """Ein leuchtender Punkt mit weichem Hof, aus vollflächigen Kreisen.

    Bewusst ohne Transparenz und ohne Radialverlauf, wie schon der
    Hintergrund: Die KDP-Druckfassung darf beides nicht enthalten. Von außen
    nach innen gezeichnet, damit der helle Kern zuletzt obenauf liegt.
    """
    for i in range(ringe, 0, -1):
        t = i / ringe
        c.setFillColor(_mischen(kern, grund, t ** 0.7))
        c.circle(x, y, r * (0.35 + 0.65 * t), stroke=0, fill=1)


def kopf_zeichnen(c, x, y, breite, hoehe):
    """Zeichnet Kopf, Gehirn und Synapsen in den Rahmen (x, y, breite, hoehe).

    Der Rahmen ist das Einheitsraster der Punktfolgen oben. Das Seiten-
    verhältnis ist darin nicht erzwungen — wer die Figur verzerren will,
    kann es, und wer sie unverzerrt will, gibt breite und hoehe im
    Verhältnis der Punktfolgen an. kopf_masse() rechnet das aus.
    """
    c.saveState()
    c.setLineJoin(1)
    c.setLineCap(1)

    # Der Hals läuft unter das Raster hinaus und wird hier abgeschnitten.
    # Damit ist die untere Kante gerade — von der Beschneidung erzeugt und
    # nicht von einer Kurve, die dort entlanglaufen müsste.
    rahmen = c.beginPath()
    rahmen.rect(x, y, breite, hoehe)
    c.clipPath(rahmen, stroke=0, fill=0)

    # Höhere Spannung als der Vorgabewert: An Lippen und Kinn wechselt die
    # Richtung auf engem Raum, und mit 6,0 schoss die Kurve dort über die
    # Punkte hinaus — aus dem Mund wurde eine Zickzacklinie.
    umriss = _figurpfad(c, KOPF_UMRISS, x, y, breite, hoehe, spannung=7.5)

    # Kopf als eigene Fläche, eine Spur heller als der Grund. Damit wirkt er
    # als Volumen und nicht als Loch, und die Leuchtpunkte darin haben einen
    # definierten Grund, in den sie ausblenden können.
    c.setFillColor(FARBEN["kopf_fuell"])
    c.drawPath(umriss, stroke=0, fill=1)

    # Alles Weitere liegt im Kopf und wird daran beschnitten. Ohne das ragen
    # die Gehirnwindungen an der Stirn heraus.
    c.saveState()
    c.clipPath(umriss, stroke=0, fill=0)

    hirn = _figurpfad(c, KOPF_HIRN, x, y, breite, hoehe)
    c.setFillColor(FARBEN["hirn_fuell"])
    c.drawPath(hirn, stroke=0, fill=1)

    # Hirnstamm vor dem Kleinhirn, damit dessen Fläche ihn oben überdeckt.
    # Kurz gehalten und im Kleinhirn endend: Ein längerer Strich stand als
    # Stiel frei im Schädel und sah nach Versehen aus.
    c.setStrokeColor(FARBEN["hirn_fuell"])
    c.setLineWidth(breite * 0.032)
    c.line(x + 0.376 * breite, y + 0.676 * hoehe,
           x + 0.352 * breite, y + 0.600 * hoehe)

    klein = _figurpfad(c, KOPF_KLEINHIRN, x, y, breite, hoehe)
    c.setFillColor(FARBEN["hirn_fuell"])
    c.drawPath(klein, stroke=0, fill=1)

    _windungen(c, x, y, breite, hoehe, hirn)

    # Umrisse von Gehirn und Kleinhirn zuletzt, damit sie über den Windungen
    # liegen.
    c.setStrokeColor(FARBEN["hirn_linie"])
    c.setLineWidth(breite * 0.011)
    c.drawPath(hirn, stroke=1, fill=0)
    c.drawPath(klein, stroke=1, fill=0)

    for px, py, pr in KOPF_SYNAPSEN:
        _glimmpunkt(c, x + px * breite, y + py * hoehe, pr * breite,
                    FARBEN["synapse"], FARBEN["hirn_fuell"])

    c.restoreState()

    # Die Profillinie zum Schluss und über allem — sie ist die Kante, an der
    # die Figur erkannt wird.
    c.setStrokeColor(FARBEN["kopf_linie"])
    c.setLineWidth(breite * 0.014)
    c.drawPath(umriss, stroke=1, fill=0)

    c.restoreState()


def _windungen(c, x, y, breite, hoehe, hirnpfad, anzahl=8):
    """Die Gehirnwindungen: flache Wellenlinien, am Gehirn beschnitten.

    Gezeichnet wird über die volle Breite des Kopfes; sichtbar bleibt nur,
    was innerhalb des Gehirnumrisses liegt. Das ist erheblich einfacher, als
    jede Linie einzeln an die Kontur anzupassen — und sieht besser aus, weil
    die Linien dadurch an der Kante sauber auslaufen.
    """
    import math

    c.saveState()
    c.clipPath(hirnpfad, stroke=0, fill=0)
    c.setStrokeColor(FARBEN["hirn_linie"])
    c.setLineWidth(breite * 0.009)

    oben, unten = 0.925, 0.655
    for i in range(anzahl):
        basis = oben - (oben - unten) * (i + 0.5) / anzahl
        pfad = c.beginPath()
        schritte = 48
        for s in range(schritte + 1):
            u = 0.21 + (0.50 * s / schritte)
            # Zwei überlagerte Wellen, damit kein Sinusmuster entsteht. Die
            # Ausschläge bleiben kleiner als der Zeilenabstand, sonst laufen
            # benachbarte Windungen ineinander.
            v = (basis
                 + 0.017 * math.sin(u * 26 + i * 1.7)
                 + 0.008 * math.sin(u * 41 + i * 0.6))
            px, py = x + u * breite, y + v * hoehe
            if s == 0:
                pfad.moveTo(px, py)
            else:
                pfad.lineTo(px, py)
        c.drawPath(pfad, stroke=1, fill=0)
    c.restoreState()


def kopf_masse(hoehe):
    """Die Breite, die die Figur bei gegebener Höhe unverzerrt braucht.

    Die Punktfolgen laufen in x von 0,150 bis 0,888 und in y von 0 bis 1 —
    die Figur ist also deutlich schmaler als ihr Raster. Ohne diese Rechnung
    steht sie nicht dort, wo man sie hingesetzt hat.
    """
    return hoehe * (KOPF_RASTER_RECHTS - KOPF_RASTER_LINKS)


KOPF_RASTER_LINKS = min(p[0] for p in KOPF_UMRISS)
KOPF_RASTER_RECHTS = max(p[0] for p in KOPF_UMRISS)


# --- Titelfoto ---------------------------------------------------------------
def titelbild_suchen():
    """Sucht ein Titelfoto — **nur** im Umschlagverzeichnis dieses Bandes.

    Bewusst ohne den Rückfall auf buch/cover/, den die Bände 1 bis 3 haben:
    Dort liegt die Lebensmittelauslage der Stoffwechsel-Reihe. Auf diesem
    Umschlag wäre sie nicht nur unpassend, sondern irreführend — und sie käme
    ohne jede Warnung, weil der Rückfall stillschweigend greift.
    """
    for endung in (".jpg", ".jpeg", ".png", ".webp"):
        pfad = BAND / "cover" / f"titelbild{endung}"
        if pfad.exists():
            return pfad
    return None


def titelbild_sollmasse(cfg, dpi=300):
    """Wie groß das Titelfoto mindestens sein muss.

    Gerechnet aus TITELBILD_BAND und nicht fest eingetragen: Wer das Band
    höher zieht, bekommt die neue Mindestgröße automatisch gemeldet.
    """
    sf = cfg["seitenformat"]
    breite_mm = sf["breite_mm"] + BESCHNITT_MM
    hoehe_mm = sf["hoehe_mm"] * TITELBILD_BAND + BESCHNITT_MM
    je_mm = dpi / 25.4
    return round(breite_mm * je_mm), round(hoehe_mm * je_mm)


def titelbild_melden(cfg, pfad):
    soll_b, soll_h = titelbild_sollmasse(cfg)
    if not pfad:
        print("Titelbild: keins — es wird der gezeichnete Kopf verwendet. "
              f"Für ein Foto: dopamin/cover/titelbild.png ablegen "
              f"(mindestens {soll_b} x {soll_h} px).")
        return
    from PIL import Image
    with Image.open(pfad) as bild:
        breite, hoehe = bild.size
    print(f"Titelbild: {Path(pfad).relative_to(WURZEL)} "
          f"({breite} x {hoehe} px, nötig {soll_b} x {soll_h})")
    if breite < soll_b or hoehe < soll_h:
        band = soll_b / soll_h
        nutz_b = round(hoehe * band) if breite / hoehe > band else breite
        print(f"  ACHTUNG: {nutz_b / (soll_b / 300):.0f} dpi statt 300 — wird "
              f"auf {soll_b} px hochgerechnet. Das erfindet keine Schärfe.")


def grundfarbe_bei(y_abs, gesamt_h):
    """Die Farbe des Verlaufs auf einer bestimmten Höhe.

    Gebraucht wird sie für die Unterkante des Titelfotos: Es blendet in den
    Grund aus, und der ist an dieser Stelle weder grund_oben noch
    grund_unten, sondern der Zwischenwert. Mit einem der beiden Endwerte
    stünde dort wieder eine sichtbare Kante — nur eine weichere.
    """
    t = max(0.0, min(1.0, (gesamt_h - y_abs) / gesamt_h))
    o, u = FARBEN["grund_oben"], FARBEN["grund_unten"]
    return Color(o.red + (u.red - o.red) * t,
                 o.green + (u.green - o.green) * t,
                 o.blue + (u.blue - o.blue) * t)


# --- Vorderseite -------------------------------------------------------------
def einzeilig_einpassen(c, text, schrift, breite, *, maximal, minimal):
    """Größte Schriftgröße, bei der `text` in **eine** Zeile passt."""
    groesse = float(maximal)
    while groesse > minimal and c.stringWidth(text, schrift, groesse) > breite:
        groesse -= 0.5
    return groesse


def vorderseite(c, x, y, breite, hoehe, cfg, titelbild=None,
                ueberstand=0, ausblendfarbe=None):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    if titelbild:
        # Das Foto füllt das obere Band bis in den Anschnitt — oben und
        # rechts, nicht links: Links grenzt die Vorderseite an den Rücken,
        # und dort darf nichts überstehen.
        band_h = hoehe * TITELBILD_BAND
        titelbild_zeichnen(c, titelbild, x, y + hoehe - band_h,
                           breite + ueberstand, band_h + ueberstand,
                           ausblenden=ausblendfarbe)
    else:
        # Ohne Foto der gezeichnete Kopf. Die Figur steht als Ganzes im
        # oberen Bereich und wird nicht angeschnitten — ein halber Kopf
        # liest sich im Vorschaubild wie ein Fehler. Die Breite kommt aus
        # der Höhe, damit sie bei einer anderen Trimmgröße nicht verzerrt.
        figur_h = hoehe * KOPF_ANTEIL
        figur_b = kopf_masse(figur_h)
        kopf_zeichnen(c,
                      x + (breite - figur_b) / 2 - KOPF_RASTER_LINKS * figur_h,
                      y + hoehe * KOPF_FUSS, figur_h, figur_h)

    # Akzentlinie als Trenner zwischen Motiv und Titel.
    c.setStrokeColor(FARBEN["akzent"])
    c.setLineWidth(1.4)
    c.line(x + rand, y + hoehe * 0.395, x + rand + textbreite * 0.30,
           y + hoehe * 0.395)

    # Titel — einzeilig. Nicht groesse_einpassen(): Das bricht um, statt zu
    # verkleinern, und liefert deshalb bei jeder Größe ein Ergebnis. Der
    # Titel stünde dann zweizeilig da, mit einer ersten Zeile aus einem
    # einzigen Artikel — im Amazon-Vorschaubild sieht das nach Satzfehler aus.
    groesse = einzeilig_einpassen(c, cfg["titel"], "Sans-Bold", textbreite,
                                  maximal=34, minimal=18)
    cursor = y + hoehe * 0.335
    c.setFillColor(FARBEN["text"])
    c.setFont("Sans-Bold", groesse)
    c.drawString(x + rand, cursor, cfg["titel"])
    cursor -= groesse * 1.32

    # Untertitel
    cursor = block_schreiben(c, cfg["untertitel"], x + rand, cursor,
                             textbreite, "Serif", 12.5, 17,
                             FARBEN["text_leise"])

    # Autor unten, mit Linie darüber
    c.setStrokeColor(FARBEN["text_leise"])
    c.setLineWidth(0.6)
    c.line(x + rand, y + hoehe * 0.115, x + breite - rand, y + hoehe * 0.115)
    c.setFillColor(FARBEN["text"])
    c.setFont("Sans-Bold", 13)
    c.drawString(x + rand, y + hoehe * 0.078, cfg["autor"])


# --- Rücken ------------------------------------------------------------------
def ruecken(c, x, y, breite, hoehe, cfg, mit_text):
    if not mit_text:
        return
    groesse = min(11, breite * 0.5)
    c.saveState()
    c.translate(x + breite / 2, y + hoehe / 2)
    c.rotate(-90)
    c.setFillColor(FARBEN["text"])
    c.setFont("Sans-Bold", groesse)
    c.drawCentredString(0, -groesse * 0.35,
                        f"{cfg['titel']}   ·   {cfg['autor']}")
    c.restoreState()


# --- Rückseite ---------------------------------------------------------------
def _hoehe_schaetzen(c, kopf, absaetze, punkte, textbreite, g):
    g_kopf, g_text, g_punkt = g
    hoehe = 0.0
    if kopf.get("schlagzeile"):
        hoehe += len(umbrechen(c, kopf["schlagzeile"], "Sans-Bold", g_kopf,
                               textbreite)) * g_kopf * 1.28 + 16
    for absatz in absaetze:
        hoehe += len(umbrechen(c, absatz, "Serif", g_text,
                               textbreite)) * g_text * 1.42 + 9
    for punkt in punkte:
        hoehe += len(umbrechen(c, punkt, "Serif", g_punkt,
                               textbreite - 14)) * g_punkt * 1.36 + 4
    return hoehe + 10


def rueckseite(c, x, y, breite, hoehe, cfg, kopf, absaetze, punkte,
               *, hardcover=False):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    # Kleines Motiv als Wiedererkennung, oben rechts und weit weg vom Text.
    molekuel(c, x + breite * 0.78, y + hoehe * 0.895, breite * 0.10,
             FARBEN["molekuel"], breite * 0.008)

    barcodefeld_freistellen(c, x, y, breite, hardcover=hardcover)

    hinweis_zeilen = len(umbrechen(c, MARKENHINWEIS, "Serif", 7, textbreite))
    _, fy, _, fh = weissflaeche(x, y, breite, hardcover=hardcover)
    hinweis_y = fy + fh + BARCODE_LUFT_MM * mm + hinweis_zeilen * 9
    oben = y + hoehe * 0.815
    platz = oben - (hinweis_y + 16)

    # Der Klappentext sucht sich seine Größe selbst — 5 x 8 Zoll ist eine
    # kleine Rückseite, und der Text soll weder überlaufen noch verloren
    # wirken.
    faktor = 1.0
    basis = (13.0, 9.6, 9.2)

    def passt(f):
        return _hoehe_schaetzen(c, kopf, absaetze, punkte, textbreite,
                                [g * f for g in basis]) <= platz

    if passt(faktor):
        while faktor < 1.20 and passt(faktor + 0.02):
            faktor += 0.02
    else:
        while faktor > 0.70 and not passt(faktor):
            faktor -= 0.02
    g_kopf, g_text, g_punkt = (g * faktor for g in basis)
    if abs(faktor - 1.0) > 0.001:
        wort = "vergrößert" if faktor > 1 else "verkleinert"
        print(f"  Rückseitentext auf {faktor:.0%} {wort} "
              f"(Fließtext {g_text:.1f} pt)")

    rest = platz - _hoehe_schaetzen(c, kopf, absaetze, punkte, textbreite,
                                    (g_kopf, g_text, g_punkt))
    cursor = oben - max(0.0, rest) / 2

    if kopf.get("schlagzeile"):
        cursor = block_schreiben(c, kopf["schlagzeile"], x + rand, cursor,
                                 textbreite, "Sans-Bold", g_kopf,
                                 g_kopf * 1.28, FARBEN["akzent"])
        cursor -= 13

    for absatz in absaetze:
        cursor = block_schreiben(c, absatz, x + rand, cursor, textbreite,
                                 "Serif", g_text, g_text * 1.42,
                                 FARBEN["text"])
        cursor -= 6

    cursor -= 3
    for punkt in punkte:
        c.setFillColor(FARBEN["akzent"])
        c.setFont("Sans-Bold", g_punkt)
        c.drawString(x + rand, cursor, "•")
        c.setFillColor(FARBEN["text"])
        for zeile in umbrechen(c, punkt, "Serif", g_punkt, textbreite - 14):
            c.setFont("Serif", g_punkt)
            c.drawString(x + rand + 14, cursor, zeile)
            cursor -= g_punkt * 1.36
        cursor -= 3

    if cursor < hinweis_y + 10:
        print("  ACHTUNG: Rückseitentext reicht bis an den Pflichthinweis — "
              "Klappentext kürzen.")

    # Der Pflichthinweis wird von unten gesetzt: Der Block wächst nach unten,
    # also bestimmt die letzte Zeile die Position, nicht die erste. Sonst
    # läuft er durch das Barcodefeld — siehe buch/README.md.
    unterlaenge = 7 * 0.25
    start = fy + fh + BARCODE_LUFT_MM * mm + unterlaenge + (hinweis_zeilen - 1) * 9
    block_schreiben(c, MARKENHINWEIS, x + rand, start, textbreite,
                    "Serif", 7, 9, FARBEN["text_leise"])


# --- Zusammenbau -------------------------------------------------------------
def cover_bauen(cfg, seiten, klappentext_pfad, ziel, *, hardcover=False):
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    if hardcover:
        anschnitt = WRAP_MM * mm
        ruecken_b = (seiten * RUECKEN_PRO_SEITE_MM + BUCHDECKE_MM) * mm
    else:
        anschnitt = BESCHNITT_MM * mm
        ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")

    verlauf(c, 0, 0, gesamt_b, gesamt_h,
            FARBEN["grund_oben"], FARBEN["grund_unten"])

    kopf, absaetze, punkte = klappentext_laden(klappentext_pfad)
    titelbild = titelbild_suchen()
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    # Die Farbe, in die das Foto ausblendet, wird an seiner Unterkante
    # abgegriffen — siehe grundfarbe_bei().
    band_unterkante = anschnitt + trim_h * (1 - TITELBILD_BAND)

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte, hardcover=hardcover)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_ruecken_text)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg, titelbild, ueberstand=anschnitt,
                ausblendfarbe=grundfarbe_bei(band_unterkante, gesamt_h))

    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm,
            "ruecken_text": mit_ruecken_text,
            "titelbild": titelbild}


def main():
    cfg = yaml.safe_load((BAND / "dopamin.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(BAND / "out" / f"{cfg['slug']}.pdf")
    klappentext = BAND / "cover" / "klappentext.md"

    # Nur Taschenbuch. KDP führt 5 x 8 Zoll ausschließlich als Taschenbuch;
    # für Hardcover gibt es 5,5x8,5 · 6x9 · 6,14x9,21 · 7x10 · 8,25x11 Zoll
    # und sonst nichts. Ein Hardcover-Umschlag in diesem Maß würde beim
    # Hochladen mit der Meldung zur erwarteten Covergröße abgelehnt — Band 3
    # ist genau darüber gestolpert, siehe buch/README.md. Wer den Band
    # gebunden herausbringen will, muss zuerst die Trimmgröße wechseln und
    # den Innenteil neu bauen.
    for hardcover in (False,):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue

        ziel = BAND / "out" / f"{name}.pdf"
        masse = cover_bauen(cfg, seiten, klappentext, ziel,
                            hardcover=hardcover)
        png = vorschau(ziel, BAND / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        rand = WRAP_MM if hardcover else BESCHNITT_MM
        randname = "Umschlagrand um die Buchdecke" if hardcover else "Anschnitt"
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {rand} mm {randname}")
        titelbild_melden(cfg, masse["titelbild"])
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
