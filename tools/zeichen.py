#!/usr/bin/env python3
"""Misst die Verkaufstexte gegen die Grenzen, die Amazon durchsetzt.

    python3 tools/zeichen.py

Hintergrund: Zwei Felder bei Amazon sind hart begrenzt, und beide schneiden
ohne Warnung ab.

  Buchbeschreibung   4000 Zeichen, Auszeichnung zählt mit. Soll der Block
                     „Über den Autor" ans Ende, teilen sich Klappentext und
                     Biografie diese 4000 Zeichen.
  Author-Central-Biografie   rund 2500 Zeichen. Amazon nennt je nach
                     Oberfläche unterschiedliche Werte — die Anzeige im Feld
                     gilt, diese Zahl ist die vorsichtige Annahme.

Gemessen wird, was tatsächlich ins Feld kopiert wird: bei den Beschreibungen
der HTML-Block, bei der Biografie der Fließtext ohne die Zitatstriche des
Markdowns.

Exit-Code 1, sobald eine Kombination über ihrer Grenze liegt.
"""

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

GRENZE_BESCHREIBUNG = 4000
GRENZE_BIOGRAFIE = 2500

BIOGRAFIE = WURZEL / "autorenbiografie.md"

# Band → (Beschreibungsdatei, Nummer der Bio-Variante).
#
# Der erste HTML-Block einer Beschreibungsdatei ist die Langfassung; die
# Kurzfassung weiter unten wird nicht geprüft.
#
# Die Bio-Variante ist der wievielte HTML-Block in autorenbiografie.md:
# 0 = Variante A ohne Offenlegung (Band 1 hat sie schon in der Beschreibung),
# 1 = Variante B mit Offenlegung (Band 2 und 3 haben sie sonst nirgends).
BESCHREIBUNGEN = {
    "Band 1": (WURZEL / "buch" / "cover" / "amazon-beschreibung.md", 0),
    "Band 2": (WURZEL / "workbook" / "cover" / "amazon-beschreibung.md", 1),
    "Band 3": (WURZEL / "rezepte" / "cover" / "amazon-beschreibung.md", 1),
}


def html_bloecke(pfad):
    """Alle ```html-Blöcke einer Datei, in Reihenfolge."""
    if not pfad.is_file():
        return []
    text = pfad.read_text(encoding="utf-8")
    return [b.strip() for b in re.findall(r"```html\n(.*?)```", text, re.S)]


def zitat(pfad, ueberschrift):
    """Der Blockquote unter einer ##-Überschrift, als reiner Fließtext.

    Zeilenumbrüche innerhalb eines Absatzes stammen aus dem Markdown-Umbruch
    und verschwinden; Leerzeilen trennen Absätze und bleiben.
    """
    text = pfad.read_text(encoding="utf-8")
    treffer = re.search(
        r"^## " + re.escape(ueberschrift) + r".*?$(.*?)(?=^## |\Z)",
        text, re.S | re.M)
    if not treffer:
        return None
    zeilen = [z[2:] if z.startswith("> ") else ""
              for z in treffer.group(1).splitlines() if z.startswith(">")]
    absaetze = [" ".join(a.split())
                for a in "\n".join(zeilen).split("\n\n") if a.strip()]
    return "\n\n".join(absaetze)


def zeile(name, laenge, grenze):
    rest = grenze - laenge
    marke = "OK " if rest >= 0 else "ÜBER"
    print(f"  {marke}  {name:<34} {laenge:5d} / {grenze}   "
          f"{'noch ' + str(rest) if rest >= 0 else str(-rest) + ' zu viel'}")
    return rest >= 0


def main():
    if not BIOGRAFIE.is_file():
        raise SystemExit(f"Nicht gefunden: {BIOGRAFIE}")

    gut = True

    print("Author-Central-Biografie")
    for ueberschrift in ("Ich-Fassung für Author Central",
                         "Lang in der dritten Person"):
        text = zitat(BIOGRAFIE, ueberschrift)
        if text is None:
            print(f"  ??    {ueberschrift} — Abschnitt fehlt")
            gut = False
            continue
        gut &= zeile(ueberschrift, len(text), GRENZE_BIOGRAFIE)

    bio_html = html_bloecke(BIOGRAFIE)
    if len(bio_html) < 2:
        raise SystemExit("autorenbiografie.md braucht zwei HTML-Varianten "
                         f"(gefunden: {len(bio_html)}).")

    varianten = "  ".join(f"{'AB'[i]}: {len(b)}" for i, b in
                          enumerate(bio_html[:2]))
    print(f"\nBuchbeschreibung + Bio-Block ({varianten} Zeichen)")
    for band, (pfad, nummer) in BESCHREIBUNGEN.items():
        bloecke = html_bloecke(pfad)
        if not bloecke:
            print(f"  --    {band:<34} keine Beschreibung gefunden")
            continue
        beschreibung, block = bloecke[0], bio_html[nummer]
        gut &= zeile(f"{band} allein", len(beschreibung), GRENZE_BESCHREIBUNG)
        gut &= zeile(f"{band} + Bio {'AB'[nummer]}",
                     len(beschreibung) + len(block) + 1, GRENZE_BESCHREIBUNG)

    if not gut:
        print("\nMindestens ein Text liegt über seiner Grenze.")
        return 1
    print("\nAlle Texte liegen innerhalb der Grenzen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
