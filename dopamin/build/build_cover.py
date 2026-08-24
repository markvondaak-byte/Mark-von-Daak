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

Zwei Motive:

* **Vorderseite: ein Kopf im Profil** mit Nervennetz und leuchtenden
  Synapsen. Das Motiv wird in titelbild.py als Bild **gerendert**, nicht als
  Vektorgrafik gezeichnet — dort steht auch, warum.
* **Rückseite: die Strukturformel des Dopamins** — ein Benzolring mit zwei
  Hydroxylgruppen und einer Aminoethyl-Seitenkette, also
  4-(2-Aminoethyl)benzol-1,2-diol, als Vektorgrafik.

Zusammen sagen sie, worum es im Buch geht: ein sehr kleines Molekül, dem man
nichts von Glück ansieht, und was es in einem Kopf anrichtet.

Liegt unter dopamin/cover/ ein eigenes Titelfoto, tritt es an die Stelle des
gerenderten Motivs; die Formel bleibt davon unberührt.
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))

from build_cover import (BARCODE_LUFT_MM,  # noqa: E402
                         BESCHNITT_MM,
                         BUCHDECKE_MM, HARDCOVER_MIN_SEITEN,
                         RUECKEN_PRO_SEITE_MM, RUECKENTEXT_AB_SEITEN, WRAP_MM,
                         block_schreiben,
                         klappentext_laden, schriften_laden, seitenzahl,
                         titelbild_zeichnen, _unterkante_ausblenden,
                         umbrechen, vorschau, weissflaeche)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import titelbild  # noqa: E402

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

# Anteil der Vorderseitenhöhe, den ein Titelfoto einnimmt — von der Oberkante
# nach unten. Darunter beginnt der freie Grund mit Akzentlinie und Titel.
TITELBILD_BAND = 0.47

# Auflösung, in der das Motiv gerechnet wird. KDP verlangt 300 dpi für
# Umschläge; mehr kostet nur Bauzeit und Dateigröße.
BILD_DPI = 300

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


def titelbild_sollmasse(cfg, dpi=300, *, hardcover=False):
    """Wie groß das Titelfoto mindestens sein muss.

    Gerechnet aus TITELBILD_BAND und nicht fest eingetragen: Wer das Band
    höher zieht, bekommt die neue Mindestgröße automatisch gemeldet. Das
    Hardcover braucht mehr — größere Trimmgröße und 18 mm Umschlagrand
    statt 3,175 mm Anschnitt.
    """
    sf = cfg["hardcover_seitenformat"] if hardcover else cfg["seitenformat"]
    rand = WRAP_MM if hardcover else BESCHNITT_MM
    breite_mm = sf["breite_mm"] + rand
    hoehe_mm = sf["hoehe_mm"] * TITELBILD_BAND + rand
    je_mm = dpi / 25.4
    return round(breite_mm * je_mm), round(hoehe_mm * je_mm)


def titelbild_melden(cfg, pfad, *, hardcover=False):
    soll_b, soll_h = titelbild_sollmasse(cfg, hardcover=hardcover)
    if not pfad:
        print("Titelbild: keins — es wird das Motiv aus titelbild.py "
              f"gerechnet. Für ein eigenes Foto: dopamin/cover/titelbild.png "
              f"ablegen (mindestens {soll_b} x {soll_h} px).")
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


def untertitel_einpassen(c, text, schrift, breite, *, maximal, minimal,
                         zeilen_max=2):
    """Größte Schriftgröße, bei der der Untertitel sauber umbricht.

    Sauber heißt zweierlei: höchstens `zeilen_max` Zeilen, und keine Zeile,
    die mit einem Gedankenstrich anfängt. Der Untertitel dieses Bandes hat
    seinen Strich in der Mitte, und rutscht der an einen Zeilenanfang, sieht
    das im Amazon-Vorschaubild nach Satzfehler aus.

    Gerechnet statt eingetragen, weil der Wert von zwei Dingen abhängt, die
    sich beide ändern können: von der Seitenbreite — der Band stand einmal
    auf 5 x 8 Zoll, dort waren 14 pt die Grenze, auf 6 x 9 Zoll sind es
    17 — und vom Wortlaut des Untertitels. Ein fester Wert wäre nach der
    ersten Änderung an einem von beiden still falsch.
    """
    groesse = float(maximal)
    while groesse > minimal:
        zeilen = umbrechen(c, text, schrift, groesse, breite)
        if len(zeilen) <= zeilen_max and not any(z.startswith("—")
                                                 for z in zeilen):
            break
        groesse -= 0.5
    return groesse


