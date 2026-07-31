#!/usr/bin/env python3
"""Prüft jedes Rezept gegen die Regeln der Phase, in der es stehen soll.

    python3 rezepte/build/zutaten_check.py

Ein Rezeptbuch zu einem Ernährungskonzept ist nur so viel wert wie seine
Regeltreue. Ein einziges Rezept mit Zwiebeln an einem weißen Tag macht das
ganze Buch unglaubwürdig — und diesen Fehler übersieht man beim Korrekturlesen
zuverlässig. Deshalb prüft dieses Skript maschinell.

Geprüft wird je Tagesfarbe:

  weiss           nur Eiweiß, Fett, Kräuter und Gewürze. Kein Gemüse, kein
                  Obst, kein Salz, kein Zucker, keine Milchprodukte außer
                  dem Joghurt am Morgen.
  fruehstueck     Joghurt, Leinsamen, Sonnenblumenkerne, optional eine halbe
                  Eiweißportion. In der Aktivierungsphase kein Obst.
  gruen           wie weiss, zusätzlich erlaubtes Gemüse und eine Portion Obst.
  stabilisierung  zusätzlich Milchprodukte, Nüsse, Salz in Maßen, kleine
                  Mengen Kohlenhydrate.
  grundrezept     Gewürzmischungen, Dressings, Grundlagen.

Zusätzlich wird geprüft, ob die Eiweißangabe zur Tagesfarbe passt.
"""

import re
import sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]

# --- Verbote -----------------------------------------------------------------
# In jeder Phase außer roten Tagen tabu. Rote Tage haben keine Rezepte.
IMMER_VERBOTEN = {
    r"\bSalz\b(?!frei|arm|ersatz)": "Salz",
    r"\bMeersalz\b|\bSteinsalz\b|\bKräutersalz\b": "Salz",
    r"\bZucker\b(?!frei|ersatz)|\bHonig\b|\bAhornsirup\b|\bAgavendicksaft\b":
        "Zucker",
    r"\bZwiebel": "Zwiebeln (Frühlingszwiebeln sind erlaubt)",
    r"\bMais\b|\bKichererbse|\bLinsen\b|\bKidneybohne|\bweiße Bohne":
        "Hülsenfrüchte",
    r"\bErbsen\b": "Hülsenfrüchte",
    r"\bWeizen|\bNudeln\b|\bPasta\b|\bReis\b|\bCouscous\b|\bBulgur\b":
        "Getreide",
    r"\bHaferflocken\b|\bParniermehl\b|\bPaniermehl\b": "Getreide",
    r"\bBanane|\bAnanas\b|\bWeintraube|\bTraube\b|\bDattel": "zuckerreiches Obst",
    r"\bSchwein|\bSpeck\b|\bWurst\b|\bSchinken\b|\bBacon\b": "Schweinefleisch",
    r"\bgeräuchert": "Geräuchertes",
    r"\bCashew": "Cashewkerne",
    r"\bBalsamico\b": "Balsamico (zu viele Kohlenhydrate)",
    r"\bSonnenblumenöl\b|\bRapsöl\b|\bDistelöl\b|\bMaiskeimöl\b|\bErdnussöl\b":
        "ungeeignetes Öl",
    r"\bMargarine\b": "ungeeignetes Fett",
    r"\bAlkohol\b|\bWein\b(?!essig)|\bBier\b": "Alkohol",
    r"\bSüßstoff\b|\bAspartam\b|\bSucralose\b": "Süßstoff",
}

