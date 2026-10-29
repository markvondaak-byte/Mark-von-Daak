#!/usr/bin/env python3
"""Baut die Kindle-Ausgabe von „Kopf schlägt Kalorien" als EPUB 3.

    python3 kopf/build/build_epub.py

Fließender Text wie bei Band 1 der Reihe: gebaut direkt aus kopf/kapitel/*.md,
ohne Seitenzahlen und Kopfzeilen — die Navigation übernimmt der Reader. Die
Bausteine (Paketdokument, Navigation, Markdown-Umsetzung, Prüfung) kommen aus
buch/build/build_epub.py. Eigen sind drei Dinge:

- **Kennung:** eine eigene UUID — mit der von Band 1 hielte Amazon beide
  Bücher für dasselbe.
- **Farben:** Nachtblau und Bernstein wie auf dem Umschlag statt des Grüns
  der Reihe.
- **Arbeitsteil:** Im E-Book kann man nicht schreiben. Der Einleitungstext
  von Teil IV sagt deshalb, wie man die Vorlagen trotzdem nutzt.

Dazu das Kindle-Titelbild: 1600 × 2560 Pixel (Seitenverhältnis 1,6, Amazons
Empfehlung), mit denselben Funktionen gesetzt wie der gedruckte Umschlag.
"""

import importlib.util
import sys
from pathlib import Path

import yaml
from PIL import Image

WURZEL = Path(__file__).resolve().parents[2]
KOPF = WURZEL / "kopf"
sys.path.insert(0, str(WURZEL / "buch" / "build"))

import build_epub as reihe  # noqa: E402
from build_docx import kapitel_laden  # noqa: E402

KINDLE_PX = (1600, 2560)

# Fest vergeben und über Auflagen hinweg stabil halten.
reihe.KENNUNG = "urn:uuid:587de3e0-789e-4e6c-b760-12503544b24d"

# Farbwelt des Umschlags: Nachtblau für Überschriften, Bernstein als Akzent,
# helles Blaugrau für Kästen. Auf Graustufendisplays bleiben alle Töne als
# unterscheidbare Grauwerte erhalten.
reihe.STIL_FLIESSEND = (reihe.STIL_FLIESSEND
                        .replace("#2F7A3E", "#1E2A38")
                        .replace("#6FA85E", "#C77A12")
                        .replace("#EEF4EA", "#EEF1F5"))

ARBEITSTEIL_DRUCK = (
    "Hier findest du die Vorlagen zu den Übungen aus diesem Buch. Du kannst direkt\n"
    "ins Buch schreiben oder die Seiten kopieren, wenn du eine Übung mehrmals machen\n"
    "willst. Schreib mit Bleistift — manche Antworten ändern sich, wenn du weiter\n"
    "bist.")
ARBEITSTEIL_EBOOK = (
    "Hier findest du die Vorlagen zu den Übungen aus diesem Buch. In einem E-Book "
    "kannst du nicht schreiben — übertrag die Tabellen deshalb in ein Notizbuch "
    "oder in eine Datei auf deinem Rechner. Die Spalten zeigen dir, was du "
    "jeweils festhältst. Wer lieber auf Papier arbeitet, findet alle Vorlagen "
    "auch in der gedruckten Ausgabe.")


def umschlag_modul():
    """Lädt kopf/build/build_cover.py unter eigenem Namen.

    Unter „build_cover" fände Python das Umschlagskript der Reihe in
    buch/build/ — das steht weiter vorn im Suchpfad.
    """
    pfad = KOPF / "build" / "build_cover.py"
    spec = importlib.util.spec_from_file_location("kopf_cover", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def kindle_cover_bauen(cfg, ziel):
    uc = umschlag_modul()
    breite, hoehe = KINDLE_PX
    titelbild = uc.titelbild_suchen()
    oben, unten = uc.FARBE["grund_oben"], uc.FARBE["grund_unten"]
    if titelbild:
        foto = Image.open(titelbild)
        oben, unten = uc.randfarbe(foto, "oben"), uc.randfarbe(foto, "unten")
    bild = uc.verlauf(breite, hoehe, oben, unten)
    if titelbild:
        uc.titelbild_einsetzen(bild, titelbild, 0, breite, ueberblendung=0)
    uc.vorderseite(bild, 0, 0, breite, hoehe, cfg, titelbild)
    bild.save(ziel, "JPEG", quality=92, optimize=True)
    return ziel


def main():
    cfg = yaml.safe_load((KOPF / "kopf.yaml").read_text(encoding="utf-8"))
    out = KOPF / "out"
    out.mkdir(exist_ok=True)

    umschlag = kindle_cover_bauen(cfg, out / "kindle-cover.jpg")

    kapitel = kapitel_laden(KOPF / "kapitel")
    teil4 = [k for k in kapitel if k["meta"].get("titel", "").startswith("Teil IV")]
    if len(teil4) != 1 or ARBEITSTEIL_DRUCK not in teil4[0]["text"]:
        raise SystemExit("Einleitung von Teil IV nicht gefunden — "
                         "ARBEITSTEIL_DRUCK an kopf/kapitel/50-teil-4.md angleichen.")
    teil4[0]["text"] = teil4[0]["text"].replace(ARBEITSTEIL_DRUCK,
                                                ARBEITSTEIL_EBOOK)

    ziel = out / f"{cfg['slug']}-kindle.epub"
    ziel, eintraege = reihe.band1_bauen(cfg, kapitel, umschlag, ziel)
    verzeichnis = sum(1 for e in eintraege if e["im_verzeichnis"])
    reihe.bericht("Kindle-Ausgabe — fließender Text", ziel,
                  f"{len(kapitel)} Kapitel, {verzeichnis} Navigationspunkte")
    groesse = Image.open(umschlag).size
    print(f"  → {umschlag.relative_to(WURZEL)}  ({groesse[0]} x {groesse[1]} px, "
          "Titelbild für KDP)")


if __name__ == "__main__":
    main()
