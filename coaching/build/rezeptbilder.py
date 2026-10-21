#!/usr/bin/env python3
"""Bindet Rezeptfotos in die App ein.

    python3 coaching/build/rezeptbilder.py

Originale (JPG, PNG oder WebP, beliebige Größe) nach
coaching/build/rezeptbilder/ legen, Dateiname = Rezept-ID, z. B.
`chili-con-carne.jpg`. Welche ID zu welchem Rezept gehört und welche Bilder
in Canva schon existieren, steht in coaching/build/rezeptbilder.json.

Das Skript schneidet jedes Bild mittig auf 4:3 zu, rechnet es auf 960 × 720
herunter und legt es als JPEG unter coaching/bilder/rezepte/ ab — klein genug
fürs Handy, scharf genug für die große Ansicht. Danach trägt es in
daten/rezepte.json bei jedem Rezept mit Bild das Feld `bild` ein und entfernt
es bei Rezepten ohne Bild. Nach dem Lauf VERSION in sw.js erhöhen.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

APP = Path(__file__).resolve().parents[1]
QUELLE = APP / "build" / "rezeptbilder"
ZIEL = APP / "bilder" / "rezepte"
DATEN = APP / "daten" / "rezepte.json"
BREITE, HOEHE = 960, 720


def umrechnen(quelle, ziel):
    bild = ImageOps.exif_transpose(Image.open(quelle)).convert("RGB")
    bild = ImageOps.fit(bild, (BREITE, HOEHE), Image.LANCZOS, centering=(0.5, 0.5))
    bild.save(ziel, "JPEG", quality=80, optimize=True, progressive=True)


def main():
    ZIEL.mkdir(parents=True, exist_ok=True)
    daten = json.loads(DATEN.read_text(encoding="utf-8"))
    ids = {r["id"] for r in daten["rezepte"]}

    for datei in sorted(QUELLE.glob("*")):
        if datei.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        if datei.stem not in ids:
            print(f"  übersprungen: {datei.name} (keine Rezept-ID)")
            continue
        ziel = ZIEL / f"{datei.stem}.jpg"
        umrechnen(datei, ziel)
        print(f"  {datei.name:34s} → {ziel.relative_to(APP)}  {ziel.stat().st_size / 1024:5.0f} KB")

    mit, ohne = 0, []
    for r in daten["rezepte"]:
        if (ZIEL / f"{r['id']}.jpg").exists():
            r["bild"] = f"bilder/rezepte/{r['id']}.jpg"
            mit += 1
        else:
            r.pop("bild", None)
            ohne.append(r["id"])
    DATEN.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\n{mit} von {len(daten['rezepte'])} Rezepten mit Bild.")
    if ohne:
        print("Ohne Bild (Platzhalter):", ", ".join(ohne))
    return 0


if __name__ == "__main__":
    sys.exit(main())
