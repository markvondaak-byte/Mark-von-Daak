#!/usr/bin/env python3
"""Erzeugt die Icons für den Homescreen.

    python3 app/build/build_icons.py

Motiv ist die Pulslinie aus dem Favicon der Website — damit gehören
Browser-Tab und Homescreen-Symbol sichtbar zusammen. Kein FitLine-Logo und
keine Wortmarke: Die App ist Marks eigenes Werkzeug, keine Publikation von
PM-International.

Zwei Dinge, die bei Homescreen-Icons regelmäßig schiefgehen und hier bewusst
anders gemacht sind:

1. **Keine vorgerundeten Ecken, keine Transparenz.** iOS legt über das
   Apple-Touch-Icon selbst eine Rundung. Wer schon gerundet abliefert, bekommt
   die Ecken zweimal beschnitten — sichtbare Artefakte und ein Symbol, das
   kleiner wirkt als die Nachbarn. Geliefert wird deshalb ein randfüllendes,
   deckendes Quadrat; das Runden übernimmt das Betriebssystem.

2. **Maskable getrennt.** Android beschneidet adaptive Icons je nach Hersteller
   zu Kreis, Squircle oder Tropfen. Das Motiv muss dafür innerhalb der sicheren
   Zone von 80 Prozent liegen — beim randfüllenden Icon darf es größer sein.
"""

from pathlib import Path

from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[2]
ZIEL = WURZEL / "app" / "icons"

# Pulslinie aus dem Website-Favicon, Koordinaten im 64er-Raster.
PULS = [(9, 34), (18, 34), (22, 23), (28, 43), (33, 16), (38, 34), (42, 28), (50, 28)]

# Verlauf im Markenrot. Oben etwas heller, damit das Symbol auf dunklen wie
# hellen Homescreens Tiefe hat, statt flach zu wirken.
ROT_OBEN = (216, 26, 55)
ROT_UNTEN = (152, 10, 33)
WEISS = (255, 255, 255)

UEBERABTASTUNG = 8   # 8-fach zeichnen und herunterrechnen ergibt weiche Kanten


def _verlauf(kante):
    bild = Image.new("RGB", (kante, kante), ROT_OBEN)
    zeichner = ImageDraw.Draw(bild)
    for y in range(kante):
        anteil = y / max(1, kante - 1)
        # Leicht beschleunigt, damit die obere Hälfte heller bleibt.
        t = anteil ** 1.25
        farbe = tuple(round(ROT_OBEN[i] + (ROT_UNTEN[i] - ROT_OBEN[i]) * t)
                      for i in range(3))
        zeichner.line([(0, y), (kante, y)], fill=farbe)
    return bild


def _punkte_einpassen(kante, anteil_breite):
    """Skaliert die Pulslinie auf die gewünschte Breite und zentriert sie."""
    xs = [p[0] for p in PULS]
    ys = [p[1] for p in PULS]
    breite, hoehe = max(xs) - min(xs), max(ys) - min(ys)
    faktor = (kante * anteil_breite) / breite

    versatz_x = (kante - breite * faktor) / 2 - min(xs) * faktor
    versatz_y = (kante - hoehe * faktor) / 2 - min(ys) * faktor
    return [(x * faktor + versatz_x, y * faktor + versatz_y) for x, y in PULS], faktor


def _puls_zeichnen(bild, kante, anteil_breite, strichanteil):
    punkte, _ = _punkte_einpassen(kante, anteil_breite)
    staerke = max(2, round(kante * strichanteil))
    zeichner = ImageDraw.Draw(bild)

    # joint="curve" rundet die Innenecken. Die beiden Enden bekommen ihre
    # runden Abschlüsse von Hand — sonst stehen sie hart ab.
    zeichner.line(punkte, fill=WEISS, width=staerke, joint="curve")
    r = staerke / 2
    for x, y in (punkte[0], punkte[-1]):
        zeichner.ellipse([x - r, y - r, x + r, y + r], fill=WEISS)
    return bild


def icon_bauen(kante, *, maskable=False):
    gross = kante * UEBERABTASTUNG
    bild = _verlauf(gross)

    # Randfüllend darf das Motiv breiter sein. Beim maskable-Icon muss es in
    # die sichere Zone passen, sonst schneiden manche Launcher es an.
    anteil = 0.52 if maskable else 0.66
    strich = 0.075 if maskable else 0.088

    _puls_zeichnen(bild, gross, anteil, strich)
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
    vorschau = Image.new("RGB", (560, 200), (242, 240, 235))
    for i, name in enumerate(["icon-180.png", "icon-192.png",
                              "icon-512.png", "icon-maskable-512.png"]):
        mini = Image.open(ZIEL / name).resize((120, 120), Image.LANCZOS)
        vorschau.paste(mini, (24 + i * 134, 40))
    vorschau.save(Path(__file__).parent / "vorschau.png")
    print("\n  Vorschau: app/build/vorschau.png (wird nicht ausgeliefert)")


if __name__ == "__main__":
    main()
