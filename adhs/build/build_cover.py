#!/usr/bin/env python3
"""Baut den druckfertigen KDP-Umschlag für Band 4 — „Chaos mit System“.

    python3 adhs/build/build_adhs.py     # zuerst der Innenteil
    python3 adhs/build/build_cover.py    # dann der Umschlag

Die Rückenbreite ergibt sich aus der Seitenzahl des fertigen Innenteils, der
also vorher gebaut sein muss.

Farbwelt, Motiv und die drei Flächen stehen in `gestaltung.py` — geteilt mit
dem Kindle-Titelbild, damit Druck- und E-Book-Ausgabe im Katalog als dasselbe
Buch erkennbar bleiben. Hier steht nur der Zusammenbau: Maße, Anschnitt,
Rücken.

Zu KDP hochgeladen wird `cover-druck.pdf`, nicht `cover.pdf`:

    python3 buch/build/cover_flach.py adhs/out/cover.pdf
"""

import sys
from pathlib import Path

import yaml
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "buch" / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import gestaltung as g  # noqa: E402
from build_cover import (BESCHNITT_MM, BUCHDECKE_MM,  # noqa: E402
                         HARDCOVER_MIN_SEITEN, RUECKEN_PRO_SEITE_MM,
                         RUECKENTEXT_AB_SEITEN, WRAP_MM, klappentext_laden,
                         schriften_laden, seitenzahl, vorschau)

ADHS = WURZEL / "adhs"


def cover_bauen(cfg, seiten, klappentext_pfad, ziel, *, hardcover=False):
    schriften_laden()

    trim_b = cfg["seitenformat"]["breite_mm"] * mm
    trim_h = cfg["seitenformat"]["hoehe_mm"] * mm
    if hardcover:
        anschnitt = WRAP_MM * mm
        ruecken_b = (seiten * RUECKEN_PRO_SEITE_MM + BUCHDECKE_MM) * mm
    else:
        anschnitt = BESCHNITT_MM * mm
        ruecken_b = seiten * RUECKEN_PRO_SEITE_MM * mm

    gesamt_b = 2 * trim_b + ruecken_b + 2 * anschnitt
    gesamt_h = trim_h + 2 * anschnitt

    # initialFontName: reportlab schreibt sonst einen Seitenvorspann mit
    # Helvetica in die Ressourcen — eine Schrift ohne Einbettung, die kein
    # Zeichen setzt, aber bei der KDP-Prüfung auffallen kann.
    c = canvas.Canvas(str(ziel), pagesize=(gesamt_b, gesamt_h),
                      initialFontName="Serif")
    c.setTitle(f"{cfg['titel']} — Umschlag")

    g.tintengrund(c, 0, 0, gesamt_b, gesamt_h)

    kopf, absaetze, punkte = klappentext_laden(Path(klappentext_pfad))
    mit_ruecken_text = hardcover or seiten >= RUECKENTEXT_AB_SEITEN

    g.rueckseite(c, anschnitt, anschnitt, trim_b, trim_h, cfg,
                 kopf, absaetze, punkte, hardcover=hardcover)
    g.ruecken(c, anschnitt + trim_b, anschnitt, ruecken_b, trim_h, cfg,
              mit_ruecken_text)
    # ueberstand nur nach rechts: Links liegt der Rücken, und Striche quer
    # über den Rückentext wären beim Hardcover 18 mm breit.
    g.vorderseite(c, anschnitt + trim_b + ruecken_b, anschnitt,
                  trim_b, trim_h, cfg, ueberstand=anschnitt)

    c.showPage()
    c.save()
    return {
        "gesamt_mm": (gesamt_b / mm, gesamt_h / mm),
        "ruecken_mm": ruecken_b / mm,
        "ruecken_text": mit_ruecken_text,
    }


def main():
    cfg = yaml.safe_load((ADHS / "adhs.yaml").read_text(encoding="utf-8"))
    seiten = seitenzahl(ADHS / "out" / f"{cfg['slug']}.pdf")
    klappentext = ADHS / "cover" / "klappentext.md"

    for hardcover in (False, True):
        art = "Hardcover" if hardcover else "Taschenbuch"
        name = "cover-hardcover" if hardcover else "cover"
        if hardcover and seiten < HARDCOVER_MIN_SEITEN:
            print(f"\n{art}: übersprungen — KDP verlangt mindestens "
                  f"{HARDCOVER_MIN_SEITEN} Seiten, der Band hat {seiten}.")
            continue

        ziel = ADHS / "out" / f"{name}.pdf"
        masse = cover_bauen(cfg, seiten, klappentext, ziel, hardcover=hardcover)
        png = vorschau(ziel, ADHS / "out" / f"{name}-vorschau.png")

        b, h = masse["gesamt_mm"]
        rand = WRAP_MM if hardcover else BESCHNITT_MM
        randname = "Umschlagrand um die Buchdecke" if hardcover else "Anschnitt"
        print(f"\n{art} — Innenteil: {seiten} Seiten")
        print(f"Rückenbreite: {masse['ruecken_mm']:.1f} mm"
              f"  (Rückentext: {'ja' if masse['ruecken_text'] else 'nein'})")
        print(f"Umschlag gesamt: {b:.2f} x {h:.2f} mm "
              f"= {b/25.4:.3f} x {h/25.4:.3f} Zoll, inkl. {rand} mm {randname}")
        print(f"  → {ziel.relative_to(WURZEL)}")
        print(f"  → {png.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
