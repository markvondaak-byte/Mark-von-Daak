#!/usr/bin/env python3
"""Stellt das Veröffentlichungsverzeichnis für Netlify zusammen.

    python3 tools/build_site.py

Warum überhaupt ein Build: Im Repository liegen neben der Website auch die
Quellen der drei Bücher (buch/, workbook/, rezepte/) und die Build-Skripte.
Die gehören nicht ins Netz. Dieses Skript kopiert deshalb gezielt nur das,
was ausgeliefert werden soll, nach dist/.

Nutzt ausschließlich die Standardbibliothek — auf Netlify muss dafür nichts
installiert werden.
"""

import shutil
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
ZIEL = WURZEL / "dist"

# Einzelne Dateien aus dem Wurzelverzeichnis.
DATEIEN = [
    "index.html",
    "impressum.html",
    "datenschutz.html",
    "robots.txt",
    "404.html",
]

# Ganze Verzeichnisse. Der zweite Wert nennt Unterordner, die drinbleiben
# sollen — Build-Skripte haben auf dem Server nichts verloren.
VERZEICHNISSE = [
    ("assets", set()),
    ("app", {"build"}),
    ("business", {"build"}),
]


def kopieren():
    if ZIEL.exists():
        shutil.rmtree(ZIEL)
    ZIEL.mkdir(parents=True)

    kopiert, fehlend = [], []

    for name in DATEIEN:
        quelle = WURZEL / name
        if not quelle.exists():
            fehlend.append(name)
            continue
        shutil.copy2(quelle, ZIEL / name)
        kopiert.append((name, quelle.stat().st_size))

    for name, ausnehmen in VERZEICHNISSE:
        quelle = WURZEL / name
        if not quelle.is_dir():
            fehlend.append(name + "/")
            continue
        shutil.copytree(
            quelle, ZIEL / name,
            ignore=shutil.ignore_patterns(*ausnehmen, "__pycache__", "*.pyc",
                                          ".DS_Store"),
        )
        groesse = sum(p.stat().st_size for p in (ZIEL / name).rglob("*")
                      if p.is_file())
        anzahl = sum(1 for p in (ZIEL / name).rglob("*") if p.is_file())
        kopiert.append((f"{name}/  ({anzahl} Dateien)", groesse))

    return kopiert, fehlend


def pruefen():
    """Sicherheitsnetz: Wenn Buchquellen im dist landen, ist etwas faul."""
    verboten = ["buch", "workbook", "rezepte", "tools", ".git", ".claude"]
    treffer = [v for v in verboten if (ZIEL / v).exists()]
    if treffer:
        print(f"\nFEHLER: Diese Verzeichnisse dürfen nicht veröffentlicht "
              f"werden: {', '.join(treffer)}")
        return False

    # Die App braucht ihre Daten, sonst startet sie beim Nutzer nicht.
    pflicht = ["app/index.html", "app/app.js", "app/app.css", "app/sw.js",
               "app/manifest.webmanifest", "app/daten/programm.json",
               "app/daten/rezepte.json", "app/daten/wissen.json",
               "app/icons/icon-192.png", "app/icons/icon-512.png",
               "business/index.html", "business/app.js", "business/app.css",
               "business/sw.js", "business/manifest.webmanifest",
               "business/icons/icon-192.png", "business/icons/icon-512.png",
               "index.html"]
    fehlt = [p for p in pflicht if not (ZIEL / p).exists()]
    if fehlt:
        print(f"\nFEHLER: Im dist fehlen: {', '.join(fehlt)}")
        return False
    return True


def main():
    print(f"Baue Veröffentlichungsverzeichnis in {ZIEL.relative_to(WURZEL)}/\n")
    kopiert, fehlend = kopieren()

    for name, groesse in kopiert:
        print(f"  {name:34s} {groesse / 1024:8.1f} KB")

    if fehlend:
        print(f"\n  Nicht gefunden (übersprungen): {', '.join(fehlend)}")

    if not pruefen():
        return 1

    gesamt = sum(p.stat().st_size for p in ZIEL.rglob("*") if p.is_file())
    anzahl = sum(1 for p in ZIEL.rglob("*") if p.is_file())
    print(f"\n{anzahl} Dateien, {gesamt / 1024 / 1024:.2f} MB — bereit zum "
          "Ausliefern.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
