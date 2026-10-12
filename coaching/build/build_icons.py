#!/usr/bin/env python3
"""Erzeugt die Icons für den Homescreen.

    python3 coaching/build/build_icons.py

Motiv ist eine neutrale Hantel in Orange, leicht schräg gestellt — sie steht
für das, worum es in der App geht: dranbleiben, trainieren, Fortschritt
sichtbar machen. Keine Logos, keine Wortmarke.

Zwei Dinge, die bei Homescreen-Icons regelmäßig schiefgehen:

1. **Keine vorgerundeten Ecken, keine Transparenz.** iOS rundet das
   Apple-Touch-Icon selbst.
2. **Maskable getrennt.** Android beschneidet adaptive Icons; das Motiv muss
   dort in der sicheren Zone von 80 Prozent liegen.
"""

from pathlib import Path

from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[2]
ZIEL = WURZEL / "coaching" / "icons"

ORANGE_OBEN = (234, 98, 30)
ORANGE_UNTEN = (168, 52, 8)
WEISS = (255, 255, 255)

UEBERABTASTUNG = 8
NEIGUNG = -32   # Grad; gegen den Uhrzeigersinn, wirkt dynamischer als waagerecht


def _verlauf(kante):
    bild = Image.new("RGB", (kante, kante), ORANGE_OBEN)
    zeichner = ImageDraw.Draw(bild)
    for y in range(kante):
        t = (y / max(1, kante - 1)) ** 1.25
        farbe = tuple(round(ORANGE_OBEN[i] + (ORANGE_UNTEN[i] - ORANGE_OBEN[i]) * t)
                      for i in range(3))
        zeichner.line([(0, y), (kante, y)], fill=farbe)
    return bild


def _hantel(kante, breite_anteil):
    """Zeichnet die Hantel waagerecht auf eine transparente Ebene.

    Maße relativ zur Gesamtbreite der Hantel: Griff in der Mitte, je Seite
    eine große und eine kleine Scheibe, außen ein kurzer Stangenstummel.
    """
    ebene = Image.new("L", (kante, kante), 0)
    z = ImageDraw.Draw(ebene)
    b = kante * breite_anteil
    mx = my = kante / 2

    def rechteck(x0, x1, hoehe, radius):
        z.rounded_rectangle([mx + x0 * b, my - hoehe * b / 2,
                             mx + x1 * b, my + hoehe * b / 2],
                            radius=radius * b, fill=255)

    rechteck(-0.30, 0.30, 0.075, 0.03)           # Griff
    for s in (-1, 1):
        aussen = [(0.30, 0.38, 0.44), (0.38, 0.45, 0.32), (0.45, 0.50, 0.10)]
        for x0, x1, hoehe in aussen:
            a, e = sorted((s * x0, s * x1))
            rechteck(a, e, hoehe, 0.025)
    return ebene.rotate(NEIGUNG, resample=Image.BICUBIC, center=(mx, my))


def icon_bauen(kante, *, maskable=False):
    gross = kante * UEBERABTASTUNG
    bild = _verlauf(gross)
    anteil = 0.62 if maskable else 0.80
    maske = _hantel(gross, anteil)
    bild.paste(Image.new("RGB", (gross, gross), WEISS), (0, 0), maske)
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
        bild.convert("RGB").save(pfad, optimize=True)
        art = "maskable" if maskable else "randfüllend"
        print(f"  {name:24s} {kante:4d}px  {art:12s} "
              f"{pfad.stat().st_size / 1024:6.1f} KB")

    vorschau = Image.new("RGB", (560, 200), (241, 243, 242))
    for i, name in enumerate(["icon-180.png", "icon-192.png",
                              "icon-512.png", "icon-maskable-512.png"]):
        mini = Image.open(ZIEL / name).resize((120, 120), Image.LANCZOS)
        vorschau.paste(mini, (24 + i * 134, 40))
    vorschau.save(Path(__file__).parent / "vorschau.png")
    print("\n  Vorschau: coaching/build/vorschau.png (wird nicht ausgeliefert)")


if __name__ == "__main__":
    main()
