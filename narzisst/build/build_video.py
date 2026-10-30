#!/usr/bin/env python3
"""Baut das Werbevideo zu „Der Narzisst in meinem Bett" (9:16, 1080 × 1920, 26 s).

    python3 narzisst/build/build_video.py

Vorher müssen Innenteil und Umschlag gebaut sein — das Buch-Mockup wird aus
narzisst/out/cover.png ausgeschnitten, das Hauptmotiv ist
narzisst/cover/titelbild.png (das Schlafzimmer um 3:33 Uhr).

Gesetzt wird wie bei „Kopf schlägt Kalorien" Bild für Bild mit Pillow und
direkt an ffmpeg gereicht; Bewegung, Textsprites und Mockup kommen aus
kopf/build/build_video.py. Kein KI-Video: Die Schrift soll scharf und
fehlerfrei sein, und jede Aussage im Video steht so oder sinngemäß im Buch.
Keine Diagnosen, keine Heilversprechen, keine Aussagen über reale Personen.

Ablauf:
  1. 0–4 s    Das Schlafzimmer, langsame Fahrt auf den Wecker: „3:33 Uhr.
              Du liegst wach."
  2. 4–8 s    „Und fragst dich wieder: Bin ich zu empfindlich?"
  3. 8–13 s   Seine Sätze als Chatnachrichten, eine nach der anderen.
  4. 13–16 s  „Du bist nicht verrückt. Du steckst in einem Muster."
  5. 16–20 s  Was das Buch zeigt, vier Punkte.
  6. 20–26 s  Das Buch, Titel, „Jetzt erhältlich", Hilfetelefon.

Das Video hat keine Tonspur. Musik aus der Bibliothek der jeweiligen
Plattform (Instagram, TikTok, YouTube) ist dort lizenziert; eine eigene Datei
müsste für Werbung eigens lizenziert sein.
"""

import importlib.util
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

WURZEL = Path(__file__).resolve().parents[2]
BAND = WURZEL / "narzisst"
AUS = BAND / "out"