# Zusätzlich an weißen Tagen und beim Frühstück tabu.
OHNE_GEMUESE_VERBOTEN = {
    r"\bTomate|\bGurke\b|\bPaprika\b|\bZucchini\b|\bBrokkoli\b|\bBlumenkohl\b":
        "Gemüse gehört auf grüne Tage",
    r"\bSalat\b|\bSpinat\b|\bRucola\b|\bFenchel\b|\bSpargel\b|\bAubergine\b":
        "Gemüse gehört auf grüne Tage",
    r"\bChampignon|\bPilz|\bRadieschen\b|\bKohlrabi\b|\bSellerie\b":
        "Gemüse gehört auf grüne Tage",
    r"\bRosenkohl\b|\bGrünkohl\b|\bMangold\b|\bChicorée\b|\bArtischocke":
        "Gemüse gehört auf grüne Tage",
    r"\bApfel\b|\bBirne\b|\bBeere|\bErdbeer|\bHimbeer|\bHeidelbeer":
        "Obst gehört auf grüne Tage",
    r"\bPfirsich\b|\bAprikose\b|\bGrapefruit\b|\bPapaya\b|\bRhabarber\b":
        "Obst gehört auf grüne Tage",
}

# Erst ab der Stabilisierungsphase erlaubt.
ERST_AB_STABILISIERUNG = {
    # Wurzel- und Knollengemüse: in der Aktivierungsphase tabu, ab der
    # Stabilisierung wieder erlaubt — Stärkehaltiges nur bis 30 g je Mahlzeit.
    r"\bKartoffel|\bSüßkartoffel|\bTopinambur\b":
        "Kartoffeln erst ab der Stabilisierungsphase, dann bis 30 g",
    r"\bKarotte|\bMöhre|\bPastinake|\bSchwarzwurzel\b":
        "Wurzelgemüse erst ab der Stabilisierungsphase",
    r"\bRote Bete\b|\bRote Beete\b":
        "Rote Bete erst ab der Stabilisierungsphase",
    r"\bKürbis\b(?!kern)": "Kürbis erst ab der Stabilisierungsphase",
    r"\bLauch\b|\bPorree\b":
        "Lauch erst ab der Stabilisierungsphase (Frühlingszwiebeln sind erlaubt)",
    r"\bIngwer\b|\bSellerie\b|\bRotkohl\b|\bBlaukraut\b":
        "erst ab der Stabilisierungsphase",
    r"\bKäse\b|\bHartkäse\b|\bMozzarella\b|\bFrischkäse\b|\bParmesan\b":
        "Milchprodukte erst ab der Stabilisierungsphase",
    r"\bQuark\b|\bMascarpone\b|\bSahne\b|\bCrème fraîche\b|\bSchmand\b":
        "Milchprodukte erst ab der Stabilisierungsphase",
    r"\bButter\b(?!milch)|\bGhee\b": "Butter erst ab der Stabilisierungsphase",
    r"\bWalnuss|\bHaselnuss|\bParanuss|\bPistazie|\bPekannuss":
        "Nüsse außer Mandeln erst ab der Stabilisierungsphase",
    r"\bKürbiskern|\bChiasamen\b|\bMacadamia|\bPinienkern|\bHanfsamen\b":
        "Kerne erst ab der Stabilisierungsphase",
    r"\bErythrit\b|\bStevia\b": "Süßungsmittel erst ab der Stabilisierungsphase",
    r"\bBrot\b|\bBrötchen\b": "Brot erst ab der Stabilisierungsphase",
    r"\bWhey\b|\bMolkenprotein\b": "Molkenprotein erst ab der Stabilisierungsphase",
}

# Beim Frühstück in der Aktivierungsphase zusätzlich tabu.
FRUEHSTUECK_VERBOTEN = {
    r"\bObst\b": "Kein Obst in den Joghurt der Aktivierungsphase",
}

REGELN = {
    "weiss": [IMMER_VERBOTEN, OHNE_GEMUESE_VERBOTEN, ERST_AB_STABILISIERUNG],
    "fruehstueck": [IMMER_VERBOTEN, OHNE_GEMUESE_VERBOTEN,
                    ERST_AB_STABILISIERUNG, FRUEHSTUECK_VERBOTEN],
    "gruen": [IMMER_VERBOTEN, ERST_AB_STABILISIERUNG],
    "stabilisierung": [IMMER_VERBOTEN],
    "grundrezept": [IMMER_VERBOTEN, ERST_AB_STABILISIERUNG],
}