def vorderseite(c, x, y, breite, hoehe, cfg, foto=None,
                ueberstand=0, ausblendfarbe=None):
    rand = breite * 0.11
    textbreite = breite - 2 * rand

    # Das Motiv füllt das obere Band bis in den Anschnitt — oben und rechts,
    # nicht links: Links grenzt die Vorderseite an den Rücken, und dort darf
    # nichts überstehen.
    band_h = hoehe * TITELBILD_BAND
    band = (x, y + hoehe - band_h, breite + ueberstand, band_h + ueberstand)

    if foto:
        titelbild_zeichnen(c, foto, *band, ausblenden=ausblendfarbe)
    else:
        # Ohne eigenes Foto wird das Motiv gerechnet — in genau der
        # Pixelgröße, die das Band bei 300 dpi braucht. Es geht denselben
        # Weg wie ein Foto, einschließlich der Ausblendung nach unten.
        from reportlab.lib.utils import ImageReader
        bild = titelbild.rendern(round(band[2] / 72 * BILD_DPI),
                                 round(band[3] / 72 * BILD_DPI))
        if ausblendfarbe:
            bild = _unterkante_ausblenden(bild, ausblendfarbe)
        c.drawImage(ImageReader(bild), *band,
                    preserveAspectRatio=False, mask=None)

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

    # Untertitel, so groß wie er zweizeilig sauber umbricht — siehe dort.
    unter = untertitel_einpassen(c, cfg["untertitel"], "Serif", textbreite,
                                 maximal=20, minimal=11)
    cursor = block_schreiben(c, cfg["untertitel"], x + rand, cursor,
                             textbreite, "Serif", unter, unter * 1.36,
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
    #
    # Der Mittelpunkt sitzt bei 0,70 und nicht weiter rechts, weil die
    # Formel nicht mittig um ihn steht: Die Seitenkette ragt 2,74 Radien
    # nach rechts, also 0,274 Seitenbreiten. Bei 0,78 lief ihr Ende über
    # die Trimmkante hinaus und wurde vom Rücken abgeschnitten.
    molekuel(c, x + breite * 0.70, y + hoehe * 0.895, breite * 0.10,
             FARBEN["molekuel"], breite * 0.008)

    # Keine eigene Weißfläche unter dem Barcodefeld — auf keiner Bindeart.
    #
    # KDP druckt den Barcode nach eigener Angabe „in a 2 x 1,2 inch white
    # box", bringt das Weiß also mit. Ein zweites weißes Rechteck darunter
    # zeigt sich nur dann, wenn es größer ist als KDPs Box, und steht dann
    # als weißer Rand auf dem dunklen Grund. Beim Hardcover war genau das in
    # der Vorschau zu sehen; die Bände 1 bis 3 behalten es beim Taschenbuch
    # als Rückversicherung, dieser Band nicht — siehe buch/README.md.
    #
    # Freigehalten wird die Fläche weiterhin: Der Klappentext und der
    # Pflichthinweis rechnen unten mit `weissflaeche()`, damit kein Wort
    # unter KDPs Box gerät.

    hinweis_zeilen = len(umbrechen(c, MARKENHINWEIS, "Serif", 7, textbreite))
    _, fy, _, fh = weissflaeche(x, y, breite, hardcover=hardcover)
    hinweis_y = fy + fh + BARCODE_LUFT_MM * mm + hinweis_zeilen * 9
    oben = y + hoehe * 0.815
    platz = oben - (hinweis_y + 16)

    # Der Klappentext sucht sich seine Größe selbst: Er wird beim Schreiben
    # länger und kürzer, und der Text soll weder überlaufen noch auf der
    # Rückseite verloren wirken.
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

    # Die Trimmgröße kommt je Bindeart aus der Konfiguration. Zurzeit sind
    # beide 6 x 9 Zoll; die Unterscheidung bleibt, weil KDP für Taschenbuch
    # und Hardcover verschiedene Formatlisten führt und eine Fassung
    # deshalb jederzeit wieder abweichen kann. Passt die Trimmgröße nicht
    # zur Auswahl im Formular, lehnt der Upload mit „erwartete
    # Covergröße …" ab — dieselbe Falle wie bei Band 3.
    sf = cfg["hardcover_seitenformat"] if hardcover else cfg["seitenformat"]
    trim_b = sf["breite_mm"] * mm
    trim_h = sf["hoehe_mm"] * mm
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
    foto = titelbild_suchen()
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    # Die Farbe, in die das Foto ausblendet, wird an seiner Unterkante
    # abgegriffen — siehe grundfarbe_bei().
    band_unterkante = anschnitt + trim_h * (1 - TITELBILD_BAND)

    rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
               kopf, absaetze, punkte, hardcover=hardcover)
    ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
            mit_ruecken_text)
    vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                trim_b, trim_h, cfg, foto, ueberstand=anschnitt,
                ausblendfarbe=grundfarbe_bei(band_unterkante, gesamt_h))

    c.showPage()
    c.save()
    return {"gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
            "ruecken_mm": ruecken_b / mm,
            "ruecken_text": mit_ruecken_text,
            "titelbild": foto}


