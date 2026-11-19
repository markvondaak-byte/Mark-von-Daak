#!/usr/bin/env python3
"""Baut einen kurzen Trailer zu „Die Dopamin-Lüge" (9:16, 1080 × 1920, 15 s).

    python3 dopamin/build/build_trailer.py

Vorher muss der Umschlag gebaut sein (dopamin/out/cover.png) — das
Buch-Mockup wird aus der Vorderseite ausgeschnitten. Das Hauptmotiv ist
dopamin/cover/titelbild.png (Kopf im Profil mit leuchtenden Synapsen).

Gesetzt wie die Werbevideos der anderen Titel Bild für Bild mit Pillow und an
ffmpeg gereicht; Bewegung, Textsprites, Mockup, Filmkorn und Vignette kommen
aus kopf/build/build_video.py und narzisst/build/build_video.py. Alle Sätze
stammen aus dem Klappentext und stehen so im Buch. Anrede „Sie" wie im Buch.

Ablauf:
  1. 0–3,4 s   „23:20 Uhr. Sie greifen zum Telefon." — Bildschirmlicht
  2. 3,4–6,6 s „40 Minuten später. Nichts davon hat Spaß gemacht."
  3. 6,6–10 s  Das Titelmotiv in Fahrt: „Dopamin macht kein Glück.
               Es macht Verlangen."
  4. 10–15 s   Das Buch, Titel, „Jetzt erhältlich".

Ohne Tonspur — Musik aus der Bibliothek der jeweiligen Plattform wählen.
"""

import importlib.util
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "dopamin"
AUS = BAND / "out"


def _laden(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


NV = _laden("narzisst_video", WURZEL / "narzisst" / "build" / "build_video.py")
KV = NV.KV
B, H, FPS = KV.B, KV.H, KV.FPS
DAUER = 15.0

# Farbwelt des Umschlags (dopamin/build/build_cover.py): Indigo, Violett.
TEXT = (242, 241, 248)
LEISE = (166, 163, 196)
AKZENT = (160, 151, 240)
GRUND_OBEN = (27, 26, 58)
GRUND_UNTEN = (14, 13, 34)
BILDSCHIRM = (120, 170, 255)

KV.AUS = AUS
KV.AKZENT = AKZENT
KV.TEXT = TEXT

fenster, aus_kubisch, klemmen = KV.fenster, KV.aus_kubisch, KV.klemmen
einsetzen, einblenden = KV.einsetzen, KV.einblenden


def textbild(zeilen, groesse, schnitt="Black", farbe=TEXT, **kw):
    return KV.textbild(zeilen, groesse, schnitt, farbe, **kw)


def bildschirmlicht():
    """Kaltes Licht eines Telefons, von unten in den dunklen Raum."""
    r = 760
    maske = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(maske).ellipse((r * 0.3, r * 0.3, r * 1.7, r * 1.7),
                                  fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(r * 0.3))
    licht = Image.new("RGBA", maske.size, BILDSCHIRM + (0,))
    licht.putalpha(maske.point(lambda v: round(v * 0.55)))
    return licht


def telefon():
    """Schlichtes Telefon als Silhouette mit leuchtendem Bildschirm."""
    b, h = 300, 600
    bild = Image.new("RGBA", (b + 120, h + 120), (0, 0, 0, 0))
    glow = Image.new("L", bild.size, 0)
    ImageDraw.Draw(glow).rounded_rectangle((60, 60, 60 + b, 60 + h),
                                           radius=46, fill=200)
    bild.paste(BILDSCHIRM + (255,), (0, 0),
               glow.filter(ImageFilter.GaussianBlur(40)))
    z = ImageDraw.Draw(bild)
    z.rounded_rectangle((60, 60, 60 + b, 60 + h), radius=46,
                        fill=(18, 18, 30, 255))
    z.rounded_rectangle((74, 74, 46 + b, 46 + h), radius=36,
                        fill=(44, 70, 130, 255))
    # angedeutete Kacheln eines endlosen Feeds
    for i in range(5):
        y = 110 + i * 104
        z.rounded_rectangle((100, y, 20 + b, y + 82), radius=14,
                            fill=(78, 110, 184, 255))
    return bild


def titelmotiv():
    foto = Image.open(BAND / "cover" / "titelbild.png").convert("RGB")
    faktor = max(B / foto.width, H / foto.height) * 1.02
    return foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS)


def fahrt(foto, t, start, dauer):
    """Langsame Fahrt auf den Kopf zu (er sitzt rechts der Bildmitte)."""
    f = klemmen((t - start) / dauer)
    zoom = 1.0 + 0.12 * f
    fb, fh = B / zoom, H / zoom
    ziel_x = foto.width * 0.56
    mx = foto.width / 2 + (ziel_x - foto.width / 2) * (0.6 + 0.4 * f)
    my = foto.height * 0.48
    x0 = min(max(mx - fb / 2, 0), foto.width - fb)
    y0 = min(max(my - fh / 2, 0), foto.height - fh)
    return foto.resize((B, H), Image.BILINEAR, box=(x0, y0, x0 + fb, y0 + fh))