# Ausnahmen, die die Muster sonst fälschlich treffen würden.
AUSNAHMEN = [
    r"ohne Salz", r"salzfrei", r"salzfreie", r"statt Salz", r"kein Salz",
    r"Frühlingszwiebel", r"Weinessig", r"Weißweinessig", r"Rotweinessig",
    r"Zuckerersatz", r"ohne Zucker", r"zuckerfrei",
    r"Mandel",  # Mandeln sind in der Aktivierungsphase erlaubt
]


def _entschaerfen(text):
    """Entfernt Formulierungen, die ein Verbot ausdrücklich verneinen."""
    for muster in AUSNAHMEN:
        text = re.sub(muster, "", text, flags=re.IGNORECASE)
    return text


def rezept_pruefen(rezept):
    farbe = rezept.get("tagesfarbe")
    if farbe not in REGELN:
        return [(rezept["name"], f"unbekannte Tagesfarbe: {farbe}")]

    text = _entschaerfen(" | ".join(rezept["zutaten"]))
    treffer = []
    for regelsatz in REGELN[farbe]:
        for muster, grund in regelsatz.items():
            fund = re.search(muster, text, re.IGNORECASE)
            if fund:
                treffer.append((rezept["name"],
                                f"„{fund.group(0).strip()}“ — {grund}"))
    return treffer


def struktur_pruefen(rezept):
    fehlend = [f for f in ("name", "tagesfarbe", "portionen", "zutaten",
                           "schritte") if not rezept.get(f)]
    if fehlend:
        return [(rezept.get("name", "?"),
                 f"Pflichtfelder fehlen: {', '.join(fehlend)}")]

    treffer = []
    if rezept["tagesfarbe"] in ("weiss", "gruen") and not rezept.get("eiweiss_g"):
        treffer.append((rezept["name"],
                        "Eiweißangabe fehlt — bei Hauptmahlzeiten Pflicht"))
    if rezept.get("eiweiss_g") and rezept["tagesfarbe"] in ("weiss", "gruen"):
        # Untergrenze 12 g: Das Konzept führt zwei Eier als vollwertige
        # Eiweißportion, und die liefern rund 12 g. Eine höhere Schwelle
        # würde Eiergerichte aussortieren, die konzeptkonform sind.
        if rezept["eiweiss_g"] < 12:
            treffer.append((rezept["name"],
                            f"nur {rezept['eiweiss_g']} g Eiweiß — zu wenig "
                            "für eine Hauptmahlzeit bei 80 kg"))
    return treffer


def main():
    verzeichnis = WURZEL / "rezepte" / "rezepte"
    dateien = sorted(verzeichnis.glob("*.yaml"))
    if not dateien:
        raise SystemExit(f"Keine Rezeptdateien in {verzeichnis}.")

    alle, fehler = 0, []
    for pfad in dateien:
        daten = yaml.safe_load(pfad.read_text(encoding="utf-8"))
        for rezept in daten.get("rezepte", []):
            alle += 1
            for name, grund in struktur_pruefen(rezept):
                fehler.append((pfad.name, name, grund))
            for name, grund in rezept_pruefen(rezept):
                fehler.append((pfad.name, name, grund))

    print(f"Zutatenprüfung über {alle} Rezepte in {len(dateien)} Dateien")
    if fehler:
        print("-" * 70)
        for datei, name, grund in fehler:
            print(f"  {datei}  ·  {name}")
            print(f"      {grund}")
        print(f"\n{len(fehler)} Regelverstoß/Regelverstöße gefunden.")
        return 1

    print("\nAlle Rezepte halten die Regeln ihrer Phase ein.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
