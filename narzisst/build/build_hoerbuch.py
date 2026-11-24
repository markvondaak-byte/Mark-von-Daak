#!/usr/bin/env python3
"""Hörbuch — Der Narzisst in meinem Bett.

Liest die Kapitel aus narzisst/kapitel/*.md, macht daraus Vorlesetext
(Tabellen in Sätze, Rufnummern ziffernweise, Abkürzungen ausgeschrieben) und
spricht ihn mit einer freien deutschen Piper-Stimme ein. Standard ist die
Frauenstimme „Kerstin“ (Datensatz CC0, kommerziell nutzbar); andere mit
--stimme ramona | eva_k | thorsten.

Ausgabe in narzisst/out/hoerbuch/:
  NN-<kapitel>.mp3      je Kapitel, 192 kbit/s CBR, 44,1 kHz, mono
                        (ACX-Vorgaben: Pegel um -20 dB RMS, Spitzen < -3 dB,
                        0,75 s Stille vorn, 3 s hinten)
  <slug>-hoerbuch.m4b   alles in einer Datei mit Kapitelmarken
  hoerbuch-cover.jpg    3000 × 3000 px
  vorlesetext/*.txt     der gesprochene Text zum Gegenhören

Voraussetzungen: pip install piper-tts, ffmpeg. Stimme einmalig laden:
  python3 build_hoerbuch.py --stimme-laden
Nur ein Kapitel zum Probehören:  python3 build_hoerbuch.py --nur 10
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.request
import wave
from pathlib import Path

import yaml

HIER = Path(__file__).resolve().parent
ORDNER = HIER.parent
KAPITEL = ORDNER / "kapitel"
AUS = ORDNER / "out" / "hoerbuch"
STIMMEN = ORDNER / "out" / "stimmen"
STIMMEN_PFAD = {
    "kerstin": "kerstin/low/de_DE-kerstin-low",
    "ramona": "ramona/low/de_DE-ramona-low",
    "eva_k": "eva_k/x_low/de_DE-eva_k-x_low",
    "thorsten": "thorsten/high/de_DE-thorsten-high",
}
STIMME_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/"

ZIFFERN = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben",
           "acht", "neun"]
ORDINAL = ["", "Erstens", "Zweitens", "Drittens", "Viertens", "Fünftens",
           "Sechstens", "Siebtens", "Achtens", "Neuntens", "Zehntens"]
ROEMISCH = {"I": "eins", "II": "zwei", "III": "drei", "IV": "vier"}

# Pausen in Sekunden
P_ABSATZ = 0.7
P_UEBERSCHRIFT = 1.2
P_KAPITEL = 1.8

# Kapitel, die im Hörbuch anders behandelt werden
UEBERSPRINGEN = {"00-titelseite", "01-impressum", "03-inhalt"}


# ---------------------------------------------------------------- Text

def frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        _, kopf, rumpf = text.split("---", 2)
        return yaml.safe_load(kopf) or {}, rumpf
    return {}, text


def ziffernweise(nummer: str) -> str:
    """„0800 111 0 111“ → „null acht null null, eins eins eins, …“"""
    gruppen = re.findall(r"\d+", nummer)
    return ", ".join(" ".join(ZIFFERN[int(z)] for z in g) for g in gruppen)


RUFNUMMER = re.compile(r"\b(?:0800|116|143|110|112)(?: \d{1,4})*\b(?!\.\d)")


def normalisieren(s: str) -> str:
    s = s.replace("{{LEERZEILE}}", "")
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)        # Links
    s = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", s)   # fett/kursiv
    s = s.replace("\\", "")
    s = re.sub(r"(\d)\s+·\s+(\d)", r"\1 oder \2", s)
    s = s.replace("Die Quellen stehen am Ende des Buches.",
                  "Die Quellen stehen in der gedruckten Ausgabe und im E-Book.")
    # Rufnummern ziffernweise; „Kapitel 11“ und Altersangaben bleiben Zahlen
    s = re.sub(r"(?<!Kapitel )" + RUFNUMMER.pattern,
               lambda m: ziffernweise(m.group(0)), s)
    s = s.replace("1950er", "neunzehnhundertfünfziger")
    s = re.sub(r"(\d)\s*%", r"\1 Prozent", s)
    s = re.sub(r"(\d)\s*[–-]\s*(\d)", r"\1 bis \2", s)
    ersatz = {
        "z. B.": "zum Beispiel", "z.B.": "zum Beispiel", "d. h.": "das heißt",
        "u. a.": "unter anderem", "bzw.": "beziehungsweise", "ca.": "circa",
        "usw.": "und so weiter", "etc.": "et cetera", "ggf.": "gegebenenfalls",
        "vgl.": "vergleiche", "Nr.": "Nummer", "§": "Paragraf",
        "DARVO": "Darvo", "BIFF": "Biff", "JADE": "Jade",
        "markvondaak@icloud.com": "mark von daak, at, icloud, punkt com",
        " · ": ", ", "·": ",", "…": "...", "→": ":", "&": "und",
    }
    for alt, neu in ersatz.items():
        s = s.replace(alt, neu)
    s = re.sub(r"\bTeil (III|II|IV|I)\b", lambda m: "Teil " + ROEMISCH[m.group(1)], s)
    # Gedankenstrich als kurze Sprechpause
    s = re.sub(r"\s+—\s+", ", ", s)
    s = s.replace("—", ", ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def satzende(s: str) -> str:
    return s if not s or s[-1] in ".!?:…“\"" else s + "."


def tabelle(zeilen: list[str]) -> list[str]:
    reihen = [[z.strip() for z in r.strip().strip("|").split("|")]
              for r in zeilen if not re.match(r"^\|\s*-", r.strip())]
    kopf, daten = reihen[0], reihen[1:]
    saetze = []
    for r in daten:
        if len(kopf) == 3 and kopf[-1].lower().startswith("nummer"):
            saetze.append(f"{r[0]}: {r[1]}, Nummer {r[2]}.")
        elif len(kopf) == 3:
            saetze.append(f"{r[0]}: {r[1]}, {r[2]}.")
        else:
            saetze.append(" ".join(satzende(f"{k}: {z}") for k, z in zip(kopf, r)))
    return saetze


def bloecke(rumpf: str) -> list[tuple[str, str]]:
    """Zerlegt Markdown in (art, text); art ∈ ueberschrift, absatz."""
    aus: list[tuple[str, str]] = []
    zeilen = rumpf.strip().splitlines()
    i = 0
    puffer: list[str] = []

    def absatz_schliessen():
        if puffer:
            t = normalisieren(" ".join(puffer))
            if t:
                aus.append(("absatz", satzende(t)))
            puffer.clear()

    while i < len(zeilen):
        z = zeilen[i].rstrip()
        roh = z.strip()
        if roh.startswith("|"):
            absatz_schliessen()
            tab = []
            while i < len(zeilen) and zeilen[i].strip().startswith("|"):
                tab.append(zeilen[i]); i += 1
            for satz in tabelle(tab):
                aus.append(("absatz", normalisieren(satz)))
            continue
        if not roh or roh == "---" or roh == "{{LEERZEILE}}":
            absatz_schliessen()
        elif roh.startswith("#"):
            absatz_schliessen()
            aus.append(("ueberschrift", satzende(normalisieren(roh.lstrip("#").strip()))))
        elif re.match(r"^[-*] ", roh):
            absatz_schliessen()
            puffer.append(roh[2:])
        elif m := re.match(r"^(\d+)\. (.*)", roh):
            absatz_schliessen()
            n = int(m.group(1))
            puffer.append((ORDINAL[n] + ": " if n < len(ORDINAL) else "") + m.group(2))
        elif roh.startswith(">"):
            inhalt = roh.lstrip(">").strip()
            if not inhalt:
                absatz_schliessen()
            else:
                if re.match(r"^\**Kurz gefasst", inhalt):
                    absatz_schliessen()
                puffer.append(inhalt)
        else:
            puffer.append(roh)
        i += 1
    absatz_schliessen()
    return aus


def kapitel_liste(meta: dict) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """(dateiname, titel, bloecke) in Hörbuch-Reihenfolge."""
    titel, unter, autor = meta["titel"], meta["untertitel"], meta["autor"]
    liste = [("00-ansage", "Ansage", [
        ("ueberschrift", f"{titel}."),
        ("absatz", f"{unter}."),
        ("absatz", f"Geschrieben von {autor}. "
                   "Gelesen von einer synthetischen Stimme."),
    ])]
    nr_kap = 0
    for datei in sorted(KAPITEL.glob("*.md")):
        if datei.stem in UEBERSPRINGEN:
            continue
        fm, rumpf = frontmatter(datei.read_text(encoding="utf-8"))
        name = fm.get("titel", datei.stem)
        if datei.stem == "61-quellen":
            b = [("ueberschrift", "Quellen."),
                 ("absatz", "Die Studien und Werke, auf die sich dieses Buch "
                            "stützt, sind nach Kapiteln geordnet in der "
                            "gedruckten Ausgabe und im E-Book aufgeführt. "
                            "Dort findest du alle Angaben zum Nachlesen.")]
        else:
            b = bloecke(rumpf)
        if datei.stem == "02-bitte-zuerst-lesen":
            name = "Bitte zuerst hören"
            b = [("ueberschrift", "Bitte zuerst hören.") if k == "ueberschrift"
                 and "zuerst lesen" in t.lower() else (k, t) for k, t in b]
        name = normalisieren(name)
        if fm.get("typ") == "kapitel" and re.match(r"^[2-4][1-9]-", datei.stem):
            nr_kap += 1
            name = f"Kapitel {nr_kap}: {name}"
            if b and b[0][0] == "ueberschrift":
                b[0] = ("ueberschrift", f"Kapitel {nr_kap}. {b[0][1]}")
        liste.append((datei.stem, name, b))
    liste.append(("99-abspann", "Abspann", [
        ("absatz", f"Das war: {titel}. {unter}. Geschrieben von {autor}."),
        ("absatz", f"Copyright {meta.get('jahr', '')}, {autor}. "
                   "Ende des Hörbuchs."),
    ]))
    return liste


# ---------------------------------------------------------------- Audio

def stimme_laden(name: str) -> Path:
    STIMMEN.mkdir(parents=True, exist_ok=True)
    pfad = STIMMEN_PFAD[name]
    datei = pfad.rsplit("/", 1)[1]
    onnx = STIMMEN / f"{datei}.onnx"
    for endung in (".onnx", ".onnx.json"):
        ziel = STIMMEN / f"{datei}{endung}"
        if not ziel.exists():
            print("lade", ziel.name)
            urllib.request.urlretrieve(STIMME_URL + pfad + endung, ziel)
    return onnx


def einsprechen(stimme, bloecke_: list[tuple[str, str]], wav_ziel: Path):
    from piper import SynthesisConfig
    cfg = SynthesisConfig(length_scale=1.08, noise_scale=0.6, noise_w_scale=0.8)
    rate = stimme.config.sample_rate
    stille = lambda sek: b"\x00\x00" * int(rate * sek)  # noqa: E731
    with wave.open(str(wav_ziel), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        for art, text in bloecke_:
            if art == "ueberschrift":
                w.writeframes(stille(P_UEBERSCHRIFT / 2))
            for chunk in stimme.synthesize(text, cfg):
                w.writeframes(chunk.audio_int16_bytes)
            w.writeframes(stille(P_UEBERSCHRIFT if art == "ueberschrift" else P_ABSATZ))


def mp3_mastern(wav: Path, mp3: Path, titel: str, nr: int, meta: dict):
    # Lautheit auf ca. -20 dB RMS (ACX: -23 … -18), Spitzen bei -3,5 dB,
    # Rumpeln unter 80 Hz weg, vorn 0,75 s und hinten 3 s Raumstille.
    filt = ("highpass=f=80,loudnorm=I=-20:TP=-3.5:LRA=11,"
            "adelay=750,apad=pad_dur=3,aresample=44100")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", filt,
        "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k",
        "-metadata", f"title={titel}", "-metadata", f"track={nr}",
        "-metadata", f"album={meta['titel']}",
        "-metadata", f"artist={meta['autor']}",
        "-metadata", f"album_artist={meta['autor']}",
        "-metadata", "genre=Hörbuch", "-metadata", f"date={meta.get('jahr', '')}",
        str(mp3)], check=True)


def dauer(datei: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(datei)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def m4b_bauen(mp3s: list[tuple[Path, str]], ziel: Path, cover: Path, meta: dict):
    liste = AUS / "_liste.txt"
    liste.write_text("".join(f"file '{p.name}'\n" for p, _ in mp3s), encoding="utf-8")
    kap = [";FFMETADATA1", f"title={meta['titel']}", f"artist={meta['autor']}",
           f"album={meta['titel']}", "genre=Hörbuch"]
    start = 0
    for p, t in mp3s:
        ende = start + int(dauer(p) * 1000)
        kap += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={start}", f"END={ende}",
                f"title={t}"]
        start = ende
    meta_datei = AUS / "_kapitel.txt"
    meta_datei.write_text("\n".join(kap) + "\n", encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(liste),
        "-i", str(meta_datei), "-i", str(cover),
        "-map", "0:a", "-map", "2:v", "-map_metadata", "1",
        "-c:a", "aac", "-b:a", "96k", "-c:v", "mjpeg",
        "-disposition:v", "attached_pic", "-f", "mp4", str(ziel)], check=True)
    liste.unlink(); meta_datei.unlink()


def cover_bauen(ziel: Path):
    """3000 × 3000 px: Titelmotiv des Buches, quadratisch gesetzt."""
    sys.path.insert(0, str(HIER))
    from PIL import Image, ImageDraw, ImageFont
    vorlage = ORDNER / "out" / "kindle-cover.jpg"
    if not vorlage.exists():
        subprocess.run([sys.executable, str(HIER / "build_epub.py")], check=True)
    vorn = Image.open(vorlage).convert("RGB")          # 1600 × 2560
    grund = vorn.getpixel((10, vorn.height - 10))
    bild = Image.new("RGB", (3000, 3000), grund)
    # Hintergrund: unscharf vergrößertes Cover, darüber das Cover in voller Höhe
    from PIL import ImageFilter
    hg = vorn.resize((3000, int(3000 * vorn.height / vorn.width))).filter(
        ImageFilter.GaussianBlur(60))
    bild.paste(hg.crop((0, (hg.height - 3000) // 2, 3000, (hg.height + 3000) // 2)))
    bild = Image.blend(bild, Image.new("RGB", bild.size, grund), 0.45)
    h = 2760
    w = int(vorn.width * h / vorn.height)
    bild.paste(vorn.resize((w, h), Image.LANCZOS), ((3000 - w) // 2, 120))
    # Hörbuch-Kennzeichnung links und rechts neben dem Cover
    zug = ImageDraw.Draw(bild)
    schrift = ImageFont.truetype(
        "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 64)
    for x in ((3000 - w) // 4, 3000 - (3000 - w) // 4):
        txt = Image.new("RGBA", (1400, 120), (0, 0, 0, 0))
        ImageDraw.Draw(txt).text((700, 60), "H Ö R B U C H", font=schrift,
                                 fill=(255, 255, 255, 230), anchor="mm")
        txt = txt.rotate(90, expand=True)
        bild.paste(txt, (x - 60, 1500 - 700), txt)
    del zug
    bild.save(ziel, "JPEG", quality=92)


# ---------------------------------------------------------------- Ablauf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nur", help="nur Kapitel mit diesem Dateianfang, z. B. 10")
    ap.add_argument("--stimme", default="kerstin", choices=list(STIMMEN_PFAD))
    ap.add_argument("--stimme-laden", action="store_true")
    ap.add_argument("--nur-text", action="store_true",
                    help="nur den Vorlesetext schreiben, nichts einsprechen")
    a = ap.parse_args()

    meta = yaml.safe_load((ORDNER / "narzisst.yaml").read_text(encoding="utf-8"))
    onnx = stimme_laden(a.stimme)
    if a.stimme_laden:
        return

    AUS.mkdir(parents=True, exist_ok=True)
    (AUS / "vorlesetext").mkdir(exist_ok=True)
    kapitel = kapitel_liste(meta)
    for stem, titel, b in kapitel:
        (AUS / "vorlesetext" / f"{stem}.txt").write_text(
            "\n\n".join(t for _, t in b) + "\n", encoding="utf-8")
    if a.nur_text:
        print("Vorlesetext in", AUS / "vorlesetext"); return

    from piper import PiperVoice
    stimme = PiperVoice.load(str(onnx))
    mp3s = []
    for nr, (stem, titel, b) in enumerate(kapitel, start=1):
        teil = stem.split("-", 1)[1].replace("bitte-zuerst-lesen", "bitte-zuerst-hoeren")
        mp3 = AUS / f"{nr:02d}-{teil}.mp3"
        if not a.nur or stem.startswith(a.nur):
            wav = AUS / "_roh.wav"
            print(f"spreche {nr:02d} {titel} …", flush=True)
            einsprechen(stimme, b, wav)
            mp3_mastern(wav, mp3, titel, nr, meta)
            wav.unlink()
        if mp3.exists():
            mp3s.append((mp3, titel))
    if a.nur:
        return

    cover = AUS / "hoerbuch-cover.jpg"
    cover_bauen(cover)
    m4b = AUS / f"{meta['slug']}-hoerbuch.m4b"
    m4b_bauen(mp3s, m4b, cover, meta)
    gesamt = sum(dauer(p) for p, _ in mp3s)
    print(f"fertig: {len(mp3s)} Spuren, {gesamt / 3600:.2f} h → {m4b}")


if __name__ == "__main__":
    main()
