#!/usr/bin/env python3
"""FitLine-Katalog (kataloge/fitline.yaml) aus dem offiziellen Shop neu erzeugen.

    python3 rechnungen/kataloge/fitline_aktualisieren.py            # live abrufen
    python3 rechnungen/kataloge/fitline_aktualisieren.py roh.json   # aus gespeicherter Abfrage

Übernimmt je Produkt: Artikelnummer, Name, Inhalt, Endkundenpreis (brutto) und
den Steuersatz, den FitLine selbst angibt. Zeigt an, welche Preise sich
gegenüber dem bisherigen Katalog geändert haben.
"""

import datetime as dt
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import yaml

HIER = Path(__file__).resolve().parent
ZIEL = HIER / "fitline.yaml"

# Kurze Namen für häufige Produkte (zusätzlich zu den automatischen Schlüsseln)
ALIASE = {
    "optimal-set": "9700977",          # Optimal-Set (PowerCocktail + Restorate)
    "restorate": "0702037",            # Restorate Citrus
    "activize": "0708054",             # Activize Oxyplus
    "omega-3": "0712067",
    "omega-3-plus": "0712073",
    "q10": "0712066",
    "heart-duo": "0712063",
    "lutein": "0712062",
    "topshape": "0704031",
    "zellschutz": "0707013",
    "joghurt": "9709071",
    "proshape-shake": "0701045",       # Sorte über text: anpassen
}

KATEGORIEN = {
    "optimalsupply": "Optimalversorgung", "fitness": "Fitness & Sport", "specialneeds": "Individuell",
    "beauty": "Beauty", "weightmanagement": "Figur & Balance", "fanshop": "FanShop",
}


def schluessel(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.replace("ß", "ss").replace("+", " plus ")
    s = "".join(c for c in s if not unicodedata.combining(c) and unicodedata.category(c)[0] in "LNZP")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)


def sauber(name: str) -> str:
    name = " ".join(name.split())
    return re.sub(r"[¹²³⁴⁵⁶⁷⁸⁹⁰®]", "", name).replace("⁺", "+").strip()


def inhalt(d) -> str:
    menge, einheit = d.get("netWeight") or 0, d.get("netWeightUnit") or ""
    if not menge:
        return ""
    einheit = {"gr": "g"}.get(einheit, einheit)
    return f"{menge:g} {einheit}".replace(".", ",")


def main():
    if len(sys.argv) > 1:
        roh = json.loads(Path(sys.argv[1]).read_text())
    else:
        env = {**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()}
        lauf = subprocess.run(["node", str(HIER / "fitline_abrufen.js")], capture_output=True, text=True, env=env, timeout=300)
        if lauf.returncode:
            sys.exit(f"Abruf fehlgeschlagen: {lauf.stderr.strip()}")
        roh = json.loads(lauf.stdout)

    alt = {}
    if ZIEL.exists():
        for e in (yaml.safe_load(ZIEL.read_text()) or {}).get("artikel", {}).values():
            if e.get("artikelnr"):
                alt[e["artikelnr"]] = e.get("preis")

    produkte = []
    for x in roh:
        d = x["details"]
        name = sauber(d["attributes"]["name"]["value"])
        kat = [KATEGORIEN[t.split(":")[-1]] for t in d.get("tags", []) if t.startswith("pim:category:") and t.split(":")[-1] in KATEGORIEN]
        produkte.append({"nr": x["articleNumber"], "name": name, "preis": round(float(d["finalPrice"]), 2),
                         "ust": int(d["tax"]) if float(d["tax"]).is_integer() else float(d["tax"]),
                         "inhalt": inhalt(d), "kategorie": kat[0] if kat else "Sonstiges",
                         "lieferbar": bool(x.get("inStock", True))})
    produkte.sort(key=lambda p: (p["kategorie"], p["name"]))

    namen = {}
    for p in produkte:
        namen.setdefault(schluessel(p["name"]), []).append(p)
    eintraege = {}
    for k, gruppe in namen.items():
        for p in gruppe:
            eintraege[k if len(gruppe) == 1 else f"{k}-{p['nr']}"] = p

    zeilen = [
        "# FitLine-Produktkatalog für Rechnungen – AUTOMATISCH ERZEUGT, nicht von Hand ändern.",
        "# Neu erzeugen: python3 rechnungen/kataloge/fitline_aktualisieren.py",
        f"# Quelle: offizieller FitLine-Shop Deutschland (fitline.com/de/de-de), Stand {dt.date.today():%d.%m.%Y}",
        "#",
        "# Preise = Endkundenpreise inkl. USt. Steuersatz je Produkt so, wie FitLine ihn",
        "# deklariert (Nahrungsergänzung 7 %, Kosmetik und Shop-Artikel 19 %; Ausnahmen",
        "# übernimmt der Abruf automatisch, z. B. Fertiggetränke in Dosen 19 %).",
        "#",
        "# In der Rechnung:   - artikel: powercocktail      (Schlüssel, Alias oder Artikelnummer)",
        "#                      menge: 2",
        "# Eigene Preise/Texte in der Position überschreiben den Katalog.",
        "",
        "katalog: FitLine",
        "preise: brutto",
        f"stand: {dt.date.today().isoformat()}",
        "",
        "aliase:",
    ]
    nr_zu_k = {p["nr"]: k for k, p in eintraege.items()}
    for a, nr in ALIASE.items():
        if nr in nr_zu_k:
            zeilen.append(f"  {a}: {nr_zu_k[nr]}")
    zeilen += ["", "artikel:"]
    kat_alt = None
    for k, p in eintraege.items():
        if p["kategorie"] != kat_alt:
            zeilen += ["", f"  # ---- {p['kategorie']} ----"]
            kat_alt = p["kategorie"]
        text = p["name"] if re.match(r"(?i)fitline|pm\b", p["name"]) else f"FitLine {p['name']}"
        detail = " · ".join(x for x in [f"Art.-Nr. {p['nr']}", p["inhalt"]] if x)
        zeilen.append(f"  {k}:")
        zeilen.append(f"    text: {json.dumps(text, ensure_ascii=False)}")
        zeilen.append(f"    detail: {json.dumps(detail, ensure_ascii=False)}")
        zeilen.append(f"    artikelnr: \"{p['nr']}\"")
        zeilen.append("    einheit: " + ("Set" if re.search(r"(?i)set\b", p["name"]) else "Stk."))
        zeilen.append(f"    preis: {p['preis']:.2f}")
        zeilen.append(f"    ust: {p['ust']}" + ("" if p["lieferbar"] else "   # derzeit nicht lieferbar"))
    zeilen += ["", "  # ---- Eigene Positionen ----",
               "  versand:", "    text: Versandkosten", "    einheit: pausch.", "    preis: 0.00",
               "    ust: 7   # folgt der Ware; bei 7 % und 19 % gemischt aufteilen (zweite Position mit ust: 19)", ""]
    ZIEL.write_text("\n".join(zeilen), encoding="utf-8")

    neu = {p["nr"]: p for p in produkte}
    geaendert = [(p["name"], alt[nr], p["preis"]) for nr, p in neu.items() if nr in alt and alt[nr] is not None and float(alt[nr]) != p["preis"]]
    print(f"✓ {len(produkte)} Produkte → {ZIEL.relative_to(HIER.parent.parent)}")
    for n, a, b in geaendert:
        print(f"  Preis geändert: {n}: {a:.2f} → {b:.2f} €")
    if alt:
        weg = set(alt) - set(neu)
        if weg:
            print(f"  Nicht mehr im Shop: {', '.join(sorted(weg))}")


if __name__ == "__main__":
    main()