def kindle_titelbild(cfg, ziel, breite_px=1600, hoehe_px=2560, qualitaet=92):
    """Das Titelbild der Kindle-Ausgabe: nur die Vorderseite, Verhältnis 1,6.

    Ein Kindle-Buch braucht kein aufgeklapptes PDF mit Rückseite, Rücken und
    Anschnitt, sondern ein einzelnes Bild. Amazon empfiehlt 1600 x 2560 px.

    Gezeichnet wird mit **derselben** Funktion wie die gedruckte Vorderseite,
    nur auf eine höhere Leinwand — im Katalog stehen Taschenbuch und
    Kindle-Ausgabe nebeneinander und müssen als dasselbe Buch erkennbar sein.

    Die Leinwand bekommt die echte Buchbreite in Punkt, die Höhe folgt aus
    dem Verhältnis. Das ist nicht beliebig: Die Schriftgrößen sind absolute
    Punktwerte, und auf einer breiteren Leinwand bliebe alles außer dem
    Titel winzig.
    """
    import io

    import fitz
    from PIL import Image

    schriften_laden()
    breite_pt = cfg["seitenformat"]["breite_mm"] * mm
    hoehe_pt = breite_pt * (hoehe_px / breite_px)

    puffer = io.BytesIO()
    c = canvas.Canvas(puffer, pagesize=(breite_pt, hoehe_pt),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Kindle")

    verlauf(c, 0, 0, breite_pt, hoehe_pt,
            FARBEN["grund_oben"], FARBEN["grund_unten"])
    vorderseite(c, 0, 0, breite_pt, hoehe_pt, cfg, titelbild_suchen(),
                ausblendfarbe=grundfarbe_bei(
                    hoehe_pt * (1 - TITELBILD_BAND), hoehe_pt))
    c.showPage()
    c.save()

    dokument = fitz.open(stream=puffer.getvalue(), filetype="pdf")
    pix = dokument[0].get_pixmap(
        matrix=fitz.Matrix(breite_px / breite_pt, hoehe_px / hoehe_pt),
        alpha=False)
    bild = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    ziel = Path(ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ziel, format="JPEG", quality=qualitaet, optimize=True)
    return {"ziel": ziel, "px": bild.size, "kb": ziel.stat().st_size / 1024}


def main():
    cfg = yaml.safe_load((BAND / "dopamin.yaml").read_text(encoding="utf-8"))
    klappentext = BAND / "cover" / "klappentext.md"

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"

        # Jede Bindeart liest ihre eigene Seitenzahl. Die Innenteile haben
        # verschiedene Trimmgrößen, und aus der Seitenzahl folgt der Rücken.
        innenteil = (f"{cfg['slug']}-hardcover.pdf" if hardcover
                     else f"{cfg['slug']}.pdf")
        seiten = seitenzahl(BAND / "out" / innenteil)

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
        # Die Trimmgröße gehört in die Ausgabe, weil sie die eine Angabe
        # ist, die im Formular von Hand gesetzt wird und mit der Datei
        # übereinstimmen muss. Weicht sie ab, meldet KDP „erwartete
        # Covergröße …" mit den Maßen der ausgewählten Trimmgröße — die
        # Zahl daneben ist dann die der eingereichten Datei, und aus der
        # Differenz lässt sich ablesen, welche der beiden falsch ist.
        sf = cfg["hardcover_seitenformat"] if hardcover else cfg["seitenformat"]
        print(f"Im KDP-Formular als Trimmgröße wählen: "
              f"{sf['breite_mm']/25.4:.4g} x {sf['hoehe_mm']/25.4:.4g} Zoll")
        titelbild_melden(cfg, masse["titelbild"], hardcover=hardcover)
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")

    kindle = kindle_titelbild(cfg, BAND / "out" / "kindle-cover.jpg")
    b, h = kindle["px"]
    print(f"\nKindle-Titelbild: {b} x {h} px · {kindle['kb']:.0f} KB")
    print(f"  → {kindle['ziel'].relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
