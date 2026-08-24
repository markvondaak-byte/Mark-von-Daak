#!/usr/bin/env python3
"""Prüft die Kapitel beider Bände auf unzulässige Gesundheitsaussagen.

    python3 buch/build/claim_check.py

Hintergrund: Die Health-Claims-Verordnung (EG) Nr. 1924/2006 und das
Heilmittelwerberecht verbieten krankheitsbezogene Aussagen und nicht
zugelassene Wirkversprechen. Die Original-Anleitung, auf der dieses Buch
inhaltlich fußt, enthält eine Reihe solcher Formulierungen — sie dürfen in
einer verkauften Publikation nicht auftauchen.

Zwei Stufen:

  FEHLER   Formulierungen, die nirgends stehen dürfen (außer in den
           ausdrücklich freigegebenen Rechtskapiteln). Exit-Code 1.
  HINWEIS  Krankheitsbegriffe. Sie sind als Warnhinweis zulässig
           ("bei Diabetes bitte ärztlich abklären"), als Anwendungsgebiet
           dagegen nicht. Muss ein Mensch beurteilen. Kein Exit-Code.

Das Skript ersetzt keine juristische Prüfung.
"""

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]

# Kapitel, in denen Krankheits- und Warnbegriffe stehen müssen.
FREIGEGEBEN = {
    "02-bitte-zuerst-lesen.md",
    "62-in-eigener-sache.md",
    "64-hinweise-haftung.md",
    "90-rechtliches.md",
    # „Der Darm im Gleichgewicht": Rechtskapitel und das eine Kapitel, dessen
    # Zweck es ist, Krankheitszeichen zu benennen und zum Arzt zu schicken.
    # Ohne diese Ausnahme kann das Buch die Warnung nicht aussprechen, um
    # derentwillen es geschrieben ist.
    "002-bitte-zuerst-lesen.md",
    "303-wann-zum-arzt.md",
    "901-hinweise-haftung.md",
}

# Nie zulässig — Wirkversprechen, Heilaussagen, Werbesuperlative.
FEHLER = {
    r"entgift\w*": "Entgiftungsaussage",
    r"entschlack\w*": "Entschlackungsaussage",
    r"\bAltlast\w*": "Entgiftungsmetapher aus der Vorlage",
    r"\bdetox\w*": "Entgiftungsaussage",
    r"heilt\b|\bheilend\w*|\bHeilung\b": "Heilaussage",
    # „Krebs" nur in Krankheitsbedeutung treffen — als Krustentier steht das
    # Wort völlig zu Recht in der Meeresfrüchte-Liste.
    (r"Krebs(erkrankung|risiko|zellen|leiden)\w*"
     r"|(Magen|Darm|Prostata|Brust|Lungen)krebs"
     r"|gegen Krebs"): "Krankheitsbezug, unzulässig",
    r"\bTumor\w*": "Krankheitsbezug, unzulässig",
    r"\bInfarkt\w*": "Krankheitsbezug, unzulässig",
    r"Cholesterin\w*": "Aussage zu Blutfettwerten",
    r"\blindert\b|\bLinderung\b": "Wirkversprechen",
    r"\bvorbeug\w*": "Präventionsaussage",
    r"entzündungshemmend\w*": "Wirkversprechen",
    r"\bZuckersucht\b": "Suchtbegriff aus der Vorlage",
    r"Stoffwechselalter": "nicht belegbare Aussage",
    r"\bverjüng\w*": "nicht belegbare Aussage",
    r"jung essen": "nicht belegbare Aussage aus der Vorlage",
    r"\bgarantiert\b": "Erfolgsversprechen",
    # Nicht die Redewendung „kein Wunder", sondern die Werbebehauptung.
    (r"Wundermittel|Wunderwirkung|Wunderkur"
     r"|wirkt Wunder|wahre Wunder"): "Werbesuperlativ",
    r"stärkt (das|dein) Immunsystem": "nicht zugelassene Wirkaussage",
    r"(senkt|reduziert) das Risiko": "Präventionsaussage",
    r"\bkiloweise\b|\bPfunde purzeln\b": "Erfolgsversprechen",
}

