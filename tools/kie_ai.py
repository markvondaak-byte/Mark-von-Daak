#!/usr/bin/env python3
"""Erzeugt Bilder und Videos über die API von Kie.ai.

    python3 tools/kie_ai.py guthaben
    python3 tools/kie_ai.py bild  "Lachs mit Ofengemüse, Food-Fotografie"
    python3 tools/kie_ai.py video "Langsamer Schwenk über einen gedeckten Tisch"
    python3 tools/kie_ai.py status <taskId>

Der API-Key kommt aus der Umgebungsvariable KIE_API_KEY — er gehört nie ins
Repository. Fertige Dateien landen in kie_out/ (steht in .gitignore).

Kie.ai arbeitet asynchron: Ein Auftrag liefert zuerst nur eine taskId, das
Skript fragt dann so lange nach, bis das Ergebnis da ist oder fehlschlägt.

Welches Modell genutzt wird, steuert --modell. Die Voreinstellungen unten
lassen sich überschreiben, die genauen Modellnamen stehen in der
Kie.ai-Dokumentation. Zusätzliche Eingabefelder (Seitenverhältnis, Dauer …)
gehen per --feld name=wert mit.

Nutzt ausschließlich die Standardbibliothek.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASIS = "https://api.kie.ai/api/v1"
WURZEL = Path(__file__).resolve().parents[1]
AUSGABE = WURZEL / "kie_out"

MODELL_BILD = "google/nano-banana"
MODELL_VIDEO = "kling/v2-1-standard"

# Zustände, nach denen nicht mehr nachgefragt werden muss.
FERTIG = {"success"}
FEHLER = {"fail"}


def anfrage(methode, pfad, daten=None):
    schluessel = os.environ.get("KIE_API_KEY")
    if not schluessel:
        sys.exit("KIE_API_KEY ist nicht gesetzt.")
    koerper = json.dumps(daten).encode() if daten is not None else None
    req = urllib.request.Request(
        BASIS + pfad,
        data=koerper,
        method=methode,
        headers={
            "Authorization": f"Bearer {schluessel}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as antwort:
            ergebnis = json.load(antwort)
    except urllib.error.HTTPError as fehler:
        sys.exit(f"HTTP {fehler.code}: {fehler.read().decode(errors='replace')}")
    if ergebnis.get("code") != 200:
        sys.exit(f"Kie.ai meldet Fehler: {json.dumps(ergebnis, ensure_ascii=False)}")
    return ergebnis.get("data")


def auftrag_anlegen(modell, eingabe):
    daten = anfrage("POST", "/jobs/createTask", {"model": modell, "input": eingabe})
    return daten["taskId"]


def warten(task_id, intervall=5, hoechstens=1800):
    beginn = time.monotonic()
    while True:
        daten = anfrage("GET", f"/jobs/recordInfo?taskId={task_id}")
        zustand = daten.get("state")
        if zustand in FERTIG:
            return json.loads(daten.get("resultJson") or "{}").get("resultUrls", [])
        if zustand in FEHLER:
            sys.exit(f"Auftrag fehlgeschlagen: {daten.get('failMsg') or daten}")
        if time.monotonic() - beginn > hoechstens:
            sys.exit(f"Zeitüberschreitung, Auftrag {task_id} läuft noch ({zustand}).")
        print(f"  … {zustand}", file=sys.stderr)
        time.sleep(intervall)


def herunterladen(urls, task_id):
    AUSGABE.mkdir(exist_ok=True)
    pfade = []
    for nummer, url in enumerate(urls, 1):
        endung = Path(url.split("?")[0]).suffix or ".bin"
        ziel = AUSGABE / f"{task_id}_{nummer}{endung}"
        urllib.request.urlretrieve(url, ziel)
        pfade.append(ziel)
    return pfade


def felder_lesen(paare):
    eingabe = {}
    for paar in paare:
        name, _, wert = paar.partition("=")
        try:
            eingabe[name] = json.loads(wert)
        except json.JSONDecodeError:
            eingabe[name] = wert
    return eingabe


def erzeugen(modell, prompt, felder):
    eingabe = {"prompt": prompt, **felder_lesen(felder)}
    task_id = auftrag_anlegen(modell, eingabe)
    print(f"Auftrag {task_id} angelegt ({modell}).", file=sys.stderr)
    for pfad in herunterladen(warten(task_id), task_id):
        print(pfad)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    befehle = parser.add_subparsers(dest="befehl", required=True)

    befehle.add_parser("guthaben", help="verbleibende Credits anzeigen")

    for name, modell in (("bild", MODELL_BILD), ("video", MODELL_VIDEO)):
        teil = befehle.add_parser(name, help=f"{name} erzeugen")
        teil.add_argument("prompt")
        teil.add_argument("--modell", default=modell)
        teil.add_argument("--feld", action="append", default=[], metavar="NAME=WERT")

    status = befehle.add_parser("status", help="laufenden Auftrag abholen")
    status.add_argument("task_id")

    args = parser.parse_args()
    if args.befehl == "guthaben":
        print(anfrage("GET", "/chat/credit"))
    elif args.befehl == "status":
        for pfad in herunterladen(warten(args.task_id), args.task_id):
            print(pfad)
    else:
        erzeugen(args.modell, args.prompt, args.feld)


if __name__ == "__main__":
    main()
