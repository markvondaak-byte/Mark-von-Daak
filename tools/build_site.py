#!/usr/bin/env python3
"""Stellt das Veröffentlichungsverzeichnis für Netlify zusammen.

    python3 tools/build_site.py

Veröffentlicht wird ausschließlich **Mark von Daak – Personal Training**
unter https://markvondaak-coaching.de:

| Pfad        | Quelle                                   |
|-------------|------------------------------------------|
| `/`         | `personal-training/` (Startseite, Danke-, |
|             | Fehlerseite, Impressum, Datenschutz,     |
|             | Bilder, Schriften, robots.txt, Sitemap)  |
| `/coaching/`| App SMART Coaching samt Coach-Ansicht    |

Die FitLine-Seite „Vital und fit mit Mark“ (`index.html`, `impressum.html`,
`datenschutz.html`, `assets/`), die Stoffwechsel-Reset-App (`app/`), das
Kontakttool (`business/`) und die Buchquellen bleiben im Repository, werden
hier aber bewusst **nicht** ausgeliefert. Das Skript bricht mit einem Fehler
ab, falls doch etwas davon in `dist/` landet.

Nutzt ausschließlich die Standardbibliothek — auf Netlify muss dafür nichts
installiert werden.
"""

import shutil
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
ZIEL = WURZEL / "dist"

# (Quelle, Ziel in dist/, ausgenommene Dateien/Ordner)
VERZEICHNISSE = [
    ("personal-training", ".", set()),
    ("coaching", "coaching", {"build", "README.md"}),
]


def kopieren():
    if ZIEL.exists():
        shutil.rmtree(ZIEL)
    ZIEL.mkdir(parents=True)

    kopiert, fehlend = [], []
    for quelle_name, ziel_name, ausnehmen in VERZEICHNISSE:
        quelle = WURZEL / quelle_name
        if not quelle.is_dir():
            fehlend.append(quelle_name + "/")
            continue
        ziel = ZIEL / ziel_name
        shutil.copytree(
            quelle, ziel, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(*ausnehmen, "__pycache__", "*.pyc",
                                          ".DS_Store", "_*.html"),
        )
        dateien = [p for p in quelle.rglob("*") if p.is_file()
                   and not p.name.startswith("_")
                   and not any(teil in ausnehmen for teil in p.relative_to(quelle).parts)]
        kopiert.append((f"{quelle_name}/ → /{'' if ziel_name == '.' else ziel_name + '/'}"
                        f"  ({len(dateien)} Dateien)",
                        sum(p.stat().st_size for p in dateien)))
    return kopiert, fehlend


def pruefen():
    """Sicherheitsnetz: Nichts von FitLine und keine Buchquellen im dist."""
    verboten = ["app", "business", "assets", "buch", "workbook", "rezepte",
                "kopf", "tools", "marke", "personal-training", ".git",
                ".claude", ".netlify"]
    treffer = [v for v in verboten if (ZIEL / v).exists()]
    if treffer:
        print(f"\nFEHLER: Diese Verzeichnisse dürfen nicht veröffentlicht "
              f"werden: {', '.join(treffer)}")
        return False

    fitline = [p.relative_to(ZIEL).as_posix() for p in ZIEL.rglob("*.html")
               if "FitLine" in p.read_text(encoding="utf-8", errors="ignore")]
    if fitline:
        print(f"\nFEHLER: FitLine wird erwähnt in: {', '.join(fitline)}")
        return False

    pflicht = ["index.html", "danke.html", "404.html", "impressum.html",
               "datenschutz.html", "recht.css", "robots.txt", "sitemap.xml",
               "img/pin.png", "img/og.jpg", "fonts/inter-400.woff2",
               "coaching/index.html", "coaching/app.js", "coaching/app.css",
               "coaching/sw.js", "coaching/manifest.webmanifest",
               "coaching/daten/uebungen.json", "coaching/daten/lebensmittel.json",
               "coaching/daten/rezepte.json", "coaching/gemeinsam.js",
               "coaching/coach/index.html", "coaching/coach/coach.js",
               "coaching/recht/impressum.html", "coaching/recht/datenschutz.html",
               "coaching/recht/agb.html",
               "coaching/icons/icon-192.png", "coaching/icons/icon-512.png"]
    fehlt = [p for p in pflicht if not (ZIEL / p).exists()]
    if fehlt:
        print(f"\nFEHLER: Im dist fehlen: {', '.join(fehlt)}")
        return False
    return True


def main():
    print(f"Baue Veröffentlichungsverzeichnis in {ZIEL.relative_to(WURZEL)}/\n")
    kopiert, fehlend = kopieren()

    for name, groesse in kopiert:
        print(f"  {name:48s} {groesse / 1024:8.1f} KB")

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
