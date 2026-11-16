#!/usr/bin/env python3
"""Erzeugt die Icons für den Homescreen.

    python3 coaching/build/build_icons.py

Motiv ist das Logo von Mark von Daak – Personal Training: der Standort-Pin
mit Hantel. Im Icon steht er weiß auf himmelblauem Grund (#38B6FF, leichter
Verlauf nach unten), Kreis und Hantel im Pin bleiben blau. Quelle ist
`marke/logo-bildmarke.png` im Wurzelverzeichnis.

Zwei Dinge, die bei Homescreen-Icons regelmäßig schiefgehen:

1. **Keine vorgerundeten Ecken, keine Transparenz.** iOS rundet das
   Apple-Touch-Icon selbst.
2. **Maskable getrennt.** Android beschneidet adaptive Icons; das Motiv muss
   dort in der sicheren Zone von 80 Prozent liegen.

Außerdem entsteht `icons/logo-pin.png` (das Logo in Originalfarben, 192 px
hoch) für Kopfzeile und Einrichtung der App.
"""

from pathlib import Path

from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[2]
ZIEL = WURZEL / "coaching" / "icons"
QUELLE = WURZEL / "marke" / "logo-bildmarke.png"

BLAU_OBEN = (64, 188, 255)
BLAU_UNTEN = (24, 143, 214)
LOGO_BLAU_R = 56     # Rotanteil von #38B6FF; Weiß hat 255


def _verlauf(kante):
    bild = Image.new("RGB", (kante, kante), BLAU_OBEN)
    zeichner = ImageDraw.Draw(bild)
    for y in range(kante):
        t = (y / max(1, kante - 1)) ** 1.2
        farbe = tuple(round(BLAU_OBEN[i] + (BLAU_UNTEN[i] - BLAU_OBEN[i]) * t)
                      for i in range(3))
        zeichner.line([(0, y), (kante, y)], fill=farbe)
    return bild


def _logo():
    logo = Image.open(QUELLE).convert("RGBA")
    return logo.crop(logo.getbbox())


def _weisser_pin(logo):
    """Blaue Flächen des Logos werden weiß, weiße Flächen durchsichtig.

    Der Rotkanal trennt beide sauber (56 gegen 255), Kantenpixel werden
    anteilig gemischt, damit nichts ausfranst.
    """
    quelle = logo.load()
    ziel = Image.new("RGBA", logo.size, (255, 255, 255, 0))
    pixel = ziel.load()
    for y in range(logo.size[1]):
        for x in range(logo.size[0]):
            r, _, _, a = quelle[x, y]
            if not a:
                continue
            blau = max(0.0, min(1.0, (255 - r) / (255 - LOGO_BLAU_R)))
            pixel[x, y] = (255, 255, 255, round(a * blau))
    return ziel


def _icon(kante, hoehe_anteil, pin):
    bild = _verlauf(kante).convert("RGBA")
    hoehe = round(kante * hoehe_anteil)
    breite = round(pin.width * hoehe / pin.height)
    klein = pin.resize((breite, hoehe), Image.LANCZOS)
    # Der Pin wirkt optisch zu tief, wenn er geometrisch mittig sitzt —
    # seine Masse liegt oben im Kreis. Deshalb leicht nach oben versetzt.
    x = (kante - breite) // 2
    y = (kante - hoehe) // 2 - round(kante * 0.015)
    bild.alpha_composite(klein, (x, y))
    return bild.convert("RGB")


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    logo = _logo()
    pin = _weisser_pin(logo)

    for kante, name in [(180, "icon-180.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
        _icon(kante, 0.62, pin).save(ZIEL / name, optimize=True)
    # Maskable: Motiv innerhalb der sicheren Zone (Kreis mit 80 % Durchmesser).
    _icon(512, 0.46, pin).save(ZIEL / "icon-maskable-512.png", optimize=True)

    hoehe = 192
    logo.resize((round(logo.width * hoehe / logo.height), hoehe), Image.LANCZOS) \
        .save(ZIEL / "logo-pin.png", optimize=True)

    print("Icons geschrieben nach", ZIEL)


if __name__ == "__main__":
    main()
