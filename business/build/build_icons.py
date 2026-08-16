#!/usr/bin/env python3
"""Erzeugt die Icons für den Homescreen.

    python3 business/build/build_icons.py

Motiv ist eine Struktur aus drei Knoten: einer oben, zwei darunter, verbunden
durch zwei Linien. Es steht für das, was die App abbildet — Menschen, die an
Menschen hängen.

Bewusst anders als das Symbol der Programm-App nebenan, und in Petrol statt
Rot: Beide Apps liegen am Ende auf demselben Homescreen und müssen sich auf
einen Blick unterscheiden. Kein FitLine-Logo und keine Wortmarke — die App ist
Marks eigenes Werkzeug, keine Publikation von PM-International.

Zwei Dinge, die bei Homescreen-Icons regelmäßig schiefgehen und hier bewusst
anders gemacht sind:

1. **Keine vorgerundeten Ecken, keine Transparenz.** iOS legt über das
   Apple-Touch-Icon selbst eine Rundung. Wer schon gerundet abliefert, bekommt
   die Ecken zweimal beschnitten — sichtbare Artefakte und ein Symbol, das
   kleiner wirkt als die Nachbarn.

2. **Maskable getrennt.** Android beschneidet adaptive Icons je nach Hersteller
   zu Kreis, Squircle oder Tropfen. Das Motiv muss dafür innerhalb der sicheren
   Zone von 80 Prozent liegen — beim randfüllenden Icon darf es größer sein.
"""

from pathlib import Path

from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[2]
ZIEL = WURZEL / "business" / "icons"

# Knoten im 64er-Raster: oben die eigene Position, darunter die Linie.
OBEN = (32, 17)
LINKS = (17, 45)
RECHTS = (47, 45)

# Verlauf im Petrol der App. Oben etwas heller, damit das Symbol auf hellen
# wie dunklen Homescreens Tiefe hat, statt flach zu wirken.
PETROL_OBEN = (23, 133, 139)
PETROL_UNTEN = (10, 84, 89)
WEISS = (255, 255, 255)

UEBERABTASTUNG = 8   # 8-fach zeichnen und herunterrechnen ergibt weiche Kanten


def _verlauf(kante):
    bild = Image.new("RGB", (kante, kante), PETROL_OBEN)
    zeichner = ImageDraw.Draw(bild)
    for y in range(kante):
        anteil = y / max(1, kante - 1)
        # Leicht beschleunigt, damit die obere Hälfte heller bleibt.
        t = anteil ** 1.25
        farbe = tuple(round(PETROL_OBEN[i] + (PETROL_UNTEN[i] - PETROL_OBEN[i]) * t)
                      for i in range(3))
        zeichner.line([(0, y), (kante, y)], fill=farbe)
    return bild


def _einpassen(kante, anteil_breite):
    """Skaliert das Motiv auf die gewünschte Breite und zentriert es."""
    punkte = [OBEN, LINKS, RECHTS]
    xs = [p[0] for p in punkte]
    ys = [p[1] for p in punkte]
    breite, hoehe = max(xs) - min(xs), max(ys) - min(ys)
    faktor = (kante * anteil_breite) / breite

    versatz_x = (kante - breite * faktor) / 2 - min(xs) * faktor
    versatz_y = (kante - hoehe * faktor) / 2 - min(ys) * faktor
    return [(x * faktor + versatz_x, y * faktor + versatz_y) for x, y in punkte]


def _struktur_zeichnen(bild, kante, anteil_breite, strichanteil):
    oben, links, rechts = _einpassen(kante, anteil_breite)
    staerke = max(2, round(kante * strichanteil))
    knoten = staerke * 1.75
    zeichner = ImageDraw.Draw(bild)

    # Erst die Verbindungen, dann die Knoten darüber — so verschwinden die
    # Linienenden sauber unter den Kreisen.
    zeichner.line([oben, links], fill=WEISS, width=staerke)
    zeichner.line([oben, rechts], fill=WEISS, width=staerke)

    for punkt, groesse in ((oben, knoten * 1.22), (links, knoten), (rechts, knoten)):
        x, y = punkt
        zeichner.ellipse([x - groesse, y - groesse, x + groesse, y + groesse],
                         fill=WEISS)
    return bild


def icon_bauen(kante, *, maskable=False):
    gross = kante * UEBERABTASTUNG
    bild = _verlauf(gross)

    # Randfüllend darf das Motiv breiter sein. Beim maskable-Icon muss es in
    # die sichere Zone passen, sonst schneiden manche Launcher es an.
    anteil = 0.46 if maskable else 0.58
    strich = 0.052 if maskable else 0.062

    _struktur_zeichnen(bild, gross, anteil, strich)
    return bild.resize((kante, kante), Image.LANCZOS)


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    aufgaben = [
        ("icon-180.png", 180, False),   # Apple-Touch-Icon
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
    ]
    for name, kante, maskable in aufgaben:
        bild = icon_bauen(kante, maskable=maskable)
        pfad = ZIEL / name
        # Ohne Alphakanal speichern: iOS zeigt Transparenz sonst schwarz an.
        bild.convert("RGB").save(pfad, optimize=True)
        art = "maskable" if maskable else "randfüllend"
        print(f"  {name:24s} {kante:4d}px  {art:12s} "
              f"{pfad.stat().st_size / 1024:6.1f} KB")

    # Kleine Kontrollmontage, um die Symbole nebeneinander zu beurteilen.
    vorschau = Image.new("RGB", (560, 200), (241, 243, 242))
    for i, name in enumerate(["icon-180.png", "icon-192.png",
                              "icon-512.png", "icon-maskable-512.png"]):
        mini = Image.open(ZIEL / name).resize((120, 120), Image.LANCZOS)
        vorschau.paste(mini, (24 + i * 134, 40))
    vorschau.save(Path(__file__).parent / "vorschau.png")
    print("\n  Vorschau: business/build/vorschau.png (wird nicht ausgeliefert)")


if __name__ == "__main__":
    main()
