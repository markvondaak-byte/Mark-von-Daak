#!/usr/bin/env python3
"""Erzeugt die App-Icons.

    python3 app/build/build_icons.py

Ein Icon in der Akzentfarbe der Website mit einem stilisierten Blatt als
Zeichen für den Neustart. Bewusst ohne FitLine-Logo oder -Wortmarke: Die App
ist Marks eigenes Werkzeug, keine Publikation von PM-International.

Drei Größen, weil die Plattformen unterschiedliche brauchen:
  icon-192          Homescreen Android, Apple Touch Icon
  icon-512          Splash und Store-Darstellung
  icon-maskable-512 Android adaptive icons, Motiv innerhalb der sicheren Zone
"""

from pathlib import Path

from PIL import Image, ImageDraw

WURZEL = Path(__file__).resolve().parents[2]
ZIEL = WURZEL / "app" / "icons"

AKZENT = (200, 16, 46)        # #C8102E, wie --accent der Website
AKZENT_TIEF = (150, 10, 33)
WEISS = (255, 255, 255)


def blatt_zeichnen(bild, mitte, groesse, farbe):
    """Ein Blatt aus zwei gespiegelten Bögen, dazu die Mittelrippe."""
    zeichner = ImageDraw.Draw(bild)
    cx, cy = mitte
    h = groesse / 2

    # Blattfläche als Polygon aus zwei Bezier-Näherungen
    punkte = []
    schritte = 40
    for i in range(schritte + 1):
        t = i / schritte
        # obere Kante
        x = cx - h + 2 * h * t
        y = cy - h * 0.72 * (1 - (2 * t - 1) ** 2) ** 0.85
        punkte.append((x, y))
    for i in range(schritte + 1):
        t = 1 - i / schritte
        x = cx - h + 2 * h * t
        y = cy + h * 0.72 * (1 - (2 * t - 1) ** 2) ** 0.85
        punkte.append((x, y))
    zeichner.polygon(punkte, fill=farbe)

    # Mittelrippe
    zeichner.line([(cx - h * 0.86, cy), (cx + h * 0.86, cy)],
                  fill=AKZENT, width=max(2, int(groesse * 0.045)))
    # Seitenadern
    for anteil in (-0.42, -0.14, 0.14, 0.42):
        x0 = cx + anteil * h
        laenge = h * (0.5 - abs(anteil) * 0.55)
        for richtung in (-1, 1):
            zeichner.line(
                [(x0, cy), (x0 + laenge * 0.9, cy + richtung * laenge)],
                fill=AKZENT, width=max(1, int(groesse * 0.028)))


def icon_bauen(kante, *, maskable=False):
    # 4x zeichnen und herunterrechnen — ergibt weiche Kanten ohne Zusatzbibliothek.
    faktor = 4
    gross = kante * faktor
    bild = Image.new("RGB", (gross, gross), AKZENT)
    zeichner = ImageDraw.Draw(bild)

    # Sanfter Verlauf von oben links nach unten rechts
    for i in range(gross):
        anteil = i / gross
        farbe = tuple(int(AKZENT[k] + (AKZENT_TIEF[k] - AKZENT[k]) * anteil)
                      for k in range(3))
        zeichner.line([(0, i), (gross, i)], fill=farbe)

    # Bei maskable bleibt das Motiv in der sicheren Zone (80 % Durchmesser).
    motiv = gross * (0.44 if maskable else 0.58)
    blatt_zeichnen(bild, (gross / 2, gross / 2), motiv, WEISS)

    bild = bild.resize((kante, kante), Image.LANCZOS)

    if not maskable:
        # Abgerundete Ecken für Plattformen, die nicht selbst maskieren.
        maske = Image.new("L", (gross, gross), 0)
        ImageDraw.Draw(maske).rounded_rectangle(
            [0, 0, gross - 1, gross - 1], radius=int(gross * 0.22), fill=255)
        maske = maske.resize((kante, kante), Image.LANCZOS)
        mit_alpha = bild.convert("RGBA")
        mit_alpha.putalpha(maske)
        return mit_alpha

    return bild.convert("RGBA")


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    aufgaben = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
    ]
    for name, kante, maskable in aufgaben:
        bild = icon_bauen(kante, maskable=maskable)
        pfad = ZIEL / name
        bild.save(pfad)
        print(f"  {name:24s} {kante}x{kante}  {pfad.stat().st_size / 1024:5.1f} KB")


if __name__ == "__main__":
    main()
