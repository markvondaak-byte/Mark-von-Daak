#!/usr/bin/env python3
"""Erzeugt die Daten der App aus den Quellen der drei Bände.

    python3 app/build/build_app_daten.py

Der Punkt dieses Skripts: Die App darf keine eigene Kopie der Inhalte haben.
Der Wochenplan steht in workbook/build/wochenplan.py, die Rezepte in
rezepte/rezepte/*.yaml, das Wissen in buch/kapitel/*.md — und genau von dort
kommen die JSON-Dateien. Ändert sich ein Rezept im Buch, ändert es sich nach
einem Lauf dieses Skripts auch in der App.

Ergebnis:
    app/daten/programm.json   12 Wochen, 84 Tage mit Tagesfarben
    app/daten/rezepte.json    alle Rezepte samt Zutaten und Schritten
    app/daten/wissen.json     Nachschlageteil aus den Buchkapiteln
"""

import json
import re
import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "workbook" / "build"))
import wochenplan as wp  # noqa: E402

ZIEL = WURZEL / "app" / "daten"

# Welche Buchkapitel in den Wissensteil der App wandern. Bewusst eine
# Auswahl: Die App ist Nachschlagewerk, nicht das ganze Buch.
WISSENSKAPITEL = [
    ("21-die-vier-phasen.md", "Die vier Phasen"),
    ("22-die-tagesfarben.md", "Die Tagesfarben"),
    ("23-die-grundregeln.md", "Die Grundregeln"),
    ("33-der-weisse-tag.md", "Der weiße Tag"),
    ("35-der-gruene-tag.md", "Der grüne Tag"),
    ("34-eiweissmenge.md", "Eiweißmenge berechnen"),
    ("41-lebensmittel.md", "Lebensmittel"),
    ("42-was-wegbleibt.md", "Was wegbleibt"),
    ("51-die-ersten-tage.md", "Die ersten Tage"),
    ("52-wenn-die-waage-steht.md", "Wenn die Waage steht"),
    ("53-haeufige-fragen.md", "Häufige Fragen"),
    ("64-hinweise-haftung.md", "Wichtige Hinweise"),
]


def programm_bauen():
    wochen = []
    for woche in wp.wochen():
        wochen.append({
            "nummer": woche["nummer"],
            "phase": woche["phase"],
            "phaseName": woche["phase_name"],
            "fokusTitel": woche["fokus_titel"],
            "fokusText": woche["fokus_text"],
            "planbar": woche["vorschlag"],
            "tage": [{
                "nummer": tag["nummer"],
                "wochentag": tag["wochentag"],
                "farbe": tag["farbe"],
            } for tag in woche["tage"]],
        })
    return {
        "wochen": wochen,
        "phasen": {s: {"name": d["name"], "wochen": list(d["wochen"])}
                   for s, d in wp.PHASEN.items()},
        "verteilung": wp.verteilung(),
    }


def rezepte_bauen():
    quelle = WURZEL / "rezepte" / "rezepte"
    teile, alle = [], []
    for pfad in sorted(quelle.glob("*.yaml")):
        daten = yaml.safe_load(pfad.read_text(encoding="utf-8"))
        teile.append({"id": pfad.stem, "titel": daten["teil"]})
        for nummer, rezept in enumerate(daten.get("rezepte", [])):
            alle.append({
                "id": f"{pfad.stem}-{nummer}",
                "teil": daten["teil"],
                "name": rezept["name"],
                "farbe": rezept["tagesfarbe"],
                "portionen": rezept["portionen"],
                "zeit": rezept.get("zeit_min"),
                "eiweiss": rezept.get("eiweiss_g"),
                "zutaten": rezept["zutaten"],
                "schritte": rezept["schritte"],
                "tipp": rezept.get("tipp"),
            })
    return {"teile": teile, "rezepte": alle}