# Zulässig als Warnhinweis, unzulässig als Anwendungsgebiet.
HINWEIS = {
    r"\bDiabet\w*": "Krankheitsbegriff — nur als Warnhinweis zulässig",
    # Darmthemen: Begriffe, an denen ein Ratgeber nicht vorbeikommt, die aber
    # nur als Abgrenzung stehen dürfen („das ist ärztliche Sache"), nie als
    # Anwendungsgebiet („dieses Buch hilft bei …").
    r"\bReizdarm\w*": "Krankheitsbegriff",
    r"\bZöliakie\b": "Krankheitsbegriff",
    r"Morbus Crohn|\bColitis\b|chronisch-entzündlich\w*": "Krankheitsbegriff",
    r"\bDivertik\w*": "Krankheitsbegriff",
    r"\bHelicobacter\b": "Krankheitsbegriff",
    r"\bLeaky.Gut\b": "Begriff ohne anerkannte Krankheitsdefinition",
    r"\bNierenerkrank\w*|\bNiereninsuffizienz\b": "Krankheitsbegriff",
    r"\bHerzerkrank\w*|Herz-Kreislauf-Erkrank\w*": "Krankheitsbegriff",
    r"\bPhenylketonurie\b": "Krankheitsbegriff",
    r"\bEssstörung\w*": "Krankheitsbegriff",
    r"\bAllergi\w*": "Krankheitsbegriff",
    r"\bMigräne\b": "Krankheitsbegriff",
}

QUELLEN = [
    WURZEL / "buch" / "kapitel",
    WURZEL / "workbook" / "rahmen",
    WURZEL / "darm" / "kapitel",
]


def pruefen(pfade):
    fehler, hinweise = [], []
    for pfad in pfade:
        freigegeben = pfad.name in FREIGEGEBEN
        for nummer, zeile in enumerate(
                pfad.read_text(encoding="utf-8").splitlines(), 1):
            for muster, grund in FEHLER.items():
                for treffer in re.finditer(muster, zeile, re.IGNORECASE):
                    if freigegeben:
                        continue
                    fehler.append((pfad, nummer, treffer.group(0), grund, zeile))
            for muster, grund in HINWEIS.items():
                for treffer in re.finditer(muster, zeile, re.IGNORECASE):
                    if freigegeben:
                        continue
                    hinweise.append((pfad, nummer, treffer.group(0), grund, zeile))
    return fehler, hinweise


def ausgeben(titel, treffer):
    print(f"\n{titel} ({len(treffer)})")
    print("-" * 70)
    for pfad, nummer, wort, grund, zeile in treffer:
        ort = pfad.relative_to(WURZEL)
        print(f'  {ort}:{nummer}  „{wort}“ — {grund}')
        print(f"      {zeile.strip()[:100]}")


def main():
    pfade = sorted(p for quelle in QUELLEN if quelle.is_dir()
                   for p in quelle.glob("*.md"))
    if not pfade:
        raise SystemExit("Keine Kapiteldateien gefunden.")

    fehler, hinweise = pruefen(pfade)
    print(f"HCVO-Prüfung über {len(pfade)} Dateien")

    if hinweise:
        ausgeben("HINWEIS — im Warnkontext zulässig, bitte prüfen", hinweise)
    if fehler:
        ausgeben("FEHLER — muss entfernt werden", fehler)
        print(f"\n{len(fehler)} unzulässige Formulierung(en) gefunden.")
        return 1

    print("\nKeine unzulässigen Formulierungen gefunden.")
    if hinweise:
        print(f"{len(hinweise)} Krankheitsbegriff(e) im Warnkontext — "
              "einmal gegenlesen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
