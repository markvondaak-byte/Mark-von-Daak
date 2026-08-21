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

Das Motiv ist die Strukturformel des Dopamins, als Vektorgrafik gezeichnet:
ein Benzolring mit zwei Hydroxylgruppen und einer Aminoethyl-Seitenkette,
also 4-(2-Aminoethyl)benzol-1,2-diol. Sie ist das einzige Bild, das dieses
Buch braucht, und sie ist zugleich das Argument des Buches: ein sehr kleines
Molekül, dem man nichts von Glück ansieht.
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM, BESCHNITT_MM,  # noqa: E402
                         BUCHDECKE_MM, HARDCOVER_MIN_SEITEN,
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN, WRAP_MM,
                         barcodefeld_freistellen, block_schreiben,
                         klappentext_laden, schriften_laden, seitenzahl,
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
}

VERLAUF_STUFEN = 220   # so fein, dass keine Bänder sichtbar bleiben

# Ausdehnung der Strukturformel, gemessen in Ringradien — aus der Geometrie
# in molekuel() ausgerechnet, nicht geschätzt. Links reicht sie 2,4 Radien
# über die Ringmitte hinaus (Bindung plus „HO"), rechts 3,9 (Kette plus
# „NH2"), nach oben 1,0 und nach unten 2,2. Aus der Asymmetrie folgt der
# Versatz: Die Ringmitte muss um 0,75 Radien nach links, damit die Formel
# als Ganzes mittig steht.
MOLEKUEL_BREITE = 6.3
MOLEKUEL_HOEHE = 3.2
MOLEKUEL_VERSATZ = 0.75

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


# --- Vorderseite -------------------------------------------------------------
def einzeilig_einpassen(c, text, schrift, breite, *, maximal, minimal):
    """Größte Schriftgröße, bei der `text` in **eine** Zeile passt."""
    groesse = float(maximal)
    while groesse > minimal and c.stringWidth(text, schrift, groesse) > breite:
        groesse -= 0.5
    return groesse


def vorderseite(c, x, y, breite, hoehe, cfg):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    # Das Motiv steht als Ganzes im oberen Drittel — nicht angeschnitten.
    # Eine halbe Strukturformel liest sich im Vorschaubild wie ein Fehler.
    # `r` und die Position kommen aus MOLEKUEL_BREITE/MOLEKUEL_HOEHE, damit
    # die Formel bei einer anderen Trimmgröße nicht in den Titel läuft.
    r = textbreite / MOLEKUEL_BREITE
    molekuel(c, x + breite / 2 - MOLEKUEL_VERSATZ * r, y + hoehe * 0.735, r,
             FARBEN["molekuel_hell"], r * 0.075,
             beschriftung=FARBEN["molekuel_hell"], schriftgroesse=r * 0.40)

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
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte, hardcover=hardcover)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_ruecken_text)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg)

    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm,
            "ruecken_text": mit_ruecken_text}


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
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