def markdown_zu_bloecken(text):
    """Reduziert ein Kapitel auf eine für die App brauchbare Struktur.

    Absichtlich einfach gehalten: Überschriften, Absätze, Listen, Tabellen und
    Hinweiskästen. Alles, was die App darstellen können muss — mehr nicht.
    """
    bloecke = []
    zeilen = text.splitlines()
    i = 0
    while i < len(zeilen):
        zeile = zeilen[i].rstrip()

        if not zeile.strip():
            i += 1
            continue

        if zeile.startswith("# "):
            bloecke.append({"typ": "h1", "text": zeile[2:].strip()})
            i += 1
        elif zeile.startswith("## "):
            bloecke.append({"typ": "h2", "text": zeile[3:].strip()})
            i += 1
        elif zeile.startswith("### "):
            bloecke.append({"typ": "h3", "text": zeile[4:].strip()})
            i += 1
        elif zeile.startswith("> "):
            kasten, titel = [], None
            while i < len(zeilen) and zeilen[i].startswith(">"):
                inhalt = zeilen[i].lstrip("> ").strip()
                if inhalt:
                    if titel is None and inhalt.endswith(":"):
                        titel = inhalt.rstrip(":")
                    else:
                        kasten.append(inhalt)
                i += 1
            bloecke.append({"typ": "kasten", "titel": titel,
                            "text": " ".join(kasten)})
        elif zeile.startswith("|"):
            tabelle = []
            while i < len(zeilen) and zeilen[i].startswith("|"):
                felder = [f.strip() for f in zeilen[i].strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", f) for f in felder):
                    tabelle.append(felder)
                i += 1
            if tabelle:
                bloecke.append({"typ": "tabelle", "kopf": tabelle[0],
                                "zeilen": tabelle[1:]})
        elif re.match(r"^[-*] ", zeile):
            punkte = []
            while i < len(zeilen) and re.match(r"^[-*] ", zeilen[i].rstrip()):
                punkte.append(zeilen[i].rstrip()[2:].strip())
                i += 1
            bloecke.append({"typ": "liste", "punkte": punkte})
        elif re.match(r"^\d+\. ", zeile):
            punkte = []
            while i < len(zeilen) and re.match(r"^\d+\. ", zeilen[i].rstrip()):
                punkte.append(re.sub(r"^\d+\.\s*", "", zeilen[i].rstrip()))
                i += 1
            bloecke.append({"typ": "nummern", "punkte": punkte})
        else:
            absatz = []
            while (i < len(zeilen) and zeilen[i].strip()
                   and not zeilen[i].startswith(("#", ">", "|", "- ", "* "))
                   and not re.match(r"^\d+\. ", zeilen[i])):
                absatz.append(zeilen[i].strip())
                i += 1
            text_absatz = " ".join(absatz)
            if "{{" not in text_absatz:
                bloecke.append({"typ": "absatz", "text": text_absatz})
    return bloecke


def wissen_bauen():
    quelle = WURZEL / "buch" / "kapitel"
    kapitel = []
    for datei, titel in WISSENSKAPITEL:
        pfad = quelle / datei
        if not pfad.exists():
            print(f"  Warnung: {datei} fehlt, wird übersprungen")
            continue
        roh = pfad.read_text(encoding="utf-8")
        if roh.startswith("---"):
            roh = roh.split("---", 2)[2]
        kapitel.append({
            "id": pfad.stem,
            "titel": titel,
            "bloecke": markdown_zu_bloecken(roh.strip()),
        })
    return {"kapitel": kapitel}


def schreiben(name, daten):
    ZIEL.mkdir(parents=True, exist_ok=True)
    pfad = ZIEL / name
    pfad.write_text(json.dumps(daten, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    groesse = pfad.stat().st_size / 1024
    print(f"  {name:18s} {groesse:6.1f} KB")
    return pfad


def main():
    print("App-Daten aus den Quellen der drei Bände:")
    programm = programm_bauen()
    rezepte = rezepte_bauen()
    wissen = wissen_bauen()

    schreiben("programm.json", programm)
    schreiben("rezepte.json", rezepte)
    schreiben("wissen.json", wissen)

    tage = sum(len(w["tage"]) for w in programm["wochen"])
    print(f"\n{len(programm['wochen'])} Wochen mit {tage} Tagen, "
          f"{len(rezepte['rezepte'])} Rezepte, "
          f"{len(wissen['kapitel'])} Wissenskapitel")


if __name__ == "__main__":
    main()