class Trailer:
    def __init__(self):
        self.grund = KV.verlauf(GRUND_OBEN, GRUND_UNTEN).convert("RGBA")
        self.licht = bildschirmlicht()
        self.telefon = telefon()
        self.motiv = titelmotiv()
        self.vignette = NV.vignette()
        self.korn = NV.filmkorn()
        self.buch = KV.buch_mockup(600)

        self.s1a = textbild(["23:20 Uhr."], 170, farbe=AKZENT)
        self.s1b = textbild(["Sie greifen", "zum Telefon."], 104)
        self.s2a = textbild(["40 Minuten später."], 96, farbe=LEISE)
        self.s2b = textbild(["Nichts davon", "hat Spaß gemacht."], 104)
        self.s3a = textbild(["Dopamin macht", "kein Glück."], 120)
        self.s3b = textbild(["Es macht", "Verlangen."], 150, farbe=AKZENT)
        self.s4a = textbild(["JETZT ERHÄLTLICH"], 48, "SemiBold", AKZENT,
                            sperrung=9)
        self.s4b = textbild(["Taschenbuch · Hardcover · E-Book"], 52,
                            "ExtraBold")
        self.s4c = textbild(["bei Amazon"], 52, "Medium", LEISE)
        self.s4d = textbild(["MARK VON DAAK"], 42, "SemiBold", TEXT,
                            sperrung=10)

    def bild(self, t):
        bild = self.grund.copy()

        # Szene 1 und 2: dunkler Raum, Telefonlicht flackert leicht
        d_tel = fenster(t, 0.0, 6.6, ein=0.6, aus=0.5)
        if d_tel > 0:
            flackern = 0.85 + 0.15 * math.sin(t * 7.3) * math.sin(t * 2.1)
            einsetzen(bild, self.licht, (B - self.licht.width) / 2,
                      H * 0.70 - self.licht.height / 2, d_tel * flackern)
            schweben = math.sin(t * 1.4) * 6
            einsetzen(bild, self.telefon, (B - self.telefon.width) / 2,
                      1130 + schweben, d_tel)

        # Szene 3: Titelmotiv in Fahrt
        d_motiv = fenster(t, 6.4, 10.2, ein=0.6, aus=0.6)
        if d_motiv > 0:
            m = fahrt(self.motiv, t, 6.4, 3.8).convert("RGBA")
            einsetzen(bild, m, 0, 0, d_motiv)
            einsetzen(bild, self.vignette, 0, 0, d_motiv)

        einblenden(bild, self.s1a, 380, t, 0.3, 3.4, hub=40)
        einblenden(bild, self.s1b, 620, t, 1.2, 3.4)
        einblenden(bild, self.s2a, 400, t, 3.6, 6.6, hub=30)
        einblenden(bild, self.s2b, 580, t, 4.4, 6.6)
        einblenden(bild, self.s3a, 1180, t, 6.9, 10.0)
        einblenden(bild, self.s3b, 1460, t, 7.9, 10.0, hub=80)

        d4 = fenster(t, 10.0, DAUER + 1, ein=0.7)
        if d4 > 0:
            auf = aus_kubisch((t - 10.0) / 1.0)
            schweben = math.sin((t - 10.0) * 1.5) * 7
            einsetzen(bild, self.buch, (B - self.buch.width) / 2,
                      120 + (1 - auf) * 240 + schweben, d4)
        einblenden(bild, self.s4a, 1300, t, 10.8, DAUER + 1, hub=30)
        einblenden(bild, self.s4b, 1395, t, 11.2, DAUER + 1)
        einblenden(bild, self.s4c, 1480, t, 11.6, DAUER + 1)
        einblenden(bild, self.s4d, 1640, t, 12.1, DAUER + 1, hub=30)

        ergebnis = bild.convert("RGB")
        ergebnis = Image.blend(ergebnis,
                               self.korn[int(t * 12) % len(self.korn)], 0.03)
        if t > DAUER - 0.6:
            ergebnis = Image.blend(ergebnis, Image.new("RGB", (B, H)),
                                   klemmen((t - (DAUER - 0.6)) / 0.6))
        if t < 0.3:
            ergebnis = Image.blend(Image.new("RGB", (B, H)), ergebnis,
                                   klemmen(t / 0.3))
        return ergebnis


def main():
    for pflicht in (AUS / "cover.png", BAND / "cover" / "titelbild.png"):
        if not pflicht.exists():
            raise SystemExit(f"{pflicht.relative_to(WURZEL)} fehlt — erst "
                             "den Umschlag bauen.")
    ziel = AUS / "trailer-9x16.mp4"
    trailer = Trailer()
    befehl = ["ffmpeg", "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{B}x{H}",
              "-r", str(FPS), "-i", "-",
              "-c:v", "libx264", "-preset", "slow", "-crf", "18",
              "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ziel)]
    prozess = subprocess.Popen(befehl, stdin=subprocess.PIPE)
    anzahl = round(DAUER * FPS)
    for n in range(anzahl):
        prozess.stdin.write(trailer.bild(n / FPS).tobytes())
    prozess.stdin.close()
    if prozess.wait() != 0:
        raise SystemExit("ffmpeg ist fehlgeschlagen.")
    print(f"{anzahl} Bilder, {DAUER:.0f} s, {B} x {H}, {FPS} fps")
    print(f"  → {ziel.relative_to(WURZEL)}  "
          f"({ziel.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
