#!/usr/bin/env python3
"""Bindet eigene Übungsvideos in die App ein.

    python3 coaching/build/uebungsvideos.py

Clips (MP4, MOV, M4V oder WebM, z. B. direkt vom Handy) nach
coaching/build/uebungsvideos/ legen, Dateiname = Übungs-ID, z. B.
`bankdruecken.mov`. Die IDs stehen in coaching/daten/uebungen.json.

Das Skript (braucht ffmpeg) kürzt jeden Clip auf höchstens 20 Sekunden,
entfernt den Ton, rechnet auf 720 px Breite herunter und speichert ihn als
MP4 (H.264, für alle Browser) unter coaching/videos/. Danach trägt es in
daten/uebungen.json bei jeder Übung mit Clip das Feld `video` ein und entfernt
es bei Übungen ohne Clip. Übungen ohne Clip zeigen in der App einen Link zur
YouTube-Suche. Nach dem Lauf VERSION in sw.js erhöhen.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
QUELLE = APP / "build" / "uebungsvideos"
ZIEL = APP / "videos"
DATEN = APP / "daten" / "uebungen.json"
ENDUNGEN = {".mp4", ".mov", ".m4v", ".webm"}
MAX_SEKUNDEN = 20


def umrechnen(quelle, ziel):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(quelle),
        "-t", str(MAX_SEKUNDEN), "-an",
        "-vf", "scale='min(720,iw)':-2,fps=30",
        "-c:v", "libx264", "-profile:v", "main", "-pix_fmt", "yuv420p",
        "-crf", "28", "-preset", "slow", "-movflags", "+faststart",
        str(ziel),
    ], check=True)


def speichern(daten):
    """Schreibt uebungen.json im gewohnten Format: eine Kopfzeile je Übung."""
    dump = lambda x: json.dumps(x, ensure_ascii=False)
    zeilen = ["{", f' "gruppen": {dump(daten["gruppen"])},', ' "uebungen": [']
    alle = daten["uebungen"]
    for i, u in enumerate(alle):
        kopf = {k: v for k, v in u.items() if k not in ("schritte", "tipp")}
        ende = "," if i < len(alle) - 1 else ""
        zeilen.append(f"  {dump(kopf)[:-1]},")
        zeilen.append(f'   "schritte": {dump(u["schritte"])},')
        zeilen.append(f'   "tipp": {dump(u["tipp"])}}}{ende}')
    zeilen += [" ]", "}"]
    DATEN.write_text("\n".join(zeilen) + "\n", encoding="utf-8")


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg fehlt — bitte installieren (z. B. brew install ffmpeg).")
    ZIEL.mkdir(parents=True, exist_ok=True)
    daten = json.loads(DATEN.read_text(encoding="utf-8"))
    ids = {u["id"] for u in daten["uebungen"]}

    for datei in sorted(QUELLE.glob("*")):
        if datei.suffix.lower() not in ENDUNGEN:
            continue
        if datei.stem not in ids:
            print(f"  übersprungen: {datei.name} (keine Übung mit dieser ID)")
            continue
        ziel = ZIEL / f"{datei.stem}.mp4"
        umrechnen(datei, ziel)
        print(f"  {datei.name:34} → videos/{ziel.name}  {ziel.stat().st_size // 1024:>5} KB")

    vorhanden = {p.stem for p in ZIEL.glob("*.mp4")}
    for u in daten["uebungen"]:
        u.pop("video", None)
        if u["id"] in vorhanden:
            # `video` vor die Schritte, damit die Kopfzeile vollständig bleibt
            rest = {k: u.pop(k) for k in ("schritte", "tipp")}
            u["video"] = f"videos/{u['id']}.mp4"
            u.update(rest)
    speichern(daten)

    ohne = [u["id"] for u in daten["uebungen"] if "video" not in u]
    print(f"\n{len(daten['uebungen']) - len(ohne)} von {len(daten['uebungen'])} Übungen mit eigenem Video.")


if __name__ == "__main__":
    main()
