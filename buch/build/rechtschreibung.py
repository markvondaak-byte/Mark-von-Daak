#!/usr/bin/env python3
"""Rechtschreibprüfung über alle Quelltexte aller Bücher.

    pip install pyspellchecker
    python3 buch/build/rechtschreibung.py

Geprüft werden die **Quellen**, nicht die PDFs: In den Markdown- und
YAML-Dateien lässt sich ein Fund direkt korrigieren, im PDF nicht.

Zur Genauigkeit, offen gesagt: Der Prüfer arbeitet mit einer Wortliste, nicht
mit einer Grammatik des Deutschen. Zusammensetzungen wie „Eiweißmenge" oder
„Stabilisierungsphase" stehen in keiner Liste, sind aber richtig. Deshalb:

1. Wörter aus der Liste gelten als richtig.
2. Was nicht drinsteht, wird zerlegt: Besteht ein Wort aus bekannten Teilen
   (mit oder ohne Fugen-s), gilt es als Zusammensetzung und damit als richtig.
   Das fängt den größten Teil der Fehlalarme ab.
3. Was dann noch übrig bleibt, steht in FACHWORTE — geprüfte Begriffe des
   Projekts — oder wird gemeldet.

Was der Prüfer **nicht** findet: Wörter, die es gibt, aber falsch am Platz
sind („das" statt „dass", „wieder" statt „wider"). Dafür gibt es am Ende
zusätzlich ein paar gezielte Suchen.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]

QUELLEN = [
    ("Band 1", "buch/kapitel", "*.md"),
    ("Band 2", "workbook/rahmen", "*.md"),
    ("Band 3", "rezepte/rahmen", "*.md"),
    ("Band 3", "rezepte/rezepte", "*.yaml"),
    ("KI-Buch", "ki/kapitel", "*.md"),
    ("Umschlag", "buch/cover", "klappentext.md"),
    ("Umschlag", "workbook/cover", "klappentext.md"),
    ("Umschlag", "rezepte/cover", "klappentext.md"),
    ("Umschlag", "ki/cover", "klappentext.md"),
]

# Fachbegriffe des KI-Buches: englische Bezeichnungen ohne deutsche
# Entsprechung, Eigennamen und Wortbildungen, die eine Wortliste nicht kennt.
# Getrennt geführt, weil sie mit der Stoffwechsel-Reihe nichts zu tun haben.
KI_FACHWORTE = {
    "llm", "token", "transformer", "transformers", "deep", "learning",
    "chatbot", "cloud", "app", "audio", "screening", "loitering",
    "science", "fiction", "and", "stop", "dartmouth", "colorado",
    "robotik", "onkologie", "dermatologie", "sepsis", "neurons",
    "begleiterkrankungen", "beipackzettel", "untertitelung",
    "sehbeeinträchtigung", "hörbeeinträchtigung", "sprech",
    "lernschwierigkeiten", "lernschwelle", "lerngegenstand", "lernzeiten",
    "erklärwerkzeug", "programmierunterricht", "programmierberufe",
    "schulalltag", "lehrstücke", "wegbeschreibung", "belegbarkeit",
    "nachweisbarkeit", "beurteilbarkeit", "erklärbarkeit",
    "versicherbarkeit", "kuratierung", "prüfkapazität", "prüffrage",
    "prüfschritt", "prüfschritte", "prüfpflichten", "aufsichts",
    "auskunfts", "dokumentations", "genauigkeits", "vorpriorisierung",
    "vorsortieren", "vorsortiert", "altsysteme", "abkündigung",
    "abgekündigt", "bezahlschranken", "bewerter", "förderprogramme",
    "fördermittel", "kontrollbruch", "kontrollverlust", "rückprall",
    "rückrechnen", "rückrechnungsverfahren", "rüstungskontrollverträge",
    "dekarbonisierung", "elektroschrott", "gaskraftwerke", "ausbringung",
    "lieferverkehren", "notbremsassistent", "totwinkelwarnung",
    "heizungs", "lüftungs", "schwingungs", "bewegungs", "kleinteilig",
    "verschriftlichung", "eingeschliffen", "jahrzehntealt", "körperlos",
    "unwirtschaftlich", "verkraftbar", "umverteilt", "umschlägt",
    "auszuspielen", "beschicken", "aggregiert", "aggregierte", "flacht",
    "gestuft", "existenzen", "kennwörter", "lektorat", "warnern",
    "naheliegendste", "spekulativste", "fünftens", "unüberwachtes", "ern",
    "rebound", "effect",
}

# Begriffe, die richtig sind, aber in keiner Wortliste stehen: Marken,
# Fachbegriffe des Konzepts, Zutaten, Eigennamen.
FACHWORTE = {
    "cellreset", "fitline", "pm", "international", "daak", "wolfsburg",
    "rabenbergstraße", "icloud", "ustid", "hcvo",
    "stoffwechselreset", "lifestyletag", "lifestylephase", "vitalcheck",
    "aktivierungsphase", "stabilisierungsphase", "vorbereitungsphase",
    "tagesfarbe", "tagesfarben", "tagestyp", "eiweißmenge", "eiweißgehalt",
    "eiweißgerichte", "eiweißreich", "eiweißreiche", "eiweißreichen",
    "eiweißquellen", "eiweißbedarf", "grundumsatz", "fettstoffwechsel",
    "kohlenhydratarm", "kohlenhydratarme", "makronährstoffe",
    "seitan", "tempeh", "lupine", "lupinenschnitzel", "erythrit",
    "chiasamen", "kokosöl", "leinöl", "leinsamen", "ghee", "quark",
    "mandelmehl", "kokosmehl", "hüttenkäse", "harzer", "skyr",
    "chinakohl", "chinakohlsalat", "pak", "choi", "mangold", "grünkohl",
    "kohlrabi", "rucola", "fenchel", "fenchelsalat", "radieschen",
    "radieschensalat", "aubergine", "auberginenauflauf", "zucchini",
    "zucchininudeln", "blumenkohlreis", "rosenkohl", "champignonpfanne",
    "butterfisch", "kabeljau", "makrele", "garnelen", "tintenfischringe",
    "meeresfrüchte", "geflügelhack", "putengeschnetzeltes", "hackbällchen",
    "hähnchenfrikadellen", "thunfischfrikadellen", "geflügelspieße",
    "eiersalat", "kräuteromelett", "trinkjoghurt", "probiotisch",
    "probiotischer", "probiotischen", "probiotische",
    "kurkuma", "chiliflocken", "kreuzkümmel", "paprikapulver",
    "apfelessig", "weißweinessig", "rotweinessig", "maltodextrin",
    "hefeextrakt", "dinkelkleber", "zöliakie", "vergine",
    "kdp", "epub", "asin", "isbn", "dpi",
}

# Häufige Verwechslungen, die eine Wortliste nicht sieht. Jeder Treffer wird
# nur gemeldet, nicht bewertet — entschieden wird beim Lesen.
STOLPERSTELLEN = [
    (r"\bdas\s+(?:du|Sie|er|sie|es|man|ich|wir)\s+\w+st?\b",
     "'das' vor Personalpronomen - oft muss dort 'dass' stehen"),
    (r"\bseit\s+(?:du|Sie|ihr)\b", "'seit' statt 'seid'?"),
    (r"\bwieder\s+(?:sprechen|spiegeln|legen)", "'wieder' statt 'wider'?"),
    (r"\b(\w{3,})\s+\1\b", "Wort doppelt"),
    (r"\s+[,.;:!?]", "Leerzeichen vor Satzzeichen"),
    (r"[a-zäöüß],[A-Za-zÄÖÜ]", "Leerzeichen nach Komma fehlt"),
    (r"[a-zäöüß]\.[A-ZÄÖÜ]", "Leerzeichen nach Punkt fehlt"),
    (r"\bin\s+dem\s+Maße\b", "'in dem Maße' - gemeint 'in dem Masse'?"),
]


def pruefe_typo(name, bedingung, detail=""):
    print(f"  [{'OK  ' if bedingung else 'FEHL'}] {name}"
          + (f"  — {detail}" if detail else ""))


def texte_sammeln():
    """Liest die Quellen und gibt (Band, Datei, Zeilennummer, Zeile) zurück."""
    zeilen = []
    for band, ordner, muster in QUELLEN:
        pfad = WURZEL / ordner
        if not pfad.exists():
            continue
        for datei in sorted(pfad.glob(muster)):
            for nummer, zeile in enumerate(
                    datei.read_text(encoding="utf-8").splitlines(), 1):
                zeilen.append((band, datei.relative_to(WURZEL), nummer, zeile))
    return zeilen


def pruefbar(zeile):
    """Entfernt, was keine Prosa ist: Auszeichnung, Marker, Zahlen, Code."""
    zeile = re.sub(r"\{\{[A-ZÄÖÜ_]+\}\}", " ", zeile)
    zeile = re.sub(r"`[^`]*`", " ", zeile)
    zeile = re.sub(r"https?://\S+|\S+@\S+", " ", zeile)
    zeile = re.sub(r"[*_#>|\[\]()\"„“”‚‘’»«]", " ", zeile)
    zeile = re.sub(r"\b\d+[.,]?\d*\b", " ", zeile)
    return zeile


def zusammensetzung(wort, bekannt):
    """Prüft, ob sich das Wort aus zwei bekannten Teilen zusammensetzt.

    Deutsch bildet Komposita frei; eine Wortliste kann sie nicht alle
    enthalten. Wer das ignoriert, bekommt bei einem deutschen Text mehr
    Fehlalarme als Text.
    """
    if len(wort) < 8:
        return False
    for schnitt in range(4, len(wort) - 3):
        links, rechts = wort[:schnitt], wort[schnitt:]
        if links in bekannt or links.rstrip("s") in bekannt:
            if rechts in bekannt or zusammensetzung(rechts, bekannt):
                return True
        # Fugen-s
        if links.endswith("s") and links[:-1] in bekannt:
            if rechts in bekannt or zusammensetzung(rechts, bekannt):
                return True
    return False


def main():
    try:
        from spellchecker import SpellChecker
    except ImportError:
        raise SystemExit("pyspellchecker fehlt: pip install pyspellchecker")

    pruefer = SpellChecker(language="de")
    bekannt = set(pruefer.word_frequency.dictionary)
    bekannt |= FACHWORTE | KI_FACHWORTE

    zeilen = texte_sammeln()
    print(f"{len(zeilen)} Zeilen aus {len({z[1] for z in zeilen})} Dateien\n")

    verdacht = defaultdict(list)
    woerter_gesamt = 0
    for band, datei, nummer, roh in zeilen:
        # Akzentbuchstaben gehören ins Wort: Ohne sie zerfällt „Chicorée" in
        # „Chicor" und „e" und wird als Fehler gemeldet.
        for wort in re.findall(r"[^\W\d_]+(?:-[^\W\d_]+)*",
                               pruefbar(roh)):
            woerter_gesamt += 1
            teile = wort.split("-")
            for teil in teile:
                klein = teil.lower()
                if len(klein) < 3 or klein in bekannt:
                    continue
                if zusammensetzung(klein, bekannt):
                    continue
                verdacht[teil].append((band, datei, nummer))

    print(f"{woerter_gesamt} Wörter geprüft, "
          f"{len(verdacht)} verschiedene Wörter unbekannt\n")

    print("=" * 70)
    print("ZU PRÜFEN — nach Häufigkeit, seltene zuerst")
    print("=" * 70)
    for wort, stellen in sorted(verdacht.items(), key=lambda e: len(e[1])):
        # Vorschläge nur für kurze Wörter: correction() prüft alle Varianten
        # mit ein bis zwei Änderungen, und das dauert bei langen deutschen
        # Zusammensetzungen Sekunden — für ein Wort, zu dem es ohnehin keinen
        # sinnvollen Vorschlag gibt.
        vorschlag = (pruefer.correction(wort.lower())
                     if len(wort) <= 11 else None)
        hinweis = (f"   vielleicht: {vorschlag}"
                   if vorschlag and vorschlag != wort.lower() else "")
        band, datei, nummer = stellen[0]
        mehr = f" (+{len(stellen) - 1})" if len(stellen) > 1 else ""
        print(f"{wort:28s} {datei}:{nummer}{mehr}{hinweis}")

    print("\n" + "=" * 70)
    print("TYPOGRAFIE")
    print("=" * 70)
    volltext = "\n".join(z[3] for z in zeilen)
    auf, zu = volltext.count("„"), volltext.count("“")
    pruefe_typo("Deutsche Anführungszeichen paarig", auf == zu,
                f"{auf} öffnende, {zu} schließende")
    # Ein gerades " in deutscher Prosa ist fast immer ein nicht geschlossenes
    # „…“ — genau das stand hier 63-mal, bis es jemand nachgezählt hat.
    gerade = sum(1 for band, datei, nummer, zeile in zeilen
                 if '"' in zeile and not zeile.lstrip().startswith("teil:"))
    pruefe_typo("Keine geraden Anführungszeichen in der Prosa", gerade == 0,
                f"{gerade} Zeilen")

    print("\n" + "=" * 70)
    print("STOLPERSTELLEN — Wörter, die es gibt, aber falsch stehen könnten")
    print("=" * 70)
    gefunden = 0
    for muster, beschreibung in STOLPERSTELLEN:
        if beschreibung is None:
            continue
        for band, datei, nummer, roh in zeilen:
            if roh.lstrip().startswith(("|", "`", "    ")):
                continue
            for treffer in re.finditer(muster, roh):
                gefunden += 1
                stelle = roh[max(0, treffer.start() - 35):treffer.end() + 35]
                print(f"{datei}:{nummer}  {beschreibung}")
                print(f"    … {stelle.strip()} …")
    if not gefunden:
        print("keine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
