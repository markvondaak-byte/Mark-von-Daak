#!/usr/bin/env python3
"""Baut den Umschlag für „Das Reptiliengehirn des Menschen".

    python3 reptilienhirn/build/build_cover.py

**Nach dem Innenteil aufrufen** — die Rückenbreite errechnet sich aus der
Seitenzahl des fertigen PDFs.

Die Zeichenarbeit kommt unverändert aus `buch/build/build_cover.py`; hier
stehen nur die abweichenden Pfade und die eigene Metadatendatei. Der Band
nutzt die Farbwelt `schiefer` mit dem Akzent `bernstein`.

**Dieser Band braucht ein eigenes Titelbild.** Die Illustrationsroutine der
Stoffwechsel-Reihe zeichnet Obst und Gemüse; ohne Foto fiele der Umschlag auf
genau diese Motive zurück, und die passen zu einem Buch über Hirnforschung
nicht. Das Skript bricht deshalb ab, wenn kein Titelbild vorliegt, statt
stillschweigend eine Lebensmittelauslage zu setzen — siehe README.md.
"""

import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "reptilienhirn"

sys.path.insert(0, str(WURZEL / "buch" / "build"))
import build_cover  # noqa: E402


def main():
    cfg = yaml.safe_load(
        (BAND / "reptilienhirn.yaml").read_text(encoding="utf-8"))
    innenteil = BAND / "out" / f"{cfg['slug']}.pdf"
    if not innenteil.exists():
        raise SystemExit(
            f"Innenteil fehlt: {innenteil.relative_to(WURZEL)}\n"
            "Erst bauen: python3 reptilienhirn/build/build_reptilienhirn.py")

    klappentext = BAND / "cover" / "klappentext.md"
    seiten = build_cover.seitenzahl(innenteil)

    # Vor dem Zeichnen prüfen, nicht danach: Ohne eigenes Motiv griffe
    # titelbild_suchen() auf buch/cover/titelbild.jpg zurück — das Foto der
    # Stoffwechsel-Reihe — oder auf die gezeichnete Lebensmittelauslage.
    # Beides wäre für diesen Band falsch und fiele erst beim Ansehen auf.
    eigenes = build_cover.titelbild_suchen(BAND / "cover")
    if eigenes is None or eigenes.parent != (BAND / "cover"):
        soll_b, soll_h = build_cover.titelbild_sollmasse(cfg)
        raise SystemExit(
            "Kein eigenes Titelbild für diesen Band.\n"
            f"Erwartet: reptilienhirn/cover/titelbild.jpg "
            f"(oder .png/.jpeg/.webp), mindestens {soll_b} x {soll_h} px.\n"
            "Ohne diese Datei zeichnete der Umschlag Obst und Gemüse — die "
            "Motive der Stoffwechsel-Reihe. Näheres in reptilienhirn/README.md."
        )

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < build_cover.HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{build_cover.HARDCOVER_MIN_SEITEN} Seiten, "
                  f"der Band hat {seiten}.")
            continue

        ziel = BAND / "out" / f"{name}.pdf"
        masse = build_cover.cover_bauen(cfg, seiten, klappentext, ziel,
                                        hardcover=hardcover)
        png = build_cover.vorschau(ziel, BAND / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        rand = build_cover.WRAP_MM if hardcover else build_cover.BESCHNITT_MM
        randname = ("Umschlagrand um die Buchdecke" if hardcover
                    else "Anschnitt")
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {rand} mm {randname}")
        build_cover.titelbild_melden(cfg, masse["titelbild"])
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