def _kopf_video():
    pfad = WURZEL / "kopf" / "build" / "build_video.py"
    spec = importlib.util.spec_from_file_location("kopf_video", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


KV = _kopf_video()
B, H, FPS = KV.B, KV.H, KV.FPS
DAUER = 26.0

TEXT = (247, 238, 232)
LEISE = (196, 206, 218)
AKZENT = (240, 168, 150)
GRUND_OBEN = (14, 18, 24)
GRUND_UNTEN = (6, 8, 12)

# Das Mockup und die Stichpunkte aus kopf/build/build_video.py lesen diese
# Modulwerte erst beim Aufruf — so greifen Umschlag und Farbe dieses Titels.
KV.AUS = AUS
KV.AKZENT = AKZENT
KV.TEXT = TEXT

schrift, fenster, aus_kubisch = KV.schrift, KV.fenster, KV.aus_kubisch
klemmen, einsetzen, einblenden = KV.klemmen, KV.einsetzen, KV.einblenden


def textbild(zeilen, groesse, schnitt="Black", farbe=TEXT, **kw):
    return KV.textbild(zeilen, groesse, schnitt, farbe, **kw)


# --- Bausteine ---------------------------------------------------------------
def foto_laden():
    """Titelfoto, groß genug für eine Fahrt auf den Wecker."""
    foto = Image.open(BAND / "cover" / "titelbild.png").convert("RGB")
    faktor = max(B / foto.width, H / foto.height) * 1.02
    return foto.resize((round(foto.width * faktor), round(foto.height * faktor)),
                       Image.LANCZOS), faktor


# Wo im Originalfoto (896 × 1110 px) der Wecker steht — Ziel der Kamerafahrt.
WECKER = (292, 563)


def kamerafahrt(foto, faktor, t, start, dauer, zoom_bis=1.6):
    """Ken-Burns-Fahrt: vom ganzen Bild langsam auf den Wecker zu."""
    f = aus_kubisch(klemmen((t - start) / dauer)) * 0.85 \
        + klemmen((t - start) / dauer) * 0.15
    zoom = 1.0 + (zoom_bis - 1.0) * f
    fb, fh = B / zoom, H / zoom
    wx, wy = WECKER[0] * faktor, WECKER[1] * faktor
    # Bildmitte wandert von der Fotomitte zum Wecker
    mx = foto.width / 2 + (wx - foto.width / 2) * f
    my = foto.height / 2 + (wy - foto.height / 2) * f * 0.7
    x0 = min(max(mx - fb / 2, 0), foto.width - fb)
    y0 = min(max(my - fh / 2, 0), foto.height - fh)
    return foto.resize((B, H), Image.BILINEAR, box=(x0, y0, x0 + fb, y0 + fh))


def unscharf_dunkel(foto):
    """Ruhiger Hintergrund für die Textszenen: das Foto, weich und abgedunkelt."""
    x0 = (foto.width - B) / 2
    bild = foto.crop((round(x0), 0, round(x0) + B, H))
    bild = bild.filter(ImageFilter.GaussianBlur(26))
    return Image.blend(bild, Image.new("RGB", (B, H), GRUND_UNTEN), 0.55)


def vignette():
    maske = Image.new("L", (B, H), 0)
    ImageDraw.Draw(maske).ellipse((-B * 0.35, -H * 0.18, B * 1.35, H * 1.18),
                                  fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(160))
    schwarz = Image.new("RGBA", (B, H), (0, 0, 0, 255))
    schwarz.putalpha(maske.point(lambda v: round((255 - v) * 0.85)))
    return schwarz


def filmkorn(anzahl=6, staerke=16):
    """Ein paar Rauschbilder, die sich abwechseln — wirkt wie Filmkorn."""
    zufall = random.Random(333)
    bilder = []
    for _ in range(anzahl):
        klein = Image.new("L", (B // 2, H // 2))
        klein.putdata([128 + zufall.randint(-staerke, staerke)
                       for _ in range((B // 2) * (H // 2))])
        bilder.append(klein.resize((B, H), Image.NEAREST).convert("RGB"))
    return bilder


def nachricht(text, groesse=58):
    """Chatblase von links, wie eine eingehende Nachricht."""
    f = schrift("Medium", groesse)
    messen = ImageDraw.Draw(Image.new("L", (1, 1)))
    breite = messen.textlength(text, font=f)
    pad_x, pad_y = 44, 30
    b, h = round(breite + 2 * pad_x), round(groesse * 1.25 + 2 * pad_y)
    bild = Image.new("RGBA", (b + 40, h + 50), (0, 0, 0, 0))
    schatten = Image.new("L", bild.size, 0)
    ImageDraw.Draw(schatten).rounded_rectangle((14, 22, b + 14, h + 22),
                                               radius=h / 2.4, fill=150)
    bild.paste((0, 0, 0, 255), (0, 0), schatten.filter(ImageFilter.GaussianBlur(16)))
    z = ImageDraw.Draw(bild)
    z.rounded_rectangle((0, 0, b, h), radius=h / 2.4, fill=(44, 50, 60, 255))
    z.polygon([(18, h - 26), (0, h + 10), (52, h - 6)], fill=(44, 50, 60, 255))
    z.text((pad_x, pad_y - groesse * 0.06), text, font=f, fill=(238, 240, 244))
    return bild


def lesebestaetigung(groesse=30):
    return textbild(["gelesen 03:33"], groesse, "Medium", (130, 140, 154),
                    breite=420)


# --- Video -------------------------------------------------------------------
class Video:
    def __init__(self):
        self.foto, self.faktor = foto_laden()
        self.hintergrund = unscharf_dunkel(self.foto).convert("RGBA")
        self.verlauf = KV.verlauf(GRUND_OBEN, GRUND_UNTEN).convert("RGBA")
        self.vignette = vignette()
        self.korn = filmkorn()
        self.buch = KV.buch_mockup(620)
        self.buch_klein = self.buch.resize(
            (round(self.buch.width * 0.80), round(self.buch.height * 0.80)),
            Image.LANCZOS)

        # Szene 1 — Hook
        self.s1a = textbild(["3:33 Uhr."], 170, farbe=AKZENT)
        self.s1b = textbild(["Du liegst wach."], 104)
        # Szene 2 — die Frage
        self.s2a = textbild(["Und fragst dich wieder:"], 70, "SemiBold",
                            LEISE)
        self.s2b = textbild(["Bin ich", "zu empfindlich?"], 128, farbe=TEXT)
        # Szene 3 — seine Sätze
        self.s3kopf = textbild(["WAS ER SAGT"], 44, "SemiBold", AKZENT,
                               sperrung=9)
        self.s3 = [nachricht(z) for z in (
            "Das habe ich nie gesagt.",
            "Du bildest dir das ein.",
            "Du bist einfach zu sensibel.",
            "Ohne mich schaffst du das nicht.")]
        self.s3gelesen = lesebestaetigung()
        # Szene 4 — Wendung
        self.s4a = textbild(["Du bist nicht", "verrückt."], 132)
        self.s4b = textbild(["Du steckst in", "einem Muster."], 132,
                            farbe=AKZENT)
        # Szene 5 — Inhalte
        self.s5kopf = textbild(["WAS DIESES BUCH DIR ZEIGT"], 42, "SemiBold",
                               AKZENT, sperrung=6)
        self.s5 = [KV.punktzeile(z, 54) for z in (
            "Manipulation früh erkennen",
            "Verstehen, warum du bleibst",
            "Gehen — sicher und mit Plan",
            "Dir selbst wieder vertrauen")]
        # Szene 6 — Abschluss
        self.s6titel = textbild(["Der Narzisst", "in meinem Bett"], 92)
        self.s6a = textbild(["JETZT ERHÄLTLICH"], 48, "SemiBold", AKZENT,
                            sperrung=9)
        self.s6b = textbild(["Taschenbuch · Hardcover · E-Book"], 52,
                            "ExtraBold")
        self.s6c = textbild(["bei Amazon"], 52, "Medium", LEISE)
        self.s6d = textbild(["MARK VON DAAK"], 42, "SemiBold", TEXT,
                            sperrung=10)
        self.s6hilfe = textbild(
            ["Bei Gewalt: Notruf 110 · Hilfetelefon 116 016"], 30,
            "Medium", (150, 160, 174))

    def bild(self, t):
        # Grund: in Szene 1 und 2 das Foto in Fahrt, danach unscharf
        bild = self.verlauf.copy()
        d_foto = fenster(t, 0.0, 8.4, ein=0.01, aus=0.9)
        if d_foto > 0:
            fahrt = kamerafahrt(self.foto, self.faktor, t, 0.0, 8.4)
            einsetzen(bild, fahrt.convert("RGBA"), 0, 0, d_foto)
            # unten und oben abdunkeln, damit die Schrift steht
            einsetzen(bild, self.vignette, 0, 0, d_foto)
        d_grund = fenster(t, 7.6, 20.4, ein=0.9, aus=0.8)
        einsetzen(bild, self.hintergrund, 0, 0, d_grund)

        # Szene 1
        einblenden(bild, self.s1a, 1180, t, 0.5, 4.0, hub=40)
        einblenden(bild, self.s1b, 1400, t, 1.5, 4.0)

        # Szene 2
        einblenden(bild, self.s2a, 1150, t, 4.3, 8.0, hub=30)
        einblenden(bild, self.s2b, 1270, t, 5.1, 8.0, hub=70)

        # Szene 3: Nachrichten ploppen nacheinander auf
        einblenden(bild, self.s3kopf, 560, t, 8.4, 13.0, hub=30)
        ankunft = [8.8, 9.7, 10.6, 11.5]
        for i, (sprite, a) in enumerate(zip(self.s3, ankunft)):
            d = fenster(t, a, 13.0, ein=0.25, aus=0.4)
            if d <= 0:
                continue
            pop = aus_kubisch((t - a) / 0.3)
            skal = 0.86 + 0.14 * pop
            s = sprite.resize((max(1, round(sprite.width * skal)),
                               max(1, round(sprite.height * skal))),
                              Image.BILINEAR)
            y = 700 + i * 220 + (1 - pop) * 40
            einsetzen(bild, s, 90, y, d)
        d = fenster(t, 12.0, 13.0, ein=0.3, aus=0.4)
        einsetzen(bild, self.s3gelesen, B - self.s3gelesen.width - 80,
                  700 + 3 * 220 + 165, d)

        # Szene 4
        einblenden(bild, self.s4a, 700, t, 13.2, 16.2)
        einblenden(bild, self.s4b, 1060, t, 14.2, 16.2, hub=80)

        # Szene 5
        einblenden(bild, self.s5kopf, 700, t, 16.4, 20.2, hub=30)
        for i, sprite in enumerate(self.s5):
            d = fenster(t, 16.8 + i * 0.6, 20.2)
            if d > 0:
                schub = (1 - aus_kubisch((t - 16.8 - i * 0.6) / 0.6)) * -70
                einsetzen(bild, sprite, schub - 10, 830 + i * 130, d)

        # Szene 6: Buch schwebt ein, Titel und Kauf-Hinweis
        d6 = fenster(t, 20.3, DAUER + 1, ein=0.7)
        if d6 > 0:
            auf = aus_kubisch((t - 20.3) / 1.0)
            schweben = math.sin((t - 20.3) * 1.5) * 7
            y = 150 + (1 - auf) * 240 + schweben
            einsetzen(bild, self.buch_klein,
                      (B - self.buch_klein.width) / 2, y, d6)
        einblenden(bild, self.s6a, 1225, t, 21.2, DAUER + 1, hub=30)
        einblenden(bild, self.s6b, 1320, t, 21.6, DAUER + 1)
        einblenden(bild, self.s6c, 1405, t, 22.0, DAUER + 1)
        einblenden(bild, self.s6d, 1560, t, 22.6, DAUER + 1, hub=30)
        einblenden(bild, self.s6hilfe, 1760, t, 23.2, DAUER + 1, hub=20)

        # Filmkorn und Abblende
        ergebnis = bild.convert("RGB")
        korn = self.korn[int(t * 12) % len(self.korn)]
        ergebnis = Image.blend(ergebnis, korn, 0.035)
        if t > DAUER - 0.6:
            ergebnis = Image.blend(ergebnis, Image.new("RGB", (B, H)),
                                   klemmen((t - (DAUER - 0.6)) / 0.6))
        if t < 0.4:
            ergebnis = Image.blend(Image.new("RGB", (B, H)), ergebnis,
                                   klemmen(t / 0.4))
        return ergebnis


def main():
    for pflicht in (AUS / "cover.png", BAND / "cover" / "titelbild.png"):
        if not pflicht.exists():
            raise SystemExit(f"{pflicht.relative_to(WURZEL)} fehlt — erst "
                             "build_narzisst.py und build_cover.py laufen "
                             "lassen.")
    ziel = AUS / "werbevideo-9x16.mp4"
    video = Video()
    befehl = ["ffmpeg", "-y", "-loglevel", "error",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{B}x{H}",
              "-r", str(FPS), "-i", "-",
              "-c:v", "libx264", "-preset", "slow", "-crf", "18",
              "-pix_fmt", "yuv420p", "-movflags", "+faststart",
              str(ziel)]
    prozess = subprocess.Popen(befehl, stdin=subprocess.PIPE)
    anzahl = round(DAUER * FPS)
    for n in range(anzahl):
        prozess.stdin.write(video.bild(n / FPS).tobytes())
    prozess.stdin.close()
    if prozess.wait() != 0:
        raise SystemExit("ffmpeg ist fehlgeschlagen.")

    for sekunde in (3.2, 7.2, 12.6, 15.6, 19.6, 25.0):
        video.bild(sekunde).resize((B // 3, H // 3)).save(
            AUS / f"werbevideo-standbild-{sekunde:04.1f}s.png")
    print(f"{anzahl} Bilder, {DAUER:.0f} s, {B} x {H}, {FPS} fps")
    print(f"  → {ziel.relative_to(WURZEL)}  "
          f"({ziel.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
